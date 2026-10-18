<<<<<<< HEAD
"""Backtest educativo: tamaño configurable, costes y ejecución en referencia siguiente."""
=======
"""Backtest educativo: una unidad base, compras, costes cero y referencia siguiente."""
>>>>>>> 638028febb9f67c519664efb59553f8a56fc3b09

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
<<<<<<< HEAD
from decimal import Context, Decimal, ROUND_DOWN, localcontext
=======
from decimal import Context, Decimal, localcontext
>>>>>>> 638028febb9f67c519664efb59553f8a56fc3b09

from trading_ai.data import SUPPORTED_PAIRS
from trading_ai.strategies import Signal


@dataclass(frozen=True)
class Position:
<<<<<<< HEAD
    """Compra con cantidad en moneda base; distingue señal y ejecución simulada."""
=======
    """Compra de una unidad base; distingue señal y ejecución simulada."""
>>>>>>> 638028febb9f67c519664efb59553f8a56fc3b09

    entry_signal_date: date
    entry_date: date
    entry_price: Decimal
<<<<<<< HEAD
    entry_cost: Decimal = Decimal("0")
    quantity: Decimal = Decimal("1")
=======
>>>>>>> 638028febb9f67c519664efb59553f8a56fc3b09


@dataclass(frozen=True)
class Trade:
<<<<<<< HEAD
    """Posición cerrada; pnl descuenta entrada y salida, en moneda cotizada."""
=======
    """Posición cerrada y resultado en moneda cotizada, con costes cero."""
>>>>>>> 638028febb9f67c519664efb59553f8a56fc3b09

    position: Position
    exit_signal_date: date
    exit_date: date
    exit_price: Decimal
    pnl: Decimal
<<<<<<< HEAD
    exit_cost: Decimal = Decimal("0")

    @property
    def gross_pnl(self) -> Decimal:
        with localcontext(Context(prec=28)):
            return (self.exit_price * self.position.quantity
                    - self.position.entry_price * self.position.quantity)

    @property
    def costs(self) -> Decimal:
        with localcontext(Context(prec=28)):
            return self.position.entry_cost + self.exit_cost


@dataclass(frozen=True)
class EquityPoint:
    """Valoración posterior a la ejecución de cada observación."""

    date: date
    cash: Decimal
    position_value: Decimal
    equity: Decimal
    drawdown: Decimal
    drawdown_percent: Decimal
=======
>>>>>>> 638028febb9f67c519664efb59553f8a56fc3b09


@dataclass(frozen=True)
class BacktestResult:
    pair: str
    quote_currency: str
    closed_trades: tuple[Trade, ...]
    open_position: Position | None
    realized_pnl: Decimal
<<<<<<< HEAD
    cost_rate: Decimal = Decimal("0")
    initial_capital: Decimal = Decimal("1000")
    equity_curve: tuple[EquityPoint, ...] = ()
    rejected_entries: int = 0
    allocation_fraction: Decimal | None = None

    @property
    def final_equity(self) -> Decimal:
        return self.equity_curve[-1].equity if self.equity_curve else self.initial_capital

    @property
    def max_drawdown(self) -> Decimal:
        return max((point.drawdown for point in self.equity_curve), default=Decimal("0"))

    @property
    def max_drawdown_percent(self) -> Decimal:
        return max((point.drawdown_percent for point in self.equity_curve), default=Decimal("0"))

    @property
    def unrealized_pnl(self) -> Decimal:
        """Variación de precio de la posición abierta, sin simular su cierre."""
        if self.open_position is None or not self.equity_curve:
            return Decimal("0")
        with localcontext(Context(prec=28)):
            return (self.equity_curve[-1].position_value
                    - self.open_position.entry_price * self.open_position.quantity)

    @property
    def gross_realized_pnl(self) -> Decimal:
        with localcontext(Context(prec=28)):
            return sum((trade.gross_pnl for trade in self.closed_trades), Decimal("0"))

    @property
    def closed_costs(self) -> Decimal:
        with localcontext(Context(prec=28)):
            return sum((trade.costs for trade in self.closed_trades), Decimal("0"))

    @property
    def total_costs(self) -> Decimal:
        """Costes incurridos, incluida la entrada de una posición aún abierta."""
        with localcontext(Context(prec=28)):
            return self.closed_costs + (self.open_position.entry_cost if self.open_position else Decimal("0"))

    @property
    def pnl_after_incurred_costs(self) -> Decimal:
        """Cierres netos menos coste de entrada abierta; excluye su variación de precio."""
        with localcontext(Context(prec=28)):
            return self.realized_pnl - (self.open_position.entry_cost if self.open_position else Decimal("0"))


def validate_cost_rate(cost_rate: Decimal) -> None:
    """Fracción por ejecución: 0.001 significa 0.1 %, no una tarifa verificada."""
    if not isinstance(cost_rate, Decimal):
        raise TypeError("El coste debe ser Decimal.")
    if not cost_rate.is_finite() or not Decimal("0") <= cost_rate < Decimal("1"):
        raise ValueError("El coste debe ser finito, mayor o igual a cero y menor que 1.")


