"""Memoria verificable de campaña: propuestas, revisiones y resultados separados."""

import argparse
from contextlib import nullcontext
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import PROJECT_NAME
from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_controller as controller
from trading_ai import campaign_execution as execution
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_permission as permissions
from trading_ai import campaign_review as reviews
from trading_ai import rule_execution as engine
from trading_ai.formalization import _read, _strict_json
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.verification_session import VerificationSession


MEMORY_FILES = ("memory.json", "memory.json.sha256", "events.jsonl")
EXECUTION_FILES = ("results.json", "report.md", "baseline.json", "candidate.json", "development.xml", "comparison.json", "events.jsonl")
MAX_CLAIMS = 128


def _code_hashes():
    return {**permissions._code_hashes(), **{name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in ("campaign_memory.py", "verification_session.py")}}


def _claims(root):
    paths = sorted(root.glob("*.json"))
    if len(paths) > MAX_CLAIMS: raise ValueError("Demasiadas reservas; no se omitirán entradas de memoria.")
    return [(path, _read(path, 262144)) for path in paths]


def _partial(directory, claim, comparison, permission_dir):
    fixed, _ = execution._fixed(permission_dir, comparison)
    if claim != execution._claim(fixed, directory): raise ValueError("El intento parcial no corresponde a su permiso y plan.")
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 4 * 1024 * 1024).splitlines()]
    if not events or events[0]["event"] != "campaign_execution_started": raise ValueError("Falta el inicio del intento de cálculo.")
    tried, done, claimed = [], [], False
    for event in events:
        data, name = event["data"], event["event"]
        if name == "shared_calculation_claimed":
            if claimed or data["sha256"] != sha256(_canonical(claim)).hexdigest(): raise ValueError("Reserva parcial incompatible.")
            claimed = True
        elif name == "backtest_attempted":
            if not claimed or data["role"] != ["baseline", "candidate"][len(tried)] or tried != done:
                raise ValueError("Secuencia de intentos de cálculo no verificable.")
            tried.append(data["role"])
            if data["attempted_backtests"] != tried: raise ValueError("Contadores parciales incompatibles.")
        elif name == "backtest_completed":
            if not tried or len(done) + 1 != len(tried) or data["role"] != tried[-1]: raise ValueError("Cierre parcial incompatible.")
            if sha256(_read(directory / (data["role"] + ".json"), 32 * 1024 * 1024)).hexdigest() != data["sha256"]:
                raise ValueError("Contabilidad parcial alterada.")
            done.append(data["role"])
    failed = events[-1]["event"] == "campaign_execution_failed"
    error = None
    if failed:
        data = events[-1]["data"]
        if (data["shared_calculation_claimed"] is not True or data["attempted_backtests"] != tried
                or data["completed_backtests"] != done or data["comparison_receipt"] != comparison):
            raise ValueError("El fallo no coincide con la reserva y los intentos observados.")
        error = {"type": data["error_type"], "message": data["message"]}
    elif any(event["event"] in ("campaign_execution_failed", "campaign_execution_completed") for event in events):
        raise ValueError("Cierre de cálculo incompatible.")
    files = tuple(name for name in EXECUTION_FILES if (directory / name).is_file())
    return {"status": "failed_consumed" if failed else "interrupted_or_in_progress", "run_dir": str(directory),
            "observed_attempted_backtests": tried, "observed_completed_backtests": done,
            "counts_scope": "recorded_events_not_independent_execution_telemetry", "error": error,
            "source": _origin(directory, files), "assessment": None, "results": None,
            "requires_stop": True, "retry_allowed": False}


def _calculations(scope_id, state, permission_status):
    receipts = {item["operation_id"]: item for item in state["reservations"] if item["kind"] == "comparison"}
    permits = {item["calculation_id"]: item for item in permission_status["permissions"]}
    items, seen, sources = [], set(), []
    for path, raw in _claims(engine.ACCESS_ROOT):
        sources.append({"path": str(path.absolute()), "sha256": sha256(raw).hexdigest()})
        claim = _strict_json(raw)
        if not isinstance(claim, dict): raise ValueError("La reserva compartida debe ser un objeto JSON.")
        if claim.get("protocol") != "campaign_virtual_execution_claim_v1":
            if path.stem in permits or path.stem in receipts:
                seen.add(path.stem)
                items.append({"calculation_id": path.stem, "comparison": receipts.get(path.stem),
                              "status": "unverifiable_shared_claim", "requires_stop": True,
                              "error": "La reserva del cálculo registrado tiene un protocolo desconocido.",
                              "assessment": None, "results": None, "retry_allowed": False})
            continue
        calculation_id = path.stem
        ledger._identifier(calculation_id)
        permit = permits.get(calculation_id)
        if permit is None:
            # Un intento ocupado antes de fallar la reserva SQLite también cuenta.
            try:
                record, _ = _artifact(Path(claim["permission"]["directory"]), "permission.json", "campaign_permission_granted")
                if record["binding"]["scope_id"] != scope_id: continue
            except controller.ERRORS:
                seen.add(calculation_id)
                items.append({"calculation_id": calculation_id, "status": "unattributed_shared_claim",
                              "requires_stop": True, "assessment": None, "results": None, "retry_allowed": False})
                continue
        seen.add(calculation_id)
        item = {"calculation_id": calculation_id, "comparison": receipts.get(calculation_id),
                "status": "unverifiable_execution", "requires_stop": True, "assessment": None, "results": None,
                "retry_allowed": False}
        try:
            directory, permission_dir = Path(claim["execution_run"]), Path(claim["permission"]["directory"])
            if not directory.is_absolute() or not permission_dir.is_absolute(): raise ValueError("Ruta de cálculo no absoluta.")
            if (directory / "results.json").is_file():
                result = execution.verify_execution(directory)
                if (result["binding"]["scope_id"] != scope_id or result["calculation_id"] != calculation_id
                        or result["comparison"] != receipts.get(calculation_id)):
                    raise ValueError("Resultado ajeno al ámbito o a la reserva contable.")
                item.update(status="completed_verified", requires_stop=False, run_dir=str(directory),
                            assessment=result["assessment"], results={role: result[role] for role in ("baseline", "candidate")},
                            spec_sha256=result["proposal"]["spec_sha256"], criterion=result["proposal"]["criterion"],
                            data=result["data"], policy=result["policy"],
                            source=_origin(directory, EXECUTION_FILES), transport_verified=False,
                            automatic_adoption=False, verification_scope=result["verification_scope"])
            else:
                item.update(_partial(directory, claim, receipts.get(calculation_id), permission_dir))
        except controller.ERRORS as error: item["error"] = str(error)[:1000]
        items.append(item)
    for calculation_id, receipt in receipts.items():
        if calculation_id not in seen:
            items.append({"calculation_id": calculation_id, "comparison": receipt, "status": "reserved_without_verified_execution",
                          "requires_stop": True, "assessment": None, "results": None, "retry_allowed": False})
    return sorted(items, key=lambda item: item["calculation_id"]), sources


