"""Tres ventanas expansivas sobre desarrollo conocido, selección antes de comprobar."""

import argparse
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from trading_ai import PROJECT_NAME
from trading_ai import rule_execution as engine
from trading_ai.data import load_ecb_rates
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _policy, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.robustness import _development
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.strategies import create_strategy
from trading_ai.validation import NAMESPACE, _partition_xml
from trading_ai.validated_read_cache import ValidatedReadCache


ACCESS_ROOT = ROOT / ".local/walk-forward-access"
FOLDS = 3
PLAN_FILES = ("plan.json", "plan.json.sha256", "events.jsonl", "development.xml")


def _code_hashes():
    from trading_ai.robustness import _code_hashes as prior
    return {**prior(), "walk_forward.py": sha256(Path(__file__).read_bytes()).hexdigest(),
            "rule_execution.py": sha256(Path(engine.__file__).read_bytes()).hexdigest()}


def _grid(frozen):
    args = frozen["proposal"]["arguments"]
    fast, slow = args["fast_window"], args["slow_window"]
    candidates, omitted = [], []
    for f, s in ((fast, slow), (fast - 1, slow), (fast + 1, slow), (fast, slow - 1), (fast, slow + 1)):
        value = {"strategy": args["strategy"], "fast_window": f, "slow_window": s}
        try: create_strategy(value["strategy"], f, s)
        except ValueError:
            omitted.append({**value, "reason": "invalid_windows"})
            continue
        base = frozen["policy"]
        if (value["strategy"], f, s) == (base["baseline_strategy"], base["fast_window"], base["slow_window"]):
            omitted.append({**value, "reason": "same_as_baseline"})
            continue
        candidates.append({"id": sha256(_canonical(value)).hexdigest(), **value})
    return candidates, omitted


def _build(frozen_dir, directory):
    frozen, reference, raw = _development(frozen_dir)
    candidates, omitted = _grid(frozen)
    if not candidates: raise ValueError("No quedan variantes válidas para el protocolo.")
    days = sorted(ET.fromstring(raw).findall(f"./{{{NAMESPACE}}}Cube/{{{NAMESPACE}}}Cube"), key=lambda item: item.attrib["time"])
    if len(days) // 4 <= max(item["slow_window"] for item in candidates):
        raise ValueError("El primer tramo no permite calentamiento y ejecución posterior.")
    blocks, contents = [], {"development.xml": raw}
    for index in range(1, FOLDS + 1):
        boundary, stop = index * len(days) // 4, (index + 1) * len(days) // 4
        block = {"index": index}
        for role, start, end in (("train", 0, boundary), ("check", boundary, stop)):
            name = f"{role}-{index:02d}.xml"
            content = _partition_xml(days[start:end])
            contents[name] = content
            block[role] = {"file": name, "sha256": sha256(content).hexdigest(), "observations": end - start,
                           "first_date": days[start].attrib["time"], "last_date": days[end - 1].attrib["time"]}
        blocks.append(block)
    identity = {"protocol": "known_expanding_walk_forward_v1", "data_sha256": sha256(raw).hexdigest(),
                "policy": frozen["policy"], "candidates": candidates, "folds": blocks}
    plan = {"schema_version": 1, "protocol": "known_walk_forward_plan_v1", "run_dir": str(directory),
            "frozen_dir": str(frozen_dir), "reference": reference, "policy": frozen["policy"],
            "criterion": frozen["proposal"]["criterion"], "candidates": candidates, "omitted": omitted, "folds": blocks,
            "identity": identity, "campaign_id": sha256(_canonical(identity)).hexdigest(),
            "budget": {"maximum_backtests": FOLDS * (len(candidates) + 3), "model_requests": 0, "automatic_retries": 0},
            "selection": "criterion_met_then_return_desc_drawdown_asc_windows_asc_id",
            "no_selection": "retain_empty_no_forced_winner_no_check_calculations",
            "accounts": "independent_per_fold_role_strategy", "carry_positions": False, "carry_signals": False,
            "indicator_warmup": "inside_each_partition", "forced_final_close": False,
            "scope": "known_development_history_only", "independent_validation": False,
            "outer_evaluation_allowed": False, "automatic_adoption": False, "api_cost_usd": "0", "code_sha256": _code_hashes()}
    return plan, contents


