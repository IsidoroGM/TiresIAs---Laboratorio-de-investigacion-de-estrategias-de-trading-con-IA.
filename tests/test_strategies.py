"""Cruces conocidos, igualdades, huecos y causalidad de las señales."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from trading_ai.indicators import simple_moving_average
from trading_ai.strategies import (
    Signal, SmaCrossoverStrategy, Strategy, sma_crossover_signals, validate_sma_windows,
)


@pytest.mark.parametrize("previous, current, expected", [
    (1, 3, Signal.ENTER_LONG),
    (3, 1, Signal.EXIT_LONG),
    (2, 3, Signal.ENTER_LONG),
    (2, 1, Signal.EXIT_LONG),
    (1, 2, Signal.NONE),
    (3, 2, Signal.NONE),
    (2, 2, Signal.NONE),
    (3, 4, Signal.NONE),
    (1, 0, Signal.NONE),
])
def test_crossings_and_equalities(previous, current, expected):
    assert sma_crossover_signals(
        [Decimal(previous), Decimal(current)], [Decimal(2), Decimal(2)]
    ) == [Signal.NONE, expected]


@pytest.mark.parametrize("missing_index", range(4))
def test_missing_any_required_average_suppresses_signal(missing_index):
    values = [Decimal(1), Decimal(2), Decimal(3), Decimal(2)]
    values[missing_index] = None
    assert sma_crossover_signals(values[::2], values[1::2]) == [Signal.NONE] * 2


def test_does_not_bridge_missing_observations():
    fast = [Decimal(1), None, Decimal(3), Decimal(1)]
    slow = [Decimal(2)] * 4
    assert sma_crossover_signals(fast, slow) == [
        Signal.NONE, Signal.NONE, Signal.NONE, Signal.EXIT_LONG
    ]


def test_empty_and_single_observation():
    assert sma_crossover_signals([], []) == []
    assert sma_crossover_signals([Decimal(3)], [Decimal(2)]) == [Signal.NONE]


def test_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="misma longitud"):
        sma_crossover_signals([None], [])


@pytest.mark.parametrize("bad", [1, 1.2, "1", True])
@pytest.mark.parametrize("side", ["fast", "slow"])
def test_rejects_nondecimal_values(bad, side):
    fast, slow = [Decimal(1)], [Decimal(2)]
    (fast if side == "fast" else slow)[0] = bad
    with pytest.raises(TypeError, match="Decimal o None"):
        sma_crossover_signals(fast, slow)


@pytest.mark.parametrize("bad", ["NaN", "sNaN", "Infinity", "-Infinity"])
@pytest.mark.parametrize("side", ["fast", "slow"])
def test_rejects_nonfinite_values(bad, side):
    fast, slow = [Decimal(1)], [Decimal(2)]
    (fast if side == "fast" else slow)[0] = Decimal(bad)
    with pytest.raises(ValueError, match="valor finito"):
        sma_crossover_signals(fast, slow)


def test_sma_pipeline_known_result_and_no_mutation():
    prices = [Decimal(value) for value in (3, 2, 1, 2, 3, 2, 1)]
    fast = simple_moving_average(prices, 1)
    slow = simple_moving_average(prices, 2)
    original_fast, original_slow = fast.copy(), slow.copy()
    assert sma_crossover_signals(fast, slow) == [
        Signal.NONE, Signal.NONE, Signal.NONE, Signal.ENTER_LONG,
        Signal.NONE, Signal.EXIT_LONG, Signal.NONE,
    ]
    assert fast == original_fast and slow == original_slow


def test_equality_can_produce_repeated_entry_events():
    # El futuro gestor de posiciones decidirá si una entrada ya está abierta.
    fast = [Decimal(value) for value in (1, 3, 2, 3)]
    assert sma_crossover_signals(fast, [Decimal(2)] * 4) == [
        Signal.NONE, Signal.ENTER_LONG, Signal.NONE, Signal.ENTER_LONG
    ]


def test_default_strategy_has_no_lookahead():
    prices = [Decimal(value) for value in list(range(1, 81)) + list(range(80, 0, -1)) + list(range(1, 81))]

    def signals(values):
        return sma_crossover_signals(
            simple_moving_average(values, 20), simple_moving_average(values, 60)
        )

    full = signals(prices)
    assert Signal.ENTER_LONG in full and Signal.EXIT_LONG in full
    assert full[:60] == [Signal.NONE] * 60
    for end in (0, 1, 59, 60, 61, 100, 180, 220):
        assert signals(prices[:end]) == full[:end]
    assert signals(prices[:180] + [Decimal("10000")] * 60)[:180] == full[:180]


@pytest.mark.parametrize("fast, slow", [(1, 2), (10, 40), (20, 60)])
def test_valid_sma_windows(fast, slow):
    validate_sma_windows(fast, slow)


@pytest.mark.parametrize("fast, slow, error", [
    (0, 60, ValueError), (-1, 60, ValueError), (20, 0, ValueError),
    (20, -1, ValueError), (20, 20, ValueError), (60, 20, ValueError),
    (True, 60, TypeError), (20, False, TypeError), (1.5, 60, TypeError),
    (20, 60.0, TypeError), ("20", 60, TypeError), (20, None, TypeError),
])
def test_invalid_sma_windows(fast, slow, error):
    with pytest.raises(error, match="ventana"):
        validate_sma_windows(fast, slow)


def test_strategy_known_signals_and_reuse_without_mutation():
    strategy: Strategy = SmaCrossoverStrategy(1, 2)
    prices = [Decimal(value) for value in (3, 2, 1, 2, 3, 2, 1)]
    original = prices.copy()
    expected = [Signal.NONE, Signal.NONE, Signal.NONE, Signal.ENTER_LONG,
                Signal.NONE, Signal.EXIT_LONG, Signal.NONE]
    assert strategy.name == "SMA1/SMA2"
    signals = strategy.generate_signals(prices)
    assert signals == expected
    signals.clear()
    assert strategy.generate_signals(()) == []
    assert strategy.generate_signals(prices) == expected
    assert prices == original


@pytest.mark.parametrize("fast, slow", [(10, 40), (20, 60)])
def test_strategy_matches_existing_pipeline_and_is_causal(fast, slow):
    prices = tuple(Decimal(value) for value in
                   list(range(1, 81)) + list(range(80, 0, -1)) + list(range(1, 81)))
    strategy = SmaCrossoverStrategy(fast, slow)
    full = strategy.generate_signals(prices)
    assert len(full) == len(prices)
    assert full == sma_crossover_signals(simple_moving_average(prices, fast),
                                         simple_moving_average(prices, slow))
    assert Signal.ENTER_LONG in full and Signal.EXIT_LONG in full
    for end in (0, 1, slow - 1, slow, slow + 1, 100, 180, 220):
        assert strategy.generate_signals(prices[:end]) == full[:end]
    assert strategy.generate_signals(prices[:180] + (Decimal("10000"),) * 60)[:180] == full[:180]


def test_strategy_default_configuration_is_immutable():
    strategy = SmaCrossoverStrategy()
    assert (strategy.fast_window, strategy.slow_window, strategy.name) == (20, 60, "SMA20/SMA60")
    with pytest.raises(FrozenInstanceError):
        strategy.fast_window = 10


@pytest.mark.parametrize("fast, slow, error", [(20, 20, ValueError), (True, 60, TypeError)])
def test_strategy_rejects_invalid_configuration_on_construction(fast, slow, error):
    with pytest.raises(error, match="ventana"):
        SmaCrossoverStrategy(fast, slow)
