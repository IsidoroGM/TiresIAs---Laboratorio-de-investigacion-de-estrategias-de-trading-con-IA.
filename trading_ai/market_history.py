"""Históricos H1 aportados: CSV Dukascopy y JSON anual EV Trading Labs. Sin red."""

import argparse
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import sys

from trading_ai.dukascopy import compare_exports, inspect_export
from trading_ai.dukascopy_history import save_json
from trading_ai.tv_contracts import canonical, checksum, decimal_text, fields, instant, number, safe_under, strict_json


PROFILE = "tiresias_supplied_hourly_bidask_history_v1"
CSV_FORMAT = "dukascopy_csv"
EV_FORMAT = "evtradelabs_h1_json_gzip"
MAX_INPUT = 4 * 1024 * 1024
MAX_GZIP = 1024 * 1024
MAX_HOURS = 26784
EV_COLUMNS = ("ts", "o", "h", "l", "c", "ao", "ah", "al", "ac", "v")


def read_file(path, maximum=MAX_INPUT):
    with Path(path).open("rb") as stream:
        raw = stream.read(maximum + 1)
    if not raw or len(raw) > maximum:
        raise ValueError("Archivo vacío o excesivo: " + Path(path).name)
    return raw


def filename(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 200 or Path(value).name != value
            or value in (".", "..") or any(ord(char) < 32 for char in value)):
        raise ValueError("Nombre original inválido; no se admiten rutas.")
    return value


def selection(start, end):
    values = []
    for value in (start, end):
        if not isinstance(value, str) or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", value):
            raise ValueError("Fechas UTC requeridas: YYYY-MM-DD.")
        values.append(datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC))
    first, last = values
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    if not first < last <= today or last - first > timedelta(days=1098):
        raise ValueError("El período debe estar cerrado, ordenado y no superar tres años; fin exclusivo.")
    return instant(first.isoformat()), instant(last.isoformat())


def decode_ev(raw, year):
    if type(year) is not int or not 2000 <= year < datetime.now(UTC).year:
        raise ValueError("Declarar un año completo cerrado entre 2000 y el año anterior.")
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_GZIP:
        raise ValueError("JSON gzip anual requerido, máximo 1 MiB comprimido.")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            decoded = stream.read(MAX_INPUT + 1)
    except (OSError, EOFError) as error:
        raise ValueError("Gzip inválido o truncado.") from error
    if len(decoded) > MAX_INPUT:
        raise ValueError("JSON descomprimido mayor de 4 MiB.")
    strict_json(decoded)  # Rechaza claves duplicadas, profundidad excesiva y NaN.
    rows = json.loads(decoded.decode("utf-8-sig"), parse_float=Decimal)
    if not isinstance(rows, list) or not 1 <= len(rows) <= 8784:
        raise ValueError("Se requiere una lista anual H1 no vacía y acotada.")
    pairs, previous = [], None
    for row in rows:
        fields(row, EV_COLUMNS, "vela H1 anual")
        if type(row["ts"]) is not int or row["ts"] % 3600:
            raise ValueError("Timestamp entero de apertura horaria requerido.")
        try:
            opening = datetime.fromtimestamp(row["ts"], UTC)
        except (ValueError, OSError, OverflowError) as error:
            raise ValueError("Timestamp fuera de límites.") from error
        if opening.year != year or previous is not None and row["ts"] <= previous:
            raise ValueError("Velas fuera del año declarado, duplicadas o desordenadas.")
        previous = row["ts"]
        sides = {}
        for side, prefix in (("bid", ""), ("ask", "a")):
            prices = {}
            for key, short in (("open", "o"), ("high", "h"), ("low", "l"), ("close", "c")):
                value = row[prefix + short]
                if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
                    raise ValueError("Precio JSON numérico requerido.")
                prices[key] = number(str(value), key, positive=True)
            if prices["high"] < max(prices.values()) or prices["low"] > min(prices.values()):
                raise ValueError("OHLC anual incompatible.")
            sides[side] = {key: decimal_text(value) for key, value in prices.items()}
        if any(Decimal(sides["ask"][key]) < Decimal(sides["bid"][key]) for key in ("open", "close")):
            raise ValueError("ASK inferior al BID en apertura o cierre.")
        if isinstance(row["v"], bool) or not isinstance(row["v"], (int, Decimal)):
            raise ValueError("Volumen JSON numérico requerido.")
        number(str(row["v"]), "volumen")
        pairs.append({"open_at": instant(opening.isoformat()),
                      "close_at": instant((opening + timedelta(hours=1)).isoformat()), **sides})
    return pairs


