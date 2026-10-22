"""Aritmética, causalidad y originales: cotizaciones artificiales, nunca red."""

import calendar
from datetime import UTC, datetime, timedelta
from decimal import Decimal, getcontext
import json
import lzma
import struct

import pytest

from trading_ai.dukascopy_backtest import load_history, main, run_backtest, simulate
from trading_ai.dukascopy_history import prepare_history
from trading_ai.tv_contracts import canonical, checksum


def daily(closes=(3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3)):
    sessions = []
    for index, close in enumerate(closes):
        day = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=index)
        stamp = lambda value: value.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        sessions.append({"date": day.date().isoformat(), "session_close_at": stamp(day + timedelta(days=1)),
                         "first_observed_open_at": stamp(day + timedelta(hours=22)),
                         "last_observed_close_at": stamp(day + timedelta(hours=23)), "internal_gaps": [],
                         "bid": {"open": str(10 + index), "close": str(close)},
                         "ask": {"open": str(11 + index), "close": str(close + 1)}})
    return {"sessions": sessions, "sessions_sha256": checksum(sessions)}


def calculate(data=None, **kwargs):
    return simulate(daily() if data is None else data,
                    **{"capital": "100", "quantity": "2", "commission_rate": "0.01", "fast": 2, "slow": 3, **kwargs})


def source_fetch(url):
    parts = url.split("/")
    year, month = int(parts[-3]), int(parts[-2]) + 1
    ask = parts[-1].startswith("ASK_")
    records = []
    for hour in range(calendar.monthrange(year, month)[1] * 24):
        day = hour // 24 + (datetime(year, month, 1) - datetime(2025, 1, 1)).days
        price = 100000 + (day % 50 - 25) ** 2 + (10 if ask else 0)
        records.append(struct.pack(">5If", hour * 3600, price, price, price, price, 1.0 if hour % 24 == 22 else 0.0))
    return {"body": lzma.compress(b"".join(records), format=lzma.FORMAT_ALONE), "final_url": url,
            "content_type": "application/octet-stream", "retrieved_at": "2026-01-01T00:00:00Z"}


@pytest.fixture
def history(tmp_path):
    directory = tmp_path / ".local/dukascopy/sample"
    prepare_history(first="2025-01", last="2025-03", cache=tmp_path / "cache", output=directory,
                    now=datetime(2026, 1, 1, tzinfo=UTC), fetch=source_fetch, pause=0)
    return directory


def test_buy_ask_sell_bid_commission_and_spread_are_not_charged_twice():
    result = calculate()
    bought, sold = result["hypothetical_fills"]
    assert bought["signal_at"] == "2025-01-06T00:00:00.000Z"
    assert bought["executed_at"] == "2025-01-06T22:00:00.000Z"
    assert bought["price"] == "16" and bought["assumed_commission"] == "0.32"
    assert sold["price"] == "18" and sold["assumed_commission"] == "0.36"
    assert bought["quote_basis"] == "ask_open" and sold["quote_basis"] == "bid_open"
    summary = result["summary"]
    assert summary["cash"] == summary["final_equity"] == "103.32"
    assert summary["realized_pnl"] == "3.32" and summary["assumed_commissions"] == "0.68"
    assert summary["spread_vs_midpoint_diagnostic"] == "2"
    assert summary["closed_trades"] == 1 and summary["open_quantity"] == "0"
    assert not result["accounting_processed"] and not result["external_orders_sent"]


def test_open_position_is_valued_at_bid_and_is_not_force_closed():
    result = calculate(daily() | {"sessions": daily()["sessions"][:6]})
    assert len(result["hypothetical_fills"]) == 1
    assert result["summary"]["cash"] == "67.68"
    assert result["summary"]["final_equity"] == "75.68"
    assert result["equity_curve"][-1]["at"] == "2025-01-06T23:00:00.000Z"
    assert result["summary"]["open_quantity"] == "2" and result["summary"]["closed_trades"] == 0


def test_pending_last_signal_does_not_invent_a_future_execution():
    result = calculate(daily() | {"sessions": daily()["sessions"][:5]})
    assert result["pending_order"] == {"side": "buy", "signal_at": "2025-01-06T00:00:00.000Z"}
    assert not result["hypothetical_fills"]


def test_insufficient_cash_uses_next_ask_and_commission_without_leverage():
    result = calculate(capital="32")
    assert result["rejected_orders"][0]["reason"] == "insufficient_cash_at_next_ask_open"
    assert not result["hypothetical_fills"] and result["summary"]["cash"] == "32"
    assert result["summary"]["open_quantity"] == "0"


