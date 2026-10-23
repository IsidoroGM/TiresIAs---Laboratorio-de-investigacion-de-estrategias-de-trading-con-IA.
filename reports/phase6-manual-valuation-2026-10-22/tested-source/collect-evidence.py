"""Read-only audit of the example valuation and preservation of published evidence."""

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
out = root / "reports/phase6-manual-valuation-2026-10-22"


def digest(path): return sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_bytes())


def put(relative, raw):
    path = out / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): assert path.read_bytes() == raw, relative
    else:
        with path.open("xb") as stream: stream.write(raw)


def save(relative, value): put(relative, (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))


def get(path):
    connection = HTTPConnection("127.0.0.1",64162,timeout=10)
    try:
        connection.request("GET",path); response=connection.getresponse();assert response.status==200
        return json.loads(response.read())
    finally:connection.close()


prior={}
for path in sorted((root/"reports").rglob("manifest.json")):
    if path.parent==out:continue
    entries=read(path).get("evidence_sha256")
    if not isinstance(entries,dict):continue
    for relative,expected in entries.items():
        target=(path.parent/relative).resolve();assert target.is_relative_to(root)
        assert digest(target)==expected,(path,relative)
    prior[path.relative_to(root).as_posix()]={"sha256":digest(path),"files_verified":len(entries)}
assert len(prior)==11
previous_folder=root/"reports/phase6-chat-operations-2026-10-22"
previous=read(previous_folder/"manifest.json")
unchanged=previous["unchanged_prior_source_sha256"] | {key:value for key,value in previous["source_sha256"].items()
    if key not in ("trading_ai/conversation.py","trading_ai/lab_static/app.js")}
for path,expected in unchanged.items():assert digest(root/path)==expected,path
for name,expected in previous["original_price_sha256"].items():assert digest(Path("C:/Users/34656/Downloads")/name)==expected
assert digest(root/"docs/PROJECT_STATUS.md")=="9efc811155e314d6a0df14d19a4f38fd83467e52ea3e82117f83402bc41da5bb"
protocol=read(out/"protocol.json"); session=protocol["session"]
assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()==protocol["published_base_commit"]
assert subprocess.check_output(["git","rev-parse","origin/main"],cwd=root,text=True).strip()==protocol["published_base_commit"]
before=read(root/".local/ev-data/valuation-before.json")
current=get("/api/chat/"+session+"/manual-operations")
account=next(item for item in current["accounts"] if item["configuration"]["account"]["id"]==protocol["account_name"])
assert account["engine_compatible"]
old_account=read(previous_folder/"final-state.json")["accounts"][0]
preserved=next(item for item in current["accounts"] if item["id"]==old_account["id"])
assert preserved["state"]==old_account["state"] and preserved["chain_sha256"]==old_account["chain_sha256"]
assert all(before["accounts"][0]["state"][key]==value for key,value in protocol["expected_after_buy"].items())
assert all(account["state"][key]==value for key,value in protocol["expected_after_mark"].items())
intents=[item for item in current["intents"] if item["data"]["account"]==account["id"]]
marks=[item for item in current["valuations"] if item["account"]==account["id"]]
assert len(intents)==len(marks)==1 and intents[0]["status"]=="applied"
mark=marks[0]; record=mark["record"]
assert record["new_fill"] is False and record["new_fee"]=="0" and record["external_order_sent"] is False
for key in ("cash","quantity","basis","realized_pnl","fees","filled_orders","last_sequence","rejections","estimated_fee_events"):
    assert before["accounts"][0]["state"][key]==account["state"][key],key
with localcontext(Context(prec=28)):
    capital=Decimal(protocol["initial_capital_usd"]); quantity=Decimal("1")
    purchase=quantity*Decimal(protocol["setup"]["ask"])
    fee=purchase*Decimal(protocol["commission_rate"])
    cash=capital-purchase-fee
    equity=cash+quantity*Decimal(protocol["valuation"]["bid"])
    unrealized=quantity*Decimal(protocol["valuation"]["bid"])-purchase-fee
