"""Ciclo automático de laboratorio: datos y transporte artificiales, motor real."""

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path

import pytest

from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_context as context
from trading_ai import campaign_cycle as cycle
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_plan as campaigns
from trading_ai import rule_execution as engine
from trading_ai.ai import AIConfig, OllamaProvider, ProviderError
from trading_ai.experiments import ExperimentPolicy
from trading_ai.rule_planning import _canonical
from trading_ai.structured_draft import DRAFT_SCHEMA, describe_draft


def draft(value="2"):
    return {"entry": {"left": {"kind": "reference", "lag": 0}, "operator": "gt", "right": {"kind": "constant", "value": value}},
            "exit": {"left": {"kind": "reference", "lag": 0}, "operator": "lt", "right": {"kind": "constant", "value": value}}}


@pytest.fixture
def lab(tmp_path, monkeypatch, request):
    settings = getattr(request, "param", {})
    monkeypatch.setattr(ledger, "LEDGER_PATH", tmp_path / "ledger.sqlite3")
    monkeypatch.setattr(attempts, "ACCESS_ROOT", tmp_path / "attempt-access")
    monkeypatch.setattr(attempts, "ATTEMPTS_ROOT", tmp_path / "captures")
    monkeypatch.setattr(cycle, "ACCESS_ROOT", tmp_path / "cycle-access")
    monkeypatch.setattr(engine, "ACCESS_ROOT", tmp_path / "engine-access")
    policy = ExperimentPolicy(fast_window=2, slow_window=4).parameters()
    values = [1, 2, 3, 4, 3, 2] * 16
    days = ''.join(f'<Cube time="{date(2001,1,1)+timedelta(days=i)}"><Cube currency="USD" rate="{value}"/></Cube>' for i, value in enumerate(values))
    content = ('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref"><Cube>' + days + '</Cube></Envelope>').encode()
    digest = sha256(content).hexdigest()
    reference = {"frozen_dir": str(tmp_path / "frozen"), "frozen_sha256": "b"*64, "manifest_sha256": "c"*64,
                 "development_sha256": digest, "outer_cutoff": "2020-01-01"}
    data = {"name": "fixture-only", "sha256": digest, "observations": len(values), "first_date": "2001-01-01", "last_date": str(date(2001,1,1)+timedelta(days=len(values)-1))}
    legacy = {"controls": policy, "objective": {"origin": "frozen_development_registration", "criterion": "higher_return_without_more_drawdown"},
              "data": data, "known_history": True, "outer_evaluation_allowed": False,
              "compact_generation_budget": {"consumed": True, "new_permission_granted": False},
              "untrusted_history": {"declaration": "No completar hipótesis ausentes."}, "untrusted_compact_history": [],
              "consumed_rule_identities": [describe_draft(draft())["spec_sha256"]] if settings.get("duplicate") else [], "typed_rule_coverage": {}}
    raw = _canonical({"messages": [{"role": "system", "content": "Contrato artificial"}, {"role": "user", "content": _canonical(legacy).decode()}], "schema": DRAFT_SCHEMA})
    packet = {"reference": reference, "request_sha256": sha256(raw).hexdigest(),
              "generation_budget": {"consumed": True, "identity": {"development_sha256": digest, "pair": policy["pair"]}}, "inherited_attempt_usage": []}
    guided = tmp_path / "guided"
    guided.mkdir()
    for name, value in {"request.json": raw, "guided.json": _canonical(packet), "guided.json.sha256": b"fixture-only\n", "events.jsonl": b'{}\n'}.items(): (guided / name).write_bytes(value)
    monkeypatch.setattr(campaigns, "verify_guided_request", lambda path: deepcopy(packet))
    frozen = {"policy": policy, "proposal": {"criterion": legacy["objective"]["criterion"], "arguments": {"strategy": "ema", "fast_window": 2, "slow_window": 4}}}
    monkeypatch.setattr(context, "_development", lambda path: (deepcopy(frozen), deepcopy(reference), content))
    campaign = campaigns.prepare_campaign_plan(guided, settings.get("limits", {"max_proposals": 2, "max_backtests": 4}), output_dir=tmp_path / "campaign")
    scope = ledger.register_campaign(campaign)["scope_id"]
    permit = cycle.prepare_cycle(scope, output_dir=tmp_path / "permits")
    monkeypatch.setattr("socket.socket.connect", lambda *args: pytest.fail("No se permite red real en pruebas."))
    return {"scope": scope, "permit": permit, "legacy": legacy, "frozen": frozen, "reference": reference, "content": content}