def test_missing_history_and_internal_gaps_never_publish_profit_metrics():
    missing = calculate(slow=60)
    assert missing["status"] == "insufficient_history" and missing["missing_sessions"] == 50
    data = daily()
    data["sessions"][3]["internal_gaps"] = [{"from": "absent", "to": "observed"}]
    gap = calculate(data)
    assert gap["status"] == "blocked_internal_gaps"
    for result in (missing, gap):
        assert result["summary"] is None and not result["hypothetical_fills"] and not result["equity_curve"]


def test_future_quotes_do_not_change_past_observations_fills_or_valuations():
    data = daily()
    prefix = calculate(data | {"sessions": data["sessions"][:7]})
    for day in data["sessions"][7:]:
        day["bid"]["open"] = "500"
        day["bid"]["close"] = "100"
        day["ask"]["open"] = "501"
    complete = calculate(data)
    assert complete["observations"][:7] == prefix["observations"]
    assert complete["equity_curve"][:7] == prefix["equity_curve"]
    assert [fill for fill in complete["hypothetical_fills"] if fill["executed_at"] <= prefix["equity_curve"][-1]["at"]] == prefix["hypothetical_fills"]


def test_arithmetic_does_not_depend_on_the_callers_decimal_context():
    expected = calculate()
    previous = getcontext().prec
    try:
        getcontext().prec = 6
        assert calculate() == expected
    finally:
        getcontext().prec = previous


@pytest.mark.parametrize("change", [{"quantity": "-1"}, {"capital": "0"}, {"commission_rate": "NaN"},
                                   {"commission_rate": "0.2"}, {"fast": True}, {"fast": 3}, {"slow": 300}])
def test_invalid_configuration_is_rejected(change):
    with pytest.raises((ValueError, TypeError)):
        calculate(**change)


def test_raw_reconstruction_and_saved_run_are_reproducible_and_do_not_create_an_account(history, tmp_path):
    data, provenance, _, _ = load_history(history)
    assert len(data["sessions"]) == 90 and provenance["originals_verified"]
    assert provenance["all_final_transports_https"] and not provenance["provider_authenticated"]
    kwargs = {"history": history, "capital": "1000", "quantity": "1", "commission_rate": "0.001"}
    first = run_backtest(output=tmp_path / "result", **kwargs)
    second = run_backtest(output=tmp_path / "replay", **kwargs)
    assert first == second and first["status"] == "simulated"
    assert (tmp_path / "result/simulation.json").read_bytes() == (tmp_path / "replay/simulation.json").read_bytes()
    assert (tmp_path / "result/input-manifest.json").read_bytes() == (history / "manifest.json").read_bytes()
    assert not (tmp_path / ".local/simulation").exists()
    with pytest.raises(ValueError, match="ya existe"):
        run_backtest(output=tmp_path / "result", **kwargs)


@pytest.mark.parametrize("changed", ["raw", "daily", "manifest_hash", "foreign_url", "duplicate_path", "transport"])
def test_changed_sources_cannot_pass_as_the_verified_originals(history, tmp_path, changed):
    manifest_path = history / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    if changed == "raw":
        path = history / "raw/2025-01-BID.bi5"
        path.write_bytes(path.read_bytes() + b"tampered")
    elif changed == "daily":
        path = history / "daily.json"
        data = json.loads(path.read_bytes())
        data["sessions"][0]["bid"]["close"] = "9"
        data["sessions_sha256"] = checksum(data["sessions"])
        manifest["sessions_sha256"] = data["sessions_sha256"]
        path.write_bytes(canonical(data))
    elif changed == "manifest_hash":
        manifest["sources"][0]["original_sha256"] = "0" * 64
    elif changed == "foreign_url":
        manifest["sources"][0]["final_url"] = "https://example.com/quotes"
    elif changed == "duplicate_path":
        manifest["sources"][1] = manifest["sources"][0]
    else:
        manifest["sources"][0]["final_transport_https"] = False
    manifest_path.write_bytes(canonical(manifest))
    with pytest.raises(ValueError):
        run_backtest(history=history, output=tmp_path / "bad", capital="1000", quantity="1", commission_rate="0")
    assert not (tmp_path / "bad").exists()


