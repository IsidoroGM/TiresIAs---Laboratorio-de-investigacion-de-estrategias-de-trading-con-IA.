"""Cobertura en una petición preparada, sin recomendar reglas o conceder presupuesto."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews
from test_compact_request import duplicate_memory
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from trading_ai.compact_request import prepare_compact_request
from trading_ai.guided_compact_request import prepare_guided_request, verify_guided_request, main
from trading_ai.rule_coverage import capture_rule_coverage
from trading_ai.structured_draft_request import verify_draft_request
from trading_ai import guided_compact_request as guided
from trading_ai import structured_generation as generation


@pytest.fixture
def sources(duplicate_memory, memory, tmp_path):
    context = Path(json.loads((memory / "reviews.json").read_bytes())["context"]["directory"])
    coverage = capture_rule_coverage(context, history_dir=duplicate_memory, output_dir=tmp_path / "coverage")
    prepared = prepare_compact_request(duplicate_memory, output_dir=tmp_path / "prepared")
    return prepared, coverage


def test_guide_preserves_payload_and_all_controls_without_model_or_new_budget(sources, tmp_path, transport, monkeypatch):
    prepared, coverage = sources
    before = {path: path.read_bytes() for folder in sources for path in folder.iterdir()}
    claim, = generation.ACCESS_ROOT.glob("*.json")
    claim_raw = claim.read_bytes()
    def forbidden(*args, **kwargs): pytest.fail("La guía no puede consultar, calcular o liberar intentos")
    for name in ("trading_ai.compact_ollama.CompactOllamaProvider.complete", "trading_ai.compact_ollama.CompactOllamaProvider.describe",
                 "trading_ai.rule_execution._calculate", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    run = prepare_guided_request(prepared, coverage, output_dir=tmp_path / "guided")
    checked = verify_guided_request(run)
    raw = json.loads((run / "request.json").read_bytes())
    original = json.loads((prepared / "request.json").read_bytes())
    body = json.loads(raw["messages"][1]["content"])
    guide = body.pop("typed_rule_coverage")
    assert body == json.loads(original["messages"][1]["content"]) and raw["schema"] == original["schema"]
    assert raw["messages"][0]["content"] == original["messages"][0]["content"] + guided.NOTE
    assert guide["rules"] == guide["templates"] == 1 and guide["proves_novelty"] is False
    assert guide["scope"] == "captured_rules_only" and "rolling_min" in guide["not_observed_direct_kinds"]
    assert checked["submitted"] is checked["generation_ready"] is checked["new_generation_permission"] is checked["executable"] is False
    assert checked["generation_budget"]["consumed"] is True and checked["token_count"] is None
    assert checked["new_usage"]["model_requests"] == checked["new_usage"]["backtests"] == 0
    assert checked["history_entries_omitted"] == 0 and checked["history_text_truncated"] is False
    assert len(transport.model_calls) == 1 and claim.read_bytes() == claim_raw
    assert all(path.read_bytes() == raw for path, raw in before.items())
    with pytest.raises((OSError, ValueError, KeyError)): verify_draft_request(run)


def test_oversize_guide_does_not_truncate_the_previous_payload(sources, tmp_path, monkeypatch):
    monkeypatch.setattr(guided, "MAX_REQUEST_BYTES", 1)
    with pytest.raises(ValueError, match="recortarán"):
        prepare_guided_request(*sources, output_dir=tmp_path / "guided")
    run, = (tmp_path / "guided").iterdir()
    assert not (run / "request.json").exists() and not (run / "guided.json").exists()


@pytest.mark.parametrize("filename", ["request.json", "guided.json", "guided.json.sha256", "events.jsonl"])
def test_changed_guided_request_is_detected(sources, tmp_path, filename):
    run = prepare_guided_request(*sources, output_dir=tmp_path / "guided")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_guided_request(run)


@pytest.mark.parametrize("change", ["reference", "missing_identity"])
def test_coverage_cannot_be_attached_to_an_unrelated_or_incomplete_context(sources, tmp_path, monkeypatch, change):
    actual = guided.verify_rule_coverage
    def changed(*args):
        coverage = deepcopy(actual(*args))
        if change == "reference": coverage["reference"]["development_sha256"] = "f" * 64
        else: coverage["occurrences"][0]["spec_sha256"] = "f" * 64
        return coverage
    monkeypatch.setattr(guided, "verify_rule_coverage", changed)
    with pytest.raises(ValueError): prepare_guided_request(*sources, output_dir=tmp_path / "guided")


def test_cli_never_exposes_a_send_action(sources, tmp_path, capsys):
    main(["prepare", "--prepared-run", str(sources[0]), "--coverage-run", str(sources[1]), "--output-dir", str(tmp_path / "guided")])
    main(["verify", "--run", capsys.readouterr().out.strip()])
    assert json.loads(capsys.readouterr().out)["new_generation_permission"] is False
    with pytest.raises(SystemExit): main(["send", "--run", str(sources[0])])
