"""Capturas con datos artificiales; ninguna observación procede de una consulta real."""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import contextmanager
from hashlib import sha256
import json
import multiprocessing
from pathlib import Path

import pytest

from test_campaign_ledger import fake_guided, isolated_ledger, registered_ledger
from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_ledger as ledger


def observation(**changes):
    value = {"model_request_attempted": True, "content": '{"entry": "texto incompleto…',
             "model": "qwen3.5:4b", "usage": {"input_tokens": 100, "output_tokens": 17, "api_cost_usd": "0"},
             "error": None, "provider_response": {"done": True}}
    value.update(changes)
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


@pytest.fixture
def captures(registered_ledger, tmp_path, monkeypatch):
    monkeypatch.setattr(attempts, "ACCESS_ROOT", tmp_path / "capture-access")
    monkeypatch.setattr(attempts, "ATTEMPTS_ROOT", tmp_path / "captures")
    return registered_ledger[1]


def prepare(scope, suffix=b""):
    raw = b'{"request":"artificial"}' + suffix
    key = sha256(raw).hexdigest()
    ledger.reserve_proposal(scope, key)
    return key, attempts.prepare_attempt(scope, raw), raw


def test_no_reservations_returns_zero_without_writing_and_keeps_inherited_usage(captures):
    result = attempts.inspect_attempts(captures)
    assert result["usage"] == attempts.ZERO_USAGE and result["attempts"] == []
    assert result["requires_stop"] is result["execution_authorized"] is False
    assert result["inherited_usage"][0]["usage"][0]["input_tokens"] is None
    assert not attempts.ACCESS_ROOT.exists() and not attempts.ATTEMPTS_ROOT.exists()


def test_capture_preserves_original_content_before_any_proposal_validation(captures, monkeypatch):
    key, directory, request = prepare(captures)
    def forbidden(*args, **kwargs): pytest.fail("Capturar no puede enviar, reservar de nuevo o calcular.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.rule_execution._calculate", "trading_ai.structured_generation.reserve_compact_generation"):
        monkeypatch.setattr(name, forbidden)
    attempts.mark_submission_intent(captures, key)
    raw = observation()
    result = attempts.record_observation(captures, key, raw)
    assert (directory / "request.json").read_bytes() == request
    assert (directory / "observation.raw").read_bytes() == raw
    assert result["analysis"]["usage"] == {"model_requests": 1, "input_tokens": 100, "output_tokens": 17, "api_cost_usd": "0"}
    assert result["analysis"]["accounting_complete"] is True
    assert result["calculated_results"] is None and result["proposal_validation"] == "not_performed"
    assert result["execution_authorized"] is False and result["new_usage_of_recording"] == attempts.ZERO_USAGE
    summary = attempts.inspect_attempts(captures)
    assert summary["usage"]["model_requests"] == 1 and summary["requires_stop"] is False


def test_pending_or_missing_capture_is_unknown_and_never_frees_reservation(captures):
    raw = b"reserved-only"
    key = sha256(raw).hexdigest()
    ledger.reserve_proposal(captures, key)
    missing = attempts.inspect_attempts(captures)
    assert missing["requires_stop"] is True and missing["usage"]["model_requests"] is None
    directory = attempts.prepare_attempt(captures, raw)
    assert attempts.inspect_attempts(captures)["usage"]["api_cost_usd"] is None
    attempts.mark_submission_intent(captures, key)
    assert attempts.inspect_attempts(captures)["attempts"][0]["status"] == "submission_unresolved"
    with pytest.raises(ValueError): attempts.mark_submission_intent(captures, key)
    assert ledger.inspect_campaign(captures)["reserved_model_requests"] == 1
    assert directory.is_dir()


def test_explicit_preflight_error_records_zero_calls_without_releasing_slot(captures):
    key, _, _ = prepare(captures)
    raw = observation(model_request_attempted=False, content=None, usage=None,
                      error={"type": "PreflightError", "message": "Modelo no disponible; no se envió."})
    result = attempts.record_observation(captures, key, raw)
    assert result["analysis"]["accounting_complete"] is True and result["analysis"]["usage"] == attempts.ZERO_USAGE
    with pytest.raises(ValueError): attempts.mark_submission_intent(captures, key)
    assert ledger.inspect_campaign(captures)["reserved_model_requests"] == 1


