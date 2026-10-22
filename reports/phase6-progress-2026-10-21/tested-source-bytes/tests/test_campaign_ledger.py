"""Reservas exclusivas sin proveedor, motor o permisos de ejecución."""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from hashlib import sha256
import json
import multiprocessing
from pathlib import Path
import shutil
import sqlite3

import pytest

from test_campaign_plan import fake_guided, reseal_record
from trading_ai import campaign_ledger as ledger
from trading_ai.campaign_plan import prepare_campaign_plan
from trading_ai.rule_planning import _canonical


def identity(text):
    return sha256(text.encode()).hexdigest()


@pytest.fixture
def isolated_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_PATH", tmp_path / "ledger/registry.sqlite3")


@pytest.fixture
def registered_ledger(fake_guided, tmp_path, isolated_ledger):
    plan = prepare_campaign_plan(fake_guided[0], {"max_proposals": 3, "max_backtests": 6},
                                 output_dir=tmp_path / "plans")
    state = ledger.register_campaign(plan)
    return plan, state["scope_id"]


def test_missing_status_is_read_only_and_does_not_claim_free_budget(isolated_ledger):
    result = ledger.inspect_campaign(identity("absent"))
    assert result["status"] == "not_registered" and result["remaining_accounting_slots"] is None
    assert result["execution_authorized"] is False and not ledger.LEDGER_PATH.parent.exists()
    with pytest.raises(ValueError): ledger.reserve_proposal(identity("absent"), identity("request"))
    assert not ledger.LEDGER_PATH.exists()


def test_register_is_inactive_and_cannot_change_legacy_budget(registered_ledger, fake_guided, monkeypatch):
    plan, scope = registered_ledger
    def forbidden(*args, **kwargs): pytest.fail("El registro no puede consultar o calcular.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.rule_execution._calculate", "trading_ai.structured_generation.reserve_compact_generation"):
        monkeypatch.setattr(name, forbidden)
    before = {p: p.read_bytes() for p in fake_guided[0].iterdir()}
    again = ledger.register_campaign(plan)
    state = ledger.inspect_campaign(scope)
    assert state == again and state["registration"]["inherited_generation_budget"]["consumed"] is True
    assert state["reserved_model_requests"] == state["reserved_backtests"] == 0
    assert state["executable_model_requests"] == state["executable_backtests"] == 0
    assert state["execution_authorized"] is state["current_source_freshness_verified"] is False
    assert state["registration"]["inherited_usage"][0]["usage"][0]["input_tokens"] is None
    assert all(p.read_bytes() == raw for p, raw in before.items())


def test_new_directory_keeps_counts_and_first_binding_but_changed_limits_are_rejected(registered_ledger, fake_guided, tmp_path):
    first, scope = registered_ledger
    ledger.reserve_proposal(scope, identity("first"))
    second = prepare_campaign_plan(fake_guided[0], {"max_proposals": 3, "max_backtests": 6}, output_dir=tmp_path / "other")
    state = ledger.register_campaign(second)
    assert state["reserved_model_requests"] == 1 and state["registration"]["plan"]["directory"] == str(first)
    smaller = prepare_campaign_plan(fake_guided[0], {"max_proposals": 1, "max_backtests": 0}, output_dir=tmp_path / "smaller")
    with pytest.raises(ValueError, match="reinicia"): ledger.register_campaign(smaller)
    assert ledger.inspect_campaign(scope)["reserved_model_requests"] == 1


def test_proposal_receipt_is_idempotent_and_remains_reserved_after_caller_failure(registered_ledger):
    _, scope = registered_ledger
    first = ledger.reserve_proposal(scope, identity("one"))
    with pytest.raises(RuntimeError):
        raise RuntimeError("Fallo artificial del llamador después del compromiso contable.")
    same = ledger.reserve_proposal(scope, identity("one"))
    assert first["reused"] is False and same["reused"] is True and first["receipt"] == same["receipt"]
    assert same["state"]["reserved_model_requests"] == 1
    assert same["receipt"]["execution_authorized"] is False and same["receipt"]["calculated_results"] is None
    ledger.reserve_proposal(scope, identity("two"))
    ledger.reserve_proposal(scope, identity("three"))
    with pytest.raises(ValueError, match="Límite"): ledger.reserve_proposal(scope, identity("four"))
    assert ledger.inspect_campaign(scope)["remaining_accounting_slots"]["proposals"] == 0


def test_comparison_needs_a_proposal_and_reserves_one_pair_once(registered_ledger):
    _, scope = registered_ledger
    with pytest.raises(ValueError, match="propuesta reservada"):
        ledger.reserve_comparison(scope, identity("proposal"), identity("calculation"))
    ledger.reserve_proposal(scope, identity("proposal"))
    first = ledger.reserve_comparison(scope, identity("proposal"), identity("calculation"))
    same = ledger.reserve_comparison(scope, identity("proposal"), identity("calculation"))
    assert same["reused"] is True and first["receipt"] == same["receipt"]
    assert same["state"]["reserved_backtests"] == 2
    with pytest.raises(ValueError, match="ya tiene"):
        ledger.reserve_comparison(scope, identity("proposal"), identity("different calculation"))
    ledger.reserve_proposal(scope, identity("second proposal"))
    with pytest.raises(ValueError, match="otra propuesta"):
        ledger.reserve_comparison(scope, identity("second proposal"), identity("calculation"))
    assert ledger.inspect_campaign(scope)["reserved_backtests"] == 2


