"""Prueba local única; conserva originales, bloquea cálculo y archiva evidencia."""

from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

from trading_ai.compact_candidate import CompactCandidateError, generate_compact_candidate, verify_compact_candidate
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _seal
from trading_ai.structured_draft_request import verify_draft_request
from trading_ai.structured_freshness import capture_request_freshness, inspect_request_freshness
from trading_ai.structured_generation import generation_budget_status, verify_generation_reservation


REQUEST = ROOT / ".local/structured-draft-requests/1646833181eb44c386eb32872f245afa"
ARCHIVE = ROOT / "reports/phase4-compact-candidate-2026-10-20"
HISTORY = ("phase4-research-session-2026-10-19/first-proposal", "phase4-idea-memory-2026-10-19",
           "phase4-structured-ideas-2026-10-19", "phase4-structured-pipeline-2026-10-19",
           "phase4-structured-revision-2026-10-19", "phase4-structured-brief-2026-10-19",
           "phase4-structured-draft-2026-10-19", "phase4-structured-draft-context-2026-10-19",
           "phase4-structured-review-memory-2026-10-19", "phase4-structured-draft-request-2026-10-19",
           "phase4-structured-readiness-2026-10-19")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def old_artifacts():
    inventory = []
    for relative in HISTORY:
        manifest = ROOT / "reports" / relative / "snapshot.json"
        for name, item in json.loads(manifest.read_bytes())["files"].items():
            copy, original = manifest.parent / name, Path(item["source"])
            if not original.is_absolute(): original = ROOT / original
            if digest(copy) != item["sha256"] or digest(original) != item["sha256"]:
                raise ValueError("Copia o fuente histórica modificada: " + str(copy))
            inventory.append({"copy": str(copy), "source": str(original), "sha256": item["sha256"]})
    if len(inventory) != 205: raise ValueError("Inventario histórico de esta continuación incompleto.")
    return inventory


