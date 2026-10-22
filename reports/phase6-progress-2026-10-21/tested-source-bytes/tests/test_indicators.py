"""Resultados conocidos, casos límite y ausencia de información futura."""

from decimal import Decimal, ROUND_DOWN, localcontext

import pytest

from trading_ai.indicators import simple_moving_average


def test_known_averages_and_alignment():
    values = [Decimal(value) for value in (2, 4, 6, 8)]
    original = values.copy()
    assert simple_moving_average(values, 3) == [None, None, Decimal("4"), Decimal("6")]
    assert values == original


@pytest.mark.parametrize("window", [1, 2, 20, 60])
def test_empty_input(window):
    assert simple_moving_average([], window) == []


def test_insufficient_observations():
    assert simple_moving_average([Decimal("2"), Decimal("4")], 3) == [None, None]


def test_window_one_returns_each_value():
    values = [Decimal("0"), Decimal("-1.25"), Decimal("2.50")]
    assert simple_moving_average(values, 1) == values


def test_window_equal_to_length():
    values = [Decimal("0.1"), Decimal("0.2"), Decimal("0.3")]
    assert simple_moving_average(values, 3) == [None, None, Decimal("0.2")]


@pytest.mark.parametrize("window", [0, -1, -20])
def test_rejects_nonpositive_window(window):
    with pytest.raises(ValueError, match="mayor que cero"):
        simple_moving_average([], window)


@pytest.mark.parametrize("window", [True, False, 2.0, "20", None, Decimal("2")])
def test_rejects_noninteger_window(window):
    with pytest.raises(TypeError, match="entero positivo"):
        simple_moving_average([], window)


@pytest.mark.parametrize("value", [1.2, 1, "1.2", None, True])
def test_rejects_nondecimal_values_even_during_warmup(value):
    with pytest.raises(TypeError, match="posición 0 debe ser Decimal"):
        simple_moving_average([value], 20)


@pytest.mark.parametrize("value", ["NaN", "sNaN", "Infinity", "-Infinity"])
def test_rejects_nonfinite_values(value):
    with pytest.raises(ValueError, match="debe ser finito"):
        simple_moving_average([Decimal(value)], 20)


@pytest.mark.parametrize("window", [1, 3, 20, 60])
def test_future_observations_do_not_change_previous_results(window):
    history = [Decimal(value) for value in range(1, 81)]
    full_result = simple_moving_average(history, window)
    for end in (0, 1, 2, 19, 20, 59, 60, 70):
        assert full_result[:end] == simple_moving_average(history[:end], window)
    # Alterar los datos posteriores tampoco cambia el prefijo.
    changed_future = history[:70] + [Decimal("10000")] * 10
    assert simple_moving_average(changed_future, window)[:70] == full_result[:70]


@pytest.mark.parametrize("window", [20, 60])
def test_constant_series_and_warmup(window):
    result = simple_moving_average([Decimal("1.25")] * 80, window)
    assert result == [None] * (window - 1) + [Decimal("1.25")] * (81 - window)


def test_zero_and_negative_values():
    values = [Decimal("-2"), Decimal("0"), Decimal("2")]
    assert simple_moving_average(values, 2) == [None, Decimal("-1"), Decimal("1")]


def test_precision_and_rounding_are_independent_of_caller():
    values = [Decimal("1"), Decimal("0"), Decimal("1")]
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert simple_moving_average(values, 3) == [
            None, None, Decimal("0.6666666666666666666666666667")
        ]
        assert context.prec == 3
        assert context.rounding == ROUND_DOWN
