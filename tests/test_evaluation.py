"""Evaluación fijada, cuentas independientes y registro de accesos sin IA."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

# Reutiliza la preparación del flujo desarrollo -> investigación de estos tests.
from test_holdout import setup
from trading_ai.evaluation import EvaluationError, evaluate_frozen_proposal, main
from trading_ai.experiments import run_experiment
from trading_ai.holdout import freeze_proposal
from trading_ai.strategies import Signal
from trading_ai.validation import NAMESPACE


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def events(directory):
    return [json.loads(line) for line in (directory / "events.jsonl").read_bytes().splitlines()]


@pytest.fixture(autouse=True)
def isolated_access(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.evaluation.ACCESS_ROOT", tmp_path / "access")


@pytest.fixture
def frozen_setup(setup, tmp_path):
    split, research, _ = setup
    frozen = freeze_proposal(split, research, tmp_path / "frozen")
    return split, research, frozen


def test_evaluation_uses_fixed_parameters_and_separate_blocks_without_ai(frozen_setup, tmp_path, monkeypatch):
    split, research, frozen = frozen_setup
    original = {p: p.read_bytes() for folder in (split, research, frozen) for p in folder.iterdir()}
    fixed = read_json(frozen / "frozen.json")
    monkeypatch.setattr("trading_ai.ai.create_provider", lambda *args: pytest.fail("Sin IA"))
    import trading_ai.evaluation as evaluation
    actual = evaluation.run_experiment
    calls = []
    def evaluate_only(source, proposal, policy):
        assert Path(source) == split / "evaluation.xml"
        assert proposal == fixed["proposal"]
        assert policy.parameters() == fixed["policy"]
        # La marca de acceso y el evento se guardan ANTES del cálculo.
        access_path, = (tmp_path / "access").iterdir()
        access = read_json(access_path)
        assert events(Path(access["evaluation_run"]))[-1]["event"] == "evaluation_requested"
        calls.append(source)
        return actual(source, proposal, policy)
    monkeypatch.setattr(evaluation, "run_experiment", evaluate_only)
    directory = evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
    result = read_json(directory / "comparison.json")
    assert len(calls) == 1
    assert result["stage"] == "evaluation_completed"
    assert result["proposal"] == fixed["proposal"]
    assert result["policy"] == fixed["policy"]
    assert result["blocks"]["development"]["results"] == fixed["development_result"]
    assert result["blocks"]["evaluation"]["results"] == read_json(directory / "evaluation_raw.json")
    assert result["blocks"]["development"]["assessment"]["scope"] == "development"
    assert result["blocks"]["evaluation"]["assessment"]["scope"] == "held_out_period"
    assert result["model_requests"] == 0 and result["api_cost_usd"] == "0"
    assert all(p.read_bytes() == raw for p, raw in original.items())
    assert events(directory)[-1]["event"] == "evaluation_completed"
    report = (directory / "report.md").read_text(encoding="utf-8")
    assert "no crea evidencia totalmente inédita" in report
    assert "sin posiciones ni señales heredadas" in report


def test_evaluation_backtests_start_from_initial_cash_and_only_reserved_observations(frozen_setup, tmp_path, monkeypatch):
    split, _, frozen = frozen_setup
    import trading_ai.experiments as experiments
    actual = experiments.run_backtest
    evaluation_calls = []
    first_day = read_json(split / "manifest.json")["partitions"]["evaluation"]["first_date"]
    def observed(rates, signals, pair, **kwargs):
        if str(rates[0][0]) == first_day:
            assert len(rates) == 22
            assert kwargs["initial_capital"] == Decimal("1000")
            assert signals[0] is Signal.NONE
            result = actual(rates, signals, pair, **kwargs)
            assert result.equity_curve[0].equity == Decimal("1000")
            evaluation_calls.append(result)
            return result
        return actual(rates, signals, pair, **kwargs)
    monkeypatch.setattr(experiments, "run_backtest", observed)
    evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
    assert len(evaluation_calls) == 2


@pytest.mark.parametrize("target", ["frozen.json", "development.xml", "evaluation.xml", "manifest.json"])
def test_modified_inputs_stop_before_evaluation_access(frozen_setup, tmp_path, monkeypatch, target):
    split, _, frozen = frozen_setup
    path = (frozen if target == "frozen.json" else split) / target
    path.write_bytes(path.read_bytes() + b"\n")
    monkeypatch.setattr("trading_ai.evaluation.run_experiment", lambda *args: pytest.fail("No evaluar"))
    with pytest.raises(EvaluationError) as failure:
        evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
    assert events(failure.value.directory)[-1]["event"] == "evaluation_failed"
    assert not (tmp_path / "access").exists()
    assert not (failure.value.directory / "report.md").exists()


def test_repeated_evaluation_is_blocked_even_with_another_freeze_and_output_folder(frozen_setup, tmp_path, monkeypatch):
    split, research, frozen = frozen_setup
    first = evaluate_frozen_proposal(frozen, tmp_path / "first")
    saved = {p.name: p.read_bytes() for p in first.iterdir()}
    another_frozen = freeze_proposal(split, research, tmp_path / "another-freeze")
    monkeypatch.setattr("trading_ai.evaluation.run_experiment", lambda *args: pytest.fail("No repetir"))
    with pytest.raises(EvaluationError, match="ya tiene un intento") as failure:
        evaluate_frozen_proposal(another_frozen, tmp_path / "second")
    assert {p.name: p.read_bytes() for p in first.iterdir()} == saved
    assert events(failure.value.directory)[-1]["event"] == "evaluation_failed"
    assert len(list((tmp_path / "access").iterdir())) == 1


def test_failure_after_access_preserves_mark_and_blocks_retry(frozen_setup, tmp_path, monkeypatch):
    _, _, frozen = frozen_setup
    def failed_engine(*args):
        raise ValueError("Fallo simulado después del acceso")
    monkeypatch.setattr("trading_ai.evaluation.run_experiment", failed_engine)
    with pytest.raises(EvaluationError, match="Fallo simulado") as failure:
        evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
    assert any(event["event"] == "evaluation_access_claimed" for event in events(failure.value.directory))
    assert not (failure.value.directory / "comparison.json").exists()
    with pytest.raises(EvaluationError, match="ya tiene un intento"):
        evaluate_frozen_proposal(frozen, tmp_path / "evaluations")


def test_two_simultaneous_attempts_cannot_evaluate_twice(frozen_setup, tmp_path):
    _, _, frozen = frozen_setup
    def attempt(_):
        try:
            return evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
        except EvaluationError as error:
            assert "ya tiene un intento" in str(error)
            return None
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, range(2)))
    assert sum(result is not None for result in results) == 1
    assert len(list((tmp_path / "access").iterdir())) == 1


def test_wrong_actual_evaluation_dates_are_rejected_before_engine(setup, tmp_path, monkeypatch):
    split, research, _ = setup
    # Reproduce metadatos falsos: el registro previo no interpreta las fechas reservadas.
    source = split / "evaluation.xml"
    source.write_bytes(source.read_bytes().replace(b"2025-01-23", b"2024-01-23"))
    plan = read_json(split / "manifest.json")
    plan["partitions"]["evaluation"]["sha256"] = sha256(source.read_bytes()).hexdigest()
    (split / "manifest.json").write_text(json.dumps(plan), encoding="utf-8")
    frozen = freeze_proposal(split, research, tmp_path / "frozen")
    monkeypatch.setattr("trading_ai.evaluation.run_experiment", lambda *args: pytest.fail("Fechas inválidas"))
    with pytest.raises(EvaluationError, match="fechas de evaluación"):
        evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
    assert len(list((tmp_path / "access").iterdir())) == 1


def test_wrong_engine_results_are_not_published_but_remain_for_audit(frozen_setup, tmp_path, monkeypatch):
    _, _, frozen = frozen_setup
    import trading_ai.evaluation as evaluation
    actual = evaluation.run_experiment
    def wrong(source, proposal, policy):
        result = actual(source, proposal, policy)
        result["policy"]["initial_capital"] = "9999"
        return result
    monkeypatch.setattr(evaluation, "run_experiment", wrong)
    with pytest.raises(EvaluationError, match="parámetros fijados") as failure:
        evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
    assert (failure.value.directory / "evaluation_raw.json").exists()
    assert not (failure.value.directory / "comparison.json").exists()
    assert not (failure.value.directory / "report.md").exists()


def test_code_change_during_evaluation_prevents_validated_report(frozen_setup, tmp_path, monkeypatch):
    _, _, frozen = frozen_setup
    import trading_ai.evaluation as evaluation
    code = evaluation._code_hashes()
    hashes = iter([code, {**code, "evaluation.py": "changed"}])
    monkeypatch.setattr(evaluation, "_code_hashes", lambda: next(hashes))
    with pytest.raises(EvaluationError, match="código cambiaron") as failure:
        evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
    assert (failure.value.directory / "evaluation_raw.json").exists()
    assert not (failure.value.directory / "report.md").exists()


def test_evaluation_without_closures_is_inconclusive_even_if_development_has_trades(setup, tmp_path):
    split, research, _ = setup
    path = split / "evaluation.xml"
    tree = ET.parse(path)
    for node in tree.getroot().iter(f"{{{NAMESPACE}}}Cube"):
        if node.get("currency") == "USD":
            node.set("rate", "5")
    tree.write(path, encoding="utf-8")
    manifest = read_json(split / "manifest.json")
    manifest["partitions"]["evaluation"]["sha256"] = sha256(path.read_bytes()).hexdigest()
    (split / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    frozen = freeze_proposal(split, research, tmp_path / "frozen")
    directory = evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
    comparison = read_json(directory / "comparison.json")
    assert comparison["blocks"]["development"]["results"]["baseline"]["closed_trades"] > 0
    block = comparison["blocks"]["evaluation"]
    assert block["results"]["baseline"]["closed_trades"] == block["results"]["candidate"]["closed_trades"] == 0
    assert block["assessment"]["criterion_status"] == "inconclusive"
    assert block["assessment"]["scope"] == "held_out_period"


def test_report_rounding_is_independent_of_callers_decimal_context(frozen_setup, tmp_path):
    _, _, frozen = frozen_setup
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        directory = evaluate_frozen_proposal(frozen, tmp_path / "evaluations")
    comparison = read_json(directory / "comparison.json")
    value = comparison["blocks"]["evaluation"]["results"]["candidate"]["final_equity"]
    assert f"{Decimal(value):.6f}" in (directory / "report.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("extra", [["--pair", "GBP/USD"], ["--fast-window", "15"], ["--cost-rate", "0"]])
def test_cli_cannot_override_fixed_parameters(frozen_setup, tmp_path, extra):
    _, _, frozen = frozen_setup
    with pytest.raises(SystemExit) as failure:
        main(["--frozen-run", str(frozen), *extra])
    assert failure.value.code == 2
    assert not (tmp_path / "access").exists()


def test_cli_outputs_report_or_recorded_error(frozen_setup, tmp_path, capsys):
    _, _, frozen = frozen_setup
    args = ["--frozen-run", str(frozen), "--output-dir", str(tmp_path / "evaluations")]
    main(args)
    assert "Evaluación completada" in capsys.readouterr().out
    with pytest.raises(SystemExit) as failure:
        main(args)
    assert failure.value.code == 1
    assert "Registro del intento" in capsys.readouterr().err
