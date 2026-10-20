"""Captura duradera por reserva: peticiones, respuestas, errores y consumo, sin enviar."""

import argparse
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import os
from pathlib import Path

from trading_ai import campaign_ledger as ledger
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _canonical, _seal


ACCESS_ROOT = ROOT / ".local/campaign-attempt-access"
ATTEMPTS_ROOT = ROOT / ".local/campaign-attempts"
MAX_OBSERVATION_BYTES = 256 * 1024
ZERO_USAGE = {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0"}


def _code_hashes():
    return {**ledger._code_hashes(), "campaign_attempts.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _reserved(scope_id, request_sha256):
    ledger._identifier(request_sha256)
    state = ledger.inspect_campaign(scope_id)
    for receipt in state.get("reservations", []):
        if receipt["kind"] == "proposal" and receipt["operation_id"] == request_sha256:
            return state, receipt
    raise ValueError("No hay una reserva de propuesta correspondiente; no se creará otra.")


def _access(receipt):
    return ACCESS_ROOT.resolve() / (receipt["receipt_id"] + ".json")


def _claim(directory, receipt):
    return {"schema_version": 1, "directory": str(directory), "receipt": receipt, "code_sha256": _code_hashes()}


def _directory(receipt):
    claim = _strict_json(_read(_access(receipt), 65536))
    directory = Path(claim["directory"])
    if (not directory.is_absolute() or directory.resolve().parent != ATTEMPTS_ROOT.resolve()
            or claim != _claim(directory, receipt)):
        raise ValueError("La reserva de captura, su ruta o código han cambiado.")
    return directory


def _event(directory, event, **data):
    entry = {"schema_version": 1, "at": datetime.now(UTC).isoformat(), "event": event, "data": data}
    with (directory / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _save(directory, name, record, event):
    raw = json.dumps(record, ensure_ascii=True, allow_nan=False, indent=2).encode("ascii") + b"\n"
    _write_exclusive(directory / name, raw)
    digest = sha256(raw).hexdigest()
    _write_exclusive(directory / (name + ".sha256"), (digest + "\n").encode("ascii"))
    _event(directory, event, sha256=digest, executable=False)


def _sealed(directory, name):
    raw = _read(directory / name, 131072)
    digest = sha256(raw).hexdigest()
    if _read(directory / (name + ".sha256"), 128) != (digest + "\n").encode("ascii"):
        raise ValueError("Una captura no conserva su huella.")
    record = _strict_json(raw)
    if not isinstance(record, dict): raise ValueError("Se requiere un registro de captura completo.")
    return record, digest


@contextmanager
def _transition(directory):
    lock = directory / "transition.lock"
    try: lock.mkdir()
    except FileExistsError as error:
        raise ValueError("Captura ocupada o interrumpida; no se repetirá automáticamente.") from error
    try: yield
    finally: lock.rmdir()


def _usage(raw, intent, policy):
    values = {key: None for key in ZERO_USAGE}
    issues = []
    try: source = _strict_json(raw)
    except (ValueError, UnicodeError, RecursionError):
        return {"usage": values, "accounting_complete": False, "requires_stop": True,
                "issues": ["unreadable_observation"], "observation_origin": "caller_supplied_not_transport_proof"}
    if not isinstance(source, dict):
        return {"usage": values, "accounting_complete": False, "requires_stop": True,
                "issues": ["observation_must_be_object"], "observation_origin": "caller_supplied_not_transport_proof"}
    required = {"model_request_attempted", "content", "model", "usage", "error"}
    if not required.issubset(source) or set(source) - required - {"provider_response"}:
        issues.append("unexpected_observation_fields")
    attempted, reported = source.get("model_request_attempted"), source.get("usage")
    if type(attempted) is bool: values["model_requests"] = int(attempted)
    else: issues.append("model_request_count_unknown")
    if attempted is True and not intent: issues.append("missing_submission_intent")
    if source.get("content") is not None and not isinstance(source["content"], str): issues.append("invalid_content_type")
    if source.get("model") is not None and not isinstance(source["model"], str): issues.append("invalid_model_type")
    error = source.get("error")
    if error is not None and (not isinstance(error, dict) or set(error) != {"type", "message"}
                              or any(not isinstance(error[key], str) for key in ("type", "message"))):
        issues.append("invalid_error_declaration")
    if attempted is False and reported is None and source.get("content") is None and error is not None:
        values = dict(ZERO_USAGE)
    else:
        if not isinstance(reported, dict):
            issues.append("usage_unknown")
        else:
            for key in ("input_tokens", "output_tokens"):
                value = reported.get(key)
                if type(value) is int and value >= 0: values[key] = value
                else: issues.append(key + "_unknown_or_invalid")
            cost = reported.get("api_cost_usd")
            try:
                parsed = Decimal(cost) if isinstance(cost, str) and len(cost) <= 64 else Decimal("NaN")
                if not parsed.is_finite() or parsed < 0: raise InvalidOperation
                if parsed != 0 and not -12 <= parsed.adjusted() <= 12: raise InvalidOperation
                values["api_cost_usd"] = "0" if parsed == 0 else format(parsed, "f")
                if parsed != 0: issues.append("unexpected_paid_usage")
            except (InvalidOperation, ValueError): issues.append("api_cost_unknown_or_invalid")
        if attempted is False and (source.get("content") is not None
                or any(values[key] not in (0, "0") for key in ("input_tokens", "output_tokens", "api_cost_usd"))):
            values["model_requests"] = None
            issues.append("contradictory_no_call_declaration")
    if values["output_tokens"] is not None and values["output_tokens"] > policy["max_output_tokens"]:
        issues.append("output_token_limit_exceeded")
    if (values["input_tokens"] is not None and values["output_tokens"] is not None
            and values["input_tokens"] + values["output_tokens"] > policy["max_context_tokens"]):
        issues.append("context_token_limit_exceeded")
    complete = not issues and all(value is not None for value in values.values())
    return {"usage": values, "accounting_complete": complete, "requires_stop": not complete,
            "issues": issues, "observation_origin": "caller_supplied_not_transport_proof"}


def _load(state, receipt, *, held_lock=False):
    directory = _directory(receipt)
    if not held_lock and (directory / "transition.lock").exists():
        raise ValueError("Captura ocupada o interrumpida; no se considera completa.")
    header, header_sha = _sealed(directory, "attempt.json")
    expected = {"schema_version": 1, "protocol": "campaign_attempt_v1", "status": "prepared_not_submitted",
                "run_dir": str(directory), "receipt": receipt, "claim_sha256": sha256(_read(_access(receipt), 65536)).hexdigest(),
                "request_sha256": receipt["operation_id"], "request_validation": "not_performed_by_recorder",
                "code_sha256": _code_hashes(), "execution_authorized": False}
    if (header != expected or sha256(_read(directory / "request.json", 12288)).hexdigest() != receipt["operation_id"]):
        raise ValueError("La captura, petición, reserva o código han cambiado.")
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 65536).splitlines()]
    for event in events:
        if (not isinstance(event, dict) or set(event) != {"schema_version", "at", "event", "data"}
                or type(event["schema_version"]) is not int or event["schema_version"] != 1
                or not isinstance(event["at"], str) or not isinstance(event["data"], dict)):
            raise ValueError("Evento de captura incompatible.")
        at = datetime.fromisoformat(event["at"])
        if at.tzinfo is None or at.utcoffset().total_seconds() != 0:
            raise ValueError("El evento debe conservar una fecha UTC explícita.")
    names = [item["event"] for item in events]
    if names[:2] != ["campaign_attempt_started", "campaign_attempt_prepared"]:
        raise ValueError("El intento no conserva su preparación completa.")
    if (events[0]["data"] != {"scope_id": receipt["scope_id"], "receipt_id": receipt["receipt_id"]}
            or events[1]["data"] != {"sha256": header_sha, "status": "prepared_not_submitted", "executable": False}):
        raise ValueError("La preparación no corresponde al intento.")
    tail = names[2:]
    if tail not in ([], ["campaign_submission_intent"], ["campaign_observation_recorded"],
                    ["campaign_submission_intent", "campaign_observation_recorded"]):
        raise ValueError("Transiciones de captura incompletas o incompatibles.")
    intent, intent_sha = None, None
    if "campaign_submission_intent" in tail:
        intent, intent_sha = _sealed(directory, "submission.json")
        if (set(intent) != {"schema_version", "protocol", "attempt_sha256", "receipt_id", "at", "execution_authorized"}
                or intent["schema_version"] != 1 or intent["protocol"] != "campaign_submission_intent_v1"
                or intent["attempt_sha256"] != header_sha or intent["receipt_id"] != receipt["receipt_id"]
                or intent["execution_authorized"] is not False
                or events[2]["data"] != {"sha256": intent_sha, "executable": False}):
            raise ValueError("El marcador de envío no corresponde al intento.")
    elif (directory / "submission.json").exists() or (directory / "submission.json.sha256").exists():
        raise ValueError("Marcador de envío interrumpido; no se repetirá.")
    completion = None
    if "campaign_observation_recorded" in tail:
        completion, digest = _sealed(directory, "completion.json")
        raw = _read(directory / "observation.raw", MAX_OBSERVATION_BYTES)
        expected = _completion(directory, header_sha, intent_sha, raw, state)
        if completion != expected or events[-1]["data"] != {"sha256": digest, "executable": False}:
            raise ValueError("La observación, análisis o cierre han cambiado.")
    elif any((directory / name).exists() for name in ("completion.json", "completion.json.sha256", "observation.raw")):
        raise ValueError("Observación parcial conservada; no se reconstruirá su cierre.")
    return directory, header_sha, intent_sha, completion


def _completion(directory, header_sha, intent_sha, raw, state):
    return {"schema_version": 1, "protocol": "campaign_observation_v1", "status": "observation_recorded",
            "run_dir": str(directory), "attempt_sha256": header_sha, "submission_sha256": intent_sha,
            "observation_sha256": sha256(raw).hexdigest(), "observation_bytes": len(raw),
            "analysis": _usage(raw, intent_sha is not None, state["registration"]["terms"]["provider_policy"]),
            "proposal_validation": "not_performed", "calculated_results": None, "execution_authorized": False,
            "code_sha256": _code_hashes(), "new_usage_of_recording": dict(ZERO_USAGE)}


def prepare_attempt(scope_id: str, request: bytes) -> Path:
    if not isinstance(request, bytes) or len(request) > 12288: raise ValueError("Petición de captura inválida o demasiado grande.")
    request_sha = sha256(request).hexdigest()
    state, receipt = _reserved(scope_id, request_sha)
    if _access(receipt).exists(): return _load(state, receipt)[0]
    journal = RunJournal(ATTEMPTS_ROOT.resolve())
    journal.record("campaign_attempt_started", scope_id=scope_id, receipt_id=receipt["receipt_id"])
    try:
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        try: _write_exclusive(_access(receipt), _canonical(_claim(journal.directory, receipt)))
        except FileExistsError:
            journal.record("campaign_attempt_not_owner", receipt_id=receipt["receipt_id"])
            return _load(state, receipt)[0]
        _write_exclusive(journal.directory / "request.json", request)
        record = {"schema_version": 1, "protocol": "campaign_attempt_v1", "status": "prepared_not_submitted",
                  "run_dir": str(journal.directory), "receipt": receipt,
                  "claim_sha256": sha256(_read(_access(receipt), 65536)).hexdigest(), "request_sha256": request_sha,
                  "request_validation": "not_performed_by_recorder", "code_sha256": _code_hashes(), "execution_authorized": False}
        _seal(journal, "attempt.json", record, "campaign_attempt_prepared")
    except Exception as error:
        journal.record("campaign_attempt_prepare_failed", error_type=type(error).__name__, message=str(error)[:1000])
        raise
    return journal.directory


def mark_submission_intent(scope_id: str, request_sha256: str) -> Path:
    state, receipt = _reserved(scope_id, request_sha256)
    directory, header_sha, intent, completion = _load(state, receipt)
    with _transition(directory):
        current, header_sha, intent, completion = _load(state, receipt, held_lock=True)
        if current != directory: raise ValueError("La reserva de captura cambió durante la transición.")
        # El marcador es exclusivo incluso si el llamador repite o cae después de escribirlo.
        if intent is not None or completion is not None or (directory / "submission.json").exists():
            raise ValueError("El intento ya tiene envío declarado o cierre; no autoriza otro envío.")
        _save(directory, "submission.json", {"schema_version": 1, "protocol": "campaign_submission_intent_v1",
              "attempt_sha256": header_sha, "receipt_id": receipt["receipt_id"], "at": datetime.now(UTC).isoformat(),
              "execution_authorized": False}, "campaign_submission_intent")
    return directory


def record_observation(scope_id: str, request_sha256: str, raw: bytes) -> dict:
    if not isinstance(raw, bytes) or len(raw) > MAX_OBSERVATION_BYTES:
        raise ValueError("Observación demasiado grande o inválida; no se recortará.")
    state, receipt = _reserved(scope_id, request_sha256)
    directory, header_sha, intent_sha, completion = _load(state, receipt)
    with _transition(directory):
        current, header_sha, intent_sha, completion = _load(state, receipt, held_lock=True)
        if current != directory: raise ValueError("La reserva de captura cambió durante la transición.")
        if completion is not None:
            if _read(directory / "observation.raw", MAX_OBSERVATION_BYTES) != raw:
                raise ValueError("Ya hay otra observación; no se sobrescribirá.")
            return completion
        # La fuente se sincroniza a disco antes de analizar JSON, reglas o consumo.
        _write_exclusive(directory / "observation.raw", raw)
        completion = _completion(directory, header_sha, intent_sha, raw, state)
        _save(directory, "completion.json", completion, "campaign_observation_recorded")
    return completion


def inspect_attempts(scope_id: str) -> dict:
    state = ledger.inspect_campaign(scope_id)
    if state["status"] != "registered_inactive": raise ValueError("El ámbito no está registrado.")
    attempts, totals = [], dict(ZERO_USAGE)
    known = dict(ZERO_USAGE)
    blocked = False
    for receipt in state["reservations"]:
        if receipt["kind"] != "proposal": continue
        usage = {key: None for key in ZERO_USAGE}
        item = {"receipt_id": receipt["receipt_id"], "request_sha256": receipt["operation_id"]}
        try:
            directory, _, intent, completion = _load(state, receipt)
            item.update(run_dir=str(directory), status="submission_unresolved" if intent else "prepared_unresolved")
            if completion is not None:
                item.update(status="observation_recorded", analysis=completion["analysis"])
                usage = completion["analysis"]["usage"]
                blocked |= completion["analysis"]["requires_stop"]
            else: blocked = True
        except (ValueError, OSError, KeyError, TypeError, IndexError, RecursionError) as error:
            item.update(status="unverifiable_or_missing_capture", error=str(error))
            blocked = True
        item["usage"] = usage
        attempts.append(item)
        for key, value in usage.items():
            if value is None: totals[key] = None
            elif key == "api_cost_usd":
                with localcontext() as context:
                    context.prec = 64
                    known[key] = format(Decimal(known[key]) + Decimal(value), "f")
                    if totals[key] is not None: totals[key] = format(Decimal(totals[key]) + Decimal(value), "f")
            else:
                known[key] += value
                if totals[key] is not None: totals[key] += value
    return {"schema_version": 1, "protocol": "campaign_attempt_summary_v1", "scope_id": scope_id,
            "attempts": attempts, "usage": totals, "known_subtotals": known, "requires_stop": blocked,
            "scope": "recorded_campaign_proposal_observations_only", "inherited_usage": state["registration"]["inherited_usage"],
            "execution_authorized": False, "calculated_results": None, "new_usage_of_query": dict(ZERO_USAGE)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Trading AI — consultar capturas de intentos sin ejecutar herramientas")
    parser.add_argument("--scope", required=True)
    args = parser.parse_args(argv)
    try: print(json.dumps(inspect_attempts(args.scope), ensure_ascii=True))
    except (ValueError, OSError, KeyError, TypeError, IndexError, RecursionError) as error:
        parser.exit(1, f"Intentos no verificables: {error}\n")


if __name__ == "__main__": main()
