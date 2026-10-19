"""Ayudas deterministas para revisar texto, retardos y calentamiento; no aprueban ni calculan rentabilidad."""

import argparse
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re

from trading_ai.research import ROOT, RunJournal
from trading_ai.robustness import _development
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.rules import COMPARISONS
from trading_ai.structured_ideas import compile_proposal
from trading_ai.structured_planning import _code_hashes as _planning_hashes, _source


def inspect_proposal(proposal: dict, observations: int) -> dict:
    """Propiedades del contrato, sin leer precios ni producir señales."""
    if type(observations) is not int or observations < 1:
        raise ValueError("Se requiere un número positivo de observaciones.")
    spec = compile_proposal(proposal).to_spec()
    conditions = {key: spec[key]["conditions"][0] for key in ("entry", "exit")}
    first, lags, truths = {}, {}, {}
    for role, condition in conditions.items():
        values = [condition[key] for key in ("left", "right")]
        lags[role] = [value["lag"] for value in values if value["kind"] != "constant"]
        available = [0 if value["kind"] == "constant" else value["lag"] + value.get("window", 1) - 1 for value in values]
        crossing = condition["operator"].startswith("crosses_")
        first[role] = max(available) + int(crossing)
        truth = "unknown"
        if condition["left"] == condition["right"]:
            truth = "always_true" if condition["operator"] in ("eq", "gte", "lte") else "always_false"
        elif all(value["kind"] == "constant" for value in values):
            result = False if crossing else COMPARISONS[condition["operator"]](Decimal(values[0]["value"]), Decimal(values[1]["value"]))
            truth = "always_true" if result else "always_false"
        truths[role] = truth
    earliest = max(first.values())
    text = proposal["hypothesis"].strip()
    last_words = re.findall(r"\w+", text.casefold())
    findings = []
    if not text.endswith((".", "!", "?")):
        findings.append("hypothesis_has_no_sentence_terminator")
    if last_words and last_words[-1] in {"a", "al", "de", "del", "el", "la", "las", "los", "un", "una", "y", "en", "con", "por", "para"}:
        findings.append("hypothesis_ends_with_linking_word")
    if sorted(lags["entry"]) != sorted(lags["exit"]):
        findings.append("different_entry_exit_lags")
    ruled_out = (truths["entry"] == "always_false" or truths["exit"] == "always_true"
                 or conditions["entry"] == conditions["exit"] or earliest >= observations)
    if ruled_out:
        findings.append("entry_ruled_out_by_structure_or_warmup")
    return {"title_characters": len(proposal["title"]), "hypothesis_characters": len(proposal["hypothesis"]),
            "title_at_character_limit": len(proposal["title"]) == 60,
            "hypothesis_at_character_limit": len(proposal["hypothesis"]) == 160,
            "operand_lags": lags, "condition_truth_after_warmup": truths,
            "earliest_signal_index": earliest, "earliest_execution_index": earliest + 1,
            "observations": observations, "defined_signal_observations": max(0, observations - earliest),
            "entry_ruled_out": ruled_out, "findings": findings,
            "scope": "structural_properties_and_text_hints_only_not_performance_or_semantic_proof"}


def _code_hashes() -> dict:
    return {**_planning_hashes(), "structured_diagnostics.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _record(directory: Path, frozen_dir: Path) -> dict:
    proposal, source = _source(directory, frozen_dir)
    frozen, reference, _ = _development(frozen_dir)
    return {"schema_version": 1, "protocol": "structured_diagnostics_v1", "source": source, "reference": reference,
            "status": "review_aid_only", "diagnostics": inspect_proposal(proposal["proposal"], frozen["development_result"]["source"]["observations"]),
            "executable": False, "calculated_results": None, "model_requests": 0, "api_cost_usd": "0", "code_sha256": _code_hashes()}


def diagnose_structured_idea(proposal_dir: str | Path, frozen_dir: str | Path, *,
                             output_dir: str | Path = ROOT / ".local/structured-diagnostics") -> Path:
    directory, frozen = Path(proposal_dir).resolve(), Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("structured_diagnostics_started", proposal_dir=str(directory))
    try:
        record = _record(directory, frozen)
        if _canonical(_record(directory, frozen)) != _canonical(record):
            raise ValueError("El origen cambió durante el diagnóstico.")
        _seal(journal, "diagnostics.json", record, "structured_diagnostics_completed")
    except Exception as error:
        journal.record("structured_diagnostics_failed", message=str(error)[:1000], model_requests=0, api_cost_usd="0")
        raise ValueError(f"Diagnóstico detenido: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_structured_diagnostics(run_dir: str | Path, frozen_dir: str | Path) -> dict:
    record, _ = _artifact(Path(run_dir).resolve(), "diagnostics.json", "structured_diagnostics_completed")
    if _canonical(record) != _canonical(_record(Path(record["source"]["directory"]), Path(frozen_dir).resolve())):
        raise ValueError("El diagnóstico no coincide con la propuesta o sus propiedades.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — ayudas de revisión sin señales o resultados financieros")
    parser.add_argument("command", choices=("diagnose", "verify"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--frozen-run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            print(json.dumps(verify_structured_diagnostics(args.run, args.frozen_run)["diagnostics"]))
            return
        kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
        print(diagnose_structured_idea(args.run, args.frozen_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Diagnóstico no verificable: {error}\n")


if __name__ == "__main__":
    main()
