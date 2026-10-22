"""Independent raw-price reconstruction. Uses only Python stdlib, no project imports."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
import gzip
from hashlib import sha256
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
protocol_path = root / "reports/phase6-period-validation-2026-10-22/protocol.json"
protocol = json.loads(protocol_path.read_bytes())
runs = json.loads((root / ".local/ev-data/2024-validation-results.json").read_bytes())
assert sha256(protocol_path.read_bytes()).hexdigest() == runs["protocol_sha256"]


def stamp(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


audits = []
for year, identity in ((2024, runs["results"]["fixed_period"]["id"]), (2025, runs["reference_2025_run"])):
    raw = Path(f"C:/Users/34656/Downloads/{year}.json.gz").read_bytes()
    rows = json.loads(gzip.decompress(raw), parse_float=Decimal)
    grouped = defaultdict(list)
    for row in rows:
        opening = datetime.fromtimestamp(row["ts"], UTC)
        if datetime(year, 1, 1, tzinfo=UTC) <= opening < datetime(year, 12, 25, tzinfo=UTC):
            grouped[opening.date().isoformat()].append(row)
    days = sorted(grouped)
    stored = json.loads((root / ".local/dukascopy-research" / identity / "simulation.json").read_bytes())
    with localcontext(Context(prec=28)):
        initial = Decimal(protocol["initial_capital_usd_each_period"])
        size = Decimal(protocol["fixed_quantity_eur"])
        rate = Decimal(protocol["assumed_commission_rate_per_fill"])
        closes = [Decimal(grouped[day][-1]["c"]) for day in days]
        fast = [sum(closes[i-19:i+1], Decimal(0)) / 20 if i >= 19 else None for i in range(len(days))]
        slow = [sum(closes[i-59:i+1], Decimal(0)) / 60 if i >= 59 else None for i in range(len(days))]
        cash, position, basis, peak = initial, Decimal(0), Decimal(0), initial
        fee_total, realized, max_dd, spread_total = (Decimal(0) for _ in range(4))
        pending, fill_index, closed = None, 0, 0
        for index, day in enumerate(days):
            hours = grouped[day]
            if pending:
                bid, ask = Decimal(hours[0]["o"]), Decimal(hours[0]["ao"])
                price = ask if pending["side"] == "buy" else bid
                fee = size * price * rate
                expected = stored["hypothetical_fills"][fill_index]
                execution_time = stamp(datetime.fromtimestamp(hours[0]["ts"], UTC))
                assert expected["side"] == pending["side"] and expected["signal_at"] == pending["signal_at"]
                assert expected["executed_at"] == execution_time and execution_time >= pending["signal_at"]
                assert Decimal(expected["price"]) == price and Decimal(expected["assumed_commission"]) == fee
                assert Decimal(expected["quantity"]) == size
                if pending["side"] == "buy":
                    assert cash >= size * price + fee
                    cash -= size * price + fee
                    position, basis = size, size * price + fee
                else:
                    cash += size * price - fee
                    realized += size * price - fee - basis
                    position, basis = Decimal(0), Decimal(0)
                    closed += 1
                fee_total += fee
                spread_total += size * (ask-bid) / 2
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
            dd = (peak-equity) / peak * 100
            max_dd = max(max_dd, dd)
            point = stored["equity_curve"][index]
            assert Decimal(point["cash"]) == cash and Decimal(point["quantity"]) == position
            assert Decimal(point["equity"]) == equity and Decimal(point["drawdown_percent"]) == dd
            assert point["at"] == stamp(datetime.fromtimestamp(hours[-1]["ts"]+3600, UTC))
        assert fill_index == len(stored["hypothetical_fills"])
        assert stored["pending_order"] == pending and not stored["rejected_orders"]
        summary = stored["summary"]
        for key, value in (("final_equity", equity), ("cash", cash), ("open_quantity", position),
                           ("realized_pnl", realized), ("assumed_commissions", fee_total),
                           ("max_observed_drawdown_percent", max_dd), ("spread_vs_midpoint_diagnostic", spread_total),
                           ("return_percent", (equity/initial-1)*100)):
            assert Decimal(summary[key]) == value, (year, key)
        assert summary["closed_trades"] == closed
        audits.append({"year": year, "run_id": identity, "raw_sha256": sha256(raw).hexdigest(),
            "sessions_checked": len(days), "fills_checked": fill_index, "closed_trades": closed,
            "final_equity_usd": str(equity), "open_quantity_eur": str(position),
            "all_indicators_signals_fills_and_equity_points_match": True})
report = {"method": "stdlib_decimal_independent_reconstruction_from_annual_raw",
          "protocol_sha256": runs["protocol_sha256"], "periods": audits,
          "states_reset_each_period": True, "project_modules_imported": False,
          "parameter_search": False, "accounting_processed": False}
with (root / ".local/ev-data/two-period-independent-audit.json").open("x", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
print(json.dumps(report, indent=2))
