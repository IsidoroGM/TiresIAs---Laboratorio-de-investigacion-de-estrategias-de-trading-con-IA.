"""Plan previo de reglas de campaña revisadas; no reserva o ejecuta cálculos."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import PROJECT_NAME
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_review as reviews
from trading_ai import rule_execution as engine
from trading_ai.campaign_controller import ERRORS
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import EXECUTION_POLICY, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.robustness import _development
from trading_ai.rule_planning import BUDGET, _artifact, _canonical, _seal
from trading_ai.structured_draft import describe_draft


class CampaignPlanError(ValueError):
    def __init__(self, message, directory):
        super().__init__(message)
        self.directory = directory


def _code_hashes():
    return {**reviews._code_hashes(), **engine._code_hashes(),
            "campaign_experiment.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _sources(review_dir):
    review = reviews.verify_review(review_dir)
    if review["status"] != "accepted" or review["eligible_for_plan"] is not True:
        raise ValueError("Solo una revisión de campaña aceptada admite un plan.")
    candidate = _strict_json(_read(review_dir / "candidate.json", 131072))
    origin = _origin(review_dir, reviews.REVIEW_FILES)
    if origin["sha256"]["candidate.json"] != review["candidate_sha256"]:
        raise ValueError("La candidata cambió después de comprobar la revisión.")
    frozen, reference, content = _development(Path(candidate["reference"]["frozen_dir"]))
    if (reference != candidate["reference"] or reference != review["reference"]
            or _canonical(frozen["policy"]) != _canonical(candidate["controls"])
            or frozen["proposal"]["criterion"] != candidate["objective"]["criterion"]):
        raise ValueError("La revisión no conserva los datos, controles y objetivo congelados.")
    described = describe_draft(candidate["draft"])
    if described["spec_sha256"] != review["binding"]["spec_sha256"]:
        raise ValueError("Las reglas revisadas cambiaron de identidad.")
    return review, candidate, origin, frozen, reference, content, described


def _record(directory, review, candidate, origin, frozen, reference, content, described):
    policy = frozen["policy"]
    if (candidate["campaign_limits"]["max_backtests"] < 2
            or sha256(content).hexdigest() != reference["development_sha256"]):
        raise ValueError("La campaña no permite dos backtests o los datos cambiaron.")
    record = {"schema_version": 1, "protocol": "campaign_development_plan_v1", "stage": "registered_not_run",
              "run_dir": str(directory), "review": origin, "binding": deepcopy(review["binding"]),
              "reference": deepcopy(reference), "registered_campaign": deepcopy(candidate["registration"]),
              "candidate": {"spec": described["spec"], "spec_sha256": described["spec_sha256"]},
              "baseline": {"strategy": policy["baseline_strategy"], "fast_window": policy["fast_window"],
                           "slow_window": policy["slow_window"]},
              "policy": deepcopy(policy), "criterion": frozen["proposal"]["criterion"],
              "objective_origin": "frozen_development_objective_not_model_prose",
              "data": {**frozen["development_result"]["source"], "file": "development.xml"},
              "campaign_limits": deepcopy(candidate["campaign_limits"]), "budget": deepcopy(BUDGET),
              "execution_policy": deepcopy(EXECUTION_POLICY), "execution_timing": "next_observation", "direction": "long_only",
              "assessment_rules": {"implementation": "experiments.expected_assessment", "minimum_closed_trades_each": 1,
                                   "both_metrics_equal": "inconclusive"},
              "scope": "known_development_history_only", "outer_evaluation_allowed": False,
              "execution_authorized": False, "executable": False, "calculated_results": None,
              "transport_verified": False, "new_comparison_reservation": None, "shared_calculation_claimed": False,
              "execution_requirements": ["explicit_campaign_allowance", "fresh_full_campaign_history_and_sources",
                                         "verified_capture_origin", "atomic_campaign_comparison_reservation",
                                         "shared_engine_calculation_claim", "controlled_executor"],
              "attempt_usage": deepcopy(review["attempt_usage"]), "prior_compact_usage": deepcopy(review["prior_compact_usage"]),
              "new_usage": dict(reviews.ZERO_USAGE), "code_sha256": _code_hashes()}
    record["calculation_id"] = sha256(_canonical(engine._identity(record))).hexdigest()
    return record


def _available(record):
    state = ledger.inspect_campaign(record["binding"]["scope_id"])
    if (state["status"] != "registered_inactive" or state["remaining_accounting_slots"]["backtests"] < 2
            or any(item["kind"] == "comparison" and (item["proposal_id"] == record["binding"]["request_sha256"]
                   or item["operation_id"] == record["calculation_id"])
                   for item in state["reservations"])):
        raise ValueError("La comparación ya está reservada o no quedan dos huecos contables.")
    access = engine.ACCESS_ROOT.resolve() / (record["calculation_id"] + ".json")
    if access.exists(): raise ValueError("Este cálculo ya está reservado en el motor; no se reabre.")
    return state


def prepare_plan(review_dir: str | Path, *, output_dir: str | Path = ROOT / ".local/campaign-experiments") -> Path:
    review_dir = Path(review_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("campaign_experiment_plan_started", review_dir=str(review_dir))
    try:
        sources = _sources(review_dir)
        record = _record(journal.directory, *sources)
        state = _available(record)
        _write_exclusive(journal.directory / "development.xml", sources[5])
        current = _record(journal.directory, *_sources(review_dir))
        if _canonical(current) != _canonical(record) or _available(record) != state:
            raise ValueError("Las fuentes, revisión o reservas cambiaron al preparar el experimento.")
        _seal(journal, "plan.json", record, "campaign_experiment_plan_registered")
    except Exception as error:
        journal.record("campaign_experiment_plan_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_usage=dict(reviews.ZERO_USAGE))
        raise CampaignPlanError(str(error), journal.directory) from error
    return journal.directory


def verify_plan(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "plan.json", "campaign_experiment_plan_registered")
    sources = _sources(Path(record["review"]["directory"]))
    expected = _record(directory, *sources)
    if (_canonical(record) != _canonical(expected)
            or _read(directory / "development.xml", len(sources[5])) != sources[5]):
        raise ValueError("El plan, datos, revisión, controles o código han cambiado.")
    # Verificar el artefacto no consulta disponibilidad actual ni devuelve reservas.
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} — plan de experimento revisado sin ejecutar")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--review-run", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path)
    commands.add_parser("verify").add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_plan(args.run), ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(prepare_plan(args.review_run, **kwargs))
    except ERRORS as error:
        parser.exit(1, f"Plan de campaña detenido: {error}\n")


if __name__ == "__main__": main()
