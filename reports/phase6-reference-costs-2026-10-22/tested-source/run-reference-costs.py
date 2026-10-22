"""Execute the fixed reference/cost protocol without modifying previous runs."""

from hashlib import sha256
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from trading_ai.dukascopy_service import DukascopyResearch
from trading_ai.tv_simulation import SimulationLedger

protocol_path = root / "reports/phase6-reference-costs-2026-10-22/protocol.json"
protocol = json.loads(protocol_path.read_bytes())
research, ledger = DukascopyResearch(root), SimulationLedger(root)
before = ledger.overview()
results = []
for dataset in protocol["datasets"] + ["ev-eurusd-2024-full-2026-10-22", "ev-eurusd-2025-full-2026-10-22"]:
    entry = research.benchmark(dataset=dataset, capital=protocol["capital_usd_each_period"], quantity=protocol["fixed_quantity_eur"])
    summary = research.benchmark_result(entry["id"])["summary"]
    assert (summary["status"] == "calculated") == (dataset in protocol["datasets"])
    if summary["status"] != "calculated":
        assert summary["status"] == "blocked_internal_gaps" and summary["scenarios"] == [] and summary["cash_reference"] is None
    results.append({"dataset": dataset, "id": entry["id"], "summary": summary})
assert ledger.overview() == before
report = {"protocol_sha256": sha256(protocol_path.read_bytes()).hexdigest(), "runs": results,
          "accounts_and_inbox_unchanged": True, "parameter_search": False}
with (root / ".local/ev-data/reference-costs-real-runs.json").open("x", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
print(json.dumps({"accounts_unchanged": True, "runs": [{"dataset": item["dataset"], "id": item["id"],
    "status": item["summary"]["status"], "scenarios": [{"commission_rate": s["commission_rate"],
        "sma_equity_usd": s["sma"]["final_equity"], "buy_hold_equity_usd": s["buy_hold"]["final_equity"],
        "sma_minus_hold_usd": s["sma_minus_buy_hold_usd"], "sma_minus_cash_usd": s["sma_minus_cash_usd"],
        "reference_entry_at": s["reference_entry_at"]} for s in item["summary"]["scenarios"]]} for item in results]}, indent=2))
