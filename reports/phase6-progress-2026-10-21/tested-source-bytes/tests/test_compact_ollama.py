"""Adaptador probado sin servicio real: contexto sin recortes, identidad y consumo conservado."""

from copy import deepcopy
from dataclasses import replace

import pytest

from trading_ai.ai import AIConfig, ProviderError
from trading_ai.compact_ollama import CompactOllamaProvider
from trading_ai.structured_draft import DRAFT_SCHEMA


class Transport:
    def __init__(self):
        self.calls = []
        self.version = "0.40.6"
        self.digest = "a" * 64
        self.remote = False
        self.change_after_chat = False
        self.response = {"model": "qwen3.5:4b", "done": True, "done_reason": "stop",
                         "message": {"content": '{"entry":{},"exit":{}}'},
                         "prompt_eval_count": 100, "eval_count": 60, "total_duration": 123}

    def __call__(self, method, path, payload):
        self.calls.append((method, path, deepcopy(payload)))
        if path == "/api/version": return {"version": self.version}
        if path == "/api/tags":
            return {"models": [{"name": "qwen3.5:4b", "digest": self.digest,
                                "remote_host": "https://example.invalid" if self.remote else ""}]}
        assert method == "POST" and path == "/api/chat"
        if self.change_after_chat: self.digest = "b" * 64
        if isinstance(self.response, Exception): raise self.response
        return deepcopy(self.response)

    @property
    def model_calls(self):
        return [call for call in self.calls if call[1] == "/api/chat"]


@pytest.fixture
def messages():
    return [{"role": "system", "content": "Solo reglas declarativas."},
            {"role": "user", "content": "Contexto educativo sin resultados."}]


def test_advertised_policy_does_not_claim_a_token_count():
    transport = Transport()
    identity = CompactOllamaProvider(transport=transport).describe()
    assert identity["server_version"] == "0.40.6" and identity["truncate"] is identity["shift"] is False
    assert identity["prompt_tokens_before_request"] is None and identity["api_cost_usd"] == "0"
    assert len(transport.calls) == 2 and not transport.model_calls


def test_payload_disables_truncation_and_shift_without_changing_old_limits(messages):
    transport = Transport()
    provider = CompactOllamaProvider(transport=transport)
    original = deepcopy(messages)
    reply = provider.complete(messages, DRAFT_SCHEMA)
    _, _, body = transport.model_calls[0]
    assert body["truncate"] is body["shift"] is body["think"] is body["stream"] is False
    assert body["options"] == {"num_ctx": 4096, "num_predict": 384, "num_gpu": 0, "temperature": 0}
    assert body["messages"] == original == messages and body["format"] == DRAFT_SCHEMA
    assert len(transport.model_calls) == 1 and reply.content == transport.response["message"]["content"]
    assert reply.usage["input_tokens"] == 100 and reply.usage["output_tokens"] == 60
    assert reply.usage["api_cost_usd"] == "0" and reply.usage["metadata_request_attempts"] == 4


@pytest.mark.parametrize("version", ["0.40.5", "0.40.7", "1.0.0", None])
def test_unreviewed_version_is_rejected_before_generation(messages, version):
    transport = Transport()
    transport.version = version
    with pytest.raises(ProviderError, match="Versión") as failure:
        CompactOllamaProvider(transport=transport).complete(messages, DRAFT_SCHEMA)
    assert not transport.model_calls
    assert failure.value.usage["input_tokens"] == failure.value.usage["output_tokens"] == 0


@pytest.mark.parametrize("invalid", ["unknown_digest", "remote_model"])
def test_model_identity_is_checked_before_inference(messages, invalid):
    transport = Transport()
    if invalid == "unknown_digest": transport.digest = None
    else: transport.remote = True
    with pytest.raises(ProviderError): CompactOllamaProvider(transport=transport).complete(messages, DRAFT_SCHEMA)
    assert not transport.model_calls


def test_model_substitution_after_generation_preserves_consumption_and_rejects_result(messages):
    transport = Transport()
    transport.change_after_chat = True
    with pytest.raises(ProviderError, match="cambió") as failure:
        CompactOllamaProvider(transport=transport).complete(messages, DRAFT_SCHEMA)
    assert len(transport.model_calls) == 1
    assert failure.value.usage["input_tokens"] == 100 and failure.value.usage["output_tokens"] == 60


@pytest.mark.parametrize("change", ["incomplete", "wrong_model", "missing_message"])
def test_incomplete_or_inconsistent_response_is_not_retried(messages, change):
    transport = Transport()
    if change == "incomplete": transport.response["done_reason"] = "length"
    elif change == "wrong_model": transport.response["model"] = "other-model"
    else: transport.response["message"] = None
    with pytest.raises(ProviderError) as failure:
        CompactOllamaProvider(transport=transport).complete(messages, DRAFT_SCHEMA)
    assert len(transport.model_calls) == 1 and failure.value.usage["output_tokens"] == 60


def test_incomplete_raw_response_remains_available_without_accepting_it(messages):
    transport = Transport()
    transport.response["done_reason"] = "length"
    provider = CompactOllamaProvider(transport=transport)
    with pytest.raises(ProviderError): provider.complete(messages, DRAFT_SCHEMA)
    assert provider.last_response == transport.response
    transport.response["message"]["content"] = "changed"
    assert provider.last_response["message"]["content"] != "changed"


@pytest.mark.parametrize("inputs,outputs", [(None, 60), (True, 60), (-1, 60), (100, None),
                                           (100, 0), (100, 385), (4000, 200)])
def test_missing_or_out_of_limit_metrics_cannot_be_accepted(messages, inputs, outputs):
    transport = Transport()
    transport.response.update(prompt_eval_count=inputs, eval_count=outputs)
    with pytest.raises(ProviderError, match="consumo"):
        CompactOllamaProvider(transport=transport).complete(messages, DRAFT_SCHEMA)
    assert len(transport.model_calls) == 1


def test_context_or_network_error_preserves_unknown_usage_instead_of_zero(messages):
    transport = Transport()
    transport.response = ProviderError("HTTP 400: context overflow")
    with pytest.raises(ProviderError) as failure:
        CompactOllamaProvider(transport=transport).complete(messages, DRAFT_SCHEMA)
    assert len(transport.model_calls) == 1
    assert failure.value.usage["input_tokens"] is failure.value.usage["output_tokens"] is None
    assert failure.value.usage["api_cost_usd"] == "0"


@pytest.mark.parametrize("change", ["schema", "roles", "extra_field", "too_large"])
def test_only_the_bounded_compact_contract_is_accepted_before_network(messages, change):
    transport = Transport()
    schema = DRAFT_SCHEMA
    if change == "schema": schema = {"type": "string"}
    elif change == "roles": messages[0]["role"] = "assistant"
    elif change == "extra_field": messages[0]["tools"] = []
    else: messages[1]["content"] = "x" * 13000
    with pytest.raises(ProviderError): CompactOllamaProvider(transport=transport).complete(messages, schema)
    assert not transport.calls


@pytest.mark.parametrize("change", [{"context_tokens": 8192}, {"output_tokens": 512}, {"gpu_layers": 1}, {"provider": "openai"}])
def test_limits_cannot_be_expanded_or_switched_to_paid_provider(change):
    with pytest.raises(ValueError): CompactOllamaProvider(replace(AIConfig(), **change))