def decode_csv(inputs):
    bids, asks = [item for item in inputs if item["side"] == "BID"], [item for item in inputs if item["side"] == "ASK"]
    if not 1 <= len(bids) == len(asks) <= 12 or len(bids) + len(asks) != len(inputs):
        raise ValueError("Se requieren entre 1 y 12 parejas de CSV BID y ASK en orden cronológico.")
    pairs = []
    for bid, ask in zip(bids, asks, strict=True):
        left = inspect_export(bid["body"], pair="EUR/USD", side="BID", interval="1Hour")
        right = inspect_export(ask["body"], pair="EUR/USD", side="ASK", interval="1Hour")
        comparison = compare_exports(left, right)
        if not comparison["aligned"]:
            raise ValueError("CSV BID/ASK incompatibles: " + "; ".join(comparison["errors"]))
        for bid_bar, ask_bar in zip(left["bars"], right["bars"], strict=True):
            pairs.append({"open_at": bid_bar["open_at"], "close_at": bid_bar["close_at"],
                          **{side: {key: bar[key] for key in ("open", "high", "low", "close")}
                             for side, bar in (("bid", bid_bar), ("ask", ask_bar))}})
    return pairs


def aggregate(pairs, *, start, end):
    if not pairs or len(pairs) > MAX_HOURS:
        raise ValueError("Histórico H1 vacío o excesivo.")
    if any(right["open_at"] < left["close_at"] for left, right in zip(pairs, pairs[1:])):
        raise ValueError("Bloques repetidos, solapados o fuera de orden; no se eliminan duplicados.")
    selected = [bar for bar in pairs if bar["open_at"] >= start and bar["close_at"] <= end]
    if not selected:
        raise ValueError("El período solicitado no contiene velas H1 completas.")
    days = defaultdict(list)
    for bar in selected:
        days[bar["open_at"][:10]].append(bar)
    sessions = []
    for date, bars in sorted(days.items()):
        day = datetime.fromisoformat(date).replace(tzinfo=UTC)
        sides = {side: {"open": bars[0][side]["open"], "close": bars[-1][side]["close"],
                       "high": decimal_text(max(Decimal(bar[side]["high"]) for bar in bars)),
                       "low": decimal_text(min(Decimal(bar[side]["low"]) for bar in bars))} for side in ("bid", "ask")}
        sessions.append({"date": date, "session_start_at": instant(day.isoformat()),
            "session_close_at": instant((day + timedelta(days=1)).isoformat()),
            "first_observed_open_at": bars[0]["open_at"], "last_observed_close_at": bars[-1]["close_at"],
            "observed_hours": len(bars), "full_24_hours_observed": len(bars) == 24,
            "internal_gaps": [{"from": left["close_at"], "to": right["open_at"]}
                              for left, right in zip(bars, bars[1:]) if left["close_at"] != right["open_at"]], **sides})
    long_gaps = [{"from": left["close_at"], "to": right["open_at"]} for left, right in zip(selected, selected[1:])
                if datetime.fromisoformat(right["open_at"]) - datetime.fromisoformat(left["close_at"]) > timedelta(hours=96)]
    for left, right in ((start, selected[0]["open_at"]), (selected[-1]["close_at"], end)):
        if datetime.fromisoformat(right) - datetime.fromisoformat(left) > timedelta(hours=96):
            long_gaps.append({"from": left, "to": right})
    daily = {"protocol": "tiresias_supplied_hourly_daily_v1", "pair": "EUR/USD", "timezone": "Etc/UTC",
             "session_policy": "utc_calendar_date_keep_observed_partial_days_and_sundays",
             "missing_prices_filled": False, "market_calendar_verified": False, "raw_grid_complete_verified": False,
             "blocking_gaps": long_gaps, "long_gap_policy_hours": 96,
             "sessions_sha256": checksum(sessions), "sessions": sessions, "accounting_processed": False}
    return daily, len(selected)


