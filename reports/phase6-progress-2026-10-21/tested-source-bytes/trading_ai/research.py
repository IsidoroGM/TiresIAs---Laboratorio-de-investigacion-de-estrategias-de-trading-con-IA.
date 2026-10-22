"""Primer investigador local: propone, solicita un experimento y contrasta su análisis.

Ejecutar: python -m trading_ai.research --check
OpenAI queda reservado; no hay llamadas de pago ni fallback automático.
"""

import argparse
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import os
from pathlib import Path
from time import monotonic
from uuid import uuid4

from trading_ai.ai import (ProviderError, ResearchProvider, create_provider,
                           load_ai_config)
from trading_ai.data import SUPPORTED_PAIRS
from trading_ai.experiments import (ASSESSMENT_SCHEMA, PROPOSAL_SCHEMA, ExperimentPolicy,
                                    expected_assessment, run_experiment, strategies_without_closed_trades,
                                    validate_assessment, validate_proposal)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data/raw/ecb-eurofxref-hist-2026-10-18.xml"
DEFAULT_QUESTION = "Propón una variante de medias móviles y comprueba si satisface uno de los criterios permitidos."
CRITERION_RULES = (
    "higher_return_without_more_drawdown: rentabilidad estrictamente mayor y drawdown no mayor. "
    "lower_drawdown_without_lower_return: drawdown estrictamente menor y rentabilidad no menor. "
    "Si cualquiera de las dos estrategias no tiene cierres, o ambas métricas empatan, "
    "el veredicto es inconclusive. Si cumple el criterio, supported_in_sample; "
    "si no lo cumple, not_supported_in_sample. Compara siempre variante frente a base."
)


class ResearchError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


