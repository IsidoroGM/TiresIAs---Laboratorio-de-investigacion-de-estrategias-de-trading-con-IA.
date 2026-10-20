"""Cobertura real sin nuevas propuestas, cálculos o cambios de presupuesto."""

from hashlib import sha256
import json
from pathlib import Path
import runpy
from unittest.mock import patch

from trading_ai.evidence import verify_evidence
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_coverage import capture_rule_coverage, verify_rule_coverage
from trading_ai.rule_planning import _seal
from trading_ai.structured_generation import generation_budget_status


CONTEXT = ROOT / ".local/structured-draft-contexts/2d35c3461d234499a1c9300470f6f130"
HISTORY = ROOT / ".local/compact-history/a6bb9a6824904602aa0014905adfb31b"
REQUEST = ROOT / ".local/structured-draft-requests/1646833181eb44c386eb32872f245afa"
ARCHIVE = ROOT / "reports/phase4-rule-coverage-2026-10-20"


def main():
    if ARCHIVE.exists(): raise ValueError("Esta cobertura ya tiene evidencia; no se sobrescribirá.")
    previous = runpy.run_path(str(ROOT / ".local/audit-compact-candidate.py"))
    manifests = [ROOT / "reports" / folder / "snapshot.json" for folder in previous["HISTORY"]]
    manifests += [ROOT / "reports" / folder / "snapshot.json" for folder in (
        "phase4-compact-candidate-2026-10-20", "phase4-compact-memory-request-2026-10-20")]
    before = verify_evidence(manifests, with_originals=True)
    budget_before = generation_budget_status(REQUEST)
    status_sha = sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()
    journal = RunJournal(ROOT / ".local/rule-coverage-audits")
    journal.record("rule_coverage_audit_started", copies_checked=before["copies_verified"])
    io = {"provider_calls": 0, "signals": 0, "backtests": 0, "outer_reads": 0}
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        if path.name in ("evaluation.xml", "comparison.json"):
            io["outer_reads"] += 1
            raise ValueError("La cobertura no puede abrir evaluación exterior.")
        return actual_open(path, *args, **kwargs)
    def blocked(kind):
        def fail(*args, **kwargs):
            io[kind] += 1
            raise ValueError("No se permite esta acción en cobertura: " + kind)
        return fail
    with patch.object(Path, "open", guarded), \
            patch("trading_ai.compact_ollama.CompactOllamaProvider.complete", blocked("provider_calls")), \
            patch("trading_ai.compact_ollama.CompactOllamaProvider.describe", blocked("provider_calls")), \
            patch("socket.socket.connect", blocked("provider_calls")), \
            patch("trading_ai.rules.RuleStrategy.generate_signals", blocked("signals")), \
            patch("trading_ai.rule_execution._calculate", blocked("backtests")):
        coverage_dir = capture_rule_coverage(CONTEXT, history_dir=HISTORY)
        coverage = verify_rule_coverage(coverage_dir)
    after = verify_evidence(manifests, with_originals=True)
    if (before != after or generation_budget_status(REQUEST) != budget_before or any(io.values())
            or sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest() != status_sha):
        raise ValueError("La cobertura cambió una fuente, presupuesto, fase o ruta bloqueada.")
    record = {"schema_version": 1, "status": "diagnostic_only", "coverage_dir": str(coverage_dir),
              "counts": coverage["counts"], "observed_direct_operand_kinds": coverage["observed_direct_operand_kinds"],
              "direct_operand_kinds_not_observed": coverage["direct_operand_kinds_not_observed"],
              "io_guard": io, "budget_before": budget_before, "budget_after": budget_before,
              "old_copies_and_original_references_checked": before["copies_verified"],
              "new_usage": coverage["new_usage"], "semantic_equivalence_proven": False,
              "strategy_novelty_proven": False, "strategy_selected": False, "executable": False,
              "project_status_sha256": status_sha, "phase_closed": False}
    _seal(journal, "audit.json", record, "rule_coverage_audit_completed")
    ARCHIVE.mkdir()
    files = {}
    def copy(source, name):
        raw = source.read_bytes()
        target = ARCHIVE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        _write_exclusive(target, raw)
        files[name] = {"source": str(source), "sha256": sha256(raw).hexdigest()}
    for prefix, directory in (("coverage", coverage_dir), ("audit", journal.directory)):
        for source in sorted(directory.iterdir()):
            if source.is_file(): copy(source, prefix + "/" + source.name)
    copy(Path(__file__).resolve(), "audit-rule-coverage.py")
    _write_exclusive(ARCHIVE / "snapshot.json", json.dumps({"schema_version": 1, "files": files}, ensure_ascii=False, indent=2).encode("utf-8"))
    verify_evidence([ARCHIVE / "snapshot.json"], with_originals=True)
    print(json.dumps({"audit_dir": str(journal.directory), "coverage_dir": str(coverage_dir),
                      "counts": coverage["counts"], "io_guard": io, "old_copies_checked": before["copies_verified"],
                      "new_copies_checked": len(files)}, ensure_ascii=True))


if __name__ == "__main__": main()
