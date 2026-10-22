"""Freeze the real chat/price integration and verify prior evidence without rerunning it."""

from collections import Counter
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from trading_ai.conversation_prices import read_result

out = root / "reports/phase6-chat-prices-2026-10-22"
session_id = "0190241d62b543c6b69b4a5db31051d6"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def put(relative, raw):
    path = out / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, relative
    else:
        with path.open("xb") as stream:
            stream.write(raw)


def save(relative, value):
    put(relative, (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))


def get(path):
    connection = HTTPConnection("127.0.0.1", 64162, timeout=10)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        assert response.status == 200, (path, response.status)
        return json.loads(response.read())
    finally:
        connection.close()


prior = {}
for name in ("phase6-dukascopy-2026-10-22", "phase6-dukascopy-paired-2026-10-22",
             "phase6-dukascopy-history-2026-10-22", "phase6-dukascopy-spread-2026-10-22",
             "phase6-market-history-import-2026-10-22", "phase6-period-validation-2026-10-22",
             "phase6-reference-costs-2026-10-22"):
    folder = root / "reports" / name
    value = read(folder / "manifest.json")
    for relative, expected in value["evidence_sha256"].items():
        assert digest(folder / relative) == expected, (name, relative)
    prior[name] = {"manifest_sha256": digest(folder / "manifest.json"),
                   "verified_evidence_files": len(value["evidence_sha256"])}
previous = read(root / "reports/phase6-reference-costs-2026-10-22/manifest.json")
unchanged = previous["unchanged_prior_source_sha256"] | previous["source_sha256"]
for relative, expected in unchanged.items():
    assert digest(root / relative) == expected, relative

originals = {
    "2024.json.gz": "66fa719d8e7d75c11e1c691b232471fe3c9323e91ed998e8b82fe943f85d38b2",
    "2025.json.gz": "75424fa8293615a3e98d7463c90c8e1ef446bff0f29388c894298249791c995c",
    "EUR-USD_1Hour_BID_2025-01-01_to_2025-01-31_Etc_UTC.csv": "7efe20d392e9bf9506e7db31ad0c31673bb0e63e953eaeefdeaf9a1bc7396910",
    "EUR-USD_1Hour_ASK_2025-01-01_to_2025-01-31_Etc_UTC.csv": "b7e7904e871ebe7d042be5ecac2187d28cdb0317ca3a29e1233f7457478a2905",
}
for name, expected in originals.items():
    assert digest(Path("C:/Users/34656/Downloads") / name) == expected, name

detail = get("/api/chat/"+session_id)
assert detail["limits"]["model_requests"] == 24 and detail["limits"]["experiments"] == 4
assert detail["reserved"] == {"model_requests": 2, "experiments": 1}
assert len(detail["jobs"]) == 3 and all(job["state"] == "completed" and job["error"] is None for job in detail["jobs"])
job = next(item for item in detail["jobs"] if item["kind"] == "experiment")
pointer = job["result"]
assert pointer["backend"] == "prices_bidask"
source = root / ".local/chat-price-experiments" / pointer["directory"]
for name in ("results.json", "input-manifest.json", "input-daily.json", "approval.json"):
    put("result/"+name, (source / name).read_bytes())
result = read_result(out / "result", pointer)
assert get("/api/chat/"+session_id+"/results/"+job["id"]) == result
assert result["assessment"]["verdict"] == "not_supported_in_sample"
assert result["accounting_processed"] is False and result["external_orders_sent"] is False
for name, expected in result["engine_sha256"].items():
    assert digest(root / "trading_ai" / name) == expected, name
review = next(item for item in detail["revisions"] if item["hash"] == result["revision_sha256"])
assert review["data"]["origin"] == "human_review"
assert review["data"]["protocol"] == "conversation_price_proposal_v1"
assert review["data"]["proposal"]["arguments"] == {"strategy": "sma", "fast_window": 15, "slow_window": 45}
responses = [item for item in detail["jobs"] if item["kind"] == "message"]
assert len(responses) == 2 and all(item["result"]["provider"]["model_digest"] ==
    "d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04" for item in responses)
