"""Conversación local acotada; contrato independiente del ciclo de campañas."""

from copy import deepcopy
import json
import re

from trading_ai.ai import AIConfig, OllamaProvider, ProviderError
from trading_ai.conversation_explanation import SCHEMA as EXPLANATION_SCHEMA


CHAT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "answer": {"type": "string", "maxLength": 1200},
        "questions": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 180}},
        "unsupported": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 180}},
        "proposal": {"anyOf": [{"type": "null"}, {
            "type": "object", "additionalProperties": False,
            "properties": {"strategy": {"type": "string", "enum": ["sma", "ema"]},
                           "fast_window": {"type": "integer", "minimum": 1, "maximum": 120},
                           "slow_window": {"type": "integer", "minimum": 2, "maximum": 252},
                           "hypothesis": {"type": "string", "maxLength": 400}},
            "required": ["strategy", "fast_window", "slow_window", "hypothesis"]}]},
    }, "required": ["answer", "questions", "unsupported", "proposal"],
}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def check_context(messages, config=AIConfig(), schema=CHAT_SCHEMA):
    # Una cota conservadora por bytes, contando también esquema y margen de
    # envoltura. No pretende medir tokens antes de que Ollama los comunique.
    if schema != CHAT_SCHEMA and schema != EXPLANATION_SCHEMA:
        raise ValueError("Contrato conversacional incompatible.")
    size = len(encoded({"messages": messages, "schema": schema}))
    limit = config.context_tokens - config.output_tokens - 512
    if size > limit:
        raise ValueError("El contexto elegido supera la cota conservadora. Selecciona menos mensajes; no se recorta el historial.")
    return {"request_bytes": size, "max_request_bytes": limit,
            "context_tokens": config.context_tokens, "output_tokens": config.output_tokens}


class ConversationProvider(OllamaProvider):
    def __init__(self, config=AIConfig(), *, transport=None):
        if config.provider != "ollama" or config.context_tokens > 4096 or config.output_tokens > 384 or config.gpu_layers != 0:
            raise ValueError("La conversación requiere Ollama local en CPU, contexto hasta 4096 y salida hasta 384.")
        self._delegate = transport or self._request
        self._digest = None
        super().__init__(config, transport=self._guard)

    def _guard(self, method, path, payload):
        if method == "POST":
            if path != "/api/chat": raise ProviderError("Ruta de generación no permitida.")
            payload = {**deepcopy(payload), "truncate": False, "shift": False}
        return self._delegate(method, path, payload)

    def describe(self):
        if self._delegate("GET", "/api/version", None).get("version") != "0.40.6":
            raise ProviderError("Versión local no comprobada para rechazar recortes de contexto.")
        self._identity = None
        identity = super().describe()
        digest = identity.get("model_digest")
        if not isinstance(digest, str) or not re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", digest):
            raise ProviderError("El modelo no tiene una huella verificable.")
        if self._digest is not None and digest != self._digest:
            raise ProviderError("La etiqueta del modelo cambió; no se reintenta.")
        self._digest = digest
        return {**identity, "contract": "conversation_v1", "truncate": False, "shift": False}

    def complete(self, messages, schema=CHAT_SCHEMA):
        if schema != CHAT_SCHEMA and schema != EXPLANATION_SCHEMA: raise ProviderError("Contrato conversacional incompatible.")
        check_context(messages, self.config, schema)
        reply = super().complete(messages, schema)
        usage = reply.usage
        inputs, outputs = usage.get("input_tokens"), usage.get("output_tokens")
        if (type(inputs) is not int or type(outputs) is not int or inputs < 1 or outputs < 1
                or outputs > self.config.output_tokens or inputs + outputs > self.config.context_tokens):
            raise ProviderError("Consumo fuera del contrato o desconocido.", usage)
        try: self.describe()
        except ProviderError as error: raise ProviderError(str(error), usage) from error
        return reply
