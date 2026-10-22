"""Freeze evidence of the supplied-history increment without modifying older reports."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/phase6-market-history-import-2026-10-22"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def freeze(source, relative):
    target = OUT / relative
    raw = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw, f"Existing evidence differs: {relative}"
    else:
        with target.open("xb") as stream:
            stream.write(raw)


assert OUT.is_dir()
prior_evidence = {}
for name in (
    "phase6-dukascopy-2026-10-22", "phase6-dukascopy-paired-2026-10-22",
    "phase6-dukascopy-history-2026-10-22", "phase6-dukascopy-spread-2026-10-22",
):
    folder = ROOT / "reports" / name
    manifest = read_json(folder / "manifest.json")
    for relative, expected in manifest["evidence_sha256"].items():
        assert digest(folder / relative) == expected, (name, relative)
    prior_evidence[name] = {
        "manifest_sha256": digest(folder / "manifest.json"),
        "verified_evidence_files": len(manifest["evidence_sha256"]),
    }

prior_sources = read_json(ROOT / "reports/phase6-dukascopy-history-2026-10-22/manifest.json")["source_sha256"]
for relative, expected in prior_sources.items():
    assert digest(ROOT / relative) == expected, relative

annual_audit_path = ROOT / ".local/ev-data/annual-2025-af54173f782b4134bbeafceb1e0b3a48/audit.json"
annual_audit = read_json(annual_audit_path)
raw_path = Path("C:/Users/34656/Downloads/2025.json.gz")
assert digest(raw_path) == annual_audit["raw_sha256"]
assert digest(annual_audit_path.parent / "original.json.gz") == annual_audit["raw_sha256"]
original_csv = {}
for comparison in annual_audit["comparisons"]:
    side = comparison["side"]
    path = Path(f"C:/Users/34656/Downloads/EUR-USD_1Hour_{side}_2025-01-01_to_2025-01-31_Etc_UTC.csv")
    assert digest(path) == comparison["original_sha256"]
    assert comparison["csv_rows"] == comparison["annual_january_rows"] == 528
    assert not comparison["missing"] and not comparison["extra"] and not comparison["ohlc_differences"]
    original_csv[side] = digest(path)

selected_path = ROOT / ".local/dukascopy/ev-eurusd-2025-to-dec24-2026-10-22/manifest.json"
full_path = ROOT / ".local/dukascopy/ev-eurusd-2025-full-2026-10-22/manifest.json"
selected, full = read_json(selected_path), read_json(full_path)
assert selected["daily_sessions"] == 307 and selected["selected_hours"] == 6122
assert selected["excluded_hours_outside_period"] == 101
assert selected["internal_gap_count"] == selected["coverage_gap_count"] == 0
assert full["daily_sessions"] == 313 and full["selected_hours"] == 6223
assert full["internal_gap_count"] == 2

live_audit_path = ROOT / ".local/ev-data/live-import-audit.json"
live_audit = read_json(live_audit_path)
imported = read_json(ROOT / ".local/dukascopy" / live_audit["annual"]["id"] / "manifest.json")
assert imported == selected
january = read_json(ROOT / ".local/dukascopy" / live_audit["january_csv"]["id"] / "manifest.json")
pilot = read_json(ROOT / ".local/dukascopy/auto-pilot-2025-01-2026-10-22/manifest.json")
assert january["sessions_sha256"] == pilot["sessions_sha256"]
assert live_audit["accounts_and_inbox_unchanged"] is True
assert live_audit["browser_file_picker_completed"] is False

browser_path = ROOT / ".local/dukascopy-research/72061a4aa7a0455cb400edcc580cb964/simulation.json"
programmatic_path = ROOT / ".local/dukascopy-research/4a05aab5ccbf49649328cd1282d5a546/simulation.json"
blocked_path = ROOT / ".local/dukascopy-research/ad476afc753b4da9af2d408fd5e73222/simulation.json"
browser, programmatic, blocked = map(read_json, (browser_path, programmatic_path, blocked_path))
for key in ("configuration", "sessions_sha256", "observations", "hypothetical_fills", "equity_curve", "summary"):
    assert browser[key] == programmatic[key], key
assert browser["status"] == "simulated" and len(browser["hypothetical_fills"]) == 3
assert browser["summary"]["final_equity"] == "999.98870447"
assert blocked["status"] == "blocked_internal_gaps" and blocked["summary"] is None
assert not blocked["hypothetical_fills"]
for name, expected in browser["implementation_sha256"].items():
    assert digest(ROOT / "trading_ai" / name) == expected, name

independent_path = ROOT / ".local/ev-data/independent-strategy-audit.json"
independent = read_json(independent_path)
assert independent["daily_sessions_checked"] == 307 and independent["fills_checked"] == 3
assert independent["all_indicators_and_signals_match"] is True
assert independent["all_cash_positions_equity_and_drawdown_points_match"] is True
assert independent["browser_matches_programmatic_result"] is True

cases = ET.parse(OUT / "tests.xml").findall(".//testcase")
counts = Counter(case.attrib["classname"] for case in cases)
assert len(cases) == 339 and counts["tests.test_market_history"] == 40
assert all(not list(case) for case in cases), "Unexpected failures, skips or captured error output"
assert "339 passed" in (OUT / "tests.log").read_text(encoding="utf-8")
node = Path("C:/Users/34656/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")
syntax = subprocess.run([str(node), "--check", "trading_ai/lab_static/simulation.js"], cwd=ROOT,
                        check=True, capture_output=True, text=True)
whitespace = subprocess.run(["git", "diff", "--check"], cwd=ROOT,
                            check=True, capture_output=True, text=True)
for relative in ("trading_ai/market_history.py", "tests/test_market_history.py", "docs/MARKET_DATA.md"):
    assert all(line.rstrip() == line for line in (ROOT / relative).read_text(encoding="utf-8").splitlines()), relative
for relative in ("ui-real-period.jpg", "ui-real-results.jpg"):
    assert (OUT / relative).read_bytes().startswith(b"\xff\xd8\xff"), relative

copies = {
    "annual-csv-comparison.json": annual_audit_path,
    "fxcm-access-probe.json": ROOT / ".local/fxcm/probe-212e188bb575483b823acf98f529394c/report.json",
    "selected-history-manifest.json": selected_path,
    "full-year-history-manifest.json": full_path,
    "real-backtest-result.json": browser_path,
    "full-year-quality-result.json": blocked_path,
    "first-real-backtest.json": ROOT / ".local/ev-data/first-real-backtest-2026-10-22.json",
    "live-import-audit.json": live_audit_path,
    "independent-strategy-audit.json": independent_path,
    "tested-source/independent-annual-csv-comparison.py": ROOT / ".local/fxcm/inspect_ev_annual.py",
    "tested-source/independent-strategy-audit.py": ROOT / ".local/ev-data/independent_strategy_audit.py",
    "tested-source/collect-evidence.py": Path(__file__),
}
sources = (
    "trading_ai/market_history.py", "trading_ai/dukascopy_backtest.py", "trading_ai/dukascopy_service.py",
    "trading_ai/tv_service.py", "trading_ai/lab_static/simulation.js", "trading_ai/lab_static/simulation.css",
    "tests/test_market_history.py",
)
copies.update({"tested-source/" + relative: ROOT / relative for relative in sources})
for target, source in copies.items():
    freeze(source, target)

evidence_hashes = {path.relative_to(OUT).as_posix(): digest(path)
                   for path in sorted(OUT.rglob("*")) if path.is_file() and path.name != "manifest.json"}
manifest = {
    "date": "2026-10-22", "phase_closed": False,
    "tests_passed": 339, "new_history_import_tests": 40, "test_counts": dict(counts),
    "full_suite_run": False, "javascript_syntax_checked": syntax.returncode == 0,
    "git_diff_whitespace_checked": whitespace.returncode == 0,
    "source_sha256": {relative: digest(ROOT / relative) for relative in sources},
    "unchanged_prior_source_sha256": prior_sources,
    "prior_evidence_verified": prior_evidence,
    "original_csv_sha256": original_csv, "annual_original_sha256": digest(raw_path),
    "evidence_sha256": evidence_hashes,
    "selected_period": ["2025-01-01", "2025-12-25"], "end_date_exclusive": True,
    "period_reason": "before_first_date_with_internal_hourly_gaps_not_selected_by_profit",
    "selected_hours": 6122, "selected_daily_sessions": 307, "excluded_hours_outside_period": 101,
    "annual_hours": 6223, "annual_daily_sessions": 313, "annual_internal_gaps": 2,
    "complete_year_result_status": blocked["status"],
    "real_data_result_status": browser["status"], "hypothetical_fills": 3,
    "real_result_file_sha256": digest(browser_path), "real_result_summary": browser["summary"],
    "independent_strategy_reconstruction_matches": True,
    "browser_calculation_verified": True, "browser_file_picker_completed": False,
    "real_file_import_verified_via": "explicit_local_http_api",
    "january_csv_sessions_match_previous_bi5": True,
    "january_sessions_sha256": january["sessions_sha256"],
    "source_provider": "EV Trading Labs", "catalog_url": "https://evtradelabs.com/data",
    "attribution": selected["attribution"], "provider_authenticated": False,
    "all_final_transports_https": None, "volume_units_verified": False,
    "bulk_2024_2025_complete": False, "accounting_processed": False,
    "accounts_and_inbox_unchanged": True, "project_status_edited_this_increment": False,
    "committed": False, "pushed": False,
}
raw_manifest = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
target = OUT / "manifest.json"
if target.exists():
    assert target.read_bytes() == raw_manifest
else:
    with target.open("xb") as stream:
        stream.write(raw_manifest)
for relative, expected in manifest["evidence_sha256"].items():
    assert digest(OUT / relative) == expected
print(json.dumps({"tests_passed": 339, "evidence_files": len(evidence_hashes),
                  "prior_reports_verified": len(prior_evidence), "originals_unchanged": True,
                  "independent_reconstruction_matches": True, "manifest_sha256": digest(target)}, indent=2))
