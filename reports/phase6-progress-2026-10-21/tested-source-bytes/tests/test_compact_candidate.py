"""Una llamada local acotada con respuesta original, reserva y revisión separadas."""

from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from test_compact_ollama import Transport
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from test_structured_draft_context import claim_for
from trading_ai.ai import ProviderError
from trading_ai.compact_candidate import CompactCandidateError, generate_compact_candidate, verify_compact_candidate, main
from trading_ai.compact_ollama import CompactOllamaProvider
from trading_ai.structured_draft_request import prepare_draft_request
from trading_ai.structured_freshness import inspect_request_freshness
from trading_ai.structured_generation import generation_budget_status
from trading_ai import structured_generation as generation


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    for module, attribute, folder in (
        ("idea_memory", "MEMORY_ROOT", "memory"), ("structured_ideas", "ACCESS_ROOT", "ideas-access"),
        ("rule_execution", "ACCESS_ROOT", "execution-access"), ("structured_session", "ACCESS_ROOT", "sessions-access"),
        ("structured_generation", "ACCESS_ROOT", "compact-access"),
    ):
        monkeypatch.setattr(f"trading_ai.{module}.{attribute}", tmp_path / folder)


@pytest.fixture
def prepared_request(memory, tmp_path):
    return prepare_draft_request(memory, output_dir=tmp_path / "requests")


@pytest.fixture
def transport(proposal):
    transport = Transport()
    draft = {key: deepcopy(proposal[key]) for key in ("entry", "exit")}
    draft["entry"]["right"]["value"] = "2"
    transport.response["message"]["content"] = json.dumps(draft)
    return transport


def generate(prepared_request, tmp_path, transport):
    return generate_compact_candidate(prepared_request, provider=CompactOllamaProvider(transport=transport),
                                      output_dir=tmp_path / "candidates", reservation_output_dir=tmp_path / "reservations")


def events(run):
    return [json.loads(line) for line in (run / "events.jsonl").read_bytes().splitlines()]


