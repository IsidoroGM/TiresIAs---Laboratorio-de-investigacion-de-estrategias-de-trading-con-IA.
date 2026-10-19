"""Protocolo acotado, separación interna y ausencia de acceso a evaluación exterior."""

from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from test_holdout import setup
from trading_ai.data import load_ecb_rates
from trading_ai.experiments import CRITERIA
from trading_ai.holdout import freeze_proposal
from trading_ai.robustness import RobustnessError, _scenarios, _selection, main, prepare_robustness, run_robustness
from trading_ai.validation import NAMESPACE


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def events(directory):
    return [json.loads(line) for line in (directory / "events.jsonl").read_bytes().splitlines()]


@pytest.fixture
def prepared(setup, tmp_path):
    split, research, _ = setup
    frozen = freeze_proposal(split, research, tmp_path / "frozen")
    plan = prepare_robustness(frozen, date(2025, 1, 12), tmp_path / "plans")
    return split, frozen, plan


def test_preparation_does_not_calculate_or_read_outer_data_or_results(setup, tmp_path, monkeypatch):
    split, research, _ = setup
    frozen = freeze_proposal(split, research, tmp_path / "frozen")
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.resolve() != (split / "evaluation.xml").resolve()
        assert path.name != "comparison.json"
        assert path.parent.name != "evaluation-access"
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr("trading_ai.robustness.run_experiment", lambda *args: pytest.fail("Preparación sin cálculos"))
    monkeypatch.setattr("trading_ai.ai.create_provider", lambda *args: pytest.fail("Sin IA"))
    directory = prepare_robustness(frozen, date(2025, 1, 12), tmp_path / "plans")
    plan = read_json(directory / "plan.json")
    assert plan["stage"] == "prepared_not_run"
    assert len(plan["scenarios"]) == 12  # EMA1/3: rápida -1 no es válida.
    assert plan["skipped"][0]["id"] == "fast_minus"
    assert events(directory)[-1]["event"] == "plan_prepared"
    assert sha256((directory / "plan.json").read_bytes()).hexdigest() == (directory / "plan.sha256").read_text().strip()


def test_internal_partitions_reproduce_development_without_overlap(prepared):
    split, _, directory = prepared
    first = load_ecb_rates(directory / "selection.xml", "EUR/USD")
    second = load_ecb_rates(directory / "check.xml", "EUR/USD")
    assert first + second == load_ecb_rates(split / "development.xml", "EUR/USD")
    assert first[-1][0] < date(2025, 1, 12) == second[0][0]
    assert not set(day for day, _ in first).intersection(day for day, _ in second)


def test_run_records_selection_before_any_check_and_keeps_every_scenario(prepared, monkeypatch):
    split, _, plan_dir = prepared
    import trading_ai.robustness as robustness
    actual_calculate = robustness.run_experiment
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.resolve() != (split / "evaluation.xml").resolve()
        assert path.name != "comparison.json"
        assert path.parent.name != "evaluation-access"
        return actual_open(path, *args, **kwargs)
    calls = []
    def calculate(source, proposal, policy):
        assert source.parent == plan_dir
        if source.name == "check.xml":
            attempt, = (plan_dir / "attempts").iterdir()
            assert any(event["event"] == "selection_fixed" for event in events(attempt))
            assert (attempt / "selection.json").exists()
        calls.append(source.name)
        return actual_calculate(source, proposal, policy)
    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr(robustness, "run_experiment", calculate)
    directory = run_robustness(plan_dir)
    result = read_json(directory / "results.json")
    assert calls == ["selection.xml"] * 12 + ["check.xml"] * 12
    assert len(result["rows"]["selection"]) == len(result["rows"]["check"]) == 12
    assert result["selection"] == read_json(directory / "selection.json")
    assert result["model_requests"] == 0 and result["api_cost_usd"] == "0"
    assert events(directory)[-1]["event"] == "run_completed"
    assert len(list(directory.glob('selection_*__*.json'))) == 12
    assert len(list(directory.glob('check_*__*.json'))) == 12


def row(window, returns, drawdown, cost="reference", verdict="supported_in_sample", fast=20, slow=60):
    return {"scenario": {"id": window + "__" + cost, "cost_id": cost, "window_id": window,
                          "proposal": {"arguments": {"fast_window": fast, "slow_window": slow}}},
            "result": {"candidate": {"return_percent": returns, "max_drawdown_percent": drawdown}},
            "assessment": {"verdict": verdict}}


def test_selection_ignores_cost_stress_and_uses_predeclared_ties():
    rows = [row("a", "2", "2", fast=21), row("b", "2", "2", fast=19),
            row("c", "2", "3"), row("stress", "999", "0", cost="cost_minus")]
    assert _selection(rows, CRITERIA[0])["selected_scenario_id"] == "b__reference"
    assert _selection(rows[::-1], CRITERIA[0]) == _selection(rows, CRITERIA[0])


def test_lower_drawdown_criterion_ranks_drawdown_before_return():
    assert _selection([row("a", "9", "3"), row("b", "8", "2")], CRITERIA[1])["selected_scenario_id"] == "b__reference"


def test_no_eligible_scenario_does_not_force_a_winner():
    result = _selection([row("a", "-2", "4", verdict="not_supported_in_sample"),
                         row("b", "0", "0", verdict="inconclusive")], CRITERIA[0])
    assert result["selected_scenario_id"] is None
    assert result["eligible_scenario_ids"] == []


