"""Freeze the fixed-period comparison and verify prior evidence without editing it."""

from collections import Counter
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2]
out = root / "reports/phase6-period-validation-2026-10-22"


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def freeze(source, relative):
    target = out / relative
    raw = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw, relative
    else:
        with target.open("xb") as stream:
            stream.write(raw)


previous = {}
for name in ("phase6-dukascopy-2026-10-22", "phase6-dukascopy-paired-2026-10-22",
             "phase6-dukascopy-history-2026-10-22", "phase6-dukascopy-spread-2026-10-22",
             "phase6-market-history-import-2026-10-22"):
    folder = root / "reports" / name
    value = read(folder / "manifest.json")
    for relative, expected in value["evidence_sha256"].items():
        assert digest(folder / relative) == expected, (name, relative)
    previous[name] = {"manifest_sha256": digest(folder / "manifest.json"),
                      "verified_files": len(value["evidence_sha256"])}

unchanged = read(root / "reports/phase6-dukascopy-history-2026-10-22/manifest.json")["source_sha256"]
latest = read(root / "reports/phase6-market-history-import-2026-10-22/manifest.json")
for relative in ("trading_ai/market_history.py", "trading_ai/dukascopy_backtest.py", "tests/test_market_history.py"):
    unchanged[relative] = latest["source_sha256"][relative]
for relative, expected in unchanged.items():
    assert digest(root / relative) == expected, relative

quality_path = root / ".local/ev-data/2024-quality-before-results.json"
results_path = root / ".local/ev-data/2024-validation-results.json"
audit_path = root / ".local/ev-data/two-period-independent-audit.json"
quality, results, audit = map(read, (quality_path, results_path, audit_path))
assert digest(out / "protocol.json") == quality["protocol_sha256"] == results["protocol_sha256"] == audit["protocol_sha256"]
assert results["accounts_and_inbox_unchanged"] is True
raw_hashes = {}
for period in audit["periods"]:
    year = period["year"]
    raw_hashes[str(year)] = digest(Path(f"C:/Users/34656/Downloads/{year}.json.gz"))
    assert raw_hashes[str(year)] == period["raw_sha256"]
    assert period["all_indicators_signals_fills_and_equity_points_match"] is True
assert sum(p["sessions_checked"] for p in audit["periods"]) == 615
assert sum(p["fills_checked"] for p in audit["periods"]) == 9

csv_hashes = {}
for side, expected in latest["original_csv_sha256"].items():
    path = Path(f"C:/Users/34656/Downloads/EUR-USD_1Hour_{side}_2025-01-01_to_2025-01-31_Etc_UTC.csv")
    assert digest(path) == expected
    csv_hashes[side] = expected

identity = "2b074e42dc4148869384309a04926154"
comparison_dir = root / ".local/market-comparisons" / identity
comparison = read(comparison_dir / "comparison.json")
assert comparison["status"] == "compared" and not comparison["balances_combined"]
assert [p["daily_sessions"] for p in comparison["periods"]] == [308, 307]
assert [p["summary"]["final_equity"] for p in comparison["periods"]] == ["999.96832951", "999.98870447"]
for item in comparison["inputs"]:
    for file in item["files"]:
        assert digest(comparison_dir / file["file"]) == file["sha256"]
        freeze(comparison_dir / file["file"], "comparison/" + file["file"])
freeze(comparison_dir / "comparison.json", "comparison/comparison.json")


def request(path):
    connection = HTTPConnection("127.0.0.1", 64162, timeout=10)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        assert response.status == 200
        return json.loads(response.read())
    finally:
        connection.close()


assert request("/api/simulation/market-comparisons/" + identity) == comparison
overview = request("/api/simulation")
assert overview["accounts"] == [] and overview["receipts"] == []
listed = next(item for item in overview["dukascopy"]["comparisons"] if item["id"] == identity)
assert listed["inputs_verified_now"] is False
api_audit = {"comparison_id": identity, "http_detail_matches_stored_result": True,
             "browser_form_and_comparison_view_verified": True, "catalog_is_metadata_only": True,
             "accounts_and_inbox_unchanged": True, "strategy_recalculated_on_read": False}
api_path = root / ".local/ev-data/period-comparison-ui-audit.json"
api_raw = (json.dumps(api_audit, indent=2) + "\n").encode()
if api_path.exists():
    assert api_path.read_bytes() == api_raw
else:
    with api_path.open("xb") as stream:
        stream.write(api_raw)

