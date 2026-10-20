"""Vigencia comprobada por doble lectura; no es una reserva ni una transacción global."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.formalization import _read, _strict_json
from trading_ai.idea_memory import capture_memory
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_draft_context import _claims
from trading_ai.structured_draft_request import _code_hashes as _request_hashes, verify_draft_request
from trading_ai.structured_review_memory import _capture_claims
from trading_ai import structured_ideas as ideas


def _current(reference: dict) -> dict:
    frozen = Path(reference["frozen_dir"])
    return {"legacy": capture_memory(frozen), "rules": ideas._rules_memory(reference, frozen),
            "rule_claims": _claims(reference), "session_claims": _capture_claims(reference)}


def _code_hashes() -> dict:
    return {**_request_hashes(), "structured_freshness.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def inspect_request_freshness(request_dir: str | Path) -> dict:
    directory = Path(request_dir).resolve()
    request = verify_draft_request(directory)
    memory_dir = Path(request["source"]["directory"])
    memory = _strict_json(_read(memory_dir / "reviews.json", 2 * 1024 * 1024))
    context_dir = Path(memory["context"]["directory"])
    saved = {key: _strict_json(_read(context_dir / name, 2 * 1024 * 1024))
             for key, name in (("legacy", "memory.json"), ("rules", "rules-memory.json"), ("rule_claims", "claims.json"))}
    saved["session_claims"] = _strict_json(_read(memory_dir / "sessions.json", 2 * 1024 * 1024))
    first = _current(request["reference"])
    if _canonical(_current(request["reference"])) != _canonical(first):
        raise ValueError("El historial cambió durante la comprobación; volver a preparar contexto.")
    # También comprobar cambios en revisiones u otras fuentes entre ambas lecturas.
    if _canonical(verify_draft_request(directory)) != _canonical(request):
        raise ValueError("La petición cambió durante la comprobación de vigencia.")
    comparisons = {key: {"captured_sha256": sha256(_canonical(saved[key])).hexdigest(),
                         "current_sha256": sha256(_canonical(value)).hexdigest(),
                         "matches": _canonical(saved[key]) == _canonical(value)} for key, value in first.items()}
    current = all(value["matches"] for value in comparisons.values())
    record = {"schema_version": 1, "protocol": "structured_request_freshness_v1", "status": "current" if current else "stale",
              "request": {"directory": str(directory), "payload_sha256": request["request_sha256"], "sha256": {
                  name: sha256(_read(directory / name, 2 * 1024 * 1024)).hexdigest()
                  for name in ("preview.json", "preview.json.sha256", "request.json", "events.jsonl")}},
              "reference": request["reference"], "comparisons": comparisons,
              "comparison_mode": "optimistic_double_read_not_transactional", "code_sha256": _code_hashes(),
              "provider_context_fit_verified": False, "generation_ready": False, "submitted": False, "executable": False,
              "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0}}
    record["fingerprint"] = sha256(_canonical(record)).hexdigest()
    return record


def require_current_request(request_dir: str | Path, *, expected_fingerprint: str | None = None) -> dict:
    record = inspect_request_freshness(request_dir)
    if record["status"] != "current":
        changed = ", ".join(key for key, item in record["comparisons"].items() if not item["matches"])
        raise ValueError("La petición está desactualizada: " + changed + ". Preparar contexto y petición nuevos.")
    if expected_fingerprint is not None and record["fingerprint"] != expected_fingerprint:
        raise ValueError("La huella de vigencia ya no coincide con la comprobación anterior.")
    return record


def capture_request_freshness(request_dir: str | Path, *,
                              output_dir: str | Path = ROOT / ".local/structured-freshness") -> Path:
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("structured_freshness_started", request_dir=str(Path(request_dir).resolve()))
    try:
        record = {"run_dir": str(journal.directory), **inspect_request_freshness(request_dir)}
        _seal(journal, "freshness.json", record, "structured_freshness_completed")
    except Exception as error:
        journal.record("structured_freshness_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise ValueError(f"Vigencia no comprobada: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_request_freshness(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "freshness.json", "structured_freshness_completed")
    expected = {"run_dir": str(directory), **inspect_request_freshness(record["request"]["directory"])}
    if _canonical(record) != _canonical(expected):
        raise ValueError("La captura de vigencia, las fuentes o el historial actual han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — comprobar vigencia sin reservar o enviar")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture")
    capture.add_argument("--request-run", type=Path, required=True)
    capture.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            print(json.dumps(verify_request_freshness(args.run), ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(capture_request_freshness(args.request_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Vigencia no verificable: {error}\n")


if __name__ == "__main__":
    main()
