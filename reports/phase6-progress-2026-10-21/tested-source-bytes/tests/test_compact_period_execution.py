"""Campaña de periodos: reserva global e individual previa, sin selección o reintentos."""

from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews, candidate
from test_compact_plan import reviewed
from test_compact_execution import plan
from test_compact_periods import isolated_periods
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from trading_ai.compact_period_execution import (PeriodExecutionError, execute_compact_periods, verify_compact_period_execution, main)
from trading_ai.compact_periods import prepare_compact_periods, verify_compact_periods
from trading_ai import compact_periods as periods
from trading_ai import rule_execution as engine


def events(directory):
    return [json.loads(line) for line in (directory / "events.jsonl").read_bytes().splitlines()]


@pytest.mark.parametrize("count", [2, 3])
def test_all_periods_use_frozen_controls_and_independent_engine_calls_with_no_model(plan, tmp_path, monkeypatch, capsys, count):
    diagnostic = prepare_compact_periods(plan, periods=count, output_dir=tmp_path / "periods")
    fixed = verify_compact_periods(diagnostic)
    original = {path: path.read_bytes() for path in diagnostic.iterdir()}
    actual, calls = engine._calculate, []
    def observed(rates, strategy, policy):
        assert len(list(periods.ACCESS_ROOT.glob("*.json"))) == 1
        assert len(list(engine.ACCESS_ROOT.glob("*.json"))) == count
        calls.append((rates, strategy, policy))
        return actual(rates, strategy, policy)
    def forbidden(*args, **kwargs): pytest.fail("No se permite consultar modelos o recalcular al leer")
    monkeypatch.setattr(engine, "_calculate", observed)
    for name in ("trading_ai.compact_ollama.CompactOllamaProvider.complete", "trading_ai.compact_ollama.CompactOllamaProvider.describe", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    run = execute_compact_periods(diagnostic, output_dir=tmp_path / "executions")
    result = verify_compact_period_execution(run)
    assert len(calls) == 2 * count and all(call[2].parameters() == fixed["policy"] for call in calls)
    for index in range(count): assert calls[2 * index][0] == calls[2 * index + 1][0]
    assert len(result["period_results"]) == count and sum(result["assessment_counts"].values()) == count
    assert result["reserved_backtests"] == {"baseline": count, "candidate": count}
    assert len(result["completed_backtests"]) == count * 2
    assert result["model_requests"] == 0 and result["api_cost_usd"] == "0"
    assert result["walk_forward_selection"] is result["strategy_selection"] is result["outer_evaluation_allowed"] is False
    assert "compounded_return" not in result and all(path.read_bytes() == raw for path, raw in original.items())
    for row in result["period_results"]:
        if row["baseline"]["closed_trades"] == 0 or row["candidate"]["closed_trades"] == 0:
            assert row["assessment"]["criterion_status"] == "inconclusive"
    monkeypatch.setattr(engine, "_calculate", forbidden)
    assert verify_compact_period_execution(run) == result
    main(["verify", "--run", str(run)])
    assert json.loads(capsys.readouterr().out) == result["assessment_counts"]
    with pytest.raises(PeriodExecutionError, match="reservado"):
        execute_compact_periods(diagnostic, output_dir=tmp_path / "retry")


def test_failure_keeps_completed_periods_and_campaign_cannot_reset_by_count(plan, tmp_path, monkeypatch):
    two = prepare_compact_periods(plan, periods=2, output_dir=tmp_path / "two")
    three = prepare_compact_periods(plan, periods=3, output_dir=tmp_path / "three")
    actual, calls = engine._calculate, []
    def interrupted(*args):
        calls.append(None)
        if len(calls) == 3: raise OSError("Interrupción en segundo periodo")
        return actual(*args)
    monkeypatch.setattr(engine, "_calculate", interrupted)
    with pytest.raises(PeriodExecutionError, match="Interrupción") as failure:
        execute_compact_periods(two, output_dir=tmp_path / "executions")
    run = failure.value.directory
    assert (run / "period-01/baseline.json").exists() and (run / "period-01/candidate.json").exists()
    assert not (run / "results.json").exists() and not (run / "report.md").exists()
    state = events(run)[-1]["data"]
    assert state["reserved_backtests"] == {"baseline": 2, "candidate": 1}
    assert state["completed_backtests"] == ["period-01/baseline", "period-01/candidate"]
    assert len(state["access_claimed"]) == 3
    with pytest.raises(PeriodExecutionError, match="reservado"):
        execute_compact_periods(three, output_dir=tmp_path / "retry-three")
    assert len(calls) == 3


def test_late_shared_claim_collision_stops_before_any_calculation(plan, tmp_path, monkeypatch):
    diagnostic = prepare_compact_periods(plan, periods=2, output_dir=tmp_path / "periods")
    fixed = verify_compact_periods(diagnostic)
    engine.ACCESS_ROOT.mkdir(parents=True)
    (engine.ACCESS_ROOT / (fixed["periods"][1]["calculation_id"] + ".json")).write_bytes(b'{}')
    def forbidden(*args): pytest.fail("Una colisión de reserva debe detectarse antes de calcular")
    monkeypatch.setattr(engine, "_calculate", forbidden)
    with pytest.raises(PeriodExecutionError, match="reservado") as failure:
        execute_compact_periods(diagnostic, output_dir=tmp_path / "executions")
    assert events(failure.value.directory)[-1]["data"]["reserved_backtests"] == {"baseline": 0, "candidate": 0}
    assert len(list(periods.ACCESS_ROOT.glob("*.json"))) == 1
    assert len(list(engine.ACCESS_ROOT.glob("*.json"))) == 2


def test_concurrent_campaigns_only_calculate_once(plan, tmp_path, monkeypatch):
    diagnostic = prepare_compact_periods(plan, periods=2, output_dir=tmp_path / "periods")
    actual, calls = engine._calculate, []
    def observed(*args):
        calls.append(None)
        return actual(*args)
    monkeypatch.setattr(engine, "_calculate", observed)
    def execute():
        try: return execute_compact_periods(diagnostic, output_dir=tmp_path / "executions")
        except PeriodExecutionError: return None
    with ThreadPoolExecutor(max_workers=2) as executor:
        runs = list(executor.map(lambda _: execute(), range(2)))
    assert sum(run is not None for run in runs) == 1 and len(calls) == 4


def test_source_mutation_stops_without_finishing_period(plan, tmp_path, monkeypatch):
    diagnostic = prepare_compact_periods(plan, periods=2, output_dir=tmp_path / "periods")
    actual, calls = engine._calculate, []
    def changed(*args):
        calls.append(None)
        ledger = actual(*args)
        with (diagnostic / "period-01.xml").open("ab") as stream: stream.write(b' changed')
        return ledger
    monkeypatch.setattr(engine, "_calculate", changed)
    with pytest.raises(PeriodExecutionError) as failure:
        execute_compact_periods(diagnostic, output_dir=tmp_path / "executions")
    assert len(calls) == 1 and (failure.value.directory / "period-01/baseline.json").exists()
    assert events(failure.value.directory)[-1]["data"]["reserved_backtests"] == {"baseline": 1, "candidate": 0}


@pytest.mark.parametrize("filename", ["results.json", "results.json.sha256", "report.md", "period-01.xml", "period-01/baseline.json", "events.jsonl"])
def test_tampered_result_is_rejected_without_recalculation(plan, tmp_path, monkeypatch, filename):
    diagnostic = prepare_compact_periods(plan, periods=2, output_dir=tmp_path / "periods")
    run = execute_compact_periods(diagnostic, output_dir=tmp_path / "executions")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    def forbidden(*args): pytest.fail("Verificar no puede recalcular")
    monkeypatch.setattr(engine, "_calculate", forbidden)
    with pytest.raises(ValueError): verify_compact_period_execution(run)


def test_changed_campaign_claim_is_detected(plan, tmp_path):
    diagnostic = prepare_compact_periods(plan, periods=2, output_dir=tmp_path / "periods")
    run = execute_compact_periods(diagnostic, output_dir=tmp_path / "executions")
    result = verify_compact_period_execution(run)
    (periods.ACCESS_ROOT / (result["campaign_id"] + ".json")).write_bytes(b'{}')
    with pytest.raises(ValueError): verify_compact_period_execution(run)


def test_unreviewed_candidate_cannot_start_campaign(candidate, tmp_path):
    with pytest.raises(PeriodExecutionError):
        execute_compact_periods(candidate[0], output_dir=tmp_path / "executions")
    assert not periods.ACCESS_ROOT.exists() and not engine.ACCESS_ROOT.exists()
