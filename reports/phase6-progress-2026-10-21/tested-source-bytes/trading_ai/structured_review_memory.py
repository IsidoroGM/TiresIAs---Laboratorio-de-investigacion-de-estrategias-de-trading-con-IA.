"""Memoria de revisiones de sesiones registradas; no reabre acciones ni lee resultados financieros."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _check_origin, _inside
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_draft_context import _code_hashes as _context_hashes, verify_draft_context
from trading_ai.structured_planning import verify_structured_review
from trading_ai import structured_session as sessions


MAX_SESSIONS = 128
_REVIEW_FILES = {"review.json", "review.json.sha256", "events.jsonl"}


def _session_claim(path: Path) -> dict:
    raw = _read(path, 8192)
    claim = _strict_json(raw)
    if (not isinstance(claim, dict) or set(claim) != {"schema_version", "identity", "session_dir"}
            or type(claim["schema_version"]) is not int or claim["schema_version"] != 1
            or not isinstance(claim["identity"], dict)
            or set(claim["identity"]) != {"schema_version", "reference", "proposal_sha256"}
            or type(claim["identity"]["schema_version"]) is not int or claim["identity"]["schema_version"] != 1
            or not isinstance(claim["identity"]["reference"], dict)
            or not isinstance(claim["identity"]["proposal_sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", claim["identity"]["proposal_sha256"]) is None
            or not isinstance(claim["session_dir"], str) or not Path(claim["session_dir"]).is_absolute()
            or path.parent != sessions.ACCESS_ROOT.resolve()
            or path.name != sha256(_canonical(claim["identity"])).hexdigest() + ".json"):
        raise ValueError("Reserva de sesión incompatible con su identidad o ubicación.")
    return {"path": str(path), "sha256": sha256(raw).hexdigest(), "claim": claim}


def _capture_claims(reference: dict) -> list[dict]:
    paths = sorted(sessions.ACCESS_ROOT.resolve().glob("*.json"))
    if len(paths) > MAX_SESSIONS:
        raise ValueError("Demasiadas reservas de sesión; no se descartarán fuentes.")
    claims = [_session_claim(path) for path in paths]
    return [item for item in claims if item["claim"]["identity"]["reference"] == reference]


def _entry(item: dict, context: dict, rule_claims: dict) -> dict:
    if not isinstance(item, dict) or set(item) != {"path", "sha256", "claim"}:
        raise ValueError("Origen de sesión incompatible.")
    path = Path(item["path"])
    if not path.is_absolute() or path.parent != sessions.ACCESS_ROOT.resolve() or _session_claim(path) != item:
        raise ValueError("La reserva de sesión ha cambiado.")
    session = Path(item["claim"]["session_dir"]).resolve()
    manifest, proposal = sessions._load(session)
    if (manifest["reference"] != context["reference"]
            or item["claim"]["identity"] != sessions._identity(manifest["source"], manifest["reference"])):
        raise ValueError("La sesión no corresponde a este desarrollo y propuesta.")
    if not any(value["claim"]["run_dir"] == manifest["source"]["directory"]
               and value["claim"]["identity"]["spec_sha256"] == proposal["spec_sha256"]
               for value in rule_claims["entries"]):
        raise ValueError("El contexto no contiene la reserva de esta propuesta; preparar uno actualizado.")
    result = {"session": str(session), "proposal_source": deepcopy(manifest["source"]),
              "spec_sha256": proposal["spec_sha256"], "finish_consumed": False,
              "review_status": "not_registered", "review": None, "finish_origin": None,
              "proposal_text_lengths": {key: len(proposal["proposal"][key]) for key in ("title", "hypothesis")},
              "source_usage": {"model_requests": proposal["model_requests"], "usage": deepcopy(proposal["usage"]),
                               "api_cost_usd": proposal["api_cost_usd"]},
              "session_outcome_checked": False, "financial_results_read": False}
    action_path = session / "actions/finish.json"
    if not action_path.exists():
        return result
    action_raw = _read(action_path, 4096)
    action = _strict_json(action_raw)
    if not isinstance(action, dict) or set(action) != {"attempt"}:
        raise ValueError("Reserva de finalización incompatible.")
    attempt = _inside(session, action["attempt"])
    events_raw = _read(attempt / "events.jsonl", 4 * 1024 * 1024)
    events = [_strict_json(line) for line in events_raw.splitlines()]
    reviews = [event["data"]["origin"] for event in events
               if event["event"] == "artifact_registered" and event["data"].get("kind") == "review"]
    result.update(finish_consumed=True, review_status="finish_consumed_without_registered_review",
                  finish_origin={"attempt": str(attempt), "action_sha256": sha256(action_raw).hexdigest(),
                                 "events_sha256": sha256(events_raw).hexdigest()})
    if len(reviews) > 1:
        raise ValueError("La finalización registra más de una revisión.")
    if not reviews:
        return result
    origin = reviews[0]
    if (not isinstance(origin, dict) or set(origin) != {"directory", "sha256"}
            or not isinstance(origin["sha256"], dict) or set(origin["sha256"]) != _REVIEW_FILES):
        raise ValueError("La revisión no tiene los tres archivos de origen esperados.")
    review = verify_structured_review(_check_origin(session, origin), Path(context["reference"]["frozen_dir"]))
    if review["source"] != manifest["source"]:
        raise ValueError("La revisión pertenece a otra propuesta.")
    result.update(review_status=review["status"], review={"origin": origin, "reviewer": review["assessment"]["reviewer"],
                  "reason": review["reason"], "checks": deepcopy(review["assessment"]["checks"]),
                  "reason_is_unverified_reviewer_text": True})
    return result


def _code_hashes() -> dict:
    return {**_context_hashes(), **sessions._code_hashes(),
            "structured_review_memory.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _record(directory: Path, context_dir: Path) -> dict:
    context = verify_draft_context(context_dir)
    rule_claims = _strict_json(_read(context_dir / "claims.json", 2 * 1024 * 1024))
    raw = _read(directory / "sessions.json", 2 * 1024 * 1024)
    claims = _strict_json(raw)
    if (not isinstance(claims, list) or len(claims) > MAX_SESSIONS
            or len({item["path"] for item in claims}) != len(claims)):
        raise ValueError("Copia de sesiones incompatible o repetida.")
    entries = [_entry(item, context, rule_claims) for item in claims]
    return {"schema_version": 1, "protocol": "structured_review_memory_v1", "status": "review_memory_only",
            "run_dir": str(directory), "reference": context["reference"],
            "context": {"directory": str(context_dir), "sha256": {
                name: sha256(_read(context_dir / name, 2 * 1024 * 1024)).hexdigest()
                for name in ("context.json", "context.json.sha256", "memory.json", "rules-memory.json", "claims.json", "events.jsonl")}},
            "sessions_sha256": sha256(raw).hexdigest(), "entries": entries,
            "scope": "captured_registered_sessions_only_not_all_independent_reviews",
            "generation_ready": False, "eligible_for_session": False, "executable": False,
            "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
            "code_sha256": _code_hashes()}


def _report(record: dict) -> str:
    lines = ["# Memoria de revisiones registradas", "",
             "Texto del revisor conservado como declaración, sin demostrar su corrección o rentabilidad.", ""]
    for entry in record["entries"]:
        lines += ["Sesión: " + Path(entry["session"]).name, "Estado de revisión: " + entry["review_status"],
                  "Longitudes comprobadas de la propuesta: " + json.dumps(entry["proposal_text_lengths"], ensure_ascii=False), ""]
        if entry["review"] is not None:
            lines += ["Motivo original del revisor:", ""]
            lines += ["    " + line for line in entry["review"]["reason"].split("\n")]
            lines.append("")
    lines += ["No comprueba el cierre financiero de la sesión ni recopila revisiones independientes fuera del registro.",
              "La captura puede requerir renovación si una sesión cambia de etapa.",
              "No reabre acciones ni concede permisos de generación, revisión o simulación.",
              "Cero consultas nuevas, backtests y coste nuevo de API; el consumo heredado sigue separado.", ""]
    return "\n".join(lines)


def capture_review_memory(context_dir: str | Path, *,
                          output_dir: str | Path = ROOT / ".local/structured-review-memory") -> Path:
    context_dir = Path(context_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("structured_review_memory_started", context_dir=str(context_dir))
    try:
        context = verify_draft_context(context_dir)
        claims = _capture_claims(context["reference"])
        journal.save("sessions.json", claims)
        record = _record(journal.directory, context_dir)
        if _canonical(_capture_claims(context["reference"])) != _canonical(claims):
            raise ValueError("Las reservas de sesión cambiaron durante la captura.")
        if _canonical(_record(journal.directory, context_dir)) != _canonical(record):
            raise ValueError("Una sesión cambió durante la captura de revisiones.")
        _write_exclusive(journal.directory / "report.md", _report(record).encode("utf-8"))
        _seal(journal, "reviews.json", record, "structured_review_memory_completed")
    except Exception as error:
        journal.record("structured_review_memory_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise ValueError(f"Memoria detenida: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_review_memory(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "reviews.json", "structured_review_memory_completed")
    expected = _record(directory, Path(record["context"]["directory"]))
    if (_canonical(record) != _canonical(expected)
            or _read(directory / "report.md", 2 * 1024 * 1024) != _report(record).encode("utf-8")):
        raise ValueError("La memoria, sus revisiones, fuentes o ubicación han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — memoria de revisiones sin acciones o cálculos")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture")
    capture.add_argument("--context-run", type=Path, required=True)
    capture.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            print(json.dumps(verify_review_memory(args.run), ensure_ascii=False))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(capture_review_memory(args.context_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Memoria no verificable: {error}\n")


if __name__ == "__main__":
    main()
