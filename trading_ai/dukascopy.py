"""Inspección local del CSV de precios Dukascopy; no crea cuentas ni operaciones."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import io
import json
from pathlib import Path
import sys

from trading_ai.data import SUPPORTED_PAIRS
from trading_ai.tv_contracts import canonical, decimal_text, instant, number


HEADER = ["Etc/UTC", "Open", "High", "Low", "Close", "Volume"]
INTERVALS = {"1Minute": 1, "1Hour": 60}
MAX_BYTES = 4 * 1024 * 1024
MAX_ROWS = 10000


def inspect_export(raw, *, pair, side, interval):
    """Identidad e intervalo son declaraciones externas: no están en el CSV."""
    if pair not in SUPPORTED_PAIRS or side not in ("BID", "ASK") or interval not in INTERVALS:
        raise ValueError("Declarar un par admitido, BID/ASK y 1Minute/1Hour.")
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("Se requiere un CSV no vacío de hasta 4 MiB.")
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        if next(reader, None) != HEADER:
            raise ValueError("Cabecera Dukascopy UTC requerida: " + ",".join(HEADER))
        duration = timedelta(minutes=INTERVALS[interval])
        bars, gaps, previous = [], [], None
        for line, row in enumerate(reader, 2):
            if len(bars) >= MAX_ROWS or len(row) != len(HEADER):
                raise ValueError(f"Fila {line}: número de columnas o límite de 10000 velas incompatible.")
            try:
                timestamp = instant(row[0])
                supplied = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
                opening = datetime.fromisoformat(timestamp)
                if supplied.utcoffset() != timedelta(0):
                    raise ValueError("La cabecera Etc/UTC exige fechas UTC.")
                if opening.second or opening.microsecond or opening.minute % INTERVALS[interval]:
                    raise ValueError(f"La apertura no está alineada con {interval}.")
                closing = opening + duration
                if previous is not None and opening < previous:
                    raise ValueError("Velas duplicadas, fuera de orden o solapadas.")
                prices = {name: number(row[i], name, positive=True)
                          for i, name in enumerate(("open", "high", "low", "close"), 1)}
                if prices["high"] < max(prices.values()) or prices["low"] > min(prices.values()):
                    raise ValueError("Precios OHLC incoherentes.")
                volume = number(row[5], "volume")
            except (ValueError, OverflowError) as error:
                raise ValueError(f"Fila {line}: {error}") from error
            if previous is not None and opening > previous:
                gaps.append({"from": instant(previous.isoformat()), "to": timestamp,
                             "missing_intervals": (opening - previous) // duration})
            bars.append({"open_at": timestamp, "close_at": instant(closing.isoformat()),
                         **{key: decimal_text(value) for key, value in prices.items()},
                         "volume": decimal_text(volume)})
            previous = closing
    except (UnicodeError, csv.Error) as error:
        raise ValueError("CSV UTF-8 inválido.") from error
    if not bars:
        raise ValueError("El CSV no contiene velas.")
    counts = Counter(bar["open_at"][:10] for bar in bars)
    expected = 1440 // INTERVALS[interval]
    return {"protocol": "tiresias_dukascopy_prices_v1", "provider": "Dukascopy",
            "pair": pair, "side": side, "interval": interval, "timezone": "Etc/UTC",
            "identity_basis": "user_declared_not_present_in_csv", "provider_authenticated": False,
            "original_sha256": sha256(raw).hexdigest(), "original_bytes": len(raw),
            "rows": len(bars), "first_open_at": bars[0]["open_at"], "last_close_at": bars[-1]["close_at"],
            "gaps": gaps, "utc_days": [{"date": day, "observed": count,
                "expected_for_24_hours": expected, "full_24_hours_observed": count == expected}
                for day, count in sorted(counts.items())],
            "last_bar_completion_verified": False, "daily_aggregation_performed": False,
            "bars": bars, "accounting_processed": False}


def compare_exports(bid, ask):
    """Empareja solo aperturas y cierres idénticos, sin remuestrear ni rellenar."""
    errors = []
    if bid["side"] != "BID" or ask["side"] != "ASK":
        errors.append("Se requieren un archivo BID y otro ASK, en ese orden.")
    if bid["pair"] != ask["pair"]:
        errors.append("Los pares declarados son distintos.")
    if bid["interval"] != ask["interval"]:
        errors.append(f"Intervalos distintos: BID {bid['interval']}; ASK {ask['interval']}.")
    keys = lambda source: {(bar["open_at"], bar["close_at"]) for bar in source["bars"]}
    bid_keys, ask_keys = keys(bid), keys(ask)
    common = bid_keys & ask_keys
    if bid_keys != ask_keys:
        errors.append("Las fechas de las velas no coinciden; no se emparejan filas por posición.")
    spread = None
    if not errors:
        asks = {bar["open_at"]: bar for bar in ask["bars"]}
        differences = []
        for bar in bid["bars"]:
            other = asks[bar["open_at"]]
            for field in ("open", "close"):
                with localcontext(Context(prec=64)):
                    difference = Decimal(other[field]) - Decimal(bar[field])
                if difference < 0:
                    errors.append(f"ASK inferior a BID en {bar['open_at']} ({field}).")
                differences.append(difference)
        if not errors:
            spread = {"basis": "open_and_close_quotes_only_not_intrabar_spread",
                      "currency_per_base_unit": bid["pair"].split("/")[1],
                      "minimum": decimal_text(min(differences)), "maximum": decimal_text(max(differences))}
    return {"protocol": "tiresias_dukascopy_pair_check_v1", "aligned": not errors, "errors": errors,
            "bid": {key: bid[key] for key in ("original_sha256", "rows", "interval", "first_open_at", "last_close_at")},
            "ask": {key: ask[key] for key in ("original_sha256", "rows", "interval", "first_open_at", "last_close_at")},
            "matching_intervals": len(common), "bid_only_intervals": len(bid_keys - ask_keys),
            "ask_only_intervals": len(ask_keys - bid_keys), "observed_quote_differences": spread,
            "accounting_processed": False}


def read_source(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("CSV mayor de 4 MiB.")
    return raw


def write_inspection(directory, raw, inspection):
    """Salida exclusiva; conserva bytes originales y su interpretación separada."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "original.csv").write_bytes(raw)
    (directory / "inspection.json").write_bytes(canonical(inspection) + b"\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspección local de precios Dukascopy; sin operaciones ni conexión de red.")
    parser.add_argument("--pair", choices=SUPPORTED_PAIRS, required=True)
    parser.add_argument("--bid", required=True)
    parser.add_argument("--bid-interval", choices=INTERVALS, required=True)
    parser.add_argument("--ask")
    parser.add_argument("--ask-interval", choices=INTERVALS)
    parser.add_argument("--output", type=Path, required=True, help="Directorio nuevo para originales e inspecciones.")
    args = parser.parse_args(argv)
    if bool(args.ask) != bool(args.ask_interval):
        parser.error("--ask y --ask-interval deben declararse juntos.")
    try:
        bid_raw = read_source(args.bid)
        bid = inspect_export(bid_raw, pair=args.pair, side="BID", interval=args.bid_interval)
        ask_raw = None if args.ask is None else read_source(args.ask)
        ask = None if ask_raw is None else inspect_export(ask_raw, pair=args.pair, side="ASK", interval=args.ask_interval)
        report = {"bid_rows": bid["rows"], "ask_rows": None if ask is None else ask["rows"],
                  "paired_quotes_ready": False, "missing_input": "ASK" if ask is None else None,
                  "accounting_processed": False}
        if ask is not None:
            report.update(compare_exports(bid, ask))
            report["paired_quotes_ready"] = report["aligned"]
        args.output.mkdir(parents=True, exist_ok=False)
        write_inspection(args.output / "bid", bid_raw, bid)
        if ask is not None:
            write_inspection(args.output / "ask", ask_raw, ask)
        (args.output / "report.json").write_bytes(canonical(report) + b"\n")
        print(json.dumps({"output": str(args.output.resolve()), **report}, ensure_ascii=False, indent=2))
        return 0 if report["paired_quotes_ready"] else 2
    except (ValueError, OSError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
