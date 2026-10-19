"""Memoria verificable, contexto sin resultados y límites de detección de duplicados."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from test_discovery import Provider, events, idea, read_json, registered
from test_holdout import setup
from trading_ai.discovery import DiscoveryError, discover_idea
from trading_ai.formalization import _source, formalize_idea
from trading_ai.idea_memory import (capture_memory, discover_with_memory, duplicate_of, fingerprint, validate_memory)


@pytest.fixture(autouse=True)
def memory_root(tmp_path, monkeypatch):
    root = tmp_path / "memory"
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", root)
    return root


def test_fingerprint_ignores_title_hypothesis_spacing_case_parameter_order_and_numeric_spelling(idea):
    idea["parameters"].append({"name": "slow", "value": 20})
    same = deepcopy(idea)
    same.update(title="Título distinto", hypothesis="Hipótesis distinta.")
    same["entry_rule"] = "   COMPRAR cuando  se cumpla la condición declarada.\n"
    same["parameters"] = [{"name": "slow", "value": 20.0}, {"name": "lookback", "value": 10.0}]
    assert fingerprint(idea) == fingerprint(same)
    idea["parameters"][0]["value"] = 0
    same["parameters"][1]["value"] = -0.0
    assert fingerprint(idea) == fingerprint(same)


@pytest.mark.parametrize("change", ["entry", "exit", "parameter", "data"])
def test_fingerprint_preserves_meaningful_rule_parameter_and_input_differences(idea, change):
    different = deepcopy(idea)
    if change in ("entry", "exit"): different[change + "_rule"] += " Otra condición."
    elif change == "parameter": different["parameters"][0]["value"] += 1
    else: different["data_requirements"]["volume"] = True
    assert fingerprint(idea) != fingerprint(different)


def test_capture_groups_repetitions_and_attaches_only_verified_translation_feedback(registered, memory_root, idea, monkeypatch):
    split, frozen = registered
    first = discover_idea(Provider(idea), frozen, output_dir=memory_root / "discovery")
    repeated = deepcopy(idea)
    repeated["title"] = "Misma idea con otro nombre"
    discover_idea(Provider(repeated), frozen, output_dir=memory_root / "research-sessions/s/a/i")
    reason = "La salida contiene alternativas sin decidir."
    formalize_idea(Provider({"status": "needs_clarification", "reason": reason, "spec": None}), first,
                   frozen, output_dir=memory_root / "formalization")
    actual_open = Path.open
    def guarded(path, *a, **k):
        assert path.name not in ("evaluation.xml", "comparison.json")
        if path.is_relative_to(memory_root):
            assert path.name not in ("results.json", "baseline.json", "candidate.json")
        return actual_open(path, *a, **k)
    monkeypatch.setattr(Path, "open", guarded)
    memory = capture_memory(frozen)
    validate_memory(memory, memory["reference"])
    assert len(memory["entries"]) == 1 and len(memory["sources"]) == 3
    entry, = memory["entries"]
    assert len(entry["idea_ids"]) == 2 and entry["unverified_reasons"] == [reason]
    assert entry["statuses"] == ["pending_tool_mapping", "needs_clarification"]
    assert len(duplicate_of(repeated, memory)) == 2


def test_memory_sources_are_rechecked_after_capture(registered, memory_root, idea):
    _, frozen = registered
    first = discover_idea(Provider(idea), frozen, output_dir=memory_root / "discovery")
    memory = capture_memory(frozen)
    with (first / "events.jsonl").open("ab") as stream: stream.write(b' ')
    with pytest.raises(ValueError, match="fuente de memoria"): validate_memory(memory, memory["reference"])
    with pytest.raises(ValueError): capture_memory(frozen)


def test_context_and_raw_prompt_are_logged_without_performance_or_outer_data(registered, memory_root, tmp_path, idea):
    _, frozen = registered
    first = discover_idea(Provider(idea), frozen, output_dir=memory_root / "discovery")
    memory = capture_memory(frozen)
    next_idea = deepcopy(idea)
    next_idea["parameters"][0]["value"] = 11
    provider = Provider(next_idea)
    directory = discover_with_memory(provider, frozen, memory, question="Nueva idea educativa.", output_dir=tmp_path / "new")
    saved, _, _ = _source(directory, frozen)
    assert saved["proposal"] == next_idea and saved["calculated_results"] is None
    assert saved["model_requests"] == provider.calls == 1
    assert saved["api_cost_usd"] == "0"
    context = json.loads(provider.messages[-1]["content"].split("Contexto y memoria: ")[1])
    assert context["known_ideas"][0]["idea_ids"] == [read_json(first / "idea.json")["idea_id"]]
    assert set(context) == {"development", "known_ideas"}
    assert set(context["known_ideas"][0]) == {"idea_ids", "proposal", "statuses", "unverified_reasons"}
    request = next(event for event in events(directory) if event["event"] == "model_request")
    assert request["data"]["messages"] == provider.messages


@pytest.mark.parametrize("reply", ['{"title":"a","title":"b"}', 'NaN', '{broken'])
def test_invalid_response_retains_actual_usage_without_queuing_an_idea(registered, tmp_path, reply):
    _, frozen = registered
    memory = capture_memory(frozen)
    provider = Provider(reply)
    with pytest.raises(DiscoveryError) as failure:
        discover_with_memory(provider, frozen, memory, question="Idea educativa.", output_dir=tmp_path / "new")
    log = events(failure.value.directory)
    assert log[-1]["event"] == "discovery_failed" and log[-1]["data"]["usage"][0]["output_tokens"] == 40
    assert not (failure.value.directory / "idea.json").exists() and provider.calls == 1


def test_history_limit_stops_before_model_instead_of_silently_dropping_old_ideas(registered, memory_root, idea, monkeypatch):
    _, frozen = registered
    discover_idea(Provider(idea), frozen, output_dir=memory_root / "discovery")
    monkeypatch.setattr("trading_ai.idea_memory.MAX_SOURCES", 0)
    with pytest.raises(ValueError, match="límite de fuentes"): capture_memory(frozen)


@pytest.mark.parametrize("extra", ["calculated_results", "evaluation", "instruction"])
def test_extra_memory_fields_are_not_sent_to_model(registered, memory_root, idea, extra):
    _, frozen = registered
    discover_idea(Provider(idea), frozen, output_dir=memory_root / "discovery")
    memory = capture_memory(frozen)
    memory["entries"][0][extra] = "No forma parte del contrato de memoria"
    with pytest.raises(ValueError): validate_memory(memory, memory["reference"])
