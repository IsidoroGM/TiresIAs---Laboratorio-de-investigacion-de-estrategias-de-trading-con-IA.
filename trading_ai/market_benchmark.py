"""Fixed SMA/reference and commission experiments; no network or account processing."""

from decimal import Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path

from trading_ai.dukascopy_backtest import load_history, read_bounded, simulate
from trading_ai.dukascopy_history import save_json
from trading_ai.tv_contracts import canonical, checksum, decimal_text, number, safe_under, strict_json


PROTOCOL = "tiresias_fixed_reference_costs_v1"
RATES = ("0", "0.0005", "0.001", "0.002")
ENTRY_INDEX = 61
MAX_RESULT = 16 * 1024 * 1024
STATUSES = ("calculated", "blocked_coverage_gaps", "blocked_internal_gaps", "insufficient_history")
SOURCES = ("market_benchmark.py", "dukascopy_backtest.py", "dukascopy_history.py", "dukascopy.py",
           "market_history.py", "indicators.py", "strategies.py", "tv_contracts.py")


def hold_reference(daily, *, capital, quantity, commission_rate):
    """One ASK entry after the earliest possible SMA decision, then BID marks."""
    initial = number(capital, "capital hipotético", maximum=Decimal("1e9"), positive=True)
    size = number(quantity, "unidades EUR", maximum=Decimal("1e9"), positive=True)
    rate = number(commission_rate, "comisión supuesta", maximum=Decimal("0.1"))
    sessions = daily["sessions"]
    if len(sessions) <= ENTRY_INDEX:
        raise ValueError("La referencia necesita una apertura posterior a 61 sesiones completas.")
    result = {"status": "held", "hypothetical_fills": [], "rejected_orders": [], "equity_curve": []}
    with localcontext(Context(prec=28)):
        cash, position, fee, spread, peak, maximum_dd = initial, Decimal(0), Decimal(0), Decimal(0), initial, Decimal(0)
        for index, day in enumerate(sessions):
            if index == ENTRY_INDEX:
                signal_at = sessions[index-1]["session_close_at"]
                if day["first_observed_open_at"] < signal_at:
                    raise ValueError("La apertura de referencia precede al cierre de decisión.")
                bid, ask = Decimal(day["bid"]["open"]), Decimal(day["ask"]["open"])
                if ask < bid:
                    raise ValueError("Cotizaciones cruzadas en la entrada de referencia.")
                proposed_fee = size * ask * rate
                if size * ask + proposed_fee > cash:
                    result["status"] = "entry_rejected_insufficient_cash"
                    result["rejected_orders"].append({"executed_at": day["first_observed_open_at"],
                        "reason": "insufficient_cash_at_reference_ask_open"})
                else:
                    position, fee = size, proposed_fee
                    cash -= size * ask + fee
                    spread = size * (ask-bid) / 2
                    result["hypothetical_fills"].append({"side": "buy", "signal_at": signal_at,
                        "executed_at": day["first_observed_open_at"], "quantity": decimal_text(size),
                        "price": decimal_text(ask), "bid_open": decimal_text(bid), "ask_open": decimal_text(ask),
                        "quote_basis": "ask_open", "assumed_commission": decimal_text(fee),
                        "spread_vs_midpoint": decimal_text(spread)})
            equity = cash + position * Decimal(day["bid"]["close"])
            peak = max(peak, equity)
            dd = (peak-equity) / peak * 100
            maximum_dd = max(maximum_dd, dd)
            result["equity_curve"].append({"at": day["last_observed_close_at"], "cash": decimal_text(cash),
                "quantity": decimal_text(position), "equity": decimal_text(equity), "drawdown_percent": decimal_text(dd)})
        result["summary"] = {"initial_capital": decimal_text(initial), "currency": "USD", "cash": decimal_text(cash),
            "final_equity": decimal_text(equity), "open_quantity": decimal_text(position),
            "return_percent": decimal_text((equity/initial-1)*100), "max_observed_drawdown_percent": decimal_text(maximum_dd),
            "assumed_commissions": decimal_text(fee), "closed_trades": 0, "realized_pnl": "0",
            "spread_vs_midpoint_diagnostic": decimal_text(spread), "last_valuation_at": sessions[-1]["last_observed_close_at"]}
    return result


def calculate(daily, *, capital, quantity):
    control = simulate(daily, capital=capital, quantity=quantity, commission_rate="0.001")
    configuration = {key: value for key, value in control["configuration"].items() if key != "assumed_commission_rate"}
    configuration.update(assumed_commission_rates=list(RATES), reference_entry_session_index=ENTRY_INDEX,
        reference_rule="buy_fixed_quantity_at_next_ask_open_after_61_completed_sessions_hold_mark_bid",
        cash_reference_interest_rate="0", independent_scenarios=True, parameter_selection=False,
        hypothetical_exit_fee_added=False)
    result = {"protocol": PROTOCOL, "configuration": configuration, "daily_sessions": len(daily["sessions"]),
        "required_sessions": ENTRY_INDEX+1, "missing_sessions": max(0, ENTRY_INDEX+1-len(daily["sessions"])),
        "sessions_sha256": daily["sessions_sha256"], "scenarios": [], "cash_reference": None,
        "accounting_processed": False, "external_orders_sent": False, "prospective_validation": False}
    if control["status"] != "simulated":
        return {**result, "status": control["status"]}
    if result["missing_sessions"]:
        return {**result, "status": "insufficient_history"}
    result["status"] = "calculated"
    result["cash_reference"] = {"initial_capital": configuration["initial_capital"], "currency": "USD",
        "final_equity": configuration["initial_capital"], "return_percent": "0", "assumed_commissions": "0",
        "max_observed_drawdown_percent": "0", "open_quantity": "0", "hypothetical_fills": 0,
        "interest_rate": "0", "last_valuation_at": daily["sessions"][-1]["last_observed_close_at"]}
    for rate in RATES:
        sma = control if rate == "0.001" else simulate(daily, capital=capital, quantity=quantity, commission_rate=rate)
        hold = hold_reference(daily, capital=capital, quantity=quantity, commission_rate=rate)
        with localcontext(Context(prec=28)):
            difference = decimal_text(Decimal(sma["summary"]["final_equity"])-Decimal(hold["summary"]["final_equity"]))
            vs_cash = decimal_text(Decimal(sma["summary"]["final_equity"])-Decimal(configuration["initial_capital"]))
        result["scenarios"].append({"commission_rate": rate, "sma": sma, "buy_hold": hold,
            "sma_minus_buy_hold_usd": difference, "sma_minus_cash_usd": vs_cash})
    return result


