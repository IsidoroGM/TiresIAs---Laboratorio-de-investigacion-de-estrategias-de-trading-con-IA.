"""Origen estructurado, revisión independiente, planes inmutables y dos cálculos controlados."""

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

import pytest

from test_discovery import Provider, events, read_json, registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from trading_ai import rule_execution as engine
from trading_ai.rule_planning import _canonical
from trading_ai.structured_execution import (StructuredExecutionError, execute_structured_plan, verify_structured_execution)
from trading_ai.structured_ideas import propose_structured_idea
from trading_ai.structured_planning import (CHECKS, StructuredPlanningError, prepare_structured_plan,
                                          review_structured_idea, verify_structured_plan, verify_structured_review)


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr("trading_ai.structured_ideas.ACCESS_ROOT", tmp_path / "ideas-access")
    monkeypatch.setattr("trading_ai.rule_execution.ACCESS_ROOT", tmp_path / "execution-access")


def assessment_for(directory, decision="accepted"):
    return {"schema_version": 1, "proposal_sha256": sha256((directory / "proposal.json").read_bytes()).hexdigest(),
            "spec_sha256": read_json(directory / "proposal.json")["spec_sha256"], "reviewer": "Revisión del ejemplo artificial",
            "decision": decision, "rationale": "Umbral sintético explícito: entrada >1 y salida <=1 sin retardo adicional.",
            "checks": dict.fromkeys(CHECKS, True)}


@pytest.fixture
def reviewed(generated, tmp_path):
    split, frozen, directory, _ = generated
    assessment = assessment_for(directory)
    review = review_structured_idea(directory, frozen, assessment=assessment, output_dir=tmp_path / "reviews")
    return split, frozen, directory, review


@pytest.fixture
def ready(reviewed, tmp_path):
    split, frozen, directory, review = reviewed
    plan = prepare_structured_plan(review, frozen, output_dir=tmp_path / "plans")
    return split, frozen, directory, review, plan


def test_review_is_explicit_and_plan_fixes_original_controls_without_calculating(generated, tmp_path, monkeypatch):
    split, frozen, directory, _ = generated
    for method in ("trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.experiments.run_backtest",
                   "trading_ai.ai.OllamaProvider.complete"):
        monkeypatch.setattr(method, lambda *a, **k: pytest.fail("No calcular ni consultar IA"))
    original_open = Path.open
    def guarded(path, *a, **k):
        assert path.name not in ("evaluation.xml", "comparison.json")
        return original_open(path, *a, **k)
    monkeypatch.setattr(Path, "open", guarded)
    with pytest.raises(StructuredPlanningError):
        review_structured_idea(directory, frozen, output_dir=tmp_path / "invalid")
    review = review_structured_idea(directory, frozen, assessment=assessment_for(directory), output_dir=tmp_path / "reviews")
    assert verify_structured_review(review, frozen)["status"] == "accepted"
    plan = prepare_structured_plan(review, frozen, output_dir=tmp_path / "plans")
    record = verify_structured_plan(plan, frozen)
    frozen_record = read_json(frozen / "frozen.json")
    assert record["policy"] == frozen_record["policy"] and record["criterion"] == frozen_record["proposal"]["criterion"]
    assert record["candidate"]["spec"] == read_json(directory / "proposal.json")["spec"]
    assert record["budget"]["baseline_backtests"] == record["budget"]["candidate_backtests"] == 1
    assert record["executable"] is False and record["outer_evaluation_allowed"] is False
    assert (plan / "development.xml").read_bytes() == (split / "development.xml").read_bytes()


@pytest.mark.parametrize("change", ["wrong_proposal", "wrong_spec", "version", "missing_lags", "false_lags", "numeric_check",
                                    "empty_reviewer", "extra_permission", "decision"])
def test_bad_or_incomplete_assessment_cannot_approve(generated, tmp_path, change):
    _, frozen, directory, _ = generated
    assessment = assessment_for(directory)
    if change == "wrong_proposal": assessment["proposal_sha256"] = "wrong"
    elif change == "wrong_spec": assessment["spec_sha256"] = "wrong"
    elif change == "version": assessment["schema_version"] = True
    elif change == "missing_lags": assessment["checks"].pop("lags_understood")
    elif change == "false_lags": assessment["checks"]["lags_understood"] = False
    elif change == "numeric_check": assessment["checks"]["data_sufficient"] = 1
    elif change == "empty_reviewer": assessment["reviewer"] = " "
    elif change == "extra_permission": assessment["execute_now"] = True
    else: assessment["decision"] = "autoaccept"
    with pytest.raises(StructuredPlanningError):
        review_structured_idea(directory, frozen, assessment=assessment, output_dir=tmp_path / "reviews")


@pytest.mark.parametrize("decision", ["rejected", "needs_clarification"])
def test_unclear_timing_or_rejected_hypothesis_stops_before_plan(generated, tmp_path, decision):
    _, frozen, directory, _ = generated
    assessment = assessment_for(directory, decision)
    assessment["checks"]["lags_understood"] = False
    assessment["rationale"] = "El retardo adicional no está justificado por la hipótesis."
    review = review_structured_idea(directory, frozen, assessment=assessment, output_dir=tmp_path / "reviews")
    assert verify_structured_review(review, frozen)["eligible_for_plan"] is False
    with pytest.raises(StructuredPlanningError, match="aceptada"):
        prepare_structured_plan(review, frozen, output_dir=tmp_path / "plans")