def test_candidate_retains_raw_rules_and_full_python_description_without_simulation(prepared_request, tmp_path, transport, monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail("Una propuesta no puede calcular, revisar o simular")
    for name in ("trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.experiments.run_backtest",
                 "trading_ai.structured_session._action", "socket.create_connection", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    original = {path: path.read_bytes() for path in prepared_request.iterdir()}
    run = generate(prepared_request, tmp_path, transport)
    record = verify_compact_candidate(run)
    assert record["status"] == "pending_technical_review" and record["duplicate_of"] is None
    assert record["draft"] == json.loads(transport.response["message"]["content"])
    assert len(transport.model_calls) == record["model_requests"] == 1
    assert record["backtests"] == 0 and record["api_cost_usd"] == "0"
    assert record["model_description"] is record["calculated_results"] is None
    assert record["eligible_for_session"] is record["executable"] is False
    assert record["metadata_request_attempts"] == 6 and record["usage"][0]["input_tokens"] == 100
    assert "title" not in record["draft"] and not (run / "proposal.json").exists()
    assert all(record["rule_description"][key].endswith(".") for key in ("entry", "exit", "execution", "interpretation"))
    assert all(path.read_bytes() == raw for path, raw in original.items())
    assert inspect_request_freshness(prepared_request)["status"] == "stale"
    assert generation_budget_status(prepared_request)["consumed"] is True
    assert next(item["data"] for item in events(run) if item["event"] == "model_response")["content"] == transport.response["message"]["content"]


def test_duplicate_rules_keep_original_claim_and_do_not_get_approved(prepared_request, tmp_path, transport, proposal):
    originals = {path: path.read_bytes() for path in (tmp_path / "ideas-access").glob("*.json")}
    transport.response["message"]["content"] = json.dumps({key: proposal[key] for key in ("entry", "exit")})
    run = generate(prepared_request, tmp_path, transport)
    record = verify_compact_candidate(run)
    assert record["status"] == "duplicate_rules" and record["duplicate_of"] != str(run)
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert len(list((tmp_path / "ideas-access").glob("*.json"))) == len(originals)
    assert not record["eligible_for_session"] and record["backtests"] == 0


def test_new_folder_cannot_retry_or_reset_consumed_attempt(prepared_request, tmp_path, transport):
    generate(prepared_request, tmp_path, transport)
    with pytest.raises(CompactCandidateError): generate(prepared_request, tmp_path, transport)
    assert len(transport.model_calls) == 1 and len(list(generation.ACCESS_ROOT.glob("*.json"))) == 1


@pytest.mark.parametrize("invalid", ["duplicate_keys", "broken_json", "prose", "extra_controls", "future_lag", "empty"])
def test_bad_response_is_recorded_with_usage_and_no_retry(prepared_request, tmp_path, transport, invalid):
    content = transport.response["message"]["content"]
    if invalid == "duplicate_keys": content = content[:-1] + ',"entry":{}}'
    elif invalid == "broken_json": content = content[:-1]
    elif invalid == "prose": content = "Comprar si sube y salir si baja."
    elif invalid == "empty": content = "{}"
    else:
        draft = json.loads(content)
        if invalid == "extra_controls": draft["capital"] = "1000000"
        else: draft["entry"]["left"]["lag"] = -1
        content = json.dumps(draft)
    transport.response["message"]["content"] = content
    with pytest.raises(CompactCandidateError) as failure: generate(prepared_request, tmp_path, transport)
    run = failure.value.directory
    response = next(item["data"] for item in events(run) if item["event"] == "model_response")
    assert response["content"] == content and response["usage"]["output_tokens"] == 60
    assert events(run)[-1]["data"]["model_requests"] == len(transport.model_calls) == 1
    assert not (run / "candidate.json").exists() and generation_budget_status(prepared_request)["consumed"]
    with pytest.raises(CompactCandidateError): generate(prepared_request, tmp_path, transport)
    assert len(transport.model_calls) == 1


@pytest.mark.parametrize("known_usage", [True, False])
def test_provider_failure_conserves_known_or_unknown_consumption(prepared_request, tmp_path, transport, known_usage):
    if known_usage: transport.response["done_reason"] = "length"
    else: transport.response = ProviderError("HTTP 400 context overflow")
    with pytest.raises(CompactCandidateError) as failure: generate(prepared_request, tmp_path, transport)
    failed = events(failure.value.directory)[-1]["data"]
    assert failed["usage"][0]["input_tokens"] == (100 if known_usage else None)
    assert failed["api_cost_usd"] == "0" and failed["backtests"] == 0
    assert failed["model_requests"] == 1 and len(transport.model_calls) == 1
    error = next(item["data"] for item in events(failure.value.directory) if item["event"] == "model_error")
    assert error["provider_response"] == (transport.response if known_usage else None)
    assert generation_budget_status(prepared_request)["consumed"]


def test_unverified_server_is_refused_before_reservation(prepared_request, tmp_path, transport):
    transport.version = "other"
    with pytest.raises(CompactCandidateError) as failure: generate(prepared_request, tmp_path, transport)
    assert not transport.model_calls and not generation.ACCESS_ROOT.exists()
    assert events(failure.value.directory)[-1]["data"]["model_requests"] == 0


def test_new_history_during_chat_retains_response_but_does_not_accept_it(prepared_request, tmp_path, transport):
    reference = inspect_request_freshness(prepared_request)["reference"]
    class ConcurrentTransport:
        def __call__(self, method, path, payload):
            response = transport(method, path, payload)
            if path == "/api/chat": claim_for(reference, "b" * 64, tmp_path / "concurrent")
            return response
    provider = CompactOllamaProvider(transport=ConcurrentTransport())
    with pytest.raises(CompactCandidateError, match="desactualizada") as failure:
        generate_compact_candidate(prepared_request, provider=provider, output_dir=tmp_path / "candidates",
                                   reservation_output_dir=tmp_path / "reservations")
    assert any(item["event"] == "model_response" for item in events(failure.value.directory))
    assert events(failure.value.directory)[-1]["data"]["usage"][0]["output_tokens"] == 60
    assert len(transport.model_calls) == 1 and generation_budget_status(prepared_request)["consumed"]
    assert len(list((tmp_path / "ideas-access").glob("*.json"))) == 2


@pytest.mark.parametrize("filename", ["candidate.json", "candidate.json.sha256", "job.json", "job.sha256", "report.md", "events.jsonl"])
def test_artifact_tampering_is_detected(prepared_request, tmp_path, transport, filename):
    run = generate(prepared_request, tmp_path, transport)
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_compact_candidate(run)
    assert len(transport.model_calls) == 1


@pytest.mark.parametrize("which", ["rule", "submit"])
def test_changed_shared_claim_is_detected(prepared_request, tmp_path, transport, which):
    run = generate(prepared_request, tmp_path, transport)
    record = verify_compact_candidate(run)
    claim = Path(record["rule_access"]["path"]) if which == "rule" else Path(record["reservation"]["directory"]) / "actions/submit.json"
    claim.write_bytes(b'{}')
    with pytest.raises((ValueError, KeyError)): verify_compact_candidate(run)


def test_cannot_relocate_candidate(prepared_request, tmp_path, transport):
    run = generate(prepared_request, tmp_path, transport)
    shutil.copytree(run, tmp_path / "copied")
    with pytest.raises(ValueError): verify_compact_candidate(tmp_path / "copied")


def test_verify_is_offline_and_cli_cannot_adopt_or_simulate(prepared_request, tmp_path, transport, monkeypatch, capsys):
    run = generate(prepared_request, tmp_path, transport)
    def forbidden(*args, **kwargs): pytest.fail("La verificación no debe consultar ni simular")
    monkeypatch.setattr(CompactOllamaProvider, "complete", forbidden)
    monkeypatch.setattr(CompactOllamaProvider, "describe", forbidden)
    monkeypatch.setattr("trading_ai.experiments.run_backtest", forbidden)
    main(["verify", "--run", str(run)])
    assert json.loads(capsys.readouterr().out)["executable"] is False
    with pytest.raises(SystemExit): main(["adopt", "--run", str(run)])
    assert len(transport.model_calls) == 1