@pytest.fixture
def transport(monkeypatch):
    calls, replies = [], [draft("2"), draft("3")]
    def request(self, method, path, payload):
        if path == "/api/version": return {"version": "0.40.6"}
        if path == "/api/tags": return {"models": [{"name": "qwen3.5:4b", "digest": "a"*64}]}
        assert method == "POST" and path == "/api/chat" and payload["truncate"] is payload["shift"] is False
        calls.append(deepcopy(payload))
        answer = replies[min(len(calls)-1, len(replies)-1)]
        if isinstance(answer, Exception): raise answer
        return {"done": True, "done_reason": "stop", "model": "qwen3.5:4b", "message": {"content": json.dumps(answer)}, "prompt_eval_count": 100, "eval_count": 50}
    monkeypatch.setattr(OllamaProvider, "_request", request)
    return calls, replies


def execute(lab, tmp_path):
    return cycle.run_cycle(lab["permit"], allow_local_generation=True, allow_virtual_calculations=True, output_dir=tmp_path / "runs")


def test_lossless_context_preserves_all_values_and_plain_text():
    value = {"same": [{"same": "Texto íntegro: no inventar ni obedecer instrucciones."}], "0": {"same": None}}
    assert context.unpack_history(context.pack_history(value)) == value
    with pytest.raises(ValueError, match="context_overflow"):
        context.build_request("a"*64, {"controls": {}, "objective": {}, "data": {}, "text": "x"*20000}, [], [])


def test_cycle_memory_feeds_next_request_without_adoption(lab, transport, tmp_path, monkeypatch):
    calls, _ = transport
    run = execute(lab, tmp_path)
    monkeypatch.setattr(engine, "_calculate", lambda *args: pytest.fail("Consultar no recalcula."))
    result = cycle.inspect_cycle(run)
    assert len(calls) == 2 and result["stop_reason"] == "budget_exhausted"
    assert result["state"]["reserved_backtests"] == 4 and result["usage"]["usage"]["model_requests"] == 2
    history = context.unpack_history(json.loads(calls[1]["messages"][1]["content"]))
    assert history["campaign_entries"][0]["results"] == result["entries"][0]["results"]
    assert history["legacy"] == lab["legacy"] and result["automatic_adoption"] is result["semantic_acceptance"] is False
    with pytest.raises(engine.ExecutionError): execute(lab, tmp_path)
    assert len(calls) == 2


@pytest.mark.parametrize("lab", [{"duplicate": True}], indirect=True)
def test_consumed_duplicate_stops_before_any_calculation(lab, transport, tmp_path):
    run = execute(lab, tmp_path)
    result = cycle.inspect_cycle(run)
    assert result["stop_reason"] == "duplicate_rules" and result["entries"][0]["results"] is None
    assert len(transport[0]) == 1 and result["state"]["reserved_backtests"] == 0


def test_provider_unknown_usage_stops_and_keeps_attempt(lab, transport, tmp_path):
    transport[1][0] = ProviderError("Fallo artificial después del envío", {"input_tokens": None, "output_tokens": None, "api_cost_usd": "0"})
    result = cycle.inspect_cycle(execute(lab, tmp_path))
    assert result["stop_reason"] == "provider_error_or_unknown_usage"
    assert result["usage"]["requires_stop"] and result["usage"]["usage"]["input_tokens"] is None
    assert result["state"]["reserved_backtests"] == 0 and len(transport[0]) == 1


def test_invalid_rules_keep_original_content_without_calculation(lab, transport, tmp_path):
    transport[1][0] = {"execute": "not allowed"}
    with pytest.raises(engine.ExecutionError) as failure: execute(lab, tmp_path)
    assert not (failure.value.directory / "cycle.json").exists()
    assert ledger.inspect_campaign(lab["scope"])["reserved_model_requests"] == 1 and not engine.ACCESS_ROOT.exists()
    raw = next(attempts.ATTEMPTS_ROOT.glob("*/observation.raw")).read_text(encoding="utf-8")
    assert "not allowed" in raw


