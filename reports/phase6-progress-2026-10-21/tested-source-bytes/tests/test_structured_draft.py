"""Contrato compacto sin prosa inventada, atribución al modelo o paso al simulador."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from test_structured_ideas import proposal
from trading_ai.structured_draft import (DRAFT_SCHEMA, MAX_DRAFT_BYTES, describe_draft, main,
                                        preview_draft, verify_draft)
from trading_ai.structured_ideas import compile_proposal
from trading_ai.structured_session import create_structured_session


@pytest.fixture
def draft(proposal):
    return {key: deepcopy(proposal[key]) for key in ("entry", "exit")}


@pytest.fixture
def source(tmp_path, draft):
    path = tmp_path / "synthetic-draft.json"
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_compact_contract_has_no_free_prose_and_keeps_rule_identity(draft, proposal):
    original = deepcopy(draft)
    result = describe_draft(draft)
    assert set(DRAFT_SCHEMA["properties"]) == set(DRAFT_SCHEMA["required"]) == {"entry", "exit"}
    assert DRAFT_SCHEMA["additionalProperties"] is False
    assert result["spec_sha256"] == compile_proposal(proposal).spec_sha256
    assert result["rule_description"]["entry"] == "Entrar largo cuando la referencia actual es mayor que el valor 1."
    assert result["model_description"] is None and result["hypothesis_supplied"] is False
    assert result["semantic_review_required"] is True and result["duplicate_history_checked"] is False
    assert result["eligible_for_session"] is False and result["executable"] is False
    assert result["calculated_results"] is None and draft == original
    assert "Adaptador técnico" not in json.dumps(result, ensure_ascii=False)
    assert "Sin hipótesis atribuida" not in json.dumps(result, ensure_ascii=False)


@pytest.mark.parametrize("key", ["title", "hypothesis", "capital", "cost", "budget", "results", "code", "source"])
def test_prose_controls_and_claimed_results_are_not_part_of_the_new_contract(draft, key):
    draft[key] = "No permitido"
    with pytest.raises(ValueError):
        describe_draft(draft)


@pytest.mark.parametrize("value", [None, [], "Comprar", {}, {"entry": {}}])
def test_missing_or_free_text_drafts_are_rejected(value):
    with pytest.raises(ValueError):
        describe_draft(value)


@pytest.mark.parametrize("change", ["future", "bool", "missing_window", "expression", "volume", "float", "alternatives"])
def test_compact_input_does_not_weaken_the_existing_rule_limits(draft, change):
    if change == "future": draft["entry"]["left"]["lag"] = -1
    elif change == "bool": draft["entry"]["left"]["lag"] = True
    elif change == "missing_window": draft["entry"]["right"] = {"kind": "ema", "lag": 0}
    elif change == "expression": draft["entry"] = "ema(20) > sma(60)"
    elif change == "volume": draft["entry"]["left"] = {"kind": "volume", "lag": 0}
    elif change == "float": draft["entry"]["right"]["value"] = 1.0
    else: draft["exit"] = [draft["exit"], deepcopy(draft["entry"])]
    with pytest.raises(ValueError): describe_draft(draft)


def test_preview_preserves_exact_input_bytes_and_unknown_source_consumption(source, tmp_path):
    raw = source.read_bytes()
    run = preview_draft(source, output_dir=tmp_path / "previews")
    record = verify_draft(run)
    assert (run / "input.json").read_bytes() == raw == source.read_bytes()
    assert record["input"]["sha256"] == sha256(raw).hexdigest()
    assert record["input"]["origin"] == "unattributed_external_input"
    assert all(value is None for value in record["source_usage"].values())
    assert record["new_usage"] == {"model_requests": 0, "input_tokens": 0, "output_tokens": 0,
                                    "api_cost_usd": "0", "backtests": 0}
    assert record["market_data_read"] is False and record["status"] == "offline_preview_only"
    source.write_text("Origen externo cambiado después de copiarlo.", encoding="utf-8")
    assert verify_draft(run) == record  # La fuente del registro es su copia exacta, no una ruta mutable.


def test_numeric_spelling_does_not_give_compact_rules_a_new_identity(draft):
    original = describe_draft(draft)
    draft["entry"]["right"]["value"] = "1.00"
    draft["exit"]["right"]["value"] = "1e0"
    alias = describe_draft(draft)
    assert alias["spec_sha256"] == original["spec_sha256"]
    assert alias["spec"] == original["spec"]
    assert alias["rule_description"] == original["rule_description"]
    assert draft["entry"]["right"]["value"] == "1.00"


def test_preview_uses_no_model_network_market_data_or_calculation(source, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Solo validar campos y describirlos")
    for name in ("trading_ai.ai.create_provider", "socket.create_connection", "socket.socket.connect",
                 "trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.experiments.run_backtest",
                 "trading_ai.robustness._development"):
        monkeypatch.setattr(name, forbidden)
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.name not in ("development.xml", "evaluation.xml", "comparison.json")
        assert not any(part.endswith("-access") for part in path.parts)
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    run = preview_draft(source, output_dir=tmp_path / "previews")
    assert verify_draft(run)["eligible_for_session"] is False


@pytest.mark.parametrize("raw", [b'{"entry": {}, "entry": {}, "exit": {}}', b'{"entry": NaN, "exit": {}}',
                                  b'{"entry": {}, "exit": {}}\xff', b'{"entry": {}, "exit":'])
def test_invalid_ambiguous_or_cut_off_json_is_recorded_as_failure(tmp_path, raw):
    path = tmp_path / "bad.json"
    path.write_bytes(raw)
    output = tmp_path / "previews"
    with pytest.raises(ValueError): preview_draft(path, output_dir=output)
    run, = output.iterdir()
    events = [json.loads(line) for line in (run / "events.jsonl").read_bytes().splitlines()]
    assert events[-1]["event"] == "structured_draft_failed"
    assert events[-1]["data"]["model_requests"] == events[-1]["data"]["backtests"] == 0
    assert not (run / "draft.json").exists()


def test_over_limit_input_is_rejected_before_json_parsing(tmp_path):
    path = tmp_path / "too-large.json"
    path.write_bytes(b' ' * (MAX_DRAFT_BYTES + 1))
    with pytest.raises(ValueError, match="demasiado grande"):
        preview_draft(path, output_dir=tmp_path / "previews")


@pytest.mark.parametrize("filename", ["input.json", "draft.json", "draft.json.sha256", "report.md", "events.jsonl"])
def test_artifact_tampering_is_detected(source, tmp_path, filename):
    run = preview_draft(source, output_dir=tmp_path / "previews")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_draft(run)


def test_copying_a_preview_cannot_change_its_sealed_location(source, tmp_path):
    run = preview_draft(source, output_dir=tmp_path / "previews")
    copied = tmp_path / "copied"
    shutil.copytree(run, copied)
    with pytest.raises(ValueError): verify_draft(copied)


def test_new_format_cannot_be_adopted_as_a_registered_proposal(source, tmp_path):
    run = preview_draft(source, output_dir=tmp_path / "previews")
    with pytest.raises((ValueError, OSError)):
        create_structured_session(run, tmp_path / "no-frozen-context", output_dir=tmp_path / "sessions")
    assert not (tmp_path / "sessions").exists()


def test_cli_preview_and_verify_are_explicit_about_description_origin(source, tmp_path, capsys):
    main(["preview", "--input", str(source), "--output-dir", str(tmp_path / "previews")])
    run = capsys.readouterr().out.strip()
    main(["verify", "--run", run])
    assert json.loads(capsys.readouterr().out)["origin"] == "python_from_validated_rules"
