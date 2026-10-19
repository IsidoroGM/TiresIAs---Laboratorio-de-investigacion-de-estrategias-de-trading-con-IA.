"""Vista previa sin modelo de un contrato compacto: reglas sin prosa atribuida a IA."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_brief import _code_hashes as _brief_hashes, describe_proposal
from trading_ai.structured_ideas import compile_proposal
from trading_ai.rules import _condition_schema


MAX_DRAFT_BYTES = 4096
DRAFT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"entry": deepcopy(_condition_schema), "exit": deepcopy(_condition_schema)},
    "required": ["entry", "exit"],
}


def describe_draft(draft: dict) -> dict:
    """Valida condiciones y describe campos; no propone una hipótesis ni da permisos."""
    if not isinstance(draft, dict) or set(draft) != {"entry", "exit"}:
        raise ValueError("El borrador solo admite entry y exit, sin prosa, resultados o controles.")
    # Adaptador técnico al validador existente. Estas etiquetas internas no son
    # texto del modelo y nunca se guardan como título o hipótesis del borrador.
    view = {"title": "Adaptador técnico", "hypothesis": "Sin hipótesis atribuida.", **deepcopy(draft)}
    strategy = compile_proposal(view)
    return {"spec": strategy.to_spec(), "spec_sha256": strategy.spec_sha256,
            "rule_description": describe_proposal(view), "model_description": None,
            "hypothesis_supplied": False, "semantic_review_required": True,
            "duplicate_history_checked": False, "eligible_for_session": False,
            "executable": False, "calculated_results": None}


def _code_hashes() -> dict:
    return {**_brief_hashes(), "structured_draft.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _record(raw: bytes, directory: Path) -> dict:
    if not isinstance(raw, bytes) or len(raw) > MAX_DRAFT_BYTES:
        raise ValueError(f"El JSON debe ocupar como máximo {MAX_DRAFT_BYTES} bytes.")
    draft = _strict_json(raw)
    return {"schema_version": 1, "protocol": "structured_draft_preview_v1", "status": "offline_preview_only",
            "run_dir": str(directory),
            "input": {"filename": "input.json", "sha256": sha256(raw).hexdigest(), "bytes": len(raw),
                      "origin": "unattributed_external_input"},
            **describe_draft(draft),
            "source_usage": {"model_requests": None, "input_tokens": None, "output_tokens": None,
                             "api_cost_usd": None},
            "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0,
                          "api_cost_usd": "0", "backtests": 0},
            "market_data_read": False, "code_sha256": _code_hashes()}


def _report(record: dict) -> str:
    rules = record["rule_description"]
    return "\n".join([
        "# Vista previa de un borrador compacto", "",
        "Entrada externa sin autoría verificada; no se ha consultado un modelo.", "",
        "Descripción mecánica generada por Python, sin título ni hipótesis atribuidos a IA.", "",
        rules["entry"], "", rules["exit"], "", rules["execution"], "", rules["interpretation"], "",
        "Faltan pregunta de investigación, contexto de datos, control de duplicados y revisión técnica.",
        "El borrador no es una propuesta registrada y no se puede adoptar en una sesión.",
        "No modifica presupuestos o decisiones anteriores. Cero consultas nuevas, simulaciones y coste nuevo de API.",
        "El consumo de origen es desconocido; no se presenta como cero.", "",
    ])


def preview_draft(input_file: str | Path, *, output_dir: str | Path = ROOT / ".local/structured-drafts") -> Path:
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("structured_draft_started", input_file=str(Path(input_file).resolve()))
    try:
        raw = _read(Path(input_file), MAX_DRAFT_BYTES)
        record = _record(raw, journal.directory)
        _write_exclusive(journal.directory / "input.json", raw)
        _write_exclusive(journal.directory / "report.md", _report(record).encode("utf-8"))
        _seal(journal, "draft.json", record, "structured_draft_completed")
    except Exception as error:
        journal.record("structured_draft_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       model_requests=0, api_cost_usd="0", backtests=0)
        raise ValueError(f"Vista previa detenida: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_draft(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "draft.json", "structured_draft_completed")
    expected = _record(_read(directory / "input.json", MAX_DRAFT_BYTES), directory)
    if (_canonical(record) != _canonical(expected)
            or _read(directory / "report.md", 16384) != _report(record).encode("utf-8")):
        raise ValueError("El borrador, la descripción, el código o su ubicación han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — vista previa sin modelo de reglas compactas")
    commands = parser.add_subparsers(dest="command", required=True)
    preview = commands.add_parser("preview")
    preview.add_argument("--input", type=Path, required=True)
    preview.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            print(json.dumps(verify_draft(args.run)["rule_description"], ensure_ascii=False))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(preview_draft(args.input, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Borrador no verificable: {error}\n")


if __name__ == "__main__":
    main()
