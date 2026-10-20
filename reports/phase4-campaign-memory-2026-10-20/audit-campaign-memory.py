"""Memoria real vacía y tiempos de lectura; sin ejecutar propuestas pendientes."""

from contextlib import ExitStack
from hashlib import sha256
import io
import json
from pathlib import Path
import runpy
import sqlite3
import sys
from time import perf_counter
from unittest.mock import patch

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))

from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_memory as memory
from trading_ai import campaign_permission as permissions
from trading_ai.evidence import verify_evidence
from trading_ai.holdout import _write_exclusive
from trading_ai.research import RunJournal
from trading_ai.rule_planning import _seal
from trading_ai.verification_session import VerificationSession

ARCHIVE = ROOT / "reports/phase4-campaign-memory-2026-10-20"


def main():
    if ARCHIVE.exists(): raise ValueError("La evidencia ya existe; no se sobrescribe.")
    old = runpy.run_path(str(ROOT / ".local/audit-campaign-plan.py"))
    names = (*old["HISTORY"], "phase4-campaign-plan-2026-10-20", "phase4-campaign-ledger-2026-10-20",
             "phase4-campaign-attempts-2026-10-20", "phase4-campaign-controller-2026-10-20",
             "phase4-campaign-review-2026-10-20", "phase4-campaign-execution-2026-10-20")
    snapshots = [ROOT / "reports" / name / "snapshot.json" for name in names]
    journal = RunJournal(ROOT / ".local/campaign-memory-audits")
    journal.record("campaign_memory_audit_started")
    counters = {key: 0 for key in ("network", "provider", "calculation", "legacy_reservation", "outer_evaluation",
                                  "campaign_reservation", "capture_write", "review_or_plan_write", "permission_or_execution_write")}
    try:
        prior = verify_evidence(snapshots, with_originals=True)
        database = ledger.LEDGER_PATH.read_bytes()
        status_sha = sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()
        accesses = old["access_fingerprints"]()
        folders = (permissions.ACCESS_ROOT, ROOT / ".local/campaign-permissions", ROOT / ".local/campaign-executions")
        def fingerprint():
            return {str(folder): {str(path.relative_to(folder)): sha256(path.read_bytes()).hexdigest()
                                 for path in folder.rglob("*") if path.is_file()} if folder.exists() else None for folder in folders}
        roots = fingerprint()
        connection = sqlite3.connect(ledger.LEDGER_PATH.as_uri() + "?mode=ro", uri=True)
        try: rows = connection.execute("SELECT scope_id FROM scopes").fetchall()
        finally: connection.close()
        if len(rows) != 1: raise ValueError("No hay un único ámbito real identificable.")
        scope = rows[0][0]
        def forbidden(key):
            def reject(*args, **kwargs):
                counters[key] += 1
                raise AssertionError("Acción bloqueada en auditoría: " + key)
            return reject
        original_open = io.open
        def guarded_open(path, *args, **kwargs):
            if isinstance(path, (str, Path)) and Path(path).name in ("evaluation.xml", "comparison.json"):
                return forbidden("outer_evaluation")(path)
            return original_open(path, *args, **kwargs)
        with ExitStack() as stack:
            for target, key in (
                ("socket.socket.connect", "network"),
                ("trading_ai.compact_ollama.CompactOllamaProvider.complete", "provider"),
                ("trading_ai.compact_ollama.CompactOllamaProvider.describe", "provider"),
                ("trading_ai.rule_execution._calculate", "calculation"),
                ("trading_ai.experiments.run_backtest", "calculation"),
                ("trading_ai.structured_generation.reserve_compact_generation", "legacy_reservation"),
                ("trading_ai.campaign_ledger.register_campaign", "campaign_reservation"),
                ("trading_ai.campaign_ledger.reserve_proposal", "campaign_reservation"),
                ("trading_ai.campaign_ledger.reserve_comparison", "campaign_reservation"),
                ("trading_ai.campaign_attempts.prepare_attempt", "capture_write"),
                ("trading_ai.campaign_attempts.record_observation", "capture_write"),
                ("trading_ai.campaign_review.review_capture", "review_or_plan_write"),
                ("trading_ai.campaign_experiment.prepare_plan", "review_or_plan_write"),
                ("trading_ai.campaign_permission.grant_permission", "permission_or_execution_write"),
                ("trading_ai.campaign_execution.execute", "permission_or_execution_write")):
                stack.enter_context(patch(target, forbidden(key)))
            stack.enter_context(patch.object(io, "open", guarded_open))
            start = perf_counter()
            plain = memory.inspect_memory(scope)
            uncached_seconds = perf_counter() - start
            with VerificationSession() as cache:
                start = perf_counter()
                cached = memory.inspect_memory(scope)
                first_cached_seconds = perf_counter() - start
                start = perf_counter()
                warmed = memory.inspect_memory(scope)
                warmed_seconds = perf_counter() - start
                if plain != cached or plain != warmed: raise AssertionError("La caché cambió el resultado de memoria.")
                saved = memory.save_memory(scope)
                if memory.verify_memory(saved) != plain: raise AssertionError("La memoria guardada no coincide.")
                cache_stats = dict(cache.stats)
        state = ledger.inspect_campaign(scope)
        if (any(counters.values()) or plain["proposals"] or plain["comparisons"] or plain["requires_stop"]
                or state["reserved_model_requests"] or state["reserved_backtests"]):
            raise AssertionError("La campaña no conserva su estado inactivo sin propuestas o cálculos.")
        if (ledger.LEDGER_PATH.read_bytes() != database or old["access_fingerprints"]() != accesses or fingerprint() != roots
                or sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest() != status_sha
                or verify_evidence(snapshots, with_originals=True) != prior):
            raise AssertionError("Cambió el registro, las reservas, fuentes o evidencias previas.")
        timings = {"uncached_query_seconds": uncached_seconds, "first_cached_query_seconds": first_cached_seconds,
                   "warmed_cached_query_seconds": warmed_seconds, "cache_stats": cache_stats,
                   "scope": "same_empty_registered_campaign_read_queries_not_backtest_or_model_timing"}
        audit = {"schema_version": 1, "status": "verified_empty_memory_no_research_actions", "scope_id": scope,
                 "blocked_calls": counters, "prior_inventories": len(snapshots), "prior_copies_verified": prior["copies_verified"],
                 "prior_original_references_verified": prior["original_references_verified"], "access_files_unchanged": len(accesses),
                 "roots_unchanged": roots, "database_sha256": sha256(database).hexdigest(), "project_status_sha256": status_sha,
                 "memory_run": str(saved), "new_usage": plain["new_usage"], "timings": timings,
                 "inherited_compact_usage": plain["registration"]["inherited_usage"],
                 "automatic_local_cycle_enabled": False, "future_model_context_integrated": False}
        _seal(journal, "audit.json", audit, "campaign_memory_audit_completed")
        sources = {name: journal.directory / name for name in ("audit.json", "audit.json.sha256", "events.jsonl")}
        sources["audit-campaign-memory.py"] = Path(__file__).resolve()
        for name in memory.MEMORY_FILES: sources["memory/" + name] = saved / name
        for name in ("campaign_memory", "verification_session"):
            sources["source/" + name + ".py"] = ROOT / "trading_ai" / (name + ".py")
            sources["source/" + name + "_tests.py"] = ROOT / "tests" / ("test_" + name + ".py")
        sources["source/campaign_memory_integration_tests.py"] = ROOT / "tests/test_campaign_memory_integration.py"
        sources["focused-tests.xml"] = ROOT / ".local/campaign-memory-final-tests.xml"
        sources["claim-tests.xml"] = ROOT / ".local/campaign-memory-claim-tests.xml"
        sources["recheck-tests.xml"] = ROOT / ".local/campaign-memory-final-recheck.xml"
        contents = {name: path.read_bytes() for name, path in sources.items()}
        ARCHIVE.mkdir(exist_ok=False)
        files = {}
        for name, content in contents.items():
            destination = ARCHIVE / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            _write_exclusive(destination, content)
            files[name] = {"source": str(sources[name]), "sha256": sha256(content).hexdigest()}
        _write_exclusive(ARCHIVE / "snapshot.json", json.dumps({"schema_version": 1, "files": files},
                         ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
        checked = verify_evidence(snapshots + [ARCHIVE / "snapshot.json"], with_originals=True)
        print(json.dumps({"audit_run": str(journal.directory), "memory_run": str(saved), "timings": timings,
                          "copies_verified": checked["copies_verified"], "new_inventory_entries": len(files),
                          "inventories": len(snapshots) + 1, "blocked_calls": counters, "new_usage": plain["new_usage"]}, ensure_ascii=True))
    except Exception as error:
        journal.record("campaign_memory_audit_failed", error_type=type(error).__name__, message=str(error)[:1000])
        raise


if __name__ == "__main__": main()
