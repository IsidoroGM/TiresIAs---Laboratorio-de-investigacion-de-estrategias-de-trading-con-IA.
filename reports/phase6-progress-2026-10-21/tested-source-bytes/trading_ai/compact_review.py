"""Revisión declarada de reglas compactas, con consumo único y sin cálculos."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.compact_candidate import _code_hashes as _candidate_hashes, verify_compact_candidate
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal


ACCESS_ROOT = ROOT / ".local/compact-review-access"
CHECKS = ("rules_understood", "windows_and_lags_understood", "reference_data_sufficient",
          "next_observation_execution_understood", "development_objective_understood", "no_unresolved_ambiguity")
SOURCE_FILES = ("candidate.json", "candidate.json.sha256", "events.jsonl", "job.json", "job.sha256", "report.md")


class CompactReviewError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_candidate_hashes(), "compact_review.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def validate_assessment(assessment: dict, candidate: dict, origin: dict) -> None:
    if (not isinstance(assessment, dict) or set(assessment) != {
        "schema_version", "candidate_sha256", "spec_sha256", "reviewer", "decision", "rationale", "checks"
    } or type(assessment["schema_version"]) is not int or assessment["schema_version"] != 1
            or assessment["candidate_sha256"] != origin["sha256"]["candidate.json"]
            or assessment["spec_sha256"] != candidate["spec_sha256"]):
        raise ValueError("La revisión debe identificar la candidata y sus reglas exactas, sin campos extra.")
    if candidate["status"] != "pending_technical_review":
        raise ValueError("Solo una candidata pendiente admite revisión; un duplicado no se puede aprobar.")
    for key, maximum in (("reviewer", 80), ("rationale", 1200)):
        if not isinstance(assessment[key], str) or not assessment[key].strip() or len(assessment[key]) > maximum:
            raise ValueError("Revisor y motivo deben ser textos no vacíos y acotados.")
    checks = assessment["checks"]
    if (not isinstance(checks, dict) or set(checks) != set(CHECKS)
            or any(type(value) is not bool for value in checks.values())):
        raise ValueError("Se requieren las seis comprobaciones booleanas de revisión.")
    if not isinstance(assessment["decision"], str) or assessment["decision"] not in ("accepted", "rejected", "needs_clarification"):
        raise ValueError("Decisión de revisión no admitida.")
    if assessment["decision"] == "accepted" and not all(checks.values()):
        raise ValueError("Aceptar exige todas las comprobaciones; no demuestra rentabilidad.")


def _access(candidate: dict) -> tuple[dict, Path]:
    identity = {"reference": candidate["reference"], "spec_sha256": candidate["spec_sha256"]}
    return identity, ACCESS_ROOT.resolve() / (sha256(_canonical(identity)).hexdigest() + ".json")


def _record(candidate_dir: Path, directory: Path, assessment: dict) -> dict:
    candidate = verify_compact_candidate(candidate_dir)
    origin = _origin(candidate_dir, SOURCE_FILES)
    validate_assessment(assessment, candidate, origin)
    assessment_raw = _read(directory / "assessment.json", 16384)
    if _canonical(_strict_json(assessment_raw)) != _canonical(assessment):
        raise ValueError("La declaración guardada no coincide con la revisión.")
    identity, access = _access(candidate)
    raw = _read(access, 8192)
    expected = {"schema_version": 1, "identity": identity, "review_dir": str(directory),
                "candidate_sha256": origin["sha256"]["candidate.json"]}
    if _strict_json(raw) != expected:
        raise ValueError("La revisión no posee la reserva única de estas reglas.")
    return {"schema_version": 1, "protocol": "compact_review_v1", "status": assessment["decision"],
            "run_dir": str(directory), "source": origin, "reference": candidate["reference"],
            "spec_sha256": candidate["spec_sha256"], "assessment": deepcopy(assessment),
            "assessment_sha256": sha256(assessment_raw).hexdigest(),
            "scope": "technical_attestation_not_profit_or_novelty_proof",
            "objective_origin": "frozen_development_objective_not_model_prose",
            "reason_origin": "unverified_reviewer_declaration", "access": {"path": str(access), "sha256": sha256(raw).hexdigest()},
            "eligible_for_plan": assessment["decision"] == "accepted", "executable": False,
            "calculated_results": None, "inherited_usage": candidate["usage"],
            "inherited_api_cost_usd": candidate["api_cost_usd"],
            "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
            "code_sha256": _code_hashes()}


def review_compact_candidate(candidate_dir: str | Path, assessment: dict, *,
                             output_dir: str | Path = ROOT / ".local/compact-reviews") -> Path:
    candidate_dir = Path(candidate_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("compact_review_started", candidate_dir=str(candidate_dir))
    try:
        candidate = verify_compact_candidate(candidate_dir)
        origin = _origin(candidate_dir, SOURCE_FILES)
        validate_assessment(assessment, candidate, origin)
        identity, access = _access(candidate)
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            _write_exclusive(access, _canonical({"schema_version": 1, "identity": identity, "review_dir": str(journal.directory),
                                               "candidate_sha256": origin["sha256"]["candidate.json"]}))
        except FileExistsError as error:
            raise ValueError("La revisión de estas reglas ya está consumida; no se repetirá o reabrirá.") from error
        journal.save("assessment.json", assessment)
        record = _record(candidate_dir, journal.directory, assessment)
        if _origin(candidate_dir, SOURCE_FILES) != origin:
            raise ValueError("La candidata cambió durante la revisión; se conserva la reserva.")
        _seal(journal, "review.json", record, "compact_review_completed")
    except Exception as error:
        journal.record("compact_review_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise CompactReviewError(str(error), journal.directory) from error
    return journal.directory


def verify_compact_review(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "review.json", "compact_review_completed")
    assessment = _strict_json(_read(directory / "assessment.json", 16384))
    expected = _record(Path(record["source"]["directory"]), directory, assessment)
    if _canonical(expected) != _canonical(record):
        raise ValueError("La revisión, candidata, declaración, reserva o código han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — revisión compacta sin simulación")
    commands = parser.add_subparsers(dest="command", required=True)
    review = commands.add_parser("review")
    review.add_argument("--candidate-run", type=Path, required=True)
    review.add_argument("--assessment", type=Path, required=True)
    review.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_compact_review(args.run), ensure_ascii=True))
        else:
            assessment = _strict_json(_read(args.assessment, 16384))
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(review_compact_candidate(args.candidate_run, assessment, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Revisión no verificable: {error}\n")


if __name__ == "__main__":
    main()
