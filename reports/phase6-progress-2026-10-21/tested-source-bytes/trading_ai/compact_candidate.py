"""Una propuesta de reglas con origen local, reserva previa y revisión obligatoria; sin backtests."""

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import re

from trading_ai.ai import AIConfig, ProviderError
from trading_ai.compact_ollama import CompactOllamaProvider, SUPPORTED_SERVER_VERSION
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal, _api_cost
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_draft import describe_draft
from trading_ai.structured_draft_request import verify_draft_request
from trading_ai.structured_freshness import require_current_request
from trading_ai.structured_generation import (_code_hashes as _reservation_hashes, reserve_compact_generation,
                                            verify_generation_reservation)
from trading_ai import structured_ideas as ideas


class CompactCandidateError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_reservation_hashes(), **{name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                    for name in ("compact_ollama.py", "compact_candidate.py")}}


def _check_provider(config: AIConfig, identity: dict) -> None:
    digest = identity.get("model_digest") if isinstance(identity, dict) else None
    if not isinstance(digest, str) or re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", digest) is None:
        raise ValueError("El proveedor compacto carece de digest de modelo verificable.")
    expected = {**asdict(config), "model_digest": digest, "api_cost_usd": "0", "think": False, "temperature": 0,
                "server_version": SUPPORTED_SERVER_VERSION, "context_policy": "reject_overflow_no_truncate_no_shift",
                "truncate": False, "shift": False, "prompt_tokens_before_request": None}
    if identity != expected or config.provider != "ollama" or config.context_tokens > 4096 or config.output_tokens > 384 or config.gpu_layers != 0:
        raise ValueError("La identidad o los límites no corresponden al adaptador compacto local.")


def _submit_claim(reservation_dir: Path) -> Path:
    return reservation_dir / "actions/submit.json"


def _report(record: dict) -> bytes:
    return "\n".join([
        "# Candidata compacta — revisión pendiente", "", "Estado: " + record["status"], "",
        "La IA devolvió reglas. Las frases siguientes las deriva Python de esos campos, sin hipótesis atribuida al modelo.", "",
        record["rule_description"]["entry"], "", record["rule_description"]["exit"], "",
        record["rule_description"]["execution"], "", "Sin señales, backtests, aprobación o adopción en sesiones.", "",
    ]).encode("utf-8")


