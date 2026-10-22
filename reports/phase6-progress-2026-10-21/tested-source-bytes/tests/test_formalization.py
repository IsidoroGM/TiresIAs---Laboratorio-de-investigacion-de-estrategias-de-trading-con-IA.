"""Vínculo idea/reglas: estados pendientes, límites y consumo sin ejecutar señales."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from test_discovery import Provider, events, idea, read_json, registered
from test_holdout import setup
from trading_ai.ai import ProviderError
from trading_ai.discovery import discover_idea
from trading_ai.formalization import FormalizationError, formalize_idea, main, validate_translation
from trading_ai.rules import compile_rule_strategy


@pytest.fixture
def queued(registered, tmp_path, idea):
    split, frozen = registered
    directory = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    return split, frozen, directory


@pytest.fixture
def proposed():
    # Regla sintética solo para probar el contrato; sin interpretación financiera.
    def group(operator):
        return {"match": "all", "conditions": [{"left": {"kind": "reference", "lag": 0},
                "operator": operator, "right": {"kind": "constant", "value": "1"}}]}
    return {"status": "proposed", "reason": "Traducción sintética para una prueba de estructura.",
            "spec": {"schema_version": 1, "name": "test_only", "entry": group("gt"), "exit": group("lte")}}


def test_translation_links_exact_source_without_running_or_opening_outer_data(queued, tmp_path, proposed, monkeypatch):
    split, frozen, directory = queued
    original = {path: path.read_bytes() for folder in (split, frozen, directory) for path in folder.iterdir()}
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.resolve() != (split / "evaluation.xml").resolve()
        assert path.name not in ("comparison.json", "evaluation-access")
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr("trading_ai.rules.RuleStrategy.generate_signals", lambda *a: pytest.fail("Sin señales"))
    monkeypatch.setattr("trading_ai.experiments.run_backtest", lambda *a, **k: pytest.fail("Sin backtests"))
    provider = Provider(proposed)
    result = formalize_idea(provider, directory, frozen, output_dir=tmp_path / "translations")
    saved = read_json(result / "translation.json")
    source = read_json(directory / "idea.json")
    assert saved["source"]["idea_id"] == source["idea_id"]
    assert saved["source"]["sha256"] == {name: sha256(original[directory / name]).hexdigest()
                                          for name in ("idea.json", "events.jsonl")}
    assert saved["original_proposal"] == source["proposal"]
    assert saved["spec"] == proposed["spec"]
    assert saved["spec_sha256"] == compile_rule_strategy(proposed["spec"]).spec_sha256
    assert saved["status"] == "pending_semantic_review"
    assert saved["semantic_equivalence_verified"] is False and saved["executable"] is False
    assert saved["calculated_results"] is None and saved["validation_scope"] == "source_link_and_rule_structure_only"
    assert saved["model_requests"] == provider.calls == 1 and saved["api_cost_usd"] == "0"
    assert source["proposal"] == json.loads(provider.messages[-1]["content"].split("Idea original: ")[1])
    assert "baseline" not in str(provider.messages) and "final_equity" not in str(provider.messages)
    assert events(result)[-1]["event"] == "translation_queued"
    monkeypatch.undo()
    assert all(path.read_bytes() == raw for path, raw in original.items())


@pytest.mark.parametrize("status", ["needs_clarification", "unsupported"])
def test_ambiguity_and_unimplemented_rules_stay_pending_without_spec(queued, tmp_path, status):
    _, frozen, idea_dir = queued
    reply = {"status": status, "reason": "La salida ofrece dos alternativas sin elegir.", "spec": None}
    provider = Provider(reply)
    result = formalize_idea(provider, idea_dir, frozen, output_dir=tmp_path / "translations")
    saved = read_json(result / "translation.json")
    assert saved["status"] == status and saved["model_translation"] == reply
    assert saved["spec"] is None and saved["spec_sha256"] is None
    assert saved["executable"] is False and provider.calls == 1


def test_missing_data_is_recorded_without_contacting_provider(registered, tmp_path, idea, monkeypatch):
    _, frozen = registered
    idea["data_requirements"]["ohlc"] = True
    idea_dir = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "ideas")
    provider = Provider({})
    monkeypatch.setattr(provider, "describe", lambda: pytest.fail("No contactar proveedor"))
    result = formalize_idea(provider, idea_dir, frozen, output_dir=tmp_path / "translations")
    saved = read_json(result / "translation.json")
    assert saved["status"] == "needs_data" and saved["missing_declared_inputs"] == ["ohlc"]
    assert saved["provider"] is None and saved["model_translation"] is None and saved["spec"] is None
    assert saved["model_requests"] == provider.calls == 0 and saved["api_cost_usd"] == "0"
    assert saved["usage"] == [] and not any(event["event"] == "model_request" for event in events(result))


@pytest.mark.parametrize("change", ["idea_id", "proposal", "reference", "status", "permissions", "missing",
                                    "unfinished", "raw_reply", "usage", "duplicate_json", "oversize"])
def test_changed_or_incomplete_source_rejected_before_model(queued, tmp_path, change):
    _, frozen, idea_dir = queued
    path = idea_dir / "idea.json"
    value = read_json(path)
    if change == "idea_id": value["idea_id"] = "0" * 64
    elif change == "proposal": value["proposal"]["exit_rule"] = "Alterada después de la generación."
    elif change == "reference": value["reference"]["outer_cutoff"] = "2000-01-01"
    elif change == "status": value["status"] = "approved"
    elif change == "permissions": value["executable"] = True
    elif change == "missing": value["missing_declared_inputs"] = ["volume"]
    elif change == "usage": value["usage"] = []
    elif change in ("unfinished", "raw_reply"):
        log = events(idea_dir)
        if change == "unfinished": log = log[:-1]
        else: next(item for item in log if item["event"] == "model_response")["data"]["content"] = '{}'
        (idea_dir / "events.jsonl").write_text(''.join(json.dumps(item) + '\n' for item in log), encoding="utf-8")
    elif change == "duplicate_json":
        path.write_text('{"schema_version":2,' + json.dumps(value)[1:], encoding="utf-8")
    elif change == "oversize": path.write_text(' ' * 32769, encoding="utf-8")
    if change not in ("unfinished", "raw_reply", "duplicate_json", "oversize"):
        path.write_text(json.dumps(value), encoding="utf-8")
    provider = Provider({})
    with pytest.raises(FormalizationError) as failure:
        formalize_idea(provider, idea_dir, frozen, output_dir=tmp_path / "translations")
    assert provider.calls == 0
    assert not (failure.value.directory / "translation.json").exists()
    assert events(failure.value.directory)[-1]["data"]["model_requests"] == 0


def test_source_changed_during_generation_keeps_usage_without_translation(queued, tmp_path, proposed):
    _, frozen, idea_dir = queued
    class Mutating(Provider):
        def complete(self, messages, schema):
            reply = super().complete(messages, schema)
            with (idea_dir / "idea.json").open("a", encoding="utf-8") as stream:
                stream.write(" ")
            return reply
    provider = Mutating(proposed)
    with pytest.raises(FormalizationError, match="cambió") as failure:
        formalize_idea(provider, idea_dir, frozen, output_dir=tmp_path / "translations")
    assert events(failure.value.directory)[-1]["data"]["usage"][0]["output_tokens"] == 40
    assert provider.calls == 1 and not (failure.value.directory / "translation.json").exists()


@pytest.mark.parametrize("change", ["extra", "permission", "results", "ambiguous_with_spec", "proposed_null",
                                    "empty_reason", "long_reason", "status", "future", "code", "window"])
def test_invalid_translations_never_become_approved_rules(proposed, change):
    if change == "extra": proposed["cost_rate"] = "0"
    elif change == "permission": proposed["executable"] = True
    elif change == "results": proposed["return_percent"] = "100"
    elif change == "ambiguous_with_spec": proposed["status"] = "needs_clarification"
    elif change == "proposed_null": proposed["spec"] = None
    elif change == "empty_reason": proposed["reason"] = "  "
    elif change == "long_reason": proposed["reason"] = "a" * 601
    elif change == "status": proposed["status"] = "approved"
    elif change == "future": proposed["spec"]["entry"]["conditions"][0]["left"]["lag"] = -1
    elif change == "code": proposed["spec"]["entry"] = "exec('no')"
    elif change == "window": proposed["spec"]["entry"]["conditions"][0]["left"] = {"kind": "sma", "window": 253, "lag": 0}
    with pytest.raises((ValueError, TypeError)):
        validate_translation(proposed)


@pytest.mark.parametrize("response", ['not JSON', '{"status":"unsupported","status":"proposed","reason":"x","spec":null}',
                                     '{"status":"unsupported","reason":"x","spec":NaN}',
                                     {"status": "proposed", "reason": "x", "spec": None},
                                     ProviderError("truncated", {"output_tokens": 384, "api_cost_usd": "0"}),
                                     ProviderError("unavailable")])
def test_invalid_replies_and_errors_preserve_consumption_without_retry(queued, tmp_path, response):
    _, frozen, idea_dir = queued
    provider = Provider(response)
    with pytest.raises(FormalizationError) as failure:
        formalize_idea(provider, idea_dir, frozen, output_dir=tmp_path / "translations")
    log = events(failure.value.directory)
    assert provider.calls == 1 and log[-1]["data"]["model_requests"] == 1
    assert log[-1]["event"] == "formalization_failed"
    assert not (failure.value.directory / "translation.json").exists()
    if not isinstance(response, ProviderError):
        assert log[-1]["data"]["usage"][0]["output_tokens"] == 40
        assert any(item["event"] == "model_response" for item in log)
    elif response.usage is None:
        assert log[-1]["data"]["api_cost_usd"] is None
    else:
        assert log[-1]["data"]["usage"][0]["output_tokens"] == 384


def test_semantics_are_never_claimed_verified_even_with_a_valid_spec(queued, tmp_path, proposed):
    # Un validador de formato no demuestra equivalencia con lenguaje natural.
    _, frozen, idea_dir = queued
    result = formalize_idea(Provider(proposed), idea_dir, frozen, output_dir=tmp_path / "translations")
    assert read_json(result / "translation.json")["semantic_equivalence_verified"] is False


def test_cli_uses_explicit_source_and_does_not_enable_openai(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("trading_ai.formalization.create_provider", lambda config: (_ for _ in ()).throw(ValueError("OpenAI reservado")))
    with pytest.raises(SystemExit) as failure:
        main(["--idea-run", str(tmp_path / "idea"), "--frozen-run", str(tmp_path / "frozen"), "--provider", "openai"])
    assert failure.value.code == 1 and "OpenAI reservado" in capsys.readouterr().err
    assert not (tmp_path / "idea").exists()


def test_repeated_calls_create_distinct_evidence_without_overwriting(queued, tmp_path):
    _, frozen, idea_dir = queued
    provider = Provider({"status": "needs_clarification", "reason": "Falta definir la salida.", "spec": None})
    first = formalize_idea(provider, idea_dir, frozen, output_dir=tmp_path / "translations")
    raw = (first / "translation.json").read_bytes()
    second = formalize_idea(provider, idea_dir, frozen, output_dir=tmp_path / "translations")
    assert first != second and (first / "translation.json").read_bytes() == raw
    assert provider.calls == 2
