"""Reservas contables compartidas; no activa campañas o autoriza herramientas."""

import argparse
from contextlib import contextmanager
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3

from trading_ai.campaign_plan import _code_hashes as _plan_hashes, validate_campaign_limits, verify_campaign_plan
from trading_ai.formalization import _read, _strict_json
from trading_ai.research import ROOT
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical


LEDGER_PATH = ROOT / ".local/campaign-ledger/registry.sqlite3"
PLAN_FILES = ("campaign.json", "campaign.json.sha256", "limits.json", "request.json", "events.jsonl")
SCHEMA = {
    "scopes": """CREATE TABLE scopes (
        scope_id TEXT NOT NULL PRIMARY KEY,
        record_json TEXT NOT NULL,
        record_sha256 TEXT NOT NULL)""",
    "reservations": """CREATE TABLE reservations (
        scope_id TEXT NOT NULL REFERENCES scopes(scope_id),
        kind TEXT NOT NULL CHECK(kind IN ('proposal', 'comparison')),
        operation_id TEXT NOT NULL,
        proposal_id TEXT NOT NULL,
        receipt_json TEXT NOT NULL,
        receipt_sha256 TEXT NOT NULL,
        PRIMARY KEY(scope_id, kind, operation_id),
        UNIQUE(scope_id, kind, proposal_id))"""}


