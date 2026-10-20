"""Lectura breve del estado de propuestas y revisiones compactas, sin actuar."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.compact_history import _claims, _entry
from trading_ai.research import _api_cost
from trading_ai.rule_planning import _canonical
from trading_ai.structured_generation import _scope, generation_budget_status


LABELS = {
    "no_attempt_reserved": "Sin intento compacto reservado.",
    "duplicate_rules": "Bloqueado: reglas duplicadas; no se repetirá la generación.",
    "failed_preserved": "Bloqueado: intento fallido conservado, sin reintento automático.",
    "reservation_unfinished": "Bloqueado: reserva interrumpida, con intento consumido.",
    "reserved_without_submission": "Bloqueado: intento reservado, sin envío registrado.",
    "submission_unfinished": "Bloqueado: envío sin cierre comprobable; consumo de origen desconocido.",
    "awaiting_technical_review": "Pendiente de revisión técnica, sin permiso de cálculo.",
    "review_attempt_unfinished": "Bloqueado: revisión reservada sin cierre comprobable.",
    "accepted": "Revisión aceptada: puede prepararse un plan mediante una acción separada.",
    "rejected": "Bloqueado: revisión rechazada.",
    "needs_clarification": "Bloqueado: la revisión requiere aclaración; no se reabre automáticamente.",
}


def _source_usage(entries: list[dict]) -> dict:
    sources = [entry["source_usage"] for entry in entries]
    if not sources:
        return {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0"}
    requests = [source.get("model_requests") for source in sources]
    totals = {"model_requests": sum(requests) if all(type(value) is int for value in requests) else None,
              "api_cost_usd": _api_cost([{"api_cost_usd": source.get("api_cost_usd")} for source in sources])}
    for key in ("input_tokens", "output_tokens"):
        counts = []
        for source in sources:
            if source.get("model_requests") == 0:
                counts.append(0)
            elif source.get("model_requests") == 1 and len(source.get("usage", [])) == 1:
                counts.append(source["usage"][0].get(key))
            else:
                counts.append(None)
        totals[key] = sum(counts) if all(type(value) is int for value in counts) else None
    return totals


def _snapshot(request_dir: Path) -> dict:
    request, identity = _scope(request_dir)
    entries = [_entry(item) for item in _claims(identity)]
    if len(entries) > 1: raise ValueError("Más de un intento para la misma identidad compacta; no se concede permiso.")
    if not entries: status = "no_attempt_reserved"
    else:
        entry = entries[0]
        status = entry["status"]
        if status == "pending_technical_review":
            status = "awaiting_technical_review" if entry["review"] is None else entry["review"]["status"]
    if status not in LABELS: raise ValueError("Estado compacto no reconocido; se conserva el bloqueo.")
    return {"schema_version": 1, "protocol": "compact_status_v1", "status": status, "message": LABELS[status],
            "reference": request["reference"], "generation_budget": generation_budget_status(request_dir),
            "source_usage": _source_usage(entries), "usage_scope": "compact_attempts_only_excludes_legacy",
            "source_entries": entries, "inspection_scope": "proposal_and_review_only_executions_not_inspected",
            "execution_state": "not_inspected", "new_generation_permission": False, "executable": False,
            "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0}}


def inspect_compact_status(request_dir: str | Path) -> dict:
    directory = Path(request_dir).resolve()
    first = _snapshot(directory)
    if _canonical(first) != _canonical(_snapshot(directory)):
        raise ValueError("El estado cambió durante la lectura; no se publica un estado mezclado.")
    return {**first, "fingerprint": sha256(_canonical(first)).hexdigest()}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — estado compacto de solo lectura")
    parser.add_argument("--request-run", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        status = inspect_compact_status(args.request_run)
        if args.json:
            print(json.dumps(status, ensure_ascii=True))
        else:
            print(status["message"])
            print("Presupuesto de generación: " + ("consumido." if status["generation_budget"]["consumed"] else "sin reserva; esta lectura no concede permiso."))
            print("Consulta de estado: cero llamadas de modelo y simulaciones. Las ejecuciones no se inspeccionan.")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Estado no verificable: {error}\n")


if __name__ == "__main__": main()
