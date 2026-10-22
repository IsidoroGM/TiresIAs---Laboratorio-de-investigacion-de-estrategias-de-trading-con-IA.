"""Fixed configuration, independent periods and stored evidence; artificial prices only."""

from datetime import UTC, datetime, timedelta
import gzip
from http.client import HTTPConnection
import json
import threading

import pytest

from trading_ai.dukascopy_backtest import run_backtest
from trading_ai.market_comparison import create_comparison, load_comparison
from trading_ai.market_history import EV_FORMAT, prepare
from trading_ai.tv_contracts import canonical, checksum
from trading_ai.tv_service import SimulationService


def make_run(root, year, identity, *, days=90, gap=False):
    rows = []
    start = datetime(year, 1, 1, tzinfo=UTC)
    for index in range(days):
        price = 1 + ((index % 30) - 15) ** 2 / 10000
        rows.append({"ts": int((start + timedelta(days=index)).timestamp()),
                     **{key: price for key in ("o", "h", "l", "c")},
                     **{key: price + 0.0001 for key in ("ao", "ah", "al", "ac")}, "v": 1})
    if gap:
        rows.insert(1, {**rows[0], "ts": rows[0]["ts"] + 7200})
    history = root / ".local/dukascopy" / str(year)
    prepare(inputs=[{"name": f"{year}.json.gz", "side": "BOTH", "body": gzip.compress(canonical(rows))}],
            source_format=EV_FORMAT, year=year, start_date=f"{year}-01-01",
            end_date=(start + timedelta(days=days)).date().isoformat(), output=history)
    directory = root / ".local/dukascopy-research" / identity
    run_backtest(history=history, output=directory, capital="1000", quantity="1", commission_rate="0.001")
    return directory


@pytest.fixture
def runs(tmp_path):
    return make_run(tmp_path, 2023, "a" * 32), make_run(tmp_path, 2024, "b" * 32)


def rewrite_result(directory, change):
    path = directory / "simulation.json"
    value = json.loads(path.read_bytes())
    change(value)
    value["result_sha256"] = checksum({key: item for key, item in value.items() if key != "result_sha256"})
    path.write_bytes(canonical(value))


def rewrite_input(directory, filename, change):
    path = directory / filename
    value = json.loads(path.read_bytes())
    change(value)
    raw = canonical(value)
    path.write_bytes(raw)
    from hashlib import sha256
    key = "manifest_sha256" if filename == "input-manifest.json" else "daily_file_sha256"
    rewrite_result(directory, lambda result: result["source"].update({key: sha256(raw).hexdigest()}))


def test_comparison_orders_periods_and_preserves_independent_initial_capital(tmp_path, runs):
    left, right = runs
    result = create_comparison(left=right, right=left, output=tmp_path / "comparison")
    assert result["status"] == "compared"
    assert [p["start_date"] for p in result["periods"]] == ["2023-01-01", "2024-01-01"]
    assert result["configuration"]["initial_capital"] == "1000"
    assert result["independent_periods"] and not result["balances_combined"]
    assert not result["prospective_validation"] and not result["parameter_selection"]
    assert load_comparison(tmp_path / "comparison") == result
    for source, period in zip((left, right), result["periods"], strict=True):
        saved = json.loads((source / "simulation.json").read_bytes())
        assert period["summary"] == saved["summary"]
        assert period["hypothetical_fills"] == len(saved["hypothetical_fills"])
    with pytest.raises(ValueError, match="ya existe"):
        create_comparison(left=left, right=right, output=tmp_path / "comparison")


@pytest.mark.parametrize("key,value", [("fast", 10), ("initial_capital", "2000"),
                                      ("quantity", "2"), ("assumed_commission_rate", "0")])
def test_different_strategy_or_costs_rejected_before_output(tmp_path, runs, key, value):
    rewrite_result(runs[1], lambda result: result["configuration"].update({key: value}))
    with pytest.raises(ValueError, match="misma estrategia"):
        create_comparison(left=runs[0], right=runs[1], output=tmp_path / "comparison")
    assert not (tmp_path / "comparison").exists()


def test_engine_change_and_overlapping_periods_are_rejected(tmp_path, runs):
    with pytest.raises(ValueError, match="no solaparse"):
        create_comparison(left=runs[0], right=runs[0], output=tmp_path / "same")
    rewrite_result(runs[1], lambda result: result["implementation_sha256"].update({"strategies.py": "0" * 64}))
    with pytest.raises(ValueError, match="versiones distintas"):
        create_comparison(left=runs[0], right=runs[1], output=tmp_path / "engine")
    assert not (tmp_path / "same").exists() and not (tmp_path / "engine").exists()


def test_different_provider_and_session_policy_are_rejected(tmp_path, runs):
    rewrite_input(runs[1], "input-manifest.json", lambda value: value.update(provider="Other"))
    rewrite_result(runs[1], lambda result: result["source"].update(provider="Other"))
    with pytest.raises(ValueError, match="procedencia declarada"):
        create_comparison(left=runs[0], right=runs[1], output=tmp_path / "provider")
    rewrite_input(runs[1], "input-manifest.json", lambda value: value.update(provider="EV Trading Labs"))
    rewrite_result(runs[1], lambda result: result["source"].update(provider="EV Trading Labs"))
    rewrite_input(runs[1], "input-daily.json", lambda value: value.update(session_policy="other"))
    with pytest.raises(ValueError, match="sesión son distintas"):
        create_comparison(left=runs[0], right=runs[1], output=tmp_path / "session")