def compute(inputs, *, source_format, year, start_date, end_date):
    start, end = selection(start_date, end_date)
    if source_format == CSV_FORMAT:
        if year is not None:
            raise ValueError("Los CSV no usan un año declarado adicional.")
        pairs = decode_csv(inputs)
        provider, basis, upstream, attribution = "Dukascopy", "user_declared_not_embedded_in_csv", None, None
    elif source_format == EV_FORMAT:
        if len(inputs) != 1 or inputs[0]["side"] != "BOTH":
            raise ValueError("Se requiere un JSON gzip anual con BID y ASK.")
        pairs = decode_ev(inputs[0]["body"], year)
        provider, basis, upstream = "EV Trading Labs", "catalog_declared_symbol_interval_and_year", "Dukascopy (declarado por EV Trading Labs)"
        attribution = "Datos agregados por EV Trading Labs · https://evtradelabs.com/data · uso gratuito con atribución según el catálogo."
    else:
        raise ValueError("Formato de precios no admitido.")
    sources = []
    for index, item in enumerate(inputs):
        filename(item["name"])
        sources.append({"file": f"raw/{index:02d}." + ("json.gz" if source_format == EV_FORMAT else "csv"),
                        "side": item["side"], "original_name": item["name"],
                        "sha256": sha256(item["body"]).hexdigest(), "bytes": len(item["body"])})
    daily, selected_hours = aggregate(pairs, start=start, end=end)
    manifest = {"profile": PROFILE, "status": "prepared", "pair": "EUR/USD", "timezone": "Etc/UTC", "interval": "1Hour",
        "source_format": source_format, "provider": provider, "identity_basis": basis, "claimed_upstream": upstream,
        "attribution": attribution, "catalog_url": "https://evtradelabs.com/data" if source_format == EV_FORMAT else None,
        "catalog_path": f"EURUSD/H1/{year}.json.gz" if source_format == EV_FORMAT else None, "declared_year": year,
        "start_date": start_date, "end_date_exclusive": end_date, "first_month": start_date[:7],
        "last_month": (datetime.fromisoformat(end_date) - timedelta(days=1)).strftime("%Y-%m"),
        "source_files": len(sources), "sources": sources, "total_source_hours": len(pairs), "selected_hours": selected_hours,
        "excluded_hours_outside_period": len(pairs) - selected_hours, "daily_sessions": len(daily["sessions"]),
        "first_observed_open_at": daily["sessions"][0]["first_observed_open_at"],
        "last_observed_close_at": daily["sessions"][-1]["last_observed_close_at"],
        "sessions_sha256": daily["sessions_sha256"], "internal_gap_count": sum(len(day["internal_gaps"]) for day in daily["sessions"]),
        "coverage_gap_count": len(daily["blocking_gaps"]), "all_final_transports_https": None,
        "transport_basis": "supplied_file_final_download_url_not_recorded", "provider_authenticated": False,
        "volume_units_verified": False, "accounting_processed": False}
    return manifest, daily


def prepare(*, inputs, source_format, year, start_date, end_date, output):
    output = Path(output)
    output = safe_under(output.parent.resolve(), output.name)
    if output.exists():
        raise ValueError("La salida ya existe; utilizar un directorio nuevo.")
    manifest, daily = compute(inputs, source_format=source_format, year=year, start_date=start_date, end_date=end_date)
    output.mkdir(parents=True)
    (output / "raw").mkdir()
    for source, item in zip(manifest["sources"], inputs, strict=True):
        with safe_under(output, source["file"]).open("xb") as stream:
            stream.write(item["body"])
    save_json(output / "daily.json", daily)
    save_json(output / "manifest.json", manifest)
    return manifest


