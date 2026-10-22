"""Read-only evidence collection and independent Decimal audit of the manual UI example."""

from collections import Counter
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import sqlite3
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2]
out = root / "reports/phase6-chat-operations-2026-10-22"


def digest(path): return sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_bytes())


def put(relative, raw):
    path = out / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): assert path.read_bytes() == raw, relative
    else:
        with path.open("xb") as stream: stream.write(raw)


def save(relative, value): put(relative, (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))


def get(path):
    connection = HTTPConnection("127.0.0.1", 64162, timeout=10)
    try:
        connection.request("GET", path)
        response = connection.getresponse(); assert response.status == 200
        return json.loads(response.read())
    finally: connection.close()


prior = {}
for name in ("phase6-dukascopy-2026-10-22", "phase6-dukascopy-paired-2026-10-22",
             "phase6-dukascopy-history-2026-10-22", "phase6-dukascopy-spread-2026-10-22",
             "phase6-market-history-import-2026-10-22", "phase6-period-validation-2026-10-22",
             "phase6-reference-costs-2026-10-22", "phase6-chat-prices-2026-10-22",
             "phase6-chat-explanations-2026-10-22"):
    folder = root / "reports" / name
    manifest = read(folder / "manifest.json")
    for relative, expected in manifest["evidence_sha256"].items(): assert digest(folder / relative) == expected, (name, relative)
    prior[name] = {"manifest_sha256": digest(folder / "manifest.json"), "verified_evidence_files": len(manifest["evidence_sha256"])}
previous_folder = root / "reports/phase6-chat-explanations-2026-10-22"
previous = read(previous_folder / "manifest.json")
unchanged = {key: value for key, value in previous["unchanged_prior_source_sha256"].items() if key != "trading_ai/lab.py"}
unchanged.update({key: value for key, value in previous["source_sha256"].items()
                  if key not in ("trading_ai/conversation.py", "trading_ai/lab_static/app.js")})
for relative, expected in unchanged.items(): assert digest(root / relative) == expected, relative
originals = read(root / "reports/phase6-chat-prices-2026-10-22/manifest.json")["original_price_sha256"]
for name, expected in originals.items(): assert digest(Path("C:/Users/34656/Downloads") / name) == expected
assert digest(root / "docs/PROJECT_STATUS.md") == "9efc811155e314d6a0df14d19a4f38fd83467e52ea3e82117f83402bc41da5bb"
protocol = read(out / "protocol.json")
session = protocol["session"]
assert get("/api/chat/"+session) == read(previous_folder / "conversation.json")
strategy = get("/api/simulation")
assert strategy["accounts"] == [] and strategy["receipts"] == []
current = get("/api/chat/"+session+"/manual-operations")
before = read(root / ".local/ev-data/manual-before-approval.json")
after_buy = read(root / ".local/ev-data/manual-after-buy.json")
account = next(item for item in current["accounts"] if item["configuration"]["account"]["id"] == protocol["account_name"])
assert account["engine_compatible"]
assert before["accounts"][0]["state"]["cash"] == "1000" and before["accounts"][0]["state"]["quantity"] == "0"
assert before["intents"][0]["status"] == "awaiting_approval"
assert all(after_buy["accounts"][0]["state"][key] == expected for key, expected in protocol["expected_after_buy"].items())
intents = [item for item in current["intents"] if item["data"]["account"] == account["id"]]
assert len(intents) == 2 and all(item["status"] == "applied" for item in intents)

# The audit imports no project modules and never calls a simulator or model.
cash, quantity, basis, realized, fees = Decimal("1000"), Decimal(0), Decimal(0), Decimal(0), Decimal(0)
checks = []
with localcontext(Context(prec=28)):
    for index, intent in enumerate(intents):
        data, expected = intent["data"], protocol["steps"][index]
        assert data["request_text"] == expected["request"]
        assert data["quote"]["bid"] == expected["bid"] and data["quote"]["ask"] == expected["ask"]
        assert data["quote"]["source"] == "user_supplied_unverified"
        assert data["operation"]["quantity"] == "1"
        price = Decimal(data["quote"]["ask" if index == 0 else "bid"])
        cost = price * Decimal(protocol["assumed_commission_rate"])
        if index == 0:
            cash -= price + cost; quantity = Decimal(1); basis = price + cost
        else:
            cash += price - cost; quantity = Decimal(0); realized += price - cost - basis; basis = Decimal(0)
        fees += cost
        equity = cash + quantity*Decimal(data["quote"]["bid"])
        state = intent["result"]["state"]
        computed = {"cash": cash, "quantity": quantity, "basis": basis, "realized_pnl": realized, "fees": fees, "equity": equity}
        assert all(Decimal(state[key]) == value for key, value in computed.items())
        assert state["filled_orders"] == index+1 and state["last_sequence"] == index+1
        assert intent["result"]["external_order_sent"] is False and intent["result"]["mode"] == "manual_virtual"
        assert intent["result"]["approval"]["request"]["intent_sha256"] == intent["sha256"]
        assert intent["data"]["preview"]["state"] == state
        checks.append({"intent": intent["id"], "checked": {key: str(value) for key, value in computed.items()}})
