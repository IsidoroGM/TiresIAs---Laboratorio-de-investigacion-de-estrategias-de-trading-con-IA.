"""Comprobación independiente de ambos BI5 contra los CSV originales del usuario."""

import csv
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import json
import lzma
from pathlib import Path
import struct

root = Path(__file__).resolve().parent / "auto-pilot-2025-01-2026-10-22"
results = []
for side in ("BID", "ASK"):
    original = Path("C:/Users/34656/Downloads") / f"EUR-USD_1Hour_{side}_2025-01-01_to_2025-01-31_Etc_UTC.csv"
    csv_raw = original.read_bytes()
    rows = list(csv.DictReader(csv_raw.decode("utf-8-sig").splitlines()))
    binary = (root / "raw" / f"2025-01-{side}.bi5").read_bytes()
    records = list(struct.iter_unpack(">5If", lzma.decompress(binary)))
    observed = {}
    for seconds, opening, closing, low, high, volume in records:
        if volume == 0 and opening == closing == low == high:
            continue
        timestamp = (datetime(2025, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds)).isoformat()
        assert timestamp not in observed
        observed[timestamp] = {key: Decimal(value) / 100000 for key, value in
                               (("Open", opening), ("High", high), ("Low", low), ("Close", closing))}
    assert set(observed) == {row["Etc/UTC"] for row in rows}
    for row in rows:
        assert all(observed[row["Etc/UTC"]][key] == Decimal(row[key]) for key in ("Open", "High", "Low", "Close"))
    results.append({"side": side, "csv_rows": len(rows), "binary_observed_rows": len(observed),
                    "all_timestamps_match": True, "all_ohlc_prices_match": True,
                    "csv_sha256": sha256(csv_raw).hexdigest(), "bi5_sha256": sha256(binary).hexdigest()})
audit = {"method": "independent_stdlib_binary_decoder_against_user_csv", "results": results}
with (root / "csv-comparison.json").open("x", encoding="utf-8") as stream:
    json.dump(audit, stream, ensure_ascii=False, indent=2)
print(json.dumps(audit, indent=2))
