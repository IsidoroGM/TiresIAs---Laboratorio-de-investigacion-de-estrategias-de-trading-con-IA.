"""Descripción completa derivada de reglas verificadas; conserva el texto del modelo sin completarlo."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.formalization import _read
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_ideas import compile_proposal
from trading_ai.structured_planning import _code_hashes as _planning_hashes, _source


_OPERATORS = {"gt": "es mayor que", "gte": "es mayor o igual que", "lt": "es menor que",
              "lte": "es menor o igual que", "eq": "es igual a", "crosses_above": "cruza por encima de",
              "crosses_below": "cruza por debajo de"}
_INDICATORS = {"sma": "la SMA", "ema": "la EMA", "rolling_min": "el mínimo móvil", "rolling_max": "el máximo móvil"}


def describe_proposal(proposal: dict) -> dict:
    """Texto mecánico de campos conocidos; no interpreta ni corrige la hipótesis del modelo."""
    strategy = compile_proposal(proposal)
    spec = strategy.to_spec()
    def operand(item):
        if item["kind"] == "constant":
            return "el valor " + item["value"]
        lag = item["lag"]
        ago = "actual" if lag == 0 else f"de hace {lag} " + ("observación" if lag == 1 else "observaciones")
        if item["kind"] == "reference":
            return "la referencia " + ago
        window = item["window"]
        series = _INDICATORS[item["kind"]]
        period = f"de {window} " + ("observación" if window == 1 else "observaciones")
        return f"{series} actual {period}" if lag == 0 else f"{series} {period} {ago}"
    result = {"origin": "python_from_validated_rules", "spec_sha256": strategy.spec_sha256}
    for key, action in (("entry", "Entrar largo"), ("exit", "Salir de la posición larga")):
        condition = spec[key]["conditions"][0]
        result[key] = f"{action} cuando {operand(condition['left'])} {_OPERATORS[condition['operator']]} {operand(condition['right'])}."
    result["execution"] = "El motor ejecuta la señal en la observación siguiente, si existe; el retardo de una serie no cambia esta regla."
    result["interpretation"] = "Descripción mecánica de condiciones; no demuestra que ocurran señales, operaciones o mejoras."
    return result


def _code_hashes() -> dict:
    return {**_planning_hashes(), "structured_brief.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _record(directory: Path, frozen: Path) -> dict:
    proposal, source = _source(directory, frozen)
    return {"schema_version": 1, "protocol": "structured_rule_brief_v1", "status": "review_aid_only",
            "source": source, "reference": proposal["reference"],
            "model_description": {"origin": "model_unverified", "title": proposal["proposal"]["title"],
                                  "hypothesis": proposal["proposal"]["hypothesis"]},
            "rule_description": describe_proposal(proposal["proposal"]),
            "source_status": proposal["status"], "executable": False, "calculated_results": None,
            "model_requests": 0, "api_cost_usd": "0", "code_sha256": _code_hashes()}


def _report(record: dict) -> str:
    # Indentación de bloque de código: no interpretar Markdown o instrucciones del modelo.
    def literal(text):
        return "\n".join("    " + line for line in text.split("\n"))
    rules = record["rule_description"]
    return "\n".join(["# Descripción de las reglas declaradas", "",
                       "Texto derivado por Python de campos explícitos; no es una explicación escrita por el modelo.", "",
                       rules["entry"], "", rules["exit"], "", rules["execution"], "", rules["interpretation"], "",
                       "## Texto original del modelo, sin verificar ni completar", "",
                       "Título:", "", literal(record["model_description"]["title"]), "",
                       "Hipótesis:", "", literal(record["model_description"]["hypothesis"]), "",
                       "Esta ayuda no cambia la revisión, no aprueba la propuesta ni autoriza simulaciones.",
                       "Consultas nuevas de esta descripción: 0. Coste nuevo de API: 0 USD.", ""])


def create_structured_brief(proposal_dir: str | Path, frozen_dir: str | Path, *,
                            output_dir: str | Path = ROOT / ".local/structured-briefs") -> Path:
    directory, frozen = Path(proposal_dir).resolve(), Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("structured_brief_started", proposal_dir=str(directory))
    try:
        record = _record(directory, frozen)
        if _canonical(_record(directory, frozen)) != _canonical(record):
            raise ValueError("El origen o el código cambiaron durante la descripción.")
        _write_exclusive(journal.directory / "report.md", _report(record).encode("utf-8"))
        _seal(journal, "brief.json", record, "structured_brief_completed")
    except Exception as error:
        journal.record("structured_brief_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       model_requests=0, api_cost_usd="0")
        raise ValueError(f"Descripción detenida: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_structured_brief(run_dir: str | Path, frozen_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "brief.json", "structured_brief_completed")
    expected = _record(Path(record["source"]["directory"]), Path(frozen_dir).resolve())
    if (_canonical(record) != _canonical(expected)
            or _read(directory / "report.md", 16384) != _report(record).encode("utf-8")):
        raise ValueError("La descripción, el informe o las fuentes han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — descripción mecánica de reglas sin completar texto del modelo")
    parser.add_argument("command", choices=("create", "verify"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--frozen-run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            print(json.dumps(verify_structured_brief(args.run, args.frozen_run)["rule_description"], ensure_ascii=False))
            return
        kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
        print(create_structured_brief(args.run, args.frozen_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Descripción no verificable: {error}\n")


if __name__ == "__main__":
    main()
