"""Ayudas de revisión: propiedades causales, calentamiento y advertencias sin autoaprobación."""

from decimal import Decimal
from itertools import product
from pathlib import Path

import pytest

from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from trading_ai.rules import compile_rule_strategy
from trading_ai.strategies import Signal
from trading_ai.structured_diagnostics import diagnose_structured_idea, inspect_proposal, verify_structured_diagnostics
from trading_ai.structured_ideas import compile_proposal


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr("trading_ai.structured_ideas.ACCESS_ROOT", tmp_path / "ideas-access")


def test_exact_lengths_distinguish_near_limit_from_actual_truncation(proposal):
    proposal["title"] = "a" * 60
    proposal["hypothesis"] = "a" * 156 + " la"
    result = inspect_proposal(proposal, 100)
    assert result["title_characters"] == 60 and result["hypothesis_characters"] == 159
    assert result["title_at_character_limit"] is True and result["hypothesis_at_character_limit"] is False
    assert "hypothesis_ends_with_linking_word" in result["findings"]


def test_global_warmup_includes_slowest_operand_crossing_and_lag(proposal):
    proposal["entry"] = {"left":{"kind":"ema","window":20,"lag":0},"operator":"crosses_above",
                         "right":{"kind":"sma","window":60,"lag":0}}
    proposal["exit"] = {"left":{"kind":"ema","window":20,"lag":1},"operator":"crosses_below",
                        "right":{"kind":"sma","window":60,"lag":1}}
    result = inspect_proposal(proposal, 100)
    assert result["earliest_signal_index"] == 61 and result["earliest_execution_index"] == 62
    assert result["defined_signal_observations"] == 39
    assert "different_entry_exit_lags" in result["findings"]
    signals = compile_proposal(proposal).generate_signals([Decimal(1)] * 100)
    assert signals[:61] == [Signal.NONE] * 61


@pytest.mark.parametrize("change", ["false_entry", "true_exit", "same_conditions", "not_enough_data"])
def test_structurally_impossible_entry_agrees_with_all_small_price_paths(proposal, change):
    observations = 5
    if change == "false_entry": proposal["entry"]["right"] = dict(proposal["entry"]["left"])
    elif change == "true_exit": proposal["exit"]["right"] = dict(proposal["exit"]["left"])
    elif change == "same_conditions": proposal["exit"] = proposal["entry"]
    else: proposal["entry"]["right"] = {"kind":"sma","window":6,"lag":0}
    assert inspect_proposal(proposal, observations)["entry_ruled_out"] is True
    strategy = compile_proposal(proposal)
    for prices in product((Decimal(1), Decimal(2), Decimal(3)), repeat=5):
        assert Signal.ENTER_LONG not in strategy.generate_signals(prices)


@pytest.mark.parametrize("observations", [0, True, 1.5])
def test_observation_bounds_are_strict(proposal, observations):
    with pytest.raises(ValueError): inspect_proposal(proposal, observations)


def test_diagnostics_never_generate_signals_simulate_or_contact_model(generated, tmp_path, monkeypatch):
    _, frozen, source, _ = generated
    for name in ("trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.experiments.run_backtest", "trading_ai.ai.create_provider"):
        monkeypatch.setattr(name, lambda *a, **k: pytest.fail("Solo diagnóstico estático"))
    original_open = Path.open
    def guarded(path, *a, **k):
        assert path.name not in ("evaluation.xml", "comparison.json")
        return original_open(path, *a, **k)
    monkeypatch.setattr(Path, "open", guarded)
    run = diagnose_structured_idea(source, frozen, output_dir=tmp_path / "diagnostics")
    record = verify_structured_diagnostics(run, frozen)
    assert record["status"] == "review_aid_only" and record["executable"] is False and record["calculated_results"] is None
    assert record["model_requests"] == 0 and record["api_cost_usd"] == "0"
    with (run / "diagnostics.json").open("ab") as stream: stream.write(b' ')
    with pytest.raises(ValueError): verify_structured_diagnostics(run, frozen)
