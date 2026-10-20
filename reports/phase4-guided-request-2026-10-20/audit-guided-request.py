"""Petición guiada real sin enviar, manteniendo presupuestos y evidencias anteriores."""

from hashlib import sha256
import json
from pathlib import Path
import runpy
from unittest.mock import patch

from trading_ai.evidence import verify_evidence
from trading_ai.guided_compact_request import prepare_guided_request, verify_guided_request
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _seal
from trading_ai.structured_generation import generation_budget_status


PREPARED = ROOT / ".local/compact-requests/c787e8461793402788239222e3b11552"
COVERAGE = ROOT / ".local/rule-coverage/048d7ee5c7da4292b09f2e952882626a"
REQUEST = ROOT / ".local/structured-draft-requests/1646833181eb44c386eb32872f245afa"
ARCHIVE = ROOT / "reports/phase4-guided-request-2026-10-20"


def main():
    if ARCHIVE.exists(): raise ValueError("La petición guiada ya tiene evidencia archivada.")
    previous = runpy.run_path(str(ROOT / ".local/audit-compact-candidate.py"))
    manifests = [ROOT / "reports" / folder / "snapshot.json" for folder in previous["HISTORY"]]
    manifests += [ROOT / "reports" / folder / "snapshot.json" for folder in (
        "phase4-compact-candidate-2026-10-20", "phase4-compact-memory-request-2026-10-20", "phase4-rule-coverage-2026-10-20")]
    before = verify_evidence(manifests, with_originals=True)
    budget_before = generation_budget_status(REQUEST)
    status_sha = sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()
    journal = RunJournal(ROOT / ".local/guided-request-audits")
    journal.record("guided_request_audit_started", copies_checked=before["copies_verified"])
    io = {"provider_calls": 0, "signals": 0, "backtests": 0, "outer_reads": 0}
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        if path.name in ("evaluation.xml", "comparison.json"):
            io["outer_reads"] += 1
            raise ValueError("No se permite abrir evaluación exterior.")
        return actual_open(path, *args, **kwargs)
    def blocked(kind):
        def fail(*args, **kwargs):
            io[kind] += 1
            raise ValueError("Ruta prohibida en la preparación guiada: " + kind)
        return fail
    output = ROOT / ".local/guided-compact-requests"
    with patch.object(Path, "open", guarded), \
            patch("trading_ai.compact_ollama.CompactOllamaProvider.complete", blocked("provider_calls")), \
            patch("trading_ai.compact_ollama.CompactOllamaProvider.describe", blocked("provider_calls")), \
            patch("socket.socket.connect", blocked("provider_calls")), \
            patch("trading_ai.rules.RuleStrategy.generate_signals", blocked("signals")), \
            patch("trading_ai.rule_execution._calculate", blocked("backtests")):
        before_dirs = set(output.glob("*"))
        try:
            guided_dir = prepare_guided_request(PREPARED, COVERAGE, output_dir=output)
            guided, error = verify_guided_request(guided_dir), None
        except ValueError as failure:
            new_dirs = set(output.glob("*")) - before_dirs
            if len(new_dirs) != 1: raise
            guided_dir, = new_dirs
            guided, error = None, str(failure)
    after = verify_evidence(manifests, with_originals=True)
    if (before != after or generation_budget_status(REQUEST) != budget_before or any(io.values())
            or sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest() != status_sha):
        raise ValueError("La preparación alteró una evidencia, presupuesto, fase o ruta bloqueada.")
    record = {"schema_version": 1, "status": "prepared_without_permission" if guided else "preparation_blocked_preserved",
              "guided_dir": str(guided_dir), "source_prepared": str(PREPARED), "source_coverage": str(COVERAGE),
              "request_bytes": None if guided is None else guided["request_bytes"], "error": error,
              "token_count": None, "fits_provider_context_verified": False,
              "budget_before": budget_before, "budget_after": budget_before, "new_generation_permission": False,
              "io_guard": io, "old_copies_and_original_references_checked": before["copies_verified"],
              "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
              "project_status_sha256": status_sha, "phase_closed": False, "executable": False}
    _seal(journal, "audit.json", record, "guided_request_audit_completed")
    ARCHIVE.mkdir()
    files = {}
    def copy(source, name):
        raw = source.read_bytes()
        target = ARCHIVE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        _write_exclusive(target, raw)
        files[name] = {"source": str(source), "sha256": sha256(raw).hexdigest()}
    for prefix, directory in (("guided", guided_dir), ("audit", journal.directory)):
        for source in sorted(directory.iterdir()):
            if source.is_file(): copy(source, prefix + "/" + source.name)
    copy(Path(__file__).resolve(), "audit-guided-request.py")
    _write_exclusive(ARCHIVE / "snapshot.json", json.dumps({"schema_version": 1, "files": files}, ensure_ascii=False, indent=2).encode("utf-8"))
    verify_evidence([ARCHIVE / "snapshot.json"], with_originals=True)
    print(json.dumps({"audit_dir": str(journal.directory), "guided_dir": str(guided_dir), "status": record["status"],
                      "request_bytes": record["request_bytes"], "io_guard": io,
                      "old_copies_checked": before["copies_verified"], "new_copies_checked": len(files)}, ensure_ascii=True))


if __name__ == "__main__": main()
