"""Histórico, recuperación y días observados; todas las peticiones son artificiales."""

import calendar
from datetime import UTC, datetime
import json
import lzma
from pathlib import Path
import struct

import pytest

import trading_ai.dukascopy_history as history
from trading_ai.tv_contracts import canonical


MONTH = datetime(2025, 1, 1, tzinfo=UTC)
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def binary(month=MONTH, *, side="BID", active=None, transform=None):
    if active is None:
        active = {22, 23, 24, 25}
    records = []
    for hour in range(calendar.monthrange(month.year, month.month)[1] * 24):
        price = 100000 + (10 if side == "ASK" else 0) + hour
        record = (hour * 3600, price, price, price, price, 1.0 if hour in active else 0.0)
        records.append(record if transform is None else transform(hour, record))
    return lzma.compress(b"".join(struct.pack(">5If", *record) for record in records), format=lzma.FORMAT_ALONE)


def fetch(url):
    side = "ASK" if "/ASK_" in url else "BID"
    return {"body": binary(side=side), "final_url": url.replace("https://www.", "http://datafeed."),
            "content_type": "application/octet-stream", "retrieved_at": "2026-01-01T00:00:00Z"}


def prepare(tmp_path, *, fetcher=fetch, offline=False, output="result"):
    return history.prepare_history(first="2025-01", last="2025-01", cache=tmp_path / "cache", output=tmp_path / output,
                                   now=NOW, fetch=fetcher, offline=offline, pause=0)


def test_decoder_preserves_observed_prices_and_accounts_for_every_raw_record():
    result = history.decode_month(binary(), MONTH, "BID")
    assert result["raw_records"] == 744
    assert result["rows"] == 4
    assert result["excluded_flat_zero_volume_records"] == 740
    assert result["complete_raw_month"]
    assert result["bars"][0]["open"] == "1.00022"
    assert result["bars"][0]["open_at"] == "2025-01-01T22:00:00.000Z"
    assert result["bars"][0]["close_at"] == "2025-01-01T23:00:00.000Z"
    assert not result["volume_units_verified"]


@pytest.mark.parametrize("body", [b"not-lzma", lzma.compress(b"invalid"), binary()[:-5], binary() + b"trailing",
                                   lzma.compress(b"x" * (history.MAX_DECODED + 1))])
def test_decoder_rejects_corruption_truncation_and_excess_data(body):
    with pytest.raises(ValueError):
        history.decode_month(body, MONTH, "BID")


@pytest.mark.parametrize("replacement", [
    (1, 100000, 100000, 100000, 100000, 1.0),
    (744 * 3600, 100000, 100000, 100000, 100000, 1.0),
    (0, 100000, 100000, 100000, 100000, float("nan")),
    (0, 100000, 100000, 100000, 100000, -1.0),
    (0, 100000, 100000, 100001, 100000, 1.0),
    (0, 0, 100000, 100000, 100000, 1.0),
])
def test_decoder_validates_timestamps_volume_and_prices(replacement):
    body = binary(transform=lambda hour, record: replacement if hour == 0 else record)
    with pytest.raises(ValueError):
        history.decode_month(body, MONTH, "BID")


def test_incomplete_raw_month_cannot_be_presented_as_complete_daily_history():
    body = lzma.decompress(binary())
    incomplete = lzma.compress(body[24:], format=lzma.FORMAT_ALONE)
    bid = history.decode_month(incomplete, MONTH, "BID")
    ask = history.decode_month(binary(side="ASK"), MONTH, "ASK")
    assert not bid["complete_raw_month"]
    assert bid["missing_raw_hours"] == 1
    with pytest.raises(ValueError, match="incompleto"):
        history.build_daily([(bid, ask)])