def summary_of(value, result_file_sha256):
    result = {"protocol": PROTOCOL, "status": value["status"], "configuration": value["configuration"],
        "daily_sessions": value["daily_sessions"], "required_sessions": value["required_sessions"],
        "missing_sessions": value["missing_sessions"], "source": value["source"], "cash_reference": value["cash_reference"],
        "result_file_sha256": result_file_sha256, "scenarios": [{"commission_rate": item["commission_rate"],
            "sma": item["sma"]["summary"], "buy_hold": item["buy_hold"]["summary"], "buy_hold_status": item["buy_hold"]["status"],
            "sma_fills": len(item["sma"]["hypothetical_fills"]), "hold_fills": len(item["buy_hold"]["hypothetical_fills"]),
            "sma_rejections": len(item["sma"]["rejected_orders"]), "hold_rejections": len(item["buy_hold"]["rejected_orders"]),
            "reference_entry_at": item["buy_hold"]["hypothetical_fills"][0]["executed_at"] if item["buy_hold"]["hypothetical_fills"] else None,
            "sma_minus_buy_hold_usd": item["sma_minus_buy_hold_usd"], "sma_minus_cash_usd": item["sma_minus_cash_usd"]}
            for item in value["scenarios"]]}
    return {**result, "summary_sha256": checksum(result)}


def validate_summary(value):
    if (not isinstance(value, dict) or value.get("protocol") != PROTOCOL or value.get("status") not in STATUSES
            or value.get("summary_sha256") != checksum({key: item for key, item in value.items() if key != "summary_sha256"})
            or not isinstance(value.get("scenarios"), list)):
        raise ValueError("Resumen de referencias y costes inválido o modificado.")
    expected = list(RATES) if value["status"] == "calculated" else []
    if [item.get("commission_rate") if isinstance(item, dict) else None for item in value["scenarios"]] != expected:
        raise ValueError("Cuadrícula de comisiones incompatible.")


def run_benchmark(*, history, output, capital, quantity):
    output = Path(output)
    output = safe_under(output.parent.resolve(), output.name)
    if output.exists():
        raise ValueError("La salida ya existe; utilizar un directorio nuevo.")
    daily, source, manifest_raw, daily_raw = load_history(history)
    value = {**calculate(daily, capital=capital, quantity=quantity), "source": source,
             "implementation_sha256": {name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in SOURCES}}
    value["result_sha256"] = checksum(value)
    raw = canonical(value)
    if len(raw) > MAX_RESULT:
        raise ValueError("Resultado de referencias demasiado grande.")
    summary = summary_of(value, sha256(raw).hexdigest())
    output.mkdir(parents=True)
    for name, body in (("benchmark.json", raw), ("input-manifest.json", manifest_raw), ("input-daily.json", daily_raw)):
        with (output / name).open("xb") as stream:
            stream.write(body)
    save_json(output / "summary.json", summary)
    return summary


def load_summary(directory):
    value = strict_json(read_bounded(safe_under(Path(directory), "summary.json"), 256 * 1024))
    validate_summary(value)
    return value


def load_benchmark(directory):
    directory = Path(directory)
    directory = safe_under(directory.parent.resolve(), directory.name)
    summary = load_summary(directory)
    raw = read_bounded(safe_under(directory, "benchmark.json"), MAX_RESULT)
    if sha256(raw).hexdigest() != summary["result_file_sha256"]:
        raise ValueError("El resultado de referencias no coincide con su huella.")
    value = strict_json(raw)
    if (not isinstance(value, dict) or value.get("protocol") != PROTOCOL
            or value.get("result_sha256") != checksum({key: item for key, item in value.items() if key != "result_sha256"})):
        raise ValueError("Resultado de referencias inválido o modificado.")
    try:
        for name, key, maximum in (("input-manifest.json", "manifest_sha256", 256 * 1024),
                                   ("input-daily.json", "daily_file_sha256", 8 * 1024 * 1024)):
            if sha256(read_bounded(safe_under(directory, name), maximum)).hexdigest() != value["source"][key]:
                raise ValueError("La copia de entrada no coincide con el cálculo de referencias.")
        if canonical(summary) != canonical(summary_of(value, sha256(raw).hexdigest())):
            raise ValueError("El resumen no coincide con el resultado conservado.")
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("Estructura de referencias inválida.") from error
    return value, summary
