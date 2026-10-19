"""Bandeja de ideas del investigador: especificaciones declarativas, nunca código ejecutado."""

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import re
from time import monotonic

from trading_ai.ai import ResearchProvider, create_provider, load_ai_config
from trading_ai.research import ROOT, RunJournal, _api_cost, _ask
from trading_ai.robustness import _development


DATA_REQUIREMENTS = ("reference_series", "ohlc", "volume", "intraday", "other")
RESERVED_PARAMETERS = {"pair", "baseline_strategy", "cost_rate", "initial_capital", "allocation_fraction",
                       "capital", "leverage", "position_size", "quantity", "provider", "data_path", "source", "tool", "code"}
IDEA_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 80},
        "hypothesis": {"type": "string", "minLength": 1, "maxLength": 240},
        "entry_rule": {"type": "string", "minLength": 1, "maxLength": 240},
        "exit_rule": {"type": "string", "minLength": 1, "maxLength": 240},
        "parameters": {"type": "array", "maxItems": 6, "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"name": {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,31}$"},
                           "value": {"type": "number", "minimum": -1000000, "maximum": 1000000}},
            "required": ["name", "value"]}},
        "data_requirements": {"type": "object", "additionalProperties": False,
                              "properties": {name: {"type": "boolean"} for name in DATA_REQUIREMENTS},
                              "required": list(DATA_REQUIREMENTS)},
    }, "required": ["title", "hypothesis", "entry_rule", "exit_rule", "parameters", "data_requirements"],
}
DEFAULT_QUESTION = "Propón una hipótesis distinta de variar ventanas de cruces SMA/EMA. Define entrada y salida, sin afirmar resultados no calculados."


class DiscoveryError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def validate_idea(idea: dict) -> None:
    """Valida formato y límites; no demuestra la coherencia financiera de las reglas."""
    if not isinstance(idea, dict) or set(idea) != set(IDEA_SCHEMA["required"]):
        raise ValueError("Idea con campos ausentes o no autorizados.")
    for field, maximum in (("title", 80), ("hypothesis", 240), ("entry_rule", 240), ("exit_rule", 240)):
        text = idea[field]
        if not isinstance(text, str) or not text.strip() or len(text) > maximum:
            raise ValueError(f"{field} requiere texto no vacío de hasta {maximum} caracteres.")
    parameters = idea["parameters"]
    if not isinstance(parameters, list) or len(parameters) > 6:
        raise ValueError("Se admiten hasta seis parámetros declarativos.")
    names = set()
    for parameter in parameters:
        if not isinstance(parameter, dict) or set(parameter) != {"name", "value"}:
            raise ValueError("Parámetro con campos no autorizados.")
        name, value = parameter["name"], parameter["value"]
        if not isinstance(name, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,31}", name) is None or name in names:
            raise ValueError("Nombres de parámetros inválidos o repetidos.")
        if name in RESERVED_PARAMETERS:
            raise ValueError("Un parámetro de estrategia no puede sustituir los controles del simulador.")
        if type(value) not in (int, float) or not -1000000 <= value <= 1000000:
            raise ValueError("El valor del parámetro debe ser numérico, finito y acotado.")
        names.add(name)
    requirements = idea["data_requirements"]
    if (not isinstance(requirements, dict) or set(requirements) != set(DATA_REQUIREMENTS)
            or any(type(value) is not bool for value in requirements.values())
            or not any(requirements.values())):
        raise ValueError("Los requisitos de datos deben declarar sí/no para cada tipo y al menos uno necesario.")