def _collect(scope_id):
    state = ledger.inspect_campaign(scope_id)
    if state["status"] != "registered_inactive": raise ValueError("No hay una campaña registrada; la memoria no la creará.")
    plan = controller._plan(state)
    usage = attempts.inspect_attempts(scope_id)
    decisions = reviews.inspect_reviews(scope_id)
    permits = permissions.inspect_permissions(scope_id)
    proposals = [controller._proposal(state, receipt, plan) for receipt in state["reservations"] if receipt["kind"] == "proposal"]
    review_sources = [_origin(Path(item["run_dir"]), reviews.REVIEW_FILES) for item in decisions["reviews"] if "run_dir" in item]
    permission_claims = [{"path": str(path.absolute()), "sha256": sha256(raw).hexdigest()} for path, raw in _claims(permissions.ACCESS_ROOT)]
    comparisons, execution_claims = _calculations(scope_id, state, permits)
    return {"schema_version": 1, "protocol": "campaign_result_memory_v1", "scope_id": scope_id,
            "registration": state["registration"], "reservations": state["reservations"],
            "remaining_accounting_slots": state["remaining_accounting_slots"],
            "proposals": proposals, "capture_usage": usage, "reviews": decisions, "review_sources": review_sources,
            "permissions": permits, "permission_claims": permission_claims, "execution_claims": execution_claims,
            "comparisons": comparisons,
            "requires_stop": (usage["requires_stop"] or decisions["requires_stop"] or permits["requires_stop"]
                              or any(item["requires_stop"] for item in comparisons)),
            "scope": "known_development_history_only", "results_origin": "python_engine_when_completed_verified",
            "transport_verified": False, "automatic_adoption": False,
            "future_model_context_integrated": False, "automatic_local_cycle_enabled": False,
            "execution_authorized": False, "model_calls_allowed": False, "broker_operations_allowed": False,
            "outer_evaluation_allowed": False, "new_usage": {**attempts.ZERO_USAGE, "backtests": 0},
            "code_sha256": _code_hashes()}


def inspect_memory(scope_id: str) -> dict:
    """Consulta completa de dos lecturas. Nunca concede intentos ni repite cálculos."""
    first = _collect(scope_id)
    if _canonical(_collect(scope_id)) != _canonical(first):
        raise ValueError("La campaña, fuentes o resultados cambiaron durante la consulta de memoria.")
    return first


def save_memory(scope_id: str, *, output_dir: str | Path = ROOT / ".local/campaign-memory") -> Path:
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("campaign_memory_started", scope_id=scope_id)
    try:
        record = {"run_dir": str(journal.directory), "memory": inspect_memory(scope_id)}
        if len(_canonical(record)) > 120000: raise ValueError("La memoria excede el límite; no se recortarán resultados o errores.")
        _seal(journal, "memory.json", record, "campaign_memory_saved")
    except Exception as error:
        journal.record("campaign_memory_failed", error_type=type(error).__name__, message=str(error)[:1000])
        raise
    return journal.directory


def verify_memory(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "memory.json", "campaign_memory_saved")
    if record["run_dir"] != str(directory) or _canonical(record["memory"]) != _canonical(inspect_memory(record["memory"]["scope_id"])):
        raise ValueError("La memoria guardada ya no coincide con el estado y fuentes actuales.")
    return record["memory"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} — memoria de resultados sin nuevos cálculos")
    parser.add_argument("--cached", action="store_true", help="Reutilizar verificaciones guiadas con guardas de archivos en esta consulta.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect").add_argument("--scope", required=True)
    save = commands.add_parser("save")
    save.add_argument("--scope", required=True)
    save.add_argument("--output-dir", type=Path)
    commands.add_parser("verify").add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        with VerificationSession() if args.cached else nullcontext():
            if args.command == "inspect": result = inspect_memory(args.scope)
            elif args.command == "verify": result = verify_memory(args.run)
            else: result = str(save_memory(args.scope, **({"output_dir": args.output_dir} if args.output_dir else {})))
        print(json.dumps(result, ensure_ascii=True) if isinstance(result, dict) else result)
    except controller.ERRORS as error: parser.exit(1, f"Memoria de campaña detenida: {error}\n")


if __name__ == "__main__": main()