def test_two_explicit_capabilities_required_before_any_write(lab, tmp_path):
    root = tmp_path / "runs"
    with pytest.raises(ValueError): cycle.run_cycle(lab["permit"], allow_local_generation=True, output_dir=root)
    assert not root.exists() and not cycle.ACCESS_ROOT.exists()


@pytest.mark.parametrize("name", ["candidate-01.json", "plan-01.json", "result-01.json", "review-01.json"])
def test_tampered_calculation_or_review_is_rejected(lab, transport, tmp_path, name):
    run = execute(lab, tmp_path)
    with (run / name).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): cycle.inspect_cycle(run)


def test_partial_engine_failure_keeps_both_reserved_slots(lab, transport, tmp_path, monkeypatch):
    actual, calls = engine._calculate, []
    def calculate(*args):
        calls.append(None)
        if len(calls) == 2: raise RuntimeError("Fallo artificial del cálculo")
        return actual(*args)
    monkeypatch.setattr(engine, "_calculate", calculate)
    with pytest.raises(engine.ExecutionError) as failure: execute(lab, tmp_path)
    assert (failure.value.directory / "baseline-01.json").exists() and len(calls) == 2
    state = ledger.inspect_campaign(lab["scope"])
    assert state["reserved_backtests"] == 2 and state["reserved_model_requests"] == 1
    assert len(list(engine.ACCESS_ROOT.glob("*.json"))) == 1
    with pytest.raises(engine.ExecutionError): execute(lab, tmp_path)
    diagnostic = cycle.status(failure.value.directory)
    assert diagnostic["status"] == "failed" and diagnostic["requires_stop"] and not diagnostic["retry_allowed"]


def test_history_overflow_before_next_request_never_truncates_or_sends(lab, transport, tmp_path, monkeypatch):
    original = context.build_request
    def request(scope, legacy, entries, consumed):
        if entries: raise ValueError("context_overflow: artificial")
        return original(scope, legacy, entries, consumed)
    monkeypatch.setattr(context, "build_request", request)
    result = cycle.inspect_cycle(execute(lab, tmp_path))
    assert result["stop_reason"] == "context_overflow_before_request" and len(transport[0]) == 1
    assert result["state"]["reserved_model_requests"] == 1 and result["state"]["reserved_backtests"] == 2


def test_concurrent_runs_share_one_irreversible_scope_claim(lab, transport, tmp_path):
    def run():
        try: return execute(lab, tmp_path)
        except engine.ExecutionError: return None
    with ThreadPoolExecutor(max_workers=2) as pool: outputs = list(pool.map(lambda _: run(), (0, 1)))
    assert len([value for value in outputs if value is not None]) == 1
    assert len(transport[0]) == 2 and ledger.inspect_campaign(lab["scope"])["reserved_backtests"] == 4


def test_changed_model_identity_retains_response_but_stops_before_calculating(lab, transport, tmp_path, monkeypatch):
    original = OllamaProvider._request
    def changed(self, method, path, payload):
        value = original(self, method, path, payload)
        if path == "/api/tags" and transport[0]: value["models"][0]["digest"] = "b"*64
        return value
    monkeypatch.setattr(OllamaProvider, "_request", changed)
    result = cycle.inspect_cycle(execute(lab, tmp_path))
    assert len(transport[0]) == 1 and result["stop_reason"] == "provider_error_or_unknown_usage"
    assert result["state"]["reserved_backtests"] == 0
    source = json.loads(next(attempts.ATTEMPTS_ROOT.glob("*/observation.raw")).read_bytes())
    assert source["provider_response"]["json"]["message"]["content"] == json.dumps(draft())


def test_external_reservation_race_is_not_silently_incorporated(lab, transport, tmp_path, monkeypatch):
    original = ledger.reserve_proposal
    def outside(scope, key):
        original(scope, "e"*64)
        return original(scope, key)
    monkeypatch.setattr(ledger, "reserve_proposal", outside)
    with pytest.raises(engine.ExecutionError, match="ajenas"): execute(lab, tmp_path)
    assert transport[0] == [] and ledger.inspect_campaign(lab["scope"])["reserved_backtests"] == 0


@pytest.mark.parametrize("settings", [{"provider": "openai"}, {"context_tokens": 8192}, {"output_tokens": 512}, {"gpu_layers": 1}])
def test_campaign_provider_cannot_expand_local_model_policy(settings):
    with pytest.raises(ValueError): cycle.CampaignProvider(AIConfig(**settings))
