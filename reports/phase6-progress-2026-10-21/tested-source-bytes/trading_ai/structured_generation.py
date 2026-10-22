"""Reserva exclusiva de un intento compacto; todavía no conecta o invoca modelos."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_draft_request import verify_draft_request
from trading_ai.structured_freshness import _code_hashes as _freshness_hashes, require_current_request


ACCESS_ROOT = ROOT / ".local/compact-generation-access"


class GenerationReservationError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _scope(directory: Path) -> tuple[dict, dict]:
    request = verify_draft_request(directory)
    payload = _strict_json(_read(directory / "request.json", 12288))
    context = _strict_json(payload["messages"][1]["content"])
    # Datos y par, sin rutas, parámetros de riesgo, criterio o nombre de carpeta:
    # esos cambios no conceden otro intento para este protocolo compacto.
    identity = {"schema_version": 1, "scope": "compact_new_idea",
                "development_sha256": request["reference"]["development_sha256"], "pair": context["controls"]["pair"]}
    return request, identity


def _path(identity: dict) -> Path:
    return ACCESS_ROOT.resolve() / (sha256(_canonical(identity)).hexdigest() + ".json")


def _code_hashes() -> dict:
    return {**_freshness_hashes(), "structured_generation.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _claim(identity: dict, directory: Path, request: dict, fingerprint: str) -> dict:
    return {"schema_version": 1, "identity": identity, "reservation_run": str(directory),
            "request_sha256": request["request_sha256"], "freshness_fingerprint": fingerprint}


def generation_budget_status(request_dir: str | Path) -> dict:
    _, identity = _scope(Path(request_dir).resolve())
    path = _path(identity)
    claim = None
    if path.exists():
        claim = _strict_json(_read(path, 8192))
        if (not isinstance(claim, dict) or set(claim) != {"schema_version", "identity", "reservation_run", "request_sha256", "freshness_fingerprint"}
                or type(claim["schema_version"]) is not int or claim["schema_version"] != 1
                or claim["identity"] != identity or not isinstance(claim["reservation_run"], str)
                or not Path(claim["reservation_run"]).is_absolute()
                or any(not isinstance(claim[key], str) or re.fullmatch(r"[0-9a-f]{64}", claim[key]) is None
                       for key in ("request_sha256", "freshness_fingerprint"))):
            raise ValueError("La reserva compacta es incompatible; no se considerará libre.")
    return {"identity": identity, "consumed": claim is not None,
            "reservation_run": None if claim is None else claim["reservation_run"],
            "scope": "compact_generation_only_not_legacy_revision_budget",
            "transport_enabled": False, "generation_ready": False, "executable": False}


def _record(directory: Path, request_dir: Path) -> dict:
    request, identity = _scope(request_dir)
    snapshot_raw = _read(directory / "freshness.json", 65536)
    snapshot = _strict_json(snapshot_raw)
    if (snapshot["status"] != "current" or snapshot["request"]["directory"] != str(request_dir)
            or snapshot["request"]["payload_sha256"] != request["request_sha256"]
            or snapshot["code_sha256"] != _freshness_hashes()
            or snapshot["fingerprint"] != sha256(_canonical({key: value for key, value in snapshot.items() if key != "fingerprint"})).hexdigest()):
        raise ValueError("La captura previa de vigencia no corresponde a esta reserva.")
    if snapshot["request"]["sha256"] != {name: sha256(_read(request_dir / name, 2 * 1024 * 1024)).hexdigest()
                                        for name in ("preview.json", "preview.json.sha256", "request.json", "events.jsonl")}:
        raise ValueError("Los archivos de la petición cambiaron después de comprobar su vigencia.")
    raw = _read(_path(identity), 8192)
    if _strict_json(raw) != _claim(identity, directory, request, snapshot["fingerprint"]):
        raise ValueError("La reserva exclusiva no corresponde a este intento.")
    return {"schema_version": 1, "protocol": "compact_generation_reservation_v1", "status": "reserved_not_submitted",
            "run_dir": str(directory), "identity": identity,
            "request": snapshot["request"], "freshness_fingerprint": snapshot["fingerprint"],
            "freshness_sha256": sha256(snapshot_raw).hexdigest(),
            "access": {"path": str(_path(identity)), "sha256": sha256(raw).hexdigest()},
            "budget": {"model_requests": 1, "automatic_retries": 0, "backtests": 0},
            "reserved_model_requests": 1, "provider_context_fit_verified": False, "transport_enabled": False,
            "generation_ready": False, "submitted": False, "executable": False,
            "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
            "code_sha256": _code_hashes()}


def reserve_compact_generation(request_dir: str | Path, *,
                                output_dir: str | Path = ROOT / ".local/compact-generations") -> Path:
    """API interna para un futuro controlador; no hay CLI de reserva o de envío."""
    request_dir = Path(request_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("compact_generation_reservation_started", request_dir=str(request_dir))
    try:
        before = require_current_request(request_dir)
        request, identity = _scope(request_dir)
        journal.save("freshness.json", before)
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            _write_exclusive(_path(identity), _canonical(_claim(identity, journal.directory, request, before["fingerprint"])))
        except FileExistsError as error:
            raise ValueError("El intento compacto de estos datos y par ya está consumido; no se reiniciará.") from error
        journal.record("compact_generation_attempt_reserved", claim_path=str(_path(identity)), model_requests_reserved=1,
                       new_model_requests=0, new_api_cost_usd="0")
        # La reserva del contador es exclusiva; la vigencia sigue siendo optimista
        # porque los escritores históricos no participan en una transacción común.
        require_current_request(request_dir, expected_fingerprint=before["fingerprint"])
        record = _record(journal.directory, request_dir)
        _seal(journal, "reservation.json", record, "compact_generation_reservation_completed")
    except Exception as error:
        journal.record("compact_generation_reservation_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        # Nunca borrar la reserva: un fallo después de crearla conserva el intento.
        raise GenerationReservationError(str(error), journal.directory) from error
    return journal.directory


def verify_generation_reservation(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "reservation.json", "compact_generation_reservation_completed")
    if _canonical(record) != _canonical(_record(directory, Path(record["request"]["directory"]))):
        raise ValueError("La reserva, petición, captura, código o ubicación han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — inspección de presupuesto compacto sin reservar o enviar")
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status")
    status.add_argument("--request-run", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = generation_budget_status(args.request_run) if args.command == "status" else verify_generation_reservation(args.run)
        print(json.dumps(result, ensure_ascii=True))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Reserva no verificable: {error}\n")


if __name__ == "__main__":
    main()
