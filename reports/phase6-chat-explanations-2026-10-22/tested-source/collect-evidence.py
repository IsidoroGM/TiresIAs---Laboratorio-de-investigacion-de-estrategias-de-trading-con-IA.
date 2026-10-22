"""Freeze the one real constrained explanation; never rerun a model or backtest."""

from collections import Counter
from decimal import Decimal
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from trading_ai.conversation import digest, strict
from trading_ai.conversation_explanation import SCHEMA, compose, validate
from trading_ai.conversation_provider import check_context
from trading_ai.conversation_prices import read_result

out = root / "reports/phase6-chat-explanations-2026-10-22"
protocol = json.loads((out / "protocol.json").read_bytes())
session = protocol["session"]


def hash_file(path): return sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_bytes())


def put(relative, raw):
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw, relative
    else:
        with target.open("xb") as stream: stream.write(raw)


def save(relative, value):
    put(relative, (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))


def get(path):
    connection = HTTPConnection("127.0.0.1", 64162, timeout=10)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        assert response.status == 200
        return json.loads(response.read())
    finally: connection.close()


prior = {}
for name in ("phase6-dukascopy-2026-10-22", "phase6-dukascopy-paired-2026-10-22",
             "phase6-dukascopy-history-2026-10-22", "phase6-dukascopy-spread-2026-10-22",
             "phase6-market-history-import-2026-10-22", "phase6-period-validation-2026-10-22",
             "phase6-reference-costs-2026-10-22", "phase6-chat-prices-2026-10-22"):
    folder = root / "reports" / name
    value = read(folder / "manifest.json")
    for relative, expected in value["evidence_sha256"].items():
        assert hash_file(folder / relative) == expected, (name, relative)
    prior[name] = {"manifest_sha256": hash_file(folder / "manifest.json"),
                   "verified_evidence_files": len(value["evidence_sha256"])}
previous_folder = root / "reports/phase6-chat-prices-2026-10-22"
previous = read(previous_folder / "manifest.json")
unchanged = previous["unchanged_prior_source_sha256"] | {
    key: previous["source_sha256"][key] for key in
    ("trading_ai/conversation_prices.py", "trading_ai/lab.py", "trading_ai/lab_static/chat.css")}
for relative, expected in unchanged.items():
    assert hash_file(root / relative) == expected, relative
for name, expected in previous["original_price_sha256"].items():
    assert hash_file(Path("C:/Users/34656/Downloads") / name) == expected, name
assert hash_file(root / "docs/PROJECT_STATUS.md") == "9efc811155e314d6a0df14d19a4f38fd83467e52ea3e82117f83402bc41da5bb"

detail = get("/api/chat/"+session)
before = read(previous_folder / "conversation.json")
assert detail["messages"][:len(before["messages"])] == before["messages"]
assert detail["jobs"][:len(before["jobs"])] == before["jobs"]
assert detail["revisions"] == before["revisions"]
assert len(detail["jobs"]) == len(before["jobs"])+1
assert detail["reserved"] == {"model_requests": 3, "experiments": 1}
assert detail["limits"]["model_requests"] == 24 and detail["limits"]["experiments"] == 4
job = detail["jobs"][-1]
assert job["id"] == "c7af5d216275498d8d6e2f1a292ffa1c" and job["state"] == "completed" and job["error"] is None
pointer = next(item["result"] for item in detail["jobs"] if item["id"] == protocol["existing_experiment_job"])
directory = root / ".local/chat-price-experiments" / pointer["directory"]
assert pointer["sha256"] == protocol["existing_result_file_sha256"]
for name in ("results.json", "input-manifest.json", "input-daily.json", "approval.json"):
    assert (directory / name).read_bytes() == (previous_folder / "result" / name).read_bytes()
    put("referenced-result/"+name, (directory / name).read_bytes())
historical = read_result(out / "referenced-result", pointer)
assert historical == get("/api/chat/"+session+"/results/"+protocol["existing_experiment_job"])

db_path = root / ".local/conversations/chat.sqlite3"
with sqlite3.connect(db_path.as_uri()+"?mode=ro", uri=True) as connection:
    connection.execute("PRAGMA query_only=ON")
    payload_raw, request_hash = connection.execute("SELECT payload,hash FROM jobs WHERE id=? AND session=?", (job["id"], session)).fetchone()
payload = strict(payload_raw)
prepared = payload["prepared"]
assert digest({"session": session, "kind": job["kind"], "body": payload["body"]}) == request_hash
assert digest(prepared) == payload["prepared_sha256"]
assert prepared["response_schema"] == SCHEMA and job["result"]["schema_sha256"] == digest(SCHEMA)
assert prepared["evidence_sha256"] == digest(historical) == job["result"]["evidence"]["result_sha256"]
assert payload["body"]["text"] == protocol["request"] and payload["body"]["context_ids"] == []
assert job["result"]["context"]["included_ids"] == [] and len(prepared["messages"]) == 2
assert check_context(prepared["messages"], schema=SCHEMA)["request_bytes"] == job["result"]["context"]["request_bytes"]
raw = strict(job["result"]["raw"])
topics = validate(raw, historical)
assert topics == ["return", "drawdown", "scope"]
explanation = job["result"]["explanation"]
assert raw["criterion"] == protocol["criterion"] and raw["assessment"] == protocol["expected_assessment"]
assert explanation["status"] == "consistent" and explanation["summary"] == compose(historical, topics)
assert detail["messages"][-1]["content"] == explanation["summary"]
assert len(detail["messages"]) == len(before["messages"])+2

