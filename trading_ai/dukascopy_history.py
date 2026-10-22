"""Histórico público H1 de EUR/USD y sesiones UTC observadas. Sin cuentas u órdenes."""

import argparse
import base64
import binascii
import calendar
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
import lzma
import math
from pathlib import Path
import re
import struct
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener

from trading_ai.dukascopy import compare_exports
from trading_ai.indicators import simple_moving_average
from trading_ai.strategies import moving_average_crossover_signals
from trading_ai.tv_contracts import canonical, checksum, decimal_text, fields, instant, safe_under, strict_json


PROFILE = "tiresias_dukascopy_public_h1_v1"
MAX_BODY = 2 * 1024 * 1024
MAX_DECODED = 31 * 24 * 24
PRICE_SCALE = Decimal(100000)  # EUR/USD, contrastado con los CSV del usuario.


def month_start(value):
    if not isinstance(value, str) or not re.fullmatch(r"20[0-9]{2}-(?:0[1-9]|1[0-2])", value):
        raise ValueError("Mes requerido: YYYY-MM, entre 2000 y 2099.")
    return datetime.strptime(value, "%Y-%m").replace(tzinfo=UTC)


def next_month(value):
    return value.replace(year=value.year + 1, month=1) if value.month == 12 else value.replace(month=value.month + 1)


def months_between(first, last, *, now):
    start, end = month_start(first), month_start(last)
    if start > end or next_month(end) > now:
        raise ValueError("Seleccionar meses cerrados y ordenados.")
    result = []
    while start <= end:
        result.append(start)
        if len(result) > 36:
            raise ValueError("Máximo 36 meses por descarga.")
        start = next_month(start)
    return result


def source_url(month, side):
    if side not in ("BID", "ASK"):
        raise ValueError("Lado BID/ASK requerido.")
    return (f"https://www.dukascopy.com/datafeed/EURUSD/{month.year}/"
            f"{month.month - 1:02d}/{side}_candles_hour_1.bi5")


def validate_final_url(initial, final):
    source, target = urlsplit(initial), urlsplit(final)
    if (source.scheme not in ("http", "https")
            or source.netloc not in ("www.dukascopy.com", "datafeed.dukascopy.com")
            or source.query or source.fragment
            or target.scheme not in ("http", "https")
            or target.netloc not in ("www.dukascopy.com", "datafeed.dukascopy.com")
            or target.path != source.path or target.query or target.fragment):
        raise ValueError("Redirección fuera de la ruta pública de Dukascopy.")


class PublicFeedRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        validate_final_url(request.full_url, newurl)
        return super().redirect_request(request, fp, code, message, headers, newurl)


class DownloadUnavailable(ValueError):
    def __init__(self, message, *, status=None, retry_after=None):
        super().__init__(message)
        self.http_status = status
        self.retry_after = retry_after


def fetch_public(url, *, timeout=15):
    """GET ordinario, sin cookies, credenciales, reintentos ni resolución de retos."""
    try:
        with build_opener(PublicFeedRedirect()).open(url, timeout=timeout) as response:
            if response.status != 200:
                raise DownloadUnavailable(f"Dukascopy devuelve HTTP {response.status}; no se considera una descarga.",
                                          status=response.status, retry_after=response.headers.get("Retry-After"))
            final = response.geturl()
            validate_final_url(url, final)
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if content_type not in ("application/octet-stream", "application/x-lzma"):
                raise ValueError("La respuesta no es un archivo binario de cotizaciones.")
            body = response.read(MAX_BODY + 1)
            if not body or len(body) > MAX_BODY:
                raise ValueError("Archivo vacío o mayor de 2 MiB.")
            return {"body": body, "final_url": final, "content_type": content_type,
                    "retrieved_at": datetime.now(UTC).isoformat()}
    except HTTPError as error:
        retry_after = error.headers.get("Retry-After") if error.headers is not None else None
        error.close()
        detail = f"; Retry-After: {retry_after}" if retry_after else ""
        raise DownloadUnavailable(f"Descarga pública no disponible: HTTP {error.code}{detail}",
                                  status=error.code, retry_after=retry_after) from error
    except (URLError, OSError) as error:
        raise DownloadUnavailable(f"Descarga pública no disponible: {error}") from error


