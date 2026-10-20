"""Ventanas temporales artificiales: sin consultar evaluación exterior o modelos."""

from copy import deepcopy
from datetime import date, timedelta
from hashlib import sha256
import json

import pytest

from trading_ai import rule_execution as engine
from trading_ai import walk_forward as walk
from trading_ai.experiments import ExperimentPolicy


@pytest.fixture
def temporal(tmp_path, monkeypatch, request):
    monkeypatch.setattr(walk, "ACCESS_ROOT", tmp_path / "walk-access")
    monkeypatch.setattr(engine, "ACCESS_ROOT", tmp_path / "engine-access")
    values = [1]*96 if getattr(request, "param", {}).get("flat") else [1, 2, 3, 4, 3, 2] * 16
    days = ''.join(f'<Cube time="{date(2001,1,1)+timedelta(days=i)}"><Cube currency="USD" rate="{value}"/></Cube>' for i, value in enumerate(values))
    content = ('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref"><Cube>' + days + '</Cube></Envelope>').encode()
    policy = ExperimentPolicy(fast_window=2, slow_window=4).parameters()
    frozen = {"policy": policy, "proposal": {"criterion": "higher_return_without_more_drawdown", "arguments": {"strategy": "ema", "fast_window": 2, "slow_window": 4}}}
    reference = {"development_sha256": sha256(content).hexdigest()}
    def development(path): return deepcopy(frozen), deepcopy(reference), content
    monkeypatch.setattr(walk, "_development", development)
    monkeypatch.setattr("socket.socket.connect", lambda *args: pytest.fail("No red."))
    return tmp_path / "frozen", content, frozen


def test_expanding_training_precedes_disjoint_checks_and_immutable_grid(temporal, tmp_path):
    plan_dir = walk.prepare(temporal[0], output_dir=tmp_path / "plans")
    plan = walk.verify_plan(plan_dir)
    assert len(plan["folds"]) == 3 and len(plan["candidates"]) == 5
    assert plan["budget"]["maximum_backtests"] == 24
    assert [row["train"]["observations"] for row in plan["folds"]] == [24, 48, 72]
    for fold in plan["folds"]: assert fold["train"]["last_date"] < fold["check"]["first_date"]
    assert plan["independent_validation"] is plan["automatic_adoption"] is False


def test_selection_is_persisted_before_each_check_and_python_verification_never_reexecutes(temporal, tmp_path, monkeypatch):
    plan = walk.prepare(temporal[0], output_dir=tmp_path / "plans")
    run = walk.run(plan, output_dir=tmp_path / "runs")
    monkeypatch.setattr(engine, "_calculate", lambda *args: pytest.fail("No recalcular al verificar."))
    result = walk.verify_run(run)
    assert len(result["folds"]) == 3 and result["attempted_backtests"] <= 24
    assert result["completed_backtests"] == result["attempted_backtests"]
    assert result["model_requests"] == 0 and result["api_cost_usd"] == "0"
    assert result["independent_validation"] is result["automatic_adoption"] is False
    with pytest.raises(engine.ExecutionError): walk.run(plan, output_dir=tmp_path / "other-folder")


def summary(return_value, drawdown="1", closed=2):
    return {"return_percent": return_value, "max_drawdown_percent": drawdown, "closed_trades": closed}


def test_selection_keeps_empty_and_inconclusive_and_uses_only_train_metrics():
    candidates = [{"id": "a", "fast_window": 2, "slow_window": 5}, {"id": "b", "fast_window": 1, "slow_window": 5}]
    base = summary("0")
    assert walk.select(candidates, {"a": summary("0"), "b": summary("5", closed=0)}, base, "higher_return_without_more_drawdown") is None
    assert walk.select(candidates, {"a": summary("3"), "b": summary("3")}, base, "higher_return_without_more_drawdown") == "b"


def test_failed_calculation_consumes_protocol_and_shared_attempt(temporal, tmp_path, monkeypatch):
    plan = walk.prepare(temporal[0], output_dir=tmp_path / "plans")
    monkeypatch.setattr(engine, "_calculate", lambda *args: (_ for _ in ()).throw(RuntimeError("Fallo artificial")))
    with pytest.raises(engine.ExecutionError) as error: walk.run(plan, output_dir=tmp_path / "runs")
    assert not (error.value.directory / "results.json").exists()
    assert len(list(walk.ACCESS_ROOT.glob("*.json"))) == len(list(engine.ACCESS_ROOT.glob("*.json"))) == 1
    with pytest.raises(engine.ExecutionError): walk.run(plan, output_dir=tmp_path / "retry")


@pytest.mark.parametrize("name", ["development.xml", "train-01.xml", "check-02.xml", "plan.json"])
def test_tampered_plan_or_period_rejected(temporal, tmp_path, name):
    plan = walk.prepare(temporal[0], output_dir=tmp_path / "plans")
    with (plan / name).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): walk.verify_plan(plan)


def test_tampered_result_ledger_rejected(temporal, tmp_path):
    plan = walk.prepare(temporal[0], output_dir=tmp_path / "plans")
    run = walk.run(plan, output_dir=tmp_path / "runs")
    ledger_file = next(run.glob("train-*.json"))
    with ledger_file.open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): walk.verify_run(run)


@pytest.mark.parametrize("temporal", [{"flat": True}], indirect=True)
def test_no_training_selection_retains_all_folds_without_forcing_checks(temporal, tmp_path):
    plan = walk.prepare(temporal[0], output_dir=tmp_path / "plans")
    run = walk.run(plan, output_dir=tmp_path / "runs")
    result = walk.verify_run(run)
    assert result["attempted_backtests"] == 18
    assert all(fold["selected_id"] is None and fold["check"] is None for fold in result["folds"])
    assert not list(run.glob("check-*.json"))


def test_check_data_not_loaded_until_selection_is_durable(temporal, tmp_path, monkeypatch):
    plan = walk.prepare(temporal[0], output_dir=tmp_path / "plans")
    original = walk.load_ecb_rates
    checks = []
    # Selector aislado para ejercitar siempre la rama con comprobación; el motor es real.
    monkeypatch.setattr(walk, "select", lambda candidates, *args: candidates[0]["id"])
    def read(path, pair):
        if path.name.startswith("check-"):
            index = path.stem.split("-")[1]
            selection = list((tmp_path / "runs").glob(f"*/selection-{index}.json"))
            assert len(selection) == 1 and json.loads(selection[0].read_bytes())["selected_id"] is not None
            checks.append(index)
        return original(path, pair)
    monkeypatch.setattr(walk, "load_ecb_rates", read)
    result = walk.verify_run(walk.run(plan, output_dir=tmp_path / "runs"))
    assert len(checks) == 6 and result["attempted_backtests"] == 24