# Independently check the recorded criterion from saved decimals, without strategy execution.
base, candidate = historical["baseline"], historical["candidate"]
assert Decimal(candidate["return_percent"]) > Decimal(base["return_percent"])
assert Decimal(candidate["max_drawdown_percent"]) > Decimal(base["max_drawdown_percent"])
assert Decimal(candidate["return_percent"]) < 0 and Decimal(base["return_percent"]) < 0
assert "no queda respaldada" in explanation["summary"] and "perder menos" in explanation["summary"]
assert not any(word in explanation["summary"] for word in ("Stop-loss", "Cortos", "cumple cualitativamente"))
overview = get("/api/simulation")
assert overview["accounts"] == [] and overview["receipts"] == []
save("conversation.json", detail)
save("prepared-request.json", payload)
save("result-pointer.json", pointer)
save("audit.json", {"previous_messages_jobs_and_revisions_byte_equivalent": True,
    "original_result_and_input_copies_byte_identical": True, "request_and_context_hash_verified": True,
    "schema_and_evidence_fingerprints_verified": True, "criterion_checked_from_saved_decimals": True,
    "browser_evidence_selection_context_and_send_verified": True, "visible_explanation_matches_stored_text": True,
    "model_free_text_published": False, "model_selected_topics": topics, "requested_cost_topic_omitted": True,
    "model_retries": 0, "new_backtests": 0, "accounts_and_inbox_unchanged": True})

cases = ET.parse(out / "tests.xml").findall(".//testcase")
counts = Counter(case.attrib["classname"] for case in cases)
assert len(cases) == 525 and counts["tests.test_conversation_explanation"] == 41
failed = [case for case in cases if case.find("failure") is not None]
assert len(failed) == 1 and failed[0].attrib["name"] == "test_rejected_transport_does_not_create_storage[headers3-400]"
assert failed[0].attrib["classname"] == "tests.test_tv_receiver" and "10053" in failed[0].find("failure").text
assert not any(case.find("error") is not None or case.find("skipped") is not None for case in cases)
recheck = ET.parse(out / "transport-recheck.xml").findall(".//testcase")
assert len(recheck) == 1 and not list(recheck[0])
assert recheck[0].attrib["name"] == failed[0].attrib["name"]
node = "C:/Users/34656/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
subprocess.run([node, "--check", "trading_ai/lab_static/app.js"], cwd=root, check=True, capture_output=True)
subprocess.run(["git", "diff", "--check"], cwd=root, check=True, capture_output=True)
assert (out / "ui-checked-explanation.jpg").read_bytes().startswith(b"\xff\xd8\xff")
sources = ("trading_ai/conversation_explanation.py", "trading_ai/conversation.py", "trading_ai/conversation_provider.py",
           "trading_ai/lab_static/app.js", "tests/test_conversation_explanation.py",
           "tests/test_conversation.py", "tests/test_conversation_prices.py")
for relative in sources:
    put("tested-source/"+relative, (root / relative).read_bytes())
put("tested-source/collect-evidence.py", Path(__file__).read_bytes())
manifest = {"date": "2026-10-22", "phase_closed": False, "phase7_started": False,
    "protocol_sha256": hash_file(out / "protocol.json"), "new_explanation_tests": 41,
    "focused_conversation_tests_passed": 113, "selected_tests": 525, "initial_passed": 524, "initial_failed": 1,
    "isolated_transport_recheck_passed": 1, "initial_suite_all_green": False, "full_suite_run": False,
    "test_counts": dict(counts), "javascript_syntax_checked": True, "git_diff_whitespace_checked": True,
    "source_sha256": {relative: hash_file(root / relative) for relative in sources},
    "unchanged_prior_source_sha256": unchanged, "prior_evidence_verified": prior,
    "real_session": session, "real_message_job": job["id"], "real_model_requests_this_increment": 1,
    "model_provider": job["result"]["provider"], "usage": job["usage"], "model_selected_topics": topics,
    "model_omitted_requested_cost_topic": True, "free_semantic_reliability_claimed": False,
    "text_origin": "python_templates", "criterion": raw["criterion"], "assessment": raw["assessment"],
    "previous_conversation_preserved": True, "original_price_files_and_result_unchanged": True,
    "budget_before": protocol["budget_before"], "budget_after": detail["reserved"],
    "budget_limits": protocol["budget_limits"], "new_backtests": 0, "automatic_retries": 0,
    "accounting_processed": False, "external_orders_sent": False, "project_status_edited_this_increment": False,
    "committed": False, "pushed": False,
    "evidence_sha256": {path.relative_to(out).as_posix(): hash_file(path) for path in sorted(out.rglob("*"))
                        if path.is_file() and path.name != "manifest.json"}}
save("manifest.json", manifest)
for relative, expected in manifest["evidence_sha256"].items(): assert hash_file(out / relative) == expected
print(json.dumps({"selected_tests": 525, "initial_passed": 524, "initial_failed": 1, "isolated_recheck_passed": 1,
    "evidence_files": len(manifest["evidence_sha256"]), "prior_reports_verified": len(prior),
    "real_message_job": job["id"], "manifest_sha256": hash_file(out / "manifest.json")}, indent=2))
