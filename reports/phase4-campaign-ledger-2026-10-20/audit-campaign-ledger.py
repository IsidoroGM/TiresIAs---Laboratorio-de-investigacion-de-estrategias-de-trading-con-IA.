"""Registra la campaña inactiva y archiva una instantánea SQLite, sin ocupar huecos."""

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

from trading_ai import campaign_ledger as ledger
from trading_ai.evidence import verify_evidence
from trading_ai.holdout import _write_exclusive
from trading_ai.research import RunJournal
from trading_ai.rule_planning import _seal


PLAN = ROOT / ".local/campaign-plans/37316f24fb92479aa7b9af4ab8134ed0"
ARCHIVE = ROOT / "reports/phase4-campaign-ledger-2026-10-20"


def main():
    if ARCHIVE.exists(): raise ValueError("La evidencia ya existe; no se sobrescribe.")
    prior = runpy.run_path(str(ROOT / ".local/audit-campaign-plan.py"))
    history = prior["HISTORY"] + ("phase4-campaign-plan-2026-10-20",)
    snapshots = [ROOT / "reports" / name / "snapshot.json" for name in history]
    scope = json.loads((PLAN / "campaign.json").read_bytes())["scope_id"]
    journal = RunJournal(ROOT / ".local/campaign-ledger-audits")
    journal.record("campaign_ledger_audit_started", plan_dir=str(PLAN), scope_id=scope)
    counters = {key: 0 for key in ("network", "provider", "calculation", "legacy_reservation", "outer_evaluation")}
    try:
        before = verify_evidence(snapshots, with_originals=True)
        accesses = prior["access_fingerprints"]()
        status_sha = sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()
        initial = ledger.inspect_campaign(scope)
        if initial["status"] != "not_registered":
            raise ValueError("El ámbito ya está registrado; no se reiniciará esta auditoría.")

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
                ("trading_ai.experiments.run_backtest", "calculation"),
                ("trading_ai.structured_generation.reserve_compact_generation", "legacy_reservation")):
                stack.enter_context(patch(target, forbidden(key)))
            stack.enter_context(patch.object(Path, "open", guarded_open))
            state = ledger.register_campaign(PLAN)
            if ledger.inspect_campaign(scope) != state:
                raise AssertionError("La consulta no coincide con la inscripción.")
        if (state["reserved_model_requests"] or state["reserved_backtests"]
                or state["execution_authorized"] or any(counters.values())):
            raise AssertionError("El registro ocupó huecos o utilizó herramientas.")
        if accesses != prior["access_fingerprints"](): raise AssertionError("Cambió una reserva histórica.")
        if before != verify_evidence(snapshots, with_originals=True): raise AssertionError("Cambió evidencia anterior.")
        if status_sha != sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest():
            raise AssertionError("Cambió PROJECT_STATUS.md.")

        backup = journal.directory / "registry-snapshot.sqlite3"
        _write_exclusive(backup, b"")
        source = sqlite3.connect(ledger.LEDGER_PATH.resolve().as_uri() + "?mode=ro", uri=True)
        destination = sqlite3.connect(backup)
        try: source.backup(destination)
        finally: destination.close(); source.close()
        with patch.object(ledger, "LEDGER_PATH", backup):
            if ledger.inspect_campaign(scope) != state:
                raise AssertionError("La instantánea no conserva el estado contable.")
        _write_exclusive(journal.directory / "ledger-state.json", json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
        audit = {"schema_version": 1, "status": "registered_inactive_no_reservations", "scope_id": scope,
                 "plan_dir": str(PLAN), "ledger_path": str(ledger.LEDGER_PATH),
                 "snapshot": str(backup), "snapshot_sha256": sha256(backup.read_bytes()).hexdigest(),
                 "limits": state["registration"]["terms"]["limits"],
                 "reserved_model_requests": 0, "reserved_backtests": 0, "execution_authorized": False,
                 "blocked_calls": counters, "prior_inventories": len(snapshots),
                 "prior_copies_verified": before["copies_verified"],
                 "prior_original_references_verified": before["original_references_verified"],
                 "legacy_access_files_unchanged": len(accesses), "project_status_sha256": status_sha,
                 "new_usage": state["new_usage_of_this_operation"], "executable": False}
        _seal(journal, "audit.json", audit, "campaign_ledger_audit_completed")
        sources = {name: journal.directory / name for name in
                   ("audit.json", "audit.json.sha256", "events.jsonl", "ledger-state.json", "registry-snapshot.sqlite3")}
        sources.update({"audit-campaign-ledger.py": Path(__file__).resolve(),
                        "source/campaign_ledger.py": ROOT / "trading_ai/campaign_ledger.py",
                        "source/campaign_ledger_tests.py": ROOT / "tests/test_campaign_ledger.py"})
        contents = {name: path.read_bytes() for name, path in sources.items()}
        ARCHIVE.mkdir(exist_ok=False)
        files = {}
        for name, content in contents.items():
            target = ARCHIVE / name
            target.parent.mkdir(parents=True, exist_ok=True)
            _write_exclusive(target, content)
            files[name] = {"source": str(sources[name]), "sha256": sha256(content).hexdigest()}
        _write_exclusive(ARCHIVE / "snapshot.json", json.dumps(
            {"schema_version": 1, "files": files}, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
        proof = verify_evidence(snapshots + [ARCHIVE / "snapshot.json"], with_originals=True)
        print(json.dumps({"audit_run": str(journal.directory), "scope_id": scope,
                          "copies_verified": proof["copies_verified"], "new_copies": len(files),
                          "blocked_calls": counters, "new_usage": audit["new_usage"]}, ensure_ascii=True))
    except Exception as error:
        journal.record("campaign_ledger_audit_failed", error_type=type(error).__name__, message=str(error)[:1000])
        raise


if __name__ == "__main__": main()
