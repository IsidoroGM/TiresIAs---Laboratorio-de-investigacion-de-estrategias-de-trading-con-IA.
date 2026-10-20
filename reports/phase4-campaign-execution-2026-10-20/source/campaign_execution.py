"""Una comparación virtual autorizada, con reservas duraderas y cálculo del motor."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import PROJECT_NAME
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_permission as permissions
from trading_ai import rule_execution as engine
from trading_ai.campaign_controller import ERRORS
from trading_ai.data import load_ecb_rates
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _policy, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _canonical
from trading_ai.rules import compile_rule_strategy
from trading_ai.strategies import create_strategy


class ExecutionError(ValueError):
    def __init__(self, message, directory):
        super().__init__(message)
        self.directory = directory


def _code_hashes():
    return permissions._code_hashes()


def _fixed(permission_dir, comparison=None):
    permission, plan = permissions.verify_permission(permission_dir, comparison=comparison)
    origin = _origin(permission_dir, permissions.PERMISSION_FILES)
    if plan["calculation_id"] != sha256(_canonical(engine._identity(plan))).hexdigest():
        raise ValueError("La identidad del cálculo no coincide con los controles y reglas.")
    fixed = {"schema_version": 1, "protocol": "campaign_virtual_execution_v1", "stage": "execution_completed",
             "permission": origin, "plan": permission["plan"], "binding": plan["binding"],
             "calculation_id": plan["calculation_id"], "identity": engine._identity(plan),
             "data": plan["data"], "policy": plan["policy"], "budget": plan["budget"],
             "proposal": {"spec_sha256": plan["candidate"]["spec_sha256"], "criterion": plan["criterion"]},
             "reserved_backtests": {"baseline": 1, "candidate": 1}, "completed_backtests": ["baseline", "candidate"],
             "scope": "known_development_history_only", "purpose": permissions.PURPOSE,
             "capture_origin_scope": permission["capture_origin_scope"], "transport_verified": False,
             "automatic_adoption": False, "outer_evaluation_allowed": False, "broker_operations_allowed": False,
             "inherited_attempt_usage": plan["attempt_usage"], "prior_compact_usage": plan["prior_compact_usage"],
             "model_requests": 0, "usage": [], "api_cost_usd": "0", "executable": False,
             "verification_scope": "recorded_integrity_and_python_assessment_not_reexecution", "code_sha256": _code_hashes()}
    return fixed, plan


def _claim(fixed, directory):
    return {"schema_version": 1, "protocol": "campaign_virtual_execution_claim_v1", "execution_run": str(directory),
            "identity": fixed["identity"], "permission": fixed["permission"], "plan": fixed["plan"],
            "budget": fixed["budget"], "state": "attempt_reserved_no_automatic_retry", "code_sha256": _code_hashes()}


def _report(result):
    text = engine._report(result).replace("# Trading AI —", "# TiresIAs —", 1)
    return text + ("\nPermiso limitado a esta comparación virtual. Origen de captura declarado por el llamador; "
                   "transporte y autoría del modelo no acreditados. Sin adopción automática.\n")


def execute(permission_dir: str | Path, *, output_dir: str | Path = ROOT / ".local/campaign-executions") -> Path:
    permission_dir = Path(permission_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    comparison, claimed, attempted, completed = None, False, [], []
    journal.record("campaign_execution_started", permission_dir=str(permission_dir), model_requests=0, api_cost_usd="0")
    try:
        fixed, plan = _fixed(permission_dir)
        code = _code_hashes()
        content = _read(Path(fixed["plan"]["directory"]) / "development.xml", 32 * 1024 * 1024)
        if sha256(content).hexdigest() != plan["data"]["sha256"]: raise ValueError("Los datos cambiaron antes de cargarlos.")
        snapshot = journal.directory / "development.xml"
        _write_exclusive(snapshot, content)
        policy, base = _policy(plan["policy"]), plan["baseline"]
        rates = tuple(load_ecb_rates(snapshot, policy.pair))
        if (not rates or len(rates) != plan["data"]["observations"] or str(rates[0][0]) != plan["data"]["first_date"]
                or str(rates[-1][0]) != plan["data"]["last_date"]):
            raise ValueError("Las observaciones no coinciden con el plan.")
        strategies = (("baseline", create_strategy(base["strategy"], base["fast_window"], base["slow_window"])),
                      ("candidate", compile_rule_strategy(plan["candidate"]["spec"])))
        access = engine.ACCESS_ROOT / (fixed["calculation_id"] + ".json")
        access_raw = _canonical(_claim(fixed, journal.directory))
        engine.ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        try: _write_exclusive(access, access_raw)
        except FileExistsError as error: raise ValueError("El intento de cálculo ya está consumido; no se repetirá.") from error
        claimed = True
        journal.record("shared_calculation_claimed", path=str(access), sha256=sha256(access_raw).hexdigest())
        reserved = ledger.reserve_comparison(plan["binding"]["scope_id"], plan["binding"]["request_sha256"], plan["calculation_id"])
        if reserved["reused"]: raise ValueError("La reserva de comparación ya se había consumido; no se reanuda.")
        comparison = reserved["receipt"]
        journal.save("comparison.json", comparison)
        journal.record("campaign_comparison_reserved", receipt_id=comparison["receipt_id"], reserved_backtests=2)

        def unchanged():
            current, current_plan = _fixed(permission_dir, comparison)
            if (_canonical(current) != _canonical(fixed) or _canonical(current_plan) != _canonical(plan)
                    or _code_hashes() != code or _read(snapshot, len(content)) != content
                    or _read(access, 262144) != access_raw):
                raise ValueError("El permiso, memoria, datos, controles o reserva cambiaron durante el cálculo.")

        calculated = {}
        for role, strategy in strategies:
            unchanged()
            if role in attempted or len(attempted) >= 2 or plan["budget"][role + "_backtests"] != 1:
                raise ValueError("Presupuesto de cálculo agotado o incompatible.")
            attempted.append(role)
            journal.record("backtest_attempted", role=role, attempted_backtests=list(attempted))
            computed = engine._calculate(rates, strategy, policy)
            journal.save(role + ".json", computed)
            calculated[role] = computed["summary"]
            completed.append(role)
            journal.record("backtest_completed", role=role, sha256=sha256((journal.directory / (role + ".json")).read_bytes()).hexdigest())
        unchanged()
        result = {**fixed, **calculated, "comparison": comparison,
                  "artifacts_sha256": {name: sha256((journal.directory / name).read_bytes()).hexdigest()
                                       for name in ("baseline.json", "candidate.json", "development.xml", "comparison.json")}}
        result["assessment"] = engine._assessment(result)
        journal.save("results.json", result)
        report = _report(result).encode("utf-8")
        _write_exclusive(journal.directory / "report.md", report)
        journal.record("campaign_execution_completed", results_sha256=sha256((journal.directory / "results.json").read_bytes()).hexdigest(),
                       report_sha256=sha256(report).hexdigest(), access_sha256=sha256(access_raw).hexdigest(),
                       comparison_receipt_id=comparison["receipt_id"], attempted_backtests=attempted, completed_backtests=completed,
                       reserved_backtests=2, assessment=result["assessment"], model_requests=0, api_cost_usd="0")
    except Exception as error:
        journal.record("campaign_execution_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       shared_calculation_claimed=claimed, comparison_receipt=comparison,
                       attempted_backtests=attempted, completed_backtests=completed, model_requests=0, api_cost_usd="0")
        raise ExecutionError(str(error), journal.directory) from error
    return journal.directory


def verify_execution(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    raw = _read(directory / "results.json", 262144)
    result = _strict_json(raw)
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 4 * 1024 * 1024).splitlines()]
    if not events or events[-1]["event"] != "campaign_execution_completed": raise ValueError("La ejecución no conserva su cierre.")
    closed = events[-1]["data"]
    fixed, plan = _fixed(Path(result["permission"]["directory"]), result["comparison"])
    if (set(result) != set(fixed) | {"baseline", "candidate", "comparison", "artifacts_sha256", "assessment"}
            or _canonical({key: result[key] for key in fixed}) != _canonical(fixed)
            or closed["results_sha256"] != sha256(raw).hexdigest()
            or closed["attempted_backtests"] != ["baseline", "candidate"] or closed["completed_backtests"] != ["baseline", "candidate"]
            or closed["reserved_backtests"] != 2 or closed["comparison_receipt_id"] != result["comparison"]["receipt_id"]):
        raise ValueError("Los resultados no coinciden con permiso, plan o presupuesto.")
    files = {"baseline.json", "candidate.json", "development.xml", "comparison.json"}
    if set(result["artifacts_sha256"]) != files: raise ValueError("Los archivos del cálculo están incompletos.")
    for name, digest in result["artifacts_sha256"].items():
        if sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() != digest: raise ValueError("Archivo calculado alterado: " + name)
    for role in ("baseline", "candidate"):
        if _canonical(_strict_json(_read(directory / (role + ".json"), 32 * 1024 * 1024))["summary"]) != _canonical(result[role]):
            raise ValueError("Un resumen no coincide con la contabilidad guardada.")
    report = _read(directory / "report.md", 65536)
    if (result["artifacts_sha256"]["development.xml"] != plan["data"]["sha256"]
            or _canonical(_strict_json(_read(directory / "comparison.json", 32768))) != _canonical(result["comparison"])
            or result["assessment"] != engine._assessment(result) or closed["assessment"] != result["assessment"]
            or report != _report(result).encode("utf-8") or sha256(report).hexdigest() != closed["report_sha256"]):
        raise ValueError("La conclusión, datos o informe no corresponden a los registros del motor.")
    access_raw = _read(engine.ACCESS_ROOT / (fixed["calculation_id"] + ".json"), 262144)
    if access_raw != _canonical(_claim(fixed, directory)) or sha256(access_raw).hexdigest() != closed["access_sha256"]:
        raise ValueError("La reserva compartida no corresponde a esta ejecución.")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} — una comparación virtual con permiso explícito")
    commands = parser.add_subparsers(dest="command", required=True)
    execute_parser = commands.add_parser("execute")
    execute_parser.add_argument("--permission-run", type=Path, required=True)
    execute_parser.add_argument("--output-dir", type=Path)
    commands.add_parser("verify").add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_execution(args.run)["assessment"], ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(execute(args.permission_run, **kwargs))
    except ERRORS as error: parser.exit(1, f"Cálculo virtual detenido: {error}\n")


if __name__ == "__main__": main()