def decode_month(raw, month, side):
    if side not in ("BID", "ASK") or not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BODY:
        raise ValueError("Archivo BI5 acotado y lado explícito requeridos.")
    try:
        decoder = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
        data = decoder.decompress(raw, max_length=MAX_DECODED + 1)
        if not decoder.eof or decoder.unused_data or not data or len(data) > MAX_DECODED or len(data) % 24:
            raise ValueError("BI5 truncado, concatenado o de tamaño incompatible.")
    except lzma.LZMAError as error:
        raise ValueError("Compresión BI5 inválida.") from error
    expected_hours = calendar.monthrange(month.year, month.month)[1] * 24
    bars, offsets, excluded = [], [], 0
    for seconds, opening, closing, low, high, volume in struct.iter_unpack(">5If", data):
        if seconds % 3600 or not 0 <= seconds < expected_hours * 3600 or offsets and seconds <= offsets[-1]:
            raise ValueError("Aperturas BI5 fuera de mes, duplicadas o no horarias.")
        if not math.isfinite(volume) or volume < 0:
            raise ValueError("Volumen BI5 inválido.")
        offsets.append(seconds)
        if volume == 0 and opening == closing == low == high:
            excluded += 1
            continue
        if min(opening, closing, low, high) <= 0 or high < max(opening, closing, low) or low > min(opening, closing, high):
            raise ValueError("Precios OHLC BI5 inválidos.")
        start = month + timedelta(seconds=seconds)
        with localcontext(Context(prec=64)):
            prices = {key: decimal_text(Decimal(value) / PRICE_SCALE) for key, value in
                      (("open", opening), ("high", high), ("low", low), ("close", closing))}
        bars.append({"open_at": instant(start.isoformat()), "close_at": instant((start + timedelta(hours=1)).isoformat()),
                     **prices, "source_volume_float32": decimal_text(Decimal.from_float(volume))})
    if not bars:
        raise ValueError("El mes no contiene cotizaciones con actividad.")
    missing = expected_hours - len(offsets)
    return {"protocol": PROFILE, "pair": "EUR/USD", "side": side, "interval": "1Hour",
            "original_sha256": sha256(raw).hexdigest(), "rows": len(bars), "raw_records": len(offsets),
            "excluded_flat_zero_volume_records": excluded, "missing_raw_hours": missing,
            "complete_raw_month": missing == 0, "volume_units_verified": False,
            "first_open_at": bars[0]["open_at"], "last_close_at": bars[-1]["close_at"], "bars": bars}


def cached_month(cache, month, side, *, offline, fetch):
    url = source_url(month, side)
    path = safe_under(cache, f"{month:%Y-%m}-{side}.json")
    if path.exists():
        if path.stat().st_size > 3 * 1024 * 1024:
            raise ValueError("Caché excesiva.")
        entry = strict_json(path.read_bytes())
        fields(entry, ("profile", "url", "final_url", "content_type", "retrieved_at", "original_sha256",
                       "body_base64", "final_transport_https", "provider_authenticated"), "caché de histórico")
        try:
            retrieved = datetime.fromisoformat(entry["retrieved_at"])
            if retrieved.utcoffset() != timedelta(0) or entry["provider_authenticated"] is not False:
                raise ValueError("Fecha o autenticación de caché incompatible.")
            if entry["content_type"] not in ("application/octet-stream", "application/x-lzma"):
                raise ValueError("Tipo de contenido de caché incompatible.")
            raw = base64.b64decode(entry["body_base64"], validate=True)
            validate_final_url(url, entry["final_url"])
            if entry["url"] != url or entry["profile"] != PROFILE or sha256(raw).hexdigest() != entry["original_sha256"]:
                raise ValueError("Identidad o huella de caché incompatible.")
        except (KeyError, TypeError, binascii.Error) as error:
            raise ValueError("Caché de histórico inválida.") from error
        if entry["final_transport_https"] is not (urlsplit(entry["final_url"]).scheme == "https"):
            raise ValueError("Transporte de caché incompatible con su URL.")
        if not decode_month(raw, month, side)["complete_raw_month"]:
            raise ValueError("Mes incompleto en caché; requiere revisión antes de reutilizarse.")
        return raw, entry, True
    if offline:
        raise ValueError(f"Falta caché para {month:%Y-%m} {side}; el modo offline no descarga.")
    downloaded = fetch(url)
    raw = downloaded["body"]
    validate_final_url(url, downloaded["final_url"])
    if not decode_month(raw, month, side)["complete_raw_month"]:
        raise ValueError("La descarga no contiene todas las horas del mes; no se guarda en caché.")
    entry = {"profile": PROFILE, "url": url, "final_url": downloaded["final_url"],
             "content_type": downloaded["content_type"], "retrieved_at": downloaded["retrieved_at"],
             "original_sha256": sha256(raw).hexdigest(), "body_base64": base64.b64encode(raw).decode("ascii"),
             "final_transport_https": urlsplit(downloaded["final_url"]).scheme == "https",
             "provider_authenticated": False}
    cache.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(entry) + b"\n")
    return raw, entry, False