assert all(account["state"][key] == expected for key, expected in protocol["expected_after_sell"].items())
assert account["state"] == intents[-1]["result"]["state"]
database = root / ".local/manual-simulation/ledger.sqlite3"
with sqlite3.connect(database.as_uri()+"?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    rows = {table: [dict(row) for row in conn.execute(query, args)] for table, query, args in (
        ("accounts", "SELECT * FROM accounts WHERE id=?", (account["id"],)),
        ("intents", "SELECT * FROM intents WHERE session=?", (session,)),
        ("postings", "SELECT * FROM postings WHERE account=? ORDER BY id", (account["id"],)),
    )}
assert len(rows["postings"]) == 2 and len({row["approval_id"] for row in rows["intents"]}) == 2
for name, expected in json.loads(rows["accounts"][0]["engine"]).items(): assert digest(root / "trading_ai" / name) == expected
save("manual-register.json", rows)
save("final-state.json", current)
put("before-approval.json", (root / ".local/ev-data/manual-before-approval.json").read_bytes())
put("after-buy.json", (root / ".local/ev-data/manual-after-buy.json").read_bytes())
save("independent-audit.json", {"method": "stdlib_decimal_from_original_intents_and_supplied_bidask", "project_modules_imported": False,
    "checks": checks, "new_model_requests": 0, "new_backtests": 0, "chat_budget_unchanged": True,
    "strategy_accounts_inbox_and_previous_conversation_unchanged": True, "synthetic_example_only": True,
    "browser_account_review_intent_save_separate_approval_and_close_verified": True})
cases = ET.parse(out / "tests.xml").findall(".//testcase")
counts = Counter(case.attrib["classname"] for case in cases)
assert len(cases) == 562 and counts["tests.test_conversation_operations"] == 37 and all(not list(case) for case in cases)
assert "562 passed" in (out / "tests.log").read_text(encoding="utf-8")
node = "C:/Users/34656/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
subprocess.run([node, "--check", "trading_ai/lab_static/app.js"], cwd=root, check=True, capture_output=True)
subprocess.run(["git", "diff", "--check"], cwd=root, check=True, capture_output=True)
for name in ("ui-intent-review.jpg", "ui-virtual-result.jpg"): assert (out / name).read_bytes().startswith(b"\xff\xd8\xff")
sources = ("trading_ai/conversation_operations.py", "trading_ai/conversation.py", "trading_ai/lab.py",
           "trading_ai/lab_static/app.js", "tests/test_conversation_operations.py")
for relative in sources: put("tested-source/"+relative, (root / relative).read_bytes())
put("tested-source/collect-evidence.py", Path(__file__).read_bytes())
manifest = {"date": "2026-10-22", "phase_closed": False, "phase7_started": False,
    "protocol_sha256": digest(out / "protocol.json"), "tests_passed": 562, "new_manual_tests": 37,
    "test_counts": dict(counts), "full_suite_run": False, "javascript_syntax_checked": True, "git_diff_whitespace_checked": True,
    "source_sha256": {relative: digest(root / relative) for relative in sources}, "unchanged_prior_source_sha256": unchanged,
    "prior_evidence_verified": prior, "original_price_sha256": originals, "account": account["id"], "session": session,
    "independent_manual_postings_verified": 2, "new_backtests": 0, "new_model_requests": 0,
    "budget_unchanged": protocol["chat_budget_before_and_after"], "existing_conversation_byte_equivalent": True,
    "existing_strategy_accounts_and_inbox_changed": False, "synthetic_example_not_strategy_evidence": True,
    "external_orders_sent": False, "project_status_edited_this_increment": False, "committed": False, "pushed": False,
    "evidence_sha256": {path.relative_to(out).as_posix(): digest(path) for path in sorted(out.rglob("*"))
                        if path.is_file() and path.name != "manifest.json"}}
save("manifest.json", manifest)
for relative, expected in manifest["evidence_sha256"].items(): assert digest(out / relative) == expected
print(json.dumps({"tests_passed": 562, "new_manual_tests": 37, "prior_reports_verified": len(prior),
    "evidence_files": len(manifest["evidence_sha256"]), "manual_postings": 2, "account": account["id"],
    "manifest_sha256": digest(out / "manifest.json")}, indent=2))
