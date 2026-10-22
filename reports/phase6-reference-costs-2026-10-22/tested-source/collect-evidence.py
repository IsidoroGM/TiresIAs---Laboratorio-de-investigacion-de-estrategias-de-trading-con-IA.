"""Freeze the reference/cost increment and verify prior evidence byte for byte."""

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
from trading_ai.market_benchmark import load_benchmark

out = root / "reports/phase6-reference-costs-2026-10-22"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def freeze(source, relative):
    target = out / relative
    raw = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw, relative
    else:
        with target.open("xb") as stream:
            stream.write(raw)


prior = {}
for name in ("phase6-dukascopy-2026-10-22", "phase6-dukascopy-paired-2026-10-22",
             "phase6-dukascopy-history-2026-10-22", "phase6-dukascopy-spread-2026-10-22",
             "phase6-market-history-import-2026-10-22", "phase6-period-validation-2026-10-22"):
    folder = root / "reports" / name
    value = read(folder / "manifest.json")
    for relative, expected in value["evidence_sha256"].items():
        assert digest(folder / relative) == expected, (name, relative)
    prior[name] = {"manifest_sha256": digest(folder / "manifest.json"),
                   "verified_evidence_files": len(value["evidence_sha256"])}
previous = read(root / "reports/phase6-period-validation-2026-10-22/manifest.json")
unchanged = previous["unchanged_engine_and_import_source_sha256"]
for relative in ("trading_ai/market_comparison.py", "tests/test_market_comparison.py", "trading_ai/lab_static/simulation.css"):
    unchanged[relative] = previous["source_sha256"][relative]
for relative, expected in unchanged.items():
    assert digest(root / relative) == expected, relative

runs_path = root / ".local/ev-data/reference-costs-real-runs.json"
audit_path = root / ".local/ev-data/reference-costs-independent-audit.json"
runs, audit = read(runs_path), read(audit_path)
assert digest(out / "protocol.json") == runs["protocol_sha256"] == audit["protocol_sha256"]
assert audit["scenarios_checked"] == 8 and audit["equity_points_checked"] == 4920 and audit["fills_checked"] == 44
assert audit["base_rate_matches_previous_runs"] is True and runs["accounts_and_inbox_unchanged"] is True
for period in audit["periods"]:
    assert digest(Path(f'C:/Users/34656/Downloads/{period["year"]}.json.gz')) == period["raw_sha256"]
    assert all(item["all_indicators_signals_fills_and_equity_match"] for item in period["scenarios"])
for side, expected in previous["original_csv_sha256"].items():
    assert digest(Path(f"C:/Users/34656/Downloads/EUR-USD_1Hour_{side}_2025-01-01_to_2025-01-31_Etc_UTC.csv")) == expected

browser_id = "9473356c47414d66ba7d631573469e88"
browser_directory = root / ".local/market-benchmarks" / browser_id
programmatic_2025 = root / ".local/market-benchmarks" / runs["runs"][1]["id"]
assert (browser_directory / "benchmark.json").read_bytes() == (programmatic_2025 / "benchmark.json").read_bytes()
assert (browser_directory / "summary.json").read_bytes() == (programmatic_2025 / "summary.json").read_bytes()
copied_results = []
for index, item in enumerate(runs["runs"]):
    label = ("2024", "2025", "2024-full-blocked", "2025-full-blocked")[index]
    source = browser_directory if index == 1 else root / ".local/market-benchmarks" / item["id"]
    for name in ("benchmark.json", "summary.json", "input-manifest.json", "input-daily.json"):
        freeze(source / name, f"runs/{label}/{name}")
    value, summary = load_benchmark(out / "runs" / label)
    assert summary == item["summary"]
    if index >= 2:
        assert value["status"] == "blocked_internal_gaps" and value["scenarios"] == [] and value["cash_reference"] is None
    for name, expected in value["implementation_sha256"].items():
        assert digest(root / "trading_ai" / name) == expected, name
    copied_results.append({"label": label, "id": browser_id if index == 1 else item["id"],
        "status": summary["status"], "result_sha256": value["result_sha256"],
        "result_file_sha256": digest(source / "benchmark.json")})


def request(path):
    connection = HTTPConnection("127.0.0.1", 64162, timeout=10)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        assert response.status == 200
        return json.loads(response.read())
    finally:
        connection.close()


