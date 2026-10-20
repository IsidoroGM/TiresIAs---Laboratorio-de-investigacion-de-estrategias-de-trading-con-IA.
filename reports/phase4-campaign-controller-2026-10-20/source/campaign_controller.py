"""Primer control de campaña: contrasta capturas y reglas sin conceder ejecución."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import PROJECT_NAME
from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_ledger as ledger
from trading_ai.campaign_plan import verify_campaign_plan
from trading_ai.formalization import _read, _strict_json
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _canonical
from trading_ai.structured_draft import DRAFT_SCHEMA, MAX_DRAFT_BYTES, describe_draft


CAPTURE_FILES = ("attempt.json", "attempt.json.sha256", "submission.json", "submission.json.sha256",
                 "completion.json", "completion.json.sha256", "request.json", "observation.raw", "events.jsonl")
ERRORS = (ValueError, OSError, KeyError, TypeError, IndexError, RecursionError)


def _code_hashes():
    from trading_ai.structured_draft import _code_hashes as draft_hashes
    return {**attempts._code_hashes(), **draft_hashes(),
            "campaign_controller.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _plan(state):
    registration = state["registration"]
    directory = Path(registration["plan"]["directory"])
    plan = verify_campaign_plan(directory)
    if (plan["scope_id"] != state["scope_id"]
            or registration["plan"] != _origin(directory, ledger.PLAN_FILES)
            or registration["identity"] != plan["identity"]
            or registration["terms"] != {key: plan[key] for key in registration["terms"]}):
        raise ValueError("El plan vigente no corresponde al registro y sus controles.")
    return plan


def _proposal(state, receipt, plan):
    item = {"receipt_id": receipt["receipt_id"], "request_sha256": receipt["operation_id"],
            "status": "blocked", "issues": [], "capture": None,
            "draft": None, "spec_sha256": None, "rule_description": None,
            "model_description": None, "hypothesis_supplied": False,
            "technical_review": "not_performed", "transport_verified": False,
            "eligible_for_calculation": False, "calculated_results": None}
    try:
        directory, _, intent, completion = attempts._load(state, receipt)
        files = tuple(name for name in CAPTURE_FILES if (directory / name).is_file())
        item["capture"] = _origin(directory, files)
        if completion is None:
            item["issues"].append("observation_unresolved")
            return item
        if completion["analysis"]["requires_stop"]:
            item["issues"].append("usage_or_capture_unverifiable")
            return item
        raw = _read(directory / "request.json", 12288)
        expected = _read(Path(plan["run_dir"]) / "request.json", 12288)
        if raw != expected or sha256(raw).hexdigest() != plan["request_sha256"]:
            item["issues"].append("request_not_bound_to_registered_plan")
            return item
        payload = _strict_json(raw)
        if (not isinstance(payload, dict) or set(payload) != {"messages", "schema"}
                or _canonical(payload["schema"]) != _canonical(DRAFT_SCHEMA)):
            item["issues"].append("unsupported_request_contract")
            return item
        observation = _strict_json(_read(directory / "observation.raw", attempts.MAX_OBSERVATION_BYTES))
        # El origen es la observación del llamador: no acredita envío o identidad del proveedor.
        if observation["error"] is not None:
            item.update(status="provider_error", source_error=deepcopy(observation["error"]))
            return item
        usage = completion["analysis"]["usage"]
        if (observation["model_request_attempted"] is not True or intent is None
                or not isinstance(observation["model"], str) or not observation["model"].strip()
                or usage["input_tokens"] < 1 or usage["output_tokens"] < 1):
            item["issues"].append("incomplete_success_observation")
            return item
        content = observation["content"]
        try:
            if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_DRAFT_BYTES:
                raise ValueError("Se requieren reglas JSON completas dentro del límite de bytes.")
            draft = _strict_json(content)
            described = describe_draft(draft)
        except (ValueError, TypeError, KeyError, IndexError, RecursionError) as error:
            item.update(status="invalid_rules", validation_error=str(error)[:1000])
            return item
        item.update(status="pending_technical_review", draft=draft,
                    spec_sha256=described["spec_sha256"], rule_description=described["rule_description"],
                    description_origin="python_from_typed_rules_not_model_prose")
        if item["spec_sha256"] in plan["history"]["consumed_rule_identities"]:
            item.update(status="duplicate_rules", duplicate_origin="captured_consumed_history")
    except ERRORS as error:
        item["issues"].append("unverifiable_capture")
        item["error"] = str(error)[:1000]
    return item


def inspect_controller(scope_id: str) -> dict:
    """Consulta sin escrituras; no sustituye un permiso o una comprobación previa al envío."""
    state = ledger.inspect_campaign(scope_id)
    if state["status"] != "registered_inactive":
        raise ValueError("El ámbito no está registrado; no se creará o activará.")
    code = _code_hashes()
    plan = _plan(state)  # Incluye vigencia completa de las fuentes y memoria guiadas.
    summary = attempts.inspect_attempts(scope_id)
    proposals = [_proposal(state, receipt, plan) for receipt in state["reservations"] if receipt["kind"] == "proposal"]
    checks = []
    for item in proposals:
        if item["capture"] is not None:
            checks.append((item["capture"], _origin(Path(item["capture"]["directory"]), tuple(item["capture"]["sha256"]))))
    # Dos lecturas detectan cambios ordinarios; no mantienen un bloqueo global de archivos.
    if (ledger.inspect_campaign(scope_id) != state or _canonical(_plan(state)) != _canonical(plan)
            or attempts.inspect_attempts(scope_id) != summary or _code_hashes() != code
            or any(before != after for before, after in checks)):
        raise ValueError("Las reservas, capturas, memoria, fuentes o código cambiaron durante el control.")
    issues = ["comparison_without_controlled_review"] if state["reserved_backtests"] else []
    stopped = bool(issues) or summary["requires_stop"] or any(item["status"] == "blocked" for item in proposals)
    pending = sum(item["status"] == "pending_technical_review" for item in proposals)
    return {"schema_version": 1, "protocol": "campaign_controller_inspection_v1", "scope_id": scope_id,
            "status": "blocked" if stopped else "review_pending" if pending else "inactive",
            "plan": deepcopy(state["registration"]["plan"]), "controls": deepcopy(plan["controls"]),
            "objective": deepcopy(plan["objective"]), "limits": deepcopy(plan["limits"]),
            "reserved_model_requests": state["reserved_model_requests"], "reserved_backtests": state["reserved_backtests"],
            "remaining_accounting_slots": deepcopy(state["remaining_accounting_slots"]),
            "usage": summary["usage"], "known_subtotals": summary["known_subtotals"],
            "inherited_usage": summary["inherited_usage"],
            "inherited_usage_scope": "captured_compact_attempts_not_all_application_usage",
            "proposals": proposals, "technical_reviews_pending": pending, "requires_stop": bool(stopped), "issues": issues,
            "current_source_freshness_verified": True, "comparison_mode": "optimistic_double_read_not_transactional",
            "source_freshness_scope": "registered_guided_sources_not_complete_future_campaign_context",
            "campaign_history_in_future_request_verified": False,
            "transport_verified": False, "provider_identity_bound": False,
            "execution_blockers": ["explicit_campaign_allowance_missing", "controlled_sender_not_implemented",
                                   "accepted_campaign_review_and_plan_required", "shared_calculation_claim_required"],
            "execution_authorized": False, "executable_model_requests": 0, "executable_backtests": 0,
            "calculated_results": None, "outer_evaluation_allowed": False, "broker_operations_allowed": False,
            "new_usage": {**attempts.ZERO_USAGE, "backtests": 0}, "code_sha256": code}


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} — comprobar campaña sin enviar o calcular")
    parser.add_argument("--scope", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect_controller(args.scope), ensure_ascii=True))
    except ERRORS as error:
        parser.exit(1, f"Control de campaña detenido: {error}\n")


if __name__ == "__main__":
    main()