@pytest.mark.parametrize("limit", [0, 2])
def test_comparison_budget_is_atomic_and_cannot_be_spent_partially(fake_guided, tmp_path, isolated_ledger, limit):
    plan = prepare_campaign_plan(fake_guided[0], {"max_proposals": 3, "max_backtests": limit}, output_dir=tmp_path / "plans")
    scope = ledger.register_campaign(plan)["scope_id"]
    for i in range(2): ledger.reserve_proposal(scope, identity(f"proposal {i}"))
    if limit:
        ledger.reserve_comparison(scope, identity("proposal 0"), identity("calculation 0"))
    with pytest.raises(ValueError, match="Límite de backtests"):
        ledger.reserve_comparison(scope, identity("proposal 1"), identity("calculation 1"))
    assert ledger.inspect_campaign(scope)["reserved_backtests"] == limit


def test_unknown_scope_does_not_reuse_some_other_campaign(registered_ledger):
    _, scope = registered_ledger
    with pytest.raises(ValueError, match="no está registrado"):
        ledger.reserve_proposal(identity("unknown scope"), identity("request"))
    assert ledger.inspect_campaign(identity("unknown scope"))["remaining_accounting_slots"] is None
    assert ledger.inspect_campaign(scope)["reserved_model_requests"] == 0


def test_twelve_concurrent_threads_can_only_reserve_three_slots(registered_ledger):
    _, scope = registered_ledger
    def attempt(i):
        try:
            return ledger.reserve_proposal(scope, identity(str(i)))
        except ValueError as error:
            assert "Límite" in str(error)
            return None
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(attempt, range(12)))
    assert sum(result is not None for result in results) == 3
    assert ledger.inspect_campaign(scope)["reserved_model_requests"] == 3


def test_concurrent_repeated_key_only_consumes_one_slot(registered_ledger):
    _, scope = registered_ledger
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: ledger.reserve_proposal(scope, identity("same")), range(8)))
    assert sum(not result["reused"] for result in results) == 1
    assert len({result["receipt"]["receipt_id"] for result in results}) == 1
    assert ledger.inspect_campaign(scope)["reserved_model_requests"] == 1


def test_competing_comparisons_cannot_split_the_last_pair(fake_guided, tmp_path, isolated_ledger):
    plan = prepare_campaign_plan(fake_guided[0], {"max_proposals": 3, "max_backtests": 2}, output_dir=tmp_path / "plans")
    scope = ledger.register_campaign(plan)["scope_id"]
    for i in range(3): ledger.reserve_proposal(scope, identity(f"p{i}"))
    def attempt(i):
        try:
            return ledger.reserve_comparison(scope, identity(f"p{i}"), identity(f"c{i}"))
        except ValueError as error:
            assert "Límite de backtests" in str(error)
            return None
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(attempt, range(3)))
    assert sum(result is not None for result in results) == 1
    assert ledger.inspect_campaign(scope)["reserved_backtests"] == 2


def test_another_verified_plan_cannot_replace_registered_risk_controls(registered_ledger, tmp_path, monkeypatch):
    plan, scope = registered_ledger
    other = tmp_path / "other-verified-plan"
    shutil.copytree(plan, other)
    def change(record):
        record["run_dir"] = str(other)
        record["controls"]["initial_capital"] = "9999"
    reseal_record(other, change)
    monkeypatch.setattr(ledger, "verify_campaign_plan", lambda path: ledger._plan_snapshot(path)[0])
    with pytest.raises(ValueError, match="controles fijados"): ledger.register_campaign(other)
    assert ledger.inspect_campaign(scope)["registration"]["terms"]["controls"]["initial_capital"] == "1000"


def test_normal_status_preserves_database_bytes(registered_ledger):
    _, scope = registered_ledger
    ledger.reserve_proposal(scope, identity("first"))
    before = ledger.LEDGER_PATH.read_bytes()
    ledger.inspect_campaign(scope)
    assert ledger.LEDGER_PATH.read_bytes() == before


def spawned_reservation(args):
    path, scope, key = args
    from trading_ai import campaign_ledger as worker
    worker.LEDGER_PATH = Path(path)
    try:
        worker.reserve_proposal(scope, key)
        return "reserved"
    except ValueError as error:
        return str(error)


