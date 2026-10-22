"""Una campaña acotada por periodos conocidos; cálculos y criterios del motor existente."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import compact_periods as periods
from trading_ai import rule_execution as engine
from trading_ai.data import load_ecb_rates
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _policy, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.rules import compile_rule_strategy
from trading_ai.strategies import create_strategy


class PeriodExecutionError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**periods._code_hashes(), "compact_period_execution.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _registered(directory: Path) -> tuple[dict, dict]:
    plan = periods.verify_compact_periods(directory)
    files = ("periods.json", "periods.json.sha256", "events.jsonl", *(block["data"]["file"] for block in plan["periods"]))
    return plan, _origin(directory, files)


def _label(block: dict) -> str:
    return f"period-{block['index']:02d}"


def _fixed(plan: dict, origin: dict, directory: Path) -> dict:
    count = len(plan["periods"])
    return {"schema_version": 1, "protocol": "compact_period_execution_v1", "stage": "execution_completed",
            "run_dir": str(directory), "plan": origin, "reference": plan["reference"],
            "campaign_id": plan["campaign_id"], "campaign_identity": plan["campaign_identity"],
            "policy": plan["policy"], "criterion": plan["criterion"], "budget": plan["budget"],
            "reserved_backtests": {"baseline": count, "candidate": count},
            "completed_backtests": [_label(block) + "/" + role for block in plan["periods"] for role in ("baseline", "candidate")],
            "accounts": plan["accounts"], "aggregation_policy": plan["aggregation_policy"],
            "scope": "known_development_history_only", "outer_evaluation_allowed": False,
            "walk_forward_selection": False, "strategy_selection": False, "executable": False,
            "inherited_usage": plan["inherited_usage"], "inherited_api_cost_usd": plan["inherited_api_cost_usd"],
            "model_requests": 0, "usage": [], "api_cost_usd": "0", "code_sha256": _code_hashes()}


def _access(plan: dict, origin: dict, directory: Path) -> tuple[dict, list[tuple[Path, bytes]]]:
    campaign = {"schema_version": 1, "protocol": "compact_period_campaign_access_v1", "identity": plan["campaign_identity"],
                "plan": origin, "execution_run": str(directory), "budget": plan["budget"], "code_sha256": _code_hashes(),
                "state": "attempt_reserved_no_automatic_retry"}
    claims = [(periods.ACCESS_ROOT / (plan["campaign_id"] + ".json"), _canonical(campaign))]
    for block in plan["periods"]:
        view = {**plan, "data": block["data"]}
        identity = engine._identity(view)
        if sha256(_canonical(identity)).hexdigest() != block["calculation_id"]:
            raise ValueError("Identidad del periodo incompatible.")
        access = {"schema_version": 1, "protocol": "compact_period_calculation_access_v1", "identity": identity,
                  "plan": origin, "execution_run": str(directory), "period": block["index"], "campaign_id": plan["campaign_id"],
                  "budget": {"baseline_backtests": 1, "candidate_backtests": 1, "model_requests": 0, "automatic_retries": 0},
                  "code_sha256": _code_hashes(), "state": "attempt_reserved_no_automatic_retry"}
        claims.append((engine.ACCESS_ROOT / (block["calculation_id"] + ".json"), _canonical(access)))
    return campaign, claims


def _assessment(row: dict, criterion: str) -> dict:
    return engine._assessment({"proposal": {"criterion": criterion}, "baseline": row["baseline"], "candidate": row["candidate"]})


def _counts(rows: list[dict]) -> dict:
    return {state: sum(row["assessment"]["criterion_status"] == state for row in rows) for state in ("met", "not_met", "inconclusive")}


def _report(result: dict) -> bytes:
    lines = ["# Diagnóstico por periodos conocidos", "",
             "Regla fija y cuentas independientes por periodo y estrategia. No hay selección o reentrenamiento.", "",
             "| Periodo | Base retorno % | Candidata retorno % | Base drawdown % | Candidata drawdown % | Estado |",
             "|---|---:|---:|---:|---:|---|"]
    for row in result["period_results"]:
        base, candidate = row["baseline"], row["candidate"]
        lines.append(f"| {row['data']['first_date']} a {row['data']['last_date']} | {base['return_percent']} | "
                     f"{candidate['return_percent']} | {base['max_drawdown_percent']} | {candidate['max_drawdown_percent']} | {row['assessment']['criterion_status']} |")
    lines += ["", "Se conservan todos los periodos, incluidos los negativos y los inconclusos.",
              "No se elige el mejor bloque, no se suman o componen rentabilidades de cuentas independientes.",
              "El motor calcula cada criterio; los recuentos no prueban novedad, robustez o rentabilidad futura.",
              "Desarrollo ya conocido, sin evaluación inédita ni selección walk-forward.",
              "Calentamiento dentro de cada periodo; ejecución posterior, sin arrastrar posiciones o señales y sin cierre forzado.",
              "Campaña y cálculos reservados una sola vez, sin reintentos automáticos. Dinero exclusivamente virtual.",
              "Cero consultas de modelo y 0 USD nuevo de API.", ""]
    return "\n".join(lines).encode("utf-8")


def execute_compact_periods(plan_dir: str | Path, *, output_dir: str | Path = ROOT / ".local/compact-period-executions") -> Path:
    directory = Path(plan_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    reserved, completed, claimed = {"baseline": 0, "candidate": 0}, [], []
    journal.record("compact_period_execution_started", plan_dir=str(directory))
    try:
        plan, origin = _registered(directory)
        fixed = _fixed(plan, origin, journal.directory)
        _, claims = _access(plan, origin, journal.directory)
        for path, raw in claims:
            path.parent.mkdir(parents=True, exist_ok=True)
            try: _write_exclusive(path, raw)
            except FileExistsError as error:
                raise ValueError("Campaña o cálculo de periodo ya reservado; no se repetirá.") from error
            claimed.append(str(path))
            journal.record("period_access_claimed", path=str(path), sha256=sha256(raw).hexdigest())
        contents = {}
        for block in plan["periods"]:
            name = block["data"]["file"]
            raw = _read(directory / name, 32 * 1024 * 1024)
            if sha256(raw).hexdigest() != block["data"]["sha256"]: raise ValueError("Datos de periodo modificados.")
            contents[name] = raw
            _write_exclusive(journal.directory / name, raw)
        def unchanged():
            current, current_origin = _registered(directory)
            if (_canonical(current) != _canonical(plan) or current_origin != origin or fixed["code_sha256"] != _code_hashes()
                    or any(_read(path, len(raw)) != raw for path, raw in claims)
                    or any(_read(journal.directory / name, len(raw)) != raw for name, raw in contents.items())):
                raise ValueError("Plan, datos, código o reservas cambiaron durante la campaña.")
        policy, base = _policy(plan["policy"]), plan["baseline"]
        rows = []
        for block in plan["periods"]:
            label = _label(block)
            (journal.directory / label).mkdir()
            rates = tuple(load_ecb_rates(journal.directory / block["data"]["file"], policy.pair))
            if (not rates or len(rates) != block["data"]["observations"] or str(rates[0][0]) != block["data"]["first_date"]
                    or str(rates[-1][0]) != block["data"]["last_date"]):
                raise ValueError("Observaciones de periodo incompatibles.")
            row = {"index": block["index"], "data": block["data"], "calculation_id": block["calculation_id"]}
            strategies = (("baseline", create_strategy(base["strategy"], base["fast_window"], base["slow_window"])),
                          ("candidate", compile_rule_strategy(plan["candidate"]["spec"])))
            for role, strategy in strategies:
                unchanged()
                token = label + "/" + role
                if (token in completed or reserved[role] >= plan["budget"][role + "_backtests"]
                        or sum(reserved.values()) >= plan["budget"]["maximum_total_backtests"]):
                    raise ValueError("Presupuesto de periodos agotado o incompatible.")
                reserved[role] += 1
                journal.record("period_backtest_reserved", period=block["index"], role=role, reserved_backtests=dict(reserved))
                ledger = engine._calculate(rates, strategy, policy)
                journal.save(token + ".json", ledger)
                row[role] = ledger["summary"]
                completed.append(token)
                journal.record("period_backtest_completed", token=token)
            row["assessment"] = _assessment(row, plan["criterion"])
            rows.append(row)
        unchanged()
        paths = [block["data"]["file"] for block in plan["periods"]] + [token + ".json" for token in completed]
        result = {**fixed, "period_results": rows, "assessment_counts": _counts(rows),
                  "artifacts_sha256": {name: sha256((journal.directory / name).read_bytes()).hexdigest() for name in paths},
                  "access_sha256": {str(path): sha256(raw).hexdigest() for path, raw in claims}}
        report = _report(result)
        result["report_sha256"] = sha256(report).hexdigest()
        _write_exclusive(journal.directory / "report.md", report)
        _seal(journal, "results.json", result, "compact_period_execution_completed")
    except Exception as error:
        journal.record("compact_period_execution_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       access_claimed=claimed, reserved_backtests=reserved, completed_backtests=completed,
                       model_requests=0, api_cost_usd="0")
        raise PeriodExecutionError(str(error), journal.directory) from error
    return journal.directory


def verify_compact_period_execution(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    result, _ = _artifact(directory, "results.json", "compact_period_execution_completed")
    plan, origin = _registered(Path(result["plan"]["directory"]))
    fixed = _fixed(plan, origin, directory)
    extras = {"period_results", "assessment_counts", "artifacts_sha256", "access_sha256", "report_sha256"}
    if set(result) != set(fixed) | extras or _canonical({key: result[key] for key in fixed}) != _canonical(fixed):
        raise ValueError("La campaña no coincide con el plan, controles, código o presupuesto.")
    _, claims = _access(plan, origin, directory)
    expected_access = {str(path): sha256(raw).hexdigest() for path, raw in claims}
    if result["access_sha256"] != expected_access or any(_read(path, len(raw)) != raw for path, raw in claims):
        raise ValueError("Las reservas de campaña o cálculos han cambiado.")
    paths = [block["data"]["file"] for block in plan["periods"]] + [token + ".json" for token in fixed["completed_backtests"]]
    if set(result["artifacts_sha256"]) != set(paths): raise ValueError("Archivos de periodos incompatibles.")
    for name, checksum in result["artifacts_sha256"].items():
        if sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() != checksum:
            raise ValueError("Un archivo de periodo ha cambiado: " + name)
    if len(result["period_results"]) != len(plan["periods"]): raise ValueError("Faltan periodos calculados.")
    for row, block in zip(result["period_results"], plan["periods"]):
        if (set(row) != {"index", "data", "calculation_id", "baseline", "candidate", "assessment"}
                or any(row[key] != block[key] for key in ("index", "data", "calculation_id"))
                or result["artifacts_sha256"][block["data"]["file"]] != block["data"]["sha256"]
                or row["assessment"] != _assessment(row, plan["criterion"])):
            raise ValueError("Un periodo o su conclusión no coincide con lo registrado.")
        for role in ("baseline", "candidate"):
            ledger = _strict_json(_read(directory / (_label(block) + "/" + role + ".json"), 32 * 1024 * 1024))
            if ledger["summary"] != row[role]: raise ValueError("Resumen de periodo incompatible con su contabilidad.")
    report = _read(directory / "report.md", 65536)
    if (result["assessment_counts"] != _counts(result["period_results"]) or report != _report(result)
            or sha256(report).hexdigest() != result["report_sha256"]):
        raise ValueError("Informe o recuentos de periodos incompatibles.")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — ejecutar un diagnóstico conocido ya registrado")
    commands = parser.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("execute")
    execute.add_argument("--plan-run", type=Path, required=True)
    execute.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_compact_period_execution(args.run)["assessment_counts"]))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(execute_compact_periods(args.plan_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Campaña no verificable: {error}\n")


if __name__ == "__main__": main()
