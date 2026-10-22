"""Auditoría independiente del JSON anual frente a los dos CSV del usuario."""

from collections import defaultdict
import csv
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import uuid

root = Path(__file__).resolve().parents[2]
output = root / ".local/ev-data" / ("annual-2025-" + uuid.uuid4().hex)
output.mkdir(parents=True)
raw = Path("C:/Users/34656/Downloads/2025.json.gz").read_bytes()
(output / "original.json.gz").write_bytes(raw)
data = json.loads(gzip.decompress(raw), parse_float=Decimal)
assert isinstance(data, list) and len(data) == 6223
assert all(set(row) == set(("ts", "o", "h", "l", "c", "ao", "ah", "al", "ac", "v")) for row in data)
assert all(type(row["ts"]) is int and row["ts"] % 3600 == 0 and datetime.fromtimestamp(row["ts"], UTC).year == 2025 for row in data)
assert all(left["ts"] < right["ts"] for left, right in zip(data, data[1:]))
indexed = {row["ts"]: row for row in data}
comparisons = []
for side, columns in (("BID", ("o", "h", "l", "c")), ("ASK", ("ao", "ah", "al", "ac"))):
    path = Path("C:/Users/34656/Downloads") / f"EUR-USD_1Hour_{side}_2025-01-01_to_2025-01-31_Etc_UTC.csv"
    original = path.read_bytes()
    rows = list(csv.DictReader(io.StringIO(original.decode("utf-8-sig"))))
    january = [row for row in data if datetime.fromtimestamp(row["ts"], UTC).month == 1]
    times = {int(datetime.fromisoformat(row["Etc/UTC"]).timestamp()) for row in rows}
    missing, extra = sorted(times - set(indexed)), sorted(row["ts"] for row in january if row["ts"] not in times)
    differences = []
    for row in rows:
        ts = int(datetime.fromisoformat(row["Etc/UTC"]).timestamp())
        if ts not in indexed:
            continue
        for source, target in zip(("Open", "High", "Low", "Close"), columns):
            if Decimal(row[source]) != indexed[ts][target]:
                differences.append({"at": row["Etc/UTC"], "field": source, "csv": row[source], "annual": str(indexed[ts][target])})
    comparisons.append({"side": side, "original_sha256": sha256(original).hexdigest(), "csv_rows": len(rows),
                        "annual_january_rows": len(january), "missing": missing, "extra": extra,
                        "ohlc_differences": differences})

days = defaultdict(list)
for row in data:
    days[datetime.fromtimestamp(row["ts"], UTC).date().isoformat()].append(row["ts"])
internal = [{"date": date, "from": datetime.fromtimestamp(left + 3600, UTC).isoformat(),
             "to": datetime.fromtimestamp(right, UTC).isoformat()}
            for date, rows in days.items() for left, right in zip(rows, rows[1:]) if right != left + 3600]
long_gaps = [{"from": datetime.fromtimestamp(left["ts"] + 3600, UTC).isoformat(),
              "to": datetime.fromtimestamp(right["ts"], UTC).isoformat()}
             for left, right in zip(data, data[1:]) if right["ts"] - left["ts"] > 97 * 3600]
audit = {"method": "independent_json_decimal_csv_comparison", "provider": "EV Trading Labs",
         "claimed_upstream": "Dukascopy", "catalog_url": "https://evtradelabs.com/data",
         "catalog_path": "EURUSD/H1/2025.json.gz", "raw_sha256": sha256(raw).hexdigest(), "bytes": len(raw),
         "hourly_rows": len(data), "daily_sessions": len(days), "internal_gaps": internal, "gaps_over_96_hours": long_gaps,
         "comparisons": comparisons, "volume_units_verified": False,
         "license_as_displayed": "free use with attribution to EV Trading Labs"}
(output / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"output": str(output), **audit}, ensure_ascii=False, indent=2))
