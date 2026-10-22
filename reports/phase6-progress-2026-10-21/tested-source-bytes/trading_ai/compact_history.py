"""Memoria de intentos compactos: estados y uso de origen, sin resultados financieros."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from trading_ai.ai import AIConfig
from trading_ai.compact_candidate import _check_provider, _code_hashes as _candidate_hashes, verify_compact_candidate
from trading_ai.compact_review import _access as _review_access, _code_hashes as _review_hashes, verify_compact_review
from trading_ai.formalization import _read, _strict_json
from trading_ai.research import ROOT, RunJournal, _api_cost
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_generation import _scope, verify_generation_reservation
from trading_ai import structured_generation as generation


MAX_CLAIMS = 128
UNKNOWN_USAGE = {"model_requests": None, "input_tokens": None, "output_tokens": None, "api_cost_usd": None}
SNAPSHOT_FILES = {"events.jsonl", "reservation.json", "reservation.json.sha256", "freshness.json", "actions/submit.json",
                  "job.json", "job.sha256", "candidate.json", "candidate.json.sha256", "report.md", "assessment.json",
                  "review.json", "review.json.sha256"}


def _code_hashes() -> dict:
    return {**_candidate_hashes(), **_review_hashes(), "compact_history.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _claims(identity: dict) -> list[dict]:
    paths = sorted(generation.ACCESS_ROOT.glob("*.json"))
    if len(paths) > MAX_CLAIMS: raise ValueError("Demasiadas reservas compactas; no se omitirán entradas.")
    claims = []
    for path in paths:
        raw = _read(path, 8192)
        claim = _strict_json(raw)
        if (not isinstance(claim, dict) or set(claim) != {"schema_version", "identity", "reservation_run", "request_sha256", "freshness_fingerprint"}
                or type(claim["schema_version"]) is not int or claim["schema_version"] != 1
                or not isinstance(claim["identity"], dict) or set(claim["identity"]) != set(identity)
                or type(claim["identity"].get("schema_version")) is not int or claim["identity"].get("schema_version") != 1
                or claim["identity"].get("scope") != "compact_new_idea"
                or not isinstance(claim["identity"].get("development_sha256"), str)
                or re.fullmatch(r"[0-9a-f]{64}", claim["identity"]["development_sha256"]) is None
                or claim["identity"].get("pair") not in ("EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF")
                or not isinstance(claim["reservation_run"], str) or not Path(claim["reservation_run"]).is_absolute()
                or path.stem != sha256(_canonical(claim["identity"])).hexdigest()
                or any(not isinstance(claim[key], str) or re.fullmatch(r"[0-9a-f]{64}", claim[key]) is None
                       for key in ("request_sha256", "freshness_fingerprint"))):
            raise ValueError("Reserva compacta incompatible; no se considerará ausente o libre.")
        if claim["identity"] == identity:
            claims.append({"path": str(path.resolve()), "sha256": sha256(raw).hexdigest(), "claim": claim})
    return claims


def _snapshot(directory: Path) -> dict:
    paths = sorted(path for path in directory.rglob("*") if path.is_file())
    names = tuple(path.relative_to(directory).as_posix() for path in paths)
    if len(paths) > 24 or set(names) - SNAPSHOT_FILES:
        raise ValueError("Directorio compacto con archivos ajenos al contrato; no se leerán resultados.")
    return {"directory_exists": directory.is_dir(), **_origin(directory, names)}


def _failure_usage(failure: dict) -> dict:
    calls, usages, metadata = failure["model_requests"], failure["usage"], failure["metadata_request_attempts"]
    if (type(calls) is not int or calls not in (0, 1) or not isinstance(usages, list) or len(usages) > 1
            or type(metadata) is not int or not 0 <= metadata <= 6
            or any(not isinstance(usage, dict) or any(usage.get(key) is not None
                       and (type(usage[key]) is not int or usage[key] < 0) for key in ("input_tokens", "output_tokens")) for usage in usages)
            or failure["api_cost_usd"] != (_api_cost(usages) if calls else "0")):
        raise ValueError("El consumo registrado del fallo compacto es incompatible con sus límites.")
    return {key: failure[key] for key in ("model_requests", "usage", "api_cost_usd", "metadata_request_attempts")}


def _entry(item: dict) -> dict:
    path = Path(item["path"])
    raw = _read(path, 8192)
    if sha256(raw).hexdigest() != item["sha256"] or _strict_json(raw) != item["claim"]:
        raise ValueError("La reserva capturada cambió.")
    directory = Path(item["claim"]["reservation_run"])
    entry = {"generation_claim": item, "budget_consumed": True, "reservation": _snapshot(directory),
             "status": "reservation_unfinished", "source_usage": dict(UNKNOWN_USAGE),
             "candidate": None, "rules": None, "review": None, "grants_plan_permission": False}
    if not (directory / "reservation.json").exists(): return entry
    reservation = verify_generation_reservation(directory)
    if reservation["access"]["path"] != str(path) or reservation["access"]["sha256"] != item["sha256"]:
        raise ValueError("La reserva verificada no corresponde a su marca compartida.")
    entry["status"] = "reserved_without_submission"
    submit_path = directory / "actions/submit.json"
    if not submit_path.exists(): return entry
    submit = _strict_json(_read(submit_path, 8192))
    if (not isinstance(submit, dict) or set(submit) != {"candidate_dir", "job_sha256"}
            or not isinstance(submit["candidate_dir"], str) or not Path(submit["candidate_dir"]).is_absolute()):
        raise ValueError("Marca de envío compacta inválida.")
    candidate_dir = Path(submit["candidate_dir"])
    job_raw = _read(candidate_dir / "job.json", 65536)
    job = _strict_json(job_raw)
    if (sha256(job_raw).hexdigest() != submit["job_sha256"]
            or _read(candidate_dir / "job.sha256", 128).decode("ascii").strip() != submit["job_sha256"]
            or job["schema_version"] != 1 or job["protocol"] != "compact_candidate_job_v1" or job["run_dir"] != str(candidate_dir)
            or job["code_sha256"] != _candidate_hashes()
            or job["reservation"] != _origin(directory, ("reservation.json", "reservation.json.sha256", "freshness.json", "events.jsonl"))
            or job["request"]["directory"] != reservation["request"]["directory"]
            or job["request"] != _origin(Path(reservation["request"]["directory"]), ("preview.json", "preview.json.sha256", "request.json", "events.jsonl"))):
        raise ValueError("El trabajo compacto no corresponde al envío o a su código.")
    _check_provider(AIConfig(**job["ai_config"]), job["provider"])
    entry["candidate"] = _snapshot(candidate_dir)
    entry["status"] = "submission_unfinished"
    if (candidate_dir / "candidate.json").exists():
        candidate = verify_compact_candidate(candidate_dir)
        entry["status"] = candidate["status"]
        entry["source_usage"] = {"model_requests": candidate["model_requests"], "usage": candidate["usage"],
                                  "api_cost_usd": candidate["api_cost_usd"], "metadata_request_attempts": candidate["metadata_request_attempts"]}
        entry["rules"] = {"draft": candidate["draft"], "spec_sha256": candidate["spec_sha256"],
                           "description": candidate["rule_description"], "duplicate_of": candidate["duplicate_of"]}
        _, review_path = _review_access(candidate)
        if candidate["status"] == "pending_technical_review" and review_path.exists():
            review_claim = _strict_json(_read(review_path, 8192))
            if (not isinstance(review_claim, dict) or set(review_claim) != {"schema_version", "identity", "review_dir", "candidate_sha256"}
                    or type(review_claim["schema_version"]) is not int or review_claim["schema_version"] != 1
                    or review_claim["identity"] != {"reference": candidate["reference"], "spec_sha256": candidate["spec_sha256"]}
                    or review_claim["candidate_sha256"] != entry["candidate"]["sha256"]["candidate.json"]
                    or not isinstance(review_claim["review_dir"], str) or not Path(review_claim["review_dir"]).is_absolute()):
                raise ValueError("La marca de revisión compacta es incompatible con su candidata.")
            review_dir = Path(review_claim["review_dir"])
            review_info = {"claim": {"path": str(review_path), "sha256": sha256(_read(review_path, 8192)).hexdigest()},
                           "source": _snapshot(review_dir), "status": "review_attempt_unfinished", "reviewer_declaration": None,
                           "reported_eligible_for_plan": None}
            if (review_dir / "review.json").exists():
                review = verify_compact_review(review_dir)
                review_info.update(status=review["status"], reviewer_declaration=review["assessment"], reported_eligible_for_plan=review["eligible_for_plan"])
            entry["review"] = review_info
    else:
        events = [_strict_json(line) for line in _read(candidate_dir / "events.jsonl", 2 * 1024 * 1024).splitlines()]
        if any(event["event"] == "compact_candidate_completed" for event in events):
            raise ValueError("Falta el archivo de una candidata declarada completa; no es un intento pendiente.")
        if events and events[-1]["event"] == "compact_candidate_failed":
            failure = events[-1]["data"]
            entry["status"] = "failed_preserved"
            entry["source_usage"] = _failure_usage(failure)
            entry["unverified_failure_reason"] = failure["message"]
    return entry


def _record(request_dir: Path, directory: Path, claims: list[dict]) -> dict:
    request, identity = _scope(request_dir)
    return {"schema_version": 1, "protocol": "compact_history_v1", "status": "memory_only",
            "run_dir": str(directory), "request": _origin(request_dir, ("preview.json", "preview.json.sha256", "request.json", "events.jsonl")),
            "reference": request["reference"], "identity": identity, "entries": [_entry(item) for item in claims],
            "coverage": "matching_generation_claims_at_capture_only", "future_attempts_included": False,
            "compact_execution_results_read": False, "executable": False, "eligible_for_plan": False,
            "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
            "code_sha256": _code_hashes()}


def capture_compact_history(request_dir: str | Path, *, output_dir: str | Path = ROOT / ".local/compact-history") -> Path:
    request_dir = Path(request_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("compact_history_started", request_dir=str(request_dir))
    try:
        _, identity = _scope(request_dir)
        claims = _claims(identity)
        record = _record(request_dir, journal.directory, claims)
        if claims != _claims(identity) or _canonical(record) != _canonical(_record(request_dir, journal.directory, claims)):
            raise ValueError("El historial compacto cambió durante su captura.")
        _seal(journal, "history.json", record, "compact_history_completed")
    except Exception as error:
        journal.record("compact_history_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise ValueError(f"Memoria compacta detenida: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_compact_history(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "history.json", "compact_history_completed")
    request_dir = Path(record["request"]["directory"])
    _, identity = _scope(request_dir)
    expected = _record(request_dir, directory, _claims(identity))
    if _canonical(record) != _canonical(expected):
        raise ValueError("La memoria, los estados capturados, las fuentes o el código han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — memoria compacta sin modelos o cálculos")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture")
    capture.add_argument("--request-run", type=Path, required=True)
    capture.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_compact_history(args.run), ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(capture_compact_history(args.request_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Memoria no verificable: {error}\n")


if __name__ == "__main__":
    main()