def load_prepared(directory):
    directory = Path(directory)
    manifest_raw = read_file(safe_under(directory, "manifest.json"), 256 * 1024)
    manifest = strict_json(manifest_raw)
    if not isinstance(manifest, dict) or manifest.get("profile") != PROFILE:
        raise ValueError("Histórico aportado no reconocido.")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 24:
        raise ValueError("Inventario de originales inválido.")
    inputs = []
    for index, item in enumerate(sources):
        fields(item, ("file", "side", "original_name", "sha256", "bytes"), "original aportado")
        expected = f"raw/{index:02d}." + ("json.gz" if manifest.get("source_format") == EV_FORMAT else "csv")
        if item["file"] != expected:
            raise ValueError("Ruta de original incompatible.")
        raw = read_file(safe_under(directory, expected))
        if sha256(raw).hexdigest() != item["sha256"] or len(raw) != item["bytes"]:
            raise ValueError("El original no coincide con su huella.")
        inputs.append({"name": item["original_name"], "side": item["side"], "body": raw})
    expected, daily = compute(inputs, source_format=manifest.get("source_format"), year=manifest.get("declared_year"),
                              start_date=manifest.get("start_date"), end_date=manifest.get("end_date_exclusive"))
    daily_raw = read_file(safe_under(directory, "daily.json"), 8 * 1024 * 1024)
    if canonical(manifest) != canonical(expected) or canonical(strict_json(daily_raw)) != canonical(daily):
        raise ValueError("El histórico no coincide con la reconstrucción de sus originales.")
    provenance = {"directory": str(directory.resolve()), "manifest_sha256": sha256(manifest_raw).hexdigest(),
        "daily_file_sha256": sha256(daily_raw).hexdigest(), "sessions_sha256": daily["sessions_sha256"],
        "provider": manifest["provider"], "source_format": manifest["source_format"], "originals_verified": True,
        "attribution": manifest["attribution"], "identity_basis": manifest["identity_basis"],
        "claimed_upstream": manifest["claimed_upstream"], "catalog_url": manifest["catalog_url"],
        "start_date": manifest["start_date"], "end_date_exclusive": manifest["end_date_exclusive"],
        "all_final_transports_https": None, "provider_authenticated": False,
        "source_files": [{"file": item["file"], "sha256": item["sha256"]} for item in sources]}
    return daily, provenance, manifest_raw, daily_raw


def main(argv=None):
    parser = argparse.ArgumentParser(description="Preparar precios H1 aportados, sin descargas ni cuentas.")
    parser.add_argument("--format", choices=(CSV_FORMAT, EV_FORMAT), required=True)
    parser.add_argument("--bid", nargs="+", type=Path)
    parser.add_argument("--ask", nargs="+", type=Path)
    parser.add_argument("--annual", type=Path)
    parser.add_argument("--year", type=int)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True, help="Fecha UTC exclusiva.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        inputs = []
        if args.format == CSV_FORMAT:
            if args.annual or not args.bid or not args.ask:
                raise ValueError("Elegir CSV BID/ASK sin archivo anual.")
            for side, paths in (("BID", args.bid), ("ASK", args.ask)):
                inputs.extend({"name": path.name, "side": side, "body": read_file(path)} for path in paths)
        else:
            if args.bid or args.ask or not args.annual:
                raise ValueError("Elegir un archivo anual sin CSV BID/ASK.")
            inputs.append({"name": args.annual.name, "side": "BOTH", "body": read_file(args.annual, MAX_GZIP)})
        manifest = prepare(inputs=inputs, source_format=args.format, year=args.year, start_date=args.start_date,
                           end_date=args.end_date, output=args.output)
        print(json.dumps({key: value for key, value in manifest.items() if key != "sources"}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
