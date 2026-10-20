"""Audita una consulta sin inventar capturas en la campaña inactiva de la aplicación."""

from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))

from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_ledger as ledger
from trading_ai.evidence import verify_evidence
from trading_ai.holdout import _write_exclusive
from trading_ai.research import RunJournal
from trading_ai.rule_planning import _seal


ARCHIVE = ROOT / "reports/phase4-campaign-attempts-2026-10-20"
PLAN = ROOT / ".local/campaign-plans/37316f24fb92479aa7b9af4ab8134ed0"


def fingerprint(directory):
    return None if not directory.exists() else {
        str(path.relative_to(directory)): sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*") if path.is_file()}


def main():
    if ARCHIVE.exists(): raise ValueError("La evidencia ya existe; no se sobrescribe.")
    prior = runpy.run_path(str(ROOT / ".local/audit-campaign-plan.py"))
    names = prior["HISTORY"] + ("phase4-campaign-plan-2026-10-20", "phase4-campaign-ledger-2026-10-20")
    snapshots = [ROOT / "reports" / name / "snapshot.json" for name in names]
    scope = json.loads((PLAN / "campaign.json").read_bytes())["scope_id"]
    journal = RunJournal(ROOT / ".local/campaign-attempt-audits")
    journal.record("campaign_attempt_audit_started", scope_id=scope)
    counters = {key: 0 for key in ("network", "provider", "calculation", "legacy_reservation", "outer_evaluation",
                                  "campaign_reservation", "capture_write")}
    try:
        before = verify_evidence(snapshots, with_originals=True)
        accesses = prior["access_fingerprints"]()
        registry_sha = sha256(ledger.LEDGER_PATH.read_bytes()).hexdigest()
        status_sha = sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()
        roots = {path: fingerprint(path) for path in (attempts.ACCESS_ROOT, attempts.ATTEMPTS_ROOT)}

        def forbidden(key):
            def reject(*args, **kwargs):
                counters[key] += 1
                raise AssertionError("Herramienta bloqueada: " + key)
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
                ("trading_ai.structured_generation.reserve_compact_generation", "legacy_reservation"),
                ("trading_ai.campaign_ledger.reserve_proposal", "campaign_reservation"),
                ("trading_ai.campaign_ledger.reserve_comparison", "campaign_reservation"),
                ("trading_ai.campaign_attempts.prepare_attempt", "capture_write"),
                ("trading_ai.campaign_attempts.mark_submission_intent", "capture_write"),
                ("trading_ai.campaign_attempts.record_observation", "capture_write")):
                stack.enter_context(patch(target, forbidden(key)))
            stack.enter_context(patch.object(Path, "open", guarded_open))
            summary = attempts.inspect_attempts(scope)
        if (summary["attempts"] or summary["usage"] != attempts.ZERO_USAGE or summary["execution_authorized"]
                or any(counters.values())):
            raise AssertionError("La campaña inactiva no conserva su consulta vacía.")
        if registry_sha != sha256(ledger.LEDGER_PATH.read_bytes()).hexdigest(): raise AssertionError("Cambió el registro SQLite.")
        if accesses != prior["access_fingerprints"](): raise AssertionError("Cambió una reserva histórica.")
        if roots != {path: fingerprint(path) for path in roots}: raise AssertionError("Se crearon o cambiaron capturas.")
        if status_sha != sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest(): raise AssertionError("Cambió PROJECT_STATUS.md.")
        if before != verify_evidence(snapshots, with_originals=True): raise AssertionError("Cambió evidencia anterior.")
        _seal(journal, "status.json", summary, "campaign_attempt_status_captured")
        audit = {"schema_version": 1, "status": "verified_read_only_no_attempts", "scope_id": scope,
                 "sqlite_sha256_unchanged": registry_sha, "project_status_sha256": status_sha,
                 "previous_inventories": len(names), "previous_copies_verified": before["copies_verified"],
                 "legacy_access_files_unchanged": len(accesses), "capture_roots_unchanged": True,
                 "attempts_created": 0, "blocked_calls": counters, "new_usage": summary["new_usage_of_query"],
                 "executable": False}
        _seal(journal, "audit.json", audit, "campaign_attempt_audit_completed")
        sources = {name: journal.directory / name for name in
                   ("status.json", "status.json.sha256", "audit.json", "audit.json.sha256", "events.jsonl")}
        sources.update({"audit-campaign-attempts.py": Path(__file__).resolve(),
                        "source/campaign_attempts.py": ROOT / "trading_ai/campaign_attempts.py",
                        "source/campaign_attempt_tests.py": ROOT / "tests/test_campaign_attempts.py"})
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
        result = verify_evidence(snapshots + [ARCHIVE / "snapshot.json"], with_originals=True)
        print(json.dumps({"audit_run": str(journal.directory), "copies_verified": result["copies_verified"],
                          "new_copies": len(files), "blocked_calls": counters, "new_usage": audit["new_usage"]}, ensure_ascii=True))
    except Exception as error:
        journal.record("campaign_attempt_audit_failed", error_type=type(error).__name__, message=str(error)[:1000])
        raise


if __name__ == "__main__": main()
