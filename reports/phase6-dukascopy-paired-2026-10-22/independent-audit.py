"""Contraste independiente de la muestra CSV, sin importar el lector del proyecto."""

import csv
from datetime import datetime
from decimal import Decimal, localcontext
from hashlib import sha256
import io
import json
from pathlib import Path


root = Path(__file__).resolve().parent
report = json.loads((root / "report.json").read_text(encoding="utf-8"))
sources = {}
for side in ("bid", "ask"):
    raw = (root / side / "original.csv").read_bytes()
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    assert len(rows) == 528
    assert sha256(raw).hexdigest() == report[side]["original_sha256"]
    times = [datetime.fromisoformat(row["Etc/UTC"]) for row in rows]
    assert len(set(times)) == len(times) and times == sorted(times)
    for row in rows:
        prices = [Decimal(row[field]) for field in ("Open", "High", "Low", "Close")]
        assert all(value.is_finite() and value > 0 for value in prices)
        assert prices[1] == max(prices) and prices[2] == min(prices)
    sources[side] = rows
assert [row["Etc/UTC"] for row in sources["bid"]] == [row["Etc/UTC"] for row in sources["ask"]]
with localcontext() as context:
    context.prec = 64
    spreads = [Decimal(ask[field]) - Decimal(bid[field])
               for bid, ask in zip(sources["bid"], sources["ask"], strict=True)
               for field in ("Open", "Close")]
    assert min(spreads) >= 0
    assert min(spreads) == Decimal(report["observed_quote_differences"]["minimum"])
    assert max(spreads) == Decimal(report["observed_quote_differences"]["maximum"])
audit = {"method": "stdlib_csv_datetime_decimal_without_project_reader",
         "matching_intervals": 528, "duplicates": 0, "ohlc_errors": 0,
         "negative_open_close_quote_differences": 0,
         "raw_sources_match_saved_hashes": True,
         "accounting_processed": False, "daily_strategy_executed": False}
with (root / "independent-audit.json").open("x", encoding="utf-8") as stream:
    json.dump(audit, stream, ensure_ascii=False, indent=2)
print(json.dumps(audit, ensure_ascii=False))
