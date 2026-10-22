"""Revisión y planes previos: sin autoaprobación, llamadas de IA ni backtests."""

from hashlib import sha256
import json
from pathlib import Path

import pytest

from test_discovery import Provider, events, idea, read_json, registered
from test_formalization import proposed
from test_holdout import setup
from trading_ai.discovery import discover_idea
from trading_ai.formalization import formalize_idea
from trading_ai.rule_planning import (BUDGET, CHECKS, PlanningError, main, prepare_rule_plan,
                                     review_translation, verify_review, verify_rule_plan)


@pytest.fixture
def translated(registered, tmp_path, idea, proposed):
    split, frozen = registered
    # Ejemplo artificial del contrato; no es una estrategia elegida sobre datos.
    idea.update(entry_rule="Referencia estrictamente mayor que 1.", exit_rule="Referencia menor o igual que 1.",
                parameters=[{"name": "threshold", "value": 1}])
    queued = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    translation = formalize_idea(Provider(proposed), queued, frozen, output_dir=tmp_path / "translations")
    assessment = {"schema_version": 1, "translation_sha256": sha256((translation / "translation.json").read_bytes()).hexdigest(),
                  "spec_sha256": read_json(translation / "translation.json")["spec_sha256"],
                  "reviewer": "Revisión técnica de prueba", "decision": "accepted",
                  "rationale": "El ejemplo sintético usa el umbral y los operadores declarados.",
                  "checks": dict.fromkeys(CHECKS, True)}
    return split, frozen, queued, translation, assessment


@pytest.fixture
def accepted(translated, tmp_path):
    _, frozen, _, translation, assessment = translated
    review = review_translation(translation, frozen, assessment=assessment, output_dir=tmp_path / "reviews")
    return translated, review


def test_review_and_plan_preserve_sources_without_ai_signals_or_outer_data(translated, tmp_path, monkeypatch):
    split, frozen, idea_dir, translation, assessment = translated
    before = {p: p.read_bytes() for folder in (split, frozen, idea_dir, translation) for p in folder.iterdir()}
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.resolve() != (split / "evaluation.xml").resolve()
        assert path.name != "comparison.json"
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr("trading_ai.rules.RuleStrategy.generate_signals", lambda *a: pytest.fail("Sin señales"))
    monkeypatch.setattr("trading_ai.experiments.run_backtest", lambda *a, **k: pytest.fail("Sin simulación"))
    monkeypatch.setattr("trading_ai.ai.OllamaProvider.complete", lambda *a, **k: pytest.fail("Sin IA"))
    review = review_translation(translation, frozen, assessment=assessment, output_dir=tmp_path / "reviews")
    reviewed = verify_review(review, frozen)
    assert reviewed["status"] == "accepted" and reviewed["eligible_for_plan"] is True
    assert reviewed["assessment"] == assessment and reviewed["executable"] is False
    plan_dir = prepare_rule_plan(review, frozen, output_dir=tmp_path / "plans")
    plan = verify_rule_plan(plan_dir, frozen)
    fixed = read_json(frozen / "frozen.json")
    assert plan["policy"] == fixed["policy"] and plan["criterion"] == fixed["proposal"]["criterion"]
    assert plan["candidate"]["spec"] == read_json(translation / "translation.json")["spec"]
    assert plan["baseline"] == {"strategy": "sma", "fast_window": 2, "slow_window": 4}
    assert plan["budget"] == BUDGET and plan["budget"]["candidate_backtests"] + plan["budget"]["baseline_backtests"] == 2
    assert plan["scope"] == "known_development_history_only" and plan["outer_evaluation_allowed"] is False
    assert plan["stage"] == "registered_not_run" and plan["executable"] is False
    assert plan["calculated_results"] is None and plan["model_requests"] == 0 and plan["api_cost_usd"] == "0"
    assert (plan_dir / "development.xml").read_bytes() == before[split / "development.xml"]
    assert events(plan_dir)[-1]["event"] == "plan_registered"
    monkeypatch.undo()
    assert all(path.read_bytes() == raw for path, raw in before.items())


def test_no_assessment_does_not_autoapprove_proposed_rules(translated, tmp_path):
    _, frozen, _, translation, _ = translated
    with pytest.raises(PlanningError, match="Revisión") as failure:
        review_translation(translation, frozen, output_dir=tmp_path / "reviews")
    assert not (failure.value.directory / "review.json").exists()
    assert events(failure.value.directory)[-1]["event"] == "review_failed"