def build_daily(month_pairs):
    days, originals = defaultdict(list), []
    previous_close = None
    for bid, ask in month_pairs:
        comparison = compare_exports(bid, ask)
        if not comparison["aligned"] or not bid["complete_raw_month"] or not ask["complete_raw_month"]:
            raise ValueError("Mes BID/ASK incompleto o incompatible; se conserva para revisión.")
        originals.append({"bid": bid["original_sha256"], "ask": ask["original_sha256"]})
        for left, right in zip(bid["bars"], ask["bars"], strict=True):
            if previous_close is not None and left["open_at"] < previous_close:
                raise ValueError("Los meses se repiten, solapan o están fuera de orden.")
            previous_close = left["close_at"]
            days[left["open_at"][:10]].append((left, right))
    sessions = []
    for day, pairs in sorted(days.items()):
        start = datetime.fromisoformat(day).replace(tzinfo=UTC)
        missing_internal = []
        for previous, following in zip(pairs, pairs[1:]):
            if previous[0]["close_at"] != following[0]["open_at"]:
                missing_internal.append({"from": previous[0]["close_at"], "to": following[0]["open_at"]})
        sides = {}
        for index, side in enumerate(("bid", "ask")):
            bars = [pair[index] for pair in pairs]
            sides[side] = {"open": bars[0]["open"], "close": bars[-1]["close"],
                           "high": decimal_text(max(Decimal(bar["high"]) for bar in bars)),
                           "low": decimal_text(min(Decimal(bar["low"]) for bar in bars))}
        sessions.append({"date": day, "session_start_at": instant(start.isoformat()),
                         "session_close_at": instant((start + timedelta(days=1)).isoformat()),
                         "first_observed_open_at": pairs[0][0]["open_at"],
                         "last_observed_close_at": pairs[-1][0]["close_at"],
                         "observed_hours": len(pairs), "full_24_hours_observed": len(pairs) == 24,
                         "internal_gaps": missing_internal, **sides})
    return {"protocol": "tiresias_dukascopy_daily_observed_v1", "pair": "EUR/USD", "timezone": "Etc/UTC",
            "session_policy": "utc_calendar_date_keep_observed_partial_days_and_sundays",
            "zero_volume_policy": "exclude_only_flat_zero_volume_hourly_records",
            "missing_prices_filled": False, "market_calendar_verified": False,
            "source_months": originals, "sessions_sha256": checksum(sessions), "sessions": sessions,
            "accounting_processed": False}


