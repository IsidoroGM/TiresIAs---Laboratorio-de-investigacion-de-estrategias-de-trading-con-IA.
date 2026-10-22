"""Contexto de desarrollo y reservas compartidas para borradores; sin generación ni ejecución."""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.idea_memory import capture_memory, validate_memory
from trading_ai.research import ROOT, RunJournal
from trading_ai.robustness import _development
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_draft import _code_hashes as _draft_hashes, verify_draft
from trading_ai import structured_ideas as ideas


def _claims(reference: dict) -> dict:
    paths = sorted(ideas.ACCESS_ROOT.glob("*.json"))
    if len(paths) > ideas.MAX_HISTORY:
        raise ValueError("El historial compartido supera su límite; no se descartarán reservas.")
    entries = []
    for path in paths:
        raw = _read(path, 8192)
        claim = ideas._claim_value(raw)
        identity = claim["identity"]
        if (not isinstance(identity["spec_sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", identity["spec_sha256"]) is None
                or path.name != sha256(_canonical(identity)).hexdigest() + ".json"):
            raise ValueError("La reserva compartida no coincide con su identidad.")
        if identity["reference"] == reference:
            entries.append({"path": str(path.resolve()), "sha256": sha256(raw).hexdigest(), "claim": claim})
    return {"schema_version": 1, "reference": reference, "entries": entries}


def _validate_claims(snapshot: dict, reference: dict) -> None:
    if (not isinstance(snapshot, dict) or set(snapshot) != {"schema_version", "reference", "entries"}
            or type(snapshot["schema_version"]) is not int or snapshot["schema_version"] != 1
            or snapshot["reference"] != reference or not isinstance(snapshot["entries"], list)
            or len(snapshot["entries"]) > ideas.MAX_HISTORY):
        raise ValueError("Copia de reservas incompatible con el desarrollo.")
    seen = set()
    for item in snapshot["entries"]:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "claim"}:
            raise ValueError("Entrada de reserva incompatible.")
        path = Path(item["path"])
        if not path.is_absolute() or path.parent != ideas.ACCESS_ROOT.resolve():
            raise ValueError("La copia debe apuntar al registro compartido de reservas.")
        raw = _read(path, 8192)
        claim = ideas._claim_value(raw)
        if (item["sha256"] != sha256(raw).hexdigest() or item["claim"] != claim
                or claim["identity"]["reference"] != reference or item["path"] in seen
                or not isinstance(claim["identity"]["spec_sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", claim["identity"]["spec_sha256"]) is None
                or path.name != sha256(_canonical(claim["identity"])).hexdigest() + ".json"):
            raise ValueError("Una reserva consumida ha cambiado o está duplicada.")
        seen.add(item["path"])


def _code_hashes() -> dict:
    return {**_draft_hashes(), "structured_draft_context.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _record(directory: Path, frozen_dir: Path, draft_dir: Path | None) -> dict:
    frozen, reference, _ = _development(frozen_dir)
    raw = {name: _read(directory / name, 2 * 1024 * 1024)
           for name in ("memory.json", "rules-memory.json", "claims.json")}
    memory, rules, claims = (_strict_json(raw[name]) for name in ("memory.json", "rules-memory.json", "claims.json"))
    validate_memory(memory, reference)
    ideas._validate_rules_memory(rules, reference)
    _validate_claims(claims, reference)
    for entry in rules["entries"]:
        if not any(item["claim"]["identity"]["spec_sha256"] == entry["spec_sha256"]
                   and item["claim"]["run_dir"] == entry["origin"]["directory"] for item in claims["entries"]):
            raise ValueError("Una regla registrada carece de su reserva compartida en la copia.")
    candidate = None
    if draft_dir is not None:
        draft = verify_draft(draft_dir)
        matches = [item["path"] for item in claims["entries"]
                   if item["claim"]["identity"]["spec_sha256"] == draft["spec_sha256"]]
        candidate = {"directory": str(draft_dir), "sha256": {
            name: sha256(_read(draft_dir / name, 2 * 1024 * 1024)).hexdigest()
            for name in ("draft.json", "draft.json.sha256", "input.json", "report.md", "events.jsonl")},
            "spec_sha256": draft["spec_sha256"], "matching_claim_paths": matches,
            "identity_check": "duplicate_or_reserved" if matches else "not_found_in_captured_claims",
            "source_usage": draft["source_usage"], "eligible_for_session": False}
    return {"schema_version": 1, "protocol": "structured_draft_context_v1", "status": "context_snapshot_only",
            "run_dir": str(directory), "reference": reference,
            "objective": {"origin": "frozen_development_registration", "criterion": frozen["proposal"]["criterion"]},
            "controls": deepcopy(frozen["policy"]), "data": deepcopy(frozen["development_result"]["source"]),
            "scope": "known_development_history_only", "outer_evaluation_allowed": False,
            "memory_sha256": {name: sha256(value).hexdigest() for name, value in raw.items()},
            "counts": {"legacy_ideas": len(memory["entries"]), "registered_rules": len(rules["entries"]),
                       "consumed_rule_claims": len(claims["entries"])},
            "candidate": candidate, "review_decisions_complete": False,
            "generation_ready": False, "eligible_for_session": False, "executable": False,
            "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0,
                          "api_cost_usd": "0", "backtests": 0}, "code_sha256": _code_hashes()}


def _report(record: dict) -> str:
    candidate = record["candidate"]
    state = "Sin borrador vinculado." if candidate is None else "Identidad del borrador: " + candidate["identity_check"] + "."
    return "\n".join([
        "# Contexto de desarrollo del borrador", "",
        "Objetivo y controles copiados del registro congelado, sin selección por resultados.",
        "Histórico de desarrollo conocido; la evaluación exterior no se vuelve a consultar.", "",
        state, "",
        "Las reservas compartidas incluyen intentos sin propuesta terminada; no se liberan al cambiar de formato.",
        "No encontrar una identidad no demuestra novedad semántica o validez.",
        "Es una copia histórica: verificarla no garantiza que incluya entradas posteriores.",
        "Las decisiones de revisión estructurada aún no se recopilan en este contexto.",
        "No autoriza generación, revisión, sesiones ni simulaciones. Cero consultas nuevas y coste nuevo de API.", "",
    ])


def prepare_draft_context(frozen_dir: str | Path, *, draft_dir: str | Path | None = None,
                          output_dir: str | Path = ROOT / ".local/structured-draft-contexts") -> Path:
    frozen = Path(frozen_dir).resolve()
    draft = Path(draft_dir).resolve() if draft_dir is not None else None
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("structured_draft_context_started", frozen_dir=str(frozen))
    try:
        _, reference, _ = _development(frozen)
        claims = _claims(reference)
        journal.save("memory.json", capture_memory(frozen))
        journal.save("rules-memory.json", ideas._rules_memory(reference, frozen))
        journal.save("claims.json", claims)
        record = _record(journal.directory, frozen, draft)
        if _canonical(_claims(reference)) != _canonical(claims):
            raise ValueError("Las reservas cambiaron durante la captura del contexto.")
        _write_exclusive(journal.directory / "report.md", _report(record).encode("utf-8"))
        _seal(journal, "context.json", record, "structured_draft_context_completed")
    except Exception as error:
        journal.record("structured_draft_context_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       new_model_requests=0, new_api_cost_usd="0", backtests=0)
        raise ValueError(f"Contexto detenido: {error}. Registro: {journal.directory}") from error
    return journal.directory


def verify_draft_context(run_dir: str | Path) -> dict:
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "context.json", "structured_draft_context_completed")
    candidate = record["candidate"]
    draft = None if candidate is None else Path(candidate["directory"])
    expected = _record(directory, Path(record["reference"]["frozen_dir"]), draft)
    if (_canonical(record) != _canonical(expected)
            or _read(directory / "report.md", 16384) != _report(record).encode("utf-8")):
        raise ValueError("El contexto, sus fuentes, su código o su ubicación han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — contexto sin generación para borradores compactos")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--frozen-run", type=Path, required=True)
    prepare.add_argument("--draft-run", type=Path)
    prepare.add_argument("--output-dir", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            print(json.dumps(verify_draft_context(args.run), ensure_ascii=False))
        else:
            kwargs = {"output_dir": args.output_dir} if args.output_dir else {}
            print(prepare_draft_context(args.frozen_run, draft_dir=args.draft_run, **kwargs))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Contexto no verificable: {error}\n")


if __name__ == "__main__":
    main()
