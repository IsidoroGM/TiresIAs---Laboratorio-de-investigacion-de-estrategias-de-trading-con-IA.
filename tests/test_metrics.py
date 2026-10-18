"""Métricas con resultados calculados a mano y casos sin denominador válido."""

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext

import pytest

from trading_ai.backtesting import BacktestResult, Position, Trade, run_backtest
from trading_ai.metrics import calculate_metrics
from trading_ai.strategies import Signal


def result_with_pnls(*pnls):
    trades = []
    for index, value in enumerate(pnls):
        day = date(2026, 1, 1) + timedelta(days=4 * index)
        position = Position(day, day + timedelta(days=1), Decimal("100"))
        pnl = Decimal(value)
        trades.append(Trade(position, day + timedelta(days=2), day + timedelta(days=3),
                            Decimal("100") + pnl, pnl))
    return BacktestResult("EUR/USD", "USD", tuple(trades), None,
                          sum((trade.pnl for trade in trades), Decimal("0")))


def test_known_metrics_include_breakeven_in_win_rate():
    result = result_with_pnls("6", "4", "-2", "0")
    metrics = calculate_metrics(result)
    assert (metrics.total_trades, metrics.winning_trades,
            metrics.losing_trades, metrics.breakeven_trades) == (4, 2, 1, 1)
    assert metrics.win_rate_percent == Decimal("50")
    assert metrics.total_pnl == Decimal("8")
    assert metrics.average_pnl == Decimal("2")
    assert metrics.gross_profit == Decimal("10")
    assert metrics.gross_loss == Decimal("2")
    assert metrics.profit_factor == Decimal("5")
    assert metrics.pair == "EUR/USD" and metrics.quote_currency == "USD"
    assert not metrics.has_open_position
    assert result == result_with_pnls("6", "4", "-2", "0")


def test_no_closed_trades_has_unavailable_ratios():
    metrics = calculate_metrics(result_with_pnls())
    assert metrics.total_trades == metrics.winning_trades == metrics.losing_trades == metrics.breakeven_trades == 0
    assert metrics.total_pnl == metrics.gross_profit == metrics.gross_loss == 0
    assert metrics.win_rate_percent is None
    assert metrics.average_pnl is None
    assert metrics.profit_factor is None


@pytest.mark.parametrize("pnls, expected_rate, expected_average, expected_factor", [
    (("2", "4"), "100", "3", None),
    (("-2", "-4"), "0", "-3", "0"),
    (("0", "0"), "0", "0", None),
    (("2", "-2"), "50", "0", "1"),
    (("1", "-4"), "50", "-1.5", "0.25"),
])
def test_edge_cases(pnls, expected_rate, expected_average, expected_factor):
    metrics = calculate_metrics(result_with_pnls(*pnls))
    assert metrics.win_rate_percent == Decimal(expected_rate)
    assert metrics.average_pnl == Decimal(expected_average)
    assert metrics.profit_factor == (Decimal(expected_factor) if expected_factor is not None else None)
    assert metrics.winning_trades + metrics.losing_trades + metrics.breakeven_trades == metrics.total_trades


@pytest.mark.parametrize("pnls", [(), ("6", "-2")])
def test_open_position_is_flagged_but_not_counted(pnls):
    result = result_with_pnls(*pnls)
    position = Position(date(2026, 10, 1), date(2026, 10, 2), Decimal("9999"))
    expected = replace(calculate_metrics(result), has_open_position=True)
    assert calculate_metrics(replace(result, open_position=position)) == expected


def test_currency_and_integration_with_backtest():
    rates = [(date(2026, 1, 1) + timedelta(days=i), Decimal(value))
             for i, value in enumerate((10, 12, 99, 15))]
    result = run_backtest(rates, [Signal.ENTER_LONG, Signal.NONE, Signal.EXIT_LONG, Signal.NONE], "USD/JPY")
    metrics = calculate_metrics(result)
    assert metrics.pair == "USD/JPY" and metrics.quote_currency == "JPY"
    assert metrics.total_trades == 1
    assert metrics.total_pnl == metrics.average_pnl == Decimal("3")
    assert metrics.win_rate_percent == 100
    assert metrics.profit_factor is None


def test_results_are_independent_of_external_decimal_context():
    result = result_with_pnls("2", "-1", "0")
    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        metrics = calculate_metrics(result)
        assert metrics.average_pnl == Decimal("0.3333333333333333333333333333")
        assert metrics.win_rate_percent == Decimal("33.33333333333333333333333333")
        assert metrics.profit_factor == Decimal("2")
        assert context.prec == 2 and context.rounding == ROUND_DOWN


@pytest.mark.parametrize("bad", [Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_rejects_nonfinite_trade_pnl(bad):
    result = result_with_pnls("1")
    result = replace(result, closed_trades=(replace(result.closed_trades[0], pnl=bad),))
    with pytest.raises(ValueError, match="pnl debe ser finito"):
        calculate_metrics(result)


@pytest.mark.parametrize("bad", [1, 1.2, "1", None])
def test_rejects_nondecimal_trade_pnl(bad):
    result = result_with_pnls("1")
    result = replace(result, closed_trades=(replace(result.closed_trades[0], pnl=bad),))
    with pytest.raises(TypeError, match="pnl debe ser Decimal"):
        calculate_metrics(result)


@pytest.mark.parametrize("bad", [Decimal("7"), Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity")])
def test_rejects_inconsistent_or_nonfinite_total(bad):
    with pytest.raises(ValueError, match="coincidir con la suma"):
        calculate_metrics(replace(result_with_pnls("1"), realized_pnl=bad))


def test_rejects_nondecimal_total():
    with pytest.raises(TypeError, match="realized_pnl debe ser Decimal"):
        calculate_metrics(replace(result_with_pnls(), realized_pnl=0))
