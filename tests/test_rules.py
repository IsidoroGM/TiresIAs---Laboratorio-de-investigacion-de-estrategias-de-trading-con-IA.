"""Resultados conocidos, causalidad, límites y compatibilidad de las reglas."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json

import pytest

from trading_ai.backtesting import run_backtest
from trading_ai.rules import MAX_SPEC_BYTES, RuleStrategy, compile_rule_strategy, load_rule_strategy, main
from trading_ai.strategies import Signal, create_strategy


def reference(lag=0):
    return {"kind": "reference", "lag": lag}


def constant(value):
    return {"kind": "constant", "value": str(value)}


def indicator(kind, window=3, lag=0):
    return {"kind": kind, "window": window, "lag": lag}


def condition(left, op, right):
    return {"left": left, "operator": op, "right": right}


def specification(left=None, op="gt", right=None):
    return {"schema_version": 1, "name": "test_rules",
            "entry": {"match": "all", "conditions": [condition(left or reference(), op, right or constant(0))]},
            "exit": {"match": "all", "conditions": [condition(constant(0), "gt", constant(1))]}}


def prices(values):
    return [Decimal(value) for value in values]


@pytest.mark.parametrize("op,expected", [
    ("gt", [False, False, True]), ("gte", [False, True, True]),
    ("lt", [True, False, False]), ("lte", [True, True, False]), ("eq", [False, True, False])])
def test_numeric_comparisons_with_known_results(op, expected):
    strategy = compile_rule_strategy(specification(op=op))
    assert strategy.generate_signals(prices([-1, 0, 1])) == [Signal.ENTER_LONG if match else Signal.NONE for match in expected]


@pytest.mark.parametrize("op,index", [("crosses_above", 2), ("crosses_below", 5)])
def test_crosses_require_previous_value_and_strict_current_inequality(op, index):
    result = compile_rule_strategy(specification(op=op)).generate_signals(prices([-1, 0, 1, 1, 0, -1]))
    assert result == [Signal.ENTER_LONG if position == index else Signal.NONE for position in range(6)]


@pytest.mark.parametrize("kind,values,expected", [
    ("rolling_max", [3, 1, 4, 0], [Signal.NONE, Signal.NONE, Signal.ENTER_LONG, Signal.NONE]),
    ("rolling_min", [3, 1, 4, 0], [Signal.NONE, Signal.NONE, Signal.NONE, Signal.ENTER_LONG]),
])
def test_window_extrema_use_only_previous_observations_when_lag_is_one(kind, values, expected):
    op = "gt" if kind == "rolling_max" else "lt"
    strategy = compile_rule_strategy(specification(op=op, right=indicator(kind, 2, lag=1)))
    assert strategy.generate_signals(prices(values)) == expected


def test_current_window_extrema_include_current_observation():
    strategy = compile_rule_strategy(specification(op="gt", right=indicator("rolling_max", 2)))
    assert strategy.generate_signals(prices([3, 1, 4, 8])) == [Signal.NONE] * 4


def test_lag_and_indicator_warmup_are_explicit():
    strategy = compile_rule_strategy(specification(left=indicator("sma", 3, lag=2)))
    assert strategy.generate_signals(prices(range(1, 8))) == [Signal.NONE] * 4 + [Signal.ENTER_LONG] * 3
    strategy = compile_rule_strategy(specification(left=indicator("sma", 3, lag=2), op="crosses_above", right=constant(3)))
    assert strategy.generate_signals(prices(range(1, 8))) == [Signal.NONE] * 6 + [Signal.ENTER_LONG]


@pytest.mark.parametrize("match,conditions,expected", [
    ("all", [condition(reference(), "gt", constant(1)), condition(reference(), "lt", constant(3))], [2]),
    ("any", [condition(reference(), "lt", constant(1)), condition(reference(), "gt", constant(3))], [0, 4]),
])
def test_all_and_any_combine_flat_conditions(match, conditions, expected):
    spec = specification()
    spec["entry"] = {"match": match, "conditions": conditions}
    assert compile_rule_strategy(spec).generate_signals(prices(range(5))) == [Signal.ENTER_LONG if i in expected else Signal.NONE for i in range(5)]


def test_any_does_not_bypass_missing_history_and_exit_must_be_ready():
    spec = specification()
    spec["entry"] = {"match": "any", "conditions": [condition(constant(1), "gt", constant(0)),
                                                        condition(indicator("sma", 3), "gt", constant(99))]}
    assert compile_rule_strategy(spec).generate_signals(prices([1, 2, 3])) == [Signal.NONE, Signal.NONE, Signal.ENTER_LONG]
    spec = specification()
    spec["exit"]["conditions"] = [condition(indicator("ema", 3), "gt", constant(99))]
    assert compile_rule_strategy(spec).generate_signals(prices([1, 2, 3])) == [Signal.NONE, Signal.NONE, Signal.ENTER_LONG]


def test_simultaneous_entry_and_exit_have_fixed_exit_priority():
    spec = specification()
    spec["exit"] = deepcopy(spec["entry"])
    strategy = compile_rule_strategy(spec)
    assert strategy.generate_signals(prices([1, 2, 3])) == [Signal.EXIT_LONG] * 3
    rates = [(date(2000, 1, 1) + timedelta(days=i), price) for i, price in enumerate(prices([1, 2, 3]))]
    result = run_backtest(rates, strategy.generate_signals([price for _, price in rates]), "EUR/USD")
    assert result.closed_trades == () and result.open_position is None


@pytest.mark.parametrize("kind", ["sma", "ema"])
@pytest.mark.parametrize("fast,slow", [(1, 3), (2, 4), (20, 60)])
def test_existing_crossovers_and_entire_simulation_are_reproduced(kind, fast, slow):
    spec = specification(indicator(kind, fast), "crosses_above", indicator(kind, slow))
    spec["exit"]["conditions"] = [condition(indicator(kind, fast), "crosses_below", indicator(kind, slow))]
    compiled = compile_rule_strategy(spec)
    existing = create_strategy(kind, fast, slow)
    values = prices([3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3] * 9)
    assert compiled.generate_signals(values) == existing.generate_signals(values)
    rates = [(date(2000, 1, 1) + timedelta(days=i), price) for i, price in enumerate(values)]
    kwargs = {"cost_rate": Decimal("0.001"), "initial_capital": Decimal("1000"), "allocation_fraction": Decimal("0.1")}
    actual = run_backtest(rates, compiled.generate_signals(values), "EUR/USD", **kwargs)
    assert actual == run_backtest(rates, existing.generate_signals(values), "EUR/USD", **kwargs)
    for trade in actual.closed_trades:
        assert trade.position.entry_date > trade.position.entry_signal_date
        assert trade.exit_date > trade.exit_signal_date


@pytest.mark.parametrize("kind", ["reference", "sma", "ema", "rolling_min", "rolling_max"])
def test_prefixes_and_altered_future_do_not_change_past_signals(kind):
    left = reference(lag=2) if kind == "reference" else indicator(kind, 4, lag=2)
    spec = specification(left, "crosses_above", constant(3))
    spec["exit"]["conditions"] = [condition(left, "crosses_below", constant(3))]
    strategy = compile_rule_strategy(spec)
    values = prices([3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3] * 5)
    full = strategy.generate_signals(values)
    original = values.copy()
    for end in (0, 1, 3, 4, 5, 6, 20, 40):
        assert strategy.generate_signals(values[:end]) == full[:end]
    assert strategy.generate_signals(values[:40] + prices([10000] * 15))[:40] == full[:40]
    assert values == original
    assert strategy.generate_signals(values) == full


def test_compiled_strategy_and_its_specification_are_immutable_and_hash_is_canonical():
    spec = specification()
    strategy = compile_rule_strategy(spec)
    before = strategy.generate_signals(prices([-1, 1]))
    canonical = strategy.spec_json
    spec["entry"]["conditions"][0]["operator"] = "lt"
    copy = strategy.to_spec()
    copy["entry"]["conditions"][0]["operator"] = "lt"
    assert strategy.generate_signals(prices([-1, 1])) == before
    assert strategy.spec_json == canonical
    assert strategy.spec_sha256 == sha256(canonical.encode('utf-8')).hexdigest()
    equivalent = dict(reversed(list(strategy.to_spec().items())))
    assert compile_rule_strategy(equivalent).spec_sha256 == strategy.spec_sha256
    with pytest.raises(FrozenInstanceError):
        strategy.spec_json = "{}"


def test_decimal_context_does_not_change_signals_or_fingerprint():
    spec = specification(indicator("ema", 2), "crosses_above", indicator("sma", 3))
    values = prices(["1.234567890123456789", "2.34567890123456789", "7.4567890123456789", "2.567890123456789", "1.1", "9.9"])
    strategy = compile_rule_strategy(spec)
    expected = strategy.generate_signals(values)
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert compile_rule_strategy(spec).spec_sha256 == strategy.spec_sha256
        assert strategy.generate_signals(values) == expected
        assert context.prec == 3 and context.rounding == ROUND_DOWN


@pytest.mark.parametrize("field,value", [("initial_capital", "9999"), ("cost_rate", "0"),
                                         ("allocation_fraction", "1"), ("pair", "EUR/USD"), ("code", "print(1)"),
                                         ("conflict_policy", "entry_first"), ("tool", "shell")])
def test_top_level_controls_and_execution_options_are_rejected(field, value):
    spec = specification()
    spec[field] = value
    with pytest.raises(ValueError, match="campos"):
        compile_rule_strategy(spec)


@pytest.mark.parametrize("change", ["future", "huge_lag", "bool_lag", "bad_window", "huge_window", "bool_window",
                                   "unknown_series", "extra_operand_field", "unknown_operator", "nested_group",
                                   "empty_group", "too_many", "bad_match", "natural_language", "bad_version", "bad_name"])
def test_unbounded_ambiguous_or_unsupported_rules_are_rejected(change):
    spec = specification()
    rule = spec["entry"]["conditions"][0]
    if change == "future": rule["left"]["lag"] = -1
    elif change == "huge_lag": rule["left"]["lag"] = 253
    elif change == "bool_lag": rule["left"]["lag"] = True
    elif change == "bad_window": rule["left"] = indicator("sma", 0)
    elif change == "huge_window": rule["left"] = indicator("ema", 253)
    elif change == "bool_window": rule["left"] = indicator("sma", True)
    elif change == "unknown_series": rule["left"]["kind"] = "volume"
    elif change == "extra_operand_field": rule["left"]["source"] = "/other/file"
    elif change == "unknown_operator": rule["operator"] = "eval"
    elif change == "nested_group": spec["entry"]["conditions"] = [deepcopy(spec["entry"])]
    elif change == "empty_group": spec["entry"]["conditions"] = []
    elif change == "too_many": spec["entry"]["conditions"] *= 5
    elif change == "bad_match": spec["entry"]["match"] = "sometimes"
    elif change == "natural_language": spec["exit"] = "Cerrar al final del día o cuando convenga"
    elif change == "bad_version": spec["schema_version"] = True
    else: spec["name"] = "../../code"
    with pytest.raises(ValueError):
        compile_rule_strategy(spec)


@pytest.mark.parametrize("value", [True, 1.2, "NaN", "Infinity", "__import__('os').system('bad')", "1000001", "1e-1000", "1.12345678901234567890123456789"])
def test_constant_expressions_nonfinite_or_unbounded_values_are_rejected(value, monkeypatch):
    monkeypatch.setattr("os.system", lambda *args: pytest.fail("No ejecutar texto"))
    with pytest.raises(ValueError):
        compile_rule_strategy(specification(right={"kind": "constant", "value": value}))


@pytest.mark.parametrize("value", [1, 1.2, True, None, Decimal('NaN'), Decimal('Infinity')])
def test_invalid_observations_fail_even_during_warmup(value):
    strategy = compile_rule_strategy(specification(indicator("sma", 252)))
    with pytest.raises((ValueError, TypeError)):
        strategy.generate_signals([value])


def test_loading_is_bounded_and_rejects_duplicate_json_keys(tmp_path):
    path = tmp_path / "rules.json"
    text = json.dumps(specification())
    path.write_text(text.replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'), encoding="utf-8")
    with pytest.raises(ValueError, match="repetidas"):
        load_rule_strategy(path)
    path.write_text(' ' * (MAX_SPEC_BYTES + 1), encoding="utf-8")
    with pytest.raises(ValueError, match="16384"):
        load_rule_strategy(path)
    with pytest.raises(ValueError):
        RuleStrategy('{}')


def test_cli_only_validates_without_models_or_backtest(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("trading_ai.ai.create_provider", lambda *args: pytest.fail("Sin modelos"))
    monkeypatch.setattr("trading_ai.backtesting.run_backtest", lambda *args, **kwargs: pytest.fail("Sin backtest"))
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(specification()), encoding="utf-8")
    main(["--spec", str(path)])
    assert "Reglas válidas" in capsys.readouterr().out
    path.write_text('{"name":"not enough"}', encoding="utf-8")
    with pytest.raises(SystemExit) as failure:
        main(["--spec", str(path)])
    assert failure.value.code == 1
