"""Independent stdlib/Decimal SMA and reference audit from annual raw prices."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
import gzip
from hashlib import sha256
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
protocol_path = root / "reports/phase6-reference-costs-2026-10-22/protocol.json"
protocol = json.loads(protocol_path.read_bytes())
report = json.loads((root / ".local/ev-data/reference-costs-real-runs.json").read_bytes())
assert report["protocol_sha256"] == sha256(protocol_path.read_bytes()).hexdigest()
audits = []


def stamp(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def check_point(saved, cash, position, equity, dd, at):
    for key, value in (("cash", cash), ("quantity", position), ("equity", equity), ("drawdown_percent", dd)):
        assert Decimal(saved[key]) == value, key
    assert saved["at"] == at


for year, entry, old_id in ((2024, report["runs"][0], "caaf5ef7dac047fcb70c6eba7f5e57c6"),
                             (2025, report["runs"][1], "72061a4aa7a0455cb400edcc580cb964")):
    raw = Path(f"C:/Users/34656/Downloads/{year}.json.gz").read_bytes()
    rows = json.loads(gzip.decompress(raw), parse_float=Decimal)
    grouped = defaultdict(list)
    for row in rows:
        at = datetime.fromtimestamp(row["ts"], UTC)
        if datetime(year, 1, 1, tzinfo=UTC) <= at < datetime(year, 12, 25, tzinfo=UTC):
            grouped[at.date().isoformat()].append(row)
    days = sorted(grouped)
    result = json.loads((root / ".local/market-benchmarks" / entry["id"] / "benchmark.json").read_bytes())
    old_result = json.loads((root / ".local/dukascopy-research" / old_id / "simulation.json").read_bytes())
    assert [item["commission_rate"] for item in result["scenarios"]] == protocol["assumed_proportional_commission_rates_per_fill"]
    audit = {"year": year, "raw_sha256": sha256(raw).hexdigest(), "daily_sessions": len(days), "scenarios": []}
    with localcontext(Context(prec=28)):
        initial, size = Decimal(protocol["capital_usd_each_period"]), Decimal(protocol["fixed_quantity_eur"])
        closes = [Decimal(grouped[day][-1]["c"]) for day in days]
        fast = [sum(closes[i-19:i+1], Decimal(0))/20 if i >= 19 else None for i in range(len(days))]
        slow = [sum(closes[i-59:i+1], Decimal(0))/60 if i >= 59 else None for i in range(len(days))]
        assert result["cash_reference"]["final_equity"] == str(initial)
        for scenario in result["scenarios"]:
            rate = Decimal(scenario["commission_rate"])
            sma, hold = scenario["sma"], scenario["buy_hold"]
            cash, position, basis, peak = initial, Decimal(0), Decimal(0), initial
            fees, realized, spread, maximum_dd = (Decimal(0) for _ in range(4))
            hcash, hpos, hpeak, hddmax = initial, Decimal(0), initial, Decimal(0)
            hfee, hspread = Decimal(0), Decimal(0)
            pending, fill_index, closed = None, 0, 0
            for index, day in enumerate(days):
                hours = grouped[day]
                bid, ask = Decimal(hours[0]["o"]), Decimal(hours[0]["ao"])
                opening = stamp(datetime.fromtimestamp(hours[0]["ts"], UTC))
                mark_time = stamp(datetime.fromtimestamp(hours[-1]["ts"]+3600, UTC))
                if pending:
                    price = ask if pending["side"] == "buy" else bid
                    fee = size * price * rate
                    fill = sma["hypothetical_fills"][fill_index]
                    assert fill["side"] == pending["side"] and fill["signal_at"] == pending["signal_at"]
                    assert fill["executed_at"] == opening and opening >= pending["signal_at"]
                    assert Decimal(fill["price"]) == price and Decimal(fill["quantity"]) == size
                    assert Decimal(fill["assumed_commission"]) == fee
                    if pending["side"] == "buy":
                        assert cash >= size*price+fee
                        cash -= size*price+fee
                        position, basis = size, size*price+fee
                    else:
                        cash += size*price-fee
                        realized += size*price-fee-basis
                        position, basis = Decimal(0), Decimal(0)
                        closed += 1
                    fees += fee
                    spread += size*(ask-bid)/2
                    fill_index += 1
                    pending = None
                signal = "none"
                if index >= 60:
                    if fast[index-1] <= slow[index-1] and fast[index] > slow[index]:
                        signal = "enter_long"
                    elif fast[index-1] >= slow[index-1] and fast[index] < slow[index]:
                        signal = "exit_long"
                observation = sma["observations"][index]
                assert observation["signal"] == signal
                for key, value in (("fast", fast[index]), ("slow", slow[index])):
                    assert observation[key] is None if value is None else Decimal(observation[key]) == value
                if signal == "enter_long" and position == 0 or signal == "exit_long" and position > 0:
                    pending = {"side": "buy" if signal == "enter_long" else "sell",
                        "signal_at": stamp(datetime.fromisoformat(day).replace(tzinfo=UTC)+timedelta(days=1))}
                equity = cash+position*closes[index]
                peak = max(peak, equity)
                dd = (peak-equity)/peak*100
                maximum_dd = max(maximum_dd, dd)
                check_point(sma["equity_curve"][index], cash, position, equity, dd, mark_time)
                if index == 61:
                    hfee = size*ask*rate
                    assert hcash >= size*ask+hfee
                    hcash -= size*ask+hfee
                    hpos, hspread = size, size*(ask-bid)/2
                    assert len(hold["hypothetical_fills"]) == 1
                    fill = hold["hypothetical_fills"][0]
                    assert fill["executed_at"] == opening and fill["side"] == "buy"
                    previous_close = stamp(datetime.fromisoformat(days[60]).replace(tzinfo=UTC)+timedelta(days=1))
                    assert fill["signal_at"] == previous_close and opening >= previous_close
                    assert Decimal(fill["price"]) == ask and Decimal(fill["assumed_commission"]) == hfee
                hequity = hcash+hpos*closes[index]
                hpeak = max(hpeak, hequity)
                hdd = (hpeak-hequity)/hpeak*100
                hddmax = max(hddmax, hdd)
                check_point(hold["equity_curve"][index], hcash, hpos, hequity, hdd, mark_time)
            assert fill_index == len(sma["hypothetical_fills"]) and sma["pending_order"] == pending
            assert not sma["rejected_orders"] and not hold["rejected_orders"]
            for summary, values in ((sma["summary"], (("cash", cash), ("open_quantity", position), ("final_equity", equity),
                    ("return_percent", (equity/initial-1)*100), ("realized_pnl", realized), ("assumed_commissions", fees),
                    ("spread_vs_midpoint_diagnostic", spread), ("max_observed_drawdown_percent", maximum_dd))),
                  (hold["summary"], (("cash", hcash), ("open_quantity", hpos), ("final_equity", hequity),
                    ("return_percent", (hequity/initial-1)*100), ("realized_pnl", Decimal(0)), ("assumed_commissions", hfee),
                    ("spread_vs_midpoint_diagnostic", hspread), ("max_observed_drawdown_percent", hddmax)))):
                for key, value in values:
                    assert Decimal(summary[key]) == value, (year, str(rate), key)
            assert sma["summary"]["closed_trades"] == closed and hold["summary"]["closed_trades"] == 0
            assert Decimal(scenario["sma_minus_buy_hold_usd"]) == equity-hequity
            assert Decimal(scenario["sma_minus_cash_usd"]) == equity-initial
            if rate == Decimal("0.001"):
                for key in ("configuration", "observations", "hypothetical_fills", "equity_curve", "summary"):
                    assert sma[key] == old_result[key], (year, key)
            audit["scenarios"].append({"commission_rate": str(rate), "sma_fills_checked": fill_index,
                "hold_fills_checked": 1, "equity_points_checked": len(days)*2, "all_indicators_signals_fills_and_equity_match": True,
                "sma_equity_usd": str(equity), "hold_equity_usd": str(hequity),
                "sma_under_cash": equity < initial, "sma_minus_hold_usd": str(equity-hequity)})
    audits.append(audit)

result = {"method": "independent_stdlib_decimal_raw_prices_to_sma_and_buy_hold_all_fixed_commissions",
    "protocol_sha256": report["protocol_sha256"], "periods": audits, "scenarios_checked": 8,
    "equity_points_checked": sum(s["equity_points_checked"] for a in audits for s in a["scenarios"]),
    "fills_checked": sum(s["sma_fills_checked"]+s["hold_fills_checked"] for a in audits for s in a["scenarios"]),
    "base_rate_matches_previous_runs": True, "project_modules_imported": False, "accounting_processed": False}
with (root / ".local/ev-data/reference-costs-independent-audit.json").open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2)
print(json.dumps({key: value for key, value in result.items() if key != "periods"}, indent=2))
