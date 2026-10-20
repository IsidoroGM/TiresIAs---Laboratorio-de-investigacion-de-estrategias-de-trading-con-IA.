"""Revisión técnica por captura: declaración única, sin envío o simulación."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import PROJECT_NAME
from trading_ai import campaign_controller as controller
from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_ledger as ledger
from trading_ai.compact_review import CHECKS
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal


ACCESS_ROOT = ROOT / ".local/campaign-review-access"
BINDING_FIELDS = ("scope_id", "request_sha256", "receipt_id", "observation_sha256", "spec_sha256")
REVIEW_FILES = ("review.json", "review.json.sha256", "candidate.json", "assessment.json", "events.jsonl")
ZERO_USAGE = {**attempts.ZERO_USAGE, "backtests": 0}


class CampaignReviewError(ValueError):
    def __init__(self, message, directory):
        super().__init__(message)
        self.directory = directory


def _code_hashes():
    return {**controller._code_hashes(), **{name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in ("compact_review.py", "campaign_review.py")}}


def inspect_candidate(scope_id: str, request_sha256: str, *, allow_existing_comparisons: bool = False) -> dict:
    """Vista de la captura exacta; no registra una candidata o una decisión."""
    ledger._identifier(request_sha256)
    state = ledger.inspect_campaign(scope_id)
    if state["status"] != "registered_inactive": raise ValueError("El ámbito no está registrado.")
    if state["reserved_backtests"] and not allow_existing_comparisons:
        raise ValueError("No se aprobarán revisiones después de reservar comparaciones.")
    code = _code_hashes()
    plan = controller._plan(state)
    summary = attempts.inspect_attempts(scope_id)
    if summary["requires_stop"]: raise ValueError("Hay capturas o consumo no verificables; se detiene la revisión.")
    receipts = [item for item in state["reservations"] if item["kind"] == "proposal" and item["operation_id"] == request_sha256]
    if len(receipts) != 1: raise ValueError("No hay una única reserva de propuesta correspondiente.")
    item = controller._proposal(state, receipts[0], plan)
    if item["status"] != "pending_technical_review":
        raise ValueError("Solo reglas válidas pendientes admiten revisión; no se aprueban duplicados o errores.")
    binding = {"scope_id": scope_id, "request_sha256": request_sha256, "receipt_id": item["receipt_id"],
               "observation_sha256": item["capture"]["sha256"]["observation.raw"], "spec_sha256": item["spec_sha256"]}
    record = {"schema_version": 1, "protocol": "campaign_review_candidate_v1", "binding": binding,
              "registration": deepcopy(state["registration"]["plan"]), "reference": deepcopy(plan["reference"]),
              "capture": deepcopy(item["capture"]), "draft": deepcopy(item["draft"]),
              "rule_description": deepcopy(item["rule_description"]), "model_description": None,
              "description_origin": "python_from_typed_rules_not_model_prose",
              "controls": deepcopy(plan["controls"]), "objective": deepcopy(plan["objective"]),
              "campaign_limits": deepcopy(plan["limits"]),
              "attempt_usage": next(entry["usage"] for entry in summary["attempts"] if entry["request_sha256"] == request_sha256),
              "prior_compact_usage": deepcopy(summary["inherited_usage"]),
              "source_origin": "caller_observation_not_verified_transport", "transport_verified": False,
              "executable": False, "calculated_results": None, "code_sha256": code}
    if (ledger.inspect_campaign(scope_id) != state or _canonical(controller._plan(state)) != _canonical(plan)
            or attempts.inspect_attempts(scope_id) != summary or _code_hashes() != code
            or _origin(Path(item["capture"]["directory"]), tuple(item["capture"]["sha256"])) != item["capture"]):
        raise ValueError("Las fuentes, capturas, controles o reservas cambiaron durante la revisión.")
    return record


def validate_assessment(value: dict, candidate: dict) -> None:
    fields = {"schema_version", *BINDING_FIELDS, "reviewer", "decision", "rationale", "checks"}
    if (not isinstance(value, dict) or set(value) != fields or type(value["schema_version"]) is not int
            or value["schema_version"] != 1
            or any(value[key] != candidate["binding"][key] for key in BINDING_FIELDS)):
        raise ValueError("La declaración debe identificar exactamente la captura, petición y reglas, sin campos extra.")
    for key, limit in (("reviewer", 80), ("rationale", 1200)):
        if not isinstance(value[key], str) or not value[key].strip() or len(value[key]) > limit:
            raise ValueError("Revisor y motivo deben ser textos no vacíos y acotados.")
    checks = value["checks"]
    if (not isinstance(checks, dict) or set(checks) != set(CHECKS)
            or any(type(flag) is not bool for flag in checks.values())):
        raise ValueError("Se requieren las seis comprobaciones booleanas de revisión.")
    if not isinstance(value["decision"], str) or value["decision"] not in ("accepted", "rejected", "needs_clarification"):
        raise ValueError("Decisión de revisión no admitida.")
    if value["decision"] == "accepted" and not all(checks.values()):
        raise ValueError("Aceptar requiere todas las comprobaciones; no demuestra rentabilidad.")


def _access(binding):
    return ACCESS_ROOT.resolve() / (binding["receipt_id"] + ".json")


def _claim(directory, candidate):
    return {"schema_version": 1, "review_dir": str(directory), "binding": candidate["binding"],
            "candidate_sha256": sha256(_canonical(candidate)).hexdigest(), "code_sha256": _code_hashes()}


def _record(directory, candidate, assessment):
    validate_assessment(assessment, candidate)
    candidate_raw = _read(directory / "candidate.json", 131072)
    assessment_raw = _read(directory / "assessment.json", 16384)
    if (_canonical(_strict_json(candidate_raw)) != _canonical(candidate)
            or _canonical(_strict_json(assessment_raw)) != _canonical(assessment)):
        raise ValueError("La copia de candidata o declaración cambió.")
    access = _access(candidate["binding"])
    access_raw = _read(access, 32768)
    if access_raw != _canonical(_claim(directory, candidate)):
        raise ValueError("La captura ya pertenece a otra revisión o su reserva ha cambiado.")
    return {"schema_version": 1, "protocol": "campaign_technical_review_v1", "status": assessment["decision"],
            "run_dir": str(directory), "binding": deepcopy(candidate["binding"]),
            "candidate_sha256": sha256(candidate_raw).hexdigest(), "assessment": deepcopy(assessment),
            "assessment_sha256": sha256(assessment_raw).hexdigest(),
            "access": {"path": str(access), "sha256": sha256(access_raw).hexdigest()},
            "reference": deepcopy(candidate["reference"]), "scope": "technical_attestation_not_profit_or_novelty_proof",
            "reason_origin": "unverified_reviewer_declaration", "transport_verified": False,
            "eligible_for_plan": assessment["decision"] == "accepted", "execution_authorized": False,
            "calculated_results": None, "attempt_usage": deepcopy(candidate["attempt_usage"]),
            "prior_compact_usage": deepcopy(candidate["prior_compact_usage"]),
            "new_usage": dict(ZERO_USAGE), "code_sha256": _code_hashes()}


def review_capture(scope_id: str, request_sha256: str, assessment: dict, *,
                   output_dir: str | Path = ROOT / ".local/campaign-reviews") -> Path:
    ledger._identifier(scope_id); ledger._identifier(request_sha256)
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("campaign_review_started", scope_id=scope_id, request_sha256=request_sha256)
    try:
        candidate = inspect_candidate(scope_id, request_sha256)
        validate_assessment(assessment, candidate)
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        try: _write_exclusive(_access(candidate["binding"]), _canonical(_claim(journal.directory, candidate)))
        except FileExistsError as error:
            raise ValueError("La revisión de esta captura está consumida; no se reabre o repite.") from error
        journal.save("candidate.json", candidate)
        journal.save("assessment.json", assessment)
        record = _record(journal.directory, candidate, assessment)
        if _canonical(inspect_candidate(scope_id, request_sha256)) != _canonical(candidate):
            raise ValueError("Las fuentes cambiaron al guardar; se conserva la reserva de revisión.")
        _seal(journal, "review.json", record, "campaign_review_completed")
    except Exception as error:
        journal.record("campaign_review_failed", error_type=type(error).__name__, message=str(error)[:1000], new_usage=dict(ZERO_USAGE))
        raise CampaignReviewError(str(error), journal.directory) from error
    return journal.directory


def verify_review(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "review.json", "campaign_review_completed")
    binding = record["binding"]
    candidate = inspect_candidate(binding["scope_id"], binding["request_sha256"], allow_existing_comparisons=True)
    assessment = _strict_json(_read(directory / "assessment.json", 16384))
    if _canonical(record) != _canonical(_record(directory, candidate, assessment)):
        raise ValueError("La revisión, declaración, captura, controles o código han cambiado.")
    return record


def inspect_reviews(scope_id: str) -> dict:
    state = ledger.inspect_campaign(scope_id)
    if state["status"] != "registered_inactive": raise ValueError("El ámbito no está registrado.")
    items, guards = [], []
    for receipt in state["reservations"]:
        if receipt["kind"] != "proposal": continue
        path = ACCESS_ROOT.resolve() / (receipt["receipt_id"] + ".json")
        raw = _read(path, 32768) if path.exists() else None
        guards.append((path, raw))
        item = {"receipt_id": receipt["receipt_id"], "request_sha256": receipt["operation_id"],
                "status": "not_reviewed", "execution_authorized": False}
        if raw is not None:
            try:
                claim = _strict_json(raw)
                directory = Path(claim["review_dir"])
                if not directory.is_absolute(): raise ValueError("Ruta de revisión no absoluta.")
                record = verify_review(directory)
                if (record["binding"]["scope_id"] != scope_id or record["binding"]["receipt_id"] != receipt["receipt_id"]
                        or record["binding"]["request_sha256"] != receipt["operation_id"]):
                    raise ValueError("La revisión pertenece a otra captura o ámbito.")
                item.update(status=record["status"], run_dir=str(directory), eligible_for_plan=record["eligible_for_plan"])
            except controller.ERRORS as error:
                item.update(status="unverifiable_review", error=str(error)[:1000])
        items.append(item)
    if (ledger.inspect_campaign(scope_id) != state
            or any((_read(path, 32768) if path.exists() else None) != raw for path, raw in guards)):
        raise ValueError("El registro o las revisiones cambiaron durante la consulta.")
    return {"schema_version": 1, "protocol": "campaign_review_status_v1", "scope_id": scope_id, "reviews": items,
            "requires_stop": any(item["status"] == "unverifiable_review" for item in items),
            "current_source_freshness_verified": False, "scope": "review_registry_not_execution_preflight",
            "execution_authorized": False, "calculated_results": None, "new_usage": dict(ZERO_USAGE)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} — revisión técnica de capturas sin simulación")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("candidate", "review"):
        command = commands.add_parser(name)
        command.add_argument("--scope", required=True)
        command.add_argument("--request-sha", required=True)
        if name == "review":
            command.add_argument("--assessment", type=Path, required=True)
            command.add_argument("--output-dir", type=Path)
    commands.add_parser("verify").add_argument("--run", type=Path, required=True)
    commands.add_parser("status").add_argument("--scope", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": result = verify_review(args.run)
        elif args.command == "status": result = inspect_reviews(args.scope)
        elif args.command == "candidate": result = inspect_candidate(args.scope, args.request_sha)
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            result = str(review_capture(args.scope, args.request_sha, _strict_json(_read(args.assessment, 16384)), **kwargs))
        print(json.dumps(result, ensure_ascii=True) if isinstance(result, dict) else result)
    except controller.ERRORS as error:
        parser.exit(1, f"Revisión de campaña detenida: {error}\n")


if __name__ == "__main__": main()
