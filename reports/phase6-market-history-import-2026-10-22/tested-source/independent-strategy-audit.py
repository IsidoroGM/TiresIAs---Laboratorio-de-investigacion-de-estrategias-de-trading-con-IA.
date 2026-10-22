"""Reproduce SMA, órdenes y efectivo desde el gzip sin importar código del proyecto."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
import gzip
from hashlib import sha256
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
raw = Path("C:/Users/34656/Downloads/2025.json.gz").read_bytes()
rows = json.loads(gzip.decompress(raw), parse_float=Decimal)
groups = defaultdict(list)
for row in rows:
    opening = datetime.fromtimestamp(row["ts"], UTC)
    if datetime(2025, 1, 1, tzinfo=UTC) <= opening < datetime(2025, 12, 25, tzinfo=UTC):
        groups[opening.date().isoformat()].append(row)
days = sorted(groups)
stored = json.loads((root / ".local/dukascopy-research/72061a4aa7a0455cb400edcc580cb964/simulation.json").read_bytes())
programmatic = json.loads((root / ".local/dukascopy-research/4a05aab5ccbf49649328cd1282d5a546/simulation.json").read_bytes())
for key in ("configuration", "sessions_sha256", "observations", "hypothetical_fills", "equity_curve", "summary"):
    assert stored[key] == programmatic[key]


def stamp(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


with localcontext(Context(prec=28)):
    closes = [Decimal(groups[day][-1]["c"]) for day in days]
    fast = [sum(closes[i-19:i+1], Decimal(0)) / 20 if i >= 19 else None for i in range(len(days))]
    slow = [sum(closes[i-59:i+1], Decimal(0)) / 60 if i >= 59 else None for i in range(len(days))]
    cash, position, basis, fee_total, realized = Decimal(1000), Decimal(0), Decimal(0), Decimal(0), Decimal(0)
    peak, max_dd, pending, fill_index = cash, Decimal(0), None, 0
    for index, day in enumerate(days):
        hours = groups[day]
        if pending:
            price = Decimal(hours[0]["ao"] if pending["side"] == "buy" else hours[0]["o"])
            fee = price * Decimal("0.001")
            execution_time = stamp(datetime.fromtimestamp(hours[0]["ts"], UTC))
            expected = stored["hypothetical_fills"][fill_index]
            assert expected["side"] == pending["side"] and expected["signal_at"] == pending["signal_at"]
            assert expected["executed_at"] == execution_time and execution_time >= pending["signal_at"]
            assert Decimal(expected["price"]) == price and Decimal(expected["assumed_commission"]) == fee
            if pending["side"] == "buy":
                assert cash >= price + fee
                cash -= price + fee
                position, basis = Decimal(1), price + fee
            else:
                cash += price - fee
                realized += price - fee - basis
                position, basis = Decimal(0), Decimal(0)
            fee_total += fee
            fill_index += 1
            pending = None
        signal = "none"
        if index >= 60:
            if fast[index-1] <= slow[index-1] and fast[index] > slow[index]:
                signal = "enter_long"
            elif fast[index-1] >= slow[index-1] and fast[index] < slow[index]:
                signal = "exit_long"
        observation = stored["observations"][index]
        assert observation["signal"] == signal
        for key, value in (("fast", fast[index]), ("slow", slow[index])):
            assert observation[key] is None if value is None else Decimal(observation[key]) == value
        if signal == "enter_long" and position == 0 or signal == "exit_long" and position > 0:
            pending = {"side": "buy" if signal == "enter_long" else "sell",
                       "signal_at": stamp(datetime.fromisoformat(day).replace(tzinfo=UTC) + timedelta(days=1))}
        equity = cash + position * Decimal(hours[-1]["c"])
        peak = max(peak, equity)
        dd = (peak - equity) / peak * 100
        max_dd = max(max_dd, dd)
        saved = stored["equity_curve"][index]
        assert Decimal(saved["cash"]) == cash and Decimal(saved["quantity"]) == position
        assert Decimal(saved["equity"]) == equity and Decimal(saved["drawdown_percent"]) == dd
        assert saved["at"] == stamp(datetime.fromtimestamp(hours[-1]["ts"] + 3600, UTC))
    assert fill_index == len(stored["hypothetical_fills"]) == 3
    summary = stored["summary"]
    for key, expected in (("final_equity", equity), ("cash", cash), ("open_quantity", position),
                          ("assumed_commissions", fee_total), ("realized_pnl", realized), ("max_observed_drawdown_percent", max_dd)):
        assert Decimal(summary[key]) == expected

audit = {"method": "independent_stdlib_decimal_raw_hourly_to_sma_execution_and_accounting",
         "raw_sha256": sha256(raw).hexdigest(), "daily_sessions_checked": len(days), "fills_checked": fill_index,
         "all_indicators_and_signals_match": True, "all_cash_positions_equity_and_drawdown_points_match": True,
         "browser_matches_programmatic_result": True, "final_equity_usd": summary["final_equity"],
         "open_quantity_eur": summary["open_quantity"], "assumed_commission_rate": "0.001",
         "project_modules_imported": False, "accounting_processed": False}
with (root / ".local/ev-data/independent-strategy-audit.json").open("x", encoding="utf-8") as stream:
    json.dump(audit, stream, indent=2)
print(json.dumps(audit, indent=2))
