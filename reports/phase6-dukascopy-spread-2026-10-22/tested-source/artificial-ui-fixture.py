"""Caso ARTIFICIAL aislado para revisar curva y operaciones; no son datos de mercado."""

import calendar
from datetime import UTC, datetime
import json
import lzma
from pathlib import Path
import struct
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from trading_ai.dukascopy_history import prepare_history
from trading_ai.dukascopy_service import DukascopyResearch

workspace = root / ".local/dukascopy-spread-ui-artificial-2026-10-22"


def artificial(url):
    parts = url.split("/")
    year, month, ask = int(parts[-3]), int(parts[-2]) + 1, parts[-1].startswith("ASK_")
    records = []
    for hour in range(calendar.monthrange(year, month)[1] * 24):
        day = hour // 24 + (datetime(year, month, 1) - datetime(2025, 1, 1)).days
        offset = day if day < 60 else 120 - day if day < 120 else day - 120
        price = 120000 - offset * 200 + (10 if ask else 0)
        records.append(struct.pack(">5If", hour * 3600, price, price, price, price, 1.0 if hour % 24 == 22 else 0.0))
    return {"body": lzma.compress(b"".join(records), format=lzma.FORMAT_ALONE), "final_url": url,
            "content_type": "application/octet-stream", "retrieved_at": "2026-01-01T00:00:00Z"}


prepare_history(first="2025-01", last="2025-06", cache=workspace / "cache",
                output=workspace / ".local/dukascopy/ARTIFICIAL-NOT-MARKET-DATA", fetch=artificial, pause=0)
research = DukascopyResearch(workspace)
result = research.run(dataset="ARTIFICIAL-NOT-MARKET-DATA", capital="1000", quantity="1", commission_rate="0.001")
saved = research.get(result["id"])
assert saved["status"] == "simulated" and saved["summary"]["closed_trades"] >= 1
audit = {"role": "synthetic_ui_test_not_market_evidence", "root": str(workspace), "result_id": result["id"],
         "daily_sessions": saved["daily_sessions"], "hypothetical_fills": len(saved["hypothetical_fills"]),
         "closed_trades": saved["summary"]["closed_trades"], "result_sha256": saved["result_sha256"]}
(workspace / "fixture-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
print(json.dumps(audit, indent=2))
