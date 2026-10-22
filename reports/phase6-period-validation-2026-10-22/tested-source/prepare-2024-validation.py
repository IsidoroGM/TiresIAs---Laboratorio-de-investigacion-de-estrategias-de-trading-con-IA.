"""Audit and prepare the fixed 2024 periods before calculating strategy metrics."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from trading_ai.market_history import EV_FORMAT, prepare

protocol_path = root / "reports/phase6-period-validation-2026-10-22/protocol.json"
protocol = json.loads(protocol_path.read_bytes())
assert protocol["additional_period"] == ["2024-01-01", "2024-12-25"]
raw = Path("C:/Users/34656/Downloads/2024.json.gz").read_bytes()
rows = json.loads(gzip.decompress(raw), parse_float=Decimal)
grouped = defaultdict(list)
for row in rows:
    opening = datetime.fromtimestamp(row["ts"], UTC)
    assert opening.year == 2024 and row["ts"] % 3600 == 0
    grouped[opening.date().isoformat()].append(row)
assert all(a["ts"] < b["ts"] for a, b in zip(rows, rows[1:]))
gaps = [{"date": day, "from": datetime.fromtimestamp(a["ts"]+3600, UTC).isoformat(),
         "to": datetime.fromtimestamp(b["ts"], UTC).isoformat()}
        for day, items in grouped.items() for a, b in zip(items, items[1:]) if b["ts"]-a["ts"] != 3600]
long_gaps = [{"from": a["ts"]+3600, "to": b["ts"]} for a, b in zip(rows, rows[1:])
             if b["ts"]-a["ts"]-3600 > 96*3600]
report = {"protocol_sha256": sha256(protocol_path.read_bytes()).hexdigest(),
          "raw_sha256": sha256(raw).hexdigest(), "bytes": len(raw), "hourly_rows": len(rows),
          "observed_utc_dates": len(grouped), "internal_gaps": gaps, "gaps_over_96_hours": long_gaps,
          "quality_checked_before_strategy_results": True, "periods": {}}
for label, end in (("fixed_period", "2024-12-25"), ("full_year_diagnostic", "2025-01-01")):
    identity = "ev-eurusd-2024-" + ("to-dec24" if label == "fixed_period" else "full") + "-2026-10-22"
    result = prepare(inputs=[{"name": "2024.json.gz", "side": "BOTH", "body": raw}], source_format=EV_FORMAT,
                     year=2024, start_date="2024-01-01", end_date=end,
                     output=root / ".local/dukascopy" / identity)
    report["periods"][label] = {"dataset": identity, "daily_sessions": result["daily_sessions"],
        "selected_hours": result["selected_hours"], "internal_gap_count": result["internal_gap_count"],
        "coverage_gap_count": result["coverage_gap_count"], "excluded_hours": result["excluded_hours_outside_period"]}
    assert result["internal_gap_count"] == sum(gap["date"] < end for gap in gaps)
    selected = [row for row in rows if datetime.fromtimestamp(row["ts"], UTC).date().isoformat() < end]
    assert result["selected_hours"] == len(selected)
with (root / ".local/ev-data/2024-quality-before-results.json").open("x", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
print(json.dumps(report, indent=2))
