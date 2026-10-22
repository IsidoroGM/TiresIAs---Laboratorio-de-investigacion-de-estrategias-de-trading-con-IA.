"""Ejecutor único de planes revisados: dos backtests como máximo y ninguna consulta de IA."""

import argparse
from dataclasses import asdict
from datetime import date
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
from time import monotonic

from trading_ai.backtesting import run_backtest
from trading_ai.data import load_ecb_rates
from trading_ai.experiments import expected_assessment
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _policy, _write_exclusive
from trading_ai.metrics import calculate_metrics
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _canonical, _code_hashes as _planning_hashes, verify_rule_plan
from trading_ai.rules import compile_rule_strategy
from trading_ai.strategies import create_strategy


ACCESS_ROOT = ROOT / ".local/rule-execution-access"


class ExecutionError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_planning_hashes(), "rule_execution.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _registered(directory: Path, frozen_dir: Path) -> tuple[dict, dict]:
    plan = verify_rule_plan(directory, frozen_dir)
    hashes = {name: sha256((directory / name).read_bytes()).hexdigest()
              for name in ("plan.json", "plan.json.sha256", "events.jsonl", "development.xml")}
    if hashes["development.xml"] != plan["data"]["sha256"]:
        raise ValueError("Los datos no coinciden con el plan verificado.")
    return plan, {"directory": str(directory), "sha256": hashes}


def _identity(plan: dict) -> dict:
    # El nombre técnico y el criterio no cambian los cálculos: tampoco liberan otro intento.
    spec = {key: value for key, value in plan["candidate"]["spec"].items() if key != "name"}
    return {"schema_version": 1, "protocol": "rule_calculation_identity_v1", "candidate": spec,
            "baseline": plan["baseline"], "policy": plan["policy"], "data_sha256": plan["data"]["sha256"],
            "execution_policy": plan["execution_policy"], "execution_timing": plan["execution_timing"],
            "direction": plan["direction"]}


def _jsonable(value):
    def encode(item):
        if isinstance(item, Decimal):
            return str(item)
        if isinstance(item, date):
            return item.isoformat()
        raise TypeError("Tipo no autorizado en el resultado del motor.")
    return json.loads(json.dumps(value, default=encode, allow_nan=False))


def _calculate(rates: tuple, strategy, policy) -> dict:
    signals = tuple(strategy.generate_signals(tuple(value for _, value in rates)))
    result = run_backtest(rates, signals, policy.pair, cost_rate=policy.cost_rate,
                          initial_capital=policy.initial_capital, allocation_fraction=policy.allocation_fraction)
    metrics = calculate_metrics(result)
    with localcontext(Context(prec=28)):
        total_return = (result.final_equity - result.initial_capital) / result.initial_capital * 100
    summary = {"strategy": strategy.name, "quote_currency": result.quote_currency,
               "final_equity": str(result.final_equity), "return_percent": str(total_return),
               "max_drawdown_percent": str(result.max_drawdown_percent), "total_costs": str(result.total_costs),
               "closed_trades": metrics.total_trades, "has_open_position": metrics.has_open_position,
               "rejected_entries": result.rejected_entries}
    return {"summary": summary, "backtest": _jsonable(asdict(result)),
            "signals_sha256": sha256(_canonical([signal.value for signal in signals])).hexdigest()}


def _assessment(result: dict) -> dict:
    assessment = expected_assessment(result)
    return {"criterion_status": {"supported_in_sample": "met", "not_supported_in_sample": "not_met",
                                 "inconclusive": "inconclusive"}[assessment["verdict"]],
            "return_comparison": assessment["return_comparison"], "drawdown_comparison": assessment["drawdown_comparison"],
            "scope": "known_development_history_only", "origin": "python"}


def _report(result: dict) -> str:
    sizing = ("una unidad base por entrada" if result["policy"]["allocation_fraction"] is None else
              "fracción del efectivo por entrada: " + result["policy"]["allocation_fraction"])
    lines = ["# Trading AI — Experimento de reglas revisadas", "",
             f"Identidad del cálculo: `{result['calculation_id']}`.",
             f"Plan SHA-256: `{result['plan']['sha256']['plan.json']}`.",
             f"Datos BCE: {result['data']['first_date']} a {result['data']['last_date']}; "
             f"{result['data']['observations']} observaciones. Par: {result['policy']['pair']}.",
             f"Datos SHA-256: `{result['data']['sha256']}`.",
             f"Capital inicial por cuenta: {result['policy']['initial_capital']}; "
             f"coste proporcional por ejecución: {result['policy']['cost_rate']}; " + sizing + ".",
             f"Criterio fijado: `{result['proposal']['criterion']}`.", "",
             "| Métrica | Base | Candidata |", "|---|---:|---:|"]
    for label, field in (("Estrategia", "strategy"), ("Capital final", "final_equity"),
                         ("Rentabilidad acumulada %", "return_percent"), ("Drawdown máximo %", "max_drawdown_percent"),
                         ("Costes incurridos", "total_costs"), ("Cierres", "closed_trades"),
                         ("Posición abierta", "has_open_position"), ("Entradas rechazadas", "rejected_entries")):
        lines.append(f"| {label} | {result['baseline'][field]} | {result['candidate'][field]} |")
    lines += ["", f"Estado del criterio: `{result['assessment']['criterion_status']}`. Calculado por Python.", "",
              "Dos cuentas independientes, con el mismo capital, costes y tamaño; ejecución en la siguiente observación.",
              "Las posiciones abiertas se valoran sin cierre forzado. Cero cierres o ambas métricas iguales: inconcluso.",
              "Histórico de desarrollo ya conocido: no es evidencia inédita ni prueba de una estrategia mejor o robusta.",
              "La revisión técnica es una declaración, no una prueba automática de equivalencia de significado.",
              "Referencias educativas, costes hipotéticos y dinero virtual; sin operaciones reales.",
              "El intento queda consumido aunque falle una comprobación posterior; no hay reintentos automáticos.",
              "Solicitudes de IA: 0. Coste de API: 0 USD.", ""]
    return "\n".join(lines)


