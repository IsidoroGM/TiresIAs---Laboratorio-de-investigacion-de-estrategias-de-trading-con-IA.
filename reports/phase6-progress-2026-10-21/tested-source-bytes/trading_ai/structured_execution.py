"""Ejecutor para planes estructurados; cálculos compartidos y reserva común con el protocolo anterior."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import rule_execution as engine
from trading_ai.data import load_ecb_rates
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _policy, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _canonical
from trading_ai.rules import compile_rule_strategy
from trading_ai.strategies import create_strategy
from trading_ai.structured_planning import _code_hashes as _planning_hashes, verify_structured_plan


class StructuredExecutionError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_planning_hashes(), **{name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                   for name in ("rule_execution.py", "structured_execution.py")}}


def _registered(directory: Path, frozen: Path) -> tuple[dict, dict]:
    plan = verify_structured_plan(directory, frozen)
    origin = {"directory": str(directory), "sha256": {
        name: sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest()
        for name in ("plan.json", "plan.json.sha256", "events.jsonl", "development.xml")}}
    if origin["sha256"]["development.xml"] != plan["data"]["sha256"]:
        raise ValueError("Los datos no coinciden con el plan estructurado.")
    return plan, origin


def _fixed_result(plan: dict, origin: dict) -> dict:
    identity = engine._identity(plan)
    return {"schema_version": 1, "protocol": "structured_execution_v1", "stage": "execution_completed",
            "calculation_id": sha256(_canonical(identity)).hexdigest(), "identity": identity, "plan": origin,
            "data": plan["data"], "policy": plan["policy"],
            "proposal": {"proposal_id": plan["proposal_id"], "spec_sha256": plan["candidate"]["spec_sha256"], "criterion": plan["criterion"]},
            "budget": plan["budget"], "reserved_backtests": {"baseline": 1, "candidate": 1},
            "completed_backtests": ["baseline", "candidate"], "code_sha256": _code_hashes(),
            "model_requests": 0, "usage": [], "api_cost_usd": "0"}


def execute_structured_plan(plan_dir: str | Path, frozen_dir: str | Path, *,
                            output_dir: str | Path = ROOT / ".local/structured-executions") -> Path:
    directory, frozen = Path(plan_dir).resolve(), Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    reserved, completed, claimed = {"baseline": 0, "candidate": 0}, [], False
    journal.record("structured_execution_started", plan_dir=str(directory), frozen_dir=str(frozen), model_requests=0, api_cost_usd="0")
    try:
        plan, origin = _registered(directory, frozen)
        hashes = _code_hashes()
        fixed = _fixed_result(plan, origin)
        policy, base = _policy(plan["policy"]), plan["baseline"]
        strategies = (("baseline", create_strategy(base["strategy"], base["fast_window"], base["slow_window"])),
                      ("candidate", compile_rule_strategy(plan["candidate"]["spec"])))
        access = {"schema_version": 1, "protocol": "structured_execution_access_v1", "identity": fixed["identity"],
                  "plan": origin, "execution_run": str(journal.directory), "budget": plan["budget"],
                  "code_sha256": hashes, "state": "attempt_reserved_no_automatic_retry"}
        access_raw = _canonical(access)
        engine.ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        access_path = engine.ACCESS_ROOT / (fixed["calculation_id"] + ".json")
        try:
            _write_exclusive(access_path, access_raw)
        except FileExistsError as error:
            raise ValueError("Estos cálculos ya tienen un intento reservado; no se repetirán.") from error
        claimed = True
        journal.record("execution_access_claimed", access_path=str(access_path), access=access)
        content = _read(directory / "development.xml", 32 * 1024 * 1024)
        snapshot = journal.directory / "development.xml"
        if sha256(content).hexdigest() != plan["data"]["sha256"]:
            raise ValueError("Los datos cambiaron antes de cargar las referencias.")
        _write_exclusive(snapshot, content)
        rates = tuple(load_ecb_rates(snapshot, policy.pair))
        if (not rates or len(rates) != plan["data"]["observations"]
                or str(rates[0][0]) != plan["data"]["first_date"] or str(rates[-1][0]) != plan["data"]["last_date"]):
            raise ValueError("Las observaciones no coinciden con el plan fijado.")
        def unchanged():
            current, current_origin = _registered(directory, frozen)
            if (_canonical(current) != _canonical(plan) or current_origin != origin or _code_hashes() != hashes
                    or _read(snapshot, len(content)) != content or _read(access_path, 262144) != access_raw):
                raise ValueError("El plan, las fuentes, el código o la reserva cambiaron durante la ejecución.")
        calculated = {}
        for role, strategy in strategies:
            unchanged()
            if reserved[role] or sum(reserved.values()) >= 2 or plan["budget"][role + "_backtests"] != 1:
                raise ValueError("Presupuesto de simulaciones agotado o incompatible.")
            reserved[role] += 1
            journal.record("backtest_reserved", role=role, reserved_backtests=dict(reserved), strategy=strategy.name)
            ledger = engine._calculate(rates, strategy, policy)
            journal.save(role + ".json", ledger)
            completed.append(role)
            calculated[role] = ledger["summary"]
            journal.record("backtest_calculated", role=role, summary=ledger["summary"],
                           sha256=sha256((journal.directory / (role + ".json")).read_bytes()).hexdigest())
        unchanged()
        result = {**fixed, **calculated, "artifacts_sha256": {
            name: sha256((journal.directory / name).read_bytes()).hexdigest()
            for name in ("baseline.json", "candidate.json", "development.xml")}}
        result["assessment"] = engine._assessment(result)
        journal.save("results.json", result)
        _write_exclusive(journal.directory / "report.md", engine._report(result).encode("utf-8"))
        journal.record("structured_execution_completed", results_sha256=sha256((journal.directory / "results.json").read_bytes()).hexdigest(),
                       report_sha256=sha256((journal.directory / "report.md").read_bytes()).hexdigest(),
                       access_sha256=sha256(access_raw).hexdigest(), assessment=result["assessment"],
                       reserved_backtests=reserved, completed_backtests=completed, model_requests=0, api_cost_usd="0")
    except Exception as error:
        journal.record("structured_execution_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       access_claimed=claimed, reserved_backtests=reserved, completed_backtests=completed,
                       model_requests=0, api_cost_usd="0")
        raise StructuredExecutionError(str(error), journal.directory) from error
    return journal.directory


def verify_structured_execution(run_dir: str | Path, frozen_dir: str | Path) -> dict:
    directory, frozen = Path(run_dir).resolve(), Path(frozen_dir).resolve()
    raw = _read(directory / "results.json", 262144)
    result = _strict_json(raw)
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 4 * 1024 * 1024).splitlines()]
    if not events or events[-1]["event"] != "structured_execution_completed":
        raise ValueError("La ejecución estructurada no conserva un cierre completo.")
    closed = events[-1]["data"]
    plan, origin = _registered(Path(result["plan"]["directory"]), frozen)
    fixed = _fixed_result(plan, origin)
    if (set(result) != set(fixed) | {"baseline", "candidate", "assessment", "artifacts_sha256"}
            or _canonical({key: result[key] for key in fixed}) != _canonical(fixed)
            or closed["results_sha256"] != sha256(raw).hexdigest()
            or closed["reserved_backtests"] != fixed["reserved_backtests"]
            or closed["completed_backtests"] != fixed["completed_backtests"]):
        raise ValueError("El resultado no coincide con el plan, el código o el presupuesto.")
    if set(result["artifacts_sha256"]) != {"baseline.json", "candidate.json", "development.xml"}:
        raise ValueError("Artefactos de ejecución incompletos o no admitidos.")
    for name, checksum in result["artifacts_sha256"].items():
        if sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() != checksum:
            raise ValueError("Un artefacto calculado ha cambiado.")
    for role in ("baseline", "candidate"):
        if _strict_json(_read(directory / (role + ".json"), 32 * 1024 * 1024))["summary"] != result[role]:
            raise ValueError("Un resumen no coincide con la contabilidad guardada.")
    report_raw = _read(directory / "report.md", 65536)
    if (result["artifacts_sha256"]["development.xml"] != plan["data"]["sha256"]
            or result["assessment"] != engine._assessment(result) or closed["assessment"] != result["assessment"]
            or report_raw != engine._report(result).encode("utf-8") or sha256(report_raw).hexdigest() != closed["report_sha256"]):
        raise ValueError("El informe, los datos o la conclusión no coinciden con el motor.")
    access_raw = _read(engine.ACCESS_ROOT / (fixed["calculation_id"] + ".json"), 262144)
    access = _strict_json(access_raw)
    expected_access = {"schema_version": 1, "protocol": "structured_execution_access_v1", "identity": fixed["identity"],
                       "plan": origin, "execution_run": str(directory), "budget": plan["budget"],
                       "code_sha256": _code_hashes(), "state": "attempt_reserved_no_automatic_retry"}
    if _canonical(access) != _canonical(expected_access) or sha256(access_raw).hexdigest() != closed["access_sha256"]:
        raise ValueError("La reserva compartida no coincide con esta ejecución.")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — ejecutar o verificar un plan estructurado")
    parser.add_argument("command", choices=("execute", "verify"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--frozen-run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = verify_structured_execution(args.run, args.frozen_run)
            print(json.dumps(result["assessment"]))
            return
        kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
        directory = execute_structured_plan(args.run, args.frozen_run, **kwargs)
    except StructuredExecutionError as error:
        parser.exit(1, f"Ejecución detenida: {error}. Evidencia: {error.directory}\n")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Registro no verificable: {error}\n")
    print(f"Resultado: {directory / 'report.md'}")


if __name__ == "__main__":
    main()
