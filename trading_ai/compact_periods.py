"""Plan de diagnóstico por periodos conocidos, sin selección de estrategias o cálculos."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from trading_ai import rule_execution as engine
from trading_ai.compact_plan import _code_hashes as _plan_hashes, verify_compact_plan
from trading_ai.data import load_ecb_rates
from trading_ai.formalization import _read
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.validation import NAMESPACE, _partition_xml


MAX_PERIODS = 3
ACCESS_ROOT = ROOT / ".local/compact-period-access"
PLAN_FILES = ("plan.json", "plan.json.sha256", "events.jsonl", "development.xml")


def _code_hashes() -> dict:
    return {**_plan_hashes(), "compact_periods.py": sha256(Path(__file__).read_bytes()).hexdigest(),
            "validation.py": sha256(Path(__file__).with_name("validation.py").read_bytes()).hexdigest()}


def _bounds(observations: int, periods: int) -> list[tuple[int, int]]:
    if type(periods) is not int or not 2 <= periods <= MAX_PERIODS:
        raise ValueError(f"El diagnóstico admite entre 2 y {MAX_PERIODS} periodos; no amplía el presupuesto.")
    if type(observations) is not int or observations < periods:
        raise ValueError("Debe haber al menos una observación por periodo.")
    return [(index * observations // periods, (index + 1) * observations // periods) for index in range(periods)]


def _build(plan_dir: Path, periods: int, directory: Path) -> tuple[dict, dict[str, bytes]]:
    source = verify_compact_plan(plan_dir)
    origin = _origin(plan_dir, PLAN_FILES)
    raw = _read(plan_dir / "development.xml", 32 * 1024 * 1024)
    if sha256(raw).hexdigest() != source["data"]["sha256"]:
        raise ValueError("El desarrollo no coincide con el plan revisado.")
    days = sorted(ET.fromstring(raw).findall(f"./{{{NAMESPACE}}}Cube/{{{NAMESPACE}}}Cube"), key=lambda day: day.attrib["time"])
    rates = load_ecb_rates(plan_dir / "development.xml", source["policy"]["pair"])
    if (len(days) != source["data"]["observations"] or [day.attrib["time"] for day in days] != [str(day) for day, _ in rates]):
        raise ValueError("Las fechas no coinciden con el desarrollo validado.")
    blocks, contents = [], {}
    for index, (start, stop) in enumerate(_bounds(len(days), periods), 1):
        filename = f"period-{index:02d}.xml"
        content = _partition_xml(days[start:stop])
        data = {"name": "BCE", "file": filename, "sha256": sha256(content).hexdigest(),
                "observations": stop - start, "first_date": days[start].attrib["time"], "last_date": days[stop - 1].attrib["time"]}
        view = {**source, "data": data}
        blocks.append({"index": index, "start_index": start, "stop_index_exclusive": stop, "data": data,
                       "calculation_id": sha256(_canonical(engine._identity(view))).hexdigest()})
        contents[filename] = content
    campaign_identity = {"schema_version": 1, "scope": "compact_known_periods_v1", "source_calculation_id": source["calculation_id"]}
    record = {"schema_version": 1, "protocol": "compact_known_periods_plan_v1", "stage": "registered_not_run",
              "run_dir": str(directory), "source_plan": origin, "reference": source["reference"],
              "candidate": deepcopy(source["candidate"]), "baseline": deepcopy(source["baseline"]),
              "policy": deepcopy(source["policy"]), "criterion": source["criterion"],
              "execution_policy": deepcopy(source["execution_policy"]), "execution_timing": source["execution_timing"],
              "direction": source["direction"], "periods": blocks, "partition_method": "equal_observation_count_contiguous",
              "budget": {"campaign_attempts": 1, "periods": periods, "baseline_backtests": periods,
                         "candidate_backtests": periods, "maximum_total_backtests": 2 * periods,
                         "model_requests": 0, "parameter_variations": 0, "automatic_retries": 0},
              "campaign_identity": campaign_identity, "campaign_id": sha256(_canonical(campaign_identity)).hexdigest(),
              "accounts": "independent_per_period_and_strategy", "carry_positions": False, "carry_signals": False,
              "indicator_warmup": "inside_each_period", "forced_final_close": False,
              "periods_with_no_trades": "retain_and_report_inconclusive", "strategy_selection": False,
              "aggregation_policy": "list_all_periods_no_selected_winner_no_compounded_return",
              "walk_forward_selection": False, "scope": "known_development_history_only", "outer_evaluation_allowed": False,
              "executable": False, "calculated_results": None, "execution_requires_explicit_tool": True,
              "inherited_usage": deepcopy(source["inherited_usage"]), "inherited_api_cost_usd": source["inherited_api_cost_usd"],
              "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
              "code_sha256": _code_hashes()}
    return record, contents


def prepare_compact_periods(plan_dir: str | Path, *, periods: int = 3,
                            output_dir: str | Path = ROOT / ".local/compact-periods") -> Path:
    plan_dir = Path(plan_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("compact_periods_started", plan_dir=str(plan_dir), periods=periods)
    try:
        record, contents = _build(plan_dir, periods, journal.directory)
        if (ACCESS_ROOT / (record["campaign_id"] + ".json")).exists():
            raise ValueError("El diagnóstico de esta candidata y desarrollo ya tiene una reserva; no se reabrirá.")
        for block in record["periods"]:
            if (engine.ACCESS_ROOT / (block["calculation_id"] + ".json")).exists():
                raise ValueError("Un cálculo de periodo ya está reservado; no se repetirá.")
        for filename, raw in contents.items(): _write_exclusive(journal.directory / filename, raw)
        current, current_contents = _build(plan_dir, periods, journal.directory)
        if _canonical(current) != _canonical(record) or current_contents != contents:
            raise ValueError("Las fuentes o el código cambiaron al preparar los periodos.")
        _seal(journal, "periods.json", record, "compact_periods_registered")
    except Exception as error:
        journal.record("compact_periods_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise ValueError(f"Diagnóstico detenido: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_compact_periods(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "periods.json", "compact_periods_registered")
    expected, contents = _build(Path(record["source_plan"]["directory"]), len(record["periods"]), directory)
    if (_canonical(record) != _canonical(expected)
            or any(_read(directory / name, len(raw)) != raw for name, raw in contents.items())):
        raise ValueError("El diagnóstico, periodos, controles, fuentes o código han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — preparar periodos conocidos sin calcular")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--plan-run", type=Path, required=True)
    prepare.add_argument("--periods", type=int, default=3)
    prepare.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_compact_periods(args.run), ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(prepare_compact_periods(args.plan_run, periods=args.periods, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError, ET.ParseError) as error:
        parser.exit(1, f"Diagnóstico no verificable: {error}\n")


if __name__ == "__main__": main()
