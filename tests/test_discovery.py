"""Ideas pendientes: límites de formato, datos requeridos y ausencia de ejecución."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from test_holdout import setup
from trading_ai.ai import ProviderError, ProviderReply
from trading_ai.discovery import DATA_REQUIREMENTS, DiscoveryError, discover_idea, main, validate_idea
from trading_ai.holdout import freeze_proposal


@pytest.fixture
def idea():
    # Especificación de prueba; no representa una recomendación ni resultados.
    return {"title": "Idea sintética", "hypothesis": "Contrastar una regla distinta de los cruces.",
            "entry_rule": "Comprar cuando se cumpla la condición declarada.",
            "exit_rule": "Cerrar cuando se cumpla la condición de salida.",
            "parameters": [{"name": "lookback", "value": 10}],
            "data_requirements": {name: name == "reference_series" for name in DATA_REQUIREMENTS}}


class Provider:
    def __init__(self, response):
        self.response, self.calls, self.messages = response, 0, []
    def describe(self):
        return {"provider": "test", "model": "offline"}
    def complete(self, messages, schema):
        self.calls += 1
        self.messages = deepcopy(messages)
        if isinstance(self.response, Exception):
            raise self.response
        return ProviderReply(self.response if isinstance(self.response, str) else json.dumps(self.response),
                             "offline", {"input_tokens": 25, "output_tokens": 40, "api_cost_usd": "0"})


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def events(directory):
    return [json.loads(line) for line in (directory / "events.jsonl").read_bytes().splitlines()]


@pytest.fixture
def registered(setup, tmp_path):
    split, research, _ = setup
    frozen = freeze_proposal(split, research, tmp_path / "frozen")
    return split, frozen


def test_one_model_request_queues_unexecuted_idea_without_outer_data_or_backtests(registered, tmp_path, idea, monkeypatch):
    split, frozen = registered
    original = {p: p.read_bytes() for folder in (split, frozen) for p in folder.iterdir()}
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.resolve() != (split / "evaluation.xml").resolve()
        assert path.name != "comparison.json"
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr("trading_ai.experiments.run_backtest", lambda *args, **kwargs: pytest.fail("No ejecutar estrategias"))
    provider = Provider(idea)
    directory = discover_idea(provider, frozen, output_dir=tmp_path / "ideas")
    saved = read_json(directory / "idea.json")
    assert provider.calls == 1
    assert saved["proposal"] == idea
    assert saved["status"] == "pending_tool_mapping"
    assert saved["executable"] is False and saved["calculated_results"] is None
    assert saved["missing_declared_inputs"] == []
    assert saved["api_cost_usd"] == "0" and saved["model_requests"] == 1
    assert events(directory)[-1]["event"] == "idea_queued"
    context = json.loads(provider.messages[-1]["content"].split("Contexto de desarrollo: ")[1])
    assert context["data"]["last_date"] == "2025-01-22"
    assert "baseline" not in context and "candidate" not in context
    assert "evaluation" not in context
    monkeypatch.undo()
    assert all(p.read_bytes() == content for p, content in original.items())


def test_additional_declared_inputs_stay_pending_without_downloads(registered, tmp_path, idea):
    _, frozen = registered
    idea["data_requirements"].update(ohlc=True, volume=True)
    directory = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    saved = read_json(directory / "idea.json")
    assert saved["status"] == "needs_data_and_tool_mapping"
    assert saved["missing_declared_inputs"] == ["ohlc", "volume"]
    assert saved["executable"] is False


def test_even_existing_strategy_name_does_not_authorize_execution(registered, tmp_path, idea):
    _, frozen = registered
    idea["title"] = "sma_crossover"
    directory = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    assert read_json(directory / "idea.json")["executable"] is False


def test_model_text_is_never_interpreted_as_python(registered, tmp_path, idea, monkeypatch):
    _, frozen = registered
    idea["entry_rule"] = "__import__('os').system('model-text-must-not-run')"
    monkeypatch.setattr("os.system", lambda *args: pytest.fail("No ejecutar texto del modelo"))
    directory = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    saved = read_json(directory / "idea.json")
    assert saved["proposal"]["entry_rule"] == idea["entry_rule"]
    assert saved["validation_scope"] == "format_and_bounds_only_not_strategy_correctness"
    assert saved["executable"] is False


@pytest.mark.parametrize("field,value", [("code", "print(1)"), ("tool", "shell"), ("initial_capital", 9999),
                                        ("results", {"return_percent": "999"}), ("executable", True)])
def test_model_cannot_add_execution_permissions_controls_or_results(idea, field, value):
    idea[field] = value
    with pytest.raises(ValueError, match="campos"):
        validate_idea(idea)


@pytest.mark.parametrize("name", ["cost_rate", "initial_capital", "allocation_fraction", "leverage", "source"])
def test_parameter_names_cannot_override_controls(idea, name):
    idea["parameters"] = [{"name": name, "value": 1}]
    with pytest.raises(ValueError, match="controles"):
        validate_idea(idea)


@pytest.mark.parametrize("value", [True, "10", float('nan'), float('inf'), 1000001, -(10 ** 400)])
def test_parameters_are_finite_bounded_numbers_not_expressions(idea, value):
    idea["parameters"][0]["value"] = value
    with pytest.raises(ValueError, match="numérico"):
        validate_idea(idea)


@pytest.mark.parametrize("change", ["empty_rule", "too_long", "duplicate_parameter", "invalid_name",
                                   "too_many_parameters", "unknown_data", "non_boolean_data", "no_data", "legacy_duplicate_array"])
def test_invalid_or_ambiguous_specs_are_rejected(idea, change):
    if change == "empty_rule": idea["entry_rule"] = "   "
    elif change == "too_long": idea["hypothesis"] = "x" * 241
    elif change == "duplicate_parameter": idea["parameters"] *= 2
    elif change == "invalid_name": idea["parameters"][0]["name"] = "eval(1)"
    elif change == "too_many_parameters": idea["parameters"] *= 7
    elif change == "unknown_data": idea["data_requirements"]["live_prices"] = True
    elif change == "non_boolean_data": idea["data_requirements"]["ohlc"] = "false"
    elif change == "legacy_duplicate_array": idea["data_requirements"] = ["reference_series", "ohlc", "volume", "ohlc", "volume"]
    else: idea["data_requirements"] = dict.fromkeys(DATA_REQUIREMENTS, False)
    with pytest.raises(ValueError):
        validate_idea(idea)


@pytest.mark.parametrize("answer", ["not JSON", {"title": "incomplete"}])
def test_invalid_reply_preserves_raw_response_and_consumption(registered, tmp_path, answer):
    _, frozen = registered
    provider = Provider(answer)
    with pytest.raises(DiscoveryError) as failure:
        discover_idea(provider, frozen, output_dir=tmp_path / "ideas")
    recorded = events(failure.value.directory)
    assert provider.calls == 1
    assert any(event["event"] == "model_response" for event in recorded)
    assert recorded[-1]["event"] == "discovery_failed"
    assert recorded[-1]["data"]["usage"][0]["output_tokens"] == 40
    assert not (failure.value.directory / "idea.json").exists()


def test_truncation_keeps_known_usage_without_retry(registered, tmp_path):
    _, frozen = registered
    provider = Provider(ProviderError("truncated", {"output_tokens": 384, "api_cost_usd": "0"}))
    with pytest.raises(DiscoveryError) as failure:
        discover_idea(provider, frozen, output_dir=tmp_path / "ideas")
    assert provider.calls == 1
    assert events(failure.value.directory)[-1]["data"]["usage"][0]["output_tokens"] == 384


def test_changed_source_blocks_model_request(registered, tmp_path, idea):
    split, frozen = registered
    path = split / "development.xml"
    path.write_bytes(path.read_bytes() + b"\n")
    provider = Provider(idea)
    with pytest.raises(DiscoveryError):
        discover_idea(provider, frozen, output_dir=tmp_path / "ideas")
    assert provider.calls == 0


def test_repeated_ideas_keep_all_attempts_and_same_fingerprint(registered, tmp_path, idea):
    _, frozen = registered
    first = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    original = {p.name: p.read_bytes() for p in first.iterdir()}
    second = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    assert first != second
    assert read_json(first / "idea.json")["idea_id"] == read_json(second / "idea.json")["idea_id"]
    assert original == {p.name: p.read_bytes() for p in first.iterdir()}


def test_openai_stays_disabled_before_idea_creation(tmp_path, capsys):
    with pytest.raises(SystemExit) as failure:
        main(["--frozen-run", str(tmp_path / "unused"), "--provider", "openai", "--output-dir", str(tmp_path / "ideas")])
    assert failure.value.code == 1
    assert "integración futura" in capsys.readouterr().err
    assert not (tmp_path / "ideas").exists()
