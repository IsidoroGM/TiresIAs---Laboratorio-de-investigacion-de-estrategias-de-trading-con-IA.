"""Comprobación local de preparación, sin inferencias o cálculos de investigación."""

from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))

from trading_ai.campaign_plan import prepare_campaign_plan, verify_campaign_plan
from trading_ai.evidence import verify_evidence
from trading_ai.holdout import _write_exclusive
from trading_ai.research import RunJournal
from trading_ai.rule_planning import _seal


GUIDED = ROOT / ".local/guided-compact-requests/1a1d0783778243ac989ca1ab3fc49911"
ARCHIVE = ROOT / "reports/phase4-campaign-plan-2026-10-20"
HISTORY = (
    "phase4-idea-memory-2026-10-19", "phase4-research-session-2026-10-19/first-proposal",
    "phase4-structured-brief-2026-10-19", "phase4-structured-draft-2026-10-19",
    "phase4-structured-draft-context-2026-10-19", "phase4-structured-draft-request-2026-10-19",
    "phase4-structured-ideas-2026-10-19", "phase4-structured-pipeline-2026-10-19",
    "phase4-structured-readiness-2026-10-19", "phase4-structured-review-memory-2026-10-19",
    "phase4-structured-revision-2026-10-19", "phase4-compact-candidate-2026-10-20",
    "phase4-compact-memory-request-2026-10-20", "phase4-rule-coverage-2026-10-20",
    "phase4-guided-request-2026-10-20", "phase4-verification-profile-2026-10-20",
    "phase4-cached-read-2026-10-20")


def access_fingerprints():
    files = {}
    for folder in (ROOT / ".local").iterdir():
        if not folder.is_dir() or not any(word in folder.name for word in ("access", "claims", "locks")):
            continue
        for path in folder.rglob("*"):
            if path.is_file():
                if not path.resolve().is_relative_to(ROOT):
                    raise ValueError("Una reserva queda fuera del proyecto.")
                files[str(path.relative_to(ROOT))] = sha256(path.read_bytes()).hexdigest()
    return files


def main():
    if ARCHIVE.exists():
        raise ValueError("El archivo de evidencia ya existe; no se sobrescribe.")
    journal = RunJournal(ROOT / ".local/campaign-plan-audits")
    journal.record("campaign_plan_audit_started", guided_dir=str(GUIDED))
    counters = {key: 0 for key in ("network", "provider", "calculation", "legacy_reservation", "outer_evaluation")}
    try:
        snapshots = [ROOT / "reports" / name / "snapshot.json" for name in HISTORY]
        before = verify_evidence(snapshots, with_originals=True)
        accesses = access_fingerprints()
        status_sha = sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()

        def forbidden(key):
            def reject(*args, **kwargs):
                counters[key] += 1
                raise AssertionError("Herramienta bloqueada durante preparación: " + key)
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
            plan_dir = prepare_campaign_plan(GUIDED, {"max_proposals": 3, "max_backtests": 6})
            plan = verify_campaign_plan(plan_dir)

        if accesses != access_fingerprints():
            raise AssertionError("Se modificaron reservas históricas.")
        after = verify_evidence(snapshots, with_originals=True)
        if before != after or status_sha != sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest():
            raise AssertionError("Cambió evidencia anterior o PROJECT_STATUS.md.")
        if (any(counters.values()) or plan["new_generation_permission"] or plan["executable"]
                or not plan["inherited_generation_budget"]["consumed"]):
            raise AssertionError("El plan no conserva sus bloqueos y presupuesto heredado.")
        audit = {"schema_version": 1, "status": "verified_not_activated", "campaign_dir": str(plan_dir),
                 "source_guided": str(GUIDED), "scope_id": plan["scope_id"], "planned_limits": plan["limits"],
                 "inherited_budget_consumed": True, "history_omitted": plan["history_entries_omitted"],
                 "request_bytes": plan["request_bytes"], "blocked_calls": counters,
                 "prior_inventories": len(snapshots), "prior_copies_verified": before["copies_verified"],
                 "prior_original_references_verified": before["original_references_verified"],
                 "access_files_unchanged": len(accesses), "project_status_sha256": status_sha,
                 "new_usage": plan["new_usage"], "executable": False}
        _seal(journal, "audit.json", audit, "campaign_plan_audit_completed")
        sources = {"campaign/" + name: plan_dir / name for name in
                   ("campaign.json", "campaign.json.sha256", "limits.json", "request.json", "events.jsonl")}
        sources.update({"audit/" + name: journal.directory / name for name in
                        ("audit.json", "audit.json.sha256", "events.jsonl")})
        sources.update({"audit-campaign-plan.py": Path(__file__).resolve(),
                        "source/campaign_plan.py": ROOT / "trading_ai/campaign_plan.py",
                        "source/campaign_plan_tests.py": ROOT / "tests/test_campaign_plan.py"})
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
        current = verify_evidence(snapshots + [ARCHIVE / "snapshot.json"], with_originals=True)
        print(json.dumps({"audit_run": str(journal.directory), "campaign_run": str(plan_dir),
                          "copies_verified": current["copies_verified"], "blocked_calls": counters,
                          "limits": plan["limits"], "new_usage": plan["new_usage"]}, ensure_ascii=True))
    except Exception as error:
        journal.record("campaign_plan_audit_failed", error_type=type(error).__name__, message=str(error)[:1000])
        raise


if __name__ == "__main__":
    main()
