"""Sesiones acotadas: control entre etapas, revisión independiente y reservas duraderas."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
from threading import Event

import pytest

from test_discovery import Provider, events, idea, read_json, registered
from test_formalization import proposed
from test_holdout import setup
from trading_ai.agent_feedback import FEEDBACK_SCHEMA
from trading_ai.ai import AIConfig, ProviderError, ProviderReply
from trading_ai.experiments import expected_assessment
from trading_ai.discovery import discover_idea
from trading_ai.research import RunJournal
from trading_ai.research_session import (BUDGET, SessionError, _BudgetProvider, create_session,
                                         finish_session, main, propose_session, session_status, session_usage)
from trading_ai.rule_planning import CHECKS


@pytest.fixture(autouse=True)
def isolated_access(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.agent_feedback.ACCESS_ROOT", tmp_path / "feedback-access")
    monkeypatch.setattr("trading_ai.rule_execution.ACCESS_ROOT", tmp_path / "execution-access")
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")


class ScriptedProvider:
    def __init__(self, answers, *, bad_analysis=False):
        self.answers, self.calls, self.messages = list(answers), 0, []
        self.bad_analysis = bad_analysis
    def describe(self):
        return {"provider": "test", "model": "offline"}
    def complete(self, messages, schema):
        self.calls += 1
        self.messages.append(deepcopy(messages))
        if schema == FEEDBACK_SCHEMA:
            context = json.loads(messages[-1]["content"])
            expected = expected_assessment(context)
            reply = {"criterion_status": {"supported_in_sample": "met", "not_supported_in_sample": "not_met",
                                          "inconclusive": "inconclusive"}[expected["verdict"]],
                     "return_comparison": expected["return_comparison"], "drawdown_comparison": expected["drawdown_comparison"],
                     "scope": "known_development_history_only"}
            if self.bad_analysis: reply["scope"] = "unseen"
        else:
            reply = self.answers.pop(0)
        if isinstance(reply, Exception): raise reply
        return ProviderReply(json.dumps(reply), "offline", {"input_tokens": 25, "output_tokens": 40, "api_cost_usd": "0"})


@pytest.fixture
def session(registered, tmp_path, idea, proposed):
    split, frozen = registered
    idea.update(entry_rule="Referencia estrictamente mayor que umbral.", exit_rule="Referencia menor o igual que umbral.",
                parameters=[{"name": "threshold", "value": 1}])
    directory = create_session(frozen, output_dir=tmp_path / "sessions")
    return split, frozen, directory, idea, proposed


def proposal_record(session):
    action = read_json(session / "actions/propose.json")
    return read_json(Path(action["attempt"]) / "proposal.json")


def assessment_for(session):
    record = proposal_record(session)
    translation = Path(record["latest_translation"])
    return {"schema_version": 1, "translation_sha256": sha256((translation / "translation.json").read_bytes()).hexdigest(),
            "spec_sha256": read_json(translation / "translation.json")["spec_sha256"], "reviewer": "Revisión técnica del ejemplo artificial",
            "decision": "accepted", "rationale": "Entrada >1 y salida <=1 coinciden con las reglas sintéticas.",
            "checks": dict.fromkeys(CHECKS, True)}


def test_create_is_offline_sealed_and_budget_starts_at_zero(session, monkeypatch):
    _, _, directory, _, _ = session
    monkeypatch.setattr("trading_ai.research_session.create_provider", lambda *a: pytest.fail("No iniciar IA"))
    status = session_status(directory)
    assert status["state"] == "prepared" and status["budget"] == BUDGET
    assert status["usage"] == {"reserved_model_requests": 0, "reserved_output_tokens": 0, "input_tokens": 0,
                               "output_tokens": 0, "api_cost_usd": "0", "reserved_backtests": 0}
    assert status["active_or_interrupted"] is False


def test_cycle_stops_at_review_and_finishes_with_fixed_accounts_and_verified_analysis(session, tmp_path, monkeypatch):
    split, frozen, directory, idea, proposed = session
    originals = {p: p.read_bytes() for folder in (split, frozen) for p in folder.iterdir()}
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.resolve() != (split / "evaluation.xml").resolve()
        assert path.name != "comparison.json"
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    provider = ScriptedProvider([idea, proposed])
    attempt = propose_session(directory, provider=provider)
    assert read_json(attempt / "proposal.json")["state"] == "awaiting_review"
    assert session_status(directory)["usage"]["reserved_model_requests"] == provider.calls == 2
    assert session_usage(directory)["reserved_backtests"] == 0 and not (tmp_path / "execution-access").exists()
    outcome = finish_session(directory, assessment_for(directory), provider=provider)
    saved = read_json(outcome / "outcome.json")
    assert saved["state"] == "completed" and saved["automatic_followup_experiments"] == 0
    assert provider.calls == 3 and session_usage(directory)["reserved_model_requests"] == 3
    assert session_usage(directory)["reserved_backtests"] == 2
    assert session_usage(directory)["input_tokens"] == 75 and session_usage(directory)["output_tokens"] == 120
    assert session_usage(directory)["api_cost_usd"] == "0"
    execution = Path(saved["artifacts"]["execution"]["directory"])
    assert read_json(execution / "results.json")["completed_backtests"] == ["baseline", "candidate"]
    assert read_json(Path(saved["artifacts"]["analysis"]["directory"]) / "analysis.json")["executable"] is False
    assert session_status(directory)["state"] == "completed" and not (directory / "active.lock").exists()
    monkeypatch.undo()
    assert all(path.read_bytes() == raw for path, raw in originals.items())


def test_revision_path_uses_four_calls_before_review_and_five_in_total(session):
    _, _, directory, idea, proposed = session
    old = deepcopy(idea)
    old["exit_rule"] += " O cerrar al final del periodo."
    revised = deepcopy(idea)
    revised["title"] = "Reformulación artificial precisa"
    unclear = {"status": "needs_clarification", "reason": "Alternativas sin decidir.", "spec": None}
    provider = ScriptedProvider([old, unclear, revised, proposed])
    propose_session(directory, provider=provider)
    assert provider.calls == 4 and "revised_idea" in proposal_record(directory)["artifacts"]
    finish_session(directory, assessment_for(directory), provider=provider)
    usage = session_usage(directory)
    assert usage["reserved_model_requests"] == provider.calls == 5
    assert usage["reserved_output_tokens"] == 1920 and usage["reserved_backtests"] == 2


@pytest.mark.parametrize("status", ["unsupported", "needs_clarification", "needs_data"])
def test_blocked_proposals_never_execute_or_force_a_winner(session, tmp_path, status):
    _, _, directory, idea, _ = session
    blocked = {"status": status, "reason": "No se puede traducir fielmente.", "spec": None}
    if status == "needs_data":
        idea["data_requirements"]["ohlc"] = True
        replies = [idea]
    elif status == "needs_clarification":
        revised = deepcopy(idea)
        revised["title"] = "Aún hay dudas"
        revised["exit_rule"] += " O en otra condición sin precisar."
        replies = [idea, blocked, revised, blocked]
    else: replies = [idea, blocked]
    provider = ScriptedProvider(replies)
    propose_session(directory, provider=provider)
    count = provider.calls
    assert session_status(directory)["state"] == status
    with pytest.raises(SessionError, match="listas para revisión"):
        finish_session(directory, {}, provider=provider)
    assert provider.calls == count and session_usage(directory)["reserved_backtests"] == 0
    assert not (tmp_path / "execution-access").exists()


@pytest.mark.parametrize("decision", ["rejected", "needs_clarification"])
def test_nonaccepting_review_is_recorded_without_spending_backtests(session, decision):
    _, _, directory, idea, proposed = session
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    assessment = assessment_for(directory)
    assessment["decision"] = decision
    assessment["checks"]["exit_matches"] = False
    outcome = finish_session(directory, assessment, provider=provider)
    assert read_json(outcome / "outcome.json")["state"] == decision
    assert provider.calls == 2 and session_usage(directory)["reserved_backtests"] == 0


def test_invalid_assessment_can_be_corrected_without_regenerating_proposal(session):
    _, _, directory, idea, proposed = session
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    assessment = assessment_for(directory)
    wrong = deepcopy(assessment)
    wrong["translation_sha256"] = "wrong"
    with pytest.raises(SessionError): finish_session(directory, wrong, provider=provider)
    assert not (directory / "actions/finish.json").exists()
    assert session_usage(directory)["reserved_backtests"] == 0
    finish_session(directory, assessment, provider=provider)
    assert provider.calls == 3


def test_global_provider_guard_refuses_a_sixth_call_and_keeps_known_usage(session):
    _, _, directory, _, _ = session
    journal = RunJournal(directory / "attempts")
    provider = ScriptedProvider([{}] * 6)
    wrapped = _BudgetProvider(provider, directory, journal, lambda: None)
    for _ in range(5): wrapped.complete([], {})
    with pytest.raises(ValueError, match="agotado"): wrapped.complete([], {})
    assert provider.calls == 5 and session_usage(directory)["reserved_model_requests"] == 5


@pytest.mark.parametrize("usage", [None, {"output_tokens": 384, "api_cost_usd": "0"}])
def test_generation_failure_consumes_action_and_preserves_unknown_or_known_cost(session, usage):
    _, _, directory, _, _ = session
    provider = ScriptedProvider([ProviderError("failed", usage)])
    with pytest.raises(SessionError) as failure: propose_session(directory, provider=provider)
    assert events(failure.value.directory)[-1]["event"] == "action_failed"
    counts = session_usage(directory)
    assert counts["reserved_model_requests"] == 1 and counts["reserved_backtests"] == 0
    assert counts["api_cost_usd"] == (None if usage is None else "0")
    assert session_status(directory)["state"] == "propose_incomplete_or_invalid"
    with pytest.raises(SessionError, match="no se repetirá"): propose_session(directory, provider=provider)
    assert provider.calls == 1


def test_copied_session_cannot_reset_budget_or_create_a_new_identity(session, tmp_path):
    _, _, directory, idea, proposed = session
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    shutil.copytree(directory, tmp_path / "copy")
    with pytest.raises(ValueError, match="ubicación"):
        session_status(tmp_path / "copy")
    assert provider.calls == 2


@pytest.mark.parametrize("field", ["budget", "config", "review", "code"])
def test_manifest_changes_are_rejected_even_if_only_seal_is_recomputed(session, field):
    _, _, directory, _, _ = session
    path = directory / "session.json"
    value = read_json(path)
    if field == "budget": value["budget"]["model_requests"] = 100
    elif field == "config": value["ai_config"]["output_tokens"] = 2048
    elif field == "review": value["technical_review_required"] = False
    else: value["code_sha256"]["research_session.py"] = "wrong"
    path.write_text(json.dumps(value), encoding="utf-8")
    (directory / "session.sha256").write_text(sha256(path.read_bytes()).hexdigest(), encoding="ascii")
    with pytest.raises(ValueError): session_status(directory)


@pytest.mark.parametrize("config", [AIConfig(provider="openai"), AIConfig(output_tokens=512), AIConfig(context_tokens=8192)])
def test_disallowed_provider_or_resource_limits_fail_before_creating_session(registered, tmp_path, config):
    _, frozen = registered
    with pytest.raises(ValueError): create_session(frozen, config=config, output_dir=tmp_path / "sessions")
    assert not (tmp_path / "sessions").exists()


def test_propose_or_finish_cannot_be_repeated(session):
    _, _, directory, idea, proposed = session
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    with pytest.raises(SessionError, match="no se repetirá"): propose_session(directory, provider=provider)
    assessment = assessment_for(directory)
    finish_session(directory, assessment, provider=provider)
    with pytest.raises(SessionError, match="no se repetirá"): finish_session(directory, assessment, provider=provider)
    assert provider.calls == 3


def test_simultaneous_actions_are_rejected_without_a_second_model_call(session):
    _, _, directory, idea, proposed = session
    entered, release = Event(), Event()
    class Slow(ScriptedProvider):
        def complete(self, messages, schema):
            if self.calls == 0:
                entered.set()
                assert release.wait(15)
            return super().complete(messages, schema)
    provider = Slow([idea, proposed])
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(propose_session, directory, provider=provider)
        assert entered.wait(15)
        second = pool.submit(propose_session, directory, provider=provider)
        try:
            with pytest.raises(SessionError, match="ocupada"): second.result(timeout=15)
        finally: release.set()
        first.result(timeout=15)
    assert provider.calls == 2 and session_status(directory)["state"] == "awaiting_review"


def test_existing_lock_is_not_removed_or_recovered_automatically(session):
    _, _, directory, idea, proposed = session
    (directory / "active.lock").write_bytes(b'previous interrupted action')
    provider = ScriptedProvider([idea, proposed])
    with pytest.raises(SessionError, match="interrupción"): propose_session(directory, provider=provider)
    assert provider.calls == 0 and (directory / "active.lock").read_bytes() == b'previous interrupted action'


def test_inconclusive_analysis_skips_third_model_call(session):
    _, _, directory, idea, proposed = session
    idea["parameters"][0]["value"] = 100
    idea["entry_rule"] = "Referencia estrictamente mayor que 100."
    idea["exit_rule"] = "Referencia menor o igual que 100."
    for role in ("entry", "exit"): proposed["spec"][role]["conditions"][0]["right"]["value"] = "100"
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    outcome = finish_session(directory, assessment_for(directory), provider=provider)
    assert provider.calls == 2 and read_json(outcome / "outcome.json")["state"] == "completed"
    assert session_usage(directory)["reserved_backtests"] == 2


def test_analysis_failure_keeps_engine_results_and_consumed_backtest_budget(session):
    _, _, directory, idea, proposed = session
    provider = ScriptedProvider([idea, proposed], bad_analysis=True)
    propose_session(directory, provider=provider)
    with pytest.raises(SessionError) as failure:
        finish_session(directory, assessment_for(directory), provider=provider)
    log = events(failure.value.directory)
    execution = next(item["data"]["origin"]["directory"] for item in log
                     if item["event"] == "artifact_registered" and item["data"]["kind"] == "execution")
    assert read_json(Path(execution) / "results.json")["stage"] == "execution_completed"
    assert session_usage(directory)["reserved_backtests"] == 2 and provider.calls == 3
    assert session_status(directory)["state"] == "finish_incomplete_or_invalid"


def test_reservation_without_response_remains_spent_with_unknown_usage(session):
    _, _, directory, _, _ = session
    journal = RunJournal(directory / "attempts")
    (directory / "budget").mkdir()
    (directory / "budget/model-1.json").write_text(json.dumps({"ordinal": 1, "attempt": str(journal.directory),
                                                              "max_output_tokens": 384}), encoding="utf-8")
    usage = session_usage(directory)
    assert usage["reserved_model_requests"] == 1 and usage["reserved_output_tokens"] == 384
    assert usage["input_tokens"] is None and usage["output_tokens"] is None and usage["api_cost_usd"] is None


def test_engine_failure_consumes_global_backtest_reservation_and_cannot_retry(session, monkeypatch):
    _, _, directory, idea, proposed = session
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    calls = []
    def fail(*args, **kwargs):
        calls.append(1)
        raise RuntimeError("Engine test")
    monkeypatch.setattr("trading_ai.rule_execution.run_backtest", fail)
    assessment = assessment_for(directory)
    with pytest.raises(SessionError, match="Engine test"):
        finish_session(directory, assessment, provider=provider)
    assert session_usage(directory)["reserved_backtests"] == 2
    with pytest.raises(SessionError, match="no se repetirá"):
        finish_session(directory, assessment, provider=provider)
    assert len(calls) == 1 and provider.calls == 2


def test_invalidated_proposal_is_not_hidden_by_a_completed_finish(session):
    _, _, directory, idea, proposed = session
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    finish_session(directory, assessment_for(directory), provider=provider)
    source = Path(proposal_record(directory)["latest_idea"]) / "idea.json"
    with source.open("ab") as stream: stream.write(b' ')
    assert session_status(directory)["state"] == "propose_incomplete_or_invalid"


def test_changed_proposal_artifact_prevents_finish_before_backtest_reservation(session):
    _, _, directory, idea, proposed = session
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    assessment = assessment_for(directory)
    translation = Path(proposal_record(directory)["latest_translation"])
    with (translation / "translation.json").open("ab") as stream: stream.write(b' ')
    with pytest.raises(SessionError): finish_session(directory, assessment, provider=provider)
    assert session_usage(directory)["reserved_backtests"] == 0 and provider.calls == 2


def test_cli_create_and_status_are_offline_and_no_override_is_exposed(registered, tmp_path, monkeypatch, capsys):
    _, frozen = registered
    monkeypatch.setattr("trading_ai.research_session.create_provider", lambda *a: pytest.fail("Sin IA"))
    main(["create", "--frozen-run", str(frozen), "--output-dir", str(tmp_path / "sessions")])
    directory, = (tmp_path / "sessions").iterdir()
    main(["status", "--session", str(directory)])
    assert '"state": "prepared"' in capsys.readouterr().out
    with pytest.raises(SystemExit) as failure:
        main(["propose", "--session", str(directory), "--max-requests", "100"])
    assert failure.value.code == 2


def test_duplicate_is_stopped_after_one_call_before_translation_or_revision(session, tmp_path, monkeypatch):
    _, frozen, _, idea, _ = session
    previous = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "memory/discovery")
    directory = create_session(frozen, output_dir=tmp_path / "fresh")
    repeated = deepcopy(idea)
    repeated["title"] = "Otro título para las mismas reglas"
    repeated["hypothesis"] = "Otra explicación sin cambiar condiciones."
    repeated["parameters"][0]["value"] = 1.0
    repeated["entry_rule"] = "  REFERENCIA estrictamente MAYOR que umbral. "
    provider = ScriptedProvider([repeated])
    monkeypatch.setattr("trading_ai.research_session.formalize_idea", lambda *a, **k: pytest.fail("No traducir duplicado"))
    monkeypatch.setattr("trading_ai.research_session.revise_idea", lambda *a, **k: pytest.fail("No gastar reformulación"))
    propose_session(directory, provider=provider)
    record = proposal_record(directory)
    assert record["state"] == "duplicate_idea" and record["latest_translation"] is None
    assert record["duplicate_of"] == [read_json(previous / "idea.json")["idea_id"]]
    assert provider.calls == session_usage(directory)["reserved_model_requests"] == 1
    assert session_usage(directory)["reserved_backtests"] == 0
    assert session_status(directory)["state"] == "duplicate_idea"
    with pytest.raises(SessionError, match="listas para revisión"): finish_session(directory, {}, provider=provider)
    assert provider.calls == 1


def test_retitle_only_revision_is_stopped_before_second_translation(session):
    _, _, directory, idea, _ = session
    revised = deepcopy(idea)
    revised["title"] = "Solo cambia el título"
    provider = ScriptedProvider([idea, {"status": "needs_clarification", "reason": "Regla sin precisar.", "spec": None}, revised])
    propose_session(directory, provider=provider)
    record = proposal_record(directory)
    assert record["state"] == "duplicate_idea" and provider.calls == 3
    assert "revised_idea" in record["artifacts"] and "revised_translation" not in record["artifacts"]
    assert session_usage(directory)["reserved_backtests"] == 0


def test_novel_proposal_receives_sealed_history_and_can_reach_review(session, tmp_path):
    _, frozen, _, idea, proposed = session
    previous = deepcopy(idea)
    previous["exit_rule"] += " O al final del periodo."
    discover_idea(Provider(previous), frozen, output_dir=tmp_path / "memory/discovery")
    directory = create_session(frozen, output_dir=tmp_path / "fresh")
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    assert session_status(directory)["state"] == "awaiting_review" and provider.calls == 2
    context = json.loads(provider.messages[0][-1]["content"].split("Contexto y memoria: ")[1])
    assert context["known_ideas"][0]["proposal"] == previous
    assert "rolling_min" in context["development"]["available_rule_features"]
    assert "candidate" not in context and "evaluation" not in context
    initial = Path(proposal_record(directory)["artifacts"]["root_idea"]["directory"])
    recorded = next(item for item in events(initial) if item["event"] == "model_request")
    assert recorded["data"]["messages"] == provider.messages[0]


@pytest.mark.parametrize("target", ["memory", "source"])
def test_changed_memory_or_sources_stop_before_generation(session, tmp_path, target):
    _, frozen, _, idea, proposed = session
    previous = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "memory/discovery")
    directory = create_session(frozen, output_dir=tmp_path / "fresh")
    path = directory / "memory.json" if target == "memory" else previous / "idea.json"
    with path.open("ab") as stream: stream.write(b' ')
    provider = ScriptedProvider([idea, proposed])
    with pytest.raises(ValueError): propose_session(directory, provider=provider)
    assert provider.calls == 0
    assert not (directory / "actions/propose.json").exists()


def test_ideas_added_after_creation_do_not_change_the_sealed_context(session, tmp_path):
    _, frozen, directory, idea, proposed = session
    assert read_json(directory / "memory.json")["entries"] == []
    discover_idea(Provider(idea), frozen, output_dir=tmp_path / "memory/discovery")
    provider = ScriptedProvider([idea, proposed])
    propose_session(directory, provider=provider)
    assert session_status(directory)["state"] == "awaiting_review" and provider.calls == 2
    context = json.loads(provider.messages[0][-1]["content"].split("Contexto y memoria: ")[1])
    assert context["known_ideas"] == []
