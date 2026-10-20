"""Permisos limitados: fuente declarada, ninguna autorización de proveedor o dinero real."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest

from test_campaign_review import campaign_fixture, review_roots, reviewed
from test_structured_draft import draft
from test_structured_ideas import proposal
from trading_ai import campaign_experiment as experiments
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_permission as permissions
from trading_ai import campaign_review as reviews
from trading_ai import rule_execution as engine
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _canonical


def declaration(plan, origin):
    return {"schema_version": 1, "scope_id": plan["binding"]["scope_id"], "plan_sha256": origin["sha256"]["plan.json"],
            "calculation_id": plan["calculation_id"], "purpose": permissions.PURPOSE, "allowed_backtests": 2,
            "allowed_model_requests": 0, "api_cost_usd": "0", "acknowledge_caller_declared_source": True,
            "authorizer": "Controlador artificial de prueba", "rationale": "Solo cálculo virtual; no acredita autoría o transporte."}


@pytest.fixture
def permission_plan(reviewed, tmp_path, monkeypatch):
    review_dir, fixture = reviewed
    directory = experiments.prepare_plan(review_dir, output_dir=tmp_path / "plans")
    plan = experiments.verify_plan(directory)
    review = reviews.verify_review(review_dir)
    # Aísla verificadores previos ya probados: las huellas y capturas se leen de nuevo.
    monkeypatch.setattr(experiments, "verify_plan", lambda path: deepcopy(plan))
    monkeypatch.setattr(reviews, "verify_review", lambda path: deepcopy(review))
    monkeypatch.setattr(permissions, "ACCESS_ROOT", tmp_path / "permissions-access")
    return directory, plan, fixture


@pytest.fixture
def permitted(permission_plan, tmp_path):
    directory, plan, fixture = permission_plan
    origin = _origin(directory, permissions.PLAN_FILES)
    permit = permissions.grant_permission(directory, declaration(plan, origin), output_dir=tmp_path / "permissions")
    return permit, plan, fixture


@pytest.mark.parametrize("change", ["schema", "scope", "plan", "calculation", "purpose", "backtests", "bool_backtests",
                                   "models", "paid", "source", "authorizer", "rationale", "extra"])
def test_declaration_cannot_expand_scope_budget_or_paid_capabilities(change):
    plan = {"binding": {"scope_id": "a" * 64}, "calculation_id": "b" * 64}
    origin = {"sha256": {"plan.json": "c" * 64}}
    value = declaration(plan, origin)
    if change == "schema": value["schema_version"] = True
    elif change == "scope": value["scope_id"] = "f" * 64
    elif change == "plan": value["plan_sha256"] = "f" * 64
    elif change == "calculation": value["calculation_id"] = "f" * 64
    elif change == "purpose": value["purpose"] = "real_trading"
    elif change == "backtests": value["allowed_backtests"] = 3
    elif change == "bool_backtests": value["allowed_backtests"] = True
    elif change == "models": value["allowed_model_requests"] = 1
    elif change == "paid": value["api_cost_usd"] = "0.01"
    elif change == "source": value["acknowledge_caller_declared_source"] = False
    elif change in ("authorizer", "rationale"): value[change] = " "
    else: value["broker"] = True
    with pytest.raises(ValueError): permissions.validate_declaration(value, plan, origin)


def test_permission_is_exact_and_does_not_reserve_comparison_or_calculate(permission_plan, tmp_path, monkeypatch):
    directory, plan, fixture = permission_plan
    before = ledger.LEDGER_PATH.read_bytes()
    def forbidden(*args, **kwargs): pytest.fail("Conceder permiso no puede enviar, reservar o calcular.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.campaign_ledger.reserve_comparison", "trading_ai.rule_execution._calculate"):
        monkeypatch.setattr(name, forbidden)
    value = declaration(plan, _origin(directory, permissions.PLAN_FILES))
    permit = permissions.grant_permission(directory, value, output_dir=tmp_path / "permissions")
    record, verified = permissions.verify_permission(permit)
    assert record["allowed_backtests"] == 2 and record["allowed_model_requests"] == 0
    assert record["transport_verified"] is record["broker_operations_allowed"] is record["outer_evaluation_allowed"] is False
    assert record["new_usage"] == reviews.ZERO_USAGE and record["calculated_results"] is None
    assert verified == plan and ledger.LEDGER_PATH.read_bytes() == before and not engine.ACCESS_ROOT.exists()
    assert permissions.inspect_permissions(fixture["scope"])["permissions"][0]["status"] == "granted_not_executed"
    with pytest.raises(permissions.PermissionError, match="no se reinicia"):
        permissions.grant_permission(directory, value, output_dir=tmp_path / "new-permission-dir")


def test_legacy_calculation_claim_cannot_be_reset_by_permission(permission_plan, tmp_path):
    directory, plan, _ = permission_plan
    engine.ACCESS_ROOT.mkdir()
    (engine.ACCESS_ROOT / (plan["calculation_id"] + ".json")).write_bytes(b'interrupted')
    with pytest.raises(permissions.PermissionError, match="consumido"):
        permissions.grant_permission(directory, declaration(plan, _origin(directory, permissions.PLAN_FILES)), output_dir=tmp_path / "permissions")
    assert not permissions.ACCESS_ROOT.exists()


@pytest.mark.parametrize("filename", ["permission.json", "permission.json.sha256", "declaration.json", "events.jsonl"])
def test_permission_tampering_is_detected(permitted, filename):
    permit, _, _ = permitted
    with (permit / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): permissions.verify_permission(permit)


def test_new_unresolved_capture_invalidates_permission_without_releasing_it(permitted):
    permit, _, fixture = permitted
    ledger.reserve_proposal(fixture["scope"], "f" * 64)
    with pytest.raises(ValueError): permissions.verify_permission(permit)
    assert len(list(permissions.ACCESS_ROOT.glob("*.json"))) == 1
    assert permissions.inspect_permissions(fixture["scope"])["requires_stop"] is True


def test_changed_review_bytes_or_capture_bytes_invalidates_permission(permitted):
    permit, _, fixture = permitted
    record, _ = permissions.verify_permission(permit)
    review_dir = record["history"]["review_sources"][0]["directory"]
    from pathlib import Path
    path = Path(review_dir) / "assessment.json"
    original = path.read_bytes()
    path.write_bytes(original + b' ')
    with pytest.raises(ValueError): permissions.verify_permission(permit)
    path.write_bytes(original)
    with (fixture["capture"] / "observation.raw").open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): permissions.verify_permission(permit)


def test_comparison_cannot_be_ignored_without_exact_ledger_receipt(permitted):
    permit, plan, fixture = permitted
    receipt = ledger.reserve_comparison(fixture["scope"], fixture["key"], plan["calculation_id"])["receipt"]
    with pytest.raises(ValueError): permissions.verify_permission(permit)
    assert permissions.verify_permission(permit, comparison=receipt)[0]["calculation_id"] == plan["calculation_id"]
    changed = deepcopy(receipt)
    changed["proposal_id"] = "f" * 64
    with pytest.raises(ValueError): permissions.verify_permission(permit, comparison=changed)


def test_permission_interruption_keeps_claim_and_failed_journal(permission_plan, tmp_path, monkeypatch):
    directory, plan, _ = permission_plan
    value = declaration(plan, _origin(directory, permissions.PLAN_FILES))
    original = permissions._record
    def fail(*args): raise OSError("Interrupción artificial después de reservar permiso")
    monkeypatch.setattr(permissions, "_record", fail)
    with pytest.raises(permissions.PermissionError) as failure:
        permissions.grant_permission(directory, value, output_dir=tmp_path / "permissions")
    monkeypatch.setattr(permissions, "_record", original)
    assert not (failure.value.directory / "permission.json").exists()
    with pytest.raises(permissions.PermissionError, match="no se reinicia"):
        permissions.grant_permission(directory, value, output_dir=tmp_path / "retry")
    assert len(list(permissions.ACCESS_ROOT.glob("*.json"))) == 1


def test_status_missing_registry_is_read_only(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_PATH", tmp_path / "missing/registry.sqlite3")
    monkeypatch.setattr(permissions, "ACCESS_ROOT", tmp_path / "missing-permissions")
    with pytest.raises(ValueError): permissions.inspect_permissions("a" * 64)
    assert not ledger.LEDGER_PATH.exists() and not permissions.ACCESS_ROOT.exists()


def test_cli_requires_exact_declaration_and_exposes_no_model_calls(permission_plan, tmp_path, capsys):
    directory, plan, _ = permission_plan
    value = declaration(plan, _origin(directory, permissions.PLAN_FILES))
    path = tmp_path / "declaration.json"
    path.write_bytes(_canonical(value))
    permissions.main(["grant", "--plan-run", str(directory), "--declaration", str(path), "--output-dir", str(tmp_path / "permissions")])
    assert capsys.readouterr().out.strip()
    for action in ("generate", "paid", "reset", "retry"):
        with pytest.raises(SystemExit): permissions.main([action])
