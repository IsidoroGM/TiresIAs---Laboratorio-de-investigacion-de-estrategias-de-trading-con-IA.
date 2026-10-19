"""EMA: semilla explícita, recurrencia conocida y señales causales."""

from dataclasses import FrozenInstanceError
from decimal import Decimal, ROUND_DOWN, localcontext

import pytest

from trading_ai.indicators import exponential_moving_average
from trading_ai.strategies import EmaCrossoverStrategy, Signal, create_strategy


def test_ema_known_seed_recurrence_and_no_mutation():
    values = [Decimal(n) for n in (2, 4, 6, 10, 2)]
    original = values.copy()
    # Periodo 3: semilla 4; alfa 1/2; siguientes 7 y 4.5.
    assert exponential_moving_average(values, 3) == [None, None, Decimal(4), Decimal(7), Decimal("4.5")]
    assert values == original


def test_ema_empty_warmup_and_period_one():
    assert exponential_moving_average([], 3) == []
    assert exponential_moving_average([Decimal(2)], 3) == [None]
    values = [Decimal("-1.25"), Decimal("0"), Decimal("3.75")]
    assert exponential_moving_average(values, 1) == values
    assert exponential_moving_average(values, 1) is not values
    assert exponential_moving_average([Decimal(7)] * 5, 3) == [None, None] + [Decimal(7)] * 3


@pytest.mark.parametrize("window, error", [(0, ValueError), (-1, ValueError),
                                          (True, TypeError), (2.0, TypeError), (None, TypeError)])
def test_ema_rejects_invalid_period_even_without_data(window, error):
    with pytest.raises(error):
        exponential_moving_average([], window)


@pytest.mark.parametrize("value, error", [(1.5, TypeError), (True, TypeError), (None, TypeError),
                                         (Decimal("NaN"), ValueError), (Decimal("Infinity"), ValueError)])
def test_ema_validates_all_values_during_warmup(value, error):
    with pytest.raises(error):
        exponential_moving_average([Decimal(1), value], 60)


def test_ema_uses_local_decimal_context():
    prices = [Decimal("1.234567890123456789"), Decimal("2.34567890123456789"),
              Decimal("7.4567890123456789"), Decimal("2.567890123456789")]
    expected = exponential_moving_average(prices, 2)
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        assert exponential_moving_average(prices, 2) == expected
        assert context.prec == 6 and context.rounding == ROUND_DOWN


def test_ema_strategy_known_crosses_and_stateless_reuse():
    strategy = EmaCrossoverStrategy(1, 3)
    prices = tuple(Decimal(n) for n in (3, 2, 1, 2, 3, 2, 1))
    # EMA lenta: None, None, 2, 2, 2.5, 2.25, 1.625.
    expected = [Signal.NONE] * 4 + [Signal.ENTER_LONG, Signal.EXIT_LONG, Signal.NONE]
    assert strategy.name == "EMA1/EMA3"
    assert strategy.generate_signals(prices) == expected
    assert strategy.generate_signals(()) == []
    assert strategy.generate_signals(prices) == expected
    with pytest.raises(FrozenInstanceError):
        strategy.fast_window = 2


@pytest.mark.parametrize("fast, slow", [(1, 3), (20, 60)])
def test_ema_indicator_and_strategy_do_not_use_future_prices(fast, slow):
    prices = [Decimal(n) for n in list(range(1, 81)) + list(range(80, 0, -1)) + list(range(1, 81))]
    strategy = EmaCrossoverStrategy(fast, slow)
    signals = strategy.generate_signals(prices)
    averages = exponential_moving_average(prices, slow)
    assert len(signals) == len(prices) and signals[:slow] == [Signal.NONE] * slow
    assert Signal.ENTER_LONG in signals and Signal.EXIT_LONG in signals
    for end in (0, slow - 1, slow, slow + 1, 100, 180, len(prices)):
        assert exponential_moving_average(prices[:end], slow) == averages[:end]
        assert strategy.generate_signals(prices[:end]) == signals[:end]
    changed = prices[:180] + [Decimal("10000")] * 60
    assert strategy.generate_signals(changed)[:180] == signals[:180]


@pytest.mark.parametrize("fast, slow, error", [(20, 20, ValueError), (60, 20, ValueError),
                                              (0, 60, ValueError), (True, 60, TypeError)])
def test_ema_strategy_validates_configuration(fast, slow, error):
    with pytest.raises(error):
        EmaCrossoverStrategy(fast, slow)


def test_strategy_selection_and_invalid_name():
    assert create_strategy("sma").name == "SMA20/SMA60"
    assert create_strategy("ema", 10, 40).name == "EMA10/EMA40"
    with pytest.raises(ValueError, match="no admitida"):
        create_strategy("unknown")