detail = request("/api/simulation/market-benchmarks/"+browser_id)
assert detail["summary"] == runs["runs"][1]["summary"]
overview = request("/api/simulation")
assert overview["accounts"] == [] and overview["receipts"] == []
assert next(item for item in overview["dukascopy"]["benchmarks"] if item["id"] == browser_id)["inputs_verified_now"] is False
ui_audit = {"browser_result_id": browser_id, "browser_calculation_button_verified": True,
    "zero_and_base_commission_selection_verified": True, "both_period_views_verified": True,
    "browser_result_byte_identical_to_programmatic_2025": True,
    "http_detail_matches_stored_result": True, "catalog_metadata_only": True,
    "accounting_processed": False, "accounts_and_inbox_unchanged": True}
ui_path = root / ".local/ev-data/reference-costs-ui-audit.json"
ui_raw = (json.dumps(ui_audit, indent=2)+"\n").encode()
if ui_path.exists():
    assert ui_path.read_bytes() == ui_raw
else:
    with ui_path.open("xb") as stream:
        stream.write(ui_raw)

cases = ET.parse(out / "tests.xml").findall(".//testcase")
counts = Counter(case.attrib["classname"] for case in cases)
assert len(cases) == 391 and counts["tests.test_market_benchmark"] == 28
assert all(not list(case) for case in cases)
assert "391 passed" in (out / "tests.log").read_text(encoding="utf-8")
node = "C:/Users/34656/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
subprocess.run([node, "--check", "trading_ai/lab_static/simulation.js"], cwd=root, check=True, capture_output=True)
subprocess.run(["git", "diff", "--check"], cwd=root, check=True, capture_output=True)
for name in ("ui-2024-cost-grid.jpg", "ui-2025-cost-grid.jpg", "ui-2025-base-scenario.jpg"):
    assert (out / name).read_bytes().startswith(b"\xff\xd8\xff")

sources = ("trading_ai/market_benchmark.py", "trading_ai/dukascopy_service.py", "trading_ai/tv_service.py",
           "trading_ai/lab_static/simulation.js", "tests/test_market_benchmark.py")
copies = {"real-runs.json": runs_path, "independent-audit.json": audit_path, "ui-and-http-audit.json": ui_path,
          "tested-source/independent-reference-cost-audit.py": root / ".local/ev-data/audit_reference_costs.py",
          "tested-source/run-reference-costs.py": root / ".local/ev-data/run_reference_costs.py",
          "tested-source/collect-evidence.py": Path(__file__)}
for relative in sources:
    assert all(line.rstrip() == line for line in (root / relative).read_text(encoding="utf-8").splitlines()), relative
    copies["tested-source/"+relative] = root / relative
for target, source in copies.items():
    freeze(source, target)

manifest = {"date": "2026-10-22", "phase_closed": False, "phase7_started": False,
    "protocol_sha256": digest(out / "protocol.json"), "tests_passed": 391, "new_reference_cost_tests": 28,
    "test_counts": dict(counts), "full_suite_run": False, "javascript_syntax_checked": True,
    "git_diff_whitespace_checked": True, "source_sha256": {relative: digest(root / relative) for relative in sources},
    "unchanged_prior_source_sha256": unchanged, "prior_evidence_verified": prior,
    "commission_rates": ["0", "0.0005", "0.001", "0.002"], "reference_entry_session_index": 61,
    "capital_usd_each_scenario": "1000", "fixed_quantity_eur": "1", "rate_or_strategy_selected": False,
    "independent_scenarios_verified": 8, "independent_equity_points_checked": 4920, "independent_fills_checked": 44,
    "base_rate_matches_previous_sma_runs": True, "sma_below_cash_all_eight_scenarios": True,
    "sma_vs_buy_hold": {"2024": "higher_equity_all_rates", "2025": "lower_equity_all_rates"},
    "copied_results": copied_results, "browser_result_id": browser_id,
    "browser_action_and_commission_selector_verified": True, "original_price_files_unchanged": True,
    "full_year_quality_blocks_preserved": True, "accounting_processed": False, "external_orders_sent": False,
    "prospective_validation": False, "project_status_edited_this_increment": False, "committed": False, "pushed": False,
    "evidence_sha256": {path.relative_to(out).as_posix(): digest(path) for path in sorted(out.rglob("*"))
                        if path.is_file() and path.name != "manifest.json"}}
raw_manifest = (json.dumps(manifest, ensure_ascii=False, indent=2)+"\n").encode("utf-8")
target = out / "manifest.json"
if target.exists():
    assert target.read_bytes() == raw_manifest
else:
    with target.open("xb") as stream:
        stream.write(raw_manifest)
for relative, expected in manifest["evidence_sha256"].items():
    assert digest(out / relative) == expected
print(json.dumps({"tests_passed": 391, "evidence_files": len(manifest["evidence_sha256"]),
    "prior_reports_verified": len(prior), "independent_scenarios_checked": 8,
    "browser_result_id": browser_id, "manifest_sha256": digest(target)}, indent=2))