def test_duplicate_cannot_be_converted_into_an_accepted_review(generated, proposal, tmp_path):
    _, frozen, _, _ = generated
    duplicate = propose_structured_idea(Provider(proposal), frozen, output_dir=tmp_path / "more")
    with pytest.raises(StructuredPlanningError, match="duplicada"):
        review_structured_idea(duplicate, frozen, assessment=assessment_for(duplicate), output_dir=tmp_path / "reviews")
    review = review_structured_idea(duplicate, frozen, output_dir=tmp_path / "blocked")
    assert verify_structured_review(review, frozen)["status"] == "blocked_proposal"


@pytest.mark.parametrize("field", ["criterion", "policy", "budget", "candidate", "outer"])
def test_resealed_plan_still_cannot_change_experiment_controls(ready, field):
    _, frozen, _, _, plan = ready
    record = read_json(plan / "plan.json")
    if field == "criterion": record["criterion"] = "other_criterion"
    elif field == "policy": record["policy"]["initial_capital"] = "999999"
    elif field == "budget": record["budget"]["candidate_backtests"] = 100
    elif field == "candidate": record["candidate"]["spec"]["entry"]["conditions"][0]["operator"] = "lt"
    else: record["outer_evaluation_allowed"] = True
    path = plan / "plan.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    checksum = sha256(path.read_bytes()).hexdigest()
    (plan / "plan.json.sha256").write_text(checksum, encoding="ascii")
    log = events(plan)
    log[-1]["data"]["sha256"] = checksum
    (plan / "events.jsonl").write_text("\n".join(json.dumps(item) for item in log) + "\n", encoding="utf-8")
    with pytest.raises(ValueError): verify_structured_plan(plan, frozen)


def test_execution_has_two_independent_accounts_same_rates_fixed_controls_and_python_conclusion(ready, tmp_path, monkeypatch):
    split, frozen, _, _, plan = ready
    actual = engine.run_backtest
    calls = []
    def tracked(rates, signals, pair, **controls):
        assert len(list((tmp_path / "execution-access").glob("*.json"))) == 1
        assert controls == {"cost_rate": Decimal("0.001"), "initial_capital": Decimal("1000"), "allocation_fraction": Decimal("0.1")}
        calls.append((rates, signals, pair))
        return actual(rates, signals, pair, **controls)
    monkeypatch.setattr(engine, "run_backtest", tracked)
    original_open = Path.open
    def guarded(path, *a, **k):
        assert path.name not in ("evaluation.xml", "comparison.json")
        return original_open(path, *a, **k)
    monkeypatch.setattr(Path, "open", guarded)
    run = execute_structured_plan(plan, frozen, output_dir=tmp_path / "executions")
    record = verify_structured_execution(run, frozen)
    assert len(calls) == 2 and calls[0][0] is calls[1][0]
    assert record["reserved_backtests"] == {"baseline": 1, "candidate": 1}
    assert record["completed_backtests"] == ["baseline", "candidate"]
    assert record["assessment"] == engine._assessment(record) and record["assessment"]["origin"] == "python"
    assert record["model_requests"] == 0 and record["api_cost_usd"] == "0"
    assert record["artifacts_sha256"]["development.xml"] == read_json(plan / "plan.json")["data"]["sha256"]
    monkeypatch.setattr(engine, "run_backtest", lambda *a, **k: pytest.fail("No recalcular al verificar"))
    assert verify_structured_execution(run, frozen) == record


def test_a_new_plan_folder_does_not_release_another_calculation_attempt(ready, tmp_path):
    _, frozen, _, review, first = ready
    execute_structured_plan(first, frozen, output_dir=tmp_path / "executions")
    second = prepare_structured_plan(review, frozen, output_dir=tmp_path / "new-plans")
    with pytest.raises(StructuredExecutionError, match="intento reservado"):
        execute_structured_plan(second, frozen, output_dir=tmp_path / "again")


def test_reservation_namespace_is_shared_with_legacy_executor(ready, tmp_path, monkeypatch):
    _, frozen, _, _, plan = ready
    identity = engine._identity(verify_structured_plan(plan, frozen))
    path = tmp_path / "execution-access" / (sha256(_canonical(identity)).hexdigest() + ".json")
    path.parent.mkdir()
    path.write_text('{"legacy_attempt":"consumed"}', encoding="utf-8")
    monkeypatch.setattr(engine, "_calculate", lambda *a: pytest.fail("No ejecutar un cálculo ya reservado"))
    with pytest.raises(StructuredExecutionError, match="intento reservado"):
        execute_structured_plan(plan, frozen, output_dir=tmp_path / "executions")
    assert path.read_text(encoding="utf-8") == '{"legacy_attempt":"consumed"}'


def test_engine_failure_keeps_reserved_budget_and_never_retries(ready, tmp_path, monkeypatch):
    _, frozen, _, _, plan = ready
    calls = []
    def failed(*args):
        calls.append(1)
        raise RuntimeError("Fallo artificial del motor")
    monkeypatch.setattr(engine, "_calculate", failed)
    with pytest.raises(StructuredExecutionError) as failure:
        execute_structured_plan(plan, frozen, output_dir=tmp_path / "executions")
    close = events(failure.value.directory)[-1]["data"]
    assert close["access_claimed"] is True and close["reserved_backtests"] == {"baseline": 1, "candidate": 0}
    with pytest.raises(StructuredExecutionError, match="intento reservado"):
        execute_structured_plan(plan, frozen, output_dir=tmp_path / "again")
    assert calls == [1]


@pytest.mark.parametrize("filename", ["results.json", "report.md", "candidate.json", "baseline.json", "development.xml"])
def test_changed_execution_cannot_be_verified(ready, tmp_path, filename):
    _, frozen, _, _, plan = ready
    run = execute_structured_plan(plan, frozen, output_dir=tmp_path / "executions")
    with (run / filename).open("ab") as stream: stream.write(b' ')
    with pytest.raises(ValueError): verify_structured_execution(run, frozen)
