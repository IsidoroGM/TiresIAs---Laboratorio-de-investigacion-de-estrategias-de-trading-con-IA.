"""Auditoría explícita de consulta. No llama al modelo ni calcula simulaciones."""

from collections import Counter
from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
import socket
import sqlite3
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from trading_ai import ai, backtesting, campaign_cycle, campaign_ledger, experiments, rule_execution
from trading_ai.lab_query import LabQuery
from trading_ai.research import RunJournal


def check():
    query = LabQuery(ROOT)
    paths = {ROOT / entry["path"] for entry in query.catalog.files.values()}
    paths.add(campaign_ledger.LEDGER_PATH)
    for directory in (ROOT / ".local").iterdir():
        if directory.name.endswith("-access") and directory.is_dir():
            paths.update(path for path in directory.glob("*.json") if path.is_file())

    def fingerprints():
        return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in sorted(paths) if path.is_file()}

    before = fingerprints()
    calls = []

    def denied(*args, **kwargs):
        calls.append("forbidden_action")
        raise AssertionError("Una consulta intentó iniciar una acción prohibida.")

    original_open, original_connect = Path.open, sqlite3.connect

    def readonly(path, mode="r", *args, **kwargs):
        if any(char in mode for char in "wax+"): return denied()
        return original_open(path, mode, *args, **kwargs)

    def readonly_db(database, *args, **kwargs):
        if not kwargs.get("uri") or "mode=ro" not in str(database): return denied()
        return original_connect(database, *args, **kwargs)

    with ExitStack() as guards:
        functions = (backtesting.run_backtest, experiments.run_experiment, rule_execution._calculate)
        for name, module in tuple(sys.modules.items()):
            if not name.startswith("trading_ai.") or module is None: continue
            for key, value in tuple(vars(module).items()):
                if any(value is function for function in functions): guards.enter_context(patch.object(module, key, denied))
        for owner, attribute in ((ai, "create_provider"), (ai.OllamaProvider, "complete"),
                                 (campaign_cycle, "run_cycle"), (campaign_ledger, "_reserve"),
                                 (RunJournal, "__init__"), (socket.socket, "connect"), (socket.socket, "connect_ex")):
            guards.enter_context(patch.object(owner, attribute, denied))
        guards.enter_context(patch.object(Path, "open", readonly))
        guards.enter_context(patch.object(sqlite3, "connect", readonly_db))
        home = query.home()
        rows = query.experiments()["items"]
        counts, detailed, summary_only, warnings = Counter(), 0, 0, []
        for row in rows:
            detail = query.detail(row["id"])
            counts[detail["integrity"]["state"]] += 1
            if detail["warnings"]: warnings.append({"path": row["path"], "warnings": detail["warnings"]})
            for account in detail["accounts"]:
                saved = query.account(row["id"], account["id"])
                if saved["backtest"] is not None: detailed += 1
                else: summary_only += 1
                if saved["warnings"]: warnings.append({"account": account["id"], "warnings": saved["warnings"]})
        consumption = query.consumption()
    after = fingerprints()
    if before != after or calls or warnings or home["warnings"]:
        raise AssertionError(json.dumps({"files_unchanged": before == after, "forbidden_calls": calls, "warnings": warnings, "catalog": home["warnings"]}))
    return {"status": "passed", "experiments": len(rows), "integrity_states": dict(counts),
            "accounts_with_saved_details": detailed, "accounts_with_summary_only": summary_only,
            "consumption_sources": len(consumption["items"]), "forbidden_calls": len(calls),
            "tracked_read_files": len(before), "files_unchanged": before == after,
            "new_model_requests": 0, "new_backtests": 0, "new_reservations": 0,
            "source_sha256": before}


if __name__ == "__main__":
    result = check()
    if len(sys.argv) == 2:
        with Path(sys.argv[1]).open("x", encoding="utf-8") as output: json.dump(result, output, ensure_ascii=False, indent=2)
    print(json.dumps({key: value for key, value in result.items() if key != "source_sha256"}, ensure_ascii=True))