def discover_idea(provider: ResearchProvider, frozen_dir: str | Path, *,
                  question: str = DEFAULT_QUESTION,
                  output_dir: str | Path = ROOT / ".local/discovery") -> Path:
    """Una propuesta por llamada; no hay backtests, descargas ni cambio de proveedor."""
    if not isinstance(question, str) or not question.strip() or len(question) > 800:
        raise ValueError("La pregunta debe tener entre 1 y 800 caracteres.")
    journal = RunJournal(Path(output_dir))
    started = monotonic()
    usages: list[dict] = []
    journal.record("discovery_started", frozen_dir=str(Path(frozen_dir).resolve()), max_model_requests=1,
                   code_sha256={name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                for name in ("discovery.py", "robustness.py", "ai.py", "research.py")})
    try:
        frozen, reference, _ = _development(Path(frozen_dir).resolve())
        context = {"pair": frozen["policy"]["pair"], "data": frozen["development_result"]["source"],
                   "available_inputs": ["reference_series"],
                   "execution_constraints": {"direction": "long_only", "execution": "next_observation",
                                             "controls": frozen["policy"]},
                   "implemented_tools": ["sma_crossover", "ema_crossover"],
                   "context_limit": "Historical educational ECB references; no OHLC, volume or executable prices."}
        identity = provider.describe()
        journal.record("provider_ready", idea_schema_version=2, **identity)
        idea = _ask(provider, journal, "new_strategy_idea", [
            {"role": "system", "content": "Eres un investigador educativo. Propón una sola idea en JSON conforme al esquema. "
             "Título e hipótesis breves; entrada y salida de como máximo 20 palabras cada una. "
             "Usa como máximo tres parámetros simples. Describe reglas de compra y cierre, sin cortos ni apalancamiento. "
             "No generes código, no cambies límites del simulador ni inventes métricas. "
             "Los datos son referencias educativas, no precios negociables. Declara cualquier necesidad de OHLC, volumen u otros datos. "
             "data_requirements es un objeto: indica true o false en cada tipo, sin listas ni tipos repetidos. "
             "La idea quedará pendiente de implementación y no se considerará mejor por proponerla."},
            {"role": "user", "content": question + "\nContexto de desarrollo: " + json.dumps(context, ensure_ascii=False)},
        ], IDEA_SCHEMA, usages)
        validate_idea(idea)
        # Siempre pendiente: ni el nombre ni el texto autorizan una herramienta.
        missing = [name for name, required in idea["data_requirements"].items() if required and name != "reference_series"]
        canonical = json.dumps(idea, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")
        record = {"schema_version": 2, "idea_id": sha256(canonical).hexdigest(),
                  "status": "needs_data_and_tool_mapping" if missing else "pending_tool_mapping",
                  "executable": False, "proposal": idea, "missing_declared_inputs": missing,
                  "validation_scope": "format_and_bounds_only_not_strategy_correctness",
                  "reference": reference, "development_context": context, "provider": identity,
                  "usage": usages, "api_cost_usd": _api_cost(usages), "model_requests": len(usages),
                  "calculated_results": None}
        journal.save("idea.json", record)
        journal.record("idea_queued", idea_id=record["idea_id"], status=record["status"], executable=False,
                       model_requests=len(usages), usage=usages, api_cost_usd=_api_cost(usages),
                       elapsed_seconds=round(monotonic() - started, 3))
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        journal.record("discovery_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       usage=usages, api_cost_usd=_api_cost(usages),
                       elapsed_seconds=round(monotonic() - started, 3))
        raise DiscoveryError(str(error), journal.directory) from error
    return journal.directory


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — ideas de estrategia pendientes, sin ejecución")
    parser.add_argument("--frozen-run", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--provider", choices=("ollama", "openai"))
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".local/discovery")
    args = parser.parse_args(argv)
    try:
        personal = ROOT / "config/ai.local.json"
        config = load_ai_config(args.config or (personal if personal.exists() else None))
        if args.provider:
            config = replace(config, provider=args.provider)
        provider = create_provider(config)
        directory = discover_idea(provider, args.frozen_run, question=args.question, output_dir=args.output_dir)
    except DiscoveryError as error:
        parser.exit(1, f"Idea detenida: {error}. Registro: {error.directory}\n")
    except (ValueError, TypeError, OSError) as error:
        parser.exit(1, f"No se pudo preparar el investigador de ideas: {error}\n")
    print(f"Idea registrada como pendiente, sin calcular resultados: {directory / 'idea.json'}")


if __name__ == "__main__":
    main()
