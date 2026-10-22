"""Adaptador compacto para Ollama 0.40.6: solicita error en vez de recortar contexto.

Contrato contrastado con api/types.go y server/routes.go de la etiqueta v0.40.6.
No modifica el proveedor histórico, descarga modelos o inicia servicios.
"""

from copy import deepcopy
import re

from trading_ai.ai import AIConfig, OllamaProvider, ProviderError, ProviderReply
from trading_ai.rule_planning import _canonical
from trading_ai.structured_draft import DRAFT_SCHEMA
from trading_ai.structured_draft_request import MAX_REQUEST_BYTES


SUPPORTED_SERVER_VERSION = "0.40.6"


class CompactOllamaProvider(OllamaProvider):
    def __init__(self, config: AIConfig = AIConfig(), *, transport=None):
        if (config.provider != "ollama" or config.context_tokens > 4096
                or config.output_tokens > 384 or config.gpu_layers != 0):
            raise ValueError("El adaptador compacto solo admite Ollama local, CPU, contexto hasta 4096 y salida hasta 384.")
        self._delegate = transport or self._request
        self._bound_digest = None
        self.metadata_requests = 0
        self._model_attempted = False
        self.last_response = None
        super().__init__(config, transport=self._guarded_transport)

    def _metadata(self, path):
        self.metadata_requests += 1
        return self._delegate("GET", path, None)

    def _guarded_transport(self, method, path, payload):
        if method == "GET" and path == "/api/tags":
            return self._metadata(path)
        if method != "POST" or path != "/api/chat":
            raise ProviderError("Ruta no admitida por el adaptador compacto.")
        body = {**deepcopy(payload), "truncate": False, "shift": False}
        self._model_attempted = True
        response = self._delegate(method, path, body)
        self.last_response = deepcopy(response)
        return response

    def describe(self) -> dict:
        version = self._metadata("/api/version")
        if not isinstance(version, dict) or version.get("version") != SUPPORTED_SERVER_VERSION:
            raise ProviderError("Versión de Ollama no comprobada para impedir recortes; no se enviará el borrador.")
        # Refrescar la etiqueta en cada comprobación: no aceptar una sustitución
        # silenciosa del modelo entre la preparación y la respuesta.
        self._identity = None
        identity = super().describe()
        digest = identity["model_digest"]
        if not isinstance(digest, str) or re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", digest) is None:
            raise ProviderError("Ollama no identifica el modelo local con un digest verificable.")
        if self._bound_digest is not None and digest != self._bound_digest:
            raise ProviderError("La etiqueta local cambió de modelo; se detiene sin reintento.")
        self._bound_digest = digest
        return {**identity, "server_version": SUPPORTED_SERVER_VERSION,
                "context_policy": "reject_overflow_no_truncate_no_shift", "truncate": False, "shift": False,
                "prompt_tokens_before_request": None}

    def complete(self, messages: list[dict], schema: dict) -> ProviderReply:
        self._model_attempted = False
        self.last_response = None
        metadata_start, used = self.metadata_requests, None
        try:
            if (_canonical(schema) != _canonical(DRAFT_SCHEMA) or not isinstance(messages, list) or len(messages) != 2
                    or [item.get("role") for item in messages if isinstance(item, dict)] != ["system", "user"]
                    or any(set(item) != {"role", "content"} or not isinstance(item["content"], str)
                           or not item["content"].strip() for item in messages)
                    or len(_canonical({"messages": messages, "schema": schema})) > MAX_REQUEST_BYTES):
                raise ProviderError("Solo se acepta la petición compacta acotada con mensajes de sistema y usuario.")
            reply = super().complete(messages, schema)
            used = dict(reply.usage)
            inputs, outputs = used.get("input_tokens"), used.get("output_tokens")
            if (type(inputs) is not int or inputs < 1 or type(outputs) is not int or outputs < 1
                    or outputs > self.config.output_tokens or inputs + outputs > self.config.context_tokens):
                raise ProviderError("El proveedor no permite comprobar el consumo dentro del límite de contexto.", used)
            self.describe()
            return ProviderReply(reply.content, reply.model,
                                 {**used, "metadata_request_attempts": self.metadata_requests - metadata_start})
        except ProviderError as error:
            usage = error.usage if error.usage is not None else used
            if usage is None:
                count = None if self._model_attempted else 0
                usage = {"input_tokens": count, "output_tokens": count, "api_cost_usd": "0"}
            raise ProviderError(str(error), {**usage, "metadata_request_attempts": self.metadata_requests - metadata_start}) from error
