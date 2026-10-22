"""Plan de campaña local: límites explícitos e historial, sin activar herramientas."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.compact_ollama import SUPPORTED_SERVER_VERSION
from trading_ai.formalization import _read, _strict_json
from trading_ai.guided_compact_request import _code_hashes as _guided_hashes, verify_guided_request
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_draft_request import MAX_REQUEST_BYTES


SOURCE_FILES = ("guided.json", "guided.json.sha256", "request.json", "events.jsonl")
MAX_PROPOSALS = 3
MAX_BACKTESTS = 6


def validate_campaign_limits(limits: dict) -> dict:
    """Valida un techo solicitado; no concede ni reserva ese presupuesto."""
    if not isinstance(limits, dict) or set(limits) != {"max_proposals", "max_backtests"}:
        raise ValueError("Indica únicamente max_proposals y max_backtests.")
    proposals, backtests = limits["max_proposals"], limits["max_backtests"]
    if type(proposals) is not int or not 1 <= proposals <= MAX_PROPOSALS:
        raise ValueError("El límite de propuestas debe ser un entero entre 1 y 3.")
    if (type(backtests) is not int or backtests not in (0, 2, 4, MAX_BACKTESTS)
            or backtests > 2 * proposals):
        raise ValueError("El límite de backtests debe ser 0, 2, 4 o 6 y como máximo dos por propuesta.")
    return {"max_proposals": proposals, "max_backtests": backtests}


def _code_hashes() -> dict:
    return {**_guided_hashes(), "campaign_plan.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _sources(directory: Path) -> tuple[dict, dict, bytes, dict]:
    guided = verify_guided_request(directory)
    origin = _origin(directory, SOURCE_FILES)
    raw = _read(directory / "request.json", MAX_REQUEST_BYTES)
    if sha256(raw).hexdigest() != guided["request_sha256"] or origin["sha256"]["request.json"] != guided["request_sha256"]:
        raise ValueError("La petición guiada cambió durante su lectura.")
    payload = _strict_json(raw)
    context = _strict_json(payload["messages"][1]["content"])
    if (context["known_history"] is not True or context["outer_evaluation_allowed"] is not False
            or context["data"]["sha256"] != guided["reference"]["development_sha256"]):
        raise ValueError("La campaña requiere desarrollo conocido y evaluación exterior desactivada.")
    identity = guided["generation_budget"]["identity"]
    if (identity["development_sha256"] != context["data"]["sha256"]
            or identity["pair"] != context["controls"]["pair"]):
        raise ValueError("El presupuesto heredado no identifica los datos y par de la campaña.")
    if context["compact_generation_budget"] != {
            "consumed": guided["generation_budget"]["consumed"], "new_permission_granted": False}:
        raise ValueError("La petición no conserva el presupuesto compacto observado.")
    return guided, origin, raw, context


def _record(directory: Path, guided: dict, origin: dict, raw: bytes, context: dict, limits: dict) -> dict:
    limits = validate_campaign_limits(limits)
    identity = {"schema_version": 1, "protocol": "local_campaign_scope_v1",
                "development_sha256": guided["reference"]["development_sha256"], "pair": context["controls"]["pair"]}
    history = {"structured_history": deepcopy(context["untrusted_history"]),
               "compact_attempts": deepcopy(context["untrusted_compact_history"]),
               "consumed_rule_identities": deepcopy(context["consumed_rule_identities"]),
               "typed_rule_coverage": deepcopy(context["typed_rule_coverage"])}
    return {
        "schema_version": 1, "protocol": "local_campaign_plan_v1", "status": "planned_not_activated",
        "run_dir": str(directory), "source_guided": origin, "reference": deepcopy(guided["reference"]),
        "identity": identity, "scope_id": sha256(_canonical(identity)).hexdigest(),
        "scope_identity_excludes": ["output_directory", "limits", "criterion", "risk_parameters"],
        "objective": deepcopy(context["objective"]), "controls": deepcopy(context["controls"]),
        "data": deepcopy(context["data"]), "scope": "known_development_history_only",
        "limits": limits, "limits_sha256": sha256(_canonical(limits)).hexdigest(),
        "proposed_budget": {"model_requests": limits["max_proposals"], "backtests": limits["max_backtests"],
                            "backtests_per_comparison": 2, "automatic_retries": 0, "reformulations": 0,
                            "period_diagnostics": 0},
        "budget_state": {"reserved_model_requests": 0, "reserved_backtests": 0,
                         "executable_model_requests": 0, "executable_backtests": 0,
                         "activation_ledger_implemented": False},
        "inherited_generation_budget": deepcopy(guided["generation_budget"]),
        "inherited_usage": deepcopy(guided["inherited_attempt_usage"]),
        "inherited_usage_scope": "captured_compact_attempts_not_all_application_usage",
        "history": history, "history_sha256": sha256(_canonical(history)).hexdigest(),
        "history_entries_omitted": 0, "history_text_truncated": False,
        "request_sha256": sha256(raw).hexdigest(), "request_bytes": len(raw),
        "request_role": "unchanged_guided_preview_not_campaign_transport",
        "max_request_bytes": MAX_REQUEST_BYTES, "token_count": None, "fits_provider_context_verified": False,
        "provider_policy": {"provider": "ollama", "server_version_required": SUPPORTED_SERVER_VERSION,
                            "network": "loopback_only", "gpu_layers": 0, "max_context_tokens": 4096,
                            "max_output_tokens": 384, "max_timeout_seconds": 180,
                            "context_overflow": "reject_without_truncation", "model_identity_bound": False},
        "stage_contract": {
            "proposal": "one_new_rule_pair_per_reserved_request_no_pending_lineage_reformulation",
            "review": "explicit_accepted_compact_assessment_required_before_plan",
            "calculation": "verified_plan_and_shared_calculation_claim_before_existing_engine",
            "analysis": "existing_python_criterion_keep_negative_and_inconclusive_results",
            "memory": "refresh_full_history_and_consumed_identities_before_each_future_request",
            "selection": "no_automatic_adoption_or_claim_of_independent_validation"},
        "future_stop_conditions": ["proposal_or_backtest_budget_exhausted", "unknown_usage",
                                   "stale_history_or_changed_sources", "changed_controls_or_code",
                                   "context_overflow_or_incomplete_history", "provider_identity_unverified"],
        "future_discard_policy": {"duplicate_or_failed_request_consumes_attempt": True,
                                  "keep_original_response_errors_and_usage": True,
                                  "discarded_candidate_may_be_simulated": False,
                                  "new_plan_resets_legacy_budgets": False},
        "activation_requirements": ["explicit_campaign_allowance_not_legacy_budget_reset",
                                    "shared_scope_ledger_and_atomic_reservations",
                                    "fresh_full_history_and_bound_local_provider",
                                    "controlled_runner_with_review_and_calculation_claims"],
        "provider_configured": False, "submitted": False, "generation_ready": False,
        "new_generation_permission": False, "executable": False, "calculated_results": None,
        "outer_evaluation_allowed": False, "broker_operations_allowed": False,
        "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0,
                      "api_cost_usd": "0", "backtests": 0},
        "code_sha256": _code_hashes()}


def prepare_campaign_plan(guided_dir: str | Path, limits: dict, *,
                          output_dir: str | Path = ROOT / ".local/campaign-plans") -> Path:
    """Registra la intención de una campaña; no crea reservas o herramientas de envío."""
    limits = validate_campaign_limits(limits)
    guided_dir = Path(guided_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("campaign_plan_started", guided_dir=str(guided_dir), requested_limits=limits)
    try:
        guided, origin, raw, context = _sources(guided_dir)
        record = _record(journal.directory, guided, origin, raw, context, limits)
        _write_exclusive(journal.directory / "limits.json", _canonical(limits))
        _write_exclusive(journal.directory / "request.json", raw)
        current = _record(journal.directory, *_sources(guided_dir), limits)
        if _canonical(current) != _canonical(record):
            raise ValueError("Las fuentes, memoria o presupuesto cambiaron al preparar la campaña.")
        _seal(journal, "campaign.json", record, "campaign_plan_prepared")
    except Exception as error:
        journal.record("campaign_plan_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise ValueError(f"Campaña no preparada: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_campaign_plan(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "campaign.json", "campaign_plan_prepared")
    limits_raw = _read(directory / "limits.json", 1024)
    limits = validate_campaign_limits(_strict_json(limits_raw))
    if limits_raw != _canonical(limits):
        raise ValueError("Los límites de la campaña no conservan sus bytes originales.")
    expected = _record(directory, *_sources(Path(record["source_guided"]["directory"])), limits)
    if (_canonical(record) != _canonical(expected)
            or _read(directory / "request.json", MAX_REQUEST_BYTES) != _read(
                Path(record["source_guided"]["directory"]) / "request.json", MAX_REQUEST_BYTES)):
        raise ValueError("La campaña, límites, memoria, fuentes o código han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — planificar una campaña local sin activarla")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--guided-run", type=Path, required=True)
    prepare.add_argument("--max-proposals", type=int, required=True)
    prepare.add_argument("--max-backtests", type=int, required=True)
    prepare.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            print(json.dumps(verify_campaign_plan(args.run), ensure_ascii=True))
        else:
            limits = {"max_proposals": args.max_proposals, "max_backtests": args.max_backtests}
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(prepare_campaign_plan(args.guided_run, limits, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Campaña no verificable: {error}\n")


if __name__ == "__main__":
    main()