def validate_initial_capital(initial_capital: Decimal) -> None:
    if not isinstance(initial_capital, Decimal):
        raise TypeError("El capital inicial debe ser Decimal.")
    if not initial_capital.is_finite() or initial_capital <= 0:
        raise ValueError("El capital inicial debe ser finito y mayor que cero.")


def validate_allocation_fraction(allocation_fraction: Decimal | None) -> None:
    """None conserva una unidad fija; una fracción representa presupuesto, no riesgo."""
    if allocation_fraction is None:
        return
    if not isinstance(allocation_fraction, Decimal):
        raise TypeError("La asignación debe ser Decimal o None.")
    if not allocation_fraction.is_finite() or not Decimal("0") < allocation_fraction <= Decimal("1"):
        raise ValueError("La asignación debe ser finita, mayor que cero y como máximo 1.")


def _entry_quantity(cash: Decimal, price: Decimal, cost_rate: Decimal,
                    allocation_fraction: Decimal | None) -> Decimal:
    if allocation_fraction is None:
        return Decimal("1")
    # Al entrar estamos fuera del mercado: capital disponible = efectivo actual.
    with localcontext(Context(prec=28, rounding=ROUND_DOWN)):
        budget = cash * allocation_fraction
        quantity = budget / (price * (1 + cost_rate))
    # La división y los productos pueden redondearse de forma diferente.
    # Ajustamos hacia abajo si el coste calculado excede el presupuesto.
    while quantity > 0:
        notional = price * quantity
        if notional + notional * cost_rate <= budget:
            break
        quantity = quantity.next_minus()
    return quantity


def run_backtest(
    rates: Sequence[tuple[date, Decimal]], signals: Sequence[Signal], pair: str,
    *, cost_rate: Decimal = Decimal("0"),
    initial_capital: Decimal = Decimal("1000"),
    allocation_fraction: Decimal | None = None,
) -> BacktestResult:
    """Ejecuta la señal de la posición i en la referencia i+1, si existe.

    Empieza sin posición y no piramida. None compra una unidad base; una fracción
    asigna esa parte del efectivo actual, incluyendo el coste, a cada nueva entrada.
    Cantidad fraccionaria calculada al ejecutar y constante hasta el cierre.
    Ignora entradas estando dentro y salidas estando fuera. La última señal no
    se ejecuta. Valora la posición abierta en cada observación sin liquidarla.
    El llamante debe alinear señales y referencias del mismo par por posición.
    Se rechazan fechas no crecientes, referencias no positivas y señales inválidas.
    Coste por ejecución = referencia * cantidad * cost_rate, en moneda cotizada. Solo cobra
    acciones ejecutadas; realized_pnl es neto de costes de los cierres.
    Capital en moneda cotizada. Compra solo con saldo para precio más coste;
    una entrada rechazada no queda pendiente. Sin préstamos ni margen.
    Curva posterior a ejecución; máximo previo incluye el capital inicial.
    """
    validate_cost_rate(cost_rate)
    validate_initial_capital(initial_capital)
    validate_allocation_fraction(allocation_fraction)
=======


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
>>>>>>> 638028febb9f67c519664efb59553f8a56fc3b09
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
<<<<<<< HEAD
    cash = peak = initial_capital
    curve: list[EquityPoint] = []
    rejected_entries = 0
    with localcontext(Context(prec=28)):
        for index, (execution_date, execution_price) in enumerate(rates):
            signal = signals[index - 1] if index else Signal.NONE
            signal_date = rates[index - 1][0] if index else execution_date
            if signal == Signal.ENTER_LONG and position is None:
                quantity = _entry_quantity(cash, execution_price, cost_rate, allocation_fraction)
                entry_notional = execution_price * quantity
                entry_cost = entry_notional * cost_rate
                required_cash = entry_notional + entry_cost
                if quantity > 0 and required_cash <= cash:
                    cash -= required_cash
                    position = Position(signal_date, execution_date, execution_price, entry_cost, quantity)
                else:
                    rejected_entries += 1
            elif signal == Signal.EXIT_LONG and position is not None:
                exit_notional = execution_price * position.quantity
                exit_cost = exit_notional * cost_rate
                pnl = (exit_notional - position.entry_price * position.quantity) - (position.entry_cost + exit_cost)
                trades.append(Trade(position, signal_date, execution_date, execution_price, pnl, exit_cost))
                realized_pnl += pnl
                cash += exit_notional - exit_cost
                position = None
            position_value = execution_price * position.quantity if position is not None else Decimal("0")
            equity = cash + position_value
            peak = max(peak, equity)
            drawdown = peak - equity
            curve.append(EquityPoint(execution_date, cash, position_value, equity,
                                     drawdown, drawdown / peak * 100))

    return BacktestResult(pair, pair.split("/")[1], tuple(trades), position, realized_pnl,
                          cost_rate, initial_capital, tuple(curve), rejected_entries, allocation_fraction)
=======
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
>>>>>>> 638028febb9f67c519664efb59553f8a56fc3b09