assert responses[1]["result"]["context"]["result_job"] == job["id"]
assert responses[1]["result"]["context"]["included_ids"] == []
assert responses[1]["result"]["evidence"]["assessment"] == result["assessment"]
assert "cumple cualitativamente" in responses[1]["result"]["raw"]
overview = get("/api/simulation")
assert overview["accounts"] == [] and overview["receipts"] == []
save("conversation.json", detail)
save("result-pointer.json", pointer)
save("ui-and-http-audit.json", {
    "session_id": session_id, "experiment_job_id": job["id"],
    "browser_created_conversation_and_requested_model_proposal": True,
    "browser_selected_source_reviewed_and_saved_revision": True,
    "browser_separate_approval_and_result_view_verified": True,
    "both_equity_curves_fills_and_source_link_observed": True,
    "browser_attached_result_without_previous_messages": True,
    "python_verdict_visible_above_model_comment_and_in_result": True,
    "model_semantic_error_preserved": True, "model_retry_performed": False,
    "http_matches_stored_result": True, "input_copies_and_approval_verified": True,
    "accounts_and_inbox_unchanged": True,
    "budget_before": {"model_requests": 0, "experiments": 0}, "budget_after": detail["reserved"],
})

audit_path = root / ".local/ev-data/chat-prices-independent-audit.json"
audit = read(audit_path)
assert audit["protocol_sha256"] == digest(out / "protocol.json")
assert audit["equity_points_checked"] == 614 and audit["fills_checked"] == 8
assert audit["baseline_matches_previous_real_run"] and audit["assessment_matches_independent_metrics"]
assert audit["human_review_and_separate_approval_verified"] and not audit["parameter_search"]
put("independent-audit.json", audit_path.read_bytes())

cases = ET.parse(out / "tests.xml").findall(".//testcase")
counts = Counter(case.attrib["classname"] for case in cases)
assert len(cases) == 463 and counts["tests.test_conversation_prices"] == 26 and counts["tests.test_conversation"] == 46
assert all(not list(case) for case in cases)
assert "463 passed" in (out / "tests.log").read_text(encoding="utf-8")
node = "C:/Users/34656/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
subprocess.run([node, "--check", "trading_ai/lab_static/app.js"], cwd=root, check=True, capture_output=True)
subprocess.run(["git", "diff", "--check"], cwd=root, check=True, capture_output=True)
for name in ("ui-chat-price-result.jpg", "ui-model-explanation.jpg"):
    assert (out / name).read_bytes().startswith(b"\xff\xd8\xff")

sources = ("trading_ai/conversation_prices.py", "trading_ai/conversation.py", "trading_ai/lab.py",
           "trading_ai/lab_static/app.js", "trading_ai/lab_static/chat.css", "tests/test_conversation_prices.py")
for relative in sources:
    put("tested-source/"+relative, (root / relative).read_bytes())
put("tested-source/independent-chat-price-audit.py", (root / ".local/ev-data/audit_chat_prices.py").read_bytes())
put("tested-source/collect-evidence.py", Path(__file__).read_bytes())

manifest = {"date": "2026-10-22", "phase_closed": False, "phase7_started": False,
    "protocol_sha256": digest(out / "protocol.json"), "tests_passed": 463, "new_chat_price_tests": 26,
    "previous_conversation_tests": 46, "prior_selected_tests": 391, "test_counts": dict(counts),
    "full_suite_run": False, "javascript_syntax_checked": True, "git_diff_whitespace_checked": True,
    "source_sha256": {relative: digest(root / relative) for relative in sources},
    "unchanged_prior_source_sha256": unchanged, "prior_evidence_verified": prior, "original_price_sha256": originals,
    "real_conversation": session_id, "real_experiment_job": job["id"], "result_sha256": pointer["sha256"],
    "review_origin": "human_review", "candidate": "SMA15/SMA45", "baseline": "SMA20/SMA60",
    "criterion": "higher_return_without_more_drawdown", "assessment": result["assessment"],
    "independent_equity_points_checked": 614, "independent_fills_checked": 8,
    "baseline_matches_previous_real_run": True, "parameter_search": False, "strategy_selected": False,
    "model": responses[0]["result"]["provider"], "real_model_responses": 2,
    "model_semantic_error_observed_and_preserved": True, "semantic_reliability_claimed": False,
    "budget_limits": {"model_requests": 24, "experiments": 4}, "reserved_after": detail["reserved"],
    "accounts_and_inbox_unchanged": True, "accounting_processed": False, "external_orders_sent": False,
    "prospective_validation": False, "project_status_edited_this_increment": False, "committed": False, "pushed": False,
    "evidence_sha256": {path.relative_to(out).as_posix(): digest(path) for path in sorted(out.rglob("*"))
                        if path.is_file() and path.name != "manifest.json"}}
save("manifest.json", manifest)
for relative, expected in manifest["evidence_sha256"].items():
    assert digest(out / relative) == expected
print(json.dumps({"tests_passed": 463, "evidence_files": len(manifest["evidence_sha256"]),
    "prior_reports_verified": len(prior), "independent_equity_points_checked": 614,
    "session": session_id, "manifest_sha256": digest(out / "manifest.json")}, indent=2))
