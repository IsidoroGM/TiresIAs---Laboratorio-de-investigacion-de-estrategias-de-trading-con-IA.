"""Asignación por capital: presupuesto con costes, cantidades y contabilidad."""

from datetime import date, timedelta
from decimal import Decimal, localcontext

import pytest

from trading_ai.backtesting import run_backtest
from trading_ai.strategies import Signal


def rates(*prices):
    return [(date(2026, 1, 1) + timedelta(days=i), Decimal(price))
            for i, price in enumerate(prices)]


def test_known_quantity_costs_and_closed_profit():
    result = run_backtest(rates("9", "10", "12"),
                          [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE], "EUR/USD",
                          initial_capital=Decimal("1010"), cost_rate=Decimal("0.01"),
                          allocation_fraction=Decimal("0.1"))
    trade, = result.closed_trades
    assert trade.position.quantity == Decimal("10")
    assert trade.position.entry_cost == Decimal("1")
    assert trade.exit_cost == Decimal("1.2")
    assert trade.gross_pnl == Decimal("20")
    assert trade.pnl == result.realized_pnl == Decimal("17.8")
    assert result.final_equity == Decimal("1027.8")
    assert result.equity_curve[1].cash == Decimal("909")


def test_open_quantity_is_constant_and_unrealized_pnl_scales():
    result = run_backtest(rates("9", "10", "8"),
                          [Signal.ENTER_LONG, Signal.NONE, Signal.NONE], "EUR/USD",
                          initial_capital=Decimal("1010"), cost_rate=Decimal("0.01"),
                          allocation_fraction=Decimal("0.1"))
    assert result.open_position.quantity == Decimal("10")
    assert result.equity_curve[-1].cash == Decimal("909")
    assert result.equity_curve[-1].position_value == Decimal("80")
    assert result.unrealized_pnl == Decimal("-20")
    assert result.final_equity == Decimal("989")
    assert result.max_drawdown == Decimal("21")
    assert result.final_equity == result.initial_capital + result.pnl_after_incurred_costs + result.unrealized_pnl


@pytest.mark.parametrize("sale, next_quantity", [("20", "11"), ("5", "9.5")])
def test_each_new_entry_uses_current_cash(sale, next_quantity):
    result = run_backtest(rates("9", "10", sale, "10"),
                          [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.ENTER_LONG, Signal.NONE],
                          "EUR/USD", allocation_fraction=Decimal("0.1"))
    assert result.closed_trades[0].position.quantity == Decimal("10")
    assert result.open_position.quantity == Decimal(next_quantity)


def test_default_and_explicit_none_keep_one_unit_mode():
    observations = rates("9", "10", "12")
    signals = [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE]
    default = run_backtest(observations, signals, "EUR/USD")
    assert default == run_backtest(observations, signals, "EUR/USD", allocation_fraction=None)
    assert default.closed_trades[0].position.quantity == 1
    assert default.realized_pnl == 2


@pytest.mark.parametrize("fraction", ["0.1", "1"])
@pytest.mark.parametrize("price", ["3", "0.0000123456789", "123456.789"])
def test_rounding_respects_budget_and_no_borrowing(fraction, price):
    result = run_backtest(rates("1", price), [Signal.ENTER_LONG, Signal.NONE], "USD/JPY",
                          initial_capital=Decimal("1000"), cost_rate=Decimal("0.001"),
                          allocation_fraction=Decimal(fraction))
    p = result.open_position
    budget = Decimal("1000") * Decimal(fraction)
    used = p.entry_price * p.quantity + p.entry_cost
    assert 0 < used <= budget
    assert budget - used < Decimal("1e-23")
    assert result.rejected_entries == 0 and result.equity_curve[-1].cash >= 0


def test_fractional_quantity_can_buy_when_one_unit_is_unaffordable():
    observations = rates("1", "100")
    signals = [Signal.ENTER_LONG, Signal.NONE]
    fixed = run_backtest(observations, signals, "EUR/USD", initial_capital=Decimal("10"))
    fractional = run_backtest(observations, signals, "EUR/USD", initial_capital=Decimal("10"),
                              allocation_fraction=Decimal("0.1"))
    assert fixed.rejected_entries == 1
    assert fractional.open_position.quantity == Decimal("0.01")
    assert fractional.equity_curve[-1].cash == Decimal("9")


def test_same_relative_prices_produce_same_exposure_results():
    signals = [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE]
    a = run_backtest(rates("9", "10", "11"), signals, "EUR/USD", allocation_fraction=Decimal("0.1"))
    b = run_backtest(rates("900", "1000", "1100"), signals, "USD/JPY", allocation_fraction=Decimal("0.1"))
    assert a.final_equity == b.final_equity == Decimal("1010")
    assert a.closed_trades[0].position.quantity == Decimal("10")
    assert b.closed_trades[0].position.quantity == Decimal("0.1")


@pytest.mark.parametrize("bad", [Decimal("0"), Decimal("-0.1"), Decimal("1.01"),
                                 Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity")])
def test_rejects_invalid_fraction(bad):
    with pytest.raises(ValueError, match="asignación debe ser finita"):
        run_backtest([], [], "EUR/USD", allocation_fraction=bad)


@pytest.mark.parametrize("bad", [0.1, "0.1", 1, True])
def test_requires_decimal_fraction(bad):
    with pytest.raises(TypeError, match="asignación debe ser Decimal"):
        run_backtest([], [], "EUR/USD", allocation_fraction=bad)


def test_external_context_does_not_change_sizing_or_accounting():
    observations = rates("1", "3", "4")
    signals = [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE]
    options = {"allocation_fraction": Decimal("1"), "cost_rate": Decimal("0.001")}
    expected = run_backtest(observations, signals, "EUR/USD", **options)
    with localcontext() as context:
        context.prec = 2
        assert run_backtest(observations, signals, "EUR/USD", **options) == expected
        assert context.prec == 2


def test_future_observations_do_not_change_previous_sizes_or_curve():
    observations = rates("9", "10", "12", "9", "11")
    signals = [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.ENTER_LONG, Signal.NONE, Signal.NONE]
    result = run_backtest(observations, signals, "EUR/USD", allocation_fraction=Decimal("0.1"))
    for end in range(len(observations) + 1):
        prefix = run_backtest(observations[:end], signals[:end], "EUR/USD", allocation_fraction=Decimal("0.1"))
        assert prefix.equity_curve == result.equity_curve[:end]