def _record(directory: Path) -> dict:
    raw = _read(directory / "job.json", 65536)
    job = _strict_json(raw)
    if (job["schema_version"] != 1 or job["protocol"] != "compact_candidate_job_v1"
            or type(job["preflight_metadata_requests"]) is not int or job["preflight_metadata_requests"] < 2
            or job["run_dir"] != str(directory) or job["code_sha256"] != _code_hashes()
            or _read(directory / "job.sha256", 128).decode("ascii").strip() != sha256(raw).hexdigest()):
        raise ValueError("El trabajo compacto cambió de contenido, código o ubicación.")
    config = AIConfig(**job["ai_config"])
    _check_provider(config, job["provider"])
    request_dir, reservation_dir = Path(job["request"]["directory"]), Path(job["reservation"]["directory"])
    request = verify_draft_request(request_dir)
    reservation = verify_generation_reservation(reservation_dir)
    request_origin = _origin(request_dir, ("preview.json", "preview.json.sha256", "request.json", "events.jsonl"))
    reservation_origin = _origin(reservation_dir, ("reservation.json", "reservation.json.sha256", "freshness.json", "events.jsonl"))
    if (job["request"] != request_origin or job["reservation"] != reservation_origin
            or reservation["request"]["directory"] != str(request_dir)
            or reservation["request"]["payload_sha256"] != request["request_sha256"]):
        raise ValueError("La reserva y petición no corresponden al trabajo compacto.")
    submit_raw = _read(_submit_claim(reservation_dir), 8192)
    if _strict_json(submit_raw) != {"candidate_dir": str(directory), "job_sha256": sha256(raw).hexdigest()}:
        raise ValueError("El envío no pertenece a la reserva exclusiva de este trabajo.")
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 2 * 1024 * 1024).splitlines()]
    requests = [item["data"] for item in events if item["event"] == "model_request"]
    replies = [item["data"] for item in events if item["event"] == "model_response"]
    payload = _strict_json(_read(request_dir / "request.json", 12288))
    if (len(requests) != 1 or requests[0] != payload or len(replies) != 1
            or any(item["event"] == "model_error" for item in events) or replies[0]["model"] != config.model):
        raise ValueError("La consulta o respuesta no coincide con el envío compacto registrado.")
    draft = _strict_json(replies[0]["content"])
    described = describe_draft(draft)
    usage = replies[0]["usage"]
    if (type(usage.get("input_tokens")) is not int or usage["input_tokens"] < 1
            or type(usage.get("output_tokens")) is not int or not 1 <= usage["output_tokens"] <= config.output_tokens
            or usage["input_tokens"] + usage["output_tokens"] > config.context_tokens or _api_cost([usage]) != "0"
            or type(usage.get("metadata_request_attempts")) is not int or usage["metadata_request_attempts"] < 4):
        raise ValueError("Consumo compacto incompleto o fuera de los límites locales.")
    identity = {"reference": request["reference"], "spec_sha256": described["spec_sha256"]}
    claim_path = ideas.ACCESS_ROOT / (sha256(_canonical(identity)).hexdigest() + ".json")
    claim_raw = _read(claim_path, 8192)
    claim = ideas._claim_value(claim_raw)
    if claim["identity"] != identity:
        raise ValueError("La reserva de reglas no corresponde a la candidata.")
    duplicate = claim["run_dir"] != str(directory)
    return {"schema_version": 1, "protocol": "compact_candidate_v1", "status": "duplicate_rules" if duplicate else "pending_technical_review",
            "run_dir": str(directory), "reference": request["reference"], "job_sha256": sha256(raw).hexdigest(),
            "request": job["request"], "reservation": job["reservation"], "submit_sha256": sha256(submit_raw).hexdigest(),
            "ai_config": asdict(config), "provider": job["provider"], "draft": draft,
            "spec": described["spec"], "spec_sha256": described["spec_sha256"], "rule_description": described["rule_description"],
            "model_description": None, "hypothesis_origin": "frozen_development_objective_not_model_prose",
            "duplicate_of": claim["run_dir"] if duplicate else None,
            "rule_access": {"path": str(claim_path), "sha256": sha256(claim_raw).hexdigest()},
            "usage": [usage], "api_cost_usd": _api_cost([usage]), "model_requests": 1, "backtests": 0,
            "metadata_request_attempts": job["preflight_metadata_requests"] + usage["metadata_request_attempts"],
            "executable": False, "calculated_results": None, "eligible_for_session": False,
            "scope": "known_development_history_only", "code_sha256": _code_hashes()}


