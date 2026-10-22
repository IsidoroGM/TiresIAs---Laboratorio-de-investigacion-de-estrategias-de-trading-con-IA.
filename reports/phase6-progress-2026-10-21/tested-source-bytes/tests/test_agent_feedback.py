"""Ideas revisadas y conclusiones contrastadas: presupuestos, linaje y fuentes verificadas."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import shutil
from threading import Barrier

import pytest

from test_discovery import Provider, events, idea, read_json, registered
from test_formalization import proposed
from test_holdout import setup
from test_rule_execution import another_plan, ready
from test_rule_planning import accepted, translated
from trading_ai.ai import ProviderError
from trading_ai.agent_feedback import (FEEDBACK_SCHEMA, FeedbackError, analyze_execution, main,
                                       revise_idea, verify_revision)
from trading_ai.discovery import discover_idea
from trading_ai.formalization import formalize_idea
from trading_ai.rule_execution import execute_rule_plan


@pytest.fixture(autouse=True)
def isolated_access(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.agent_feedback.ACCESS_ROOT", tmp_path / "feedback-access")
    monkeypatch.setattr("trading_ai.rule_execution.ACCESS_ROOT", tmp_path / "execution-access")


@pytest.fixture
def parent(registered, tmp_path, idea):
    split, frozen = registered
    idea["exit_rule"] = "Salir al cierre del día o por cruce inverso."
    idea_dir = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    translation = formalize_idea(Provider({"status": "needs_clarification", "reason": "Dos alternativas de salida.", "spec": None}),
                                idea_dir, frozen, output_dir=tmp_path / "translations")
    revised = deepcopy(idea)
    revised.update(title="Reformulación sintética", entry_rule="Referencia mayor que umbral.",
                   exit_rule="Referencia menor o igual que umbral.", parameters=[{"name": "threshold", "value": 1}])
    return split, frozen, idea_dir, translation, revised


@pytest.fixture
def completed(ready, tmp_path):
    _, frozen, _, plan = ready
    directory = execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    result = read_json(directory / "results.json")
    expected = {key: result["assessment"][key] for key in FEEDBACK_SCHEMA["required"]}
    return frozen, directory, expected


def test_revision_preserves_parent_links_is_pending_and_compatible_with_formalizer(parent, tmp_path, monkeypatch):
    split, frozen, old_idea, translation, revised = parent
    original = {p: p.read_bytes() for folder in (split, frozen, old_idea, translation) for p in folder.iterdir()}
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.resolve() != (split / "evaluation.xml").resolve()
        assert path.name != "comparison.json"
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr("trading_ai.rule_execution.run_backtest", lambda *a, **k: pytest.fail("Sin simulaciones"))
    provider = Provider(revised)
    directory = revise_idea(provider, translation, frozen, output_dir=tmp_path / "revisions")
    saved = verify_revision(directory, frozen)
    assert saved["proposal"] == revised and saved["idea_id"] != read_json(old_idea / "idea.json")["idea_id"]
    assert saved["lineage"]["root_idea_id"] == read_json(old_idea / "idea.json")["idea_id"]
    assert saved["lineage"]["parent_proposal"] == read_json(old_idea / "idea.json")["proposal"]
    assert saved["status"] == "pending_tool_mapping" and saved["calculated_results"] is None
    assert saved["executable"] is False and saved["model_requests"] == provider.calls == 1
    assert saved["api_cost_usd"] == "0" and saved["lineage"]["depth"] == 1
    assert events(directory)[-1]["event"] == "idea_queued"
    assert "final_equity" not in str(provider.messages) and "max_drawdown_percent" not in str(provider.messages)
    context = json.loads(provider.messages[-1]["content"])
    assert context["parent_idea"] == read_json(old_idea / "idea.json")["proposal"]
    assert context["unverified_model_reason"] == "Dos alternativas de salida."
    assert "nueva" in provider.messages[0]["content"]
    next_translation = formalize_idea(Provider({"status": "unsupported", "reason": "Prueba del contrato.", "spec": None}),
                                     directory, frozen, output_dir=tmp_path / "next-translation")
    assert read_json(next_translation / "translation.json")["source"]["idea_id"] == saved["idea_id"]
    monkeypatch.undo()
    assert all(path.read_bytes() == raw for path, raw in original.items())


@pytest.mark.parametrize("kind", ["same", "copy", "new_translation"])
def test_revision_limit_survives_output_changes_copies_and_another_reason(parent, tmp_path, kind):
    _, frozen, idea_dir, translation, revised = parent
    revise_idea(Provider(revised), translation, frozen, output_dir=tmp_path / "revisions")
    if kind == "copy":
        shutil.copytree(translation, tmp_path / "copy")
        translation = tmp_path / "copy"
    elif kind == "new_translation":
        translation = formalize_idea(Provider({"status": "needs_clarification", "reason": "Otro texto de la misma duda.", "spec": None}),
                                     idea_dir, frozen, output_dir=tmp_path / "new-translation")
    provider = Provider(revised)
    with pytest.raises(FeedbackError, match="reservado"):
        revise_idea(provider, translation, frozen, output_dir=tmp_path / "different-output")
    assert provider.calls == 0


@pytest.mark.parametrize("remove_lineage", [False, True])
def test_revised_child_cannot_start_an_automatic_chain(parent, tmp_path, remove_lineage):
    _, frozen, _, translation, revised = parent
    child = revise_idea(Provider(revised), translation, frozen, output_dir=tmp_path / "revisions")
    if remove_lineage:
        record = read_json(child / "idea.json")
        del record["lineage"]
        (child / "idea.json").write_text(json.dumps(record), encoding="utf-8")
    next_translation = formalize_idea(Provider({"status": "needs_clarification", "reason": "Todavía falta claridad.", "spec": None}),
                                     child, frozen, output_dir=tmp_path / "next")
    provider = Provider(revised)
    with pytest.raises(FeedbackError, match="cadenas"):
        revise_idea(provider, next_translation, frozen, output_dir=tmp_path / "more")
    assert provider.calls == 0


def test_unchanged_reply_is_rejected_and_consumes_the_only_revision(parent, tmp_path):
    _, frozen, idea_dir, translation, revised = parent
    provider = Provider(read_json(idea_dir / "idea.json")["proposal"])
    with pytest.raises(FeedbackError, match="exactamente") as failure:
        revise_idea(provider, translation, frozen, output_dir=tmp_path / "revisions")
    assert events(failure.value.directory)[-1]["data"]["usage"][0]["output_tokens"] == 40
    assert not (failure.value.directory / "idea.json").exists()
    with pytest.raises(FeedbackError, match="reservado"):
        revise_idea(Provider(revised), translation, frozen, output_dir=tmp_path / "retry")


@pytest.mark.parametrize("response", ["not JSON", '{"title":"a","title":"b"}', {"code": "print(1)"},
                                     ProviderError("truncated", {"output_tokens": 384, "api_cost_usd": "0"}),
                                     ProviderError("unknown usage")])
def test_bad_revision_responses_preserve_raw_usage_without_retry(parent, tmp_path, response):
    _, frozen, _, translation, _ = parent
    provider = Provider(response)
    with pytest.raises(FeedbackError) as failure:
        revise_idea(provider, translation, frozen, output_dir=tmp_path / "revisions")
    log = events(failure.value.directory)
    assert provider.calls == 1 and log[-1]["event"] == "revision_failed"
    assert log[-1]["data"]["access_claimed"] is True
    assert log[-1]["data"]["model_requests"] == 1
    assert not (failure.value.directory / "idea.json").exists()
    if isinstance(response, ProviderError) and response.usage is None:
        assert log[-1]["data"]["api_cost_usd"] is None
    else: assert log[-1]["data"]["usage"]


def test_changed_parent_during_revision_prevents_saving_child(parent, tmp_path):
    _, frozen, _, translation, revised = parent
    class Mutating(Provider):
        def complete(self, messages, schema):
            result = super().complete(messages, schema)
            with (translation / "translation.json").open("ab") as stream: stream.write(b' ')
            return result
    with pytest.raises(FeedbackError, match="cambiaron") as failure:
        revise_idea(Mutating(revised), translation, frozen, output_dir=tmp_path / "revisions")
    assert not (failure.value.directory / "idea.json").exists()


@pytest.mark.parametrize("status", ["unsupported", "proposed"])
def test_nonambiguous_parent_is_rejected_without_reservation(parent, tmp_path, proposed, status):
    _, frozen, idea_dir, _, revised = parent
    reply = proposed if status == "proposed" else {"status": status, "reason": "No hay herramienta.", "spec": None}
    translation = formalize_idea(Provider(reply), idea_dir, frozen, output_dir=tmp_path / "other")
    provider = Provider(revised)
    with pytest.raises(FeedbackError, match="pendientes de aclaración"):
        revise_idea(provider, translation, frozen, output_dir=tmp_path / "revisions")
    assert provider.calls == 0 and not (tmp_path / "feedback-access").exists()


@pytest.mark.parametrize("target", ["lineage", "parent", "claim"])
def test_revision_verifier_detects_changed_lineage_parent_or_reservation(parent, tmp_path, target):
    _, frozen, _, translation, revised = parent
    directory = revise_idea(Provider(revised), translation, frozen, output_dir=tmp_path / "revisions")
    if target == "lineage":
        record = read_json(directory / "idea.json")
        record["lineage"]["root_idea_id"] = "wrong"
        (directory / "idea.json").write_text(json.dumps(record), encoding="utf-8")
    elif target == "parent":
        with (translation / "translation.json").open("ab") as stream: stream.write(b' ')
    else:
        claim, = (tmp_path / "feedback-access").iterdir()
        with claim.open("ab") as stream: stream.write(b' ')
    with pytest.raises(ValueError): verify_revision(directory, frozen)


def test_extra_data_or_still_ambiguous_revision_does_not_grant_permissions(parent, tmp_path):
    _, frozen, _, translation, revised = parent
    revised["data_requirements"]["ohlc"] = True
    revised["exit_rule"] = "Cerrar con alternativa A o B todavía sin decidir."
    directory = revise_idea(Provider(revised), translation, frozen, output_dir=tmp_path / "revisions")
    record = verify_revision(directory, frozen)
    assert record["status"] == "needs_data_and_tool_mapping" and record["executable"] is False
    assert record["calculated_results"] is None


def test_analysis_sends_verified_summaries_and_checks_exact_python_conclusion(completed, tmp_path, monkeypatch):
    frozen, execution, expected = completed
    original = {p: p.read_bytes() for p in execution.iterdir()}
    monkeypatch.setattr("trading_ai.rule_execution.run_backtest", lambda *a, **k: pytest.fail("No recalcular"))
    provider = Provider(expected)
    directory = analyze_execution(provider, execution, frozen, output_dir=tmp_path / "analyses")
    saved = read_json(directory / "analysis.json")
    assert provider.calls == saved["model_requests"] == 1 and saved["assessment"] == expected
    assert saved["model_assessment"] == expected and saved["origin"] == "model_cross_checked_by_python"
    assert saved["api_cost_usd"] == "0" and saved["executable"] is False and saved["new_experiments"] == 0
    context = json.loads(provider.messages[-1]["content"])
    results = read_json(execution / "results.json")
    assert context == {key: results[key] for key in ("data", "policy", "proposal", "baseline", "candidate")}
    assert "equity_curve" not in str(provider.messages) and "entry_rule" not in str(provider.messages)
    assert all(path.read_bytes() == raw for path, raw in original.items())
    with pytest.raises(FeedbackError, match="reservado"):
        analyze_execution(Provider(expected), execution, frozen, output_dir=tmp_path / "more")


@pytest.mark.parametrize("change", ["verdict", "scope", "invented_metric", "operator", "raw_json", "provider_error"])
def test_invented_or_wrong_conclusion_is_not_saved_and_usage_is_preserved(completed, tmp_path, change):
    frozen, execution, expected = completed
    reply = deepcopy(expected)
    if change == "verdict": reply["criterion_status"] = "not_met" if expected["criterion_status"] == "met" else "met"
    elif change == "scope": reply["scope"] = "future_profit_guaranteed"
    elif change == "invented_metric": reply["return_percent"] = "1000"
    elif change == "operator": reply["return_comparison"] = "equal"
    elif change == "raw_json": reply = "not JSON"
    else: reply = ProviderError("lost", {"output_tokens": 100, "api_cost_usd": "0"})
    provider = Provider(reply)
    with pytest.raises(FeedbackError) as failure:
        analyze_execution(provider, execution, frozen, output_dir=tmp_path / "analyses")
    assert provider.calls == 1 and not (failure.value.directory / "analysis.json").exists()
    assert events(failure.value.directory)[-1]["data"]["usage"]
    with pytest.raises(FeedbackError, match="reservado"):
        analyze_execution(Provider(expected), execution, frozen, output_dir=tmp_path / "retry")


def test_invalid_results_are_rejected_before_model_or_feedback_reservation(completed, tmp_path):
    frozen, execution, expected = completed
    with (execution / "results.json").open("ab") as stream: stream.write(b' ')
    provider = Provider(expected)
    with pytest.raises(FeedbackError):
        analyze_execution(provider, execution, frozen, output_dir=tmp_path / "analyses")
    assert provider.calls == 0 and not (tmp_path / "feedback-access").exists()


def test_results_changed_during_analysis_preserve_response_without_accepted_analysis(completed, tmp_path):
    frozen, execution, expected = completed
    class Mutating(Provider):
        def complete(self, messages, schema):
            result = super().complete(messages, schema)
            with (execution / "report.md").open("ab") as stream: stream.write(b' ')
            return result
    with pytest.raises(FeedbackError) as failure:
        analyze_execution(Mutating(expected), execution, frozen, output_dir=tmp_path / "analyses")
    assert not (failure.value.directory / "analysis.json").exists()
    assert events(failure.value.directory)[-1]["data"]["model_requests"] == 1


def test_inconclusive_results_skip_model_without_losing_python_conclusion(ready, tmp_path, monkeypatch):
    _, frozen, _, _ = ready
    plan = another_plan(ready, tmp_path, threshold=100)
    execution = execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    provider = Provider({})
    monkeypatch.setattr(provider, "describe", lambda: pytest.fail("Sin contactar proveedor"))
    directory = analyze_execution(provider, execution, frozen, output_dir=tmp_path / "analyses")
    result = read_json(directory / "analysis.json")
    assert provider.calls == result["model_requests"] == 0 and result["usage"] == []
    assert result["model_assessment"] is None and result["assessment"]["criterion_status"] == "inconclusive"
    assert result["origin"] == "python_inconclusive_precheck" and result["api_cost_usd"] == "0"


def test_two_concurrent_analyses_only_one_calls_the_model(completed, tmp_path, monkeypatch):
    frozen, execution, expected = completed
    import trading_ai.agent_feedback as feedback
    actual, barrier = feedback._write_exclusive, Barrier(2)
    def simultaneous(path, content):
        if path.parent == tmp_path / "feedback-access": barrier.wait(timeout=15)
        return actual(path, content)
    monkeypatch.setattr(feedback, "_write_exclusive", simultaneous)
    provider = Provider(expected)
    def attempt(index):
        try: return analyze_execution(provider, execution, frozen, output_dir=tmp_path / str(index))
        except FeedbackError as error: return error
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(attempt, (1, 2)))
    assert provider.calls == 1 and sum(isinstance(item, Path) for item in results) == 1


def test_cli_revision_and_readonly_verification(parent, tmp_path, monkeypatch, capsys):
    _, frozen, _, translation, revised = parent
    provider = Provider(revised)
    monkeypatch.setattr("trading_ai.agent_feedback.create_provider", lambda config: provider)
    main(["revise", "--translation-run", str(translation), "--frozen-run", str(frozen), "--output-dir", str(tmp_path / "revisions")])
    directory, = (tmp_path / "revisions").iterdir()
    main(["verify-revision", "--run", str(directory), "--frozen-run", str(frozen)])
    assert provider.calls == 1 and "sin consultar al modelo" in capsys.readouterr().out


def test_openai_remains_disabled_before_creating_a_feedback_attempt(parent, tmp_path, capsys):
    _, frozen, _, translation, _ = parent
    with pytest.raises(SystemExit) as failure:
        main(["revise", "--translation-run", str(translation), "--frozen-run", str(frozen), "--provider", "openai", "--output-dir", str(tmp_path / "revisions")])
    assert failure.value.code == 1 and "OpenAI" in capsys.readouterr().err
    assert not (tmp_path / "revisions").exists() and not (tmp_path / "feedback-access").exists()