assert Decimal(account["state"]["cash"])==cash and Decimal(account["state"]["equity"])==equity
assert Decimal(account["valuation"]["unrealized_pnl_usd"])==unrealized==Decimal(protocol["expected_unrealized_pnl_usd"])
assert not account["valuation"]["market_verified"] and record["quote"]["source"]=="user_supplied_unverified"
assert record["quote"]["at"]>intents[0]["data"]["quote"]["at"]
assert record["request"]["chain_sha256"]==before["accounts"][0]["chain_sha256"]
for name,expected in record["engine_sha256"].items():assert digest(root/"trading_ai"/name)==expected,name
database=root/".local/manual-simulation/ledger.sqlite3"
with sqlite3.connect(database.as_uri()+"?mode=ro",uri=True) as conn:
    conn.row_factory=sqlite3.Row;conn.execute("PRAGMA query_only=ON")
    rows=[dict(row) for row in conn.execute("SELECT * FROM postings WHERE account=? ORDER BY id",(account["id"],))]
assert len(rows)==2
save("postings.json",rows)
save("before-valuation.json",before)
save("after-valuation.json",{"account":account,"intents":intents,"valuations":marks,"as_of":current["as_of"]})
strategy=get("/api/simulation");assert strategy["accounts"]==[] and strategy["receipts"]==[]
# Store only counts and states; no user's new chat message or action token is copied.
conversation=get("/api/chat/"+session)
reserved=conversation["reserved"]
save("audit.json",{"method":"independent_stdlib_decimal_from_fixed_example_prices","project_modules_imported":False,
    "cash":str(cash),"equity":str(equity),"unrealized_pnl_usd":str(unrealized),"unchanged_fill_count":1,
    "unchanged_purchase_fee":str(fee),"valuation_rows":1,"existing_manual_account_preserved":True,
    "browser_review_and_mark_verified":True,"live_age_display_verified":True,"user_messages_copied":False,
    "reserved_observed_after_demo":reserved,"own_model_requests":0,"own_backtests":0,"synthetic_example_only":True})
cases=ET.parse(out/"tests.xml").findall(".//testcase");counts=Counter(case.attrib["classname"] for case in cases)
assert len(cases)==586 and counts["tests.test_manual_valuation"]==24 and all(not list(case) for case in cases)
assert "586 passed" in (out/"tests.log").read_text(encoding="utf-8")
node="C:/Users/34656/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
subprocess.run([node,"--check","trading_ai/lab_static/app.js"],cwd=root,check=True,capture_output=True)
subprocess.run(["git","diff","--check"],cwd=root,check=True,capture_output=True)
assert (out/"ui-manual-valuation.jpg").read_bytes().startswith(b"\xff\xd8\xff")
sources=("trading_ai/manual_valuation.py","trading_ai/conversation.py","trading_ai/lab_static/app.js","tests/test_manual_valuation.py")
for path in sources:put("tested-source/"+path,(root/path).read_bytes())
put("tested-source/collect-evidence.py",Path(__file__).read_bytes())
manifest={"date":"2026-10-22","published_base_commit":protocol["published_base_commit"],"phase_closed":False,
    "this_increment_committed":False,"this_increment_pushed":False,"tests_passed":586,"new_valuation_tests":24,
    "full_suite_run":False,"test_counts":dict(counts),"javascript_syntax_checked":True,"git_diff_whitespace_checked":True,
    "protocol_sha256":digest(out/"protocol.json"),"prior_evidence_verified":prior,
    "source_sha256":{path:digest(root/path) for path in sources},"unchanged_prior_source_sha256":unchanged,
    "manual_account":account["id"],"new_valuation_rows":1,"new_fill_from_valuation":False,
    "own_model_requests":0,"new_backtests":0,"synthetic_example_only":True,"user_messages_copied":False,
    "existing_manual_account_preserved":True,"strategy_accounts_and_inbox_changed":False,
    "project_status_edited_this_increment":False,"external_orders_sent":False,
    "evidence_sha256":{path.relative_to(out).as_posix():digest(path) for path in sorted(out.rglob("*")) if path.is_file() and path.name!="manifest.json"}}
save("manifest.json",manifest)
for path,expected in manifest["evidence_sha256"].items():assert digest(out/path)==expected
print(json.dumps({"tests_passed":586,"new_valuation_tests":24,"prior_manifests_verified":len(prior),
    "evidence_files":len(manifest["evidence_sha256"]),"account":account["id"],"manifest_sha256":digest(out/"manifest.json")},indent=2))
