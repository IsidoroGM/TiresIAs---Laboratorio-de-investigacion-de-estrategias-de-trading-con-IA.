"""Independent raw-price reconstruction of the real chat comparison; stdlib only."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
import gzip
from hashlib import sha256
from http.client import HTTPConnection
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
session_id = "0190241d62b543c6b69b4a5db31051d6"
protocol_path = root / "reports/phase6-chat-prices-2026-10-22/protocol.json"
protocol = json.loads(protocol_path.read_bytes())


def get(path):
    connection = HTTPConnection("127.0.0.1", 64162, timeout=10)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        assert response.status == 200
        return json.loads(response.read())
    finally: connection.close()


def stamp(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


detail = get("/api/chat/"+session_id)
job = next(item for item in detail["jobs"] if item["kind"] == "experiment")
assert job["state"] == "completed"
result = get("/api/chat/"+session_id+"/results/"+job["id"])
model_draft = next(item for item in detail["revisions"] if item["data"]["origin"] == "model_suggestion")["data"]
assert {key: model_draft["candidate"][key] for key in ("strategy", "fast_window", "slow_window")} == protocol["requested_candidate"]
review = next(item for item in detail["revisions"] if item["hash"] == result["revision_sha256"])["data"]
assert review["origin"] == "human_review" and review["dataset"] == protocol["dataset"]
assert review["candidate"]["fast_window"] == 15 and review["candidate"]["slow_window"] == 45
raw = Path("C:/Users/34656/Downloads/2025.json.gz").read_bytes()
rows = json.loads(gzip.decompress(raw), parse_float=Decimal)
groups = defaultdict(list)
for row in rows:
    opening = datetime.fromtimestamp(row["ts"], UTC)
    if datetime(2025, 1, 1, tzinfo=UTC) <= opening < datetime(2025, 12, 25, tzinfo=UTC):
        groups[opening.date().isoformat()].append(row)
days = sorted(groups)
audits = []
for role, choice in (("baseline", protocol["reviewed_baseline"]), ("candidate", protocol["requested_candidate"])):
    stored = result["price_calculations"][role]
    fast_window, slow_window = choice["fast_window"], choice["slow_window"]
    with localcontext(Context(prec=28)):
        closes = [Decimal(groups[day][-1]["c"]) for day in days]
        fast = [sum(closes[i-fast_window+1:i+1], Decimal(0))/fast_window if i >= fast_window-1 else None for i in range(len(days))]
        slow = [sum(closes[i-slow_window+1:i+1], Decimal(0))/slow_window if i >= slow_window-1 else None for i in range(len(days))]
        initial, size, rate = Decimal(protocol["initial_capital_usd"]), Decimal(protocol["fixed_quantity_eur"]), Decimal(protocol["assumed_commission_rate"])
        cash, position, basis, peak = initial, Decimal(0), Decimal(0), initial
        fees, spread, realized, max_dd = (Decimal(0) for _ in range(4))
        pending, fills, closed = None, 0, 0
        for index, day in enumerate(days):
            hours = groups[day]
            if pending:
                bid, ask = Decimal(hours[0]["o"]), Decimal(hours[0]["ao"])
                price = ask if pending["side"] == "buy" else bid
                fee = size*price*rate
                saved = stored["hypothetical_fills"][fills]
                opening = stamp(datetime.fromtimestamp(hours[0]["ts"], UTC))
                assert saved["side"] == pending["side"] and saved["signal_at"] == pending["signal_at"]
                assert saved["executed_at"] == opening and opening >= pending["signal_at"]
                assert Decimal(saved["price"]) == price and Decimal(saved["assumed_commission"]) == fee
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
                pending = None
                fills += 1
            signal = "none"
            if index >= slow_window:
                if fast[index-1] <= slow[index-1] and fast[index] > slow[index]: signal = "enter_long"
                elif fast[index-1] >= slow[index-1] and fast[index] < slow[index]: signal = "exit_long"
            observation = stored["observations"][index]
            assert observation["signal"] == signal
            for key, value in (("fast", fast[index]), ("slow", slow[index])):
                assert observation[key] is None if value is None else Decimal(observation[key]) == value
            if signal == "enter_long" and position == 0 or signal == "exit_long" and position > 0:
                pending = {"side": "buy" if signal == "enter_long" else "sell",
                    "signal_at": stamp(datetime.fromisoformat(day).replace(tzinfo=UTC)+timedelta(days=1))}
            equity = cash+position*closes[index]
            peak = max(peak, equity)
            dd = (peak-equity)/peak*100
            max_dd = max(max_dd, dd)
            saved = stored["equity_curve"][index]
            assert Decimal(saved["cash"]) == cash and Decimal(saved["quantity"]) == position
            assert Decimal(saved["equity"]) == equity and Decimal(saved["drawdown_percent"]) == dd
            assert saved["at"] == stamp(datetime.fromtimestamp(hours[-1]["ts"]+3600, UTC))
        summary = stored["summary"]
        for key, value in (("cash", cash), ("open_quantity", position), ("final_equity", equity), ("realized_pnl", realized),
                           ("return_percent", (equity/initial-1)*100), ("max_observed_drawdown_percent", max_dd),
                           ("assumed_commissions", fees), ("spread_vs_midpoint_diagnostic", spread)):
            assert Decimal(summary[key]) == value, (role, key)
        assert summary["closed_trades"] == closed and len(stored["hypothetical_fills"]) == fills
        assert stored["pending_order"] == pending and not stored["rejected_orders"]
        audits.append({"role": role, "strategy": result[role]["strategy"], "sessions_checked": len(days),
            "fills_checked": fills, "final_equity_usd": summary["final_equity"],
            "all_indicators_signals_fills_equity_and_drawdown_match": True})

old = json.loads((root / ".local/dukascopy-research/72061a4aa7a0455cb400edcc580cb964/simulation.json").read_bytes())
for key in ("configuration", "observations", "hypothetical_fills", "equity_curve", "summary"):
    assert result["price_calculations"]["baseline"][key] == old[key]
assert result["assessment"] == {"drawdown_comparison": "higher", "return_comparison": "higher",
    "scope": "historical_sample_only", "verdict": "not_supported_in_sample"}
assert get('/api/simulation')['accounts'] == [] and get('/api/simulation')['receipts'] == []
audit = {"method": "independent_stdlib_decimal_raw_to_chat_sma_comparison", "session_id": session_id, "experiment_job_id": job["id"],
    "protocol_sha256": sha256(protocol_path.read_bytes()).hexdigest(), "raw_sha256": sha256(raw).hexdigest(), "calculations": audits,
    "equity_points_checked": 614, "fills_checked": 8, "baseline_matches_previous_real_run": True,
    "model_strategy_and_windows_preserved": True, "model_draft_status": model_draft["status"],
    "model_draft_questions": model_draft["questions"], "model_draft_unsupported": model_draft["unsupported"],
    "human_review_and_separate_approval_verified": True, "assessment_matches_independent_metrics": True,
    "project_modules_imported": False, "accounts_and_inbox_unchanged": True, "parameter_search": False}
with (root / ".local/ev-data/chat-prices-independent-audit.json").open("x", encoding="utf-8") as stream:
    json.dump(audit, stream, ensure_ascii=False, indent=2)
print(json.dumps({key: value for key, value in audit.items() if key not in ('model_draft_questions','model_draft_unsupported')}, ensure_ascii=False, indent=2))
