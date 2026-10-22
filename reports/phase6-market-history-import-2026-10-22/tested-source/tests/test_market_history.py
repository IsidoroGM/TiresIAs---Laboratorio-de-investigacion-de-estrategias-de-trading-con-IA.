"""Entradas artificiales, originales verificables y carga explícita sin red."""

import base64
from datetime import UTC, datetime, timedelta
import gzip
from http.client import HTTPConnection
import json
import threading

import pytest

from trading_ai.dukascopy_backtest import load_history, run_backtest, simulate
from trading_ai.market_history import CSV_FORMAT, EV_FORMAT, decode_ev, load_prepared, prepare, selection
from trading_ai.tv_contracts import canonical
from trading_ai.tv_service import SimulationService


def rows(count=90):
    first = datetime(2025, 1, 1, 22, tzinfo=UTC)
    return [{"ts": int((first + timedelta(days=index)).timestamp()),
             "o": 1, "h": 2, "l": 1, "c": 1.5, "ao": 1.1, "ah": 2.1, "al": 1.1, "ac": 1.6, "v": 0}
            for index in range(count)]


def packed(values=None):
    return gzip.compress(json.dumps(rows() if values is None else values, separators=(",", ":")).encode(), mtime=0)


def inputs(raw=None):
    return [{"name": "2025.json.gz", "side": "BOTH", "body": packed() if raw is None else raw}]


def prepare_ev(tmp_path, **kwargs):
    return prepare(**{"inputs": inputs(), "source_format": EV_FORMAT, "year": 2025, "start_date": "2025-01-01",
                      "end_date": "2025-04-01", "output": tmp_path / "dataset", **kwargs})


def csv_bytes(side="BID", opening="2025-01-01T22:00:00+00:00"):
    price = "1" if side == "BID" else "1.01"
    return f"Etc/UTC,Open,High,Low,Close,Volume\n{opening},{price},{price},{price},{price},0\n".encode()


def csv_inputs():
    return [{"name": side.lower() + ".csv", "side": side, "body": csv_bytes(side)} for side in ("BID", "ASK")]


def test_ev_preserves_decimal_prices_and_flat_zero_volume_rows_without_claiming_a_broker_identity(tmp_path):
    value = rows(1)
    value[0].update(o=1, h=1, l=1, c=1, ao=1.1, ah=1.1, al=1.1, ac=1.1)
    raw = packed(value)
    result = prepare_ev(tmp_path, inputs=inputs(raw))
    assert result["selected_hours"] == 1 and result["daily_sessions"] == 1
    daily, provenance, _, _ = load_history(tmp_path / "dataset")
    assert daily["sessions"][0]["ask"]["open"] == "1.1"
    assert provenance["provider"] == "EV Trading Labs" and provenance["attribution"]
    assert provenance["all_final_transports_https"] is None and not provenance["provider_authenticated"]
    assert not daily["missing_prices_filled"] and not daily["market_calendar_verified"]


@pytest.mark.parametrize("change", [
    lambda r: r[0].update(ts=r[0]["ts"] + 60),
    lambda r: r[0].update(ts=True),
    lambda r: r[0].update(ts=-1),
    lambda r: r[0].update(o=0),
    lambda r: r[0].update(h=0.5),
    lambda r: r[0].update(ao=0.9),
    lambda r: r[0].update(ac=1.4),
    lambda r: r[0].update(v=-1),
    lambda r: r[0].update(v=True),
    lambda r: r[0].update(o="1"),
    lambda r: r[0].pop("ac"),
    lambda r: r[0].update(extra=1),
    lambda r: r.append(r[0]),
])
def test_ev_rejects_wrong_grid_year_prices_volume_schema_and_order(change):
    values = rows(1)
    change(values)
    with pytest.raises(ValueError):
        decode_ev(packed(values), 2025)


