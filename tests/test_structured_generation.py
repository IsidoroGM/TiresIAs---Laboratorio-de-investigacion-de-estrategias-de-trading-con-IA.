"""Contador exclusivo, interrupciones y separación entre reservar y usar un proveedor."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil

import pytest

from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from test_structured_draft_context import claim_for
from trading_ai.structured_draft_request import prepare_draft_request
from trading_ai.structured_freshness import inspect_request_freshness
from trading_ai.structured_generation import (GenerationReservationError, generation_budget_status, main,
                                            reserve_compact_generation, verify_generation_reservation)
from trading_ai import structured_generation as generation


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr("trading_ai.structured_ideas.ACCESS_ROOT", tmp_path / "ideas-access")
    monkeypatch.setattr("trading_ai.rule_execution.ACCESS_ROOT", tmp_path / "execution-access")
    monkeypatch.setattr("trading_ai.structured_session.ACCESS_ROOT", tmp_path / "sessions-access")
    monkeypatch.setattr(generation, "ACCESS_ROOT", tmp_path / "compact-access")


@pytest.fixture
def prepared_request(memory, tmp_path):
    return prepare_draft_request(memory, output_dir=tmp_path / "requests")


def test_status_does_not_reserve_or_grant_permission(prepared_request):
    status = generation_budget_status(prepared_request)
    assert status["consumed"] is False and status["generation_ready"] is False
    assert status["transport_enabled"] is False and not generation.ACCESS_ROOT.exists()


def test_reservation_uses_one_slot_without_calling_a_model(prepared_request, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail("Reservar no puede enviar o calcular")
    for name in ("trading_ai.ai.create_provider", "socket.create_connection", "socket.socket.connect",
                 "trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.experiments.run_backtest"):
        monkeypatch.setattr(name, forbidden)
    original = {path: path.read_bytes() for path in prepared_request.iterdir()}
    run = reserve_compact_generation(prepared_request, output_dir=tmp_path / "reservations")
    record = verify_generation_reservation(run)
    assert record["reserved_model_requests"] == record["budget"]["model_requests"] == 1
    assert record["budget"]["automatic_retries"] == record["budget"]["backtests"] == 0
    assert record["generation_ready"] is record["submitted"] is record["transport_enabled"] is False
    assert record["provider_context_fit_verified"] is False
    assert record["new_usage"]["model_requests"] == 0 and record["new_usage"]["api_cost_usd"] == "0"
    assert generation_budget_status(prepared_request)["consumed"] is True
    assert all(path.read_bytes() == raw for path, raw in original.items())


def test_repeating_in_a_different_output_directory_cannot_reset_budget(prepared_request, tmp_path):
    reserve_compact_generation(prepared_request, output_dir=tmp_path / "first")
    with pytest.raises(GenerationReservationError, match="consumido"):
        reserve_compact_generation(prepared_request, output_dir=tmp_path / "another")
    assert len(list(generation.ACCESS_ROOT.glob("*.json"))) == 1


def test_repreparing_identical_payload_does_not_give_a_new_slot(prepared_request, memory, tmp_path):
    reserve_compact_generation(prepared_request, output_dir=tmp_path / "first")
    another = prepare_draft_request(memory, output_dir=tmp_path / "different-request")
    assert another != prepared_request
    with pytest.raises(GenerationReservationError, match="consumido"):
        reserve_compact_generation(another, output_dir=tmp_path / "second")


def test_stale_history_fails_before_consuming_a_slot(prepared_request, tmp_path):
    info = inspect_request_freshness(prepared_request)
    claim_for(info["reference"], "a" * 64, tmp_path / "interrupted-rule")
    with pytest.raises(GenerationReservationError, match="desactualizada"):
        reserve_compact_generation(prepared_request, output_dir=tmp_path / "reservations")
    assert generation_budget_status(prepared_request)["consumed"] is False


def test_failure_after_exclusive_claim_does_not_release_attempt(prepared_request, tmp_path, monkeypatch):
    actual, calls = generation.require_current_request, []
    def interrupted(*args, **kwargs):
        calls.append(None)
        if len(calls) == 2: raise ValueError("Historial cambiado después de reservar")
        return actual(*args, **kwargs)
    monkeypatch.setattr(generation, "require_current_request", interrupted)
    with pytest.raises(GenerationReservationError, match="después") as failure:
        reserve_compact_generation(prepared_request, output_dir=tmp_path / "reservations")
    assert generation_budget_status(prepared_request)["consumed"] is True
    assert not (failure.value.directory / "reservation.json").exists()
    monkeypatch.setattr(generation, "require_current_request", actual)
    with pytest.raises(GenerationReservationError, match="consumido"):
        reserve_compact_generation(prepared_request, output_dir=tmp_path / "retry")


def test_simultaneous_attempts_can_reserve_only_once(prepared_request, tmp_path):
    def reserve():
        try:
            return reserve_compact_generation(prepared_request, output_dir=tmp_path / "reservations")
        except GenerationReservationError:
            return None
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: reserve(), range(2)))
    assert sum(result is not None for result in results) == 1
    assert len(list(generation.ACCESS_ROOT.glob("*.json"))) == 1


def test_new_history_does_not_delete_a_valid_historical_reservation(prepared_request, tmp_path):
    run = reserve_compact_generation(prepared_request, output_dir=tmp_path / "reservations")
    record = verify_generation_reservation(run)
    claim_for(inspect_request_freshness(prepared_request)["reference"], "a" * 64, tmp_path / "later-rule")
    assert verify_generation_reservation(run) == record
    assert generation_budget_status(prepared_request)["consumed"] is True


@pytest.mark.parametrize("filename", ["reservation.json", "reservation.json.sha256", "freshness.json", "events.jsonl"])
def test_tampered_reservation_is_rejected(prepared_request, tmp_path, filename):
    run = reserve_compact_generation(prepared_request, output_dir=tmp_path / "reservations")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_generation_reservation(run)


def test_changed_claim_fails_closed(prepared_request, tmp_path):
    reserve_compact_generation(prepared_request, output_dir=tmp_path / "reservations")
    path, = generation.ACCESS_ROOT.glob("*.json")
    path.write_text('{}', encoding="utf-8")
    with pytest.raises(ValueError): generation_budget_status(prepared_request)


def test_reservation_location_cannot_be_changed(prepared_request, tmp_path):
    run = reserve_compact_generation(prepared_request, output_dir=tmp_path / "reservations")
    copied = tmp_path / "copied"
    shutil.copytree(run, copied)
    with pytest.raises(ValueError): verify_generation_reservation(copied)


def test_cli_is_read_only_and_exposes_no_reserve_command(prepared_request, capsys):
    main(["status", "--request-run", str(prepared_request)])
    assert json.loads(capsys.readouterr().out)["consumed"] is False
    with pytest.raises(SystemExit): main(["reserve", "--request-run", str(prepared_request)])
    assert not generation.ACCESS_ROOT.exists()
