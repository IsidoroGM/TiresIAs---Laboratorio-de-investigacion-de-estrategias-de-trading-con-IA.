"""Cálculo virtual sobre datos artificiales; nunca se ejecutan propuestas reales pendientes."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
import json
from pathlib import Path

import pytest

from test_campaign_permission import permission_plan, permitted, declaration
from test_campaign_review import campaign_fixture, review_roots, reviewed, assessment
from test_campaign_controller import captured
from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews
from test_compact_request import duplicate_memory
from test_discovery import registered
from test_guided_compact_request import sources
from test_holdout import setup
from test_structured_draft import draft
from test_structured_draft_request import memory
from test_structured_ideas import generated, proposal
from test_structured_session import session
from trading_ai import campaign_execution as execution
from trading_ai import campaign_experiment as experiments
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_permission as permissions
from trading_ai import campaign_plan as campaigns
from trading_ai import campaign_review as reviews
from trading_ai import rule_execution as engine
from trading_ai.guided_compact_request import prepare_guided_request
from trading_ai.research_session import _origin
from trading_ai.validated_read_cache import ValidatedReadCache


@pytest.fixture
def virtual(permitted, monkeypatch):
    # El validador de datos anterior está aislado; el cálculo del motor es real.
    rates = ((date(2001, 1, 1), Decimal("1.2")), (date(2001, 1, 2), Decimal("0.9")))
    monkeypatch.setattr(execution, "load_ecb_rates", lambda path, pair: rates)
    return permitted


def read_events(directory):
    return [json.loads(line) for line in (directory / "events.jsonl").read_bytes().splitlines()]


def test_exactly_two_engine_calculations_and_python_inconclusive_result(virtual, tmp_path, monkeypatch):
    permit, plan, fixture = virtual
    calls = []
    calculate = engine._calculate
    def counted(*args):
        calls.append(args[1].name)
        return calculate(*args)
    monkeypatch.setattr(engine, "_calculate", counted)
    def forbidden(*args, **kwargs): pytest.fail("El cálculo no puede enviar peticiones o concederse nuevos permisos.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.compact_ollama.CompactOllamaProvider.describe", "trading_ai.campaign_permission.grant_permission",
                 "trading_ai.structured_generation.reserve_compact_generation"):
        monkeypatch.setattr(name, forbidden)
    directory = execution.execute(permit, output_dir=tmp_path / "executions")
    assert len(calls) == 2
    monkeypatch.setattr(engine, "_calculate", forbidden)
    result = execution.verify_execution(directory)
    assert result["calculation_id"] == plan["calculation_id"]
    assert result["assessment"]["criterion_status"] == "inconclusive"
    assert result["assessment"]["origin"] == "python"
    assert result["automatic_adoption"] is result["transport_verified"] is result["broker_operations_allowed"] is False
    assert result["model_requests"] == 0 and result["api_cost_usd"] == "0"
    assert result["completed_backtests"] == ["baseline", "candidate"]
    state = ledger.inspect_campaign(fixture["scope"])
    assert state["reserved_model_requests"] == 1 and state["reserved_backtests"] == 2
    assert state["remaining_accounting_slots"]["backtests"] == 4
    assert len(list(engine.ACCESS_ROOT.glob("*.json"))) == 1
    assert "TiresIAs" in (directory / "report.md").read_text(encoding="utf-8")
    assert permissions.inspect_permissions(fixture["scope"])["permissions"][0]["status"] == "calculation_claimed"
    with pytest.raises(execution.ExecutionError): execution.execute(permit, output_dir=tmp_path / "another-directory")
    assert len(calls) == 2 and ledger.inspect_campaign(fixture["scope"])["reserved_backtests"] == 2


def test_no_permission_cannot_execute_a_plan_or_create_calculation_claim(permission_plan, tmp_path):
    directory, _, fixture = permission_plan
    before = ledger.LEDGER_PATH.read_bytes()
    with pytest.raises(execution.ExecutionError): execution.execute(directory, output_dir=tmp_path / "no-permission")
    assert ledger.LEDGER_PATH.read_bytes() == before and not engine.ACCESS_ROOT.exists()
    assert ledger.inspect_campaign(fixture["scope"])["reserved_backtests"] == 0


@pytest.mark.parametrize("fail_on", [1, 2])
def test_engine_failure_keeps_shared_claim_and_both_reserved_slots(virtual, tmp_path, monkeypatch, fail_on):
    permit, plan, fixture = virtual
    calculate = engine._calculate
    calls = []
    def fail(*args):
        calls.append(None)
        if len(calls) == fail_on: raise RuntimeError("Fallo artificial del motor")
        return calculate(*args)
    monkeypatch.setattr(engine, "_calculate", fail)
    with pytest.raises(execution.ExecutionError) as failure:
        execution.execute(permit, output_dir=tmp_path / "failed-execution")
    directory = failure.value.directory
    event = read_events(directory)[-1]
    assert event["event"] == "campaign_execution_failed" and event["data"]["shared_calculation_claimed"] is True
    assert event["data"]["attempted_backtests"] == ["baseline", "candidate"][:fail_on]
    assert event["data"]["completed_backtests"] == ([] if fail_on == 1 else ["baseline"])
    assert not (directory / "results.json").exists()
    assert (engine.ACCESS_ROOT / (plan["calculation_id"] + ".json")).exists()
    assert ledger.inspect_campaign(fixture["scope"])["reserved_backtests"] == 2
    with pytest.raises(execution.ExecutionError): execution.execute(permit, output_dir=tmp_path / "retry")
    assert len(calls) == fail_on


def test_failed_ledger_reservation_consumes_shared_attempt_without_calculating(virtual, tmp_path, monkeypatch):
    permit, plan, fixture = virtual
    def fail(*args, **kwargs): raise ValueError("Fallo artificial del registro")
    monkeypatch.setattr(ledger, "reserve_comparison", fail)
    monkeypatch.setattr(engine, "_calculate", lambda *args: pytest.fail("No hay reserva contable válida."))
    with pytest.raises(execution.ExecutionError) as failure:
        execution.execute(permit, output_dir=tmp_path / "failed-ledger")
    assert read_events(failure.value.directory)[-1]["data"]["attempted_backtests"] == []
    assert (engine.ACCESS_ROOT / (plan["calculation_id"] + ".json")).exists()
    assert ledger.inspect_campaign(fixture["scope"])["reserved_backtests"] == 0
    with pytest.raises(execution.ExecutionError): execution.execute(permit, output_dir=tmp_path / "retry")


def test_changed_source_between_baseline_and_candidate_stops_second_calculation(virtual, tmp_path, monkeypatch):
    permit, _, fixture = virtual
    calculate, calls = engine._calculate, []
    def change(*args):
        calls.append(None)
        result = calculate(*args)
        with (fixture["capture"] / "observation.raw").open("ab") as stream: stream.write(b' changed')
        return result
    monkeypatch.setattr(engine, "_calculate", change)
    with pytest.raises(execution.ExecutionError) as failure:
        execution.execute(permit, output_dir=tmp_path / "changed-source")
    assert len(calls) == 1 and (failure.value.directory / "baseline.json").exists()
    assert not (failure.value.directory / "candidate.json").exists()
    assert ledger.inspect_campaign(fixture["scope"])["reserved_backtests"] == 2


def test_concurrent_executors_calculate_at_most_one_pair(virtual, tmp_path, monkeypatch):
    permit, _, fixture = virtual
    calculate, calls = engine._calculate, []
    def counted(*args):
        calls.append(None)
        return calculate(*args)
    monkeypatch.setattr(engine, "_calculate", counted)
    def run(index):
        try: return execution.execute(permit, output_dir=tmp_path / "parallel")
        except execution.ExecutionError: return None
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(run, (0, 1)))
    successful = [directory for directory in results if directory is not None]
    assert len(successful) == 1 and len(calls) == 2
    assert len(list(engine.ACCESS_ROOT.glob("*.json"))) == 1
    assert ledger.inspect_campaign(fixture["scope"])["reserved_backtests"] == 2
    execution.verify_execution(successful[0])


@pytest.mark.parametrize("filename", ["results.json", "events.jsonl", "baseline.json", "candidate.json",
                                      "development.xml", "comparison.json", "report.md"])
def test_tampered_execution_artifact_cannot_be_verified(virtual, tmp_path, filename):
    directory = execution.execute(virtual[0], output_dir=tmp_path / "executions")
    with (directory / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): execution.verify_execution(directory)


def test_changed_shared_claim_blocks_verification(virtual, tmp_path):
    permit, plan, _ = virtual
    directory = execution.execute(permit, output_dir=tmp_path / "executions")
    with (engine.ACCESS_ROOT / (plan["calculation_id"] + ".json")).open("ab") as stream: stream.write(b' ')
    with pytest.raises(ValueError): execution.verify_execution(directory)


def test_cli_executes_only_explicit_permission_and_verifies_result(virtual, tmp_path, capsys):
    execution.main(["execute", "--permission-run", str(virtual[0]), "--output-dir", str(tmp_path / "executions")])
    directory = capsys.readouterr().out.strip()
    execution.main(["verify", "--run", directory])
    assert json.loads(capsys.readouterr().out)["criterion_status"] == "inconclusive"
    with pytest.raises(SystemExit): execution.main(["retry", "--run", directory])


def test_full_guided_review_permission_execution_integration_has_no_model_or_outer_evaluation(
        sources, tmp_path, transport, monkeypatch, review_roots):
    monkeypatch.setattr(permissions, "ACCESS_ROOT", tmp_path / "permissions-access")
    execution_root = tmp_path / "executions"
    with ValidatedReadCache():
        guided = prepare_guided_request(*sources, output_dir=tmp_path / "guided")
        campaign = campaigns.prepare_campaign_plan(guided, {"max_proposals": 1, "max_backtests": 2}, output_dir=tmp_path / "campaign")
        scope = ledger.register_campaign(campaign)["scope_id"]
        draft = {"entry": {"left": {"kind": "reference", "lag": 0}, "operator": "gt", "right": {"kind": "constant", "value": "2"}},
                 "exit": {"left": {"kind": "reference", "lag": 0}, "operator": "lte", "right": {"kind": "constant", "value": "2"}}}
        key, _, _ = captured((scope, (campaign / "request.json").read_bytes()), content=json.dumps(draft))
        def forbidden(*args, **kwargs): pytest.fail("No se permite consultar modelos, red o presupuestos heredados.")
        for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                     "trading_ai.compact_ollama.CompactOllamaProvider.describe", "trading_ai.structured_generation.reserve_compact_generation"):
            monkeypatch.setattr(name, forbidden)
        original_open = Path.open
        def guarded(path, *args, **kwargs):
            if path.name == "evaluation.xml" or (path.name == "comparison.json" and not path.resolve().is_relative_to(execution_root.resolve())):
                pytest.fail("No se permite evaluación exterior.")
            return original_open(path, *args, **kwargs)
        monkeypatch.setattr(Path, "open", guarded)
        candidate = reviews.inspect_candidate(scope, key)
        review = reviews.review_capture(scope, key, assessment(candidate), output_dir=tmp_path / "reviews")
        plan_dir = experiments.prepare_plan(review, output_dir=tmp_path / "plans")
        plan = experiments.verify_plan(plan_dir)
        permit = permissions.grant_permission(plan_dir, declaration(plan, _origin(plan_dir, permissions.PLAN_FILES)), output_dir=tmp_path / "permissions")
        directory = execution.execute(permit, output_dir=execution_root)
        result = execution.verify_execution(directory)
        assert result["completed_backtests"] == ["baseline", "candidate"] and result["assessment"]["origin"] == "python"
        assert ledger.inspect_campaign(scope)["reserved_backtests"] == 2 and len(transport.model_calls) == 1
        assert result["model_requests"] == 0 and result["transport_verified"] is False
