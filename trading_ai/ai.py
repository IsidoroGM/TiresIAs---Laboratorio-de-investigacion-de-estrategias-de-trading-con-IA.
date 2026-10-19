"""Contrato de proveedores de IA; Ollama local y reserva explícita para OpenAI.

No instala paquetes, descarga modelos, inicia servicios ni lee credenciales.
"""

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class ProviderError(ValueError):
    """Fallo del proveedor sin reintentos ni sustitución por servicios de pago."""

    def __init__(self, message: str, usage: dict | None = None):
        super().__init__(message)
        self.usage = usage


@dataclass(frozen=True)
class AIConfig:
    provider: str = "ollama"
    model: str = "qwen3.5:4b"
    base_url: str = "http://127.0.0.1:11435"
    timeout_seconds: int = 180
    context_tokens: int = 4096
    output_tokens: int = 384
    gpu_layers: int = 0

    def __post_init__(self) -> None:
        if self.provider not in ("ollama", "openai"):
            raise ValueError("Proveedor desconocido. Opciones: ollama, openai (reservado).")
        if not isinstance(self.model, str) or not self.model.strip() or len(self.model) > 128:
            raise ValueError("El modelo debe tener un nombre no vacío de hasta 128 caracteres.")
        for name, minimum, maximum in (("timeout_seconds", 1, 600),
                                       ("context_tokens", 1024, 8192),
                                       ("output_tokens", 128, 2048),
                                       ("gpu_layers", -1, 128)):
            value = getattr(self, name)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"{name} debe ser un entero entre {minimum} y {maximum}.")
        if self.provider == "ollama":
            if "cloud" in self.model.lower():
                raise ValueError("Solo se admiten modelos locales; los modelos cloud están desactivados.")
            if not isinstance(self.base_url, str):
                raise ValueError("base_url debe ser una dirección local.")
            url = urlsplit(self.base_url)
            if (url.scheme != "http" or url.hostname not in ("127.0.0.1", "::1")
                    or url.username is not None or url.password is not None
                    or url.path not in ("", "/") or url.query or url.fragment
                    or url.port is None):
                raise ValueError("Ollama requiere HTTP en 127.0.0.1 o ::1 con puerto explícito.")


def load_ai_config(path: str | Path | None = None) -> AIConfig:
    """Lee una configuración explícita; la ausencia de ruta utiliza valores locales."""
    if path is None:
        return AIConfig()
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    fields = set(AIConfig.__dataclass_fields__)
    if not isinstance(values, dict) or values.keys() - fields:
        raise ValueError("Configuración de IA inválida o con campos desconocidos.")
    return AIConfig(**values)


@dataclass(frozen=True)
class ProviderReply:
    content: str
    model: str
    usage: dict


class ResearchProvider(Protocol):
    """Un futuro adaptador OpenAI podrá cumplir este mismo contrato."""

    def describe(self) -> dict: ...

    def complete(self, messages: list[dict], schema: dict) -> ProviderReply: ...


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError("El proveedor local no puede redirigir peticiones.")


class OllamaProvider:
    """Peticiones solo a loopback, sin proxy, redirecciones ni descarga automática."""

    def __init__(self, config: AIConfig,
                 transport: Callable[[str, str, dict | None], dict] | None = None):
        if config.provider != "ollama":
            raise ValueError("OllamaProvider requiere provider=ollama.")
        self.config = config
        self._transport = transport or self._request
        self._identity: dict | None = None

    def _request(self, method: str, path: str, payload: dict | None) -> dict:
        body = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
        request = Request(self.config.base_url.rstrip("/") + path, data=body,
                          headers={"Content-Type": "application/json"}, method=method)
        try:
            with build_opener(ProxyHandler({}), _NoRedirect()).open(
                    request, timeout=self.config.timeout_seconds) as response:
                raw = response.read(65537)
            if len(raw) > 65536:
                raise ProviderError("La respuesta local supera el tamaño permitido.")
            result = json.loads(raw)
        except HTTPError as error:
            raise ProviderError(f"Ollama respondió con HTTP {error.code}; sin reintento.") from error
        except (URLError, OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ProviderError("No se pudo leer Ollama. Comprueba el servicio local y el modelo.") from error
        if not isinstance(result, dict) or "error" in result:
            raise ProviderError("Respuesta de error o formato inválido de Ollama.")
        return result

    def describe(self) -> dict:
        if self._identity is None:
            response = self._transport("GET", "/api/tags", None)
            models = response.get("models")
            if not isinstance(models, list):
                raise ProviderError("Ollama no devolvió una lista de modelos locales.")
            selected = next((model for model in models if isinstance(model, dict)
                             and model.get("name") == self.config.model), None)
            if selected is None:
                raise ProviderError(f"El modelo {self.config.model} no está descargado. No se descargará automáticamente.")
            if selected.get("remote_host") or selected.get("remote_model"):
                raise ProviderError("El modelo seleccionado remite a un servicio remoto.")
            self._identity = {"provider": "ollama", "model": self.config.model,
                              "model_digest": selected.get("digest"),
                              "base_url": self.config.base_url, "api_cost_usd": "0",
                              "context_tokens": self.config.context_tokens,
                              "output_tokens": self.config.output_tokens,
                              "gpu_layers": self.config.gpu_layers,
                              "timeout_seconds": self.config.timeout_seconds,
                              "think": False, "temperature": 0}
        return dict(self._identity)

    def complete(self, messages: list[dict], schema: dict) -> ProviderReply:
        self.describe()
        response = self._transport("POST", "/api/chat", {
            "model": self.config.model, "messages": messages, "format": schema,
            "stream": False, "think": False, "keep_alive": "2m",
            "options": {"num_ctx": self.config.context_tokens,
                        "num_predict": self.config.output_tokens,
                        "num_gpu": self.config.gpu_layers, "temperature": 0},
        })
        def count(name: str):
            value = response.get(name)
            return value if type(value) is int and value >= 0 else None
        usage = {"input_tokens": count("prompt_eval_count"),
                 "output_tokens": count("eval_count"),
                 "cached_input_tokens": count("prompt_eval_cached_count"),
                 "duration_ns": count("total_duration"), "api_cost_usd": "0"}
        if response.get("done") is not True or response.get("done_reason") != "stop":
            raise ProviderError("Ollama no completó la respuesta; no se aceptan salidas truncadas.", usage)
        message = response.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ProviderError("Ollama no devolvió contenido de texto.", usage)
        if response.get("model") != self.config.model:
            raise ProviderError("Ollama respondió con un modelo distinto al solicitado.", usage)
        return ProviderReply(message["content"], response["model"], usage)


def create_provider(config: AIConfig) -> ResearchProvider:
    if config.provider == "openai":
        raise ProviderError("OpenAI está reservado para una integración futura. Requiere acordar credenciales y presupuesto; no se ha realizado ninguna llamada.")
    return OllamaProvider(config)
