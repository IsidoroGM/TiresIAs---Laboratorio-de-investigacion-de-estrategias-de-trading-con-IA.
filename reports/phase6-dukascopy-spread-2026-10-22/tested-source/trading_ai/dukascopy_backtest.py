"""Prueba histórica local con BID/ASK; independiente de Pine y del libro de cuentas."""

import argparse
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import sys

from trading_ai.dukascopy_history import (MAX_BODY, PROFILE, build_daily, decode_month,
                                        months_between, save_json, source_url, validate_final_url)
from trading_ai.indicators import simple_moving_average
from trading_ai.strategies import moving_average_crossover_signals, validate_crossover_windows
from trading_ai.tv_contracts import canonical, checksum, decimal_text, number, safe_under, strict_json


PROTOCOL = "tiresias_dukascopy_spread_research_v1"


def read_bounded(path, maximum):
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("Archivo de histórico excesivo: " + path.name)
    return raw


def load_history(directory):
    """Reconstruye desde BI5 y contrasta el diario; un resumen no verifica los precios."""
    directory = Path(directory)
    directory = safe_under(directory.parent.resolve(), directory.name)
    manifest_raw = read_bounded(safe_under(directory, "manifest.json"), 256 * 1024)
    manifest = strict_json(manifest_raw)
    if (not isinstance(manifest, dict) or manifest.get("profile") != PROFILE
            or manifest.get("status") != "prepared" or manifest.get("pair") != "EUR/USD"
            or manifest.get("provider_authenticated") is not False):
        raise ValueError("Se requiere un histórico EUR/USD preparado con procedencia explícita.")
    months = months_between(manifest.get("first_month"), manifest.get("last_month"), now=datetime.now(UTC))
    sources = manifest.get("sources")
    if not isinstance(sources, list) or len(sources) != len(months) * 2 or manifest.get("source_files") != len(sources):
        raise ValueError("Inventario de fuentes incompleto.")
    expected = {f"raw/{month:%Y-%m}-{side}.bi5" for month in months for side in ("BID", "ASK")}
    if any(not isinstance(item, dict) or not isinstance(item.get("file"), str) for item in sources):
        raise ValueError("Inventario de fuentes inválido.")
    indexed = {item["file"]: item for item in sources}
    if len(indexed) != len(sources) or set(indexed) != expected:
        raise ValueError("Rutas de fuentes repetidas o incompatibles.")
    pairs = []
    for month in months:
        sides = []
        for side in ("BID", "ASK"):
            name = f"raw/{month:%Y-%m}-{side}.bi5"
            entry = indexed[name]
            url = source_url(month, side)
            if entry.get("url") != url or not isinstance(entry.get("final_url"), str):
                raise ValueError("URL de origen incompatible.")
            validate_final_url(url, entry["final_url"])
            if (entry.get("provider_authenticated") is not False
                    or entry.get("final_transport_https") is not entry["final_url"].startswith("https://")):
                raise ValueError("Procedencia o transporte incompatible.")
            raw = read_bounded(safe_under(directory, name), MAX_BODY)
            if sha256(raw).hexdigest() != entry.get("original_sha256"):
                raise ValueError("La huella del archivo original no coincide: " + name)
            decoded = decode_month(raw, month, side)
            for field, key in (("raw_records", "raw_records"), ("observed_hours", "rows"),
                               ("excluded_flat_zero_volume_records", "excluded_flat_zero_volume_records")):
                if entry.get(field) != decoded[key]:
                    raise ValueError("El inventario no coincide con las cotizaciones originales.")
            sides.append(decoded)
        pairs.append(tuple(sides))
    daily = build_daily(pairs)
    daily_raw = read_bounded(safe_under(directory, "daily.json"), 8 * 1024 * 1024)
    if (canonical(strict_json(daily_raw)) != canonical(daily)
            or manifest.get("sessions_sha256") != daily["sessions_sha256"]
            or manifest.get("daily_sessions") != len(daily["sessions"])):
        raise ValueError("El diario no coincide con su reconstrucción desde los originales.")
    all_https = all(item["final_transport_https"] for item in sources)
    if manifest.get("all_final_transports_https") is not all_https:
        raise ValueError("Resumen de transporte incompatible.")
    return daily, {"directory": str(directory.resolve()), "manifest_sha256": sha256(manifest_raw).hexdigest(),
                   "daily_file_sha256": sha256(daily_raw).hexdigest(),
                   "sessions_sha256": daily["sessions_sha256"], "originals_verified": True,
                   "all_final_transports_https": all_https, "provider_authenticated": False,
                   "source_files": [{"file": item["file"], "sha256": item["original_sha256"]} for item in sources]}, manifest_raw, daily_raw


