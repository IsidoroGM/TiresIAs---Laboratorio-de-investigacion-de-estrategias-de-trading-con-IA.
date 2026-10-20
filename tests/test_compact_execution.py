"""Simulación explícita acotada: reserva compartida, fallos parciales y lectura sin recalcular."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pytest

from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews, candidate
from test_compact_plan import reviewed
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from trading_ai.compact_execution import CompactExecutionError, execute_compact_plan, verify_compact_execution, main
from trading_ai.compact_plan import prepare_compact_plan, verify_compact_plan
from trading_ai import rule_execution as engine


@pytest.fixture
def plan(reviewed, tmp_path):
    return prepare_compact_plan(reviewed[0], output_dir=tmp_path / "plans")


def events(directory):
    return [json.loads(line) for line in (directory / "events.jsonl").read_bytes().splitlines()]


def test_explicit_execution_reuses_engine_keeps_sources_and_verifies_offline(plan, tmp_path, monkeypatch, capsys):
    original = {path: path.read_bytes() for path in plan.iterdir()}
    actual, calls = engine._calculate, []
    def observed(rates, strategy, policy):
        calls.append((rates, strategy, policy))
        return actual(rates, strategy, policy)
    def forbidden(*args, **kwargs): pytest.fail("Ejecutar o leer no puede consultar modelos o evaluación")
    monkeypatch.setattr(engine, "_calculate", observed)
    for name in ("trading_ai.compact_ollama.CompactOllamaProvider.complete", "trading_ai.compact_ollama.CompactOllamaProvider.describe", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    actual_open = Path.open
    def development_only(path, *args, **kwargs):
        assert path.name not in ("evaluation.xml", "comparison.json")
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", development_only)
    run = execute_compact_plan(plan, output_dir=tmp_path / "executions")
    result = verify_compact_execution(run)
    assert len(calls) == 2 and calls[0][0] == calls[1][0] and calls[0][2] == calls[1][2]
    assert result["completed_backtests"] == ["baseline", "candidate"]
    assert result["reserved_backtests"] == {"baseline": 1, "candidate": 1}
    assert result["model_requests"] == 0 and result["api_cost_usd"] == "0" and result["outer_evaluation_allowed"] is False
    assert result["assessment"]["origin"] == "python" and result["scope"] == "known_development_history_only"
    assert result["inherited_usage"][0]["input_tokens"] == 100
    assert all(path.read_bytes() == raw for path, raw in original.items())
    assert result["policy"] == verify_compact_plan(plan)["policy"]
    monkeypatch.setattr(engine, "_calculate", forbidden)
    assert verify_compact_execution(run) == result
    main(["verify", "--run", str(run)])
    assert json.loads(capsys.readouterr().out) == result["assessment"]
    with pytest.raises(CompactExecutionError, match="reservado"):
        execute_compact_plan(plan, output_dir=tmp_path / "different-executions")


@pytest.mark.parametrize("fail_index", [0, 1])
def test_failed_calculation_conserves_partial_results_and_never_retries(plan, tmp_path, monkeypatch, fail_index):
    actual, calls = engine._calculate, []
    def fail(rates, strategy, policy):
        calls.append(None)
        if len(calls) - 1 == fail_index: raise OSError("Fallo del motor de prueba")
        return actual(rates, strategy, policy)
    monkeypatch.setattr(engine, "_calculate", fail)
    with pytest.raises(CompactExecutionError, match="Fallo") as failure:
        execute_compact_plan(plan, output_dir=tmp_path / "executions")
    run = failure.value.directory
    assert not (run / "results.json").exists() and not (run / "report.md").exists()
    assert (run / "baseline.json").exists() == (fail_index == 1)
    state = events(run)[-1]["data"]
    assert state["access_claimed"] is True
    assert state["completed_backtests"] == (["baseline"] if fail_index else [])
    assert state["reserved_backtests"] == {"baseline": 1, "candidate": int(fail_index == 1)}
    with pytest.raises(CompactExecutionError, match="reservado"):
        execute_compact_plan(plan, output_dir=tmp_path / "retry")
    assert len(calls) == fail_index + 1


def test_pending_candidate_cannot_bypass_review_and_plan(candidate, tmp_path, monkeypatch):
    def forbidden(*args): pytest.fail("Una candidata pendiente no puede calcular")
    monkeypatch.setattr(engine, "_calculate", forbidden)
    with pytest.raises(CompactExecutionError): execute_compact_plan(candidate[0], output_dir=tmp_path / "executions")
    assert not engine.ACCESS_ROOT.exists()


def test_existing_shared_reservation_blocks_other_protocols_even_if_incomplete(plan, tmp_path, monkeypatch):
    registered = verify_compact_plan(plan)
    engine.ACCESS_ROOT.mkdir(parents=True)
    (engine.ACCESS_ROOT / (registered["calculation_id"] + ".json")).write_bytes(b'{}')
    def forbidden(*args): pytest.fail("Una reserva anterior, incluso incompleta, está consumida")
    monkeypatch.setattr(engine, "_calculate", forbidden)
    with pytest.raises(CompactExecutionError, match="reservado"):
        execute_compact_plan(plan, output_dir=tmp_path / "executions")


def test_concurrent_executions_only_compute_one_pair_of_accounts(plan, tmp_path, monkeypatch):
    actual, calls = engine._calculate, []
    def observed(*args):
        calls.append(None)
        return actual(*args)
    monkeypatch.setattr(engine, "_calculate", observed)
    def execute():
        try: return execute_compact_plan(plan, output_dir=tmp_path / "executions")
        except CompactExecutionError: return None
    with ThreadPoolExecutor(max_workers=2) as executor:
        runs = list(executor.map(lambda _: execute(), range(2)))
    assert sum(run is not None for run in runs) == 1 and len(calls) == 2
    assert len(list(engine.ACCESS_ROOT.glob("*.json"))) == 1


def test_changed_plan_between_accounts_stops_after_baseline(plan, tmp_path, monkeypatch):
    actual, calls = engine._calculate, []
    def changed(*args):
        calls.append(None)
        ledger = actual(*args)
        with (plan / "development.xml").open("ab") as stream: stream.write(b' changed')
        return ledger
    monkeypatch.setattr(engine, "_calculate", changed)
    with pytest.raises(CompactExecutionError) as failure:
        execute_compact_plan(plan, output_dir=tmp_path / "executions")
    assert len(calls) == 1 and (failure.value.directory / "baseline.json").exists()
    assert events(failure.value.directory)[-1]["data"]["reserved_backtests"] == {"baseline": 1, "candidate": 0}


@pytest.mark.parametrize("filename", ["results.json", "baseline.json", "candidate.json", "development.xml", "report.md", "events.jsonl"])
def test_changed_output_is_rejected_without_recalculation(plan, tmp_path, monkeypatch, filename):
    run = execute_compact_plan(plan, output_dir=tmp_path / "executions")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    def forbidden(*args): pytest.fail("Verificar no recalcula")
    monkeypatch.setattr(engine, "_calculate", forbidden)
    with pytest.raises(ValueError): verify_compact_execution(run)


def test_changed_execution_reservation_is_detected(plan, tmp_path):
    run = execute_compact_plan(plan, output_dir=tmp_path / "executions")
    result = verify_compact_execution(run)
    (engine.ACCESS_ROOT / (result["calculation_id"] + ".json")).write_bytes(b'{}')
    with pytest.raises(ValueError): verify_compact_execution(run)
