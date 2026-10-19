"""Sesión estructurada sin nuevas consultas; revisión, controles y resultados de Python vinculados."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import shutil
from threading import Event

import pytest

from test_discovery import Provider, events, read_json, registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_pipeline import assessment_for
from trading_ai import rule_execution as engine
from trading_ai.ai import ProviderReply
from trading_ai.structured_ideas import propose_structured_idea
from trading_ai.structured_session import (BUDGET, StructuredSessionError, create_structured_session,
                                         finish_structured_session, main, structured_session_status, structured_session_usage)


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr("trading_ai.structured_ideas.ACCESS_ROOT", tmp_path / "ideas-access")
    monkeypatch.setattr("trading_ai.rule_execution.ACCESS_ROOT", tmp_path / "execution-access")
    monkeypatch.setattr("trading_ai.structured_session.ACCESS_ROOT", tmp_path / "sessions-access")


@pytest.fixture
def session(generated, tmp_path):
    split, frozen, proposal_dir, provider = generated
    directory = create_structured_session(proposal_dir, frozen, output_dir=tmp_path / "sessions")
    return split, frozen, proposal_dir, provider, directory


def test_create_attributes_existing_consumption_without_new_api_or_resetting_source(session, monkeypatch):
    _, _, proposal_dir, provider, directory = session
    original = {path: path.read_bytes() for path in proposal_dir.iterdir()}
    monkeypatch.setattr("trading_ai.ai.create_provider", lambda *a: pytest.fail("No crear proveedor"))
    status = structured_session_status(directory)
    assert status["state"] == "awaiting_review" and status["budget"] == BUDGET
    assert status["usage"] == {"source_model_requests": 1, "new_model_requests": 0, "source_input_tokens": 25,
                               "source_output_tokens": 40, "source_api_cost_usd": "0", "new_api_cost_usd": "0", "reserved_backtests": 0}
    assert provider.calls == 1 and all(path.read_bytes() == raw for path, raw in original.items())


def test_complete_synthetic_cycle_preserves_outer_data_and_uses_exactly_two_backtests(session, monkeypatch):
    split, frozen, proposal_dir, provider, directory = session
    original_open = Path.open
    def guarded(path, *a, **k):
        assert path.name not in ("evaluation.xml", "comparison.json")
        return original_open(path, *a, **k)
    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr("trading_ai.ai.create_provider", lambda *a: pytest.fail("No crear IA"))
    actual, calls = engine.run_backtest, []
    def tracked(*args, **kwargs):
        assert structured_session_usage(directory)["reserved_backtests"] == 2
        calls.append(1)
        return actual(*args, **kwargs)
    monkeypatch.setattr(engine, "run_backtest", tracked)
    run = finish_structured_session(directory, assessment_for(proposal_dir))
    outcome = read_json(run / "outcome.json")
    status = structured_session_status(directory)
    assert status["state"] == outcome["state"] == "completed"
    assert status["assessment"]["origin"] == "python" and status["assessment"]["scope"] == "known_development_history_only"
    assert calls == [1, 1] and provider.calls == 1
    assert outcome["automatic_followup_experiments"] == 0 and status["usage"]["new_model_requests"] == 0
    assert not (directory / "active.lock").exists()
    monkeypatch.setattr(engine, "run_backtest", lambda *a, **k: pytest.fail("Verificar no recalcula"))
    assert structured_session_status(directory) == status


@pytest.mark.parametrize("decision", ["rejected", "needs_clarification"])
def test_negative_review_records_reason_without_backtests_or_asking_for_approval(session, monkeypatch, decision):
    _, _, proposal_dir, provider, directory = session
    assessment = assessment_for(proposal_dir, decision)
    assessment["checks"]["lags_understood"] = False
    monkeypatch.setattr(engine, "run_backtest", lambda *a, **k: pytest.fail("No simular una propuesta no aceptada"))
    finish_structured_session(directory, assessment)
    status = structured_session_status(directory)
    assert status["state"] == decision and status["usage"]["reserved_backtests"] == 0
    assert status["assessment"] is None and provider.calls == 1


def test_invalid_assessment_is_correctable_before_consuming_finish(session):
    _, _, proposal_dir, provider, directory = session
    bad = assessment_for(proposal_dir)
    bad["proposal_sha256"] = "wrong"
    with pytest.raises(StructuredSessionError): finish_structured_session(directory, bad)
    assert not (directory / "actions/finish.json").exists()
    assert structured_session_status(directory)["state"] == "awaiting_review"
    finish_structured_session(directory, assessment_for(proposal_dir))
    assert structured_session_status(directory)["state"] == "completed" and provider.calls == 1


def test_same_source_cannot_get_another_session_or_replay_finish(session, tmp_path):
    _, frozen, proposal_dir, _, directory = session
    with pytest.raises(StructuredSessionError, match="sesión registrada"):
        create_structured_session(proposal_dir, frozen, output_dir=tmp_path / "other")
    finish_structured_session(directory, assessment_for(proposal_dir))
    with pytest.raises(StructuredSessionError, match="no se repetirá"):
        finish_structured_session(directory, assessment_for(proposal_dir))


def test_copied_session_cannot_reset_budget_or_location(session, tmp_path):
    _, _, _, _, directory = session
    shutil.copytree(directory, tmp_path / "copy")
    with pytest.raises(ValueError): structured_session_status(tmp_path / "copy")


def test_duplicate_proposal_cannot_create_a_session(session, tmp_path, proposal):
    _, frozen, _, _, _ = session
    duplicate = propose_structured_idea(Provider(proposal), frozen, output_dir=tmp_path / "duplicate")
    with pytest.raises(ValueError, match="duplicada"):
        create_structured_session(duplicate, frozen, output_dir=tmp_path / "other")
    assert not (tmp_path / "other").exists()


def test_interrupted_lock_is_preserved_without_model_call_or_recovery(session):
    _, _, proposal_dir, provider, directory = session
    (directory / "active.lock").write_bytes(b'interrupted')
    with pytest.raises(StructuredSessionError, match="interrupción"):
        finish_structured_session(directory, assessment_for(proposal_dir))
    assert (directory / "active.lock").read_bytes() == b'interrupted'
    assert provider.calls == 1 and structured_session_status(directory)["active_or_interrupted"] is True


def test_engine_failure_consumes_global_budget_and_does_not_trigger_retry(session, monkeypatch):
    _, _, proposal_dir, provider, directory = session
    calls = []
    def fail(*a, **k):
        calls.append(1)
        raise RuntimeError("Engine failed")
    monkeypatch.setattr(engine, "run_backtest", fail)
    with pytest.raises(StructuredSessionError) as failure:
        finish_structured_session(directory, assessment_for(proposal_dir))
    assert events(failure.value.directory)[-1]["data"]["child_run"]
    status = structured_session_status(directory)
    assert status["state"] == "finish_incomplete_or_invalid" and status["usage"]["reserved_backtests"] == 2
    with pytest.raises(StructuredSessionError, match="no se repetirá"):
        finish_structured_session(directory, assessment_for(proposal_dir))
    assert calls == [1] and provider.calls == 1


def test_concurrent_finish_actions_cannot_run_twice(session, monkeypatch):
    _, _, proposal_dir, provider, directory = session
    entered, release = Event(), Event()
    actual = engine.run_backtest
    def slow(*a, **k):
        entered.set()
        assert release.wait(20)
        return actual(*a, **k)
    monkeypatch.setattr(engine, "run_backtest", slow)
    assessment = assessment_for(proposal_dir)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(finish_structured_session, directory, assessment)
        assert entered.wait(20)
        second = pool.submit(finish_structured_session, directory, assessment)
        try:
            with pytest.raises(StructuredSessionError, match="ocupada"): second.result(timeout=20)
        finally: release.set()
        first.result(timeout=20)
    assert provider.calls == 1 and structured_session_status(directory)["state"] == "completed"


@pytest.mark.parametrize("field", ["budget", "source", "review", "scope"])
def test_changed_session_manifest_is_not_accepted(session, field):
    _, _, _, _, directory = session
    record = read_json(directory / "session.json")
    if field == "budget": record["budget"]["backtests"] = 100
    elif field == "source": record["source"]["sha256"]["proposal.json"] = "wrong"
    elif field == "review": record["technical_review_required"] = False
    else: record["scope"] = "unseen"
    (directory / "session.json").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError): structured_session_status(directory)


def test_changed_calculated_artifact_is_not_hidden_by_a_completed_outcome(session):
    _, _, proposal_dir, _, directory = session
    run = finish_structured_session(directory, assessment_for(proposal_dir))
    outcome = read_json(run / "outcome.json")
    candidate = Path(outcome["artifacts"]["execution"]["directory"]) / "candidate.json"
    with candidate.open("ab") as stream: stream.write(b' ')
    assert structured_session_status(directory)["state"] == "finish_incomplete_or_invalid"


def test_status_cli_is_read_only_with_no_provider_factory(session, monkeypatch, capsys):
    _, _, _, _, directory = session
    monkeypatch.setattr("trading_ai.ai.create_provider", lambda *a: pytest.fail("No crear proveedor"))
    main(["status", "--session", str(directory)])
    assert '"new_model_requests": 0' in capsys.readouterr().out


def test_unknown_inherited_cost_and_input_tokens_are_not_reported_as_zero(registered, proposal, tmp_path):
    _, frozen = registered
    class PartialUsage(Provider):
        def complete(self, messages, schema):
            reply = super().complete(messages, schema)
            return ProviderReply(reply.content, reply.model, {"output_tokens": 40})
    source = propose_structured_idea(PartialUsage(proposal), frozen, output_dir=tmp_path / "unknown-source")
    directory = create_structured_session(source, frozen, output_dir=tmp_path / "sessions")
    usage = structured_session_usage(directory)
    assert usage["source_input_tokens"] is None and usage["source_api_cost_usd"] is None
    assert usage["source_output_tokens"] == 40 and usage["new_api_cost_usd"] == "0"
    finish_structured_session(directory, assessment_for(source, "needs_clarification"))
    assert structured_session_status(directory)["usage"] == usage