def test_daily_aggregation_keeps_partial_dates_and_sundays_and_observed_execution_times():
    active = {22, 23, 24, 25, 4 * 24 + 22, 4 * 24 + 23}
    bid = history.decode_month(binary(active=active), MONTH, "BID")
    ask = history.decode_month(binary(active=active, side="ASK"), MONTH, "ASK")
    daily = history.build_daily([(bid, ask)])
    assert [day["date"] for day in daily["sessions"]] == ["2025-01-01", "2025-01-02", "2025-01-05"]
    first = daily["sessions"][0]
    assert first["first_observed_open_at"] == "2025-01-01T22:00:00.000Z"
    assert first["session_start_at"] == "2025-01-01T00:00:00.000Z"
    assert first["session_close_at"] == "2025-01-02T00:00:00.000Z"
    assert first["bid"] == {"open": "1.00022", "high": "1.00023", "low": "1.00022", "close": "1.00023"}
    assert first["observed_hours"] == 2
    assert not first["full_24_hours_observed"]
    assert not daily["missing_prices_filled"]
    assert not history.signal_preview(daily)["available"]


def test_internal_gaps_remain_visible_and_prevent_signal_preview():
    bid = history.decode_month(binary(active={0, 2}), MONTH, "BID")
    ask = history.decode_month(binary(active={0, 2}, side="ASK"), MONTH, "ASK")
    daily = history.build_daily([(bid, ask)])
    assert len(daily["sessions"][0]["internal_gaps"]) == 1
    assert history.signal_preview(daily)["reason"] == "internal_hourly_gaps"


@pytest.mark.parametrize("first,last", [("2025-00", "2025-01"), ("2025-02", "2025-01"),
                                        ("2026-01", "2026-01"), ("2020-01", "2025-01"),
                                        ("2025-1", "2025-01")])
def test_only_bounded_closed_months_are_requested(first, last):
    with pytest.raises(ValueError):
        history.months_between(first, last, now=NOW)


def test_source_path_and_redirect_are_restricted_and_transport_is_not_misrepresented():
    url = history.source_url(MONTH, "BID")
    assert url.endswith("/2025/00/BID_candles_hour_1.bi5")
    history.validate_final_url(url, url.replace("https://www.", "http://datafeed."))
    history.validate_final_url(url.replace("https://www.", "http://datafeed."),
                               url.replace("https://www.", "https://datafeed."))
    for final in (url.replace("www.dukascopy.com", "example.com"), url + "?token=unknown", url.replace("EURUSD", "GBPUSD")):
        with pytest.raises(ValueError):
            history.validate_final_url(url, final)


def test_cache_is_verified_and_offline_replay_is_identical_without_network(tmp_path):
    result = prepare(tmp_path)
    assert result["network_requests"] == 2
    assert not result["all_final_transports_https"]
    assert not result["provider_authenticated"]
    assert not result["accounting_processed"]
    assert not (tmp_path / ".local").exists()
    def forbidden(_):
        raise AssertionError("No debe descargar en offline")
    replay = prepare(tmp_path, fetcher=forbidden, offline=True, output="replay")
    assert replay["network_requests"] == 0
    assert replay["sessions_sha256"] == result["sessions_sha256"]
    assert (tmp_path / "result/daily.json").read_bytes() == (tmp_path / "replay/daily.json").read_bytes()
    with pytest.raises(ValueError):
        prepare(tmp_path)


def test_corrupt_cache_is_not_silently_replaced(tmp_path):
    prepare(tmp_path)
    path = tmp_path / "cache/2025-01-BID.json"
    entry = json.loads(path.read_bytes())
    entry["original_sha256"] = "0" * 64
    path.write_bytes(canonical(entry))
    with pytest.raises(ValueError, match="huella"):
        prepare(tmp_path, output="bad")
    assert json.loads(path.read_bytes())["original_sha256"] == "0" * 64
    assert (tmp_path / "bad/failure.json").exists()


@pytest.mark.parametrize("changed", ["retrieved_at", "final_transport_https"])
def test_cache_metadata_is_validated_before_reuse(tmp_path, changed):
    prepare(tmp_path)
    path = tmp_path / "cache/2025-01-BID.json"
    entry = json.loads(path.read_bytes())
    if changed == "retrieved_at":
        del entry[changed]
    else:
        entry[changed] = True  # El archivo real procede de una URL final HTTP.
    path.write_bytes(canonical(entry))
    with pytest.raises(ValueError):
        prepare(tmp_path, output="bad_metadata")
    assert not (tmp_path / "bad_metadata/daily.json").exists()


