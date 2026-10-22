"""Proveedores: ninguna prueba descarga, abre sockets ni utiliza credenciales."""

import json
from urllib.error import URLError

import pytest

from trading_ai.ai import (AIConfig, OllamaProvider, ProviderError, _NoRedirect,
                           create_provider, load_ai_config)


@pytest.mark.parametrize("url", ["https://api.openai.com", "http://example.com:11435",
                                   "http://0.0.0.0:11435", "http://127.0.0.1",
                                   "http://127.0.0.1:11435/remote", "http://user@127.0.0.1:11435",
                                   "http://127.0.0.1:11435?proxy=remote", "http://127.0.0.1:11435#remote"])
def test_local_provider_rejects_non_loopback_or_ambiguous_urls(url):
    with pytest.raises(ValueError):
        AIConfig(base_url=url)


@pytest.mark.parametrize("changes", [{"model": "qwen3.5:cloud"}, {"provider": "unknown"},
                                       {"context_tokens": True}, {"output_tokens": 100000},
                                       {"timeout_seconds": 0}])
def test_invalid_or_unbounded_configuration(changes):
    with pytest.raises(ValueError):
        AIConfig(**changes)


def test_openai_is_reserved_without_network_or_credentials(monkeypatch):
    monkeypatch.setattr("trading_ai.ai.build_opener", lambda *args: pytest.fail("No debe abrir red"))
    with pytest.raises(ProviderError, match="futura"):
        create_provider(AIConfig(provider="openai"))


def test_configuration_is_explicit_and_rejects_unknown_fields(tmp_path):
    assert load_ai_config().provider == "ollama"
    path = tmp_path / "ai.json"
    path.write_text(json.dumps({"model": "small:4b", "output_tokens": 512}), encoding="utf-8")
    assert load_ai_config(path).model == "small:4b"
    path.write_text('{"api_key":"must-not-be-stored-here"}', encoding="utf-8")
    with pytest.raises(ValueError, match="desconocidos"):
        load_ai_config(path)


def test_missing_local_model_never_triggers_download():
    calls = []
    def transport(method, path, payload):
        calls.append((method, path))
        return {"models": []}
    with pytest.raises(ProviderError, match="no está descargado"):
        OllamaProvider(AIConfig(), transport).complete([], {})
    assert calls == [("GET", "/api/tags")]


def test_cloud_alias_rejected_even_if_listed_as_a_model():
    def transport(*args):
        return {"models": [{"name": "qwen3.5:4b", "remote_host": "remote.example"}]}
    with pytest.raises(ProviderError, match="remoto"):
        OllamaProvider(AIConfig(), transport).describe()


def test_ollama_records_measured_usage_and_bounds_generation():
    calls = []
    def transport(method, path, payload):
        calls.append((method, path, payload))
        if path == "/api/tags":
            return {"models": [{"name": "qwen3.5:4b", "digest": "a" * 64}]}
        return {"model": "qwen3.5:4b", "message": {"content": '{"ok":true}'},
                "done": True, "done_reason": "stop", "prompt_eval_count": 40,
                "eval_count": 12, "total_duration": 100}
    provider = OllamaProvider(AIConfig(), transport)
    reply = provider.complete([{"role": "user", "content": "test"}], {"type": "object"})
    assert reply.usage["input_tokens"] == 40
    assert reply.usage["cached_input_tokens"] is None
    assert reply.usage["api_cost_usd"] == "0"
    request = calls[-1][2]
    assert request["stream"] is False and request["think"] is False
    assert request["options"]["num_ctx"] == 4096
    assert request["options"]["num_predict"] == 384
    assert request["options"]["num_gpu"] == 0
    assert "tools" not in request  # Se utiliza el contrato JSON limitado del experimento.


def test_truncated_reply_is_rejected_with_its_known_consumption():
    def transport(method, path, payload):
        if path == "/api/tags":
            return {"models": [{"name": "qwen3.5:4b"}]}
        return {"done": True, "done_reason": "length", "eval_count": 384}
    with pytest.raises(ProviderError, match="truncadas") as failure:
        OllamaProvider(AIConfig(), transport).complete([], {})
    assert failure.value.usage["output_tokens"] == 384


def test_redirects_are_blocked():
    with pytest.raises(ProviderError, match="redirigir"):
        _NoRedirect().redirect_request(None, None, 302, "", {}, "https://remote.example")


def test_local_transport_ignores_proxies_and_does_not_retry(monkeypatch):
    calls = []
    class OfflineOpener:
        def open(self, *args, **kwargs):
            calls.append(1)
            raise URLError("offline")
    def opener(*handlers):
        assert handlers[0].proxies == {}
        assert isinstance(handlers[1], _NoRedirect)
        return OfflineOpener()
    monkeypatch.setattr("trading_ai.ai.build_opener", opener)
    with pytest.raises(ProviderError, match="servicio local"):
        OllamaProvider(AIConfig()).describe()
    assert calls == [1]
