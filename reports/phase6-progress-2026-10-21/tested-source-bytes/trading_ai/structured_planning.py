"""Revisión y planes con origen estructurado real, sin traducciones fabricadas ni cálculos."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import EXECUTION_POLICY, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.robustness import _development
from trading_ai.rule_planning import BUDGET, REVIEW_SCOPE, _artifact, _canonical, _seal
from trading_ai.structured_ideas import _code_hashes as _source_hashes, verify_structured_idea


CHECKS = ("entry_matches_hypothesis", "exit_matches_hypothesis", "windows_understood",
          "lags_understood", "data_sufficient", "no_unresolved_ambiguity")


class StructuredPlanningError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_source_hashes(), "structured_planning.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _source(directory: Path, frozen: Path) -> tuple[dict, dict]:
    record = verify_structured_idea(directory, frozen)
    origin = {"directory": str(directory), "sha256": {
        name: sha256(_read(directory / name, 2 * 1024 * 1024)).hexdigest()
        for name in ("proposal.json", "events.jsonl", "report.md", "memory.json", "rules-memory.json")}}
    return record, origin


def validate_assessment(assessment: dict, proposal: dict, origin: dict) -> None:
    fields = {"schema_version", "proposal_sha256", "spec_sha256", "reviewer", "decision", "rationale", "checks"}
    if (not isinstance(assessment, dict) or set(assessment) != fields
            or type(assessment["schema_version"]) is not int or assessment["schema_version"] != 1
            or assessment["proposal_sha256"] != origin["sha256"]["proposal.json"]
            or assessment["spec_sha256"] != proposal["spec_sha256"]):
        raise ValueError("La revisión debe identificar la propuesta y sus reglas exactas, sin campos extra.")
    if proposal["status"] != "pending_semantic_review":
        raise ValueError("Solo una propuesta estructurada pendiente admite revisión técnica.")
    for key, maximum in (("reviewer", 80), ("rationale", 1200)):
        if not isinstance(assessment[key], str) or not assessment[key].strip() or len(assessment[key]) > maximum:
            raise ValueError("Revisor y justificación deben ser textos no vacíos y acotados.")
    checks = assessment["checks"]
    if (not isinstance(checks, dict) or set(checks) != set(CHECKS)
            or any(type(item) is not bool for item in checks.values())):
        raise ValueError("La revisión requiere seis comprobaciones booleanas, incluidos los retardos.")
    if assessment["decision"] not in ("accepted", "rejected", "needs_clarification"):
        raise ValueError("Decisión de revisión no admitida.")
    if assessment["decision"] == "accepted" and not all(checks.values()):
        raise ValueError("Aceptar exige todas las comprobaciones, sin ambigüedades pendientes.")


def _review_record(proposal: dict, origin: dict, assessment: dict | None) -> dict:
    if proposal["status"] != "pending_semantic_review":
        if assessment is not None:
            raise ValueError("Una propuesta duplicada no puede aprobarse mediante una revisión.")
        status, reason = "blocked_proposal", "Estado de origen: " + proposal["status"]
    else:
        validate_assessment(assessment, proposal, origin)
        status, reason = assessment["decision"], assessment["rationale"]
    return {"schema_version": 1, "protocol": "structured_review_v1", "source": origin,
            "reference": proposal["reference"], "spec_sha256": proposal["spec_sha256"],
            "status": status, "reason": reason, "assessment": deepcopy(assessment), "scope": REVIEW_SCOPE,
            "eligible_for_plan": status == "accepted", "executable": False, "calculated_results": None,
            "model_requests": 0, "api_cost_usd": "0", "code_sha256": _code_hashes()}


def review_structured_idea(proposal_dir: str | Path, frozen_dir: str | Path, *, assessment: dict | None = None,
                           output_dir: str | Path = ROOT / ".local/structured-reviews") -> Path:
    directory, frozen = Path(proposal_dir).resolve(), Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("structured_review_started", proposal_dir=str(directory), frozen_dir=str(frozen))
    try:
        proposal, origin = _source(directory, frozen)
        record = _review_record(proposal, origin, assessment)
        if _source(directory, frozen)[1] != origin or record["code_sha256"] != _code_hashes():
            raise ValueError("El origen o el código cambiaron durante la revisión.")
        _seal(journal, "review.json", record, "structured_review_completed")
    except Exception as error:
        journal.record("structured_review_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       model_requests=0, api_cost_usd="0")
        raise StructuredPlanningError(str(error), journal.directory) from error
    return journal.directory


def _review(directory: Path, frozen: Path) -> tuple[dict, dict, dict]:
    record, origin = _artifact(directory, "review.json", "structured_review_completed")
    proposal, source = _source(Path(record["source"]["directory"]), frozen)
    if _canonical(record) != _canonical(_review_record(proposal, source, record["assessment"])):
        raise ValueError("La revisión estructurada no coincide con su origen, decisiones o código.")
    return record, origin, proposal


def verify_structured_review(review_dir: str | Path, frozen_dir: str | Path) -> dict:
    return _review(Path(review_dir).resolve(), Path(frozen_dir).resolve())[0]


def _plan_record(review: dict, origin: dict, proposal: dict, frozen: dict, reference: dict) -> dict:
    if review["status"] != "accepted" or review["eligible_for_plan"] is not True:
        raise ValueError("Solo una revisión aceptada permite registrar el plan estructurado.")
    policy = frozen["policy"]
    return {"schema_version": 1, "protocol": "structured_development_plan_v1", "stage": "registered_not_run",
            "review": origin, "proposal_id": review["source"]["sha256"]["proposal.json"], "reference": reference,
            "candidate": {"spec": proposal["spec"], "spec_sha256": proposal["spec_sha256"]},
            "baseline": {"strategy": policy["baseline_strategy"], "fast_window": policy["fast_window"],
                         "slow_window": policy["slow_window"]},
            "policy": deepcopy(policy), "criterion": frozen["proposal"]["criterion"],
            "assessment_rules": {"implementation": "experiments.expected_assessment",
                                 "minimum_closed_trades_each": 1, "both_metrics_equal": "inconclusive"},
            "data": {**frozen["development_result"]["source"], "file": "development.xml"},
            "budget": deepcopy(BUDGET), "execution_policy": deepcopy(EXECUTION_POLICY),
            "execution_timing": "next_observation", "direction": "long_only", "executable": False,
            "scope": "known_development_history_only", "outer_evaluation_allowed": False,
            "calculated_results": None, "model_requests": 0, "api_cost_usd": "0", "code_sha256": _code_hashes()}


def prepare_structured_plan(review_dir: str | Path, frozen_dir: str | Path, *,
                            output_dir: str | Path = ROOT / ".local/structured-plans") -> Path:
    directory, frozen_dir = Path(review_dir).resolve(), Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("structured_plan_started", review_dir=str(directory), frozen_dir=str(frozen_dir))
    try:
        review, origin, proposal = _review(directory, frozen_dir)
        frozen, reference, content = _development(frozen_dir)
        record = _plan_record(review, origin, proposal, frozen, reference)
        _write_exclusive(journal.directory / "development.xml", content)
        if (_review(directory, frozen_dir)[1] != origin or _development(frozen_dir)[2] != content
                or record["code_sha256"] != _code_hashes()):
            raise ValueError("Las fuentes o el código cambiaron al registrar el plan.")
        _seal(journal, "plan.json", record, "structured_plan_registered")
    except Exception as error:
        journal.record("structured_plan_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       model_requests=0, api_cost_usd="0")
        raise StructuredPlanningError(str(error), journal.directory) from error
    return journal.directory


def verify_structured_plan(plan_dir: str | Path, frozen_dir: str | Path) -> dict:
    directory, frozen_dir = Path(plan_dir).resolve(), Path(frozen_dir).resolve()
    record, _ = _artifact(directory, "plan.json", "structured_plan_registered")
    review, origin, proposal = _review(Path(record["review"]["directory"]), frozen_dir)
    frozen, reference, content = _development(frozen_dir)
    if (_canonical(record) != _canonical(_plan_record(review, origin, proposal, frozen, reference))
            or _read(directory / "development.xml", len(content)) != content):
        raise ValueError("El plan estructurado, los controles o sus fuentes han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — revisión y plan de propuestas estructuradas")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("review", "prepare", "verify-review", "verify-plan"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--run", type=Path, required=True)
        cmd.add_argument("--frozen-run", type=Path, required=True)
        if name in ("review", "prepare"):
            cmd.add_argument("--output-dir", type=Path)
        if name == "review":
            cmd.add_argument("--assessment", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command.startswith("verify-"):
            record = (verify_structured_review if args.command == "verify-review" else verify_structured_plan)(args.run, args.frozen_run)
            print(json.dumps({"status": record.get("status", record.get("stage")), "executable": False}))
            return
        kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
        if args.command == "review":
            kwargs["assessment"] = _strict_json(_read(args.assessment, 16384)) if args.assessment else None
        directory = (review_structured_idea if args.command == "review" else prepare_structured_plan)(args.run, args.frozen_run, **kwargs)
    except StructuredPlanningError as error:
        parser.exit(1, f"Registro detenido: {error}. Evidencia: {error.directory}\n")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Registro no verificable: {error}\n")
    print(f"Registro: {directory}")


if __name__ == "__main__":
    main()
