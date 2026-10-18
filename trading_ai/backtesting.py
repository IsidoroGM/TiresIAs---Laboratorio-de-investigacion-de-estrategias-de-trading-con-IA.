"""Backtest educativo: una unidad base, compras, costes cero y referencia siguiente."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Context, Decimal, localcontext

from trading_ai.data import SUPPORTED_PAIRS
from trading_ai.strategies import Signal


@dataclass(frozen=True)
class Position:
    """Compra de una unidad base; distingue señal y ejecución simulada."""

    entry_signal_date: date
    entry_date: date
    entry_price: Decimal


@dataclass(frozen=True)
class Trade:
    """Posición cerrada y resultado en moneda cotizada, con costes cero."""

    position: Position
    exit_signal_date: date
    exit_date: date
    exit_price: Decimal
    pnl: Decimal


@dataclass(frozen=True)
class BacktestResult:
    pair: str
    quote_currency: str
    closed_trades: tuple[Trade, ...]
    open_position: Position | None
    realized_pnl: Decimal


def run_backtest(
    rates: Sequence[tuple[date, Decimal]], signals: Sequence[Signal], pair: str
) -> BacktestResult:
    """Ejecuta la señal de la posición i en la referencia i+1, si existe.

    Empieza sin posición, permite una compra de una unidad base y no piramida.
    Ignora entradas estando dentro y salidas estando fuera. La última señal no
    se ejecuta. No liquida ni valora la posición abierta al finalizar.
    El llamante debe alinear señales y referencias del mismo par por posición.
    Se rechazan fechas no crecientes, referencias no positivas y señales inválidas.
    No modela capital, margen, costes ni precios ejecutables: no es un bróker.
    """
    if pair not in SUPPORTED_PAIRS:
        raise ValueError(f"Par no admitido: {pair}.")
    if len(rates) != len(signals):
        raise ValueError("Referencias y señales deben tener la misma longitud.")
    previous_date = None
    for index, ((day, price), signal) in enumerate(zip(rates, signals)):
        if type(day) is not date:
            raise TypeError(f"Posición {index}: se requiere una fecha date sin hora.")
        if previous_date is not None and day <= previous_date:
            raise ValueError("Las fechas deben ser estrictamente crecientes, sin duplicados.")
        previous_date = day
        if not isinstance(price, Decimal):
            raise TypeError(f"Posición {index}: el precio debe ser Decimal.")
        if not price.is_finite() or price <= 0:
            raise ValueError(f"Posición {index}: el precio debe ser finito y positivo.")
        if not isinstance(signal, Signal):
            raise TypeError(f"Posición {index}: se requiere un valor de Signal.")

    position: Position | None = None
    trades: list[Trade] = []
    realized_pnl = Decimal("0")
    with localcontext(Context(prec=28)):
        for index in range(1, len(rates)):
            signal = signals[index - 1]
            signal_date = rates[index - 1][0]
            execution_date, execution_price = rates[index]
            if signal == Signal.ENTER_LONG and position is None:
                position = Position(signal_date, execution_date, execution_price)
            elif signal == Signal.EXIT_LONG and position is not None:
                pnl = execution_price - position.entry_price  # Una unidad base.
                trades.append(Trade(position, signal_date, execution_date, execution_price, pnl))
                realized_pnl += pnl
                position = None

    return BacktestResult(pair, pair.split("/")[1], tuple(trades), position, realized_pnl)
