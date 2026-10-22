"""Reference arithmetic, fixed scenarios, quality blocks and explicit local actions."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal, getcontext
import gzip
from http.client import HTTPConnection
import json
import threading

import pytest

from trading_ai.market_benchmark import ENTRY_INDEX, RATES, calculate, hold_reference, load_benchmark, run_benchmark
from trading_ai.market_history import EV_FORMAT, prepare
from trading_ai.tv_contracts import canonical, checksum
from trading_ai.tv_service import SimulationService


def daily(count=64):
    sessions = []
    for index in range(count):
        day = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=index)
        stamp = lambda value: value.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        close = "10" if index < 62 else "15"
        sessions.append({"date": day.date().isoformat(), "session_close_at": stamp(day+timedelta(days=1)),
            "first_observed_open_at": stamp(day+timedelta(hours=22)),
            "last_observed_close_at": stamp(day+timedelta(hours=23)), "internal_gaps": [],
            "bid": {"open": "10", "close": close}, "ask": {"open": "11", "close": str(int(close)+1)}})
    return {"sessions": sessions, "sessions_sha256": checksum(sessions)}


def reference(data=None, **kwargs):
    return hold_reference(daily() if data is None else data, **{
        "capital": "100", "quantity": "2", "commission_rate": "0.01", **kwargs})


@pytest.fixture
def history(tmp_path):
    rows = []
    start = datetime(2025, 1, 1, tzinfo=UTC)
    for index in range(90):
        price = 1 + ((index % 30)-15)**2 / 10000
        rows.append({"ts": int((start+timedelta(days=index)).timestamp()),
                     **{key: price for key in ("o", "h", "l", "c")},
                     **{key: price+0.0001 for key in ("ao", "ah", "al", "ac")}, "v": 1})
    directory = tmp_path / ".local/dukascopy/sample"
    prepare(inputs=[{"name": "2025.json.gz", "side": "BOTH", "body": gzip.compress(canonical(rows))}],
        source_format=EV_FORMAT, year=2025, start_date="2025-01-01", end_date="2025-04-01", output=directory)
    return directory


def test_reference_waits_61_complete_sessions_buys_ask_marks_bid_and_charges_once():
    data, result = daily(), reference()
    assert len(result["hypothetical_fills"]) == 1
    fill = result["hypothetical_fills"][0]
    assert fill["executed_at"] == data["sessions"][ENTRY_INDEX]["first_observed_open_at"]
    assert fill["signal_at"] == data["sessions"][ENTRY_INDEX-1]["session_close_at"]
    assert fill["price"] == "11" and fill["assumed_commission"] == "0.22"
    assert result["equity_curve"][60]["equity"] == "100"
    assert result["equity_curve"][61]["equity"] == "97.78"
    assert result["summary"]["cash"] == "77.78" and result["summary"]["final_equity"] == "107.78"
    assert result["summary"]["assumed_commissions"] == "0.22" and result["summary"]["open_quantity"] == "2"
    assert result["summary"]["max_observed_drawdown_percent"] == "2.22"
    assert result["summary"]["closed_trades"] == 0 and result["summary"]["realized_pnl"] == "0"


def test_zero_commission_keeps_spread_and_does_not_force_a_final_sale():
    result = reference(commission_rate="0")
    assert result["equity_curve"][61]["equity"] == "98"
    assert result["summary"]["final_equity"] == "108"
    assert result["summary"]["assumed_commissions"] == "0"
    assert result["summary"]["open_quantity"] == "2" and len(result["hypothetical_fills"]) == 1


def test_reference_cannot_afford_entry_with_fee_and_does_not_resize_or_leverage():
    result = reference(capital="22")
    assert result["status"] == "entry_rejected_insufficient_cash"
    assert not result["hypothetical_fills"] and len(result["rejected_orders"]) == 1
    assert result["summary"]["final_equity"] == "22" and result["summary"]["open_quantity"] == "0"


@pytest.mark.parametrize("change", ["time", "crossed"])
def test_reference_rejects_impossible_execution(change):
    data = daily()
    if change == "time":
        data["sessions"][61]["first_observed_open_at"] = data["sessions"][59]["first_observed_open_at"]
    else:
        data["sessions"][61]["ask"]["open"] = "9"
    with pytest.raises(ValueError):
        reference(data)


def test_fixed_grid_cash_and_difference_arithmetic():
    result = calculate(daily(), capital="100", quantity="2")
    assert result["status"] == "calculated"
    assert tuple(item["commission_rate"] for item in result["scenarios"]) == RATES
    assert result["cash_reference"]["final_equity"] == "100" and result["cash_reference"]["interest_rate"] == "0"
    assert not result["configuration"]["parameter_selection"] and not result["accounting_processed"]
    for item in result["scenarios"]:
        sma, hold = item["sma"]["summary"], item["buy_hold"]["summary"]
        assert Decimal(item["sma_minus_buy_hold_usd"]) == Decimal(sma["final_equity"])-Decimal(hold["final_equity"])
        assert Decimal(item["sma_minus_cash_usd"]) == Decimal(sma["final_equity"])-100
        assert hold["initial_capital"] == sma["initial_capital"] == "100"
        assert item["sma"]["configuration"]["quantity"] == "2"
        assert item["sma"]["configuration"]["assumed_commission_rate"] == item["commission_rate"]


@pytest.mark.parametrize("count", [60, 61])
def test_comparison_requires_next_open_after_warmup(count):
    result = calculate(daily(count), capital="100", quantity="2")
    assert result["status"] == "insufficient_history" and result["required_sessions"] == 62
    assert result["missing_sessions"] == 62-count
    assert result["scenarios"] == [] and result["cash_reference"] is None


def test_62_sessions_are_sufficient_for_reference_without_inventing_sma_fills():
    result = calculate(daily(62), capital="100", quantity="2")
    assert result["status"] == "calculated"
    for item in result["scenarios"]:
        assert not item["sma"]["hypothetical_fills"] and len(item["buy_hold"]["hypothetical_fills"]) == 1


@pytest.mark.parametrize("kind,status", [("internal", "blocked_internal_gaps"), ("coverage", "blocked_coverage_gaps")])
def test_quality_blocks_all_references_without_profit_metrics(kind, status):
    data = daily()
    if kind == "internal":
        data["sessions"][10]["internal_gaps"] = [{"from": "missing", "to": "observed"}]
    else:
        data["blocking_gaps"] = [{"from": "missing", "to": "observed"}]
    result = calculate(data, capital="100", quantity="2")
    assert result["status"] == status and not result["scenarios"] and result["cash_reference"] is None


def test_future_close_does_not_change_reference_entry_or_earlier_equity():
    data, modified = daily(), deepcopy(daily())
    modified["sessions"][-1]["bid"]["close"] = "1000"
    before, after = reference(data), reference(modified)
    assert before["hypothetical_fills"] == after["hypothetical_fills"]
    assert before["equity_curve"][:-1] == after["equity_curve"][:-1]


def test_decimal_context_does_not_change_reference_results():
    expected, old = reference(), getcontext().prec
    try:
        getcontext().prec = 6
        assert reference() == expected
    finally:
        getcontext().prec = old


@pytest.mark.parametrize("capital,quantity", [("0", "1"), ("-1", "1"), ("100", "0"), ("NaN", "1")])
def test_invalid_amounts_rejected_before_output(history, tmp_path, capital, quantity):
    with pytest.raises(ValueError):
        run_benchmark(history=history, output=tmp_path / "result", capital=capital, quantity=quantity)
    assert not (tmp_path / "result").exists()


def test_preserves_inputs_and_does_not_recompute_when_loading(history, tmp_path, monkeypatch):
    directory = tmp_path / "result"
    summary = run_benchmark(history=history, output=directory, capital="1000", quantity="1")
    for name in ("manifest.json", "daily.json"):
        assert (directory / ("input-"+name)).read_bytes() == (history / name).read_bytes()
    def forbidden(*args, **kwargs):
        raise AssertionError("No strategy calculation during read")
    monkeypatch.setattr("trading_ai.market_benchmark.calculate", forbidden)
    monkeypatch.setattr("trading_ai.market_benchmark.simulate", forbidden)
    assert load_benchmark(directory)[1] == summary
    with pytest.raises(ValueError, match="ya existe"):
        run_benchmark(history=history, output=directory, capital="1000", quantity="1")


@pytest.mark.parametrize("filename", ["summary.json", "benchmark.json", "input-manifest.json", "input-daily.json"])
def test_modified_saved_result_summary_or_input_is_rejected(history, tmp_path, filename):
    directory = tmp_path / "result"
    run_benchmark(history=history, output=directory, capital="1000", quantity="1")
    path = directory / filename
    value = json.loads(path.read_bytes())
    value["changed"] = True
    path.write_bytes(canonical(value))
    with pytest.raises(ValueError):
        load_benchmark(directory)


def test_tampered_original_rejected_before_computing(history, tmp_path):
    path = history / "raw/00.json.gz"
    path.write_bytes(path.read_bytes()+b"changed")
    with pytest.raises(ValueError):
        run_benchmark(history=history, output=tmp_path / "result", capital="1000", quantity="1")
    assert not (tmp_path / "result").exists()


def test_service_action_has_no_account_effects_and_catalog_reads_only_metadata(history, tmp_path, monkeypatch):
    service = SimulationService(tmp_path)
    before = service.ledger.overview()
    result = service.action({"action": "benchmark_price_history", "dataset": "sample", "capital": "1000", "quantity": "1"})
    detail = service.get("market-benchmarks", result["id"])
    assert detail["summary"]["status"] == "calculated" and not detail["result"]["accounting_processed"]
    def forbidden(*args, **kwargs):
        raise AssertionError("Metadata catalog cannot load full results or recalculate")
    monkeypatch.setattr("trading_ai.dukascopy_service.load_benchmark", forbidden)
    monkeypatch.setattr("trading_ai.market_benchmark.calculate", forbidden)
    assert service.overview()["dukascopy"]["benchmarks"][0]["inputs_verified_now"] is False
    assert service.ledger.overview() == before


@pytest.mark.parametrize("identity", ["../outside", "..", None])
def test_invalid_dataset_path_rejected_without_writes(tmp_path, identity):
    with pytest.raises(ValueError):
        SimulationService(tmp_path).action({"action": "benchmark_price_history", "dataset": identity, "capital": "1000", "quantity": "1"})
    assert not (tmp_path / ".local").exists()


def test_http_action_requires_origin_and_token_and_returns_guarded_detail(history, tmp_path):
    from trading_ai.lab import create_server
    server = create_server(root=tmp_path, port=0)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05})
    thread.start()
    def request(method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()
    try:
        overview = request("GET", "/api/simulation")[1]
        body = canonical({"action": "benchmark_price_history", "dataset": "sample", "capital": "1000", "quantity": "1"})
        assert request("POST", "/api/simulation", body, {"Content-Type": "application/json"})[0] == 403
        headers = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{server.server_port}", "X-Tiresias-Action": overview["action_token"]}
        assert request("POST", "/api/simulation", body, {**headers, "Origin": "https://example.invalid"})[0] == 403
        assert request("POST", "/api/simulation", body, {**headers, "X-Tiresias-Action": "wrong"})[0] == 403
        code, result = request("POST", "/api/simulation", body, headers)
        assert code == 202
        code, detail = request("GET", "/api/simulation/market-benchmarks/"+result["id"])
        assert code == 200 and len(detail["summary"]["scenarios"]) == 4
        after = request("GET", "/api/simulation")[1]
        assert after["accounts"] == overview["accounts"] and after["receipts"] == overview["receipts"]
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