@pytest.mark.parametrize("decision", ["needs_clarification", "rejected"])
def test_nonaccepting_reviews_cannot_prepare_plans(translated, tmp_path, decision):
    _, frozen, _, translation, assessment = translated
    assessment["decision"] = decision
    assessment["checks"]["exit_matches"] = False
    review = review_translation(translation, frozen, assessment=assessment, output_dir=tmp_path / "reviews")
    assert verify_review(review, frozen)["eligible_for_plan"] is False
    with pytest.raises(PlanningError, match="aceptada") as failure:
        prepare_rule_plan(review, frozen, output_dir=tmp_path / "plans")
    assert not (failure.value.directory / "plan.json").exists()
    assert not (failure.value.directory / "development.xml").exists()


@pytest.mark.parametrize("status", ["needs_clarification", "unsupported", "needs_data"])
def test_untranslated_ideas_get_automatic_blocked_records_not_approval(registered, tmp_path, idea, status):
    _, frozen = registered
    if status == "needs_data": idea["data_requirements"]["ohlc"] = True
    queued = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    translation = formalize_idea(Provider({"status": status, "reason": "Falta concretar.", "spec": None}), queued,
                                frozen, output_dir=tmp_path / "translations")
    review = review_translation(translation, frozen, output_dir=tmp_path / "reviews")
    record = verify_review(review, frozen)
    assert record["status"] == "blocked_by_translation" and record["assessment"] is None
    assert record["spec_sha256"] is None and record["eligible_for_plan"] is False
    with pytest.raises(PlanningError):
        prepare_rule_plan(review, frozen, output_dir=tmp_path / "plans")
    with pytest.raises(PlanningError, match="sin reglas"):
        review_translation(translation, frozen, assessment={}, output_dir=tmp_path / "reviews")


@pytest.mark.parametrize("change", ["false_check", "missing_check", "extra_check", "numeric_check", "wrong_translation",
                                    "wrong_spec", "extra_control", "extra_permission", "empty_reviewer", "long_rationale",
                                    "wrong_decision", "version", "missing_field"])
def test_invalid_assessments_cannot_override_review_controls(translated, tmp_path, change):
    _, frozen, _, translation, assessment = translated
    if change == "false_check": assessment["checks"]["entry_matches"] = False
    elif change == "missing_check": del assessment["checks"]["entry_matches"]
    elif change == "extra_check": assessment["checks"]["profitable"] = True
    elif change == "numeric_check": assessment["checks"]["entry_matches"] = 1
    elif change == "wrong_translation": assessment["translation_sha256"] = "0" * 64
    elif change == "wrong_spec": assessment["spec_sha256"] = "0" * 64
    elif change == "extra_control": assessment["cost_rate"] = "0"
    elif change == "extra_permission": assessment["executable"] = True
    elif change == "empty_reviewer": assessment["reviewer"] = " "
    elif change == "long_rationale": assessment["rationale"] = "a" * 1201
    elif change == "wrong_decision": assessment["decision"] = "approved_by_model"
    elif change == "version": assessment["schema_version"] = True
    else: del assessment["rationale"]
    with pytest.raises(PlanningError) as failure:
        review_translation(translation, frozen, assessment=assessment, output_dir=tmp_path / "reviews")
    assert not (failure.value.directory / "review.json").exists()


@pytest.mark.parametrize("change", ["raw_reply", "status", "spec", "permission", "unfinished", "origin"])
def test_changed_translation_is_rejected_before_review(translated, tmp_path, change):
    _, frozen, _, translation, assessment = translated
    record = read_json(translation / "translation.json")
    if change == "raw_reply":
        log = events(translation)
        next(event for event in log if event["event"] == "model_response")["data"]["content"] = '{}'
        (translation / "events.jsonl").write_text(''.join(json.dumps(item) + '\n' for item in log), encoding="utf-8")
    elif change == "unfinished":
        (translation / "events.jsonl").write_text(''.join(json.dumps(item) + '\n' for item in events(translation)[:-1]), encoding="utf-8")
    else:
        if change == "status": record["status"] = "approved"
        elif change == "spec": record["spec"]["name"] = "changed"
        elif change == "permission": record["executable"] = True
        else: record["source"]["idea_id"] = "changed"
        (translation / "translation.json").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(PlanningError):
        review_translation(translation, frozen, assessment=assessment, output_dir=tmp_path / "reviews")


def reseal(directory, filename, closing, value):
    path = directory / filename
    path.write_text(json.dumps(value), encoding="utf-8")
    checksum = sha256(path.read_bytes()).hexdigest()
    (directory / (filename + ".sha256")).write_text(checksum, encoding="ascii")
    log = events(directory)
    assert log[-1]["event"] == closing
    log[-1]["data"]["sha256"] = checksum
    (directory / "events.jsonl").write_text(''.join(json.dumps(item) + '\n' for item in log), encoding="utf-8")


