"""Operaciones conocidas y ejecución posterior a la señal, sin red."""

from datetime import date, datetime, timedelta
from decimal import Decimal, localcontext

import pytest

from trading_ai.backtesting import Position, run_backtest
from trading_ai.strategies import Signal


def observations(*prices):
    return [(date(2026, 1, 1) + timedelta(days=i), Decimal(p)) for i, p in enumerate(prices)]


@pytest.mark.parametrize("exit_price, expected", [("15", "3"), ("9", "-3"), ("12", "0")])
def test_known_profit_loss_and_execution_delay(exit_price, expected):
    rates = observations("10", "12", "99", exit_price)
    signals = [Signal.ENTER_LONG, Signal.NONE, Signal.EXIT_LONG, Signal.NONE]
    original_rates, original_signals = rates.copy(), signals.copy()
    result = run_backtest(rates, signals, "EUR/USD")
    assert result.quote_currency == "USD"
    assert result.open_position is None
    assert result.realized_pnl == Decimal(expected)
    trade, = result.closed_trades
    assert trade.position == Position(rates[0][0], rates[1][0], Decimal("12"))
    assert trade.exit_signal_date == rates[2][0]
    assert trade.exit_date == rates[3][0]
    assert trade.exit_price == Decimal(exit_price)
    assert trade.pnl == Decimal(expected)
    assert rates == original_rates and signals == original_signals


def test_ignores_entries_while_open_and_exits_while_flat():
    rates = observations("10", "11", "12", "13", "14", "15", "16")
    signals = [Signal.EXIT_LONG, Signal.ENTER_LONG, Signal.ENTER_LONG,
               Signal.EXIT_LONG, Signal.EXIT_LONG, Signal.NONE, Signal.NONE]
    result = run_backtest(rates, signals, "GBP/USD")
    assert len(result.closed_trades) == 1
    assert result.closed_trades[0].position.entry_price == Decimal("12")
    assert result.closed_trades[0].exit_price == Decimal("14")
    assert result.realized_pnl == Decimal("2")
    assert result.open_position is None


def test_open_position_is_preserved_and_excluded_from_realized_pnl():
    rates = observations("10", "12", "99")
    result = run_backtest(rates, [Signal.ENTER_LONG, Signal.NONE, Signal.EXIT_LONG], "EUR/USD")
    assert result.open_position == Position(rates[0][0], rates[1][0], Decimal("12"))
    assert result.closed_trades == ()
    assert result.realized_pnl == Decimal("0")


def test_last_entry_has_no_execution():
    result = run_backtest(observations("10", "12"), [Signal.NONE, Signal.ENTER_LONG], "EUR/USD")
    assert result.open_position is None and result.closed_trades == ()


@pytest.mark.parametrize("size", [0, 1])
def test_empty_and_single_observation(size):
    result = run_backtest(observations(*(["10"] * size)), [Signal.ENTER_LONG] * size, "EUR/USD")
    assert result.closed_trades == () and result.open_position is None
    assert result.realized_pnl == 0


def test_no_signals_means_no_trades():
    result = run_backtest(observations("10", "20", "30"), [Signal.NONE] * 3, "EUR/USD")
    assert result.closed_trades == () and result.open_position is None


def test_multiple_trades_sum_only_closed_results():
    rates = observations("10", "11", "13", "20", "18", "30", "100")
    signals = [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.ENTER_LONG,
               Signal.EXIT_LONG, Signal.ENTER_LONG, Signal.NONE, Signal.NONE]
    result = run_backtest(rates, signals, "USD/JPY")
    assert [trade.pnl for trade in result.closed_trades] == [Decimal("2"), Decimal("-2")]
    assert result.realized_pnl == 0
    assert result.quote_currency == "JPY"
    assert result.open_position.entry_price == Decimal("30")


@pytest.mark.parametrize("pair, currency", [("EUR/USD", "USD"), ("GBP/USD", "USD"),
                                          ("USD/JPY", "JPY"), ("USD/CHF", "CHF")])
def test_reports_quote_currency(pair, currency):
    assert run_backtest([], [], pair).quote_currency == currency


def test_next_observation_not_next_calendar_day():
    rates = [(date(2026, 1, 2), Decimal("10")), (date(2026, 1, 5), Decimal("12"))]
    result = run_backtest(rates, [Signal.ENTER_LONG, Signal.NONE], "EUR/USD")
    assert result.open_position.entry_date == date(2026, 1, 5)


def test_rejects_unknown_pair():
    with pytest.raises(ValueError, match="Par no admitido"):
        run_backtest([], [], "EUR/JPY")


def test_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="misma longitud"):
        run_backtest(observations("1"), [], "EUR/USD")


@pytest.mark.parametrize("second_date", [date(2026, 1, 1), date(2025, 12, 31)])
def test_rejects_duplicate_or_unsorted_dates(second_date):
    rates = [(date(2026, 1, 1), Decimal("1")), (second_date, Decimal("2"))]
    with pytest.raises(ValueError, match="estrictamente crecientes"):
        run_backtest(rates, [Signal.NONE] * 2, "EUR/USD")


@pytest.mark.parametrize("bad", ["2026-01-01", datetime(2026, 1, 1), None])
def test_rejects_wrong_date_type(bad):
    with pytest.raises(TypeError, match="fecha date"):
        run_backtest([(bad, Decimal("1"))], [Signal.NONE], "EUR/USD")


@pytest.mark.parametrize("bad", ["0", "-1", "NaN", "sNaN", "Infinity", "-Infinity"])
def test_rejects_invalid_price(bad):
    with pytest.raises(ValueError, match="finito y positivo"):
        run_backtest(observations(bad), [Signal.NONE], "EUR/USD")


@pytest.mark.parametrize("bad", [1, 1.2, "1", None])
def test_rejects_nondecimal_price(bad):
    with pytest.raises(TypeError, match="precio debe ser Decimal"):
        run_backtest([(date(2026, 1, 1), bad)], [Signal.NONE], "EUR/USD")


@pytest.mark.parametrize("bad", ["enter_long", None, True])
def test_rejects_invalid_signal_even_on_last_observation(bad):
    with pytest.raises(TypeError, match="valor de Signal"):
        run_backtest(observations("1"), [bad], "EUR/USD")


def test_decimal_context_is_local():
    with localcontext() as context:
        context.prec = 2
        result = run_backtest(observations("1", "1.2345", "1.9999"),
                              [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE], "EUR/USD")
        assert result.realized_pnl == Decimal("0.7654")
        assert context.prec == 2


def test_future_data_cannot_change_completed_trades():
    rates = observations("10", "11", "12", "13", "14", "15")
    signals = [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE,
               Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE]
    full = run_backtest(rates, signals, "EUR/USD")
    for end in range(len(rates) + 1):
        prefix = run_backtest(rates[:end], signals[:end], "EUR/USD")
        expected = tuple(trade for trade in full.closed_trades if trade.exit_date in [d for d, _ in rates[:end]])
        assert prefix.closed_trades == expected
    changed = rates[:3] + observations("1000", "2000", "3000")
    changed = [(rates[i][0], price) for i, (_, price) in enumerate(changed)]
    assert run_backtest(changed, signals, "EUR/USD").closed_trades[0] == full.closed_trades[0]