def signal_preview(daily):
    if not daily["sessions"]:
        raise ValueError("No hay sesiones que analizar.")
    if any(day["internal_gaps"] for day in daily["sessions"]):
        return {"available": False, "reason": "internal_hourly_gaps", "signals": [], "accounting_processed": False}
    closes = [Decimal(day["bid"]["close"]) for day in daily["sessions"]]
    fast, slow = simple_moving_average(closes, 20), simple_moving_average(closes, 60)
    signals = moving_average_crossover_signals(fast, slow)
    return {"protocol": "tiresias_dukascopy_sma_signal_preview_v1", "available": len(closes) >= 61,
            "strategy": "SMA20/60", "price_basis": "observed_utc_bid_close",
            "daily_sessions": len(closes), "warmup_observations_required": 60,
            "signals": [{"at": day["session_close_at"], "signal": signal.value,
                         "fast": None if f is None else decimal_text(f), "slow": None if s is None else decimal_text(s)}
                        for day, signal, f, s in zip(daily["sessions"], signals, fast, slow, strict=True)],
            "executed_orders": False, "accounting_processed": False}


def save_json(path, value):
    with path.open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def prepare_history(*, first, last, cache, output, offline=False, now=None, fetch=fetch_public, pause=1, progress=None):
    months = months_between(first, last, now=datetime.now(UTC) if now is None else now)
    cache, output = Path(cache), Path(output)
    # Comprobar enlaces antes de escribir en cualquiera de los destinos.
    for target in (cache, output):
        safe_under(target.parent.resolve(), target.name)
    if output.exists():
        raise ValueError("La salida ya existe; utilizar un directorio nuevo.")
    output.mkdir(parents=True)
    raw_directory = output / "raw"
    raw_directory.mkdir()
    pairs, entries, requests = [], [], 0
    try:
        for month in months:
            values = []
            for side in ("BID", "ASK"):
                # Las peticiones se hacen en serie, sin descargas al consultar la interfaz.
                raw, source, hit = cached_month(cache, month, side, offline=offline, fetch=fetch)
                requests += int(not hit)
                name = f"{month:%Y-%m}-{side}.bi5"
                with (raw_directory / name).open("xb") as stream:
                    stream.write(raw)
                decoded = decode_month(raw, month, side)
                values.append(decoded)
                entries.append({"file": "raw/" + name, **{key: source[key] for key in
                    ("url", "final_url", "retrieved_at", "original_sha256", "final_transport_https", "provider_authenticated")},
                    "cache_hit": hit, "raw_records": decoded["raw_records"], "observed_hours": decoded["rows"],
                    "excluded_flat_zero_volume_records": decoded["excluded_flat_zero_volume_records"]})
                if not hit and pause:
                    time.sleep(pause)
            pairs.append(tuple(values))
            if progress is not None:
                progress({"month": month.strftime("%Y-%m"), "months_completed": len(pairs), "months_total": len(months)})
        daily = build_daily(pairs)
        preview = signal_preview(daily)
        save_json(output / "daily.json", daily)
        save_json(output / "signal-preview.json", preview)
        result = {"profile": PROFILE, "status": "prepared", "pair": "EUR/USD", "first_month": first, "last_month": last,
                  "source_files": len(entries), "network_requests": requests, "offline": offline,
                  "daily_sessions": len(daily["sessions"]), "sessions_sha256": daily["sessions_sha256"],
                  "signal_preview_available": preview["available"],
                  "all_final_transports_https": all(entry["final_transport_https"] for entry in entries),
                  "provider_authenticated": False, "sources": entries, "accounting_processed": False}
        save_json(output / "manifest.json", result)
        return result
    except (ValueError, OSError) as error:
        save_json(output / "failure.json", {"status": "incomplete", "error": str(error), "sources": entries,
                                            "http_status": getattr(error, "http_status", None),
                                            "retry_after": getattr(error, "retry_after", None),
                                            "accounting_processed": False})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="EUR/USD público: meses H1 cerrados, caché y sesiones UTC; sin órdenes.")
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--cache", type=Path, default=Path(".local/dukascopy/public-h1-cache"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = prepare_history(first=args.start_month, last=args.end_month, cache=args.cache, output=args.output,
                                 offline=args.offline, progress=lambda value: print(json.dumps(value), flush=True))
        print(json.dumps({key: value for key, value in result.items() if key != "sources"}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
