"""Decisiones heredadas sin reabrir sesiones ni consultar sus resultados financieros."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from test_discovery import Provider, registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_pipeline import assessment_for
from test_structured_session import session
from trading_ai.rule_planning import _canonical
from trading_ai.ai import ProviderReply
from trading_ai.structured_draft_context import prepare_draft_context
from trading_ai.structured_ideas import propose_structured_idea
from trading_ai.structured_session import (StructuredSessionError, create_structured_session, finish_structured_session)
from trading_ai.structured_review_memory import capture_review_memory, main, verify_review_memory
from trading_ai import structured_review_memory as memory_module
from trading_ai import structured_session as sessions


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr("trading_ai.structured_ideas.ACCESS_ROOT", tmp_path / "ideas-access")
    monkeypatch.setattr("trading_ai.rule_execution.ACCESS_ROOT", tmp_path / "execution-access")
    monkeypatch.setattr(sessions, "ACCESS_ROOT", tmp_path / "sessions-access")


def context_for(frozen, tmp_path):
    return prepare_draft_context(frozen, output_dir=tmp_path / "contexts")


def test_empty_memory_does_not_claim_global_review_coverage(registered, tmp_path):
    _, frozen = registered
    context = context_for(frozen, tmp_path)
    run = capture_review_memory(context, output_dir=tmp_path / "review-memory")
    record = verify_review_memory(run)
    assert record["entries"] == [] and record["scope"].endswith("not_all_independent_reviews")
    assert record["generation_ready"] is record["eligible_for_session"] is record["executable"] is False
    assert record["new_usage"] == {"model_requests": 0, "input_tokens": 0, "output_tokens": 0,
                                    "api_cost_usd": "0", "backtests": 0}


def test_awaiting_review_does_not_become_accepted_or_free_to_restart(session, tmp_path):
    _, frozen, _, provider, directory = session
    context = context_for(frozen, tmp_path)
    original = {path: path.read_bytes() for path in directory.rglob('*') if path.is_file()}
    run = capture_review_memory(context, output_dir=tmp_path / "review-memory")
    entry, = verify_review_memory(run)["entries"]
    assert entry["review_status"] == "not_registered" and entry["review"] is None
    assert entry["finish_consumed"] is False and entry["session_outcome_checked"] is False
    assert entry["source_usage"]["model_requests"] == 1 and provider.calls == 1
    assert all(path.read_bytes() == raw for path, raw in original.items())


def test_unknown_inherited_consumption_is_not_converted_to_zero(registered, proposal, tmp_path):
    _, frozen = registered
    class UnknownUsage(Provider):
        def complete(self, messages, schema):
            reply = super().complete(messages, schema)
            return ProviderReply(reply.content, reply.model,
                                 {"input_tokens": None, "output_tokens": None, "api_cost_usd": None})
    source = propose_structured_idea(UnknownUsage(proposal), frozen, output_dir=tmp_path / "proposals")
    create_structured_session(source, frozen, output_dir=tmp_path / "sessions")
    run = capture_review_memory(context_for(frozen, tmp_path), output_dir=tmp_path / "review-memory")
    record = verify_review_memory(run)
    inherited = record["entries"][0]["source_usage"]
    assert inherited["api_cost_usd"] is None and inherited["usage"][0]["input_tokens"] is None
    assert record["new_usage"]["api_cost_usd"] == "0"


@pytest.mark.parametrize("decision", ["needs_clarification", "rejected"])
def test_previous_decision_reason_and_source_usage_are_preserved(session, tmp_path, decision):
    _, frozen, source, provider, directory = session
    assessment = assessment_for(source, decision)
    assessment["rationale"] = "La hipótesis tiene 160 caracteres. ```\n# Texto del revisor sin verificar"
    finish_structured_session(directory, assessment)
    context = context_for(frozen, tmp_path)
    run = capture_review_memory(context, output_dir=tmp_path / "review-memory")
    record = verify_review_memory(run)
    entry, = record["entries"]
    assert entry["review_status"] == decision and entry["finish_consumed"] is True
    assert entry["review"]["reason"] == assessment["rationale"]
    assert entry["review"]["reason_is_unverified_reviewer_text"] is True
    assert entry["proposal_text_lengths"]["hypothesis"] == len(json.loads((source/'proposal.json').read_bytes())["proposal"]["hypothesis"])
    assert entry["source_usage"]["usage"][0]["input_tokens"] == 25
    assert record["new_usage"]["model_requests"] == 0 and provider.calls == 1
    assert "    # Texto del revisor sin verificar" in (run / "report.md").read_text(encoding="utf-8")


def test_accepted_review_is_not_presented_as_a_completed_financial_session(session, tmp_path, monkeypatch):
    _, frozen, source, _, directory = session
    def stop(*args, **kwargs): raise ValueError("Plan artificial interrumpido después de registrar revisión")
    monkeypatch.setattr(sessions, "prepare_structured_plan", stop)
    with pytest.raises(StructuredSessionError): finish_structured_session(directory, assessment_for(source))
    context = context_for(frozen, tmp_path)
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        if path.is_relative_to(directory):
            assert path.name not in ("results.json", "baseline.json", "candidate.json", "outcome.json")
        assert path.name not in ("evaluation.xml", "comparison.json")
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    run = capture_review_memory(context, output_dir=tmp_path / "review-memory")
    entry, = verify_review_memory(run)["entries"]
    assert entry["review_status"] == "accepted"
    assert entry["session_outcome_checked"] is entry["financial_results_read"] is False


def test_reserved_finish_without_a_registered_review_stays_consumed(session, tmp_path, monkeypatch):
    _, frozen, source, _, directory = session
    def stop(*args, **kwargs): raise ValueError("Fallo artificial anterior a registrar revisión")
    monkeypatch.setattr(sessions, "review_structured_idea", stop)
    with pytest.raises(StructuredSessionError): finish_structured_session(directory, assessment_for(source))
    context = context_for(frozen, tmp_path)
    run = capture_review_memory(context, output_dir=tmp_path / "review-memory")
    entry, = verify_review_memory(run)["entries"]
    assert entry["review_status"] == "finish_consumed_without_registered_review"
    assert entry["finish_consumed"] is True and entry["review"] is None


def test_capture_never_creates_provider_reopens_actions_or_calculates(session, tmp_path, monkeypatch):
    _, frozen, source, _, directory = session
    finish_structured_session(directory, assessment_for(source, "needs_clarification"))
    context = context_for(frozen, tmp_path)
    def forbidden(*args, **kwargs): pytest.fail("Solo memoria de revisiones")
    for name in ("trading_ai.ai.create_provider", "trading_ai.structured_session._action",
                 "trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.experiments.run_backtest",
                 "trading_ai.structured_session.verify_structured_execution", "socket.create_connection", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    run = capture_review_memory(context, output_dir=tmp_path / "review-memory")
    assert verify_review_memory(run)["entries"][0]["review_status"] == "needs_clarification"


def test_sessions_for_new_sources_require_an_updated_base_context(registered, proposal, tmp_path):
    _, frozen = registered
    context = context_for(frozen, tmp_path)
    source = propose_structured_idea(Provider(proposal), frozen, output_dir=tmp_path / "proposals")
    create_structured_session(source, frozen, output_dir=tmp_path / "sessions")
    with pytest.raises(ValueError, match="actualizado"):
        capture_review_memory(context, output_dir=tmp_path / "review-memory")


@pytest.mark.parametrize("filename", ["reviews.json", "reviews.json.sha256", "sessions.json", "report.md", "events.jsonl"])
def test_artifact_tampering_is_detected(registered, tmp_path, filename):
    _, frozen = registered
    run = capture_review_memory(context_for(frozen, tmp_path), output_dir=tmp_path / "review-memory")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_review_memory(run)


def test_changed_review_invalidates_its_memory(session, tmp_path):
    _, frozen, source, _, directory = session
    finish_structured_session(directory, assessment_for(source, "needs_clarification"))
    run = capture_review_memory(context_for(frozen, tmp_path), output_dir=tmp_path / "review-memory")
    record = verify_review_memory(run)
    path = Path(record["entries"][0]["review"]["origin"]["directory"]) / "review.json"
    with path.open("ab") as stream: stream.write(b' ')
    with pytest.raises(ValueError): verify_review_memory(run)


def test_attempt_event_changes_are_detected_even_without_changing_review(session, tmp_path):
    _, frozen, source, _, directory = session
    finish_structured_session(directory, assessment_for(source, "needs_clarification"))
    run = capture_review_memory(context_for(frozen, tmp_path), output_dir=tmp_path / "review-memory")
    record = verify_review_memory(run)
    attempt = Path(record["entries"][0]["finish_origin"]["attempt"])
    with (attempt / "events.jsonl").open("ab") as stream:
        stream.write(b'{"event":"extra","data":{}}\n')
    with pytest.raises(ValueError): verify_review_memory(run)


def test_later_review_requires_a_new_capture(session, tmp_path):
    _, frozen, source, _, directory = session
    context = context_for(frozen, tmp_path)
    run = capture_review_memory(context, output_dir=tmp_path / "review-memory")
    finish_structured_session(directory, assessment_for(source, "rejected"))
    with pytest.raises(ValueError): verify_review_memory(run)
    newer = capture_review_memory(context, output_dir=tmp_path / "review-memory")
    assert verify_review_memory(newer)["entries"][0]["review_status"] == "rejected"


def test_bound_and_claim_filename_are_enforced(session, tmp_path, monkeypatch):
    _, frozen, _, _, _ = session
    context = context_for(frozen, tmp_path)
    monkeypatch.setattr(memory_module, "MAX_SESSIONS", 0)
    with pytest.raises(ValueError, match="Demasiadas"):
        capture_review_memory(context, output_dir=tmp_path / "review-memory")
    monkeypatch.setattr(memory_module, "MAX_SESSIONS", 128)
    path, = sessions.ACCESS_ROOT.glob("*.json")
    path.rename(path.with_name("incorrect.json"))
    with pytest.raises(ValueError, match="identidad"):
        capture_review_memory(context, output_dir=tmp_path / "review-memory")


def test_memory_cannot_be_relocated(registered, tmp_path):
    _, frozen = registered
    run = capture_review_memory(context_for(frozen, tmp_path), output_dir=tmp_path / "review-memory")
    copied = tmp_path / "copied"
    shutil.copytree(run, copied)
    with pytest.raises(ValueError): verify_review_memory(copied)


def test_cli_capture_and_verification_do_not_enable_generation(registered, tmp_path, capsys):
    _, frozen = registered
    main(["capture", "--context-run", str(context_for(frozen, tmp_path)), "--output-dir", str(tmp_path / "review-memory")])
    main(["verify", "--run", capsys.readouterr().out.strip()])
    assert json.loads(capsys.readouterr().out)["generation_ready"] is False
