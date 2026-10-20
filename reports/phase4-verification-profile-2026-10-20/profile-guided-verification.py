"""Perfil de una lectura real, sin modificar validadores o ejecutar modelos/backtests."""

import cProfile
from hashlib import sha256
import json
from pathlib import Path
import pstats
import runpy
from time import perf_counter
from unittest.mock import patch

from trading_ai.evidence import verify_evidence
from trading_ai.guided_compact_request import verify_guided_request
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _seal
from trading_ai.structured_generation import generation_budget_status


GUIDED = ROOT / ".local/guided-compact-requests/1a1d0783778243ac989ca1ab3fc49911"
REQUEST = ROOT / ".local/structured-draft-requests/1646833181eb44c386eb32872f245afa"
ARCHIVE = ROOT / "reports/phase4-verification-profile-2026-10-20"


def main():
    if ARCHIVE.exists(): raise ValueError("El perfil ya tiene evidencia; no se sobrescribirá.")
    previous = runpy.run_path(str(ROOT / ".local/audit-compact-candidate.py"))
    manifests = [ROOT / "reports" / folder / "snapshot.json" for folder in previous["HISTORY"]]
    manifests += [ROOT / "reports" / folder / "snapshot.json" for folder in (
        "phase4-compact-candidate-2026-10-20", "phase4-compact-memory-request-2026-10-20",
        "phase4-rule-coverage-2026-10-20", "phase4-guided-request-2026-10-20")]
    before = verify_evidence(manifests, with_originals=True)
    budget_before = generation_budget_status(REQUEST)
    status_sha = sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()
    journal = RunJournal(ROOT / ".local/verification-profiles")
    journal.record("verification_profile_started", guided_dir=str(GUIDED))
    io = {"provider_calls": 0, "signals": 0, "backtests": 0, "outer_reads": 0}
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        if path.name in ("evaluation.xml", "comparison.json"):
            io["outer_reads"] += 1
            raise ValueError("El perfil no puede abrir evaluación exterior.")
        return actual_open(path, *args, **kwargs)
    def blocked(kind):
        def fail(*args, **kwargs):
            io[kind] += 1
            raise ValueError("Acción prohibida al perfilar: " + kind)
        return fail
    profiler = cProfile.Profile()
    with patch.object(Path, "open", guarded), \
            patch("trading_ai.compact_ollama.CompactOllamaProvider.complete", blocked("provider_calls")), \
            patch("trading_ai.compact_ollama.CompactOllamaProvider.describe", blocked("provider_calls")), \
            patch("socket.socket.connect", blocked("provider_calls")), \
            patch("trading_ai.rules.RuleStrategy.generate_signals", blocked("signals")), \
            patch("trading_ai.strategies.SmaCrossoverStrategy.generate_signals", blocked("signals")), \
            patch("trading_ai.strategies.EmaCrossoverStrategy.generate_signals", blocked("signals")), \
            patch("trading_ai.rule_execution._calculate", blocked("backtests")), \
            patch("trading_ai.backtesting.run_backtest", blocked("backtests")), \
            patch("trading_ai.experiments.run_backtest", blocked("backtests")):
        started = perf_counter()
        record = profiler.runcall(verify_guided_request, GUIDED)
        elapsed = perf_counter() - started
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, line, function), (primitive, total, own, cumulative, _) in stats.stats.items():
        rows.append({"filename": filename, "line": line, "function": function, "primitive_calls": primitive,
                     "total_calls": total, "own_seconds": round(own, 6), "cumulative_seconds": round(cumulative, 6)})
    top = sorted(rows, key=lambda row: row["cumulative_seconds"], reverse=True)[:25]
    important = [row for row in rows if Path(row["filename"]).name in ("data.py", "robustness.py", "structured_draft_request.py", "structured_freshness.py", "compact_history.py")]
    profiler.dump_stats(str(journal.directory / "verification.pstats"))
    after = verify_evidence(manifests, with_originals=True)
    if (before != after or budget_before != generation_budget_status(REQUEST) or any(io.values())
            or status_sha != sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()):
        raise ValueError("El perfil modificó una fuente, presupuesto, fase o invocó una ruta bloqueada.")
    result = {"schema_version": 1, "status": "profiled_read_only", "guided_dir": str(GUIDED),
              "guided_request_sha256": record["request_sha256"], "elapsed_wall_seconds": round(elapsed, 6),
              "profile_total_calls": stats.total_calls, "profile_primitive_calls": stats.prim_calls,
              "top_cumulative_functions": top, "selected_module_functions": important,
              "concurrent_pytest": True, "benchmark_or_speedup_claimed": False, "code_optimized": False,
              "io_guard": io, "old_copies_and_original_references_checked": before["copies_verified"],
              "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
              "budget_before": budget_before, "budget_after": budget_before, "executable": False,
              "project_status_sha256": status_sha, "phase_closed": False}
    _seal(journal, "profile.json", result, "verification_profile_completed")
    ARCHIVE.mkdir()
    files = {}
    def copy(source, name):
        raw = source.read_bytes()
        _write_exclusive(ARCHIVE / name, raw)
        files[name] = {"source": str(source), "sha256": sha256(raw).hexdigest()}
    for path in sorted(journal.directory.iterdir()):
        if path.is_file(): copy(path, path.name)
    copy(Path(__file__).resolve(), "profile-guided-verification.py")
    _write_exclusive(ARCHIVE / "snapshot.json", json.dumps({"schema_version": 1, "files": files}, ensure_ascii=False, indent=2).encode("utf-8"))
    verify_evidence([ARCHIVE / "snapshot.json"], with_originals=True)
    print(json.dumps({"profile_dir": str(journal.directory), "elapsed_wall_seconds": elapsed,
                      "total_calls": stats.total_calls, "old_copies_checked": before["copies_verified"], "new_copies_checked": len(files),
                      "io_guard": io, "top_functions": [{**row, "filename": Path(row["filename"]).name} for row in top[:12]]}, ensure_ascii=True))


if __name__ == "__main__": main()