def execute_rule_plan(plan_dir: str | Path, frozen_dir: str | Path, *,
                       output_dir: str | Path = ROOT / ".local/rule-executions") -> Path:
    directory, frozen_dir = Path(plan_dir).resolve(), Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir))
    started = monotonic()
    reserved = {"baseline": 0, "candidate": 0}
    completed = []
    claimed = False
    journal.record("execution_started", plan_dir=str(directory), frozen_dir=str(frozen_dir),
                   model_requests=0, api_cost_usd="0")
    try:
        code_hashes = _code_hashes()
        plan, origin = _registered(directory, frozen_dir)
        identity = _identity(plan)
        calculation_id = sha256(_canonical(identity)).hexdigest()
        policy = _policy(plan["policy"])
        base = plan["baseline"]
        strategies = (("baseline", create_strategy(base["strategy"], base["fast_window"], base["slow_window"])),
                      ("candidate", compile_rule_strategy(plan["candidate"]["spec"])))
        access = {"schema_version": 1, "calculation_id": calculation_id, "identity": identity,
                  "plan": origin, "execution_run": str(journal.directory.resolve()), "budget": plan["budget"],
                  "code_sha256": code_hashes, "state": "attempt_reserved_no_automatic_retry"}
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        access_path = ACCESS_ROOT / (calculation_id + ".json")
        try:
            _write_exclusive(access_path, (json.dumps(access, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        except FileExistsError as error:
            raise ValueError("Estos cálculos ya tienen un intento reservado; no se repetirán: " + str(access_path)) from error
        claimed = True
        journal.record("execution_access_claimed", access_path=str(access_path), access=access)
        # Copia estable para ambos cálculos; no se ejecuta directamente sobre una ruta mutable del plan.
        content = (directory / "development.xml").read_bytes()
        if sha256(content).hexdigest() != plan["data"]["sha256"]:
            raise ValueError("Los datos cambiaron antes de cargarlos.")
        snapshot = journal.directory / "development.xml"
        _write_exclusive(snapshot, content)
        rates = tuple(load_ecb_rates(snapshot, policy.pair))
        if (sha256(snapshot.read_bytes()).hexdigest() != plan["data"]["sha256"]
                or len(rates) != plan["data"]["observations"] or not rates
                or rates[0][0].isoformat() != plan["data"]["first_date"]
                or rates[-1][0].isoformat() != plan["data"]["last_date"]):
            raise ValueError("Las observaciones no coinciden con el desarrollo fijado.")

        def unchanged():
            current, current_origin = _registered(directory, frozen_dir)
            if (_canonical(current) != _canonical(plan) or current_origin != origin or _code_hashes() != code_hashes
                    or snapshot.read_bytes() != content or access_path.read_bytes() !=
                    (json.dumps(access, ensure_ascii=False, indent=2) + "\n").encode("utf-8")):
                raise ValueError("El plan, las fuentes, el código o la reserva cambiaron durante la ejecución.")

        calculated = {}
        for role, strategy in strategies:
            unchanged()
            if reserved[role] or plan["budget"][role + "_backtests"] != 1 or sum(reserved.values()) >= 2:
                raise ValueError("Presupuesto de simulaciones agotado o incompatible.")
            reserved[role] += 1
            journal.record("backtest_reserved", role=role, reserved_backtests=dict(reserved), strategy=strategy.name)
            raw = _calculate(rates, strategy, policy)
            journal.save(role + ".json", raw)
            completed.append(role)
            calculated[role] = raw["summary"]
            journal.record("backtest_calculated", role=role, summary=raw["summary"],
                           sha256=sha256((journal.directory / (role + ".json")).read_bytes()).hexdigest())
        unchanged()
        result = {"schema_version": 1, "stage": "execution_completed", "calculation_id": calculation_id,
                  "identity": identity, "plan": origin, "data": plan["data"], "policy": plan["policy"],
                  "proposal": {"idea_id": plan["idea_id"], "spec_sha256": plan["candidate"]["spec_sha256"],
                               "criterion": plan["criterion"]},
                  **calculated, "budget": plan["budget"], "reserved_backtests": reserved,
                  "completed_backtests": list(completed), "code_sha256": code_hashes,
                  "artifacts_sha256": {name: sha256((journal.directory / name).read_bytes()).hexdigest()
                                       for name in ("baseline.json", "candidate.json", "development.xml")},
                  "model_requests": 0, "usage": [], "api_cost_usd": "0"}
        result["assessment"] = _assessment(result)
        journal.save("results.json", result)
        _write_exclusive(journal.directory / "report.md", _report(result).encode("utf-8"))
        journal.record("execution_completed", results_sha256=sha256((journal.directory / "results.json").read_bytes()).hexdigest(),
                       report_sha256=sha256((journal.directory / "report.md").read_bytes()).hexdigest(),
                       access_sha256=sha256(access_path.read_bytes()).hexdigest(),
                       assessment=result["assessment"], reserved_backtests=dict(reserved), completed_backtests=completed,
                       elapsed_seconds=round(monotonic() - started, 3), model_requests=0, api_cost_usd="0")
    except Exception as error:
        # Incluye fallos inesperados del motor. Una reserva previa nunca se borra ni se reintenta.
        journal.record("execution_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       access_claimed=claimed, reserved_backtests=dict(reserved), completed_backtests=completed,
                       elapsed_seconds=round(monotonic() - started, 3), model_requests=0, api_cost_usd="0")
        raise ExecutionError(str(error), journal.directory) from error
    return journal.directory


def verify_rule_execution(run_dir: str | Path, frozen_dir: str | Path) -> dict:
    """Lectura verificada, sin recalcular ni consumir otro intento."""
    directory, frozen_dir = Path(run_dir).resolve(), Path(frozen_dir).resolve()
    raw = _read(directory / "results.json", 262144)
    result = _strict_json(raw)
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 4 * 1024 * 1024).splitlines()]
    if (not events or events[-1]["event"] != "execution_completed"
            or events[-1]["data"]["results_sha256"] != sha256(raw).hexdigest()
            or result["stage"] != "execution_completed"):
        raise ValueError("El resultado no tiene un cierre completo verificable.")
    closed = events[-1]["data"]
    plan, origin = _registered(Path(result["plan"]["directory"]), frozen_dir)
    identity = _identity(plan)
    calculation_id = sha256(_canonical(identity)).hexdigest()
    expected = {"schema_version": 1, "stage": "execution_completed", "calculation_id": calculation_id,
                "identity": identity, "plan": origin, "data": plan["data"], "policy": plan["policy"],
                "proposal": {"idea_id": plan["idea_id"], "spec_sha256": plan["candidate"]["spec_sha256"],
                             "criterion": plan["criterion"]}, "budget": plan["budget"],
                "reserved_backtests": {"baseline": 1, "candidate": 1}, "completed_backtests": ["baseline", "candidate"],
                "code_sha256": _code_hashes(), "model_requests": 0, "usage": [], "api_cost_usd": "0"}
    if _canonical({key: result[key] for key in expected}) != _canonical(expected):
        raise ValueError("El resultado no coincide con el plan, el código o el presupuesto.")
    if set(result["artifacts_sha256"]) != {"baseline.json", "candidate.json", "development.xml"}:
        raise ValueError("Archivos de resultados incompletos o no autorizados.")
    for name, checksum in result["artifacts_sha256"].items():
        if sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() != checksum:
            raise ValueError("Un archivo calculado ha cambiado: " + name)
    if (result["artifacts_sha256"]["development.xml"] != plan["data"]["sha256"]
            or result["assessment"] != _assessment(result)
            or sha256(_read(directory / "report.md", 65536)).hexdigest() != closed["report_sha256"]):
        raise ValueError("El informe, los datos o la conclusión han cambiado.")
    for role in ("baseline", "candidate"):
        ledger = _strict_json(_read(directory / (role + ".json"), 32 * 1024 * 1024))
        if ledger["summary"] != result[role]:
            raise ValueError("El resumen no coincide con el archivo calculado.")
    access_raw = _read(ACCESS_ROOT / (calculation_id + ".json"), 262144)
    access = _strict_json(access_raw)
    if (sha256(access_raw).hexdigest() != closed["access_sha256"] or access["identity"] != identity
            or access["plan"] != origin or access["execution_run"] != str(directory)):
        raise ValueError("La reserva del cálculo no coincide con su cierre.")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — ejecutar una vez un plan de reglas revisadas, sin IA")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan-run", type=Path)
    mode.add_argument("--verify-run", type=Path)
    parser.add_argument("--frozen-run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".local/rule-executions")
    args = parser.parse_args(argv)
    try:
        if args.verify_run:
            verify_rule_execution(args.verify_run, args.frozen_run)
            print(f"Resultado verificado sin recalcular: {args.verify_run}")
            return
        directory = execute_rule_plan(args.plan_run, args.frozen_run, output_dir=args.output_dir)
    except ExecutionError as error:
        parser.exit(1, f"Ejecución detenida: {error}. Registro: {error.directory}\n")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Resultado no verificable: {error}\n")
    print(f"Ejecución completada: {directory / 'report.md'}")


if __name__ == "__main__":
    main()
