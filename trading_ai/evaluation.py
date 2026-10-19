"""Evalúa una propuesta fijada, sin parámetros alternativos ni consultas de IA."""

import argparse
from datetime import UTC, date, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
from time import monotonic

from trading_ai.data import load_ecb_rates
from trading_ai.experiments import expected_assessment, run_experiment
from trading_ai.holdout import (_code_hashes as _frozen_code_hashes, _json, _policy,
                                _write_exclusive, verify_frozen_proposal)
from trading_ai.research import ROOT, RunJournal


# Un registro compartido por contenido, independiente de la carpeta de salida.
ACCESS_ROOT = ROOT / ".local/evaluation-access"


class EvaluationError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    result = _frozen_code_hashes()
    result["evaluation.py"] = sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def _assessment(result: dict, scope: str) -> dict:
    assessment = expected_assessment(result)
    status = {"supported_in_sample": "met", "not_supported_in_sample": "not_met",
              "inconclusive": "inconclusive"}[assessment["verdict"]]
    return {"criterion_status": status, "return_comparison": assessment["return_comparison"],
            "drawdown_comparison": assessment["drawdown_comparison"], "scope": scope,
            "origin": "python"}


def _report(comparison: dict) -> str:
    def number(value):
        with localcontext(Context(prec=28)):
            return f"{Decimal(value):.6f}"
    def percent(value):
        with localcontext(Context(prec=28)):
            return format(Decimal(value) * 100, "f")
    policy = comparison["policy"]
    sizing = ("una unidad base por entrada" if policy["allocation_fraction"] is None else
              percent(policy["allocation_fraction"]) + " % del efectivo por entrada, costes incluidos")
    labels = {"met": "Criterio cumplido en este bloque", "not_met": "Criterio no cumplido en este bloque",
              "inconclusive": "Resultado inconcluso en este bloque"}
    lines = ["# Trading AI — Evaluación de una propuesta fijada", "",
             f"Par: {policy['pair']}. Capital inicial por bloque: {policy['initial_capital']} en moneda cotizada.",
             f"Coste por compra o venta: {percent(policy['cost_rate'])} %. Tamaño: {sizing}.",
             f"Criterio fijado: `{comparison['proposal']['criterion']}`.",
             f"SHA-256 del registro previo: `{comparison['frozen_sha256']}`.",
             "La propuesta y los controles se mantienen tal como se registraron, aunque no cumplan el criterio.", ""]
    for name, title in (("development", "Desarrollo"), ("evaluation", "Evaluación reservada")):
        block = comparison["blocks"][name]
        result, assessment = block["results"], block["assessment"]
        source = result["source"]
        lines += [f"## {title}", "",
                  f"BCE: {source['first_date']} a {source['last_date']}; {source['observations']} observaciones.",
                  f"SHA-256: `{source['sha256']}`.", "",
                  "| Métrica | Base | Variante |", "|---|---:|---:|"]
        for label, field in (("Estrategia", "strategy"), ("Capital final", "final_equity"),
                             ("Rentabilidad acumulada %", "return_percent"),
                             ("Drawdown máximo %", "max_drawdown_percent"),
                             ("Costes incurridos", "total_costs"), ("Cierres", "closed_trades"),
                             ("Posición abierta", "has_open_position"), ("Entradas rechazadas", "rejected_entries")):
            values = [result["baseline"][field], result["candidate"][field]]
            if field in ("final_equity", "return_percent", "max_drawdown_percent", "total_costs"):
                values = [number(value) for value in values]
            elif field == "has_open_position":
                values = ["Sí" if value else "No" for value in values]
            lines.append(f"| {label} | {values[0]} | {values[1]} |")
        lines += ["", labels[assessment["criterion_status"]] + ".", ""]
    lines += ["## Alcance", "",
              "Cálculos y conclusiones de Python; no se ha consultado IA ni cambiado la propuesta tras evaluar.",
              "Cada bloque empieza con su propio capital, sin posiciones ni señales heredadas; indicadores calculados desde su inicio.",
              "Las posiciones abiertas se valoran sin cierre forzado. Las cuentas no forman una curva continua.",
              "Rentabilidades acumuladas, no anualizadas. Los periodos tienen distinta longitud; no se comparan como rendimientos equivalentes.",
              "El histórico completo ya se exploró en fases anteriores: esta separación no crea evidencia totalmente inédita.",
              "Cumplir un criterio no demuestra rentabilidad ni robustez; no hay selección automática de ganadores.",
              "Con cero cierres en cualquiera de las estrategias, o con ambas métricas iguales, la comparación es inconclusa.",
              "Referencias educativas del BCE y costes hipotéticos; sin operaciones con dinero real.",
              "Este bloque queda registrado como consultado por el flujo, incluso si el cálculo posterior falla.",
              "Peticiones de IA: 0. Coste de API registrado: 0 USD.", ""]
    return "\n".join(lines)


