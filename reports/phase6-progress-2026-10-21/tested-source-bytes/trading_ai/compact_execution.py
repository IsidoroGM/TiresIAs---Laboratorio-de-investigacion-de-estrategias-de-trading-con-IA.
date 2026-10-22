"""Ejecutor compacto explícito: una base y una candidata, usando el motor existente."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import rule_execution as engine
from trading_ai.compact_plan import _code_hashes as _plan_hashes, verify_compact_plan
from trading_ai.data import load_ecb_rates
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _policy, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _canonical
from trading_ai.rules import compile_rule_strategy
from trading_ai.strategies import create_strategy


PLAN_FILES = ("plan.json", "plan.json.sha256", "events.jsonl", "development.xml")


class CompactExecutionError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_plan_hashes(), "compact_execution.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _registered(directory: Path) -> tuple[dict, dict]:
    plan = verify_compact_plan(directory)
    origin = _origin(directory, PLAN_FILES)
    if origin["sha256"]["development.xml"] != plan["data"]["sha256"]:
        raise ValueError("Los datos no corresponden al plan compacto verificado.")
    return plan, origin


def _fixed(plan: dict, origin: dict) -> dict:
    identity = engine._identity(plan)
    calculation_id = sha256(_canonical(identity)).hexdigest()
    if calculation_id != plan["calculation_id"]:
        raise ValueError("La identidad del cálculo no coincide con la registrada.")
    return {"schema_version": 1, "protocol": "compact_execution_v1", "stage": "execution_completed",
            "calculation_id": calculation_id, "identity": identity, "plan": origin,
            "data": plan["data"], "policy": plan["policy"],
            "proposal": {"candidate_id": plan["candidate_id"], "spec_sha256": plan["candidate"]["spec_sha256"], "criterion": plan["criterion"]},
            "budget": plan["budget"], "reserved_backtests": {"baseline": 1, "candidate": 1},
            "completed_backtests": ["baseline", "candidate"], "code_sha256": _code_hashes(),
            "scope": "known_development_history_only", "outer_evaluation_allowed": False,
            "inherited_usage": plan["inherited_usage"], "inherited_api_cost_usd": plan["inherited_api_cost_usd"],
            "model_requests": 0, "usage": [], "api_cost_usd": "0", "executable": False}


def _access(fixed: dict, directory: Path) -> dict:
    return {"schema_version": 1, "protocol": "compact_execution_access_v1", "identity": fixed["identity"],
            "plan": fixed["plan"], "execution_run": str(directory), "budget": fixed["budget"],
            "code_sha256": _code_hashes(), "state": "attempt_reserved_no_automatic_retry"}


def execute_compact_plan(plan_dir: str | Path, *, output_dir: str | Path = ROOT / ".local/compact-executions") -> Path:
    directory = Path(plan_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    reserved, completed, claimed = {"baseline": 0, "candidate": 0}, [], False
    journal.record("compact_execution_started", plan_dir=str(directory), model_requests=0, api_cost_usd="0")
    try:
        plan, origin = _registered(directory)
        fixed = _fixed(plan, origin)
        policy, base = _policy(plan["policy"]), plan["baseline"]
        strategies = (("baseline", create_strategy(base["strategy"], base["fast_window"], base["slow_window"])),
                      ("candidate", compile_rule_strategy(plan["candidate"]["spec"])))
        access_raw = _canonical(_access(fixed, journal.directory))
        access_path = engine.ACCESS_ROOT / (fixed["calculation_id"] + ".json")
        engine.ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            _write_exclusive(access_path, access_raw)
        except FileExistsError as error:
            raise ValueError("Estos cálculos ya tienen un intento reservado; no se repetirán.") from error
        claimed = True
        journal.record("execution_access_claimed", access_path=str(access_path), access_sha256=sha256(access_raw).hexdigest())
        content = _read(directory / "development.xml", 32 * 1024 * 1024)
        if sha256(content).hexdigest() != plan["data"]["sha256"]:
            raise ValueError("Los datos cambiaron antes de cargar las referencias.")
        snapshot = journal.directory / "development.xml"
        _write_exclusive(snapshot, content)
        rates = tuple(load_ecb_rates(snapshot, policy.pair))
        if (not rates or len(rates) != plan["data"]["observations"] or str(rates[0][0]) != plan["data"]["first_date"]
                or str(rates[-1][0]) != plan["data"]["last_date"]):
            raise ValueError("Las observaciones no coinciden con el plan.")

        def unchanged():
            current, current_origin = _registered(directory)
            if (_canonical(current) != _canonical(plan) or current_origin != origin or fixed["code_sha256"] != _code_hashes()
                    or _read(snapshot, len(content)) != content or _read(access_path, 262144) != access_raw):
                raise ValueError("El plan, datos, código o reserva cambiaron durante la ejecución.")

        calculated = {}
        for role, strategy in strategies:
            unchanged()
            if reserved[role] or sum(reserved.values()) >= 2 or plan["budget"][role + "_backtests"] != 1:
                raise ValueError("Presupuesto de simulaciones agotado o incompatible.")
            reserved[role] += 1
            journal.record("backtest_reserved", role=role, reserved_backtests=dict(reserved), strategy=strategy.name)
            ledger = engine._calculate(rates, strategy, policy)
            journal.save(role + ".json", ledger)
            calculated[role] = ledger["summary"]
            completed.append(role)
            journal.record("backtest_calculated", role=role, sha256=sha256((journal.directory / (role + ".json")).read_bytes()).hexdigest())
        unchanged()
        result = {**fixed, **calculated, "artifacts_sha256": {
            name: sha256((journal.directory / name).read_bytes()).hexdigest() for name in ("baseline.json", "candidate.json", "development.xml")}}
        result["assessment"] = engine._assessment(result)
        journal.save("results.json", result)
        report = engine._report(result).encode("utf-8")
        _write_exclusive(journal.directory / "report.md", report)
        journal.record("compact_execution_completed", results_sha256=sha256((journal.directory / "results.json").read_bytes()).hexdigest(),
                       report_sha256=sha256(report).hexdigest(), access_sha256=sha256(access_raw).hexdigest(),
                       assessment=result["assessment"], reserved_backtests=reserved, completed_backtests=completed,
                       model_requests=0, api_cost_usd="0")
    except Exception as error:
        journal.record("compact_execution_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       access_claimed=claimed, reserved_backtests=reserved, completed_backtests=completed,
                       model_requests=0, api_cost_usd="0")
        raise CompactExecutionError(str(error), journal.directory) from error
    return journal.directory


def verify_compact_execution(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    raw = _read(directory / "results.json", 262144)
    result = _strict_json(raw)
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 4 * 1024 * 1024).splitlines()]
    if not events or events[-1]["event"] != "compact_execution_completed":
        raise ValueError("La ejecución no conserva un cierre completo.")
    closed = events[-1]["data"]
    plan, origin = _registered(Path(result["plan"]["directory"]))
    fixed = _fixed(plan, origin)
    if (set(result) != set(fixed) | {"baseline", "candidate", "assessment", "artifacts_sha256"}
            or _canonical({key: result[key] for key in fixed}) != _canonical(fixed)
            or closed["results_sha256"] != sha256(raw).hexdigest() or closed["reserved_backtests"] != fixed["reserved_backtests"]
            or closed["completed_backtests"] != fixed["completed_backtests"]):
        raise ValueError("El resultado no coincide con plan, código o presupuesto.")
    if set(result["artifacts_sha256"]) != {"baseline.json", "candidate.json", "development.xml"}:
        raise ValueError("Archivos calculados incompletos o incompatibles.")
    for name, checksum in result["artifacts_sha256"].items():
        if sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() != checksum:
            raise ValueError("Un archivo calculado ha cambiado: " + name)
    for role in ("baseline", "candidate"):
        if _strict_json(_read(directory / (role + ".json"), 32 * 1024 * 1024))["summary"] != result[role]:
            raise ValueError("El resumen no coincide con la contabilidad guardada.")
    report = _read(directory / "report.md", 65536)
    if (result["artifacts_sha256"]["development.xml"] != plan["data"]["sha256"] or result["assessment"] != engine._assessment(result)
            or closed["assessment"] != result["assessment"] or report != engine._report(result).encode("utf-8")
            or sha256(report).hexdigest() != closed["report_sha256"]):
        raise ValueError("Los datos, informe o conclusión no corresponden al motor.")
    access_raw = _read(engine.ACCESS_ROOT / (fixed["calculation_id"] + ".json"), 262144)
    if (_canonical(_strict_json(access_raw)) != _canonical(_access(fixed, directory))
            or sha256(access_raw).hexdigest() != closed["access_sha256"]):
        raise ValueError("La reserva compartida no corresponde a esta ejecución.")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — simulación virtual explícita de un plan compacto revisado")
    commands = parser.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("execute")
    execute.add_argument("--plan-run", type=Path, required=True)
    execute.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_compact_execution(args.run)["assessment"], ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(execute_compact_plan(args.plan_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Ejecución no verificable: {error}\n")


if __name__ == "__main__":
    main()
