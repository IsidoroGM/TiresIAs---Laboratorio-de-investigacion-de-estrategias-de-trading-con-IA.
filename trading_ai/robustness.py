"""Sensibilidad acotada y selección cronológica interna, solo sobre desarrollo."""

import argparse
from copy import deepcopy
from dataclasses import replace
from datetime import date
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
from time import monotonic
import xml.etree.ElementTree as ET

from trading_ai.data import load_ecb_rates
from trading_ai.experiments import expected_assessment, run_experiment, validate_proposal
from trading_ai.holdout import (EXECUTION_POLICY, RESEARCH_FILES, _code_hashes as _frozen_hashes,
                                _json, _policy, _write_exclusive)
from trading_ai.research import ROOT, RunJournal
from trading_ai.validation import NAMESPACE, _parse_cutoff, _partition_xml


class RobustnessError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_frozen_hashes(), "robustness.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _save_json(path: Path, value: dict) -> None:
    _write_exclusive(path, (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf-8"))


def _development(frozen_dir: Path) -> tuple[dict, dict, bytes]:
    """Verificación específica que nunca abre evaluation.xml ni sus resultados."""
    raw = (frozen_dir / "frozen.json").read_bytes()
    checksum = sha256(raw).hexdigest()
    if (frozen_dir / "frozen.sha256").read_text(encoding="ascii").strip() != checksum:
        raise ValueError("El registro previo ha cambiado.")
    frozen = _json(raw)
    events = [json.loads(line) for line in (frozen_dir / "events.jsonl").read_bytes().splitlines()]
    if (not events or events[-1]["event"] != "proposal_frozen"
            or events[-1]["data"]["frozen_sha256"] != checksum
            or frozen["schema_version"] != 1 or frozen["stage"] != "frozen_not_evaluated"
            or frozen["code_sha256"] != _frozen_hashes() or frozen["execution_policy"] != EXECUTION_POLICY):
        raise ValueError("El registro o el código no coinciden con el protocolo previo.")
    policy = _policy(frozen["policy"])
    validate_proposal(frozen["proposal"], policy)
    research_dir = Path(frozen["research"]["directory"])
    for name in RESEARCH_FILES:
        if sha256((research_dir / name).read_bytes()).hexdigest() != frozen["research"]["sha256"][name]:
            raise ValueError("La investigación de desarrollo ha cambiado.")
    if (_json((research_dir / "results.json").read_bytes()) != frozen["development_result"]
            or frozen["development_result"]["policy"] != frozen["policy"]
            or frozen["development_result"]["proposal"] != frozen["proposal"]):
        raise ValueError("Propuesta o controles incompatibles con desarrollo.")
    split_dir = Path(frozen["split"]["directory"])
    manifest_raw = (split_dir / "manifest.json").read_bytes()
    if sha256(manifest_raw).hexdigest() != frozen["split"]["manifest_sha256"]:
        raise ValueError("El manifiesto de origen ha cambiado.")
    manifest = _json(manifest_raw)
    block = manifest["partitions"]["development"]
    if (manifest["protocol"] != "chronological_holdout_v1" or block["file"] != "development.xml"
            or manifest["execution_policy"] != EXECUTION_POLICY):
        raise ValueError("Se requiere la partición de desarrollo registrada.")
    content = (split_dir / "development.xml").read_bytes()
    expected = {"name": "BCE", "sha256": block["sha256"], "first_date": block["first_date"],
                "last_date": block["last_date"], "observations": block["observations"]}
    rates = load_ecb_rates(split_dir / "development.xml", policy.pair)
    if (sha256(content).hexdigest() != block["sha256"]
            or frozen["development_result"]["source"] != expected
            or len(rates) != block["observations"] or str(rates[0][0]) != block["first_date"]
            or str(rates[-1][0]) != block["last_date"]
            or rates[-1][0] >= date.fromisoformat(manifest["cutoff"])
            or (split_dir / "development.xml").read_bytes() != content):
        raise ValueError("Los datos no coinciden con el desarrollo anterior al corte exterior.")
    reference = {"frozen_dir": str(frozen_dir), "frozen_sha256": checksum,
                 "manifest_sha256": sha256(manifest_raw).hexdigest(),
                 "development_sha256": block["sha256"], "outer_cutoff": manifest["cutoff"]}
    return frozen, reference, content


def _scenarios(frozen: dict) -> tuple[list[dict], list[dict]]:
    """Cinco ventanas mecánicas; tres costes. Omisiones antes de calcular."""
    policy = _policy(frozen["policy"])
    seed = frozen["proposal"]
    fast, slow = seed["arguments"]["fast_window"], seed["arguments"]["slow_window"]
    windows, costs, skipped = [], [], []
    for label, first, second in (("reference", fast, slow), ("fast_minus", fast - 1, slow),
                                  ("fast_plus", fast + 1, slow), ("slow_minus", fast, slow - 1),
                                  ("slow_plus", fast, slow + 1)):
        proposal = deepcopy(seed)
        proposal["hypothesis"] = f"Sensibilidad mecánica {label} de la propuesta registrada; sin resultados anticipados."
        proposal["arguments"].update(fast_window=first, slow_window=second)
        try:
            validate_proposal(proposal, policy)
        except (ValueError, TypeError) as error:
            skipped.append({"kind": "window", "id": label, "arguments": proposal["arguments"], "reason": str(error)})
        else:
            windows.append((label, proposal))
    with localcontext(Context(prec=28)):
        for label, cost in (("reference", policy.cost_rate), ("cost_minus", policy.cost_rate - Decimal("0.0005")),
                             ("cost_plus", policy.cost_rate + Decimal("0.0005"))):
            try:
                configured = replace(policy, cost_rate=cost)
            except (ValueError, TypeError) as error:
                skipped.append({"kind": "cost", "id": label, "cost_rate": str(cost), "reason": str(error)})
            else:
                costs.append((label, configured.parameters()))
    scenarios = [{"id": window + "__" + cost, "window_id": window, "cost_id": cost,
                  "proposal": proposal, "policy": parameters}
                 for window, proposal in windows for cost, parameters in costs]
    return scenarios, skipped


def _selection_rule(criterion: str) -> dict:
    return {"cost_id": "reference", "eligibility": "criterion_met_with_closed_trades", "criterion": criterion,
            "ranking": "return_desc_then_drawdown_asc" if criterion == "higher_return_without_more_drawdown" else "drawdown_asc_then_return_desc",
            "ties": "fast_asc_slow_asc_window_id_asc", "before_check": True}


def prepare_robustness(frozen_dir: str | Path, inner_cutoff: date,
                       output_dir: str | Path = ROOT / ".local/robustness") -> Path:
    journal = RunJournal(Path(output_dir))
    journal.record("preparation_started", frozen_dir=str(Path(frozen_dir).resolve()))
    try:
        if type(inner_cutoff) is not date:
            raise ValueError("El corte interno debe ser una fecha sin hora.")
        frozen, reference, raw = _development(Path(frozen_dir).resolve())
        days = sorted(ET.fromstring(raw).findall(f"./{{{NAMESPACE}}}Cube/{{{NAMESPACE}}}Cube"),
                      key=lambda day: day.attrib["time"])
        boundary = inner_cutoff.isoformat()
        partitions = {"selection": [day for day in days if day.attrib["time"] < boundary],
                      "check": [day for day in days if day.attrib["time"] >= boundary]}
        if any(not block for block in partitions.values()):
            raise ValueError("El corte debe dejar datos en selección y comprobación internas.")
        scenarios, skipped = _scenarios(frozen)
        plan = {"schema_version": 1, "protocol": "development_robustness_v1", "stage": "prepared_not_run",
                "reference": reference, "seed_proposal": frozen["proposal"], "reference_policy": frozen["policy"],
                "inner_cutoff": boundary, "execution_policy": EXECUTION_POLICY,
                "scenarios": scenarios, "skipped": skipped, "periods": {}, "code_sha256": _code_hashes(),
                "selection_rule": _selection_rule(frozen["proposal"]["criterion"]),
                "limitations": ["All source history was already explored; this is internal descriptive validation.",
                                "Designed after the earlier outer evaluation; not independent confirmation.",
                                "No outer evaluation data or results are read by this workflow.",
                                "Checking all scenarios is descriptive and cannot trigger reselection."]}
        for name, block in partitions.items():
            content = _partition_xml(block)
            _write_exclusive(journal.directory / (name + ".xml"), content)
            plan["periods"][name] = {"file": name + ".xml", "sha256": sha256(content).hexdigest(),
                                      "first_date": block[0].attrib["time"], "last_date": block[-1].attrib["time"],
                                      "observations": len(block)}
        _save_json(journal.directory / "plan.json", plan)
        checksum = sha256((journal.directory / "plan.json").read_bytes()).hexdigest()
        _write_exclusive(journal.directory / "plan.sha256", (checksum + "\n").encode("ascii"))
        journal.record("plan_prepared", plan_sha256=checksum, scenario_count=len(scenarios), model_requests=0, api_cost_usd="0")
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        journal.record("preparation_failed", message=str(error)[:1000], error_type=type(error).__name__)
        raise RobustnessError(str(error), journal.directory) from error
    return journal.directory


def _verify_plan(directory: Path) -> tuple[dict, str]:
    raw = (directory / "plan.json").read_bytes()
    checksum = sha256(raw).hexdigest()
    if (directory / "plan.sha256").read_text(encoding="ascii").strip() != checksum:
        raise ValueError("El plan ha cambiado.")
    plan = _json(raw)
    events = [json.loads(line) for line in (directory / "events.jsonl").read_bytes().splitlines()]
    if (not events or events[-1]["event"] != "plan_prepared" or events[-1]["data"]["plan_sha256"] != checksum
            or plan["schema_version"] != 1 or plan["protocol"] != "development_robustness_v1"
            or plan["stage"] != "prepared_not_run" or plan["code_sha256"] != _code_hashes()
            or plan["execution_policy"] != EXECUTION_POLICY):
        raise ValueError("El plan, registro o código no coincide con la preparación.")
    frozen, reference, original = _development(Path(plan["reference"]["frozen_dir"]))
    scenarios, skipped = _scenarios(frozen)
    if (plan["reference"] != reference or plan["scenarios"] != scenarios or plan["skipped"] != skipped
            or plan["seed_proposal"] != frozen["proposal"] or plan["reference_policy"] != frozen["policy"]
            or plan["selection_rule"] != _selection_rule(frozen["proposal"]["criterion"])
            or set(plan["periods"]) != {"selection", "check"}):
        raise ValueError("Los escenarios no coinciden con la preparación mecánica.")
    all_rates = []
    cutoff = date.fromisoformat(plan["inner_cutoff"])
    for name in ("selection", "check"):
        block = plan["periods"][name]
        if block["file"] != name + ".xml":
            raise ValueError("Ruta de periodo no permitida.")
        path = directory / block["file"]
        rates = load_ecb_rates(path, frozen["policy"]["pair"])
        if (sha256(path.read_bytes()).hexdigest() != block["sha256"] or len(rates) != block["observations"]
                or str(rates[0][0]) != block["first_date"] or str(rates[-1][0]) != block["last_date"]
                or (name == "selection" and rates[-1][0] >= cutoff) or (name == "check" and rates[0][0] < cutoff)):
            raise ValueError("Datos internos incompatibles con el plan.")
        all_rates.extend(rates)
    source = Path(frozen["split"]["directory"]) / "development.xml"
    if all_rates != load_ecb_rates(source, frozen["policy"]["pair"]) or source.read_bytes() != original:
        raise ValueError("Las particiones internas no reproducen desarrollo.")
    return plan, checksum


def _selection(rows: list[dict], criterion: str) -> dict:
    eligible = [row for row in rows if row["scenario"]["cost_id"] == "reference"
                and row["assessment"]["verdict"] == "supported_in_sample"]
    eligible.sort(key=lambda row: (row["scenario"]["proposal"]["arguments"]["fast_window"],
                                   row["scenario"]["proposal"]["arguments"]["slow_window"], row["scenario"]["window_id"]))
    # Ordenaciones estables sin operaciones Decimal que dependan del contexto exterior.
    if criterion == "higher_return_without_more_drawdown":
        eligible.sort(key=lambda row: Decimal(row["result"]["candidate"]["max_drawdown_percent"]))
        eligible.sort(key=lambda row: Decimal(row["result"]["candidate"]["return_percent"]), reverse=True)
    else:
        eligible.sort(key=lambda row: Decimal(row["result"]["candidate"]["return_percent"]), reverse=True)
        eligible.sort(key=lambda row: Decimal(row["result"]["candidate"]["max_drawdown_percent"]))
    return {"selected_scenario_id": eligible[0]["scenario"]["id"] if eligible else None,
            "eligible_scenario_ids": [row["scenario"]["id"] for row in eligible],
            "origin": "selection_period_reference_cost_only", "reselection_allowed": False}


def _report(result: dict) -> str:
    def number(value):
        with localcontext(Context(prec=28)):
            return f"{Decimal(value):.6f}"
    def percent(value):
        with localcontext(Context(prec=28)):
            return format(Decimal(value) * 100, "f")
    chosen = result["selection"]["selected_scenario_id"] or "Ninguna elegible"
    policy = result["plan"]["reference_policy"]
    seed = result["plan"]["seed_proposal"]["arguments"]
    sizing = ("una unidad base por entrada" if policy["allocation_fraction"] is None else
              percent(policy["allocation_fraction"]) + " % del efectivo por entrada, costes incluidos")
    lines = ["# Trading AI — Robustez interna en desarrollo", "",
             f"Par: {policy['pair']}. Capital inicial por escenario y periodo: {policy['initial_capital']} en moneda cotizada.",
             f"Tamaño: {sizing}. Coste original por ejecución: {percent(policy['cost_rate'])} %.",
             f"Configuración de partida: {seed['strategy'].upper()}{seed['fast_window']}/{seed['slow_window']}.",
             f"Selección fijada antes de comprobar: `{chosen}`.",
             "La selección exige cumplir el criterio frente a la base al coste original; costes alternativos solo son sensibilidad.",
             "Se conservan todos los escenarios, sin elegir de nuevo después de la comprobación interna.", ""]
    for name, title in (("selection", "Selección interna"), ("check", "Comprobación interna")):
        block = result["plan"]["periods"][name]
        lines += [f"## {title}: {block['first_date']} a {block['last_date']}", "",
                  "| Escenario | Ventanas | Coste por ejecución % | Rent. base % | Rent. variante % | DD base % | DD variante % | Cierres base/variante | Criterio |",
                  "|---|---|---:|---:|---:|---:|---:|---:|---|"]
        for row in result["rows"][name]:
            base, candidate = row["result"]["baseline"], row["result"]["candidate"]
            label = {"supported_in_sample": "Cumple", "not_supported_in_sample": "No cumple", "inconclusive": "Inconcluso"}[row["assessment"]["verdict"]]
            lines.append(f"| {row['scenario']['id']} | {candidate['strategy']} | {percent(row['scenario']['policy']['cost_rate'])} | {number(base['return_percent'])} | {number(candidate['return_percent'])} | {number(base['max_drawdown_percent'])} | {number(candidate['max_drawdown_percent'])} | {base['closed_trades']}/{candidate['closed_trades']} | {label} |")
    lines += ["", "## Límites", "",
              "Las variantes de ventanas proceden de cambios mecánicos de Python, no de nuevas propuestas del modelo.",
              "Cada escenario y periodo empieza con su propio capital, sin posiciones, señales ni indicadores heredados.",
              "Rentabilidades acumuladas no anualizadas; no se suman cuentas ni se equiparan periodos distintos.",
              "El histórico ya se había explorado y este análisis se diseñó después de la evaluación exterior: no es evidencia inédita ni confirmación independiente.",
              "Este flujo no lee datos ni resultados de la evaluación exterior. Sus resultados no permiten ajustar una propuesta y volver a evaluarla allí.",
              "Un escenario favorable o una selección interna no demuestran robustez ni rentabilidad real.",
              "Cumplir el criterio relativo puede mantener pérdidas; no se exige ni se demuestra beneficio absoluto.",
              "Referencias BCE y costes hipotéticos. Peticiones de IA: 0. Coste de API: 0 USD.", ""]
    return "\n".join(lines)


def run_robustness(plan_dir: str | Path) -> Path:
    plan_dir = Path(plan_dir).resolve()
    journal = RunJournal(plan_dir / "attempts")
    started = monotonic()
    journal.record("run_started", plan_dir=str(plan_dir), model_requests=0, api_cost_usd="0")
    try:
        plan, checksum = _verify_plan(plan_dir)
        try:
            _save_json(plan_dir / "run_claim.json", {"plan_sha256": checksum, "attempt": str(journal.directory)})
        except FileExistsError as error:
            raise ValueError("Este plan ya tiene un intento; no se repetirá ni sobrescribirá.") from error
        rows = {"selection": [], "check": []}
        selection = None
        for period in ("selection", "check"):
            for scenario in plan["scenarios"]:
                journal.record("scenario_requested", period=period, scenario=scenario)
                calculated = run_experiment(plan_dir / (period + ".xml"), scenario["proposal"], _policy(scenario["policy"]))
                source = plan["periods"][period]
                if (calculated["source"] != {"name": "BCE", "sha256": source["sha256"], "first_date": source["first_date"],
                                            "last_date": source["last_date"], "observations": source["observations"]}
                        or calculated["policy"] != scenario["policy"] or calculated["proposal"] != scenario["proposal"]):
                    raise ValueError("El cálculo no coincide con el escenario fijado.")
                assessment = {**expected_assessment(calculated), "scope": "internal_" + period}
                row = {"scenario": scenario, "result": calculated, "assessment": assessment}
                journal.save(period + "_" + scenario["id"] + ".json", row)
                journal.record("scenario_completed", period=period, scenario_id=scenario["id"], assessment=assessment)
                rows[period].append(row)
            if period == "selection":
                selection = _selection(rows[period], plan["seed_proposal"]["criterion"])
                journal.save("selection.json", selection)
                journal.record("selection_fixed", **selection)
        if _verify_plan(plan_dir)[1] != checksum:
            raise ValueError("El plan cambió durante la ejecución.")
        result = {"schema_version": 1, "stage": "completed", "plan_sha256": checksum, "plan": plan,
                  "selection": selection, "rows": rows, "model_requests": 0, "api_cost_usd": "0"}
        journal.save("results.json", result)
        _write_exclusive(journal.directory / "report.md", _report(result).encode("utf-8"))
        journal.record("run_completed", scenario_count=sum(map(len, rows.values())),
                       elapsed_seconds=round(monotonic() - started, 3), model_requests=0, api_cost_usd="0",
                       results_sha256=sha256((journal.directory / "results.json").read_bytes()).hexdigest())
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        journal.record("run_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       elapsed_seconds=round(monotonic() - started, 3))
        raise RobustnessError(str(error), journal.directory) from error
    return journal.directory


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — robustez interna, sin acceder a evaluación exterior")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Fijar particiones, escenarios y selección sin calcular métricas")
    prepare.add_argument("--frozen-run", type=Path, required=True)
    prepare.add_argument("--inner-cutoff", type=_parse_cutoff, required=True)
    prepare.add_argument("--output-dir", type=Path, default=ROOT / ".local/robustness")
    run = commands.add_parser("run", help="Calcular el plan completo una vez, sin cambiar parámetros")
    run.add_argument("--plan-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            directory = prepare_robustness(args.frozen_run, args.inner_cutoff, args.output_dir)
            print(f"Plan fijado sin cálculos: {directory / 'plan.json'}")
        else:
            directory = run_robustness(args.plan_dir)
            print(f"Robustez interna calculada: {directory / 'report.md'}")
    except RobustnessError as error:
        parser.exit(1, f"Comprobación detenida: {error}. Registro: {error.directory}\n")


if __name__ == "__main__":
    main()