def test_cli_preserves_an_insufficient_history_report_with_no_profit_claim(history, tmp_path, capsys):
    args = ["--history", str(history), "--output", str(tmp_path / "cli"), "--commission-rate", "0"]
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "simulated"
    # Un mes completo conserva las fechas; no basta para SMA20/60.
    one = tmp_path / "one"
    prepare_history(first="2025-01", last="2025-01", cache=tmp_path / "cache", output=one,
                    now=datetime(2026, 1, 1, tzinfo=UTC), fetch=source_fetch, pause=0)
    args[1], args[3] = str(one), str(tmp_path / "short")
    assert main(args) == 2
    assert json.loads(capsys.readouterr().out)["summary"] is None
    assert json.loads((tmp_path / "short/simulation.json").read_bytes())["missing_sessions"] == 30


def test_ui_catalogue_is_readonly_and_never_starts_a_download_or_a_calculation(tmp_path, monkeypatch):
    import trading_ai.dukascopy_service as service_module
    from trading_ai.tv_service import SimulationService
    def forbidden(**kwargs):
        raise AssertionError("Una consulta no debe calcular")
    monkeypatch.setattr(service_module, "run_backtest", forbidden)
    service = SimulationService(tmp_path)
    assert service.overview()["dukascopy"]["datasets"] == []
    assert service.overview()["dukascopy"]["network_requests"] == 0
    assert not (tmp_path / ".local").exists()


def test_cli_directory_names_are_not_published_as_ui_links(history, tmp_path):
    from trading_ai.dukascopy_service import DukascopyResearch
    run_backtest(history=history, output=tmp_path / ".local/dukascopy-research/cli-output",
                 capital="1000", quantity="1", commission_rate="0")
    assert DukascopyResearch(tmp_path).overview()["runs"] == []


def test_explicit_ui_calculation_and_detail_leave_accounts_and_receipts_unchanged(history, tmp_path):
    from trading_ai.tv_service import SimulationService
    service = SimulationService(tmp_path)
    before = service.ledger.overview()
    overview = service.overview()["dukascopy"]
    assert overview["datasets"][0]["id"] == "sample"
    assert not overview["datasets"][0]["originals_verified_now"]
    result = service.action({"action": "simulate_dukascopy", "dataset": "sample", "capital": "1000",
                             "quantity": "1", "commission_rate": "0.001"})
    saved = service.get("dukascopy", result["id"])
    assert saved["status"] == "simulated" and saved["source"]["originals_verified"]
    assert service.ledger.overview() == before
    assert service.overview()["dukascopy"]["runs"][0]["id"] == result["id"]


@pytest.mark.parametrize("identity", ["../history", "C:/Users/outside", "sample/../sample", "", "x" * 129])
def test_ui_does_not_accept_paths_in_place_of_catalogue_ids(tmp_path, identity):
    from trading_ai.tv_service import SimulationService
    with pytest.raises(ValueError):
        SimulationService(tmp_path).action({"action": "simulate_dukascopy", "dataset": identity,
                                           "capital": "1000", "quantity": "1", "commission_rate": "0"})
    assert not (tmp_path / ".local").exists()


@pytest.mark.parametrize("filename", ["simulation.json", "input-manifest.json", "input-daily.json"])
def test_ui_detects_changed_saved_results_and_input_snapshots(history, tmp_path, filename):
    from trading_ai.dukascopy_service import DukascopyResearch
    service = DukascopyResearch(tmp_path)
    result = service.run(dataset="sample", capital="1000", quantity="1", commission_rate="0")
    path = tmp_path / ".local/dukascopy-research" / result["id"] / filename
    value = json.loads(path.read_bytes())
    value["tampered"] = True
    path.write_bytes(canonical(value))
    with pytest.raises(ValueError):
        service.get(result["id"])


def test_http_ui_action_saves_and_reads_a_research_result_without_an_account(history, tmp_path):
    from http.client import HTTPConnection
    import threading
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
        body = canonical({"action": "simulate_dukascopy", "dataset": "sample", "capital": "1000",
                          "quantity": "1", "commission_rate": "0"})
        headers = {"Content-Type": "application/json", "X-Tiresias-Action": overview["action_token"],
                   "Origin": f"http://127.0.0.1:{server.server_port}"}
        code, result = request("POST", "/api/simulation", body, headers)
        assert code == 202 and result["status"] == "simulated"
        code, result = request("GET", "/api/simulation/dukascopy/" + result["id"])
        assert code == 200 and not result["accounting_processed"]
        assert request("GET", "/api/simulation")[1]["accounts"] == []
        assert not (tmp_path / ".local/simulation").exists()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
