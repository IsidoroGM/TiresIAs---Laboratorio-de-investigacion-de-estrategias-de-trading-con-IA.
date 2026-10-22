"""Run only the periods and settings frozen before downloading the additional year."""

import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from trading_ai.dukascopy_service import DukascopyResearch
from trading_ai.tv_simulation import SimulationLedger

protocol_path = root / "reports/phase6-period-validation-2026-10-22/protocol.json"
quality = json.loads((root / ".local/ev-data/2024-quality-before-results.json").read_bytes())
from hashlib import sha256
assert sha256(protocol_path.read_bytes()).hexdigest() == quality["protocol_sha256"]
protocol = json.loads(protocol_path.read_bytes())
ledger, research = SimulationLedger(root), DukascopyResearch(root)
before = ledger.overview()
results = {}
for label, item in quality["periods"].items():
    result = research.run(dataset=item["dataset"], capital=protocol["initial_capital_usd_each_period"],
        quantity=protocol["fixed_quantity_eur"], commission_rate=protocol["assumed_commission_rate_per_fill"])
    stored = research.get(result["id"])
    results[label] = {**result, "hypothetical_fills": len(stored["hypothetical_fills"]),
                      "result_sha256": stored["result_sha256"]}
assert results["fixed_period"]["status"] == "simulated"
assert results["full_year_diagnostic"]["status"] == "blocked_internal_gaps"
assert ledger.overview() == before
report = {"protocol_sha256": quality["protocol_sha256"], "results": results, "accounts_and_inbox_unchanged": True,
          "reference_2025_run": "72061a4aa7a0455cb400edcc580cb964"}
with (root / ".local/ev-data/2024-validation-results.json").open("x", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
print(json.dumps(report, indent=2))