def prepare(frozen_dir, *, output_dir=ROOT / ".local/walk-forward-plans"):
    frozen_dir = Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("walk_forward_plan_started", frozen_dir=str(frozen_dir))
    try:
        plan, contents = _build(frozen_dir, journal.directory)
        if (ACCESS_ROOT / (plan["campaign_id"] + ".json")).exists(): raise ValueError("El protocolo ya tiene un intento; no se repite.")
        for name, raw in contents.items(): _write_exclusive(journal.directory / name, raw)
        if _canonical(_build(frozen_dir, journal.directory)[0]) != _canonical(plan): raise ValueError("Las fuentes cambiaron.")
        _seal(journal, "plan.json", plan, "walk_forward_plan_prepared")
    except Exception as error:
        journal.record("walk_forward_plan_failed", error_type=type(error).__name__, message=str(error)[:1000], api_cost_usd="0")
        raise
    return journal.directory


def verify_plan(directory):
    directory = Path(directory).resolve()
    plan, _ = _artifact(directory, "plan.json", "walk_forward_plan_prepared")
    expected, contents = _build(Path(plan["frozen_dir"]), directory)
    if plan != expected or any(_read(directory / name, 32 * 1024 * 1024) != raw for name, raw in contents.items()):
        raise ValueError("El plan, periodos, controles, código o registro congelado cambiaron.")
    return plan


def select(candidates, summaries, baseline, criterion):
    eligible = []
    for candidate in candidates:
        value = summaries[candidate["id"]]
        result = {"baseline": baseline, "candidate": value, "proposal": {"criterion": criterion}}
        if engine._assessment(result)["criterion_status"] == "met": eligible.append(candidate)
    eligible.sort(key=lambda item: (-Decimal(summaries[item["id"]]["return_percent"]),
                                   Decimal(summaries[item["id"]]["max_drawdown_percent"]),
                                   item["fast_window"], item["slow_window"], item["id"]))
    return eligible[0]["id"] if eligible else None


