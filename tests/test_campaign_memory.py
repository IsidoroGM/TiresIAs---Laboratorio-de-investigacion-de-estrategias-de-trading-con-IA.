"""Memoria de pruebas artificiales; nunca consulta modelos ni reejecuta resultados."""

import json

import pytest

from test_campaign_execution import virtual
from test_campaign_permission import permission_plan, permitted
from test_campaign_review import campaign_fixture, review_roots, reviewed, assessment
from test_structured_draft import draft
from test_structured_ideas import proposal
from trading_ai import campaign_execution as execution
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_memory as memory
from trading_ai import campaign_permission as permissions
from trading_ai import campaign_review as reviews
from trading_ai import rule_execution as engine


def prohibit(monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail("La memoria no puede enviar, reservar, revisar ni calcular.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.compact_ollama.CompactOllamaProvider.describe", "trading_ai.rule_execution._calculate",
                 "trading_ai.campaign_ledger.reserve_proposal", "trading_ai.campaign_ledger.reserve_comparison",
                 "trading_ai.campaign_permission.grant_permission", "trading_ai.campaign_review.review_capture"):
        monkeypatch.setattr(name, forbidden)


def test_pending_review_and_usage_remain_separate_without_calculation(campaign_fixture, tmp_path, monkeypatch):
    fixture = campaign_fixture
    monkeypatch.setattr(permissions, "ACCESS_ROOT", tmp_path / "permission-access")
    before = ledger.LEDGER_PATH.read_bytes()
    prohibit(monkeypatch)
    result = memory.inspect_memory(fixture["scope"])
    assert result["proposals"][0]["status"] == "pending_technical_review"
    assert result["proposals"][0]["model_description"] is None
    assert result["reviews"]["reviews"][0]["status"] == "not_reviewed"
    assert result["comparisons"] == [] and result["capture_usage"]["usage"]["model_requests"] == 1
    assert result["capture_usage"]["inherited_usage"][0]["usage"][0]["input_tokens"] is None
    assert result["new_usage"] == {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0}
    assert result["automatic_local_cycle_enabled"] is result["future_model_context_integrated"] is False
    assert ledger.LEDGER_PATH.read_bytes() == before and not engine.ACCESS_ROOT.exists()


@pytest.mark.parametrize("decision", ["rejected", "needs_clarification"])
def test_discarded_review_remains_in_memory(campaign_fixture, tmp_path, monkeypatch, decision):
    fixture = campaign_fixture
    monkeypatch.setattr(permissions, "ACCESS_ROOT", tmp_path / "permission-access")
    view = reviews.inspect_candidate(fixture["scope"], fixture["key"])
    reviews.review_capture(fixture["scope"], fixture["key"], assessment(view, decision), output_dir=tmp_path / "reviews")
    result = memory.inspect_memory(fixture["scope"])
    assert result["reviews"]["reviews"][0]["status"] == decision and result["comparisons"] == []


def test_completed_python_results_enter_memory_without_recalculation(virtual, tmp_path, monkeypatch):
    run = execution.execute(virtual[0], output_dir=tmp_path / "executions")
    original = execution.verify_execution(run)
    before = ledger.LEDGER_PATH.read_bytes()
    prohibit(monkeypatch)
    result = memory.inspect_memory(virtual[2]["scope"])
    item = result["comparisons"][0]
    assert item["status"] == "completed_verified" and not result["requires_stop"]
    assert item["assessment"] == original["assessment"] and item["assessment"]["criterion_status"] == "inconclusive"
    assert item["results"]["candidate"] == original["candidate"]
    assert item["automatic_adoption"] is item["transport_verified"] is False
    assert result["remaining_accounting_slots"]["backtests"] == 4
    assert ledger.LEDGER_PATH.read_bytes() == before
    saved = memory.save_memory(virtual[2]["scope"], output_dir=tmp_path / "memories")
    assert memory.verify_memory(saved) == result


@pytest.mark.parametrize("fail_on", [1, 2])
def test_failed_and_partial_calculations_keep_consumed_attempts(virtual, tmp_path, monkeypatch, fail_on):
    original, calls = engine._calculate, []
    def fail(*args):
        calls.append(None)
        if len(calls) == fail_on: raise RuntimeError("Fallo artificial conservado")
        return original(*args)
    monkeypatch.setattr(engine, "_calculate", fail)
    with pytest.raises(execution.ExecutionError): execution.execute(virtual[0], output_dir=tmp_path / "executions")
    prohibit(monkeypatch)
    result = memory.inspect_memory(virtual[2]["scope"])
    item = result["comparisons"][0]
    assert item["status"] == "failed_consumed" and result["requires_stop"]
    assert item["observed_attempted_backtests"] == ["baseline", "candidate"][:fail_on]
    assert item["observed_completed_backtests"] == ([] if fail_on == 1 else ["baseline"])
    assert item["results"] is item["assessment"] is None and item["retry_allowed"] is False
    assert item["error"]["message"] == "Fallo artificial conservado" and len(calls) == fail_on
    assert result["remaining_accounting_slots"]["backtests"] == 4


def test_shared_claim_before_failed_sqlite_reservation_is_not_lost(virtual, tmp_path, monkeypatch):
    def fail(*args): raise ValueError("Registro artificial no disponible")
    monkeypatch.setattr(ledger, "reserve_comparison", fail)
    with pytest.raises(execution.ExecutionError): execution.execute(virtual[0], output_dir=tmp_path / "executions")
    prohibit(monkeypatch)
    result = memory.inspect_memory(virtual[2]["scope"])
    assert result["comparisons"][0]["status"] == "failed_consumed" and result["requires_stop"]
    assert result["comparisons"][0]["comparison"] is None
    assert result["comparisons"][0]["observed_attempted_backtests"] == []
    assert result["remaining_accounting_slots"]["backtests"] == 6


def test_receipt_without_shared_execution_remains_unresolved(permission_plan):
    _, plan, fixture = permission_plan
    ledger.reserve_comparison(fixture["scope"], fixture["key"], plan["calculation_id"])
    result = memory.inspect_memory(fixture["scope"])
    assert result["comparisons"][0]["status"] == "reserved_without_verified_execution"
    assert result["requires_stop"] and result["comparisons"][0]["results"] is None


@pytest.mark.parametrize("has_receipt", [False, True])
def test_unknown_shared_claim_for_existing_permission_cannot_be_ignored(permitted, has_receipt):
    _, plan, fixture = permitted
    if has_receipt: ledger.reserve_comparison(fixture["scope"], fixture["key"], plan["calculation_id"])
    engine.ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
    (engine.ACCESS_ROOT / (plan["calculation_id"] + ".json")).write_text('{"protocol":"unknown"}', encoding="utf-8")
    result = memory.inspect_memory(fixture["scope"])
    assert result["requires_stop"] and len(result["comparisons"]) == 1
    assert result["comparisons"][0]["status"] == "unverifiable_shared_claim"
    assert result["comparisons"][0]["results"] is None and result["comparisons"][0]["retry_allowed"] is False


def test_non_object_shared_claim_is_rejected_explicitly(permitted):
    _, plan, fixture = permitted
    engine.ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
    (engine.ACCESS_ROOT / (plan["calculation_id"] + ".json")).write_text('[]', encoding="utf-8")
    with pytest.raises(ValueError, match="objeto JSON"): memory.inspect_memory(fixture["scope"])


def test_saved_memory_becomes_stale_after_new_reservation(campaign_fixture, tmp_path, monkeypatch):
    fixture = campaign_fixture
    monkeypatch.setattr(permissions, "ACCESS_ROOT", tmp_path / "permission-access")
    saved = memory.save_memory(fixture["scope"], output_dir=tmp_path / "memories")
    ledger.reserve_proposal(fixture["scope"], "e" * 64)
    with pytest.raises(ValueError, match="coincide"): memory.verify_memory(saved)
    result = memory.inspect_memory(fixture["scope"])
    assert result["requires_stop"] and result["capture_usage"]["usage"]["input_tokens"] is None


@pytest.mark.parametrize("filename", ["results.json", "baseline.json", "report.md"])
def test_tampered_result_never_enters_verified_memory(virtual, tmp_path, filename):
    directory = execution.execute(virtual[0], output_dir=tmp_path / "executions")
    with (directory / filename).open("ab") as stream: stream.write(b' changed')
    item = memory.inspect_memory(virtual[2]["scope"])["comparisons"][0]
    assert item["status"] == "unverifiable_execution" and item["requires_stop"]
    assert item["assessment"] is item["results"] is None


def test_cli_only_inspects_and_stops_on_unknown_scope(campaign_fixture, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(permissions, "ACCESS_ROOT", tmp_path / "permission-access")
    memory.main(["inspect", "--scope", campaign_fixture["scope"]])
    assert json.loads(capsys.readouterr().out)["automatic_local_cycle_enabled"] is False
    with pytest.raises(SystemExit): memory.main(["inspect", "--scope", "a" * 64])
