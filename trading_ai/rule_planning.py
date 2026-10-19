"""Revisión técnica y registro previo de experimentos de reglas; no ejecuta simulaciones."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.formalization import _read, _source, _strict_json, validate_translation
from trading_ai.holdout import EXECUTION_POLICY, _code_hashes as _engine_hashes, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.robustness import _development


CHECKS = ("entry_matches", "exit_matches", "parameters_match", "data_sufficient", "no_unresolved_ambiguity")
BUDGET = {"candidate_backtests": 1, "baseline_backtests": 1, "max_model_requests": 0,
          "max_parameter_variations": 0, "automatic_retries": 0}
REVIEW_SCOPE = "technical_attestation_not_a_proof_of_semantic_equivalence"


class PlanningError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")


def _code_hashes() -> dict:
    return {**_engine_hashes(), **{name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in ("rule_planning.py", "rules.py", "formalization.py", "discovery.py", "robustness.py")}}


def _files(directory: Path, filename: str) -> tuple[dict, dict, list]:
    raw = {filename: _read(directory / filename, 131072),
           "events.jsonl": _read(directory / "events.jsonl", 2 * 1024 * 1024)}
    record = _strict_json(raw[filename])
    events = [_strict_json(line) for line in raw["events.jsonl"].splitlines()]
    if not isinstance(record, dict) or not events:
        raise ValueError("Se requiere un registro completo con eventos.")
    origin = {"directory": str(directory), "sha256": {name: sha256(content).hexdigest() for name, content in raw.items()}}
    return record, origin, events


def _translation(directory: Path, frozen_dir: Path) -> tuple[dict, dict]:
    record, origin, events = _files(directory, "translation.json")
    idea, source, missing = _source(Path(record["source"]["directory"]), frozen_dir)
    last = events[-1]
    if (type(record["schema_version"]) is not int or record["schema_version"] != 1
            or record["source"] != source or record["original_proposal"] != idea["proposal"]
            or record["missing_declared_inputs"] != missing or record["executable"] is not False
            or record["semantic_equivalence_verified"] is not False or record["calculated_results"] is not None
            or record["validation_scope"] != "source_link_and_rule_structure_only"
            or last["event"] != "translation_queued" or last["data"]["source"] != source
            or last["data"]["status"] != record["status"] or last["data"]["executable"] is not False
            or type(record["model_requests"]) is not int
            or last["data"]["model_requests"] != record["model_requests"]
            or last["data"]["usage"] != record["usage"] or last["data"]["api_cost_usd"] != record["api_cost_usd"]):
        raise ValueError("Traducción alterada, incompleta o incompatible con su origen.")
    requests = [event for event in events if event["event"] == "model_request"]
    replies = [event for event in events if event["event"] == "model_response"]
    if missing:
        expected = ("needs_data", None, None)
        if (requests or replies or record["model_translation"] is not None or record["usage"] != []
                or record["provider"] is not None or record["api_cost_usd"] != "0"
                or record["model_requests"] != 0):
            raise ValueError("El bloqueo por datos no coincide con sus eventos.")
    else:
        if len(requests) != 1 or len(replies) != 1 or record["model_requests"] != 1:
            raise ValueError("Se requiere una única traducción registrada.")
        reply = _strict_json(replies[0]["data"]["content"])
        if (reply != record["model_translation"] or record["reason"] != reply["reason"]
                or record["usage"] != [replies[0]["data"]["usage"]]):
            raise ValueError("La traducción no coincide con la respuesta original.")
        strategy = validate_translation(reply)
        expected = (("pending_semantic_review", strategy.to_spec(), strategy.spec_sha256) if strategy is not None
                    else (reply["status"], None, None))
    if _canonical([record["status"], record["spec"], record["spec_sha256"]]) != _canonical(list(expected)):
        raise ValueError("Reglas, estado o hash de traducción incompatibles.")
    return record, origin


def validate_assessment(assessment: dict, translation: dict, origin: dict) -> None:
    """Registra una revisión declarada; las marcas no demuestran por sí mismas el significado."""
    fields = {"schema_version", "translation_sha256", "spec_sha256", "reviewer", "decision", "rationale", "checks"}
    if not isinstance(assessment, dict) or set(assessment) != fields:
        raise ValueError("Revisión con campos ausentes o no autorizados.")
    if (type(assessment["schema_version"]) is not int or assessment["schema_version"] != 1
            or assessment["translation_sha256"] != origin["sha256"]["translation.json"]
            or assessment["spec_sha256"] != translation["spec_sha256"]):
        raise ValueError("La revisión debe identificar la traducción y las reglas exactas.")
    for key, maximum in (("reviewer", 80), ("rationale", 1200)):
        value = assessment[key]
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise ValueError("Revisor y justificación deben ser textos no vacíos y acotados.")
    checks = assessment["checks"]
    if (not isinstance(checks, dict) or set(checks) != set(CHECKS)
            or any(type(value) is not bool for value in checks.values())):
        raise ValueError("Se requieren todas las comprobaciones con valores booleanos.")
    decision = assessment["decision"]
    if not isinstance(decision, str) or decision not in ("accepted", "needs_clarification", "rejected"):
        raise ValueError("Decisión de revisión no autorizada.")
    if decision == "accepted" and not all(checks.values()):
        raise ValueError("Aceptar requiere confirmar todas las comprobaciones.")


def _review_record(translation: dict, origin: dict, assessment: dict | None) -> dict:
    if translation["status"] != "pending_semantic_review":
        if assessment is not None:
            raise ValueError("No se puede revisar ni aprobar una traducción sin reglas propuestas.")
        status, reason = "blocked_by_translation", "No hay reglas propuestas revisables: " + translation["status"]
    else:
        validate_assessment(assessment, translation, origin)
        status, reason = assessment["decision"], assessment["rationale"]
    return {"schema_version": 1, "translation": origin, "idea_id": translation["source"]["idea_id"],
            "reference": translation["source"]["reference"], "spec_sha256": translation["spec_sha256"],
            "status": status, "reason": reason, "assessment": deepcopy(assessment), "scope": REVIEW_SCOPE,
            "eligible_for_plan": status == "accepted", "executable": False, "calculated_results": None,
            "model_requests": 0, "api_cost_usd": "0", "code_sha256": _code_hashes()}


def _seal(journal: RunJournal, name: str, record: dict, event: str) -> None:
    journal.save(name, record)
    checksum = sha256((journal.directory / name).read_bytes()).hexdigest()
    _write_exclusive(journal.directory / (name + ".sha256"), (checksum + "\n").encode("ascii"))
    journal.record(event, sha256=checksum, status=record.get("status", record.get("stage")), executable=False)


def _artifact(directory: Path, filename: str, event: str) -> tuple[dict, dict]:
    record, origin, events = _files(directory, filename)
    checksum = origin["sha256"][filename]
    if (_read(directory / (filename + ".sha256"), 128).decode("ascii").strip() != checksum
            or events[-1]["event"] != event or events[-1]["data"]["sha256"] != checksum
            or events[-1]["data"]["executable"] is not False
            or events[-1]["data"]["status"] != record.get("status", record.get("stage"))):
        raise ValueError("El registro no conserva su sello o cierre.")
    return record, origin


def review_translation(translation_dir: str | Path, frozen_dir: str | Path, *, assessment: dict | None = None,
                       output_dir: str | Path = ROOT / ".local/rule-reviews") -> Path:
    directory, frozen_dir = Path(translation_dir).resolve(), Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir))
    journal.record("review_started", translation_dir=str(directory), frozen_dir=str(frozen_dir))
    try:
        translation, origin = _translation(directory, frozen_dir)
        record = _review_record(translation, origin, assessment)
        if _translation(directory, frozen_dir)[1] != origin:
            raise ValueError("La traducción cambió durante la revisión.")
        _seal(journal, "review.json", record, "review_completed")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        journal.record("review_failed", message=str(error)[:1000], model_requests=0, api_cost_usd="0")
        raise PlanningError(str(error), journal.directory) from error
    return journal.directory


def _review(directory: Path, frozen_dir: Path) -> tuple[dict, dict, dict]:
    record, origin = _artifact(directory, "review.json", "review_completed")
    translation, source = _translation(Path(record["translation"]["directory"]), frozen_dir)
    expected = _review_record(translation, source, record["assessment"])
    if _canonical(record) != _canonical(expected):
        raise ValueError("La revisión no coincide con sus fuentes, decisiones o código.")
    return record, origin, translation


def verify_review(review_dir: str | Path, frozen_dir: str | Path) -> dict:
    return _review(Path(review_dir).resolve(), Path(frozen_dir).resolve())[0]


def _plan_record(review: dict, origin: dict, translation: dict, frozen: dict, reference: dict) -> dict:
    if review["status"] != "accepted" or review["eligible_for_plan"] is not True:
        raise ValueError("Solo una revisión aceptada permite registrar un plan.")
    policy = frozen["policy"]
    return {"schema_version": 1, "protocol": "reviewed_rule_development_v1", "stage": "registered_not_run",
            "review": origin, "idea_id": review["idea_id"], "reference": reference,
            "candidate": {"spec": translation["spec"], "spec_sha256": translation["spec_sha256"]},
            "baseline": {"strategy": policy["baseline_strategy"], "fast_window": policy["fast_window"],
                         "slow_window": policy["slow_window"]},
            "policy": deepcopy(policy), "criterion": frozen["proposal"]["criterion"],
            "assessment_rules": {"implementation": "experiments.expected_assessment",
                                 "minimum_closed_trades_each": 1, "both_metrics_equal": "inconclusive"},
            "data": {**frozen["development_result"]["source"], "file": "development.xml"},
            "budget": deepcopy(BUDGET), "execution_policy": deepcopy(EXECUTION_POLICY),
            "execution_timing": "next_observation", "direction": "long_only", "executable": False,
            "scope": "known_development_history_only", "outer_evaluation_allowed": False,
            "calculated_results": None, "model_requests": 0, "api_cost_usd": "0",
            "code_sha256": _code_hashes(),
            "limitations": ["Technical review is an attestation, not a proof of semantic equivalence.",
                            "Historical data was already explored; this is not unseen evidence.",
                            "Registering a plan does not execute it or establish a better strategy."]}


def prepare_rule_plan(review_dir: str | Path, frozen_dir: str | Path, *,
                      output_dir: str | Path = ROOT / ".local/rule-plans") -> Path:
    directory, frozen_dir = Path(review_dir).resolve(), Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir))
    journal.record("plan_preparation_started", review_dir=str(directory), frozen_dir=str(frozen_dir))
    try:
        review, origin, translation = _review(directory, frozen_dir)
        frozen, reference, content = _development(frozen_dir)
        plan = _plan_record(review, origin, translation, frozen, reference)
        _write_exclusive(journal.directory / "development.xml", content)
        if (_review(directory, frozen_dir)[1] != origin
                or _development(frozen_dir)[2] != content or plan["code_sha256"] != _code_hashes()):
            raise ValueError("El origen o el código cambió durante la preparación.")
        _seal(journal, "plan.json", plan, "plan_registered")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        journal.record("plan_preparation_failed", message=str(error)[:1000], model_requests=0, api_cost_usd="0")
        raise PlanningError(str(error), journal.directory) from error
    return journal.directory


def verify_rule_plan(plan_dir: str | Path, frozen_dir: str | Path) -> dict:
    directory, frozen_dir = Path(plan_dir).resolve(), Path(frozen_dir).resolve()
    plan, _ = _artifact(directory, "plan.json", "plan_registered")
    review, origin, translation = _review(Path(plan["review"]["directory"]), frozen_dir)
    frozen, reference, content = _development(frozen_dir)
    expected = _plan_record(review, origin, translation, frozen, reference)
    if (_canonical(plan) != _canonical(expected) or (directory / "development.xml").read_bytes() != content):
        raise ValueError("El plan, sus datos, controles o fuentes han cambiado.")
    return plan


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — revisión y planes de reglas, sin ejecución")
    commands = parser.add_subparsers(dest="command", required=True)
    review = commands.add_parser("review")
    review.add_argument("--translation-run", type=Path, required=True)
    review.add_argument("--assessment", type=Path)
    review.add_argument("--output-dir", type=Path, default=ROOT / ".local/rule-reviews")
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--review-run", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path, default=ROOT / ".local/rule-plans")
    for name in ("verify-review", "verify-plan"):
        command = commands.add_parser(name)
        command.add_argument("--run", type=Path, required=True)
    for command in (review, prepare, *[commands.choices[name] for name in ("verify-review", "verify-plan")]):
        command.add_argument("--frozen-run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "review":
            assessment = _strict_json(_read(args.assessment, 16384)) if args.assessment else None
            result = review_translation(args.translation_run, args.frozen_run, assessment=assessment, output_dir=args.output_dir)
        elif args.command == "prepare":
            result = prepare_rule_plan(args.review_run, args.frozen_run, output_dir=args.output_dir)
        elif args.command == "verify-review":
            verify_review(args.run, args.frozen_run)
            result = args.run
        else:
            verify_rule_plan(args.run, args.frozen_run)
            result = args.run
    except PlanningError as error:
        parser.exit(1, f"Proceso detenido: {error}. Registro: {error.directory}\n")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"No se pudo verificar o preparar el registro: {error}\n")
    print(f"Registro preparado o verificado, sin ejecutar: {result}")


if __name__ == "__main__":
    main()