def test_spawned_processes_share_capacity_already_consumed_by_parent(registered_ledger):
    _, scope = registered_ledger
    ledger.reserve_proposal(scope, identity("parent"))
    tasks = [(str(ledger.LEDGER_PATH), scope, identity(f"child {i}")) for i in range(6)]
    with ProcessPoolExecutor(max_workers=3, mp_context=multiprocessing.get_context("spawn")) as executor:
        results = list(executor.map(spawned_reservation, tasks))
    assert results.count("reserved") == 2
    assert all(result == "reserved" or "Límite" in result for result in results)
    assert ledger.inspect_campaign(scope)["reserved_model_requests"] == 3


def test_failure_before_commit_rolls_back_the_whole_reservation(registered_ledger, monkeypatch):
    _, scope = registered_ledger
    original, calls = ledger._state, []
    def fail_after_insert(*args):
        calls.append(None)
        if len(calls) == 2: raise RuntimeError("Interrupción artificial antes de commit.")
        return original(*args)
    monkeypatch.setattr(ledger, "_state", fail_after_insert)
    with pytest.raises(RuntimeError): ledger.reserve_proposal(scope, identity("rollback"))
    monkeypatch.setattr(ledger, "_state", original)
    assert ledger.inspect_campaign(scope)["reserved_model_requests"] == 0
    assert ledger.reserve_proposal(scope, identity("rollback"))["reused"] is False


@pytest.mark.parametrize("corruption", ["schema_version", "missing_table", "receipt_hash", "rehashed_receipt", "binary_receipt"])
def test_corrupted_state_is_rejected_without_resetting_it(registered_ledger, corruption):
    _, scope = registered_ledger
    ledger.reserve_proposal(scope, identity("first"))
    with sqlite3.connect(ledger.LEDGER_PATH) as connection:
        if corruption == "schema_version": connection.execute("PRAGMA user_version = 2")
        if corruption == "missing_table": connection.execute("DROP TABLE reservations")
        if corruption == "receipt_hash": connection.execute("UPDATE reservations SET receipt_sha256 = ?", ("f" * 64,))
        if corruption == "binary_receipt": connection.execute("UPDATE reservations SET receipt_json = ?", (b"invalid-binary",))
        if corruption == "rehashed_receipt":
            raw, = connection.execute("SELECT receipt_json FROM reservations").fetchone()
            receipt = json.loads(raw)
            receipt["reserved_model_requests"] = 0
            raw = _canonical(receipt)
            connection.execute("UPDATE reservations SET receipt_json = ?, receipt_sha256 = ?",
                               (raw.decode(), sha256(raw).hexdigest()))
    before = ledger.LEDGER_PATH.read_bytes()
    with pytest.raises(ValueError): ledger.inspect_campaign(scope)
    with pytest.raises(ValueError): ledger.reserve_proposal(scope, identity("second"))
    assert ledger.LEDGER_PATH.read_bytes() == before


def test_unreadable_database_is_not_recreated(registered_ledger):
    _, scope = registered_ledger
    ledger.LEDGER_PATH.write_bytes(b"not a SQLite database")
    with pytest.raises(ValueError): ledger.inspect_campaign(scope)
    with pytest.raises(ValueError): ledger.reserve_proposal(scope, identity("second"))
    assert ledger.LEDGER_PATH.read_bytes() == b"not a SQLite database"


def test_changed_original_plan_or_code_is_not_hidden_by_registration(registered_ledger, monkeypatch):
    plan, scope = registered_ledger
    original = ledger._code_hashes
    monkeypatch.setattr(ledger, "_code_hashes", lambda: {**original(), "changed.py": "f" * 64})
    with pytest.raises(ValueError): ledger.inspect_campaign(scope)
    monkeypatch.setattr(ledger, "_code_hashes", original)
    with (plan / "request.json").open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): ledger.inspect_campaign(scope)


def test_ledger_status_does_not_claim_live_history_freshness(registered_ledger, fake_guided):
    plan, scope = registered_ledger
    with (fake_guided[0] / "events.jsonl").open("ab") as stream: stream.write(b' changed')
    state = ledger.inspect_campaign(scope)
    assert state["current_source_freshness_verified"] is state["execution_authorized"] is False
    with pytest.raises(ValueError): ledger.register_campaign(plan)


@pytest.mark.parametrize("value", [None, True, "../escape", "a" * 63, "z" * 64])
def test_invalid_identity_is_rejected_without_database_creation(value, isolated_ledger):
    with pytest.raises(ValueError): ledger.inspect_campaign(value)
    with pytest.raises(ValueError): ledger.reserve_proposal(value, identity("request"))
    assert not ledger.LEDGER_PATH.exists()


def test_cli_only_registers_or_reads_and_has_no_database_override(registered_ledger, capsys):
    plan, scope = registered_ledger
    ledger.main(["register", "--plan-run", str(plan)])
    assert json.loads(capsys.readouterr().out)["execution_authorized"] is False
    ledger.main(["status", "--scope", scope])
    assert json.loads(capsys.readouterr().out)["reserved_model_requests"] == 0
    for action in ("activate", "reserve", "generate", "execute", "release", "reset"):
        with pytest.raises(SystemExit): ledger.main([action])
    with pytest.raises(SystemExit): ledger.main(["status", "--scope", scope, "--database", "other.sqlite3"])
