"""Permiso explícito para una comparación virtual; ninguna autorización de IA o bróker."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import PROJECT_NAME
from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_experiment as experiments
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_review as reviews
from trading_ai import rule_execution as engine
from trading_ai.campaign_controller import ERRORS
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import BUDGET, _artifact, _canonical, _seal


ACCESS_ROOT = ROOT / ".local/campaign-calculation-permissions"
PLAN_FILES = ("plan.json", "plan.json.sha256", "development.xml", "events.jsonl")
PERMISSION_FILES = ("permission.json", "permission.json.sha256", "declaration.json", "events.jsonl")
PURPOSE = "offline_virtual_evaluation_of_declared_source"
REQUIREMENTS = ["explicit_campaign_allowance", "fresh_full_campaign_history_and_sources", "verified_capture_origin",
                "atomic_campaign_comparison_reservation", "shared_engine_calculation_claim", "controlled_executor"]


class PermissionError(ValueError):
    def __init__(self, message, directory):
        super().__init__(message)
        self.directory = directory


def _code_hashes():
    return {**experiments._code_hashes(), **{name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in ("campaign_permission.py", "campaign_execution.py")}}


def validate_declaration(value, plan, origin):
    expected = {"schema_version": 1, "scope_id": plan["binding"]["scope_id"],
                "plan_sha256": origin["sha256"]["plan.json"], "calculation_id": plan["calculation_id"],
                "purpose": PURPOSE, "allowed_backtests": 2, "allowed_model_requests": 0, "api_cost_usd": "0",
                "acknowledge_caller_declared_source": True}
    if (not isinstance(value, dict) or set(value) != set(expected) | {"authorizer", "rationale"}
            or _canonical({key: value[key] for key in expected}) != _canonical(expected)):
        raise ValueError("Se requiere un permiso exacto de dos backtests virtuales, sin modelos, pagos o campos adicionales.")
    for key, maximum in (("authorizer", 80), ("rationale", 1200)):
        if not isinstance(value[key], str) or not value[key].strip() or len(value[key]) > maximum:
            raise ValueError("Autor y motivo del permiso deben ser textos no vacíos y acotados.")


def _sources(plan_dir, comparison=None):
    plan = experiments.verify_plan(plan_dir)
    if (plan["execution_requirements"] != REQUIREMENTS or plan["budget"] != BUDGET
            or plan["outer_evaluation_allowed"] is not False or plan["transport_verified"] is not False):
        raise ValueError("Contrato de ejecución o procedencia no admitido por este permiso virtual.")
    state = ledger.inspect_campaign(plan["binding"]["scope_id"])
    if state["status"] != "registered_inactive": raise ValueError("La campaña no está registrada.")
    if _canonical(state["registration"]["terms"]["controls"]) != _canonical(plan["policy"]):
        raise ValueError("Los controles del registro no coinciden con el plan.")
    if comparison is not None:
        if (not isinstance(comparison, dict) or comparison.get("kind") != "comparison" or comparison.get("operation_id") != plan["calculation_id"]
                or comparison.get("proposal_id") != plan["binding"]["request_sha256"]
                or comparison.get("scope_id") != plan["binding"]["scope_id"]
                or not any(_canonical(item) == _canonical(comparison) for item in state["reservations"])):
            raise ValueError("La reserva de comparación no corresponde al plan y registro.")
    remaining = [item for item in state["reservations"] if item["kind"] == "comparison"
                 and (comparison is None or item["receipt_id"] != comparison["receipt_id"])]
    if remaining:
        raise ValueError("Hay otras comparaciones cuyo resultado no está incorporado; se detiene este permiso inicial.")
    if comparison is None and state["remaining_accounting_slots"]["backtests"] < 2:
        raise ValueError("No quedan dos huecos contables para esta comparación.")
    usage = attempts.inspect_attempts(plan["binding"]["scope_id"])
    decisions = reviews.inspect_reviews(plan["binding"]["scope_id"])
    if usage["requires_stop"] or decisions["requires_stop"]:
        raise ValueError("Hay consumo, capturas o revisiones no verificables.")
    captures = []
    for receipt in state["reservations"]:
        if receipt["kind"] != "proposal": continue
        directory, _, _, completion = attempts._load(state, receipt)
        if completion is None: raise ValueError("Hay una captura sin cerrar.")
        files = tuple(name for name in reviews.controller.CAPTURE_FILES if (directory / name).is_file())
        captures.append(_origin(directory, files))
    review_sources = [_origin(Path(item["run_dir"]), reviews.REVIEW_FILES) for item in decisions["reviews"] if "run_dir" in item]
    memory = {"registration": state["registration"],
              "proposal_reservations": [item for item in state["reservations"] if item["kind"] == "proposal"],
              "captures": captures, "usage": usage, "reviews": decisions, "review_sources": review_sources}
    return plan, _origin(plan_dir, PLAN_FILES), memory


def _access(plan):
    return ACCESS_ROOT.resolve() / (plan["calculation_id"] + ".json")


def _claim(directory, plan, origin):
    return {"schema_version": 1, "permission_dir": str(directory), "calculation_id": plan["calculation_id"],
            "scope_id": plan["binding"]["scope_id"], "plan": origin, "code_sha256": _code_hashes()}


def _record(directory, plan, origin, memory, declaration):
    validate_declaration(declaration, plan, origin)
    raw = _read(directory / "declaration.json", 16384)
    if _canonical(_strict_json(raw)) != _canonical(declaration): raise ValueError("La declaración guardada cambió.")
    access_raw = _read(_access(plan), 32768)
    if access_raw != _canonical(_claim(directory, plan, origin)): raise ValueError("El permiso no posee su reserva exclusiva.")
    return {"schema_version": 1, "protocol": "campaign_virtual_calculation_permission_v1", "status": "granted_not_executed",
            "run_dir": str(directory), "plan": origin, "binding": deepcopy(plan["binding"]),
            "calculation_id": plan["calculation_id"], "purpose": PURPOSE, "declaration": deepcopy(declaration),
            "declaration_sha256": sha256(raw).hexdigest(), "authority_origin": "local_caller_declaration_not_external_authentication",
            "history": memory, "history_sha256": sha256(_canonical(memory)).hexdigest(),
            "capture_origin_scope": "verified_recorded_linkage_not_verified_model_transport",
            "transport_verified": False, "allowed_backtests": 2, "allowed_model_requests": 0,
            "broker_operations_allowed": False, "outer_evaluation_allowed": False,
            "access": {"path": str(_access(plan)), "sha256": sha256(access_raw).hexdigest()},
            "executable": False, "calculated_results": None, "new_usage": dict(reviews.ZERO_USAGE), "code_sha256": _code_hashes()}


def grant_permission(plan_dir: str | Path, declaration: dict, *, output_dir: str | Path = ROOT / ".local/campaign-permissions") -> Path:
    plan_dir = Path(plan_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("campaign_permission_started", plan_dir=str(plan_dir))
    try:
        sources = _sources(plan_dir)
        plan, origin, memory = sources
        validate_declaration(declaration, plan, origin)
        if (engine.ACCESS_ROOT / (plan["calculation_id"] + ".json")).exists():
            raise ValueError("El cálculo ya está consumido en el motor.")
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        try: _write_exclusive(_access(plan), _canonical(_claim(journal.directory, plan, origin)))
        except FileExistsError as error: raise ValueError("Este cálculo ya tiene permiso o una preparación interrumpida; no se reinicia.") from error
        journal.save("declaration.json", declaration)
        record = _record(journal.directory, *sources, declaration)
        if _canonical(_sources(plan_dir)) != _canonical(sources):
            raise ValueError("Las fuentes o memoria cambiaron al conceder el permiso; se conserva la reserva.")
        _seal(journal, "permission.json", record, "campaign_permission_granted")
    except Exception as error:
        journal.record("campaign_permission_failed", error_type=type(error).__name__, message=str(error)[:1000], new_usage=dict(reviews.ZERO_USAGE))
        raise PermissionError(str(error), journal.directory) from error
    return journal.directory


def verify_permission(run_dir: str | Path, *, comparison: dict | None = None) -> tuple[dict, dict]:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "permission.json", "campaign_permission_granted")
    sources = _sources(Path(record["plan"]["directory"]), comparison)
    declaration = _strict_json(_read(directory / "declaration.json", 16384))
    expected = _record(directory, *sources, declaration)
    if _canonical(record) != _canonical(expected): raise ValueError("El permiso, plan, memoria, controles o código han cambiado.")
    return record, sources[0]


def inspect_permissions(scope_id: str) -> dict:
    state = ledger.inspect_campaign(scope_id)
    if state["status"] != "registered_inactive": raise ValueError("El ámbito no está registrado.")
    items = []
    paths = sorted(ACCESS_ROOT.glob("*.json"))
    if len(paths) > 128: raise ValueError("Demasiados permisos; no se omitirán entradas.")
    for path in paths:
        claim = _strict_json(_read(path, 32768))
        ledger._identifier(claim["scope_id"]); ledger._identifier(claim["calculation_id"])
        if path.stem != claim["calculation_id"]: raise ValueError("Reserva de permiso incompatible.")
        if claim["scope_id"] != scope_id: continue
        directory = Path(claim["permission_dir"])
        if not directory.is_absolute(): raise ValueError("Ruta de permiso no absoluta.")
        item = {"calculation_id": claim["calculation_id"], "run_dir": str(directory), "status": "unverifiable_permission"}
        try:
            comparison = next((entry for entry in state["reservations"] if entry["kind"] == "comparison"
                               and entry["operation_id"] == claim["calculation_id"]), None)
            record, _ = verify_permission(directory, comparison=comparison)
            item["status"] = "calculation_claimed" if (engine.ACCESS_ROOT / (record["calculation_id"] + ".json")).exists() else record["status"]
        except ERRORS as error: item["error"] = str(error)[:1000]
        items.append(item)
    return {"schema_version": 1, "protocol": "campaign_permission_status_v1", "scope_id": scope_id, "permissions": items,
            "requires_stop": any(item["status"] == "unverifiable_permission" for item in items),
            "scope": "permission_registry_not_execution_preflight", "new_usage": dict(reviews.ZERO_USAGE),
            "model_calls_allowed": False, "broker_operations_allowed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} — permiso de comparación virtual sin modelos o bróker")
    commands = parser.add_subparsers(dest="command", required=True)
    grant = commands.add_parser("grant")
    grant.add_argument("--plan-run", type=Path, required=True)
    grant.add_argument("--declaration", type=Path, required=True)
    grant.add_argument("--output-dir", type=Path)
    commands.add_parser("status").add_argument("--scope", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "status": print(json.dumps(inspect_permissions(args.scope), ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(grant_permission(args.plan_run, _strict_json(_read(args.declaration, 16384)), **kwargs))
    except ERRORS as error: parser.exit(1, f"Permiso virtual detenido: {error}\n")


if __name__ == "__main__": main()
