"""Referencia local OHLC de los contratos Pine; no ejecuta ni interpreta Pine."""

from copy import deepcopy
import csv
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import io

from trading_ai.indicators import exponential_moving_average, simple_moving_average
from trading_ai.strategies import moving_average_crossover_signals
from trading_ai.tv_contracts import canonical, checksum, decimal_text, fields, instant, milliseconds, number, validate_contract


BAR_FIELDS = ("open_at", "close_at", "open", "high", "low", "close")


def validate_bars(values):
    if not isinstance(values, list) or not 1 <= len(values) <= 10000: raise ValueError("Se requieren entre 1 y 10000 velas.")
    bars, previous = [], None
    for value in values:
        fields(value, BAR_FIELDS, "vela")
        opening, closing = instant(value["open_at"]), instant(value["close_at"])
        if opening >= closing or previous is not None and opening < previous: raise ValueError("Velas repetidas, solapadas o fuera de orden.")
        prices = {name: number(value[name], name, positive=True) for name in ("open", "high", "low", "close")}
        if prices["high"] < max(prices.values()) or prices["low"] > min(prices.values()): raise ValueError("OHLC incompatible.")
        bars.append({"open_at": opening, "close_at": closing, **{name: decimal_text(price) for name, price in prices.items()}})
        previous = closing
    return bars


def read_bars_csv(raw):
    if not isinstance(raw, bytes) or len(raw) > 4 * 1024 * 1024: raise ValueError("CSV de velas mayor de 4 MiB.")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    if reader.fieldnames != list(BAR_FIELDS): raise ValueError("CSV normalizado requerido: " + ",".join(BAR_FIELDS))
    values = []
    for row in reader:
        values.append(row)
        if len(values) > 10000: raise ValueError("Demasiadas velas.")
    return validate_bars(values)


def run_reference(contract, values):
    c, bars = validate_contract(contract), validate_bars(values)
    with localcontext(Context(prec=28)):
        first = next((i for i, bar in enumerate(bars) if bar["open_at"] >= c["period"]["start"]), len(bars))
        selected = bars[first:]
        prices = [Decimal(bar["close"]) for bar in selected]
        average = exponential_moving_average if c["strategy"]["kind"] == "ema" else simple_moving_average
        fast, slow = [average(prices, c["strategy"][key]) for key in ("fast", "slow")]
        signals = moving_average_crossover_signals(fast, slow)
        cash = Decimal(c["account"]["initial_capital"])
        quantity, cost_rate = Decimal(c["account"]["quantity"]), Decimal(c["account"]["cost_rate"])
        position, entry_basis, pending, sequence = Decimal(0), Decimal(0), None, 0
        fills, rejected, curve, observations = [], [], [], []
        costs, realized, peak, max_drawdown, closed = Decimal(0), Decimal(0), cash, Decimal(0), 0
        for i, bar in enumerate(selected):
            if pending is not None:
                price, side = Decimal(bar["open"]), pending["side"]
                size = quantity if side == "buy" else position
                fee = size * price * cost_rate
                if side == "buy" and size * price + fee > cash:
                    rejected.append({**pending, "executed_at": bar["open_at"], "reason": "insufficient_cash_at_next_open"})
                else:
                    if side == "buy":
                        cash -= size * price + fee; position = size; entry_basis = size * price + fee
                    else:
                        cash += size * price - fee; realized += size * price - fee - entry_basis; position = Decimal(0); entry_basis = Decimal(0); closed += 1
                    costs += fee
                    fills.append({"protocol": "tiresias_simulated_fill_v1", "contract_sha256": checksum(c),
                                  **pending, "quantity": decimal_text(size), "price": decimal_text(price), "fee": decimal_text(fee),
                                  "currency": c["account"]["currency"], "executed_at": bar["open_at"]})
                pending = None
            raw_signal = signals[i].value
            eligible = bar["close_at"] < c["period"]["end"]
            observations.append({"open_at": bar["open_at"], "close_at": bar["close_at"],
                                 "fast": None if fast[i] is None else decimal_text(fast[i]),
                                 "slow": None if slow[i] is None else decimal_text(slow[i]), "signal": raw_signal, "eligible": eligible})
            side = "buy" if raw_signal == "enter_long" and position == 0 else "sell" if raw_signal == "exit_long" and position > 0 else None
            if eligible and side:
                sequence += 1
                pending = {"execution_id": ("TI-B-" if side == "buy" else "TI-S-") + str(milliseconds(bar["close_at"])),
                           "sequence": sequence, "side": side, "signal_at": bar["close_at"]}
            equity = cash + position * Decimal(bar["close"])
            peak = max(peak, equity)
            drawdown = (peak - equity) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
            curve.append({"at": bar["close_at"], "cash": decimal_text(cash), "quantity": decimal_text(position),
                          "price": bar["close"], "equity": decimal_text(equity), "drawdown_percent": decimal_text(drawdown)})
        final = Decimal(curve[-1]["equity"]) if curve else cash
        return {"protocol": "tiresias_ohlc_reference_v1", "contract_sha256": checksum(c),
                "bars_sha256": sha256(canonical(bars)).hexdigest(), "source_kind": "supplied_ohlc_not_ecb",
                "python_reference_only": True, "pine_executed": False, "observations": observations,
                "fills": fills, "rejected_orders": rejected, "pending_order": pending, "equity_curve": curve,
                "summary": {"initial_capital": c["account"]["initial_capital"], "currency": c["account"]["currency"],
                            "final_equity": decimal_text(final), "return_percent": decimal_text((final / Decimal(c["account"]["initial_capital"]) - 1) * 100),
                            "max_drawdown_percent": decimal_text(max_drawdown), "total_costs": decimal_text(costs),
                            "realized_pnl": decimal_text(realized), "closed_trades": closed, "open_quantity": decimal_text(position)}}


def compare_observations(reference, exported, *, tolerance="0.00000001"):
    """Coteja observaciones aportadas; no afirma haber ejecutado el código Pine."""
    tolerance = number(tolerance, "tolerancia", maximum=Decimal("0.01"))
    expected = reference["observations"]
    if not isinstance(exported, list) or len(exported) != len(expected): raise ValueError("Observaciones no alineadas.")
    differences = []
    for index, (left, right) in enumerate(zip(expected, exported)):
        fields(right, ("close_at", "fast", "slow", "signal"), "observación exportada")
        if instant(right["close_at"]) != left["close_at"]: raise ValueError("Fechas no equivalentes; no se comparan filas por posición sin alinear.")
        for key in ("fast", "slow"):
            a, b = left[key], right[key]
            if a is None or b is None:
                equal = a is b
            else:
                with localcontext(Context(prec=28)): equal = abs(number(a, key) - number(b, key)) <= tolerance
            if not equal: differences.append({"row": index + 1, "field": key, "python": a, "external": b})
        if right["signal"] != left["signal"]: differences.append({"row": index + 1, "field": "signal", "python": left["signal"], "external": right["signal"]})
    return {"protocol": "tiresias_observation_comparison_v1", "matches": not differences, "rows": len(expected),
            "tolerance": decimal_text(tolerance), "differences": differences, "external_origin_verified": False}