class RunJournal:
    """JSONL duradero: un registro nuevo por ejecución, sin sobrescribir anteriores."""

    def __init__(self, parent: Path):
        self.directory = parent / uuid4().hex
        self.directory.mkdir(parents=True, exist_ok=False)
        self.path = self.directory / "events.jsonl"
        self.path.touch(exist_ok=False)

    def record(self, event: str, **data) -> None:
        item = {"schema_version": 1, "at": datetime.now(UTC).isoformat(),
                "event": event, "data": data}
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def save(self, name: str, data: dict) -> None:
        with (self.directory / name).open("x", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.write("\n")


def _engine_hashes() -> dict:
    return {name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in ("data.py", "indicators.py", "strategies.py", "backtesting.py",
                         "metrics.py", "experiments.py", "ai.py", "research.py")}


def _ask(provider: ResearchProvider, journal: RunJournal, stage: str,
         messages: list[dict], schema: dict, usages: list[dict]) -> dict:
    journal.record("model_request", stage=stage, messages=messages, schema=schema)
    try:
        reply = provider.complete(messages, schema)
    except ProviderError as error:
        if error.usage is not None:
            usages.append(error.usage)
        journal.record("model_error", stage=stage, usage=error.usage)
        raise
    usages.append(reply.usage)
    # Registrar consumo y respuesta ANTES de interpretar el JSON o validar sus cifras.
    journal.record("model_response", stage=stage, model=reply.model,
                   content=reply.content, usage=reply.usage)
    result = json.loads(reply.content)
    if not isinstance(result, dict):
        raise ValueError("La IA debe devolver un objeto JSON.")
    return result


def _api_cost(usages: list[dict]) -> str | None:
    """No convertir la ausencia de costes de un futuro proveedor en gasto cero."""
    try:
        costs = [Decimal(usage["api_cost_usd"]) for usage in usages]
    except (KeyError, TypeError, InvalidOperation):
        return None
    if not costs or any(not cost.is_finite() or cost < 0 for cost in costs):
        return None
    with localcontext(Context(prec=28)):
        return str(sum(costs, Decimal("0")))


def _report(result: dict, assessment: dict, identity: dict, usages: list[dict], origin: dict) -> str:
    labels = {"supported_in_sample": "Hipótesis apoyada en esta muestra",
              "not_supported_in_sample": "Hipótesis no apoyada en esta muestra",
              "inconclusive": "Resultado inconcluso"}
    criterion_labels = {"higher_return_without_more_drawdown": "Mayor rentabilidad sin aumentar el drawdown",
                        "lower_drawdown_without_lower_return": "Menor drawdown sin reducir la rentabilidad"}
    def number(value):
        with localcontext(Context(prec=28)):
            return f"{Decimal(value):.6f}"
    def percent(value):
        with localcontext(Context(prec=28)):
            return format(Decimal(value) * 100, "f")
    policy = result["policy"]
    sizing = ("una unidad base por entrada" if policy["allocation_fraction"] is None else
              percent(policy["allocation_fraction"]) + " % del efectivo por entrada, costes incluidos")
    lines = ["# Trading AI — Investigación local", "",
             f"Proveedor: {identity['provider']}. Modelo: {identity['model']}.",
             f"Experimento: `{result['experiment_id']}`.",
             f"Fuente: BCE, {result['source']['first_date']} a {result['source']['last_date']}.",
             f"SHA-256: `{result['source']['sha256']}`.", "",
             f"Par: {policy['pair']}. Capital inicial: {policy['initial_capital']} en moneda cotizada.",
             f"Coste por compra o venta: {percent(policy['cost_rate'])} %. Tamaño: {sizing}.", "",
             "## Propuesta de la IA (pendiente de contrastar al formularse)", "",
             result["proposal"]["hypothesis"].replace("\n", " "), "",
             f"Criterio registrado: {criterion_labels[result['proposal']['criterion']]}.", "",
             "## Resultados calculados por Python", "",
             "| Métrica | Base | Variante |", "|---|---:|---:|"]
    for title, field in (("Estrategia", "strategy"), ("Moneda", "quote_currency"),
                         ("Capital final", "final_equity"), ("Rentabilidad acumulada %", "return_percent"),
                         ("Drawdown máximo %", "max_drawdown_percent"), ("Costes incurridos", "total_costs"),
                         ("Cierres", "closed_trades"), ("Posición abierta", "has_open_position"),
                         ("Entradas rechazadas", "rejected_entries")):
        values = [result["baseline"][field], result["candidate"][field]]
        if field in ("final_equity", "return_percent", "max_drawdown_percent", "total_costs"):
            values = [number(value) for value in values]
        elif field == "has_open_position":
            values = ["Sí" if value else "No" for value in values]
        lines.append(f"| {title} | {values[0]} | {values[1]} |")
    cost = _api_cost(usages)
    cost_label = "no disponible" if cost is None else cost + " USD"
    if origin["source"] == "python":
        names = {"baseline": "la base", "candidate": "la variante"}
        missing = " y ".join(names[name] for name in origin["strategies_without_closed_trades"])
        explanation = ["Origen de la conclusión: Python (control previo).",
                       f"Motivo: sin operaciones cerradas en {missing}. La comparación se considera inconclusa.",
                       "No se ha solicitado un análisis a la IA para este experimento.",
                       "Cero cierres no excluye posiciones abiertas; las métricas calculadas se conservan."]
    else:
        explanation = ["Origen de la conclusión: IA, verificada por Python.",
                       "El análisis estructurado de la IA coincide con las métricas y el criterio registrado."]
    lines += ["", "## Conclusión contrastada", "", labels[assessment["verdict"]] + ".",
              *explanation,
              "Las cifras de esta tabla proceden del motor; no se extraen del texto del modelo.",
              "Solo se estudia la muestra histórica. No hay validación fuera de muestra ni selección automática de ganadores.",
              "Referencias educativas del BCE, costes hipotéticos, cuentas virtuales y ejecución en la siguiente observación.",
              "", f"Peticiones de IA: {len(usages)}. Coste de API registrado: {cost_label}.", ""]
    return "\n".join(lines)


def run_research(provider: ResearchProvider, *, source: str | Path = DEFAULT_DATA,
                 policy: ExperimentPolicy = ExperimentPolicy(),
                 question: str = DEFAULT_QUESTION, output_dir: str | Path = ROOT / ".local/research") -> Path:
    if not isinstance(question, str) or not question.strip() or len(question) > 800:
        raise ValueError("La pregunta debe tener entre 1 y 800 caracteres.")
    journal = RunJournal(Path(output_dir))
    started = monotonic()
    usages: list[dict] = []
    journal.record("run_started", experiment_id=journal.directory.name,
                   policy=policy.parameters(), engine_sha256=_engine_hashes(),
                   data_path=str(Path(source).resolve()), max_model_requests=2)
    try:
        identity = provider.describe()
        journal.record("provider_ready", **identity)
        proposal = _ask(provider, journal, "proposal", [
            {"role": "system", "content": "Eres un investigador educativo. Devuelve solo JSON conforme al esquema. "
             "Solicita exactamente una llamada a run_experiment, con una variante distinta de la base. "
             "Formula una hipótesis, sin afirmar resultados aún no calculados. No puedes cambiar los controles. " + CRITERION_RULES},
            {"role": "user", "content": question + "\nControles y base: " + json.dumps(policy.parameters())},
        ], PROPOSAL_SCHEMA, usages)
        journal.record("proposal", proposal=proposal)
        validate_proposal(proposal, policy)
        journal.record("tool_requested", tool="run_experiment", arguments=proposal["arguments"])
        result = run_experiment(source, proposal, policy)
        result["experiment_id"] = journal.directory.name
        journal.save("results.json", result)
        journal.record("tool_result", result=result)
        missing = strategies_without_closed_trades(result)
        journal.record("assessment_precheck", passed=not missing,
                       closed_trades={name: result[name]["closed_trades"] for name in ("baseline", "candidate")},
                       strategies_without_closed_trades=missing)
        if missing:
            assessment = expected_assessment(result)
            origin = {"source": "python", "reason": "no_closed_trades",
                      "strategies_without_closed_trades": missing}
            journal.record("assessment_skipped", **origin)
        else:
            assessment = _ask(provider, journal, "assessment", [
                {"role": "system", "content": "Analiza únicamente los resultados calculados adjuntos. Devuelve solo JSON. "
                 "return_comparison y drawdown_comparison usan higher/lower/equal para la variante frente a la base. "
                 "scope siempre es historical_sample_only. " + CRITERION_RULES},
                {"role": "user", "content": json.dumps(result, ensure_ascii=False)},
            ], ASSESSMENT_SCHEMA, usages)
            origin = {"source": "model", "verified_by": "python"}
        validate_assessment(assessment, result)
        journal.save("analysis.json", assessment)
        journal.save("analysis_origin.json", origin)
        with (journal.directory / "report.md").open("x", encoding="utf-8") as stream:
            stream.write(_report(result, assessment, identity, usages, origin))
        journal.record("run_completed", assessment=assessment, analysis_origin=origin,
                       model_requests=len(usages), usage=usages,
                       elapsed_seconds=round(monotonic() - started, 3), api_cost_usd=_api_cost(usages))
    except (ValueError, TypeError, KeyError, OSError) as error:
        journal.record("run_failed", error_type=type(error).__name__, message=str(error)[:500],
                       usage=usages, elapsed_seconds=round(monotonic() - started, 3))
        raise ResearchError(str(error), journal.directory) from error
    return journal.directory


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — investigador local (FASE 3)")
    parser.add_argument("--check", action="store_true", help="Comprobar proveedor/modelo sin generar texto")
    parser.add_argument("--config", type=Path, help="Configuración JSON; por defecto config/ai.local.json si existe")
    parser.add_argument("--provider", choices=("ollama", "openai"), help="OpenAI es una reserva desactivada")
    parser.add_argument("--model", help="Modelo ya descargado; no se descarga automáticamente")
    parser.add_argument("--pair", choices=SUPPORTED_PAIRS, default="EUR/USD")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".local/research")
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    args = parser.parse_args(argv)
    try:
        personal_config = ROOT / "config/ai.local.json"
        config_path = args.config or (personal_config if personal_config.exists() else None)
        config = load_ai_config(config_path)
        if args.provider:
            config = replace(config, provider=args.provider)
        if args.model:
            config = replace(config, model=args.model)
        provider = create_provider(config)
        if args.check:
            print(json.dumps(provider.describe(), ensure_ascii=False, indent=2))
            return
        directory = run_research(provider, source=args.data, policy=ExperimentPolicy(pair=args.pair),
                                 question=args.question, output_dir=args.output_dir)
    except ResearchError as error:
        parser.exit(1, f"Investigación detenida: {error}. Registro: {error.directory}\n")
    except (ValueError, TypeError, OSError) as error:
        parser.exit(1, f"No se pudo preparar el investigador: {error}\n")
    print(f"Investigación contrastada: {directory / 'report.md'}")


if __name__ == "__main__":
    main()
