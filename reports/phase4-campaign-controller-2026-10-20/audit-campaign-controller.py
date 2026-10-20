"""Consulta de campaña real sin capturas ficticias, envíos o cálculos."""

from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sqlite3
import sys
from unittest.mock import patch

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))

from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_controller as controller
from trading_ai import campaign_ledger as ledger
from trading_ai.evidence import verify_evidence
from trading_ai.holdout import _write_exclusive
from trading_ai.research import RunJournal
from trading_ai.rule_planning import _seal


ARCHIVE = ROOT / "reports/phase4-campaign-controller-2026-10-20"


def main():
    if ARCHIVE.exists(): raise ValueError("La evidencia ya existe; no se sobrescribe.")
    old = runpy.run_path(str(ROOT / ".local/audit-campaign-plan.py"))
    names = (*old["HISTORY"], "phase4-campaign-plan-2026-10-20", "phase4-campaign-ledger-2026-10-20",
             "phase4-campaign-attempts-2026-10-20")
    snapshots = [ROOT / "reports" / name / "snapshot.json" for name in names]
    journal = RunJournal(ROOT / ".local/campaign-controller-audits")
    journal.record("campaign_controller_audit_started")
    counters = {key: 0 for key in ("network", "provider", "calculation", "legacy_reservation",
                                  "outer_evaluation", "campaign_reservation", "capture_write")}
    try:
        prior = verify_evidence(snapshots, with_originals=True)
        database = ledger.LEDGER_PATH.read_bytes()
        status_sha = sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()
        accesses = old["access_fingerprints"]()
        roots = {str(path): path.exists() for path in (attempts.ACCESS_ROOT, attempts.ATTEMPTS_ROOT)}
        connection = sqlite3.connect(ledger.LEDGER_PATH.as_uri() + "?mode=ro", uri=True)
        try:
            rows = connection.execute("SELECT scope_id FROM scopes").fetchall()
        finally: connection.close()
        if len(rows) != 1: raise ValueError("No hay un único ámbito real identificable para esta auditoría.")

        def forbidden(key):
            def reject(*args, **kwargs):
                counters[key] += 1
                raise AssertionError("Herramienta bloqueada en auditoría: " + key)
            return reject

        original_open = Path.open
        def guarded_open(path, *args, **kwargs):
            if path.name in ("evaluation.xml", "comparison.json"):
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
                ("trading_ai.campaign_attempts.mark_submission_intent", "capture_write"),
                ("trading_ai.campaign_attempts.record_observation", "capture_write")):
                stack.enter_context(patch(target, forbidden(key)))
            stack.enter_context(patch.object(Path, "open", guarded_open))
            result = controller.inspect_controller(rows[0][0])

        if (any(counters.values()) or result["status"] != "inactive" or result["proposals"]
                or result["reserved_model_requests"] or result["reserved_backtests"]
                or result["execution_authorized"] or not result["current_source_freshness_verified"]):
            raise AssertionError("El control no conserva el estado inactivo esperado.")
        if (ledger.LEDGER_PATH.read_bytes() != database or old["access_fingerprints"]() != accesses
                or any(Path(path).exists() != exists for path, exists in roots.items())
                or sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest() != status_sha
                or verify_evidence(snapshots, with_originals=True) != prior):
            raise AssertionError("Cambió el registro, las reservas, fuentes o evidencias anteriores.")
        journal.save("controller.json", result)
        digest = sha256((journal.directory / "controller.json").read_bytes()).hexdigest()
        _write_exclusive(journal.directory / "controller.json.sha256", (digest + "\n").encode("ascii"))
        audit = {"schema_version": 1, "status": "verified_inactive_no_captures", "scope_id": rows[0][0],
                 "blocked_calls": counters, "prior_inventories": len(snapshots),
                 "prior_copies_verified": prior["copies_verified"],
                 "prior_original_references_verified": prior["original_references_verified"],
                 "access_files_unchanged": len(accesses), "capture_roots_unchanged": roots,
                 "database_sha256": sha256(database).hexdigest(), "project_status_sha256": status_sha,
                 "current_source_freshness_verified": result["current_source_freshness_verified"],
                 "new_usage": result["new_usage"], "controller_sha256": digest}
        _seal(journal, "audit.json", audit, "campaign_controller_audit_completed")
        sources = {name: journal.directory / name for name in
                   ("controller.json", "controller.json.sha256", "audit.json", "audit.json.sha256", "events.jsonl")}
        sources.update({"audit-campaign-controller.py": Path(__file__).resolve(),
                        "source/campaign_controller.py": ROOT / "trading_ai/campaign_controller.py",
                        "source/campaign_controller_tests.py": ROOT / "tests/test_campaign_controller.py"})
        contents = {name: path.read_bytes() for name, path in sources.items()}
        ARCHIVE.mkdir(exist_ok=False)
        files = {}
        for name, content in contents.items():
            destination = ARCHIVE / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            _write_exclusive(destination, content)
            files[name] = {"source": str(sources[name]), "sha256": sha256(content).hexdigest()}
        _write_exclusive(ARCHIVE / "snapshot.json", json.dumps(
            {"schema_version": 1, "files": files}, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
        checked = verify_evidence(snapshots + [ARCHIVE / "snapshot.json"], with_originals=True)
        print(json.dumps({"audit_run": str(journal.directory), "blocked_calls": counters,
                          "copies_verified": checked["copies_verified"], "inventories": len(snapshots) + 1,
                          "new_usage": result["new_usage"]}, ensure_ascii=True))
    except Exception as error:
        journal.record("campaign_controller_audit_failed", error_type=type(error).__name__, message=str(error)[:1000])
        raise


if __name__ == "__main__": main()