def test_provider_error_keeps_unknown_usage_unknown(captures):
    key, directory, _ = prepare(captures)
    attempts.mark_submission_intent(captures, key)
    raw = observation(content=None, usage=None, error={"type": "TimeoutError", "message": "Tiempo agotado."})
    result = attempts.record_observation(captures, key, raw)
    assert (directory / "observation.raw").read_bytes() == raw
    assert result["analysis"]["usage"]["model_requests"] == 1
    assert result["analysis"]["usage"]["input_tokens"] is result["analysis"]["usage"]["api_cost_usd"] is None
    assert result["analysis"]["requires_stop"] is True


@pytest.mark.parametrize("invalid", [True, -1, 1.5, None])
def test_invalid_token_count_is_preserved_but_not_replaced_by_zero(captures, invalid):
    key, directory, _ = prepare(captures)
    attempts.mark_submission_intent(captures, key)
    raw = observation(usage={"input_tokens": invalid, "output_tokens": 17, "api_cost_usd": "0"})
    result = attempts.record_observation(captures, key, raw)
    assert result["analysis"]["usage"]["input_tokens"] is None and result["analysis"]["requires_stop"] is True
    assert result["analysis"]["usage"]["output_tokens"] == 17
    assert (directory / "observation.raw").read_bytes() == raw


@pytest.mark.parametrize("raw", [b"", b"not JSON", b"\xff", b"[]", b'{"usage":NaN}', b'{"x":1,"x":2}'])
def test_malformed_observation_is_saved_exactly_and_blocks_accounting(captures, raw):
    key, directory, _ = prepare(captures)
    attempts.mark_submission_intent(captures, key)
    result = attempts.record_observation(captures, key, raw)
    assert (directory / "observation.raw").read_bytes() == raw
    assert result["analysis"]["requires_stop"] is True
    assert all(value is None for value in result["analysis"]["usage"].values())


@pytest.mark.parametrize("usage,issue", [
    ({"input_tokens": 100, "output_tokens": 385, "api_cost_usd": "0"}, "output_token_limit_exceeded"),
    ({"input_tokens": 4090, "output_tokens": 17, "api_cost_usd": "0"}, "context_token_limit_exceeded"),
    ({"input_tokens": 100, "output_tokens": 17, "api_cost_usd": "0.25"}, "unexpected_paid_usage"),
    ({"input_tokens": 100, "output_tokens": 17, "api_cost_usd": "1e999999999"}, "api_cost_unknown_or_invalid")])
def test_out_of_policy_usage_is_captured_without_authorizing_continuation(captures, usage, issue):
    key, directory, _ = prepare(captures)
    attempts.mark_submission_intent(captures, key)
    raw = observation(usage=usage)
    result = attempts.record_observation(captures, key, raw)
    assert issue in result["analysis"]["issues"] and result["analysis"]["requires_stop"] is True
    assert (directory / "observation.raw").read_bytes() == raw


