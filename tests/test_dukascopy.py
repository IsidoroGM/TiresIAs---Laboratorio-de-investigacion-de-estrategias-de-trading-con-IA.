"""Precios, metadatos y emparejado: no se inventan velas ni ejecuciones."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest

from trading_ai.dukascopy import HEADER, compare_exports, inspect_export, main


def source(rows, *, bom=False):
    raw = (",".join(HEADER) + "\r\n" + "\r\n".join(rows) + "\r\n").encode()
    return (b"\xef\xbb\xbf" if bom else b"") + raw


def read(raw, side="BID", interval="1Hour"):
    return inspect_export(raw, pair="EUR/USD", side=side, interval=interval)


def test_preserves_exact_source_identity_and_reports_gaps_and_partial_days():
    raw = source(["2025-01-01T22:00:00+00:00,1.10,1.2,1.0,1.15,0",
                  "2025-01-02T00:00:00+00:00,1.15,1.3,1.1,1.20,100"], bom=True)
    result = read(raw)
    assert result["original_sha256"] == sha256(raw).hexdigest()
    assert result["rows"] == 2
    assert result["bars"][0]["close_at"] == "2025-01-01T23:00:00.000Z"
    assert result["bars"][0]["volume"] == "0"
    assert result["gaps"][0]["missing_intervals"] == 1
    assert not result["utc_days"][0]["full_24_hours_observed"]
    assert result["identity_basis"] == "user_declared_not_present_in_csv"
    assert not result["provider_authenticated"]
    assert not result["daily_aggregation_performed"]
    assert not result["accounting_processed"]


@pytest.mark.parametrize("row", [
    "2025-01-01T22:01:00+00:00,1,1,1,1,1",
    "2025-01-01T22:00:00+01:00,1,1,1,1,1",
    "2025-01-01T22:00:00,1,1,1,1,1",
    "2025-01-01T22:00:00+00:00,1,0.9,1,1,1",
    "2025-01-01T22:00:00+00:00,NaN,1,1,1,1",
    "2025-01-01T22:00:00+00:00,0,1,1,1,1",
    "2025-01-01T22:00:00+00:00,1,1,1,1,-1",
    "2025-01-01T22:00:00+00:00,1,1,1,1,1,extra",
    "2025-01-01T22:00:00+00:00,1,1,1,1",
])
def test_rejects_incompatible_or_malformed_rows(row):
    with pytest.raises(ValueError, match="Fila"):
        read(source([row]))


def test_rejects_empty_files_unknown_headers_duplicates_and_reordering():
    row = "2025-01-01T22:00:00+00:00,1,1,1,1,1"
    for raw in (b"", source([]), source([row]).replace(b"Etc/UTC", b"Local time"),
                source([row, row]), source([row, row.replace("22:00", "21:00")])):
        with pytest.raises(ValueError):
            read(raw)


def test_pair_rejects_different_dates_and_intervals_without_calculating_spread():
    bid = read(source(["2025-01-01T22:00:00+00:00,1,1,1,1,1"]))
    ask = read(source(["2026-10-22T00:00:00+00:00,2,2,2,2,1"]), "ASK", "1Minute")
    report = compare_exports(bid, ask)
    assert not report["aligned"]
    assert len(report["errors"]) == 2
    assert report["matching_intervals"] == 0
    assert report["observed_quote_differences"] is None


def test_pair_joins_by_timestamp_and_exposes_crossed_prices():
    bid = read(source(["2025-01-01T22:00:00+00:00,1.1,1.2,1,1.15,1"]))
    ask = read(source(["2025-01-01T22:00:00+00:00,1.11,1.21,1.01,1.16,1"]), "ASK")
    report = compare_exports(bid, ask)
    assert report["aligned"]
    assert report["observed_quote_differences"]["minimum"] == "0.01"
    bad = deepcopy(ask)
    bad["bars"][0]["close"] = "1.14"
    assert not compare_exports(bid, bad)["aligned"]
    assert compare_exports(bid, bad)["observed_quote_differences"] is None


def test_cli_conserves_originals_even_for_mismatched_pair_and_never_overwrites(tmp_path, capsys):
    bid_raw = source(["2025-01-01T22:00:00+00:00,1,1,1,1,1"], bom=True)
    ask_raw = source(["2026-10-22T00:00:00+00:00,2,2,2,2,1"])
    bid, ask, output = tmp_path / "bid.csv", tmp_path / "ask.csv", tmp_path / "inspection"
    bid.write_bytes(bid_raw)
    ask.write_bytes(ask_raw)
    args = ["--pair", "EUR/USD", "--bid", str(bid), "--bid-interval", "1Hour",
            "--ask", str(ask), "--ask-interval", "1Minute", "--output", str(output)]
    assert main(args) == 2
    assert json.loads(capsys.readouterr().out)["matching_intervals"] == 0
    assert (output / "bid/original.csv").read_bytes() == bid_raw
    assert (output / "ask/original.csv").read_bytes() == ask_raw
    assert main(args) == 2
    assert "Error:" in capsys.readouterr().err
    assert not (tmp_path / ".local").exists()


def test_bid_only_is_pending_and_invalid_input_writes_no_output(tmp_path, capsys):
    path, output = tmp_path / "bid.csv", tmp_path / "inspection"
    path.write_bytes(source(["2025-01-01T22:00:00+00:00,1,1,1,1,1"]))
    args = ["--pair", "EUR/USD", "--bid", str(path), "--bid-interval", "1Hour", "--output", str(output)]
    assert main(args) == 2
    assert json.loads(capsys.readouterr().out)["missing_input"] == "ASK"
    path.write_text("unexpected", encoding="utf-8")
    args[-1] = str(tmp_path / "invalid")
    assert main(args) == 2
    assert not (tmp_path / "invalid").exists()


def test_complete_utc_day_is_observed_without_aggregating_or_creating_trades():
    raw = source([f"2025-01-02T{hour:02d}:00:00+00:00,1,1,1,1,0" for hour in range(24)])
    result = read(raw)
    assert result["utc_days"] == [{"date": "2025-01-02", "observed": 24,
                                   "expected_for_24_hours": 24, "full_24_hours_observed": True}]
    assert len(result["bars"]) == 24
    assert not result["gaps"]
    assert "fills" not in result


@pytest.mark.parametrize("metadata", [
    {"pair": "EUR/USD", "side": "MID", "interval": "1Hour"},
    {"pair": "EUR/USD", "side": "BID", "interval": "1Day"},
    {"pair": "UNSUPPORTED", "side": "BID", "interval": "1Hour"},
])
def test_identity_must_be_explicit_and_supported(metadata):
    with pytest.raises(ValueError):
        inspect_export(source(["2025-01-01T22:00:00+00:00,1,1,1,1,1"]), **metadata)


def test_limits_reject_oversized_input_and_excess_rows(monkeypatch):
    import trading_ai.dukascopy as dukascopy

    raw = source(["2025-01-01T22:00:00+00:00,1,1,1,1,1", "2025-01-01T23:00:00+00:00,1,1,1,1,1"])
    monkeypatch.setattr(dukascopy, "MAX_ROWS", 1)
    with pytest.raises(ValueError):
        read(raw)
    monkeypatch.setattr(dukascopy, "MAX_BYTES", len(raw) - 1)
    with pytest.raises(ValueError):
        read(raw)


def test_cli_aligned_pair_is_ready_for_inspection_only(tmp_path, capsys):
    bid, ask, output = tmp_path / "bid.csv", tmp_path / "ask.csv", tmp_path / "inspection"
    bid.write_bytes(source(["2025-01-01T22:00:00+00:00,1,1,1,1,1"]))
    ask.write_bytes(source(["2025-01-01T22:00:00+00:00,1.01,1.01,1.01,1.01,1"]))
    args = ["--pair", "EUR/USD", "--bid", str(bid), "--bid-interval", "1Hour",
            "--ask", str(ask), "--ask-interval", "1Hour", "--output", str(output)]
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["paired_quotes_ready"]
    assert result["matching_intervals"] == 1
    assert not result["accounting_processed"]
    assert not (tmp_path / ".local").exists()
