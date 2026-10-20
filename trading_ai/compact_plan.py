"""Plan previo de una candidata compacta revisada; controles congelados, cero cálculos."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.compact_candidate import verify_compact_candidate
from trading_ai.compact_review import _code_hashes as _review_hashes, verify_compact_review
from trading_ai.formalization import _read
from trading_ai.holdout import EXECUTION_POLICY, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.robustness import _development
from trading_ai.rule_planning import BUDGET, _artifact, _canonical, _seal
from trading_ai import rule_execution as execution


REVIEW_FILES = ("review.json", "review.json.sha256", "events.jsonl", "assessment.json")


class CompactPlanError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_review_hashes(), **execution._code_hashes(), "compact_plan.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _sources(review_dir: Path) -> tuple:
    review = verify_compact_review(review_dir)
    if review["status"] != "accepted" or review["eligible_for_plan"] is not True:
        raise ValueError("Solo una revisión compacta aceptada admite un plan.")
    candidate = verify_compact_candidate(review["source"]["directory"])
    frozen, reference, content = _development(Path(review["reference"]["frozen_dir"]))
    if reference != review["reference"] or candidate["reference"] != reference:
        raise ValueError("La revisión, candidata y datos congelados no coinciden.")
    return review, _origin(review_dir, REVIEW_FILES), candidate, frozen, reference, content


def _record(review: dict, origin: dict, candidate: dict, frozen: dict, reference: dict, directory: Path) -> dict:
    policy = frozen["policy"]
    record = {"schema_version": 1, "protocol": "compact_development_plan_v1", "stage": "registered_not_run",
              "run_dir": str(directory), "review": origin, "reference": reference,
              "candidate_id": review["source"]["sha256"]["candidate.json"],
              "candidate": {"spec": candidate["spec"], "spec_sha256": candidate["spec_sha256"]},
              "baseline": {"strategy": policy["baseline_strategy"], "fast_window": policy["fast_window"],
                           "slow_window": policy["slow_window"]},
              "policy": deepcopy(policy), "criterion": frozen["proposal"]["criterion"],
              "objective_origin": "frozen_development_objective_not_model_prose",
              "data": {**frozen["development_result"]["source"], "file": "development.xml"},
              "budget": deepcopy(BUDGET), "execution_policy": deepcopy(EXECUTION_POLICY),
              "execution_timing": "next_observation", "direction": "long_only",
              "assessment_rules": {"implementation": "experiments.expected_assessment", "minimum_closed_trades_each": 1,
                                   "both_metrics_equal": "inconclusive"},
              "scope": "known_development_history_only", "outer_evaluation_allowed": False,
              "executable": False, "calculated_results": None,
              "execution_requires_explicit_tool": True, "inherited_usage": candidate["usage"],
              "inherited_api_cost_usd": candidate["api_cost_usd"],
              "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
              "code_sha256": _code_hashes()}
    record["calculation_id"] = sha256(_canonical(execution._identity(record))).hexdigest()
    return record


def prepare_compact_plan(review_dir: str | Path, *, output_dir: str | Path = ROOT / ".local/compact-plans") -> Path:
    review_dir = Path(review_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("compact_plan_started", review_dir=str(review_dir))
    try:
        review, origin, candidate, frozen, reference, content = _sources(review_dir)
        record = _record(review, origin, candidate, frozen, reference, journal.directory)
        # Se comparte la identidad con todos los ejecutores históricos. Cambiar
        # contrato, nombre técnico o criterio no libera un cálculo consumido.
        access = execution.ACCESS_ROOT / (record["calculation_id"] + ".json")
        if access.exists():
            raise ValueError("Estos cálculos ya tienen un intento reservado; no se crea otro plan.")
        journal.record("calculation_access_checked", calculation_id=record["calculation_id"], consumed=False)
        _write_exclusive(journal.directory / "development.xml", content)
        current = _sources(review_dir)
        if current[1] != origin or current[-1] != content or record["code_sha256"] != _code_hashes():
            raise ValueError("Las fuentes o el código cambiaron al preparar el plan.")
        _seal(journal, "plan.json", record, "compact_plan_registered")
    except Exception as error:
        journal.record("compact_plan_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise CompactPlanError(str(error), journal.directory) from error
    return journal.directory


def verify_compact_plan(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "plan.json", "compact_plan_registered")
    review, origin, candidate, frozen, reference, content = _sources(Path(record["review"]["directory"]))
    if (_canonical(record) != _canonical(_record(review, origin, candidate, frozen, reference, directory))
            or _read(directory / "development.xml", len(content)) != content):
        raise ValueError("El plan, controles, presupuesto, fuentes o código han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — registrar un plan compacto sin ejecutarlo")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--review-run", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_compact_plan(args.run), ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(prepare_compact_plan(args.review_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Plan no verificable: {error}\n")


if __name__ == "__main__":
    main()