@pytest.mark.parametrize("raw", [b"not-gzip", packed()[:-5], gzip.compress(b"{}"),
                                 gzip.compress(b'[{"ts":1,"ts":2}]'), gzip.compress(b"[NaN]"),
                                 packed(rows(1)) + b"trailing"])
def test_ev_rejects_corruption_invalid_json_and_duplicate_keys(raw):
    with pytest.raises(ValueError):
        decode_ev(raw, 2025)


def test_extreme_numeric_exponents_are_rejected_before_expanding_a_decimal():
    encoded = json.dumps(rows(1)).replace('"o": 1,', '"o": 1e999999999,').encode()
    with pytest.raises(ValueError):
        decode_ev(gzip.compress(encoded), 2025)


def test_gzip_expansion_is_bounded(monkeypatch):
    import trading_ai.market_history as history
    monkeypatch.setattr(history, "MAX_INPUT", 128)
    with pytest.raises(ValueError, match="descomprimido"):
        decode_ev(gzip.compress(b" " * 1024), 2025)


@pytest.mark.parametrize("start,end", [("2025-1-1", "2025-02-01"), ("2025-02-01", "2025-01-01"),
                                      ("2025-01-01", "2099-01-01"), ("2000-01-01", "2025-01-01")])
def test_period_is_explicit_closed_and_bounded(start, end):
    with pytest.raises(ValueError):
        selection(start, end)


def test_csv_originals_and_multiple_blocks_are_preserved_and_never_overwritten(tmp_path):
    original = csv_inputs()
    result = prepare(inputs=original, source_format=CSV_FORMAT, year=None, start_date="2025-01-01",
                     end_date="2025-02-01", output=tmp_path / "dataset")
    assert result["provider"] == "Dukascopy" and result["daily_sessions"] == 1
    assert (tmp_path / "dataset/raw/00.csv").read_bytes() == original[0]["body"]
    assert load_prepared(tmp_path / "dataset")[0]["sessions"][0]["observed_hours"] == 1
    with pytest.raises(ValueError, match="ya existe"):
        prepare_ev(tmp_path)


def test_csv_mismatch_duplicates_and_missing_partners_do_not_create_output(tmp_path):
    original = csv_inputs()
    for index, values in enumerate((original[:1], original * 2,
                                   [original[0], {**original[1], "body": csv_bytes("ASK", "2025-02-01T22:00:00+00:00")}])):
        output = tmp_path / f"bad{index}"
        with pytest.raises(ValueError):
            prepare(inputs=values, source_format=CSV_FORMAT, year=None, start_date="2025-01-01",
                    end_date="2025-03-01", output=output)
        assert not output.exists()


def test_selection_keeps_full_original_and_does_not_use_excluded_future_prices(tmp_path):
    original = rows()
    config = {"source_format": EV_FORMAT, "year": 2025, "start_date": "2025-01-01", "end_date": "2025-03-15"}
    first = prepare(inputs=inputs(packed(original)), output=tmp_path / "first", **config)
    for row in original[73:]:
        row.update(o=10, h=11, l=9, c=10, ao=10.1, ah=11.1, al=9.1, ac=10.1)
    second = prepare(inputs=inputs(packed(original)), output=tmp_path / "second", **config)
    assert first["total_source_hours"] == 90 and first["excluded_hours_outside_period"] == 17
    assert first["sessions_sha256"] == second["sessions_sha256"]
    kwargs = {"capital": "1000", "quantity": "1", "commission_rate": "0.001"}
    assert simulate(load_history(tmp_path / "first")[0], **kwargs) == simulate(load_history(tmp_path / "second")[0], **kwargs)


