"""Extensión de cobertura mecánica para una petición futura; sin habilitar generación."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.compact_request import _code_hashes as _prepared_hashes, verify_compact_request
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_coverage import _code_hashes as _coverage_hashes, verify_rule_coverage
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_draft_request import MAX_REQUEST_BYTES


BASE_REQUEST_BYTES = MAX_REQUEST_BYTES
PREPARED_FILES = ("prepared.json", "prepared.json.sha256", "events.jsonl", "request.json")
COVERAGE_FILES = ("coverage.json", "coverage.json.sha256", "events.jsonl", "report.md")
NOTE = "\nLa cobertura no prueba novedad ni recomienda estrategias."


def _code_hashes() -> dict:
    return {**_prepared_hashes(), **_coverage_hashes(), "guided_compact_request.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _build(prepared_dir: Path, coverage_dir: Path) -> tuple[bytes, dict, dict]:
    prepared = verify_compact_request(prepared_dir)
    coverage = verify_rule_coverage(coverage_dir)
    if prepared["reference"] != coverage["reference"]:
        raise ValueError("La petición y cobertura no comparten la referencia congelada.")
    payload = _strict_json(_read(prepared_dir / "request.json", BASE_REQUEST_BYTES))
    context = _strict_json(payload["messages"][1]["content"])
    if "typed_rule_coverage" in context:
        raise ValueError("La petición ya contiene una extensión de cobertura.")
    if not {item["spec_sha256"] for item in coverage["occurrences"]}.issubset(set(context["consumed_rule_identities"])):
        raise ValueError("La petición no contiene todas las identidades de la cobertura; renovar el contexto base.")
    context["typed_rule_coverage"] = {
        "scope": "captured_rules_only", "rules": coverage["counts"]["distinct_rule_identities_without_name"],
        "templates": coverage["counts"]["distinct_templates_without_numeric_parameters"],
        "observed_direct_kinds": coverage["observed_direct_operand_kinds"],
        "not_observed_direct_kinds": coverage["direct_operand_kinds_not_observed"], "proves_novelty": False}
    payload["messages"][0]["content"] += NOTE
    payload["messages"][1]["content"] = _canonical(context).decode("utf-8")
    raw = _canonical(payload)
    if len(raw) > MAX_REQUEST_BYTES:
        raise ValueError("La petición guiada supera el límite; no se recortarán motivos, reglas o entradas.")
    return raw, prepared, coverage


def _metadata(prepared_dir: Path, coverage_dir: Path, directory: Path, raw: bytes, prepared: dict) -> dict:
    return {"schema_version": 1, "protocol": "guided_compact_request_preview_v1", "status": "prepared_not_submitted",
            "run_dir": str(directory), "source_prepared": _origin(prepared_dir, PREPARED_FILES),
            "source_coverage": _origin(coverage_dir, COVERAGE_FILES), "reference": prepared["reference"],
            "request_sha256": sha256(raw).hexdigest(), "request_bytes": len(raw), "max_request_bytes": MAX_REQUEST_BYTES,
            "token_count": None, "fits_provider_context_verified": False, "submitted": False, "generation_ready": False,
            "provider_configured": False, "new_generation_permission": False, "executable": False,
            "generation_budget": prepared["generation_budget"], "inherited_attempt_usage": prepared["inherited_attempt_usage"],
            "history_entries_omitted": 0, "history_text_truncated": False,
            "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
            "code_sha256": _code_hashes()}


def prepare_guided_request(prepared_dir: str | Path, coverage_dir: str | Path, *,
                           output_dir: str | Path = ROOT / ".local/guided-compact-requests") -> Path:
    prepared_dir, coverage_dir = Path(prepared_dir).resolve(), Path(coverage_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("guided_compact_request_started", prepared_dir=str(prepared_dir), coverage_dir=str(coverage_dir))
    try:
        raw, prepared, _ = _build(prepared_dir, coverage_dir)
        record = _metadata(prepared_dir, coverage_dir, journal.directory, raw, prepared)
        _write_exclusive(journal.directory / "request.json", raw)
        current_raw, current_prepared, _ = _build(prepared_dir, coverage_dir)
        current = _metadata(prepared_dir, coverage_dir, journal.directory, current_raw, current_prepared)
        if current_raw != raw or _canonical(current) != _canonical(record):
            raise ValueError("Las fuentes cambiaron durante la preparación guiada.")
        _seal(journal, "guided.json", record, "guided_compact_request_prepared")
    except Exception as error:
        journal.record("guided_compact_request_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise ValueError(f"Petición guiada detenida: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_guided_request(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "guided.json", "guided_compact_request_prepared")
    prepared_dir, coverage_dir = Path(record["source_prepared"]["directory"]), Path(record["source_coverage"]["directory"])
    raw, prepared, _ = _build(prepared_dir, coverage_dir)
    expected = _metadata(prepared_dir, coverage_dir, directory, raw, prepared)
    if _canonical(record) != _canonical(expected) or _read(directory / "request.json", MAX_REQUEST_BYTES) != raw:
        raise ValueError("La petición guiada, fuentes, presupuesto o código han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — cobertura en una petición futura sin envío")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--prepared-run", type=Path, required=True)
    prepare.add_argument("--coverage-run", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify": print(json.dumps(verify_guided_request(args.run), ensure_ascii=True))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(prepare_guided_request(args.prepared_run, args.coverage_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Petición guiada no verificable: {error}\n")


if __name__ == "__main__": main()