def test_observation_is_idempotent_but_cannot_be_replaced_or_resubmitted(captures):
    key, directory, request = prepare(captures)
    attempts.mark_submission_intent(captures, key)
    raw = observation()
    result = attempts.record_observation(captures, key, raw)
    before = {p: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    assert attempts.record_observation(captures, key, raw) == result
    assert attempts.prepare_attempt(captures, request) == directory
    with pytest.raises(ValueError): attempts.record_observation(captures, key, observation(content="otra respuesta"))
    with pytest.raises(ValueError): attempts.mark_submission_intent(captures, key)
    assert all(p.read_bytes() == content for p, content in before.items())


def test_call_without_marker_or_contradictory_no_call_is_not_silently_accepted(captures):
    key, _, _ = prepare(captures)
    result = attempts.record_observation(captures, key, observation())
    assert "missing_submission_intent" in result["analysis"]["issues"]
    second, _, _ = prepare(captures, b" ")
    result = attempts.record_observation(captures, second, observation(model_request_attempted=False))
    assert result["analysis"]["usage"]["model_requests"] is None
    assert "contradictory_no_call_declaration" in result["analysis"]["issues"]


@pytest.mark.parametrize("filename", ["request.json", "attempt.json", "attempt.json.sha256", "submission.json",
                                      "completion.json", "observation.raw", "events.jsonl"])
def test_changed_capture_is_reported_as_blocked_not_absent(captures, filename):
    key, directory, _ = prepare(captures)
    attempts.mark_submission_intent(captures, key)
    attempts.record_observation(captures, key, observation())
    with (directory / filename).open("ab") as stream: stream.write(b' changed')
    result = attempts.inspect_attempts(captures)
    assert result["requires_stop"] is True and result["usage"]["model_requests"] is None
    assert ledger.inspect_campaign(captures)["reserved_model_requests"] == 1


def test_interruption_after_raw_capture_preserves_bytes_and_does_not_invent_closure(captures, monkeypatch):
    key, directory, _ = prepare(captures)
    attempts.mark_submission_intent(captures, key)
    actual = attempts._completion
    def fail(*args): raise RuntimeError("Fallo artificial tras guardar la fuente.")
    monkeypatch.setattr(attempts, "_completion", fail)
    raw = observation()
    with pytest.raises(RuntimeError): attempts.record_observation(captures, key, raw)
    assert (directory / "observation.raw").read_bytes() == raw and not (directory / "completion.json").exists()
    monkeypatch.setattr(attempts, "_completion", actual)
    assert attempts.inspect_attempts(captures)["requires_stop"] is True
    with pytest.raises(ValueError): attempts.record_observation(captures, key, raw)


def test_partial_preparation_keeps_exclusive_claim(captures, monkeypatch):
    raw = b"artificial failure"
    key = sha256(raw).hexdigest()
    ledger.reserve_proposal(captures, key)
    original = attempts._write_exclusive
    def fail(path, content):
        if path.name == "request.json": raise OSError("Escritura artificial interrumpida.")
        return original(path, content)
    monkeypatch.setattr(attempts, "_write_exclusive", fail)
    with pytest.raises(OSError): attempts.prepare_attempt(captures, raw)
    assert len(list(attempts.ACCESS_ROOT.glob("*.json"))) == 1
    monkeypatch.setattr(attempts, "_write_exclusive", original)
    with pytest.raises((OSError, ValueError)): attempts.prepare_attempt(captures, raw)
    assert attempts.inspect_attempts(captures)["requires_stop"] is True


def test_busy_or_stale_transition_lock_is_not_removed_automatically(captures):
    key, directory, _ = prepare(captures)
    lock = directory / "transition.lock"
    lock.mkdir()
    with pytest.raises(ValueError): attempts.mark_submission_intent(captures, key)
    assert attempts.inspect_attempts(captures)["requires_stop"] is True and lock.exists()


def test_renamed_artifacts_or_changed_code_do_not_create_another_attempt(captures, tmp_path, monkeypatch):
    key, directory, raw = prepare(captures)
    original = attempts._code_hashes
    monkeypatch.setattr(attempts, "_code_hashes", lambda: {**original(), "changed.py": "f" * 64})
    assert attempts.inspect_attempts(captures)["requires_stop"] is True
    monkeypatch.setattr(attempts, "_code_hashes", original)
    moved = tmp_path / "moved-artifacts"
    assert directory.resolve().is_relative_to(tmp_path.resolve()) and moved.resolve().is_relative_to(tmp_path.resolve())
    directory.rename(moved)
    with pytest.raises((ValueError, OSError)): attempts.prepare_attempt(captures, raw)
    assert not directory.exists() and ledger.inspect_campaign(captures)["reserved_model_requests"] == 1


def test_concurrent_submission_markers_only_succeed_once(captures):
    key, _, _ = prepare(captures)
    def mark(_):
        try: attempts.mark_submission_intent(captures, key); return True
        except ValueError: return False
    with ThreadPoolExecutor(max_workers=6) as executor:
        assert sum(executor.map(mark, range(6))) == 1
    attempts.record_observation(captures, key, observation())
    assert attempts.inspect_attempts(captures)["usage"]["model_requests"] == 1


def spawned_marker(args):
    db, access, artifacts, scope, key = args
    from trading_ai import campaign_attempts as worker
    worker.ledger.LEDGER_PATH = Path(db)
    worker.ACCESS_ROOT, worker.ATTEMPTS_ROOT = Path(access), Path(artifacts)
    try: worker.mark_submission_intent(scope, key); return True
    except ValueError: return False


def test_processes_can_only_mark_one_submission(captures):
    key, _, _ = prepare(captures)
    task = (str(ledger.LEDGER_PATH), str(attempts.ACCESS_ROOT), str(attempts.ATTEMPTS_ROOT), captures, key)
    with ProcessPoolExecutor(max_workers=3, mp_context=multiprocessing.get_context("spawn")) as executor:
        assert sum(executor.map(spawned_marker, [task] * 6)) == 1
    attempts.record_observation(captures, key, observation())
    assert attempts.inspect_attempts(captures)["usage"]["model_requests"] == 1


def test_valid_json_event_with_changed_identity_is_rejected(captures):
    key, directory, _ = prepare(captures)
    path = directory / "events.jsonl"
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    events[0]["data"]["scope_id"] = "f" * 64
    path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
    assert attempts.inspect_attempts(captures)["requires_stop"] is True


def test_changed_global_capture_claim_blocks_new_preparation(captures):
    _, _, raw = prepare(captures)
    claim, = attempts.ACCESS_ROOT.glob("*.json")
    with claim.open("ab") as stream: stream.write(b" changed")
    with pytest.raises(ValueError): attempts.prepare_attempt(captures, raw)
    assert attempts.inspect_attempts(captures)["requires_stop"] is True


@pytest.mark.parametrize("transition", ["intent_before_observation", "observation_before_intent"])
def test_state_is_reloaded_inside_transition_lock(captures, monkeypatch, transition):
    key, _, _ = prepare(captures)
    actual, entered = attempts._transition, []
    @contextmanager
    def interleaved(directory):
        if not entered:
            entered.append(True)
            if transition == "intent_before_observation": attempts.mark_submission_intent(captures, key)
            else:
                attempts.record_observation(captures, key, observation(model_request_attempted=False, content=None,
                    usage=None, error={"type": "PreflightError", "message": "Sin envío."}))
        with actual(directory): yield
    monkeypatch.setattr(attempts, "_transition", interleaved)
    if transition == "intent_before_observation":
        assert attempts.record_observation(captures, key, observation())["analysis"]["accounting_complete"] is True
    else:
        with pytest.raises(ValueError): attempts.mark_submission_intent(captures, key)
    assert attempts.inspect_attempts(captures)["requires_stop"] is False


def test_totals_propagate_unknowns_and_keep_known_subtotals_separate(captures):
    first, _, _ = prepare(captures)
    second, _, _ = prepare(captures, b" ")
    for key in (first, second): attempts.mark_submission_intent(captures, key)
    attempts.record_observation(captures, first, observation())
    attempts.record_observation(captures, second, observation(usage={"input_tokens": None, "output_tokens": 9, "api_cost_usd": "0"}))
    result = attempts.inspect_attempts(captures)
    assert result["usage"] == {"model_requests": 2, "input_tokens": None, "output_tokens": 26, "api_cost_usd": "0"}
    assert result["known_subtotals"]["input_tokens"] == 100 and result["requires_stop"] is True


def test_input_limits_reject_without_truncating_or_creating_observation(captures):
    with pytest.raises(ValueError): attempts.prepare_attempt(captures, b"x" * 12289)
    key, directory, _ = prepare(captures)
    with pytest.raises(ValueError): attempts.record_observation(captures, key, b"x" * (attempts.MAX_OBSERVATION_BYTES + 1))
    assert not (directory / "observation.raw").exists()


def test_cli_only_inspects_without_send_or_capture_options(captures, capsys):
    attempts.main(["--scope", captures])
    assert json.loads(capsys.readouterr().out)["usage"] == attempts.ZERO_USAGE
    with pytest.raises(SystemExit): attempts.main(["--scope", captures, "--send"])