def main():
    if ARCHIVE.exists(): raise ValueError("Esta comprobación ya tiene archivo; no se repetirá.")
    journal = RunJournal(ROOT / ".local/compact-candidate-audits")
    inventory = old_artifacts()
    status_hash = digest(ROOT / "docs/PROJECT_STATUS.md")
    io = {"outer_reads": 0, "signal_calls": 0, "backtest_calls": 0, "session_actions": 0}
    actual_open = Path.open
    def guarded_open(path, *args, **kwargs):
        if path.name in ("evaluation.xml", "comparison.json"):
            io["outer_reads"] += 1
            raise ValueError("La auditoría no puede abrir evaluación exterior.")
        return actual_open(path, *args, **kwargs)
    def blocked(kind):
        def fail(*args, **kwargs):
            io[kind] += 1
            raise ValueError("La auditoría no puede calcular o actuar: " + kind)
        return fail
    journal.record("compact_candidate_audit_started", request_dir=str(REQUEST), old_artifacts=len(inventory))
    with patch.object(Path, "open", guarded_open), \
            patch("trading_ai.rules.RuleStrategy.generate_signals", blocked("signal_calls")), \
            patch("trading_ai.strategies.SmaCrossoverStrategy.generate_signals", blocked("signal_calls")), \
            patch("trading_ai.strategies.EmaCrossoverStrategy.generate_signals", blocked("signal_calls")), \
            patch("trading_ai.experiments.run_backtest", blocked("backtest_calls")), \
            patch("trading_ai.backtesting.run_backtest", blocked("backtest_calls")), \
            patch("trading_ai.rule_execution.run_backtest", blocked("backtest_calls")), \
            patch("trading_ai.rule_execution._calculate", blocked("backtest_calls")), \
            patch("trading_ai.structured_session._action", blocked("session_actions")):
        request = verify_draft_request(REQUEST)
        before_budget = generation_budget_status(REQUEST)
        if before_budget["consumed"]: raise ValueError("Intento compacto ya consumido; no se repetirá.")
        freshness_dir = capture_request_freshness(REQUEST)
        before = inspect_request_freshness(REQUEST)
        if before["status"] != "current": raise ValueError("Petición obsoleta; no se enviará.")
        print(json.dumps({"stage": "compact_controller_starting", "model_request_budget": 1, "backtests": 0}), flush=True)
        try:
            candidate_dir = generate_compact_candidate(REQUEST)
            candidate = verify_compact_candidate(candidate_dir)
            outcome = candidate["status"]
        except CompactCandidateError as error:
            candidate_dir, candidate, outcome = error.directory, None, "failed_preserved_no_retry"
        print(json.dumps({"stage": "compact_controller_finished", "status": outcome}), flush=True)
        events = [json.loads(line) for line in (candidate_dir / "events.jsonl").read_bytes().splitlines()]
        if candidate is None:
            failure = events[-1]["data"]
            use = {key: failure[key] for key in ("model_requests", "usage", "api_cost_usd", "backtests", "metadata_request_attempts")}
        else:
            use = {key: candidate[key] for key in ("model_requests", "usage", "api_cost_usd", "backtests", "metadata_request_attempts")}
        job = json.loads((candidate_dir / "job.json").read_bytes()) if (candidate_dir / "job.json").exists() else None
        reservation_dir = Path(job["reservation"]["directory"]) if job else None
        reservation = verify_generation_reservation(reservation_dir) if reservation_dir else None
        after = inspect_request_freshness(REQUEST)
        after_budget = generation_budget_status(REQUEST)
    for item in inventory:
        if digest(Path(item["copy"])) != item["sha256"] or digest(Path(item["source"])) != item["sha256"]:
            raise ValueError("Un archivo histórico cambió durante la comprobación.")
    if digest(ROOT / "docs/PROJECT_STATUS.md") != status_hash:
        raise ValueError("PROJECT_STATUS.md cambió sin cierre de fase.")
    record = {"schema_version": 1, "protocol": "compact_candidate_audit_v1", "status": outcome,
              "request_dir": str(REQUEST), "request_sha256": request["request_sha256"],
              "freshness_dir": str(freshness_dir), "before_freshness": before, "after_freshness": after,
              "before_budget": before_budget, "after_budget": after_budget,
              "candidate_dir": str(candidate_dir), "reservation_dir": str(reservation_dir) if reservation_dir else None,
              "new_usage": use, "io_guard": io, "old_artifacts_checked": len(inventory),
              "old_inventory": inventory, "project_status_sha256": status_hash,
              "previous_standalone_version_metadata_requests": 1,
              "inherited_lineage_usage": [{"run": "18fdf9274baa4b96973b8c2f67dab92b", "input_tokens": 1257,
                                            "output_tokens": 248, "api_cost_usd": "0"},
                                           {"run": "a1bacf3e52c743c2b4088cad0c82ee45", "input_tokens": 1289,
                                            "output_tokens": 239, "api_cost_usd": "0"}],
              "pending_proposals_simulated": False, "known_history": True, "outer_evaluation_allowed": False,
              "executable": False, "phase_closed": False}
    _seal(journal, "audit.json", record, "compact_candidate_audit_completed")
    ARCHIVE.mkdir()
    files = {}
    def copy(source, relative):
        destination = ARCHIVE / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_bytes()
        _write_exclusive(destination, raw)
        files[relative] = {"source": str(source), "sha256": sha256(raw).hexdigest()}
    for prefix, directory in (("audit", journal.directory), ("freshness-before", freshness_dir), ("candidate", candidate_dir),
                              ("reservation", reservation_dir)):
        if directory is None: continue
        for source in sorted(directory.rglob("*")):
            if source.is_file(): copy(source, prefix + "/" + source.relative_to(directory).as_posix())
    if reservation:
        copy(Path(reservation["access"]["path"]), "access/generation.json")
    if candidate:
        copy(Path(candidate["rule_access"]["path"]), "access/rule.json")
    copy(Path(__file__).resolve(), "audit-compact-candidate.py")
    _write_exclusive(ARCHIVE / "snapshot.json", json.dumps({"schema_version": 1, "files": files}, ensure_ascii=False, indent=2).encode("utf-8"))
    for name, item in files.items():
        if digest(ARCHIVE / name) != item["sha256"] or digest(Path(item["source"])) != item["sha256"]:
            raise ValueError("Archivo nuevo no conserva sus bytes: " + name)
    print(json.dumps({"audit_dir": str(journal.directory), "candidate_dir": str(candidate_dir), "status": outcome,
                      "new_usage": use, "io_guard": io, "old_artifacts_checked": len(inventory),
                      "new_copies_checked": len(files)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
