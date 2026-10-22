"""Particiones mecánicas conocidas: datos completos, cuentas separadas, cero cálculos."""

import json
from pathlib import Path

import pytest

from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews, candidate
from test_compact_plan import reviewed
from test_compact_execution import plan
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from trading_ai.compact_periods import _bounds, prepare_compact_periods, verify_compact_periods, main
from trading_ai.compact_plan import verify_compact_plan
from trading_ai.data import load_ecb_rates
from trading_ai import compact_periods as periods_module
from trading_ai import rule_execution as engine


@pytest.fixture(autouse=True)
def isolated_periods(tmp_path, monkeypatch):
    monkeypatch.setattr(periods_module, "ACCESS_ROOT", tmp_path / "period-access")


@pytest.mark.parametrize("count", [2, 3])
def test_periods_cover_exactly_all_observations_and_preserve_values_without_calculating(plan, tmp_path, monkeypatch, count):
    before = {path: path.read_bytes() for path in plan.iterdir()}
    def forbidden(*args, **kwargs): pytest.fail("Preparar periodos no puede calcular, consultar o seleccionar")
    for name in ("trading_ai.rule_execution._calculate", "trading_ai.experiments.run_backtest",
                 "trading_ai.rules.RuleStrategy.generate_signals", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    run = prepare_compact_periods(plan, periods=count, output_dir=tmp_path / "periods")
    record, source = verify_compact_periods(run), verify_compact_plan(plan)
    assert len(record["periods"]) == count
    for pair in ("EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF"):
        blocks = [load_ecb_rates(run / block["data"]["file"], pair) for block in record["periods"]]
        assert [row for block in blocks for row in block] == load_ecb_rates(plan / "development.xml", pair)
        assert all(blocks[index][-1][0] < blocks[index + 1][0][0] for index in range(count - 1))
    assert max(block["data"]["observations"] for block in record["periods"]) - min(block["data"]["observations"] for block in record["periods"]) <= 1
    for key in ("candidate", "baseline", "policy", "criterion", "reference"):
        assert record[key] == source[key]
    assert record["budget"]["maximum_total_backtests"] == count * 2 <= 6
    assert record["new_usage"]["backtests"] == record["new_usage"]["model_requests"] == 0
    assert record["strategy_selection"] is record["walk_forward_selection"] is record["outer_evaluation_allowed"] is False
    assert record["carry_signals"] is record["carry_positions"] is record["forced_final_close"] is False
    assert record["indicator_warmup"] == "inside_each_period" and record["executable"] is False
    assert record["calculated_results"] is None and not periods_module.ACCESS_ROOT.exists() and not engine.ACCESS_ROOT.exists()
    assert all(path.read_bytes() == raw for path, raw in before.items())


@pytest.mark.parametrize("observations,count", [(22, 1), (22, 4), (22, True), (22, 2.0), (1, 2), (0, 2), (True, 2)])
def test_invalid_period_count_cannot_expand_budget_or_create_empty_blocks(observations, count):
    with pytest.raises(ValueError): _bounds(observations, count)


def test_campaign_identity_does_not_reset_by_changing_period_count_and_historical_plan_stays_verifiable(plan, tmp_path):
    first = prepare_compact_periods(plan, periods=2, output_dir=tmp_path / "first")
    second = prepare_compact_periods(plan, periods=3, output_dir=tmp_path / "second")
    a, b = verify_compact_periods(first), verify_compact_periods(second)
    assert a["campaign_id"] == b["campaign_id"]
    periods_module.ACCESS_ROOT.mkdir(parents=True)
    (periods_module.ACCESS_ROOT / (a["campaign_id"] + ".json")).write_bytes(b'{}')
    assert verify_compact_periods(first) == a
    with pytest.raises(ValueError, match="reserva"):
        prepare_compact_periods(plan, periods=3, output_dir=tmp_path / "third")


def test_already_reserved_period_calculations_are_not_reopened(plan, tmp_path):
    first = prepare_compact_periods(plan, output_dir=tmp_path / "first")
    record = verify_compact_periods(first)
    engine.ACCESS_ROOT.mkdir(parents=True)
    (engine.ACCESS_ROOT / (record["periods"][0]["calculation_id"] + ".json")).write_bytes(b'{}')
    with pytest.raises(ValueError, match="reservado"):
        prepare_compact_periods(plan, output_dir=tmp_path / "second")


def test_candidate_without_accepted_plan_cannot_prepare_periods(candidate, tmp_path):
    with pytest.raises(ValueError):
        prepare_compact_periods(candidate[0], output_dir=tmp_path / "periods")
    assert not periods_module.ACCESS_ROOT.exists()


@pytest.mark.parametrize("filename", ["periods.json", "periods.json.sha256", "events.jsonl", "period-01.xml"])
def test_changed_period_plan_or_data_are_detected(plan, tmp_path, filename):
    run = prepare_compact_periods(plan, output_dir=tmp_path / "periods")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_compact_periods(run)


def test_cli_prepares_and_verifies_without_executing(plan, tmp_path, capsys):
    main(["prepare", "--plan-run", str(plan), "--periods", "2", "--output-dir", str(tmp_path / "periods")])
    main(["verify", "--run", capsys.readouterr().out.strip()])
    assert json.loads(capsys.readouterr().out)["scope"] == "known_development_history_only"
    with pytest.raises(SystemExit): main(["execute", "--run", str(plan)])
