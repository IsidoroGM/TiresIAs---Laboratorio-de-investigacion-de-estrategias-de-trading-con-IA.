"""Propuestas tipadas: validación, memoria, duplicados y verificación sin ejecutar estrategias."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from threading import Barrier

import pytest

from test_discovery import Provider, events, idea, read_json, registered
from test_holdout import setup
from trading_ai.ai import AIConfig, ProviderError
from trading_ai.discovery import discover_idea
from trading_ai.structured_ideas import (BUDGET, PROPOSAL_SCHEMA, StructuredIdeaError, compile_proposal, main,
                                        propose_structured_idea, verify_structured_idea)


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr("trading_ai.structured_ideas.ACCESS_ROOT", tmp_path / "access")


@pytest.fixture
def proposal():
    # Ejemplo artificial para el contrato, sin buscar resultados sobre los datos.
    return {"title": "Regla sintética", "hypothesis": "Contrastar condiciones explícitas de referencia y umbral.",
            "entry": {"left": {"kind": "reference", "lag": 0}, "operator": "gt",
                      "right": {"kind": "constant", "value": "1"}},
            "exit": {"left": {"kind": "reference", "lag": 0}, "operator": "lte",
                     "right": {"kind": "constant", "value": "1"}}}


@pytest.fixture
def generated(registered, tmp_path, proposal):
    split, frozen = registered
    provider = Provider(proposal)
    directory = propose_structured_idea(provider, frozen, output_dir=tmp_path / "structured")
    return split, frozen, directory, provider


def test_proposal_has_one_explicit_condition_per_side_and_does_not_mutate_input(proposal):
    original = deepcopy(proposal)
    proposal["entry"]["right"] = {"kind": "ema", "window": 12, "lag": 1}
    proposal["exit"]["right"] = {"kind": "sma", "window": 24, "lag": 0}
    before = deepcopy(proposal)
    spec = compile_proposal(proposal).to_spec()
    assert spec["entry"] == {"match": "all", "conditions": [proposal["entry"]]}
    assert spec["exit"] == {"match": "all", "conditions": [proposal["exit"]]}
    assert spec["entry"]["conditions"][0]["right"]["window"] == 12
    assert spec["exit"]["conditions"][0]["right"]["window"] == 24
    assert proposal == before and original != proposal


@pytest.mark.parametrize("change", ["free_text", "missing_window", "bool_window", "future_lag", "float_lag", "ohlc", "extra_operand",
                                    "operator", "code", "capital", "results", "alternatives", "long_hypothesis", "nan_constant"])
def test_ambiguous_unsupported_future_or_control_fields_are_rejected(proposal, change):
    if change == "free_text": proposal["entry"] = "Comprar cuando la rápida supera a la lenta."
    elif change == "missing_window": proposal["entry"]["right"] = {"kind": "ema", "lag": 0}
    elif change == "bool_window": proposal["entry"]["right"] = {"kind": "ema", "window": True, "lag": 0}
    elif change == "future_lag": proposal["entry"]["left"]["lag"] = -1
    elif change == "float_lag": proposal["entry"]["left"]["lag"] = 1.0
    elif change == "ohlc": proposal["entry"]["left"]["kind"] = "close"
    elif change == "extra_operand": proposal["entry"]["left"]["reference_series"] = 1
    elif change == "operator": proposal["entry"]["operator"] = "when_ready"
    elif change == "alternatives": proposal["exit"] = [proposal["exit"], deepcopy(proposal["entry"])]
    elif change == "long_hypothesis": proposal["hypothesis"] = "x" * 161
    elif change == "nan_constant": proposal["entry"]["right"]["value"] = "NaN"
    else: proposal[change] = "No permitido"
    with pytest.raises(ValueError): compile_proposal(proposal)


def test_generation_and_verification_never_translate_simulate_or_read_outer_data(registered, tmp_path, idea, proposal, monkeypatch):
    split, frozen = registered
    previous = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "memory/discovery")
    original = {path: path.read_bytes() for folder in (split, frozen, previous) for path in folder.iterdir()}
    actual_open = Path.open
    def guarded(path, *a, **k):
        assert path.name not in ("evaluation.xml", "comparison.json")
        assert "evaluation-access" not in path.parts
        return actual_open(path, *a, **k)
    monkeypatch.setattr(Path, "open", guarded)
    for method in ("trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.experiments.run_backtest",
                   "trading_ai.formalization.formalize_idea"):
        monkeypatch.setattr(method, lambda *a, **k: pytest.fail("Solo compilar estructura"))
    provider = Provider(proposal)
    directory = propose_structured_idea(provider, frozen, output_dir=tmp_path / "structured")
    record = verify_structured_idea(directory, frozen)
    assert provider.calls == record["model_requests"] == 1 and record["api_cost_usd"] == "0"
    assert record["backtests"] == 0 and record["budget"] == BUDGET and record["executable"] is False
    assert record["status"] == "pending_semantic_review" and record["calculated_results"] is None
    assert record["semantic_equivalence_verified"] is False and record["proposal"] == proposal
    context = json.loads(provider.messages[-1]["content"])
    assert context["known_ideas"][0]["entry_rule"] == idea["entry_rule"]
    assert set(context) == {"question", "pair", "data", "known_ideas", "known_rules"}
    request = next(item["data"] for item in events(directory) if item["event"] == "model_request")
    assert request["messages"] == provider.messages and request["schema"] == PROPOSAL_SCHEMA
    assert "reference(lag=0) gt 1" in (directory / "report.md").read_text(encoding="utf-8")
    monkeypatch.setattr(Path, "open", actual_open)
    assert all(path.read_bytes() == raw for path, raw in original.items())


def test_retitle_and_numeric_spelling_cannot_make_an_existing_rule_new(generated, tmp_path, proposal):
    _, frozen, first, _ = generated
    original = deepcopy(proposal)
    proposal.update(title="Título nuevo", hypothesis="Una explicación distinta.")
    proposal["entry"]["right"]["value"] = "1.0"
    proposal["exit"]["right"]["value"] = "1e0"
    provider = Provider(proposal)
    second = propose_structured_idea(provider, frozen, output_dir=tmp_path / "another")
    record = verify_structured_idea(second, frozen)
    assert record["status"] == "duplicate_rules" and record["duplicate_of"] == str(first)
    assert record["spec_sha256"] == compile_proposal(original).spec_sha256
    context = json.loads(provider.messages[-1]["content"])
    assert len(context["known_rules"]) == 1 and context["known_rules"][0]["entry"] == original["entry"]
    assert provider.calls == 1 and record["executable"] is False


def test_changed_condition_is_a_distinct_pending_proposal(generated, tmp_path, proposal):
    _, frozen, _, _ = generated
    proposal["entry"]["operator"] = "crosses_above"
    directory = propose_structured_idea(Provider(proposal), frozen, output_dir=tmp_path / "another")
    assert verify_structured_idea(directory, frozen)["status"] == "pending_semantic_review"


@pytest.mark.parametrize("reply", ['{"title":"x","title":"y"}', '{broken', 'NaN', '{"unexpected":1}'])
def test_invalid_model_output_preserves_raw_response_and_usage(registered, tmp_path, reply):
    _, frozen = registered
    provider = Provider(reply)
    with pytest.raises(StructuredIdeaError) as failure:
        propose_structured_idea(provider, frozen, output_dir=tmp_path / "structured")
    log = events(failure.value.directory)
    assert log[-1]["event"] == "structured_idea_failed" and log[-1]["data"]["usage"][0]["output_tokens"] == 40
    assert next(item["data"]["content"] for item in log if item["event"] == "model_response") == reply
    assert not (failure.value.directory / "proposal.json").exists() and provider.calls == 1


@pytest.mark.parametrize("usage", [None, {"output_tokens": 384, "api_cost_usd": "0"}])
def test_provider_failure_is_one_attempt_with_no_automatic_retry(registered, tmp_path, usage):
    _, frozen = registered
    provider = Provider(ProviderError("Salida truncada", usage))
    with pytest.raises(StructuredIdeaError) as failure:
        propose_structured_idea(provider, frozen, output_dir=tmp_path / "structured")
    end = events(failure.value.directory)[-1]["data"]
    assert provider.calls == end["model_requests"] == 1
    assert end["api_cost_usd"] == (None if usage is None else "0")
    assert not (tmp_path / "access").exists()


@pytest.mark.parametrize("filename", ["memory.json", "rules-memory.json", "report.md", "proposal.json", "events.jsonl"])
def test_changed_artifacts_cannot_be_verified(generated, filename):
    _, frozen, directory, _ = generated
    with (directory / filename).open("ab") as stream: stream.write(b' ')
    with pytest.raises((ValueError, KeyError)): verify_structured_idea(directory, frozen)


def test_changed_historical_source_stops_the_next_generation_before_provider_call(generated, tmp_path, proposal):
    _, frozen, first, _ = generated
    with (first / "proposal.json").open("ab") as stream: stream.write(b' ')
    provider = Provider(proposal)
    with pytest.raises(StructuredIdeaError):
        propose_structured_idea(provider, frozen, output_dir=tmp_path / "another")
    assert provider.calls == 0


def test_memory_changed_during_generation_is_not_silently_sealed(registered, tmp_path, proposal):
    _, frozen = registered
    class Changing(Provider):
        def complete(self, messages, schema):
            path, = (tmp_path / "structured").glob("*/memory.json")
            with path.open("ab") as stream: stream.write(b' ')
            return super().complete(messages, schema)
    provider = Changing(proposal)
    with pytest.raises(StructuredIdeaError, match="memoria") as failure:
        propose_structured_idea(provider, frozen, output_dir=tmp_path / "structured")
    assert provider.calls == 1 and not (failure.value.directory / "proposal.json").exists()
    assert not (tmp_path / "access").exists()


def test_extra_fields_remain_invalid_even_with_recomputed_closing_hash(generated):
    _, frozen, directory, _ = generated
    record = read_json(directory / "proposal.json")
    record["execute_now"] = True
    path = directory / "proposal.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    log = events(directory)
    log[-1]["data"]["sha256"] = sha256(path.read_bytes()).hexdigest()
    (directory / "events.jsonl").write_text("\n".join(json.dumps(item) for item in log) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no autorizados"): verify_structured_idea(directory, frozen)


def test_concurrent_identical_proposals_have_one_owner_and_one_duplicate(registered, tmp_path, proposal):
    _, frozen = registered
    barrier = Barrier(2)
    class Simultaneous(Provider):
        def complete(self, messages, schema):
            barrier.wait(timeout=20)
            return super().complete(messages, schema)
    with ThreadPoolExecutor(max_workers=2) as pool:
        runs = list(pool.map(lambda _: propose_structured_idea(Simultaneous(proposal), frozen,
                                                              output_dir=tmp_path / "structured"), range(2)))
    records = [verify_structured_idea(directory, frozen) for directory in runs]
    assert sorted(record["status"] for record in records) == ["duplicate_rules", "pending_semantic_review"]
    assert len(list((tmp_path / "access").glob("*.json"))) == 1


@pytest.mark.parametrize("config", [AIConfig(provider="openai"), AIConfig(output_tokens=512), AIConfig(context_tokens=8192)])
def test_disallowed_provider_or_budget_never_creates_a_run(registered, tmp_path, proposal, config):
    _, frozen = registered
    provider = Provider(proposal)
    with pytest.raises(ValueError):
        propose_structured_idea(provider, frozen, config=config, output_dir=tmp_path / "structured")
    assert provider.calls == 0 and not (tmp_path / "structured").exists()


def test_cli_verification_does_not_create_a_provider_or_offer_execution(generated, monkeypatch, capsys):
    _, frozen, directory, _ = generated
    monkeypatch.setattr("trading_ai.structured_ideas.create_provider", lambda *a: pytest.fail("Sin IA"))
    main(["verify", "--run", str(directory), "--frozen-run", str(frozen)])
    assert '"executable": false' in capsys.readouterr().out
    with pytest.raises(SystemExit) as failure:
        main(["execute", "--run", str(directory), "--frozen-run", str(frozen)])
    assert failure.value.code == 2
