"""Comprobación real autorizada: una campaña local y un walk-forward conocido."""

from contextlib import ExitStack
from hashlib import sha256
import io
import json
from pathlib import Path
import runpy
import socket
import sqlite3
import sys
from unittest.mock import patch

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
from trading_ai import campaign_cycle as cycle
from trading_ai import campaign_ledger as ledger
from trading_ai import rule_execution as engine
from trading_ai import walk_forward as walk
from trading_ai.ai import OllamaProvider
from trading_ai.evidence import verify_evidence
from trading_ai.research import RunJournal
from trading_ai.rule_planning import _seal
from trading_ai.validated_read_cache import ValidatedReadCache
from trading_ai.verification_session import VerificationSession


def main():
    old = runpy.run_path(str(ROOT / ".local/audit-campaign-plan.py"))
    names = (*old["HISTORY"], "phase4-campaign-plan-2026-10-20", "phase4-campaign-ledger-2026-10-20",
             "phase4-campaign-attempts-2026-10-20", "phase4-campaign-controller-2026-10-20",
             "phase4-campaign-review-2026-10-20", "phase4-campaign-execution-2026-10-20", "phase4-campaign-memory-2026-10-20")
    snapshots = [ROOT / "reports" / name / "snapshot.json" for name in names]
    prior = verify_evidence(snapshots, with_originals=True)
    before_access = old["access_fingerprints"]()
    db = sqlite3.connect(ledger.LEDGER_PATH.as_uri() + "?mode=ro", uri=True)
    try: rows = db.execute("SELECT scope_id, record_json FROM scopes").fetchall()
    finally: db.close()
    if len(rows) != 1: raise ValueError("No hay un único ámbito existente.")
    scope, registration_raw = rows[0]
    state = ledger.inspect_campaign(scope)
    if state["reservations"]: raise ValueError("Ya hay intentos: este script no los reanuda o repite.")
    journal = RunJournal(ROOT / ".local/phase4-completion-checks")
    journal.record("phase4_completion_check_started", scope_id=scope)
    counters = {"local_metadata_requests": 0, "local_model_request_attempts": 0,
                "cycle_backtests": 0, "walk_forward_backtests": 0, "forbidden_network": 0, "outer_evaluation": 0}
    phase = "cycle"
    original_open, original_request, original_connect, original_calculate = io.open, OllamaProvider._request, socket.socket.connect, engine._calculate
    def guarded_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path).name in ("evaluation.xml", "comparison.json"):
            counters["outer_evaluation"] += 1
            raise AssertionError("Evaluación exterior bloqueada.")
        return original_open(path, *args, **kwargs)
    def connected(sock, address):
        if not isinstance(address, tuple) or address[:2] not in (("127.0.0.1", 11435), ("::1", 11435)):
            counters["forbidden_network"] += 1
            raise AssertionError("Solo está autorizado el servidor local existente.")
        return original_connect(sock, address)
    def request(provider, method, path, payload):
        if method == "GET" and path in ("/api/version", "/api/tags"): counters["local_metadata_requests"] += 1
        elif phase == "cycle" and method == "POST" and path == "/api/chat":
            counters["local_model_request_attempts"] += 1
            if counters["local_model_request_attempts"] > state["registration"]["terms"]["limits"]["max_proposals"]:
                raise AssertionError("Presupuesto de consultas excedido.")
        else: raise AssertionError("Ruta o fase de proveedor no autorizada.")
        return original_request(provider, method, path, payload)
    def calculate(*args):
        key = "cycle_backtests" if phase == "cycle" else "walk_forward_backtests"
        counters[key] += 1
        maximum = state["registration"]["terms"]["limits"]["max_backtests"] if phase == "cycle" else 24
        if counters[key] > maximum: raise AssertionError("Presupuesto de cálculos excedido.")
        return original_calculate(*args)
    with ExitStack() as stack:
        for obj, name, value in ((io, "open", guarded_open), (socket.socket, "connect", connected),
                                 (OllamaProvider, "_request", request), (engine, "_calculate", calculate)):
            stack.enter_context(patch.object(obj, name, value))
        with VerificationSession():
            permit = cycle.prepare_cycle(scope)
            journal.record("cycle_permit_ready", directory=str(permit))
            try: cycle_run = cycle.run_cycle(permit, allow_local_generation=True, allow_virtual_calculations=True)
            except engine.ExecutionError as error: cycle_run = error.directory
            cycle_result = cycle.status(cycle_run)
            journal.save("local-cycle-status.json", cycle_result)
        print(json.dumps({"cycle_run": str(cycle_run), "stop_reason": cycle_result.get("stop_reason", cycle_result.get("status")), "counters": counters}), flush=True)
        phase = "walk_forward"
        frozen_dir = Path(json.loads((Path(state["registration"]["plan"]["directory"]) / "campaign.json").read_bytes())["reference"]["frozen_dir"])
        with ValidatedReadCache():
            plan = walk.prepare(frozen_dir)
            journal.record("walk_forward_plan_ready", directory=str(plan))
            walk_run = walk.run(plan)
            walk_result = walk.verify_run(walk_run)
            journal.save("walk-forward-result.json", walk_result)
    after = ledger.inspect_campaign(scope)
    after_access = old["access_fingerprints"]()
    if any(after_access.get(key) != value for key, value in before_access.items()): raise AssertionError("Cambió un intento histórico.")
    if after["registration"] != state["registration"]: raise AssertionError("Se cambiaron límites o controles registrados.")
    if verify_evidence(snapshots, with_originals=True) != prior: raise AssertionError("Cambió una evidencia anterior.")
    if counters["forbidden_network"] or counters["outer_evaluation"]: raise AssertionError("Se intentó una acción fuera del alcance.")
    audit = {"schema_version": 1, "status": "controlled_checks_completed", "scope_id": scope,
             "cycle_permit": str(permit), "cycle_run": str(cycle_run), "cycle_outcome": cycle_result.get("stop_reason", cycle_result.get("status")),
             "walk_forward_plan": str(plan), "walk_forward_run": str(walk_run), "counters": counters,
             "registered_terms_unchanged": True, "historical_access_files_unchanged": len(before_access),
             "prior_copies_verified": prior["copies_verified"], "prior_inventories": len(snapshots),
             "walk_forward_fold_outcomes": [{"index": fold["index"], "selected_id": fold["selected_id"],
                                             "check_status": fold["check_status"], "assessment": None if fold["check"] is None else fold["check"]["assessment"]} for fold in walk_result["folds"]],
             "api_cost_usd": "0", "scope": "known_development_history_only", "independent_validation": False,
             "automatic_adoption": False, "broker_operations_allowed": False, "full_suite_pending": True}
    _seal(journal, "application-check.json", audit, "phase4_application_check_completed")
    print(json.dumps({"application_check": str(journal.directory), "cycle_run": str(cycle_run), "walk_forward_run": str(walk_run),
                      "counters": counters, "folds": audit["walk_forward_fold_outcomes"], "api_cost_usd": "0"}), flush=True)


if __name__ == "__main__": main()