def generate_compact_candidate(request_dir: str | Path, *, provider: CompactOllamaProvider | None = None,
                                output_dir: str | Path = ROOT / ".local/compact-candidates",
                                reservation_output_dir: str | Path = ROOT / ".local/compact-generations") -> Path:
    request_dir = Path(request_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("compact_candidate_started", request_dir=str(request_dir))
    calls, usages = 0, []
    metadata_start = getattr(provider, "metadata_requests", 0)
    try:
        provider = provider or CompactOllamaProvider()
        if not isinstance(provider, CompactOllamaProvider):
            raise ValueError("Solo se permite el adaptador compacto local comprobado.")
        identity = provider.describe()
        _check_provider(provider.config, identity)
        reservation_dir = reserve_compact_generation(request_dir, output_dir=reservation_output_dir)
        reserved = verify_generation_reservation(reservation_dir)
        job = {"schema_version": 1, "protocol": "compact_candidate_job_v1", "run_dir": str(journal.directory),
               "request": _origin(request_dir, ("preview.json", "preview.json.sha256", "request.json", "events.jsonl")),
               "reservation": _origin(reservation_dir, ("reservation.json", "reservation.json.sha256", "freshness.json", "events.jsonl")),
               "ai_config": asdict(provider.config), "provider": identity,
               "preflight_metadata_requests": provider.metadata_requests - metadata_start, "code_sha256": _code_hashes()}
        journal.save("job.json", job)
        job_sha = sha256(_read(journal.directory / "job.json", 65536)).hexdigest()
        _write_exclusive(journal.directory / "job.sha256", (job_sha + "\n").encode("ascii"))
        submit = _submit_claim(reservation_dir)
        submit.parent.mkdir(exist_ok=True)
        _write_exclusive(submit, _canonical({"candidate_dir": str(journal.directory), "job_sha256": job_sha}))
        require_current_request(request_dir, expected_fingerprint=reserved["freshness_fingerprint"])
        payload = _strict_json(_read(request_dir / "request.json", 12288))
        journal.record("model_request", **payload)
        try:
            reply = provider.complete(payload["messages"], payload["schema"])
        except ProviderError as error:
            calls = int(provider._model_attempted)
            if error.usage is not None: usages.append(error.usage)
            journal.record("model_error", usage=error.usage, provider_response=provider.last_response)
            raise
        calls = int(provider._model_attempted)
        usages.append(reply.usage)
        # Nunca reconstruir JSON ni prosa: guardar la respuesta antes de interpretarla.
        journal.record("model_response", model=reply.model, content=reply.content, usage=reply.usage)
        require_current_request(request_dir, expected_fingerprint=reserved["freshness_fingerprint"])
        draft = _strict_json(reply.content)
        described = describe_draft(draft)
        request = verify_draft_request(request_dir)
        rule_identity = {"reference": request["reference"], "spec_sha256": described["spec_sha256"]}
        claim_path = ideas.ACCESS_ROOT / (sha256(_canonical(rule_identity)).hexdigest() + ".json")
        ideas.ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            _write_exclusive(claim_path, _canonical({"schema_version": 1, "identity": rule_identity, "run_dir": str(journal.directory)}))
        except FileExistsError:
            existing = ideas._claim_value(_read(claim_path, 8192))
            if existing["identity"] != rule_identity:
                raise ValueError("Reserva previa de reglas incompatible; se conserva sin modificar.")
        record = _record(journal.directory)
        _write_exclusive(journal.directory / "report.md", _report(record))
        _seal(journal, "candidate.json", record, "compact_candidate_completed")
    except Exception as error:
        journal.record("compact_candidate_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       model_requests=calls, usage=usages, api_cost_usd=_api_cost(usages) if calls else "0",
                       backtests=0, metadata_request_attempts=getattr(provider, "metadata_requests", 0) - metadata_start)
        raise CompactCandidateError(str(error), journal.directory) from error
    return journal.directory


def verify_compact_candidate(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "candidate.json", "compact_candidate_completed")
    if (_canonical(record) != _canonical(_record(directory))
            or _read(directory / "report.md", 16384) != _report(record)):
        raise ValueError("La candidata, su reserva, fuentes, consumo o código han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — una candidata local, sin revisión o simulación automática")
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate")
    generate.add_argument("--request-run", type=Path, required=True)
    generate.add_argument("--output-dir", type=Path)
    generate.add_argument("--reservation-output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            print(json.dumps(verify_compact_candidate(args.run), ensure_ascii=True))
        else:
            kwargs = {key: value for key, value in (("output_dir", args.output_dir), ("reservation_output_dir", args.reservation_output_dir)) if value is not None}
            print(generate_compact_candidate(args.request_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Candidata no verificable: {error}\n")


if __name__ == "__main__":
    main()
