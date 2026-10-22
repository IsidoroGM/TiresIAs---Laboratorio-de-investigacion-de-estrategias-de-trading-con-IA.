"""Ciclo integrado artificial con una sola generación y lecturas posteriores sin modelo."""

import json
from pathlib import Path

import pytest

from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews, candidate, assessment
from test_compact_periods import isolated_periods
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from trading_ai.compact_execution import execute_compact_plan, verify_compact_execution
from trading_ai.compact_history import capture_compact_history
from trading_ai.compact_period_execution import execute_compact_periods, verify_compact_period_execution
from trading_ai.compact_periods import prepare_compact_periods
from trading_ai.compact_plan import prepare_compact_plan
from trading_ai.compact_request import prepare_compact_request
from trading_ai.compact_review import SOURCE_FILES, review_compact_candidate
from trading_ai.compact_status import inspect_compact_status
from trading_ai.guided_compact_request import prepare_guided_request, verify_guided_request
from trading_ai.research_session import _origin
from trading_ai.rule_coverage import capture_rule_coverage
from trading_ai.structured_draft_context import prepare_draft_context
from trading_ai.structured_draft_request import prepare_draft_request
from trading_ai.structured_generation import generation_budget_status
from trading_ai.structured_review_memory import capture_review_memory
from trading_ai import rule_execution as engine


def test_artificial_cycle_preserves_one_call_and_separates_review_calculation_and_future_request(candidate, prepared_request, tmp_path, transport, monkeypatch):
    candidate_dir, source = candidate
    def forbidden(*args, **kwargs): pytest.fail("El ciclo posterior no puede volver a consultar el modelo")
    for name in ("trading_ai.compact_ollama.CompactOllamaProvider.complete", "trading_ai.compact_ollama.CompactOllamaProvider.describe", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    assert inspect_compact_status(prepared_request)["status"] == "awaiting_technical_review"
    review = review_compact_candidate(candidate_dir, assessment(source, _origin(candidate_dir, SOURCE_FILES)), output_dir=tmp_path / "reviews")
    registered_plan = prepare_compact_plan(review, output_dir=tmp_path / "plans")
    actual, calls = engine._calculate, []
    def counted(*args):
        calls.append(None)
        return actual(*args)
    monkeypatch.setattr(engine, "_calculate", counted)
    execution = execute_compact_plan(registered_plan, output_dir=tmp_path / "executions")
    result = verify_compact_execution(execution)
    diagnostic = prepare_compact_periods(registered_plan, periods=2, output_dir=tmp_path / "periods")
    diagnostic_run = execute_compact_periods(diagnostic, output_dir=tmp_path / "period-executions")
    periods_result = verify_compact_period_execution(diagnostic_run)
    assert len(calls) == 6 and len(periods_result["period_results"]) == 2
    monkeypatch.setattr(engine, "_calculate", forbidden)
    # Una regla nueva exige renovar el contexto compartido, sin modificar el original.
    original_payload = (prepared_request / "request.json").read_bytes()
    context = prepare_draft_context(source["reference"]["frozen_dir"], output_dir=tmp_path / "current-context")
    reviews = capture_review_memory(context, output_dir=tmp_path / "current-reviews")
    base = prepare_draft_request(reviews, output_dir=tmp_path / "current-base")
    history = capture_compact_history(prepared_request, output_dir=tmp_path / "compact-history")
    coverage = capture_rule_coverage(context, history_dir=history, output_dir=tmp_path / "coverage")
    extended = prepare_compact_request(history, base_request_dir=base, output_dir=tmp_path / "extended")
    guided = prepare_guided_request(extended, coverage, output_dir=tmp_path / "guided")
    packet = verify_guided_request(guided)
    body = json.loads(json.loads((guided / "request.json").read_bytes())["messages"][1]["content"])
    assert body["untrusted_compact_history"][0]["review"]["status"] == "accepted"
    assert '"return_percent":' not in json.loads((guided / "request.json").read_bytes())["messages"][1]["content"]
    assert body["typed_rule_coverage"]["proves_novelty"] is False
    assert body["compact_generation_budget"] == {"consumed": True, "new_permission_granted": False}
    assert len(transport.model_calls) == 1 and generation_budget_status(prepared_request)["consumed"] is True
    assert packet["new_generation_permission"] is packet["submitted"] is False and packet["new_usage"]["model_requests"] == 0
    assert (prepared_request / "request.json").read_bytes() == original_payload
    assert result["scope"] == periods_result["scope"] == "known_development_history_only"
    # El estado de propuesta/revisión no afirma haber inspeccionado las ejecuciones.
    status = inspect_compact_status(prepared_request)
    assert status["status"] == "accepted" and status["execution_state"] == "not_inspected"
