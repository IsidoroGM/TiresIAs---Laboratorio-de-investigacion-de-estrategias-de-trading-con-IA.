"""Consumo único, contabilidad del motor y errores del ejecutor sin proveedor de IA."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json
from pathlib import Path
import shutil
from threading import Barrier

import pytest

from test_discovery import Provider, events, idea, read_json, registered
from test_formalization import proposed
from test_holdout import setup
from test_rule_planning import accepted, reseal, translated
from trading_ai.backtesting import run_backtest
from trading_ai.data import load_ecb_rates
from trading_ai.discovery import discover_idea
from trading_ai.experiments import expected_assessment
from trading_ai.formalization import formalize_idea
from trading_ai.holdout import _policy
from trading_ai.rule_execution import ExecutionError, execute_rule_plan, main, verify_rule_execution
from trading_ai.rule_planning import CHECKS, prepare_rule_plan, review_translation
from trading_ai.rules import compile_rule_strategy
from trading_ai.strategies import create_strategy


@pytest.fixture(autouse=True)
def isolated_access(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.rule_execution.ACCESS_ROOT", tmp_path / "access")


@pytest.fixture
def ready(accepted, tmp_path):
    source, review = accepted
    split, frozen, _, _, _ = source
    plan = prepare_rule_plan(review, frozen, output_dir=tmp_path / "plans")
    return split, frozen, review, plan


def another_plan(ready, tmp_path, *, threshold=1, name="renamed_test"):
    _, frozen, review, _ = ready
    record = read_json(review / "review.json")
    old_translation = read_json(Path(record["translation"]["directory"]) / "translation.json")
    proposal = old_translation["original_proposal"]
    proposal.update(entry_rule=f"Referencia estrictamente mayor que {threshold}.",
                    exit_rule=f"Referencia menor o igual que {threshold}.",
                    parameters=[{"name": "threshold", "value": threshold}])
    reply = old_translation["model_translation"]
    reply["spec"]["name"] = name
    for role in ("entry", "exit"):
        reply["spec"][role]["conditions"][0]["right"]["value"] = str(threshold)
    idea_dir = discover_idea(Provider(proposal), frozen, output_dir=tmp_path / "more-ideas")
    translation = formalize_idea(Provider(reply), idea_dir, frozen, output_dir=tmp_path / "more-translations")
    assessment = {"schema_version": 1, "translation_sha256": sha256((translation / "translation.json").read_bytes()).hexdigest(),
                  "spec_sha256": read_json(translation / "translation.json")["spec_sha256"],
                  "reviewer": "Prueba artificial", "decision": "accepted", "rationale": "Umbral sintético explícito.",
                  "checks": dict.fromkeys(CHECKS, True)}
    new_review = review_translation(translation, frozen, assessment=assessment, output_dir=tmp_path / "more-reviews")
    return prepare_rule_plan(new_review, frozen, output_dir=tmp_path / "more-plans")


def test_exactly_two_backtests_use_same_rates_fixed_controls_and_independent_accounts(ready, tmp_path, monkeypatch):
    split, frozen, review, plan_dir = ready
    original = {p: p.read_bytes() for folder in (split, frozen, review, plan_dir) for p in folder.iterdir()}
    plan = read_json(plan_dir / "plan.json")
    import trading_ai.rule_execution as execution
    actual = execution.run_backtest
    calls = []
    def tracked(rates, signals, pair, **controls):
        claim, = (tmp_path / "access").iterdir()
        run = Path(read_json(claim)["execution_run"])
        assert events(run)[-1]["event"] == "backtest_reserved"
        assert pair == plan["policy"]["pair"]
        assert controls == {"cost_rate": Decimal("0.001"), "initial_capital": Decimal("1000"), "allocation_fraction": Decimal("0.1")}
        calls.append((rates, signals))
        return actual(rates, signals, pair, **controls)
    monkeypatch.setattr(execution, "run_backtest", tracked)
    monkeypatch.setattr("trading_ai.ai.create_provider", lambda *a: pytest.fail("Sin IA"))
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.resolve() != (split / "evaluation.xml").resolve() and path.name != "comparison.json"
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    directory = execute_rule_plan(plan_dir, frozen, output_dir=tmp_path / "executions")
    result = read_json(directory / "results.json")
    assert len(calls) == 2 and calls[0][0] is calls[1][0]
    assert calls[0][0] == tuple(load_ecb_rates(split / "development.xml", "EUR/USD"))
    policy = _policy(plan["policy"])
    strategies = (create_strategy("sma", 2, 4), compile_rule_strategy(plan["candidate"]["spec"]))
    for role, strategy in zip(("baseline", "candidate"), strategies):
        raw = read_json(directory / (role + ".json"))
        expected = actual(calls[0][0], strategy.generate_signals([p for _, p in calls[0][0]]), policy.pair,
                          cost_rate=policy.cost_rate, initial_capital=policy.initial_capital,
                          allocation_fraction=policy.allocation_fraction)
        assert raw["backtest"] == json.loads(json.dumps(asdict(expected), default=str))
        assert result[role] == raw["summary"]
        for trade in raw["backtest"]["closed_trades"]:
            assert trade["position"]["entry_date"] > trade["position"]["entry_signal_date"]
            assert trade["exit_date"] > trade["exit_signal_date"]
    assert result["completed_backtests"] == ["baseline", "candidate"]
    assert result["reserved_backtests"] == {"baseline": 1, "candidate": 1}
    assert result["assessment"]["criterion_status"] == {"supported_in_sample": "met", "not_supported_in_sample": "not_met",
                                                         "inconclusive": "inconclusive"}[expected_assessment(result)["verdict"]]
    assert result["assessment"]["scope"] == "known_development_history_only"
    assert result["model_requests"] == 0 and result["api_cost_usd"] == "0" and result["usage"] == []
    assert events(directory)[-1]["event"] == "execution_completed"
    assert verify_rule_execution(directory, frozen) == result
    assert "no es evidencia inédita" in (directory / "report.md").read_text(encoding="utf-8")
    monkeypatch.undo()
    assert all(path.read_bytes() == raw for path, raw in original.items())


@pytest.mark.parametrize("copy_kind", ["same", "copy", "prepared_again", "new_review_and_name"])
def test_repeated_calculations_blocked_across_output_dirs_copies_and_names(ready, tmp_path, copy_kind, monkeypatch):
    _, frozen, review, plan = ready
    first = execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    raw = (first / "results.json").read_bytes()
    if copy_kind == "copy":
        shutil.copytree(plan, tmp_path / "copy")
        plan = tmp_path / "copy"
    elif copy_kind == "prepared_again": plan = prepare_rule_plan(review, frozen, output_dir=tmp_path / "other-plans")
    elif copy_kind == "new_review_and_name": plan = another_plan(ready, tmp_path)
    monkeypatch.setattr("trading_ai.rule_execution.run_backtest", lambda *a, **k: pytest.fail("No repetir"))
    with pytest.raises(ExecutionError, match="reservado") as failure:
        execute_rule_plan(plan, frozen, output_dir=tmp_path / "other-executions")
    assert events(failure.value.directory)[-1]["data"]["access_claimed"] is False
    assert len(list((tmp_path / "access").iterdir())) == 1
    assert (first / "results.json").read_bytes() == raw


@pytest.mark.parametrize("bad_role", ["baseline", "candidate"])
def test_engine_failure_preserves_partial_results_consumes_attempt_without_retry(ready, tmp_path, bad_role, monkeypatch):
    _, frozen, _, plan = ready
    import trading_ai.rule_execution as execution
    actual, calls = execution.run_backtest, []
    def fail(rates, signals, pair, **kwargs):
        calls.append(1)
        if len(calls) == (1 if bad_role == "baseline" else 2): raise RuntimeError("Fallo del motor de prueba")
        return actual(rates, signals, pair, **kwargs)
    monkeypatch.setattr(execution, "run_backtest", fail)
    with pytest.raises(ExecutionError, match="Fallo del motor") as failure:
        execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    directory = failure.value.directory
    log = events(directory)[-1]
    assert log["event"] == "execution_failed" and log["data"]["access_claimed"] is True
    assert log["data"]["error_type"] == "RuntimeError"
    assert not (directory / "results.json").exists() and not (directory / "report.md").exists()
    assert (directory / "baseline.json").exists() == (bad_role == "candidate")
    count = len(calls)
    with pytest.raises(ExecutionError, match="reservado"):
        execute_rule_plan(plan, frozen, output_dir=tmp_path / "retry")
    assert len(calls) == count


def test_loading_failure_after_reservation_blocks_retry_without_backtests(ready, tmp_path, monkeypatch):
    _, frozen, _, plan = ready
    monkeypatch.setattr("trading_ai.rule_execution.load_ecb_rates", lambda *a: (_ for _ in ()).throw(ValueError("XML test")))
    monkeypatch.setattr("trading_ai.rule_execution.run_backtest", lambda *a, **k: pytest.fail("No calcular"))
    with pytest.raises(ExecutionError, match="XML test") as failure:
        execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    assert events(failure.value.directory)[-1]["data"]["reserved_backtests"] == {"baseline": 0, "candidate": 0}
    with pytest.raises(ExecutionError, match="reservado"):
        execute_rule_plan(plan, frozen, output_dir=tmp_path / "retry")


@pytest.mark.parametrize("mutation", ["plan_data", "review", "code", "claim", "snapshot"])
def test_changes_during_calculation_stop_second_backtest_and_completion(ready, tmp_path, mutation, monkeypatch):
    _, frozen, review, plan = ready
    import trading_ai.rule_execution as execution
    actual, code_hashes = execution.run_backtest, execution._code_hashes
    changed, calls = False, []
    def hashes():
        result = code_hashes()
        if changed and mutation == "code": result["rule_execution.py"] = "changed"
        return result
    monkeypatch.setattr(execution, "_code_hashes", hashes)
    def mutate(rates, signals, pair, **kwargs):
        nonlocal changed
        calls.append(1)
        result = actual(rates, signals, pair, **kwargs)
        claim, = (tmp_path / "access").iterdir()
        if mutation == "code": changed = True
        else:
            target = {"plan_data": plan / "development.xml", "review": review / "review.json", "claim": claim,
                      "snapshot": Path(read_json(claim)["execution_run"]) / "development.xml"}[mutation]
            with target.open("ab") as stream: stream.write(b' ')
        return result
    monkeypatch.setattr(execution, "run_backtest", mutate)
    with pytest.raises(ExecutionError) as failure:
        execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    assert len(calls) == 1 and (failure.value.directory / "baseline.json").exists()
    assert not (failure.value.directory / "results.json").exists()
    assert not (failure.value.directory / "report.md").exists()
    assert events(failure.value.directory)[-1]["event"] == "execution_failed"


@pytest.mark.parametrize("field", ["budget", "policy", "candidate", "permission"])
def test_modified_plan_rejected_before_claim_or_calculation(ready, tmp_path, field, monkeypatch):
    _, frozen, _, directory = ready
    plan = read_json(directory / "plan.json")
    if field == "budget": plan["budget"]["candidate_backtests"] = 99
    elif field == "policy": plan["policy"]["cost_rate"] = "0"
    elif field == "candidate": plan["candidate"]["spec"]["name"] = "changed"
    else: plan["executable"] = True
    reseal(directory, "plan.json", "plan_registered", plan)
    monkeypatch.setattr("trading_ai.rule_execution.run_backtest", lambda *a, **k: pytest.fail("Sin calcular"))
    with pytest.raises(ExecutionError) as failure:
        execute_rule_plan(directory, frozen, output_dir=tmp_path / "executions")
    assert not (tmp_path / "access").exists()
    assert events(failure.value.directory)[-1]["data"]["access_claimed"] is False


def test_concurrent_attempts_only_one_reserves_and_computes(ready, tmp_path, monkeypatch):
    _, frozen, _, plan = ready
    import trading_ai.rule_execution as execution
    write, barrier = execution._write_exclusive, Barrier(2)
    def simultaneous(path, content):
        if path.parent == tmp_path / "access": barrier.wait(timeout=15)
        return write(path, content)
    monkeypatch.setattr(execution, "_write_exclusive", simultaneous)
    def attempt(index):
        try: return execute_rule_plan(plan, frozen, output_dir=tmp_path / str(index))
        except ExecutionError as error: return error
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, (1, 2)))
    assert sum(isinstance(result, Path) for result in results) == 1
    assert sum(isinstance(result, ExecutionError) for result in results) == 1
    assert len(list((tmp_path / "access").iterdir())) == 1
    complete = next(result for result in results if isinstance(result, Path))
    assert read_json(complete / "results.json")["completed_backtests"] == ["baseline", "candidate"]


def test_no_closed_trades_remains_inconclusive_without_forcing_a_winner(ready, tmp_path):
    _, frozen, _, _ = ready
    plan = another_plan(ready, tmp_path, threshold=100)
    directory = execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    result = read_json(directory / "results.json")
    assert result["candidate"]["closed_trades"] == 0
    assert result["candidate"]["final_equity"] == "1000"
    assert result["assessment"]["criterion_status"] == "inconclusive"


def test_decimal_context_is_preserved_and_results_do_not_depend_on_low_precision(ready, tmp_path):
    _, frozen, _, plan = ready
    policy = _policy(read_json(plan / "plan.json")["policy"])
    rates = load_ecb_rates(plan / "development.xml", policy.pair)
    strategy = create_strategy("sma", 2, 4)
    expected = run_backtest(rates, strategy.generate_signals([p for _, p in rates]), policy.pair,
                            cost_rate=policy.cost_rate, initial_capital=policy.initial_capital,
                            allocation_fraction=policy.allocation_fraction)
    with localcontext() as context:
        context.prec, context.rounding = 6, ROUND_DOWN
        directory = execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
        assert context.prec == 6 and context.rounding == ROUND_DOWN
    assert read_json(directory / "baseline.json")["backtest"] == json.loads(json.dumps(asdict(expected), default=str))


def test_abrupt_interruption_does_not_release_reservation(ready, tmp_path, monkeypatch):
    _, frozen, _, plan = ready
    monkeypatch.setattr("trading_ai.rule_execution.run_backtest", lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    assert len(list((tmp_path / "access").iterdir())) == 1
    with pytest.raises(ExecutionError, match="reservado"):
        execute_rule_plan(plan, frozen, output_dir=tmp_path / "retry")


def test_cli_runs_and_reports_errors_without_allowing_control_overrides(ready, tmp_path, capsys):
    _, frozen, _, plan = ready
    args = ["--plan-run", str(plan), "--frozen-run", str(frozen), "--output-dir", str(tmp_path / "executions")]
    main(args)
    assert "Ejecución completada" in capsys.readouterr().out
    run, = (tmp_path / "executions").iterdir()
    main(["--verify-run", str(run), "--frozen-run", str(frozen)])
    assert "sin recalcular" in capsys.readouterr().out
    with pytest.raises(SystemExit) as failure: main(args)
    assert failure.value.code == 1 and "reservado" in capsys.readouterr().err
    with pytest.raises(SystemExit) as failure: main(args + ["--max-backtests", "99"])
    assert failure.value.code == 2


@pytest.mark.parametrize("name", ["baseline.json", "candidate.json", "development.xml", "report.md", "results.json", "events.jsonl", "claim"])
def test_readonly_verification_detects_changed_evidence_without_new_calculations(ready, tmp_path, monkeypatch, name):
    _, frozen, _, plan = ready
    directory = execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    if name == "claim": target, = (tmp_path / "access").iterdir()
    else: target = directory / name
    with target.open("ab") as stream: stream.write(b' ')
    monkeypatch.setattr("trading_ai.rule_execution.run_backtest", lambda *a, **k: pytest.fail("Solo leer"))
    with pytest.raises((ValueError, KeyError, TypeError)):
        verify_rule_execution(directory, frozen)


def test_report_write_failure_does_not_make_saved_results_a_completed_execution(ready, tmp_path, monkeypatch):
    _, frozen, _, plan = ready
    import trading_ai.rule_execution as execution
    write = execution._write_exclusive
    def failed(path, content):
        if path.name == "report.md": raise OSError("Report write test")
        return write(path, content)
    monkeypatch.setattr(execution, "_write_exclusive", failed)
    with pytest.raises(ExecutionError, match="Report write") as failure:
        execute_rule_plan(plan, frozen, output_dir=tmp_path / "executions")
    assert (failure.value.directory / "results.json").exists()
    assert events(failure.value.directory)[-1]["event"] == "execution_failed"
    with pytest.raises(ValueError, match="cierre"):
        verify_rule_execution(failure.value.directory, frozen)
