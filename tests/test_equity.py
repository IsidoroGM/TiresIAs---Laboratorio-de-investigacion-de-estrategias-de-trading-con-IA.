"""Contabilidad de efectivo y valoración diaria con drawdowns conocidos."""

from datetime import date, timedelta
from decimal import Decimal, localcontext

import pytest

from trading_ai.backtesting import run_backtest
from trading_ai.strategies import Signal


def rates(*prices):
    return [(date(2026, 1, 1) + timedelta(days=i), Decimal(price))
            for i, price in enumerate(prices)]


def test_known_curve_accounts_for_both_costs_and_marks_open_position():
    result = run_backtest(rates("90", "100", "80", "120", "110"),
                          [Signal.ENTER_LONG, Signal.NONE, Signal.NONE, Signal.EXIT_LONG, Signal.NONE],
                          "EUR/USD", cost_rate=Decimal("0.01"))
    assert [p.cash for p in result.equity_curve] == list(map(Decimal, ["1000", "899", "899", "899", "1007.9"]))
    assert [p.position_value for p in result.equity_curve] == list(map(Decimal, ["0", "100", "80", "120", "0"]))
    assert [p.equity for p in result.equity_curve] == list(map(Decimal, ["1000", "999", "979", "1019", "1007.9"]))
    assert [p.drawdown for p in result.equity_curve] == list(map(Decimal, ["0", "1", "21", "0", "11.1"]))
    assert result.max_drawdown == Decimal("21")
    assert result.max_drawdown_percent == Decimal("2.1")
    assert result.final_equity == result.initial_capital + result.realized_pnl
    assert result.unrealized_pnl == 0


def test_open_losses_count_in_equity_even_without_closed_trades():
    result = run_backtest(rates("90", "100", "70"),
                          [Signal.ENTER_LONG, Signal.NONE, Signal.EXIT_LONG],
                          "USD/JPY", initial_capital=Decimal("200"), cost_rate=Decimal("0.01"))
    assert result.realized_pnl == 0 and result.closed_trades == ()
    assert result.open_position is not None
    assert result.unrealized_pnl == Decimal("-30")
    assert result.final_equity == Decimal("169")
    assert result.max_drawdown == Decimal("31")
    assert result.max_drawdown_percent == Decimal("15.5")
    assert result.final_equity == result.initial_capital + result.pnl_after_incurred_costs + result.unrealized_pnl


def test_insufficient_cash_includes_entry_cost_and_does_not_charge_rejection():
    result = run_backtest(rates("99", "100", "110"),
                          [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE],
                          "EUR/USD", initial_capital=Decimal("100"), cost_rate=Decimal("0.01"))
    assert result.rejected_entries == 1
    assert result.total_costs == 0 and result.closed_trades == () and result.open_position is None
    assert result.final_equity == Decimal("100") and result.max_drawdown == 0


def test_exact_cash_boundary_is_allowed_without_borrowing():
    result = run_backtest(rates("99", "100"), [Signal.ENTER_LONG, Signal.NONE],
                          "EUR/USD", initial_capital=Decimal("101"), cost_rate=Decimal("0.01"))
    assert result.open_position is not None and result.rejected_entries == 0
    assert result.equity_curve[-1].cash == 0
    assert result.final_equity == Decimal("100")


def test_rejected_signal_is_not_queued_but_new_signal_can_buy():
    result = run_backtest(rates("90", "110", "40", "45", "50"),
                          [Signal.ENTER_LONG, Signal.NONE, Signal.ENTER_LONG, Signal.NONE, Signal.NONE],
                          "EUR/USD", initial_capital=Decimal("100"))
    assert result.rejected_entries == 1
    assert result.equity_curve[2].position_value == 0  # No compra al bajar a 40.
    assert result.open_position.entry_price == Decimal("45")
    assert result.final_equity == Decimal("105")


def test_cash_is_reused_after_sale_and_never_negative():
    result = run_backtest(rates("90", "100", "110", "105", "115"),
                          [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE],
                          "EUR/USD", initial_capital=Decimal("100"))
    assert len(result.closed_trades) == 2 and result.rejected_entries == 0
    assert result.final_equity == Decimal("120")
    assert all(p.cash >= 0 and p.equity == p.cash + p.position_value for p in result.equity_curve)


def test_absolute_and_percentage_drawdown_can_peak_at_different_times():
    result = run_backtest(rates("10", "10", "20", "1", "110", "80"),
                          [Signal.ENTER_LONG] + [Signal.NONE] * 5,
                          "EUR/USD", initial_capital=Decimal("100"))
    assert result.max_drawdown == Decimal("30")  # De 200 a 170.
    assert result.max_drawdown_percent == Decimal("19") / Decimal("110") * 100
    assert result.equity_curve[-1].drawdown_percent == Decimal("15")


@pytest.mark.parametrize("size", [0, 1, 4])
def test_empty_or_flat_account_has_zero_drawdown(size):
    result = run_backtest(rates(*(["1"] * size)), [Signal.NONE] * size, "EUR/USD",
                          initial_capital=Decimal("123"))
    assert len(result.equity_curve) == size
    assert result.final_equity == Decimal("123")
    assert result.max_drawdown == result.max_drawdown_percent == result.unrealized_pnl == 0


@pytest.mark.parametrize("bad", [Decimal("0"), Decimal("-1"), Decimal("NaN"),
                                 Decimal("sNaN"), Decimal("Infinity")])
def test_rejects_invalid_initial_capital(bad):
    with pytest.raises(ValueError, match="capital inicial debe ser finito"):
        run_backtest([], [], "EUR/USD", initial_capital=bad)


@pytest.mark.parametrize("bad", [1000, 1000.0, "1000", None, True])
def test_requires_decimal_capital(bad):
    with pytest.raises(TypeError, match="capital inicial debe ser Decimal"):
        run_backtest([], [], "EUR/USD", initial_capital=bad)


def test_equity_prefix_does_not_change_with_future_data():
    observations = rates("90", "100", "70", "120", "110")
    signals = [Signal.ENTER_LONG, Signal.NONE, Signal.NONE, Signal.EXIT_LONG, Signal.NONE]
    result = run_backtest(observations, signals, "EUR/USD", cost_rate=Decimal("0.01"))
    for end in range(len(observations) + 1):
        prefix = run_backtest(observations[:end], signals[:end], "EUR/USD", cost_rate=Decimal("0.01"))
        assert prefix.equity_curve == result.equity_curve[:end]


def test_accounting_uses_local_decimal_context():
    observations = rates("1", "1.2345", "1.9999")
    signals = [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE]
    expected = run_backtest(observations, signals, "EUR/USD", cost_rate=Decimal("0.001"))
    with localcontext() as context:
        context.prec = 2
        actual = run_backtest(observations, signals, "EUR/USD", cost_rate=Decimal("0.001"))
        assert actual == expected
        assert actual.final_equity == Decimal("1000.7621656")
        assert context.prec == 2