@pytest.mark.parametrize("change", ["seal", "closed", "assessment", "source"])
def test_stale_or_tampered_reviews_cannot_prepare_plan(accepted, tmp_path, change):
    translated, review = accepted
    _, frozen, _, translation, _ = translated
    if change == "seal": (review / "review.json.sha256").write_text("wrong", encoding="ascii")
    elif change == "closed": (review / "events.jsonl").write_text("", encoding="utf-8")
    elif change == "assessment":
        record = read_json(review / "review.json")
        record["assessment"]["checks"]["parameters_match"] = False
        reseal(review, "review.json", "review_completed", record)
    else:
        with (translation / "translation.json").open("a", encoding="utf-8") as stream: stream.write(" ")
    with pytest.raises(PlanningError):
        prepare_rule_plan(review, frozen, output_dir=tmp_path / "plans")


@pytest.mark.parametrize("change", ["budget", "criterion", "capital", "candidate", "base", "outer", "execution",
                                    "scope", "results", "data", "code", "boolean"])
def test_plan_verification_rejects_changes_even_with_a_recomputed_seal(accepted, tmp_path, change):
    translated, review = accepted
    _, frozen, _, _, _ = translated
    directory = prepare_rule_plan(review, frozen, output_dir=tmp_path / "plans")
    plan = read_json(directory / "plan.json")
    if change == "budget": plan["budget"]["candidate_backtests"] = 100
    elif change == "criterion": plan["criterion"] = "profit_only"
    elif change == "capital": plan["policy"]["initial_capital"] = "999999"
    elif change == "candidate": plan["candidate"]["spec"]["name"] = "altered"
    elif change == "base": plan["baseline"]["fast_window"] = 100
    elif change == "outer": plan["outer_evaluation_allowed"] = True
    elif change == "execution": plan["execution_timing"] = "same_observation"
    elif change == "scope": plan["scope"] = "unseen_validation"
    elif change == "results": plan["calculated_results"] = {"return": "100"}
    elif change == "code": plan["code_sha256"]["rules.py"] = "0" * 64
    elif change == "boolean": plan["executable"] = 0
    else: (directory / "development.xml").write_bytes(b'changed')
    reseal(directory, "plan.json", "plan_registered", plan)
    with pytest.raises(ValueError):
        verify_rule_plan(directory, frozen)


def test_failed_write_keeps_error_without_complete_plan(accepted, tmp_path, monkeypatch):
    translated, review = accepted
    _, frozen, _, _, _ = translated
    monkeypatch.setattr("trading_ai.rule_planning._write_exclusive", lambda *a: (_ for _ in ()).throw(OSError("disk test")))
    with pytest.raises(PlanningError, match="disk test") as failure:
        prepare_rule_plan(review, frozen, output_dir=tmp_path / "plans")
    assert events(failure.value.directory)[-1]["event"] == "plan_preparation_failed"
    with pytest.raises((ValueError, OSError)):
        verify_rule_plan(failure.value.directory, frozen)


def test_repeated_preparation_preserves_previous_record_and_does_not_execute(accepted, tmp_path):
    translated, review = accepted
    _, frozen, _, _, _ = translated
    first = prepare_rule_plan(review, frozen, output_dir=tmp_path / "plans")
    raw = (first / "plan.json").read_bytes()
    second = prepare_rule_plan(review, frozen, output_dir=tmp_path / "plans")
    assert first != second and (first / "plan.json").read_bytes() == raw
    assert verify_rule_plan(second, frozen)["calculated_results"] is None


def test_cli_review_prepare_and_verify(translated, tmp_path, capsys):
    _, frozen, _, translation, assessment = translated
    path = tmp_path / "assessment.json"
    path.write_text(json.dumps(assessment), encoding="utf-8")
    main(["review", "--translation-run", str(translation), "--assessment", str(path),
          "--frozen-run", str(frozen), "--output-dir", str(tmp_path / "reviews")])
    review, = (tmp_path / "reviews").iterdir()
    main(["verify-review", "--run", str(review), "--frozen-run", str(frozen)])
    main(["prepare", "--review-run", str(review), "--frozen-run", str(frozen), "--output-dir", str(tmp_path / "plans")])
    plan, = (tmp_path / "plans").iterdir()
    main(["verify-plan", "--run", str(plan), "--frozen-run", str(frozen)])
    assert "sin ejecutar" in capsys.readouterr().out
    assert verify_rule_plan(plan, frozen)["budget"]["max_model_requests"] == 0


def test_cli_rejects_unknown_budget_overrides(translated, capsys):
    _, frozen, _, _, _ = translated
    with pytest.raises(SystemExit) as failure:
        main(["prepare", "--review-run", "test", "--frozen-run", str(frozen), "--max-backtests", "100"])
    assert failure.value.code == 2