def evaluate_frozen_proposal(frozen_dir: str | Path,
                             output_dir: str | Path = ROOT / ".local/evaluations") -> Path:
    """Una evaluación por SHA-256 del XML; el intento se registra antes del cálculo.

    La marca local no prueba ausencia de consultas fuera de la aplicación ni
    impide que alguien con acceso completo borre registros o prepare otra copia.
    """
    journal = RunJournal(Path(output_dir))
    started = monotonic()
    frozen_dir = Path(frozen_dir).resolve()
    code_hashes = _code_hashes()
    journal.record("evaluation_started", frozen_dir=str(frozen_dir), code_sha256=code_hashes,
                   max_model_requests=0)
    try:
        frozen_raw = (frozen_dir / "frozen.json").read_bytes()
        frozen_hash = sha256(frozen_raw).hexdigest()
        frozen = verify_frozen_proposal(frozen_dir)
        if _json(frozen_raw) != frozen:
            raise ValueError("El registro cambió durante su verificación.")
        split_dir = Path(frozen["split"]["directory"])
        manifest_raw = (split_dir / "manifest.json").read_bytes()
        if sha256(manifest_raw).hexdigest() != frozen["split"]["manifest_sha256"]:
            raise ValueError("El manifiesto cambió durante su verificación.")
        manifest = _json(manifest_raw)
        block = manifest["partitions"]["evaluation"]
        source = split_dir / block["file"]
        policy = _policy(frozen["policy"])
        journal.record("registration_verified", frozen_sha256=frozen_hash,
                       evaluation_sha256=block["sha256"], proposal=frozen["proposal"], policy=frozen["policy"])
        # Creación exclusiva: dos procesos no pueden adquirir el mismo bloque.
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        access_path = ACCESS_ROOT / (block["sha256"] + ".json")
        access = {"schema_version": 1, "marked_at": datetime.now(UTC).isoformat(),
                  "evaluation_sha256": block["sha256"], "frozen_sha256": frozen_hash,
                  "frozen_dir": str(frozen_dir), "split_dir": str(split_dir),
                  "evaluation_run": str(journal.directory.resolve()),
                  "meaning": "Claimed before evaluation; do not treat this block as unseen again."}
        try:
            _write_exclusive(access_path, (json.dumps(access, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        except FileExistsError as error:
            raise ValueError(f"El bloque ya tiene un intento de evaluación registrado: {access_path}. No se recalculará.") from error
        journal.record("evaluation_access_claimed", access_path=str(access_path), **access)
        # Solo después de verificar y marcar el acceso se interpretan estas referencias.
        rates = load_ecb_rates(source, policy.pair)
        if (len(rates) != block["observations"] or str(rates[0][0]) != block["first_date"]
                or str(rates[-1][0]) != block["last_date"]
                or rates[0][0] < date.fromisoformat(manifest["cutoff"])):
            raise ValueError("Las fechas de evaluación no coinciden con el bloque reservado.")
        journal.record("evaluation_requested", data_path=str(source),
                       execution_policy=frozen["execution_policy"])
        evaluation = run_experiment(source, frozen["proposal"], policy)
        journal.save("evaluation_raw.json", evaluation)
        journal.record("evaluation_calculated", result=evaluation)
        expected_source = {"name": "BCE", "sha256": block["sha256"],
                           "first_date": block["first_date"], "last_date": block["last_date"],
                           "observations": block["observations"]}
        if (evaluation["source"] != expected_source or evaluation["policy"] != frozen["policy"]
                or evaluation["proposal"] != frozen["proposal"]):
            raise ValueError("La evaluación no coincide con los datos o parámetros fijados.")
        if (verify_frozen_proposal(frozen_dir) != frozen or _code_hashes() != code_hashes
                or sha256((frozen_dir / "frozen.json").read_bytes()).hexdigest() != frozen_hash):
            raise ValueError("El registro o el código cambiaron durante la evaluación.")
        comparison = {"schema_version": 1, "stage": "evaluation_completed",
                      "frozen_sha256": frozen_hash, "frozen_at": frozen["frozen_at"],
                      "proposal": frozen["proposal"], "policy": frozen["policy"],
                      "execution_policy": frozen["execution_policy"], "code_sha256": code_hashes,
                      "evaluation_access": access,
                      "blocks": {"development": {"results": frozen["development_result"],
                                                  "assessment": _assessment(frozen["development_result"], "development")},
                                 "evaluation": {"results": evaluation,
                                                "assessment": _assessment(evaluation, "held_out_period")}},
                      "model_requests": 0, "api_cost_usd": "0"}
        journal.save("comparison.json", comparison)
        _write_exclusive(journal.directory / "report.md", _report(comparison).encode("utf-8"))
        journal.record("evaluation_completed", assessments={key: value["assessment"] for key, value in comparison["blocks"].items()},
                       comparison_sha256=sha256((journal.directory / "comparison.json").read_bytes()).hexdigest(),
                       elapsed_seconds=round(monotonic() - started, 3), model_requests=0, api_cost_usd="0")
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        journal.record("evaluation_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       elapsed_seconds=round(monotonic() - started, 3), model_requests=0, api_cost_usd="0")
        raise EvaluationError(str(error), journal.directory) from error
    return journal.directory


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — evaluación de propuesta fijada (sin IA)")
    parser.add_argument("--frozen-run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".local/evaluations")
    args = parser.parse_args(argv)
    try:
        directory = evaluate_frozen_proposal(args.frozen_run, args.output_dir)
    except EvaluationError as error:
        parser.exit(1, f"Evaluación detenida: {error}. Registro del intento: {error.directory}\n")
    print(f"Evaluación completada: {directory / 'report.md'}")


if __name__ == "__main__":
    main()