def test_resume_uses_successful_chunk_after_an_interruption(tmp_path):
    def interrupted(url):
        if "/ASK_" in url:
            raise ValueError("Corte artificial")
        return fetch(url)
    with pytest.raises(ValueError, match="Corte"):
        prepare(tmp_path, fetcher=interrupted)
    assert not (tmp_path / "result/daily.json").exists()
    called = []
    def resumed(url):
        assert "/ASK_" in url
        called.append(url)
        return fetch(url)
    result = prepare(tmp_path, fetcher=resumed, output="resumed")
    assert len(called) == 1
    assert result["network_requests"] == 1


def test_missing_offline_cache_never_calls_fetch(tmp_path):
    def forbidden(_):
        raise AssertionError("No debe descargar en offline")
    with pytest.raises(ValueError, match="Falta caché"):
        prepare(tmp_path, fetcher=forbidden, offline=True)


def test_incomplete_download_does_not_poison_the_cache(tmp_path):
    def incomplete(url):
        response = fetch(url)
        response["body"] = lzma.compress(lzma.decompress(response["body"])[24:], format=lzma.FORMAT_ALONE)
        return response
    with pytest.raises(ValueError, match="todas las horas"):
        prepare(tmp_path, fetcher=incomplete)
    assert not (tmp_path / "cache/2025-01-BID.json").exists()
    assert not (tmp_path / "result/daily.json").exists()


@pytest.mark.parametrize("status,content_type,final", [
    (202, "text/html", "https://www.dukascopy.com"),
    (200, "text/html", "https://www.dukascopy.com"),
    (200, "application/octet-stream", "https://example.com"),
])
def test_http_response_must_be_a_real_binary_download(monkeypatch, status, content_type, final):
    class Response:
        headers = {"Content-Type": content_type}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def geturl(self): return history.source_url(MONTH, "BID").replace("https://www.dukascopy.com", final)
        def read(self, limit): return binary()
    Response.status = status
    class Opener:
        def open(self, *args, **kwargs): return Response()
    monkeypatch.setattr(history, "build_opener", lambda *args: Opener())
    with pytest.raises(ValueError):
        history.fetch_public(history.source_url(MONTH, "BID"))


def test_signal_warmup_and_past_values_do_not_depend_on_future_prices():
    from datetime import timedelta
    days = [{"session_close_at": (MONTH + timedelta(days=i + 1)).isoformat(),
             "bid": {"close": str(200 - i)}, "internal_gaps": []} for i in range(80)]
    short = history.signal_preview({"sessions": days[:60]})
    complete = history.signal_preview({"sessions": days})
    assert not short["available"]
    assert complete["available"]
    assert short["signals"] == complete["signals"][:60]
    assert not complete["executed_orders"]
    assert not complete["accounting_processed"]


def test_rate_limit_is_reported_without_retrying_or_promoting_an_empty_dataset(tmp_path, monkeypatch):
    from email.message import Message
    from urllib.error import HTTPError
    headers = Message()
    headers["Retry-After"] = "120"
    calls = []
    class Opener:
        def open(self, url, **kwargs):
            calls.append(url)
            raise HTTPError(url, 429, "Too Many Requests", headers, None)
    monkeypatch.setattr(history, "build_opener", lambda *args: Opener())
    with pytest.raises(history.DownloadUnavailable):
        prepare(tmp_path, fetcher=history.fetch_public)
    assert len(calls) == 1
    failure = json.loads((tmp_path / "result/failure.json").read_bytes())
    assert failure["http_status"] == 429 and failure["retry_after"] == "120"
    assert not (tmp_path / "result/manifest.json").exists()
    assert not (tmp_path / "result/daily.json").exists()