def _code_hashes():
    return {**_plan_hashes(), "campaign_ledger.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _identifier(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("Se requiere una identidad SHA-256 de 64 caracteres hexadecimales.")
    return value


def _schema(connection, initialize=False):
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    objects = connection.execute("SELECT name, type, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
    if version == 0 and not objects and initialize:
        for sql in SCHEMA.values(): connection.execute(sql)
        connection.execute("PRAGMA user_version = 1")
        version = 1
        objects = connection.execute("SELECT name, type, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
    normalize = lambda sql: " ".join(sql.split()).upper()
    if (version != 1 or len(objects) != len(SCHEMA)
            or any(kind != "table" or name not in SCHEMA or normalize(sql) != normalize(SCHEMA[name])
                   for name, kind, sql in objects)
            or connection.execute("PRAGMA foreign_key_check").fetchone() is not None):
        raise ValueError("Registro SQLite incompatible o incompleto; no se reiniciará.")


@contextmanager
def _connection(*, write):
    path = LEDGER_PATH.resolve()
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = None
    try:
        connection = sqlite3.connect(str(path) if write else path.as_uri() + "?mode=ro",
                                     uri=not write, timeout=5, isolation_level=None)
        connection.execute("PRAGMA foreign_keys = ON")
        if write: connection.execute("PRAGMA synchronous = FULL")
        else: connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        _schema(connection, initialize=write)
        yield connection
        connection.commit()
    except sqlite3.Error as error:
        raise ValueError("No se pudo comprobar o reservar el registro SQLite: " + str(error)) from error
    finally:
        if connection is not None:
            if connection.in_transaction: connection.rollback()
            connection.close()


def _plan_snapshot(directory):
    plan, _ = _artifact(directory, "campaign.json", "campaign_plan_prepared")
    limits = validate_campaign_limits(_strict_json(_read(directory / "limits.json", 1024)))
    identity = {"schema_version": 1, "protocol": "local_campaign_scope_v1",
                "development_sha256": plan["reference"]["development_sha256"], "pair": plan["controls"]["pair"]}
    if (plan["protocol"] != "local_campaign_plan_v1" or plan["status"] != "planned_not_activated"
            or plan["identity"] != identity or plan["scope_id"] != sha256(_canonical(identity)).hexdigest()
            or plan["limits"] != limits or _read(directory / "limits.json", 1024) != _canonical(limits)
            or plan["request_sha256"] != sha256(_read(directory / "request.json", 12288)).hexdigest()
            or plan["code_sha256"] != _plan_hashes()
            or any(plan[key] is not False for key in ("executable", "new_generation_permission", "outer_evaluation_allowed"))):
        raise ValueError("El plan de origen o sus límites han cambiado.")
    return plan, _origin(directory, PLAN_FILES)


def _registration(plan, origin, registered_at):
    return {"schema_version": 1, "protocol": "inactive_campaign_registration_v1", "scope_id": plan["scope_id"],
            "identity": plan["identity"], "plan": origin, "registered_at": registered_at,
            "terms": {key: plan[key] for key in ("limits", "controls", "objective", "data", "provider_policy")},
            "initial_history_sha256": plan["history_sha256"],
            "inherited_generation_budget": plan["inherited_generation_budget"],
            "inherited_usage": plan["inherited_usage"], "code_sha256": _code_hashes(),
            "activation_status": "inactive", "execution_authorized": False,
            "source_freshness_scope": "checked_at_registration_not_before_future_tool_use"}


def _decode(raw, digest):
    if not isinstance(raw, str) or not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("Una entrada del registro tiene un formato incompatible.")
    content = raw.encode("utf-8")
    if sha256(content).hexdigest() != digest:
        raise ValueError("Una entrada del registro no conserva su huella.")
    record = _strict_json(content)
    if not isinstance(record, dict) or _canonical(record) != content:
        raise ValueError("Una entrada del registro no conserva su formato canónico.")
    return record


def _registered(connection, scope_id):
    row = connection.execute("SELECT record_json, record_sha256 FROM scopes WHERE scope_id = ?", (scope_id,)).fetchone()
    if row is None: return None
    record = _decode(*row)
    plan, origin = _plan_snapshot(Path(record["plan"]["directory"]))
    if record != _registration(plan, origin, record["registered_at"]) or record["scope_id"] != scope_id:
        raise ValueError("El registro, plan, código o controles han cambiado.")
    return record


def _receipt(registration, kind, operation_id, proposal_id, created_at):
    identity = {"scope_id": registration["scope_id"], "kind": kind, "operation_id": operation_id}
    return {"schema_version": 1, "protocol": "inactive_campaign_reservation_v1",
            **identity, "receipt_id": sha256(_canonical(identity)).hexdigest(), "proposal_id": proposal_id,
            "created_at": created_at, "state": "reserved_accounting_only_no_result",
            "reserved_model_requests": 1 if kind == "proposal" else 0,
            "reserved_backtests": 2 if kind == "comparison" else 0,
            "execution_authorized": False, "calculated_results": None,
            "registration_sha256": sha256(_canonical(registration)).hexdigest(),
            "new_usage_of_reservation": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0,
                                         "api_cost_usd": "0", "backtests": 0}}


def _state(connection, registration):
    reservations = []
    for kind, operation, proposal, raw, digest in connection.execute(
            "SELECT kind, operation_id, proposal_id, receipt_json, receipt_sha256 FROM reservations WHERE scope_id = ? ORDER BY kind, operation_id",
            (registration["scope_id"],)):
        _identifier(operation); _identifier(proposal)
        receipt = _decode(raw, digest)
        if (kind not in ("proposal", "comparison") or kind == "proposal" and operation != proposal
                or receipt != _receipt(registration, kind, operation, proposal, receipt["created_at"])):
            raise ValueError("Una reserva no corresponde a su identidad o registro.")
        reservations.append(receipt)
    proposals = {item["operation_id"] for item in reservations if item["kind"] == "proposal"}
    comparisons = [item for item in reservations if item["kind"] == "comparison"]
    if any(item["proposal_id"] not in proposals for item in comparisons):
        raise ValueError("Hay una comparación sin reserva de propuesta.")
    limits = registration["terms"]["limits"]
    if len(proposals) > limits["max_proposals"] or 2 * len(comparisons) > limits["max_backtests"]:
        raise ValueError("El registro supera sus límites; no se concederán más reservas.")
    return {"schema_version": 1, "protocol": "inactive_campaign_ledger_v1", "status": "registered_inactive",
            "scope_id": registration["scope_id"], "registration": registration,
            "reserved_model_requests": len(proposals), "reserved_backtests": 2 * len(comparisons),
            "remaining_accounting_slots": {"proposals": limits["max_proposals"] - len(proposals),
                                           "backtests": limits["max_backtests"] - 2 * len(comparisons)},
            "reservations": reservations, "executable_model_requests": 0, "executable_backtests": 0,
            "execution_authorized": False, "current_source_freshness_verified": False,
            "new_usage_of_this_operation": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0,
                                            "api_cost_usd": "0", "backtests": 0}}


def register_campaign(plan_dir: str | Path) -> dict:
    """Vincula un ámbito a sus primeros términos, sin activarlo o sustituir otros límites."""
    directory = Path(plan_dir).resolve()
    _, before = _plan_snapshot(directory)
    verified = verify_campaign_plan(directory)
    plan, origin = _plan_snapshot(directory)
    if plan != verified or origin != before:
        raise ValueError("El plan cambió durante el registro.")
    proposed = _registration(plan, origin, datetime.now(UTC).isoformat())
    with _connection(write=True) as connection:
        existing = _registered(connection, plan["scope_id"])
        if existing is None:
            if _origin(directory, PLAN_FILES) != origin:
                raise ValueError("El plan cambió antes de reservar su ámbito.")
            raw = _canonical(proposed)
            connection.execute("INSERT INTO scopes VALUES (?, ?, ?)",
                               (plan["scope_id"], raw.decode("utf-8"), sha256(raw).hexdigest()))
            existing = proposed
        elif existing["terms"] != proposed["terms"]:
            raise ValueError("El ámbito ya tiene límites y controles fijados; otro plan no los reinicia.")
        return _state(connection, existing)


def inspect_campaign(scope_id: str) -> dict:
    scope_id = _identifier(scope_id)
    if not LEDGER_PATH.exists():
        return {"status": "not_registered", "scope_id": scope_id, "limits": None,
                "remaining_accounting_slots": None, "execution_authorized": False}
    with _connection(write=False) as connection:
        registration = _registered(connection, scope_id)
        if registration is None:
            return {"status": "not_registered", "scope_id": scope_id, "limits": None,
                    "remaining_accounting_slots": None, "execution_authorized": False}
        return _state(connection, registration)


def _reserve(scope_id, kind, operation_id, proposal_id):
    scope_id, operation_id, proposal_id = map(_identifier, (scope_id, operation_id, proposal_id))
    if not LEDGER_PATH.exists(): raise ValueError("No hay una campaña registrada; no se creará al reservar.")
    with _connection(write=True) as connection:
        registration = _registered(connection, scope_id)
        if registration is None: raise ValueError("El ámbito no está registrado.")
        state = _state(connection, registration)
        for receipt in state["reservations"]:
            if receipt["kind"] == kind and receipt["operation_id"] == operation_id:
                if receipt["proposal_id"] != proposal_id:
                    raise ValueError("La operación ya está vinculada a otra propuesta.")
                return {"receipt": receipt, "reused": True, "state": state}
        if kind == "proposal":
            if state["remaining_accounting_slots"]["proposals"] < 1:
                raise ValueError("Límite de propuestas consumido; no se libera por fallos o duplicados.")
        else:
            if not any(item["kind"] == "proposal" and item["operation_id"] == proposal_id for item in state["reservations"]):
                raise ValueError("La comparación requiere una propuesta reservada.")
            if any(item["kind"] == "comparison" and item["proposal_id"] == proposal_id for item in state["reservations"]):
                raise ValueError("La propuesta ya tiene su comparación reservada.")
            if state["remaining_accounting_slots"]["backtests"] < 2:
                raise ValueError("Límite de backtests consumido; no se reserva una comparación parcial.")
        receipt = _receipt(registration, kind, operation_id, proposal_id, datetime.now(UTC).isoformat())
        raw = _canonical(receipt)
        connection.execute("INSERT INTO reservations VALUES (?, ?, ?, ?, ?, ?)",
                           (scope_id, kind, operation_id, proposal_id, raw.decode("utf-8"), sha256(raw).hexdigest()))
        return {"receipt": receipt, "reused": False, "state": _state(connection, registration)}


def reserve_proposal(scope_id: str, request_sha256: str) -> dict:
    """API contable para un futuro controlador; no comprueba o envía esta petición."""
    return _reserve(scope_id, "proposal", request_sha256, request_sha256)


def reserve_comparison(scope_id: str, proposal_request_sha256: str, calculation_id: str) -> dict:
    """No sustituye la revisión aceptada, el plan o la reserva compartida del motor."""
    return _reserve(scope_id, "comparison", calculation_id, proposal_request_sha256)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Trading AI — registro contable de campañas inactivas")
    commands = parser.add_subparsers(dest="command", required=True)
    register = commands.add_parser("register")
    register.add_argument("--plan-run", type=Path, required=True)
    status = commands.add_parser("status")
    status.add_argument("--scope", required=True)
    args = parser.parse_args(argv)
    try:
        result = register_campaign(args.plan_run) if args.command == "register" else inspect_campaign(args.scope)
        print(json.dumps(result, ensure_ascii=True))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Registro de campaña no verificable: {error}\n")


if __name__ == "__main__":
    main()