def simulate(daily, *, capital, quantity, commission_rate, fast=20, slow=60):
    """Señal al terminar la sesión UTC; operación en la siguiente apertura observada.

    Los datos deben proceder de load_history. La función pura permite comprobar la
    causalidad con datos artificiales sin crear cuentas ni tocar almacenamiento.
    """
    validate_crossover_windows(fast, slow)
    if slow > 252:
        raise ValueError("La ventana lenta no puede superar 252 observaciones.")
    initial = number(capital, "capital hipotético", maximum=Decimal("1e9"), positive=True)
    size = number(quantity, "unidades EUR", maximum=Decimal("1e9"), positive=True)
    rate = number(commission_rate, "comisión proporcional supuesta", maximum=Decimal("0.1"))
    sessions = daily["sessions"]
    config = {"strategy": "sma", "fast": fast, "slow": slow, "currency": "USD", "pair": "EUR/USD",
              "initial_capital": decimal_text(initial), "quantity": decimal_text(size),
              "assumed_commission_rate": decimal_text(rate), "leverage": "1", "direction": "long_only",
              "signal_basis": "observed_utc_bid_close", "signal_time": "utc_calendar_session_close",
              "execution": "next_observed_session_first_hour_open", "buy_quote": "ask", "sell_quote": "bid",
              "valuation_quote": "bid", "spread_subtracted_separately": False,
              "slippage_modelled": False, "swaps_modelled": False, "forced_final_liquidation": False}
    result = {"protocol": PROTOCOL, "configuration": config, "sessions_sha256": daily["sessions_sha256"],
              "daily_sessions": len(sessions), "required_sessions": slow + 1,
              "missing_sessions": max(0, slow + 1 - len(sessions)), "accounting_processed": False,
              "external_orders_sent": False, "pine_equivalence_verified": False,
              "hypothetical_fills": [], "rejected_orders": [], "pending_order": None,
              "equity_curve": [], "observations": [], "summary": None}
    if any(day["internal_gaps"] for day in sessions):
        return {**result, "status": "blocked_internal_gaps"}
    if len(sessions) < slow + 1:
        return {**result, "status": "insufficient_history"}
    with localcontext(Context(prec=28)):
        prices = [Decimal(day["bid"]["close"]) for day in sessions]
        quick, gradual = simple_moving_average(prices, fast), simple_moving_average(prices, slow)
        signals = moving_average_crossover_signals(quick, gradual)
        cash, position, basis, pending = initial, Decimal(0), Decimal(0), None
        commissions, realized, peak, drawdown_max, spread_total = (Decimal(0) for _ in range(5))
        peak = initial
        closed = 0
        for index, day in enumerate(sessions):
            if pending is not None:
                executed_at = day["first_observed_open_at"]
                if executed_at < pending["signal_at"]:
                    raise ValueError("La apertura de ejecución precede al cierre que generó la señal.")
                side = pending["side"]
                bid, ask = Decimal(day["bid"]["open"]), Decimal(day["ask"]["open"])
                if ask < bid:
                    raise ValueError("Cotizaciones cruzadas en apertura.")
                price = ask if side == "buy" else bid
                units = size if side == "buy" else position
                fee = units * price * rate
                if side == "buy" and units * price + fee > cash:
                    result["rejected_orders"].append({**pending, "executed_at": executed_at,
                                                     "reason": "insufficient_cash_at_next_ask_open"})
                else:
                    if side == "buy":
                        cash -= units * price + fee
                        position, basis = units, units * price + fee
                    else:
                        cash += units * price - fee
                        realized += units * price - fee - basis
                        position, basis = Decimal(0), Decimal(0)
                        closed += 1
                    commissions += fee
                    # Diagnóstico frente a ejecutar al punto medio en cada operación.
                    # Ya está incluido en los precios; no se resta de nuevo al efectivo.
                    spread = units * (ask - bid) / 2
                    spread_total += spread
                    result["hypothetical_fills"].append({**pending, "executed_at": executed_at,
                        "quote_basis": "ask_open" if side == "buy" else "bid_open", "quantity": decimal_text(units),
                        "price": decimal_text(price), "bid_open": decimal_text(bid), "ask_open": decimal_text(ask),
                        "assumed_commission": decimal_text(fee), "spread_vs_midpoint": decimal_text(spread)})
                pending = None
            signal = signals[index].value
            result["observations"].append({"date": day["date"], "signal_at": day["session_close_at"],
                "fast": None if quick[index] is None else decimal_text(quick[index]),
                "slow": None if gradual[index] is None else decimal_text(gradual[index]), "signal": signal})
            side = "buy" if signal == "enter_long" and position == 0 else "sell" if signal == "exit_long" and position > 0 else None
            if side:
                pending = {"side": side, "signal_at": day["session_close_at"]}
            equity = cash + position * Decimal(day["bid"]["close"])
            peak = max(peak, equity)
            drawdown = (peak - equity) / peak * 100
            drawdown_max = max(drawdown_max, drawdown)
            result["equity_curve"].append({"at": day["last_observed_close_at"], "cash": decimal_text(cash),
                "quantity": decimal_text(position), "bid_close": day["bid"]["close"], "equity": decimal_text(equity),
                "drawdown_percent": decimal_text(drawdown)})
        result.update(status="simulated", pending_order=pending,
            summary={"initial_capital": decimal_text(initial), "currency": "USD", "final_equity": decimal_text(equity),
                     "cash": decimal_text(cash), "open_quantity": decimal_text(position),
                     "return_percent": decimal_text((equity / initial - 1) * 100),
                     "max_observed_drawdown_percent": decimal_text(drawdown_max),
                     "realized_pnl": decimal_text(realized), "closed_trades": closed,
                     "assumed_commissions": decimal_text(commissions),
                     "spread_vs_midpoint_diagnostic": decimal_text(spread_total),
                     "last_valuation_at": sessions[-1]["last_observed_close_at"]})
    return result