cases = ET.parse(out / "tests.xml").findall(".//testcase")
counts = Counter(case.attrib["classname"] for case in cases)
assert len(cases) == 363 and counts["tests.test_market_comparison"] == 24
assert all(not list(case) for case in cases)
assert "363 passed" in (out / "tests.log").read_text(encoding="utf-8")
node = "C:/Users/34656/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
subprocess.run([node, "--check", "trading_ai/lab_static/simulation.js"], cwd=root, check=True, capture_output=True)
subprocess.run(["git", "diff", "--check"], cwd=root, check=True, capture_output=True)
for relative in ("ui-period-comparison.jpg", "ui-comparison-settings.jpg"):
    assert (out / relative).read_bytes().startswith(b"\xff\xd8\xff")

copies = {
    "quality-before-results.json": quality_path,
    "validation-results.json": results_path,
    "independent-strategy-audit.json": audit_path,
    "ui-and-http-audit.json": api_path,
    "selected-2024-manifest.json": root / ".local/dukascopy/ev-eurusd-2024-to-dec24-2026-10-22/manifest.json",
    "full-year-2024-manifest.json": root / ".local/dukascopy/ev-eurusd-2024-full-2026-10-22/manifest.json",
    "full-year-2024-quality-result.json": root / ".local/dukascopy-research" / results["results"]["full_year_diagnostic"]["id"] / "simulation.json",
    "tested-source/independent-period-audit.py": root / ".local/ev-data/audit_two_periods.py",
    "tested-source/prepare-2024-validation.py": root / ".local/ev-data/prepare_2024_validation.py",
    "tested-source/run-2024-validation.py": root / ".local/ev-data/run_2024_validation.py",
    "tested-source/collect-evidence.py": Path(__file__),
}
sources = ("trading_ai/market_comparison.py", "trading_ai/dukascopy_service.py", "trading_ai/tv_service.py",
           "trading_ai/lab_static/simulation.js", "trading_ai/lab_static/simulation.css", "tests/test_market_comparison.py")
for relative in sources:
    assert all(line.rstrip() == line for line in (root / relative).read_text(encoding="utf-8").splitlines()), relative
    copies["tested-source/" + relative] = root / relative
for target, source in copies.items():
    freeze(source, target)

manifest = {"date": "2026-10-22", "phase_closed": False, "phase7_started": False,
    "tests_passed": 363, "new_period_comparison_tests": 24, "test_counts": dict(counts),
    "full_suite_run": False, "javascript_syntax_checked": True, "git_diff_whitespace_checked": True,
    "protocol_sha256": digest(out / "protocol.json"),
    "source_sha256": {relative: digest(root / relative) for relative in sources},
    "unchanged_engine_and_import_source_sha256": unchanged,
    "prior_evidence_verified": previous, "original_annual_sha256": raw_hashes, "original_csv_sha256": csv_hashes,
    "comparison_id": identity, "comparison_sha256": comparison["comparison_sha256"],
    "periods": comparison["periods"], "full_year_2024_status": "blocked_internal_gaps",
    "annual_2024_hours": 6247, "annual_2024_observed_utc_dates": 314,
    "selected_2024_hours": 6144, "selected_2024_sessions": 308, "excluded_2024_hours": 103,
    "original_annual_files_2024_and_2025_obtained": True, "complete_market_calendar_verified": False,
    "independent_audit_sessions": 615, "independent_audit_fills": 9,
    "browser_comparison_action_verified": True, "prospective_validation": False, "parameter_search": False,
    "provider": "EV Trading Labs", "catalog_url": "https://evtradelabs.com/data",
    "provider_authenticated": False, "all_final_transports_https": None,
    "accounting_processed": False, "accounts_and_inbox_unchanged": True,
    "project_status_edited_this_increment": False, "committed": False, "pushed": False,
    "evidence_sha256": {path.relative_to(out).as_posix(): digest(path) for path in sorted(out.rglob("*"))
                        if path.is_file() and path.name != "manifest.json"}}
raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
target = out / "manifest.json"
if target.exists():
    assert target.read_bytes() == raw
else:
    with target.open("xb") as stream:
        stream.write(raw)
for relative, expected in manifest["evidence_sha256"].items():
    assert digest(out / relative) == expected
print(json.dumps({"tests_passed": 363, "new_tests": 24, "evidence_files": len(manifest["evidence_sha256"]),
                  "prior_reports_verified": len(previous), "independent_sessions_checked": 615,
                  "comparison_id": identity, "manifest_sha256": digest(target)}, indent=2))
