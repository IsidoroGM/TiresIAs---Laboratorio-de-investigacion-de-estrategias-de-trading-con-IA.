"""Cobertura estructural de reglas registradas; no prueba novedad, equivalencia o rendimiento."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.compact_history import _code_hashes as _history_hashes, verify_compact_history
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.rules import OPERATORS, SERIES, compile_rule_strategy
from trading_ai.structured_draft import describe_draft
from trading_ai.structured_draft_context import _code_hashes as _context_hashes, verify_draft_context


MAX_SPECS = 256
MAX_COVERAGE_BYTES = 120000
CONTEXT_FILES = ("context.json", "context.json.sha256", "events.jsonl", "memory.json", "rules-memory.json", "claims.json", "report.md")
HISTORY_FILES = ("history.json", "history.json.sha256", "events.jsonl")


def profile_rule(spec: dict) -> dict:
    strategy = compile_rule_strategy(spec)
    normalized = strategy.to_spec()
    normalized.pop("name")
    template = deepcopy(normalized)
    operands, operators, parameters = set(), set(), []
    for role in ("entry", "exit"):
        for index, condition in enumerate(normalized[role]["conditions"]):
            operators.add(condition["operator"])
            for side in ("left", "right"):
                value = condition[side]
                operands.add(value["kind"])
                parameters.append({"role": role, "condition": index, "side": side, "operand": deepcopy(value)})
                template[role]["conditions"][index][side] = {"kind": value["kind"]}
    return {"rule_identity_without_name": sha256(_canonical(normalized)).hexdigest(),
            "template_identity_without_numeric_parameters": sha256(_canonical(template)).hexdigest(),
            "template": template, "direct_operand_kinds": sorted(operands), "operators": sorted(operators),
            "parameters": parameters, "semantic_equivalence_proven": False, "performance_or_novelty_proven": False}


def _code_hashes() -> dict:
    return {**_context_hashes(), **_history_hashes(), "rule_coverage.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _record(context_dir: Path, history_dir: Path | None, directory: Path) -> dict:
    context = verify_draft_context(context_dir)
    rules = _strict_json(_read(context_dir / "rules-memory.json", 2 * 1024 * 1024))
    items = [{"spec": entry["spec"], "spec_sha256": entry["spec_sha256"],
              "source": {"kind": "registered_structured_rule", "origin": entry["origin"]}} for entry in rules["entries"]]
    history_origin = None
    if history_dir is not None:
        history = verify_compact_history(history_dir)
        if history["reference"] != context["reference"]:
            raise ValueError("Las capturas de reglas y de intentos compactos no comparten la referencia congelada.")
        history_origin = _origin(history_dir, HISTORY_FILES)
        for entry in history["entries"]:
            if entry["rules"] is None: continue
            described = describe_draft(entry["rules"]["draft"])
            if described["spec_sha256"] != entry["rules"]["spec_sha256"]:
                raise ValueError("Las reglas compactas no corresponden a su identidad registrada.")
            items.append({"spec": described["spec"], "spec_sha256": described["spec_sha256"],
                          "source": {"kind": "compact_attempt", "origin": entry["candidate"], "status": entry["status"]}})
    if len(items) > MAX_SPECS: raise ValueError("Demasiadas reglas; no se omitirán registros para perfilar.")
    profiles, occurrences = {}, []
    for item in items:
        strategy = compile_rule_strategy(item["spec"])
        if strategy.spec_sha256 != item["spec_sha256"]: raise ValueError("Identidad de regla incompatible con su especificación.")
        profile = profile_rule(item["spec"])
        identity = profile["rule_identity_without_name"]
        profiles[identity] = profile
        occurrences.append({"source": item["source"], "spec_sha256": item["spec_sha256"], "rule_identity_without_name": identity})
    ordered = [profiles[key] for key in sorted(profiles)]
    used = sorted({kind for profile in ordered for kind in profile["direct_operand_kinds"]})
    catalog = sorted((*SERIES, "constant"))
    record = {"schema_version": 1, "protocol": "rule_coverage_v1", "status": "diagnostic_only", "run_dir": str(directory),
              "reference": context["reference"], "source_context": _origin(context_dir, CONTEXT_FILES), "source_history": history_origin,
              "occurrences": occurrences, "profiles": ordered,
              "counts": {"record_occurrences": len(items), "distinct_rule_identities_without_name": len(ordered),
                         "distinct_templates_without_numeric_parameters": len({profile["template_identity_without_numeric_parameters"] for profile in ordered}),
                         "repeated_rule_occurrences": len(items) - len(ordered)},
              "supported_direct_operand_kinds": catalog, "supported_operators": list(OPERATORS), "observed_direct_operand_kinds": used,
              "direct_operand_kinds_not_observed": [kind for kind in catalog if kind not in used],
              "coverage": "typed_rules_in_captured_sources_only", "free_text_ideas_analyzed": False, "global_history_complete": False,
              "template_method": "preserve_group_order_roles_operators_kinds_ignore_name_and_numeric_parameters",
              "semantic_equivalence_proven": False, "strategy_novelty_proven": False, "strategy_selected": False,
              "eligible_for_plan": False, "executable": False, "calculated_results": None,
              "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
              "code_sha256": _code_hashes()}
    stored_bytes = len(json.dumps(record, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8")) + 1
    if stored_bytes > MAX_COVERAGE_BYTES: raise ValueError("El diagnóstico es demasiado grande; no se recortarán perfiles o fuentes.")
    return record


def _report(record: dict) -> bytes:
    counts = record["counts"]
    return "\n".join(["# Cobertura de reglas tipadas capturadas", "",
        f"Registros: {counts['record_occurrences']}; identidades sin nombre: {counts['distinct_rule_identities_without_name']}; plantillas: {counts['distinct_templates_without_numeric_parameters']}.",
        "Operandos directos observados: " + (", ".join(record["observed_direct_operand_kinds"]) or "ninguno") + ".",
        "Tipos no observados en esos campos: " + (", ".join(record["direct_operand_kinds_not_observed"]) or "ninguno") + ".", "",
        "La plantilla conserva roles, operadores, grupos y tipos; omite nombre, valores, ventanas y retardos.",
        "Compartir plantilla no demuestra equivalencia de reglas: esos parámetros pueden cambiar señales y resultados.",
        "Un tipo no observado no es una estrategia recomendada o una oportunidad mejor. No se analizan ideas de texto libre.",
        "No se elige estrategia, consultan modelos, calculan señales, liberan intentos o aprueban propuestas.", ""]).encode("utf-8")


def capture_rule_coverage(context_dir: str | Path, *, history_dir: str | Path | None = None,
                          output_dir: str | Path = ROOT / ".local/rule-coverage") -> Path:
    context_dir, history_dir = Path(context_dir).resolve(), None if history_dir is None else Path(history_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("rule_coverage_started", context_dir=str(context_dir), history_dir=None if history_dir is None else str(history_dir))
    try:
        record = _record(context_dir, history_dir, journal.directory)
        if _canonical(_record(context_dir, history_dir, journal.directory)) != _canonical(record):
            raise ValueError("Las capturas o el código cambiaron durante el diagnóstico.")
        _write_exclusive(journal.directory / "report.md", _report(record))
        _seal(journal, "coverage.json", record, "rule_coverage_completed")
    except Exception as error:
        journal.record("rule_coverage_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise ValueError(f"Cobertura detenida: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_rule_coverage(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "coverage.json", "rule_coverage_completed")
    history = None if record["source_history"] is None else Path(record["source_history"]["directory"])
    expected = _record(Path(record["source_context"]["directory"]), history, directory)
    if _canonical(record) != _canonical(expected) or _read(directory / "report.md", 16384) != _report(record):
        raise ValueError("La cobertura, fuentes, parámetros, descripción o código han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — cobertura estructural, sin elegir estrategias")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture")
    capture.add_argument("--context-run", type=Path, required=True)
    capture.add_argument("--history-run", type=Path)
    capture.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_rule_coverage(args.run), ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(capture_rule_coverage(args.context_run, history_dir=args.history_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Cobertura no verificable: {error}\n")


if __name__ == "__main__": main()