def run_backtest(*, history, output, capital, quantity, commission_rate, fast=20, slow=60):
    output = Path(output)
    output = safe_under(output.parent.resolve(), output.name)
    if output.exists():
        raise ValueError("La salida ya existe; utilizar un directorio nuevo.")
    daily, provenance, manifest_raw, daily_raw = load_history(history)
    result = {**simulate(daily, capital=capital, quantity=quantity, commission_rate=commission_rate, fast=fast, slow=slow),
              "source": provenance,
              "implementation_sha256": {name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in
                  ("dukascopy_backtest.py", "dukascopy_history.py", "dukascopy.py", "indicators.py", "strategies.py", "tv_contracts.py")}}
    result["result_sha256"] = checksum(result)
    output.mkdir(parents=True)
    with (output / "input-manifest.json").open("xb") as stream:
        stream.write(manifest_raw)
    with (output / "input-daily.json").open("xb") as stream:
        stream.write(daily_raw)
    save_json(output / "simulation.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prueba local SMA diaria BID/ASK, sin modificar cuentas.")
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capital", default="1000")
    parser.add_argument("--quantity", default="1")
    parser.add_argument("--commission-rate", required=True, help="Tasa proporcional hipotética, no tarifa real del proveedor.")
    args = parser.parse_args(argv)
    try:
        result = run_backtest(history=args.history, output=args.output, capital=args.capital,
                              quantity=args.quantity, commission_rate=args.commission_rate)
        print(json.dumps({key: result[key] for key in ("status", "daily_sessions", "required_sessions", "missing_sessions", "summary", "result_sha256")},
                         ensure_ascii=False, indent=2))
        return 0 if result["status"] == "simulated" else 2
    except (ValueError, OSError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