def test_cannot_publish_simulated_metrics_when_copied_quality_is_blocked(tmp_path, runs):
    rewrite_input(runs[1], "input-daily.json", lambda value: value.update(blocking_gaps=[{"from": "missing", "to": "observed"}]))
    with pytest.raises(ValueError, match="Estado o métricas"):
        create_comparison(left=runs[0], right=runs[1], output=tmp_path / "comparison")
    assert not (tmp_path / "comparison").exists()


@pytest.mark.parametrize("state", ["gap", "insufficient"])
def test_blocked_periods_remain_visible_without_metrics(tmp_path, state):
    left = make_run(tmp_path, 2023, "a" * 32)
    right = make_run(tmp_path, 2024, "b" * 32, days=10 if state == "insufficient" else 90, gap=state == "gap")
    result = create_comparison(left=left, right=right, output=tmp_path / "comparison")
    assert result["status"] == "incomplete"
    assert result["periods"][0]["summary"] is not None
    assert result["periods"][1]["summary"] is None and result["periods"][1]["hypothetical_fills"] == 0


@pytest.mark.parametrize("filename", ["simulation.json", "input-manifest.json", "input-daily.json"])
def test_modified_source_run_is_rejected(tmp_path, runs, filename):
    path = runs[0] / filename
    path.write_bytes(path.read_bytes() + b" ")
    if filename == "simulation.json":
        value = json.loads(path.read_bytes())
        value["summary"]["cash"] = "9000"
        path.write_bytes(canonical(value))
    with pytest.raises(ValueError):
        create_comparison(left=runs[0], right=runs[1], output=tmp_path / "comparison")
    assert not (tmp_path / "comparison").exists()


@pytest.mark.parametrize("filename", ["comparison.json", "run-0-simulation.json", "run-1-input-manifest.json", "run-1-input-daily.json"])
def test_modified_comparison_or_copied_inputs_are_rejected(tmp_path, runs, filename):
    directory = tmp_path / "comparison"
    create_comparison(left=runs[0], right=runs[1], output=directory)
    path = directory / filename
    value = json.loads(path.read_bytes())
    value["changed"] = True
    path.write_bytes(canonical(value))
    with pytest.raises(ValueError):
        load_comparison(directory)


def test_malformed_result_fails_with_validation_error(tmp_path, runs):
    rewrite_result(runs[0], lambda result: result.update(source=[]))
    with pytest.raises(ValueError, match="Estructura"):
        create_comparison(left=runs[0], right=runs[1], output=tmp_path / "comparison")


def test_service_queries_and_comparison_never_run_strategy_or_process_accounts(tmp_path, runs, monkeypatch):
    service = SimulationService(tmp_path)
    before = service.ledger.overview()
    def forbidden(*args, **kwargs):
        raise AssertionError("No strategy or account processing allowed")
    monkeypatch.setattr("trading_ai.dukascopy_service.run_backtest", forbidden)
    monkeypatch.setattr("trading_ai.dukascopy_backtest.simulate", forbidden)
    monkeypatch.setattr(service.ledger, "process", forbidden)
    result = service.action({"action": "compare_price_periods", "left": runs[0].name, "right": runs[1].name})
    detail = service.get("market-comparisons", result["id"])
    assert detail["status"] == "compared" and not detail["accounting_processed"]
    monkeypatch.setattr("trading_ai.dukascopy_service.load_comparison", forbidden)
    overview = service.overview()["dukascopy"]
    assert overview["comparisons"][0]["inputs_verified_now"] is False
    assert service.ledger.overview() == before


@pytest.mark.parametrize("identity", ["../outside", "..", "c" * 64, None])
def test_service_rejects_paths_before_creating_comparison(tmp_path, identity):
    service = SimulationService(tmp_path)
    with pytest.raises(ValueError):
        service.action({"action": "compare_price_periods", "left": identity, "right": "b" * 32})
    assert not (tmp_path / ".local").exists()


def test_http_comparison_uses_existing_origin_token_and_read_only_detail(tmp_path, runs):
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
        body = canonical({"action": "compare_price_periods", "left": runs[0].name, "right": runs[1].name})
        assert request("POST", "/api/simulation", body, {"Content-Type": "application/json"})[0] == 403
        headers = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{server.server_port}",
                   "X-Tiresias-Action": overview["action_token"]}
        assert request("POST", "/api/simulation", body, {**headers, "X-Tiresias-Action": "wrong"})[0] == 403
        code, result = request("POST", "/api/simulation", body, headers)
        assert code == 202
        code, detail = request("GET", "/api/simulation/market-comparisons/" + result["id"])
        assert code == 200 and detail["status"] == "compared"
        assert request("GET", "/api/simulation")[1]["accounts"] == overview["accounts"]
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