def run(plan_dir, *, output_dir=ROOT / ".local/walk-forward-runs"):
    plan_dir = Path(plan_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("walk_forward_started", plan_dir=str(plan_dir))
    completed, attempted, artifacts = [], 0, {}
    try:
        plan = verify_plan(plan_dir)
        origin = _origin(plan_dir, PLAN_FILES + tuple(item[role]["file"] for item in plan["folds"] for role in ("train", "check")))
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        access = ACCESS_ROOT / (plan["campaign_id"] + ".json")
        access_raw = _canonical({"protocol": "known_walk_forward_claim_v1", "run_dir": str(journal.directory), "plan": origin})
        _write_exclusive(access, access_raw)
        policy = _policy(plan["policy"])
        base = {"strategy": policy.baseline_strategy, "fast_window": policy.fast_window, "slow_window": policy.slow_window}

        def unchanged():
            if verify_plan(plan_dir) != plan or _read(access, 32768) != access_raw:
                raise ValueError("Los datos, plan o intento del walk-forward cambiaron.")

        def calculate(block, role, key, parameters):
            nonlocal attempted
            unchanged()
            if attempted >= plan["budget"]["maximum_backtests"]: raise ValueError("Presupuesto de backtests agotado.")
            data = block[role]
            identity = {"protocol": "walk_forward_calculation_v1", "data_sha256": data["sha256"],
                        "parameters": parameters, "policy": plan["policy"], "accounts": plan["accounts"]}
            calculation_id = sha256(_canonical(identity)).hexdigest()
            engine.ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
            _write_exclusive(engine.ACCESS_ROOT / (calculation_id + ".json"), _canonical({"identity": identity, "run_dir": str(journal.directory)}))
            rates = tuple(load_ecb_rates(plan_dir / data["file"], policy.pair))
            if len(rates) != data["observations"]: raise ValueError("Fechas no compatibles con el tramo.")
            attempted += 1
            filename = f"{role}-{block['index']:02d}-{key}.json"
            journal.record("walk_forward_backtest_attempted", index=block["index"], role=role, key=key, calculation_id=calculation_id)
            value = engine._calculate(rates, create_strategy(parameters["strategy"], parameters["fast_window"], parameters["slow_window"]), policy)
            journal.save(filename, value)
            artifacts[filename] = sha256((journal.directory / filename).read_bytes()).hexdigest()
            journal.record("walk_forward_backtest_completed", index=block["index"], role=role, key=key)
            return value["summary"]

        for block in plan["folds"]:
            train_base = calculate(block, "train", "baseline", base)
            summaries = {item["id"]: calculate(block, "train", item["id"], {key: item[key] for key in base}) for item in plan["candidates"]}
            chosen = select(plan["candidates"], summaries, train_base, plan["criterion"])
            selection = {"index": block["index"], "selected_id": chosen, "train_baseline": train_base, "train_candidates": summaries}
            filename = f"selection-{block['index']:02d}.json"
            _write_exclusive(journal.directory / filename, _canonical(selection))
            artifacts[filename] = sha256((journal.directory / filename).read_bytes()).hexdigest()
            journal.record("walk_forward_selection_frozen", index=block["index"], selected_id=chosen)
            check = None
            if chosen is not None:
                item = next(item for item in plan["candidates"] if item["id"] == chosen)
                check = {"baseline": calculate(block, "check", "baseline", base),
                         "candidate": calculate(block, "check", chosen, {key: item[key] for key in base}),
                         "proposal": {"criterion": plan["criterion"]}}
                check["assessment"] = engine._assessment(check)
            completed.append({**selection, "check": check, "check_status": "not_run_no_selection" if check is None else "calculated"})
        unchanged()
        record = {"schema_version": 1, "protocol": "known_walk_forward_result_v1", "run_dir": str(journal.directory),
                  "plan": origin, "folds": completed, "attempted_backtests": attempted, "completed_backtests": len([name for name in artifacts if not name.startswith('selection')]),
                  "artifacts_sha256": artifacts, "scope": "known_development_history_only", "independent_validation": False,
                  "automatic_adoption": False, "aggregation": "no_compounded_accounts_no_new_global_winner",
                  "model_requests": 0, "api_cost_usd": "0", "code_sha256": _code_hashes()}
        _seal(journal, "results.json", record, "walk_forward_completed")
    except Exception as error:
        journal.record("walk_forward_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       attempted_backtests=attempted, completed_folds=completed, no_automatic_retry=True, api_cost_usd="0")
        raise engine.ExecutionError(str(error), journal.directory) from error
    return journal.directory


def verify_run(directory):
    directory = Path(directory).resolve()
    result, _ = _artifact(directory, "results.json", "walk_forward_completed")
    plan_dir = Path(result["plan"]["directory"])
    plan = verify_plan(plan_dir)
    names = PLAN_FILES + tuple(item[role]["file"] for item in plan["folds"] for role in ("train", "check"))
    if result["run_dir"] != str(directory) or result["plan"] != _origin(plan_dir, names) or result["code_sha256"] != _code_hashes():
        raise ValueError("Fuentes del resultado alteradas.")
    claim = _canonical({"protocol": "known_walk_forward_claim_v1", "run_dir": str(directory), "plan": result["plan"]})
    if _read(ACCESS_ROOT / (plan["campaign_id"] + ".json"), 32768) != claim: raise ValueError("Intento incompatible.")
    for name, digest in result["artifacts_sha256"].items():
        if Path(name).name != name or sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() != digest:
            raise ValueError("Archivo de walk-forward alterado.")
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 4 * 1024 * 1024).splitlines()]
    if (result["scope"] != "known_development_history_only" or result["independent_validation"] is not False
            or result["automatic_adoption"] is not False or result["model_requests"] != 0 or result["api_cost_usd"] != "0"
            or len(result["folds"]) != FOLDS): raise ValueError("Alcance o presupuesto del resultado incompatible.")
    expected_files = set()
    for fold in result["folds"]:
        block = next(block for block in plan["folds"] if block["index"] == fold["index"])
        selection_name = f"selection-{fold['index']:02d}.json"
        expected_selection = {key: fold[key] for key in ("index", "selected_id", "train_baseline", "train_candidates")}
        if _strict_json(_read(directory / selection_name, 65536)) != expected_selection: raise ValueError("Selección guardada incompatible.")
        expected_files.add(selection_name)
        calculations = [("train", "baseline", {"strategy": plan["policy"]["baseline_strategy"], "fast_window": plan["policy"]["fast_window"], "slow_window": plan["policy"]["slow_window"]}, fold["train_baseline"])]
        calculations += [("train", item["id"], {key: item[key] for key in ("strategy", "fast_window", "slow_window")}, fold["train_candidates"][item["id"]]) for item in plan["candidates"]]
        if fold["selected_id"] is None:
            if fold["check"] is not None or fold["check_status"] != "not_run_no_selection": raise ValueError("No debe existir un ganador o comprobación forzada.")
        else:
            if fold["check"] is None or fold["check_status"] != "calculated": raise ValueError("Falta la comprobación seleccionada.")
            item = next(item for item in plan["candidates"] if item["id"] == fold["selected_id"])
            calculations += [("check", "baseline", calculations[0][2], fold["check"]["baseline"]),
                             ("check", item["id"], {key: item[key] for key in ("strategy", "fast_window", "slow_window")}, fold["check"]["candidate"])]
        for role, key, parameters, summary in calculations:
            filename = f"{role}-{fold['index']:02d}-{key}.json"
            expected_files.add(filename)
            if _strict_json(_read(directory / filename, 32 * 1024 * 1024))["summary"] != summary: raise ValueError("Resumen distinto de la contabilidad.")
            identity = {"protocol": "walk_forward_calculation_v1", "data_sha256": block[role]["sha256"],
                        "parameters": parameters, "policy": plan["policy"], "accounts": plan["accounts"]}
            calculation_id = sha256(_canonical(identity)).hexdigest()
            if _read(engine.ACCESS_ROOT / (calculation_id + ".json"), 32768) != _canonical({"identity": identity, "run_dir": str(directory)}):
                raise ValueError("Reserva de cálculo incompatible.")
        if fold["selected_id"] != select(plan["candidates"], fold["train_candidates"], fold["train_baseline"], plan["criterion"]):
            raise ValueError("Selección incompatible con los resultados de entrenamiento.")
        selected = next(index for index, event in enumerate(events) if event["event"] == "walk_forward_selection_frozen" and event["data"]["index"] == fold["index"])
        checks = [index for index, event in enumerate(events) if event["event"] == "walk_forward_backtest_attempted" and event["data"]["index"] == fold["index"] and event["data"]["role"] == "check"]
        if checks and min(checks) <= selected: raise ValueError("Se comprobó el tramo antes de fijar la selección.")
        if fold["check"] is not None and fold["check"]["assessment"] != engine._assessment(fold["check"]):
            raise ValueError("Conclusión incompatible con Python.")
    if (set(result["artifacts_sha256"]) != expected_files or result["attempted_backtests"] != len(expected_files) - FOLDS
            or result["completed_backtests"] != result["attempted_backtests"]
            or result["attempted_backtests"] > plan["budget"]["maximum_backtests"]): raise ValueError("Contabilidad o presupuesto incompletos.")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} — walk-forward descriptivo sobre desarrollo conocido")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--frozen-run", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path)
    for name in ("run", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--plan" if name == "run" else "--run", type=Path, required=True)
        if name == "run": command.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        with ValidatedReadCache():
            kwargs = {"output_dir": args.output_dir} if getattr(args, "output_dir", None) else {}
            result = prepare(args.frozen_run, **kwargs) if args.command == "prepare" else run(args.plan, **kwargs) if args.command == "run" else verify_run(args.run)
        print(json.dumps(result, ensure_ascii=True) if isinstance(result, dict) else result)
    except (ValueError, OSError, TypeError, KeyError, IndexError, ET.ParseError) as error: parser.exit(1, f"Walk-forward detenido: {error}\n")


if __name__ == "__main__": main()
