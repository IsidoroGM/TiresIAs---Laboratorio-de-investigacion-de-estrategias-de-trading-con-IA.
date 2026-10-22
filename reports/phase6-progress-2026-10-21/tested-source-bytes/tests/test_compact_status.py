"""Consulta breve sin acciones, inferencias, resultados de ejecución o costes inventados."""

from pathlib import Path
import json

import pytest

from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews, candidate, assessment
from test_compact_request import duplicate_memory
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from trading_ai.compact_review import SOURCE_FILES, review_compact_candidate
from trading_ai.compact_status import inspect_compact_status, main, _source_usage
from trading_ai.research_session import _origin
from trading_ai.structured_generation import reserve_compact_generation
from trading_ai import compact_status as statuses
from trading_ai import structured_generation as generation


def test_no_attempt_is_not_a_generation_permission(prepared_request, tmp_path):
    status = inspect_compact_status(prepared_request)
    assert status["status"] == "no_attempt_reserved" and status["generation_budget"]["consumed"] is False
    assert status["new_generation_permission"] is False and not generation.ACCESS_ROOT.exists()
    assert status["source_usage"] == {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0"}


def test_duplicate_status_is_read_only_and_separates_origin_usage(duplicate_memory, prepared_request, tmp_path, monkeypatch):
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    def forbidden(*args, **kwargs): pytest.fail("Consultar estado no puede actuar o consultar modelos")
    for name in ("trading_ai.compact_ollama.CompactOllamaProvider.complete", "trading_ai.compact_ollama.CompactOllamaProvider.describe",
                 "trading_ai.rule_execution._calculate", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    status = inspect_compact_status(prepared_request)
    assert status["status"] == "duplicate_rules" and status["generation_budget"]["consumed"] is True
    assert status["source_usage"] == {"model_requests": 1, "input_tokens": 100, "output_tokens": 60, "api_cost_usd": "0"}
    assert status["new_usage"]["model_requests"] == status["new_usage"]["backtests"] == 0
    assert status["usage_scope"] == "compact_attempts_only_excludes_legacy" and status["execution_state"] == "not_inspected"
    assert {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before


def test_reserved_unknown_usage_is_not_rendered_as_zero(prepared_request, tmp_path):
    reserve_compact_generation(prepared_request, output_dir=tmp_path / "reservations")
    status = inspect_compact_status(prepared_request)
    assert status["status"] == "reserved_without_submission" and status["generation_budget"]["consumed"]
    assert status["source_usage"] == {"model_requests": None, "input_tokens": None, "output_tokens": None, "api_cost_usd": None}


def test_pending_candidate_requires_review_and_does_not_claim_execution_state(candidate, prepared_request):
    status = inspect_compact_status(prepared_request)
    assert status["status"] == "awaiting_technical_review" and status["executable"] is False
    assert status["inspection_scope"] == "proposal_and_review_only_executions_not_inspected"


@pytest.mark.parametrize("decision", ["accepted", "rejected", "needs_clarification"])
def test_review_decision_is_reported_without_granting_execution(candidate, prepared_request, tmp_path, decision):
    run, candidate_record = candidate
    review_compact_candidate(run, assessment(candidate_record, _origin(run, SOURCE_FILES), decision), output_dir=tmp_path / "reviews")
    status = inspect_compact_status(prepared_request)
    assert status["status"] == decision and status["executable"] is status["new_generation_permission"] is False
    assert status["generation_budget"]["consumed"] is True


def test_corrupt_claim_is_an_error_instead_of_an_available_attempt(candidate, prepared_request):
    claim, = generation.ACCESS_ROOT.glob("*.json")
    claim.write_bytes(b'{}')
    with pytest.raises(ValueError): inspect_compact_status(prepared_request)


def test_changed_state_during_double_read_is_refused(prepared_request, monkeypatch):
    actual, calls = statuses._snapshot, []
    def changed(*args):
        record = actual(*args)
        calls.append(None)
        if len(calls) == 2: record["status"] = "unexpected_change"
        return record
    monkeypatch.setattr(statuses, "_snapshot", changed)
    with pytest.raises(ValueError, match="cambió"): inspect_compact_status(prepared_request)


def test_usage_without_token_metrics_remains_unknown():
    entries = [{"source_usage": {"model_requests": 1, "usage": [], "api_cost_usd": "0"}}]
    assert _source_usage(entries) == {"model_requests": 1, "input_tokens": None, "output_tokens": None, "api_cost_usd": "0"}


def test_cli_is_three_lines_or_explicit_json_without_an_action_command(duplicate_memory, prepared_request, capsys):
    main(["--request-run", str(prepared_request)])
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3 and "duplicadas" in lines[0] and "consumido" in lines[1]
    main(["--request-run", str(prepared_request), "--json"])
    assert json.loads(capsys.readouterr().out)["new_usage"]["model_requests"] == 0
    with pytest.raises(SystemExit): main(["--request-run", str(prepared_request), "--generate"])