def test_invalid_window_or_negative_cost_is_recorded_as_omitted_not_clipped(prepared):
    _, frozen_dir, _ = prepared
    frozen = read_json(frozen_dir / "frozen.json")
    frozen["policy"]["cost_rate"] = "0"
    scenarios, skipped = _scenarios(frozen)
    assert len(scenarios) == 8
    assert {entry["id"] for entry in skipped} == {"fast_minus", "cost_minus"}
    assert all(Decimal(scenario["policy"]["cost_rate"]) >= 0 for scenario in scenarios)
    assert {scenario["cost_id"] for scenario in scenarios} == {"reference", "cost_plus"}


def test_only_inner_future_prices_change_neither_selection_nor_training_results(setup, tmp_path):
    split, research, research_for = setup
    first_frozen = freeze_proposal(split, research, tmp_path / "frozen")
    first_plan = prepare_robustness(first_frozen, date(2025, 1, 12), tmp_path / "plans")
    first = read_json(run_robustness(first_plan) / "results.json")
    path = split / "development.xml"
    tree = ET.parse(path)
    for day in tree.getroot().findall(f"./{{{NAMESPACE}}}Cube/{{{NAMESPACE}}}Cube"):
        if day.attrib["time"] >= "2025-01-12":
            day.find(f"{{{NAMESPACE}}}Cube[@currency='USD']").set("rate", "50")
    tree.write(path, encoding="utf-8")
    manifest = read_json(split / "manifest.json")
    manifest["partitions"]["development"]["sha256"] = sha256(path.read_bytes()).hexdigest()
    (split / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    other_research = research_for(path)
    other_frozen = freeze_proposal(split, other_research, tmp_path / "frozen")
    other_plan = prepare_robustness(other_frozen, date(2025, 1, 12), tmp_path / "plans")
    other = read_json(run_robustness(other_plan) / "results.json")
    assert first["selection"] == other["selection"]
    assert first["rows"]["selection"] == other["rows"]["selection"]
    assert first["rows"]["check"] != other["rows"]["check"]


@pytest.mark.parametrize("target", ["plan.json", "selection.xml", "check.xml"])
def test_changed_plan_or_partition_rejected_before_calculations(prepared, monkeypatch, target):
    _, _, plan_dir = prepared
    path = plan_dir / target
    path.write_bytes(path.read_bytes() + b"\n")
    monkeypatch.setattr("trading_ai.robustness.run_experiment", lambda *args: pytest.fail("No calcular"))
    with pytest.raises(RobustnessError) as failure:
        run_robustness(plan_dir)
    assert events(failure.value.directory)[-1]["event"] == "run_failed"
    assert not (plan_dir / "run_claim.json").exists()


def test_engine_error_keeps_prior_scenarios_and_blocks_retry(prepared, monkeypatch):
    _, _, plan_dir = prepared
    import trading_ai.robustness as robustness
    actual = robustness.run_experiment
    calls = []
    def fails_later(*args):
        calls.append(1)
        if len(calls) == 3:
            raise ValueError("Fallo simulado")
        return actual(*args)
    monkeypatch.setattr(robustness, "run_experiment", fails_later)
    with pytest.raises(RobustnessError, match="Fallo simulado") as failure:
        run_robustness(plan_dir)
    assert len(list(failure.value.directory.glob('selection_*__*.json'))) == 2
    assert not (failure.value.directory / "results.json").exists()
    assert not (failure.value.directory / "report.md").exists()
    with pytest.raises(RobustnessError, match="ya tiene un intento"):
        run_robustness(plan_dir)


def test_successful_run_cannot_be_overwritten(prepared):
    _, _, plan_dir = prepared
    first = run_robustness(plan_dir)
    original = {p.name: p.read_bytes() for p in first.iterdir()}
    with pytest.raises(RobustnessError, match="ya tiene un intento"):
        run_robustness(plan_dir)
    assert original == {p.name: p.read_bytes() for p in first.iterdir()}


@pytest.mark.parametrize("cutoff", [date(2024, 1, 1), date(2026, 1, 1), "2025-01-12"])
def test_invalid_cutoffs_never_prepare_a_complete_plan(setup, tmp_path, cutoff):
    split, research, _ = setup
    frozen = freeze_proposal(split, research, tmp_path / "frozen")
    with pytest.raises(RobustnessError) as failure:
        prepare_robustness(frozen, cutoff, tmp_path / "plans")
    assert not (failure.value.directory / "plan.json").exists()


def test_report_numbers_do_not_depend_on_decimal_context(prepared):
    _, _, plan_dir = prepared
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        directory = run_robustness(plan_dir)
    result = read_json(directory / "results.json")
    value = result["rows"]["check"][0]["result"]["candidate"]["return_percent"]
    assert f"{Decimal(value):.6f}" in (directory / "report.md").read_text(encoding="utf-8")


def test_cli_cannot_override_scenarios_and_reports_missing_plan(tmp_path, capsys):
    with pytest.raises(SystemExit) as failure:
        main(["run", "--plan-dir", str(tmp_path / "missing"), "--cost-rate", "0"])
    assert failure.value.code == 2
    with pytest.raises(SystemExit) as failure:
        main(["run", "--plan-dir", str(tmp_path / "missing")])
    assert failure.value.code == 1
    assert "Registro" in capsys.readouterr().err
