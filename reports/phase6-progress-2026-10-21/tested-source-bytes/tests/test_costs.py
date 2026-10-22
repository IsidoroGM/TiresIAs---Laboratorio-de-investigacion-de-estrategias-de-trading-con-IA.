"""Costes por ejecución y su efecto en cierres y posiciones abiertas."""

from datetime import date, timedelta
from decimal import Decimal, localcontext

import pytest

from trading_ai.backtesting import run_backtest
from trading_ai.metrics import calculate_metrics
from trading_ai.strategies import Signal


def rates(*values):
    return [(date(2026, 1, 1) + timedelta(days=i), Decimal(value))
            for i, value in enumerate(values)]


def test_known_entry_exit_costs_and_net_pnl():
    result = run_backtest(rates("99", "100", "110"),
                          [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE],
                          "EUR/USD", cost_rate=Decimal("0.01"))
    trade, = result.closed_trades
    assert trade.position.entry_cost == Decimal("1")
    assert trade.exit_cost == Decimal("1.1")
    assert trade.gross_pnl == result.gross_realized_pnl == Decimal("10")
    assert trade.costs == result.closed_costs == result.total_costs == Decimal("2.1")
    assert trade.pnl == result.realized_pnl == result.pnl_after_incurred_costs == Decimal("7.9")


def test_zero_cost_preserves_previous_results():
    observations = rates("99", "100", "110")
    signals = [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE]
    baseline = run_backtest(observations, signals, "EUR/USD")
    assert run_backtest(observations, signals, "EUR/USD", cost_rate=Decimal("0")) == baseline
    assert baseline.realized_pnl == Decimal("10") and baseline.total_costs == 0


def test_small_gross_gain_becomes_net_loss_in_metrics():
    result = run_backtest(rates("99", "100", "101"),
                          [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE],
                          "EUR/USD", cost_rate=Decimal("0.01"))
    m = calculate_metrics(result)
    assert result.gross_realized_pnl == 1
    assert m.total_pnl == Decimal("-1.01")
    assert m.winning_trades == 0 and m.losing_trades == 1
    assert m.win_rate_percent == 0 and m.profit_factor == 0


def test_open_entry_cost_is_incurred_without_inventing_exit():
    result = run_backtest(rates("99", "100", "200"),
                          [Signal.ENTER_LONG, Signal.NONE, Signal.EXIT_LONG],
                          "USD/JPY", cost_rate=Decimal("0.01"))
    assert result.open_position.entry_cost == Decimal("1")
    assert result.closed_trades == () and result.realized_pnl == 0
    assert result.closed_costs == 0 and result.total_costs == Decimal("1")
    assert result.pnl_after_incurred_costs == Decimal("-1")
    assert calculate_metrics(result).total_trades == 0


def test_ignored_signals_and_unexecuted_last_entry_have_no_cost():
    result = run_backtest(rates("90", "95", "100", "105", "110", "115"),
                          [Signal.EXIT_LONG, Signal.ENTER_LONG, Signal.ENTER_LONG,
                           Signal.EXIT_LONG, Signal.EXIT_LONG, Signal.ENTER_LONG],
                          "EUR/USD", cost_rate=Decimal("0.01"))
    assert len(result.closed_trades) == 1 and result.open_position is None
    assert result.total_costs == Decimal("2.1")  # Solo compra a 100 y venta a 110.


def test_total_costs_include_closed_trades_and_open_entry_once():
    result = run_backtest(rates("90", "100", "110", "200"),
                          [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.ENTER_LONG, Signal.NONE],
                          "EUR/USD", cost_rate=Decimal("0.01"))
    assert result.closed_costs == Decimal("2.1")
    assert result.total_costs == Decimal("4.1")
    assert result.realized_pnl == Decimal("7.9")
    assert result.pnl_after_incurred_costs == Decimal("5.9")


@pytest.mark.parametrize("bad", [Decimal("-0.01"), Decimal("1"), Decimal("2"),
                                 Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity")])
def test_invalid_rates_rejected_even_without_trades(bad):
    with pytest.raises(ValueError, match="coste debe ser finito"):
        run_backtest([], [], "EUR/USD", cost_rate=bad)


@pytest.mark.parametrize("bad", [0.01, "0.01", 0, None, True])
def test_rate_must_be_decimal(bad):
    with pytest.raises(TypeError, match="coste debe ser Decimal"):
        run_backtest([], [], "EUR/USD", cost_rate=bad)


def test_costs_are_independent_of_external_precision():
    with localcontext() as context:
        context.prec = 2
        result = run_backtest(rates("1", "1.2345", "1.9999"),
                              [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE],
                              "USD/CHF", cost_rate=Decimal("0.001"))
        assert result.total_costs == Decimal("0.0032344")
        assert result.realized_pnl == Decimal("0.7621656")
        assert result.gross_realized_pnl == Decimal("0.7654")
        assert context.prec == 2


def test_higher_costs_reduce_net_pnl_without_changing_execution():
    observations = rates("90", "100", "110")
    signals = [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE]
    results = [run_backtest(observations, signals, "EUR/USD", cost_rate=Decimal(rate))
               for rate in ("0", "0.001", "0.01")]
    assert results[0].realized_pnl > results[1].realized_pnl > results[2].realized_pnl
    assert all(result.closed_trades[0].exit_price == Decimal("110") for result in results)