def test_gaps_are_exposed_and_block_metrics_instead_of_being_filled(tmp_path):
    values = rows()
    # Dos observaciones dentro del primer día, separadas por una hora ausente.
    extra = {**values[0], "ts": values[0]["ts"] - 2 * 3600}
    prepare_ev(tmp_path, inputs=inputs(packed([extra, *values])))
    data = load_history(tmp_path / "dataset")[0]
    assert len(data["sessions"][0]["internal_gaps"]) == 1
    assert simulate(data, capital="1000", quantity="1", commission_rate="0")["status"] == "blocked_internal_gaps"
    long = rows()
    del long[20:30]
    prepare_ev(tmp_path, inputs=inputs(packed(long)), output=tmp_path / "long")
    data = load_history(tmp_path / "long")[0]
    result = simulate(data, capital="1000", quantity="1", commission_rate="0")
    assert result["status"] == "blocked_coverage_gaps" and result["summary"] is None


def test_missing_requested_period_boundaries_are_visible_and_block_metrics(tmp_path):
    prepare_ev(tmp_path, end_date="2026-01-01")
    daily = load_history(tmp_path / "dataset")[0]
    assert daily["blocking_gaps"][-1]["to"] == "2026-01-01T00:00:00.000Z"
    assert simulate(daily, capital="1000", quantity="1", commission_rate="0")["summary"] is None


@pytest.mark.parametrize("change", ["raw", "daily", "manifest", "path"])
def test_loader_rebuilds_from_originals_and_rejects_tampering(tmp_path, change):
    prepare_ev(tmp_path)
    directory = tmp_path / "dataset"
    if change == "raw":
        path = directory / "raw/00.json.gz"
        path.write_bytes(path.read_bytes() + b"changed")
    else:
        path = directory / ("daily.json" if change == "daily" else "manifest.json")
        value = json.loads(path.read_bytes())
        if change == "path":
            value["sources"][0]["file"] = "../outside.json.gz"
        else:
            value["modified"] = True
        path.write_bytes(canonical(value))
    with pytest.raises(ValueError):
        run_backtest(history=directory, output=tmp_path / "result", capital="1000", quantity="1", commission_rate="0")
    assert not (tmp_path / "result").exists()


def request_body(raw=None):
    return {"action": "import_price_history", "format": EV_FORMAT, "year": 2025,
            "start_date": "2025-01-01", "end_date": "2025-04-01",
            "files": [{"name": "annual.json.gz", "side": "BOTH", "content_base64": base64.b64encode(packed() if raw is None else raw).decode()}]}


def test_service_import_is_explicit_catalogued_and_does_not_process_an_account(tmp_path):
    service = SimulationService(tmp_path)
    before = service.ledger.overview()
    result = service.action(request_body())
    assert service.overview()["dukascopy"]["datasets"][0]["provider"] == "EV Trading Labs"
    detail = service.get("price-histories", result["id"])
    assert detail["daily_sessions"] == 90 and detail["source"]["originals_verified"]
    assert not detail["internal_gaps"] and not detail["coverage_gaps"]
    assert service.ledger.overview() == before and not (tmp_path / ".local/simulation").exists()


@pytest.mark.parametrize("change", ["encoding", "filename", "size"])
def test_service_rejects_invalid_files_before_creating_storage(tmp_path, change):
    body = request_body()
    if change == "encoding":
        body["files"][0]["content_base64"] = "???"
    elif change == "filename":
        body["files"][0]["name"] = "../outside"
    else:
        body["files"] = [dict(body["files"][0], content_base64=base64.b64encode(b"x" * 1100000).decode())] * 2
    with pytest.raises(ValueError):
        SimulationService(tmp_path).action(body)
    assert not (tmp_path / ".local").exists()


def test_http_import_requires_the_existing_origin_and_token_and_returns_a_verifiable_dataset(tmp_path):
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
        body = canonical(request_body())
        assert request("POST", "/api/simulation", body, {"Content-Type": "application/json"})[0] == 403
        headers = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{server.server_port}",
                   "X-Tiresias-Action": overview["action_token"]}
        code, result = request("POST", "/api/simulation", body, headers)
        assert code == 202
        code, detail = request("GET", "/api/simulation/price-histories/" + result["id"])
        assert code == 200 and detail["daily_sessions"] == 90 and not detail["accounting_processed"]
        assert request("GET", "/api/simulation")[1]["accounts"] == []
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
