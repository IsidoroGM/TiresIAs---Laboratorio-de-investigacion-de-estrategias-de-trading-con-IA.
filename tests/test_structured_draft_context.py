"""Contexto conocido y reservas consumidas, sin consultas o ampliación de intentos."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from test_discovery import Provider, idea, registered
from test_holdout import setup
from test_structured_ideas import proposal, generated
from trading_ai.rule_planning import _canonical
from trading_ai.discovery import discover_idea
from trading_ai.formalization import formalize_idea
from trading_ai.structured_draft import preview_draft
from trading_ai.structured_draft_context import _claims, main, prepare_draft_context, verify_draft_context
from trading_ai import structured_ideas as ideas
from trading_ai import structured_draft_context as contexts


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr(ideas, "ACCESS_ROOT", tmp_path / "claims")


@pytest.fixture
def draft_run(tmp_path, proposal):
    path = tmp_path / "input.json"
    path.write_text(json.dumps({key: proposal[key] for key in ("entry", "exit")}), encoding="utf-8")
    return preview_draft(path, output_dir=tmp_path / "drafts")


def claim_for(reference, checksum, directory):
    identity = {"reference": reference, "spec_sha256": checksum}
    claim = {"schema_version": 1, "identity": identity, "run_dir": str(directory.resolve())}
    path = ideas.ACCESS_ROOT / (sha256(_canonical(identity)).hexdigest() + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical(claim))
    return path


def test_empty_context_uses_registered_controls_not_candidate_requests(registered, tmp_path):
    _, frozen = registered
    run = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    record = verify_draft_context(run)
    original = json.loads((frozen / "frozen.json").read_bytes())
    assert record["controls"] == original["policy"]
    assert record["objective"] == {"origin": "frozen_development_registration",
                                   "criterion": original["proposal"]["criterion"]}
    assert record["counts"] == {"legacy_ideas": 0, "registered_rules": 0, "consumed_rule_claims": 0}
    assert record["candidate"] is None and record["outer_evaluation_allowed"] is False
    assert record["generation_ready"] is record["eligible_for_session"] is record["executable"] is False
    assert record["review_decisions_complete"] is False
    assert record["new_usage"] == {"model_requests": 0, "input_tokens": 0, "output_tokens": 0,
                                    "api_cost_usd": "0", "backtests": 0}
    assert "return" not in record["data"] and "drawdown" not in record["data"]


def test_registered_rule_is_duplicate_across_formats(generated, draft_run, tmp_path):
    _, frozen, source, _ = generated
    original = {path: path.read_bytes() for path in source.iterdir()}
    run = prepare_draft_context(frozen, draft_dir=draft_run, output_dir=tmp_path / "contexts")
    record = verify_draft_context(run)
    assert record["counts"]["registered_rules"] == record["counts"]["consumed_rule_claims"] == 1
    assert record["candidate"]["identity_check"] == "duplicate_or_reserved"
    assert len(record["candidate"]["matching_claim_paths"]) == 1
    assert all(value is None for value in record["candidate"]["source_usage"].values())
    assert all(path.read_bytes() == raw for path, raw in original.items())


def test_interrupted_reservation_remains_consumed_without_a_completed_proposal(registered, draft_run, tmp_path):
    _, frozen = registered
    preview = json.loads((draft_run / "draft.json").read_bytes())
    from trading_ai.robustness import _development
    _, reference, _ = _development(frozen)
    path = claim_for(reference, preview["spec_sha256"], tmp_path / "failed-before-proposal")
    before = path.read_bytes()
    run = prepare_draft_context(frozen, draft_dir=draft_run, output_dir=tmp_path / "contexts")
    record = verify_draft_context(run)
    assert record["counts"]["registered_rules"] == 0 and record["counts"]["consumed_rule_claims"] == 1
    assert record["candidate"]["identity_check"] == "duplicate_or_reserved"
    assert path.read_bytes() == before and not (tmp_path / "failed-before-proposal").exists()


def test_not_found_is_not_an_approval_or_a_claim_of_novelty(registered, draft_run, tmp_path):
    _, frozen = registered
    run = prepare_draft_context(frozen, draft_dir=draft_run, output_dir=tmp_path / "contexts")
    record = verify_draft_context(run)
    assert record["candidate"]["identity_check"] == "not_found_in_captured_claims"
    assert record["candidate"]["eligible_for_session"] is record["generation_ready"] is False


def test_legacy_ideas_keep_their_previous_clarification_reasons(registered, idea, tmp_path):
    _, frozen = registered
    source = discover_idea(Provider(idea), frozen, output_dir=tmp_path / "memory/discovery")
    reason = "No se ha explicado el retardo de salida."
    formalize_idea(Provider({"status": "needs_clarification", "reason": reason, "spec": None}),
                   source, frozen, output_dir=tmp_path / "memory/formalization")
    run = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    record = verify_draft_context(run)
    assert record["counts"]["legacy_ideas"] == 1
    memory = json.loads((run / "memory.json").read_bytes())
    assert memory["entries"][0]["unverified_reasons"] == [reason]
    assert "needs_clarification" in memory["entries"][0]["statuses"]
    assert record["new_usage"]["model_requests"] == 0


def test_changed_reservations_during_capture_stop_the_context(registered, tmp_path, monkeypatch):
    _, frozen = registered
    calls = []
    def changing(reference):
        calls.append(reference)
        if len(calls) == 2:
            claim_for(reference, "a" * 64, tmp_path / "concurrent-reservation")
        return _claims(reference)
    monkeypatch.setattr(contexts, "_claims", changing)
    with pytest.raises(ValueError, match="cambiaron"):
        prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    run, = (tmp_path / "contexts").iterdir()
    assert not (run / "context.json").exists()
    events = [json.loads(line) for line in (run / "events.jsonl").read_bytes().splitlines()]
    assert events[-1]["event"] == "structured_draft_context_failed"
    assert events[-1]["data"]["new_model_requests"] == events[-1]["data"]["backtests"] == 0


def test_new_claims_do_not_rewrite_a_historical_snapshot(registered, tmp_path):
    _, frozen = registered
    run = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    record = verify_draft_context(run)
    claim_for(record["reference"], "a" * 64, tmp_path / "later-reservation")
    assert verify_draft_context(run) == record
    newer = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    assert verify_draft_context(newer)["counts"]["consumed_rule_claims"] == 1


def test_foreign_development_claim_is_not_applied_to_this_candidate(registered, draft_run, tmp_path):
    _, frozen = registered
    first = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    reference = deepcopy(verify_draft_context(first)["reference"])
    reference["frozen_dir"] = str(tmp_path / "other-context")
    checksum = json.loads((draft_run / "draft.json").read_bytes())["spec_sha256"]
    claim_for(reference, checksum, tmp_path / "foreign-reservation")
    run = prepare_draft_context(frozen, draft_dir=draft_run, output_dir=tmp_path / "contexts")
    assert verify_draft_context(run)["candidate"]["identity_check"] == "not_found_in_captured_claims"


def test_capture_does_not_use_model_generate_signals_or_read_outer_data(registered, draft_run, tmp_path, monkeypatch):
    _, frozen = registered
    def prohibited(*args, **kwargs): pytest.fail("Contexto y memoria, sin cálculo o modelo")
    for name in ("trading_ai.ai.create_provider", "trading_ai.rules.RuleStrategy.generate_signals",
                 "trading_ai.experiments.run_backtest", "socket.create_connection", "socket.socket.connect"):
        monkeypatch.setattr(name, prohibited)
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.name not in ("evaluation.xml", "comparison.json")
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    run = prepare_draft_context(frozen, draft_dir=draft_run, output_dir=tmp_path / "contexts")
    assert verify_draft_context(run)["new_usage"]["backtests"] == 0


@pytest.mark.parametrize("filename", ["context.json", "context.json.sha256", "memory.json", "rules-memory.json",
                                      "claims.json", "report.md", "events.jsonl"])
def test_artifact_changes_are_detected(registered, tmp_path, filename):
    _, frozen = registered
    run = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_draft_context(run)


def test_changed_shared_claim_invalidates_its_snapshot(generated, tmp_path):
    _, frozen, _, _ = generated
    run = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    path, = ideas.ACCESS_ROOT.glob("*.json")
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError): verify_draft_context(run)


def test_changed_candidate_invalidates_context(registered, draft_run, tmp_path):
    _, frozen = registered
    run = prepare_draft_context(frozen, draft_dir=draft_run, output_dir=tmp_path / "contexts")
    with (draft_run / "input.json").open("ab") as stream: stream.write(b' ')
    with pytest.raises(ValueError): verify_draft_context(run)


def test_too_many_claims_are_not_silently_dropped(registered, tmp_path, monkeypatch):
    _, frozen = registered
    run = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    reference = verify_draft_context(run)["reference"]
    claim_for(reference, "a" * 64, tmp_path / "a")
    claim_for(reference, "b" * 64, tmp_path / "b")
    monkeypatch.setattr(ideas, "MAX_HISTORY", 1)
    with pytest.raises(ValueError, match="límite"):
        prepare_draft_context(frozen, output_dir=tmp_path / "contexts")


def test_wrong_claim_filename_is_rejected(registered, tmp_path):
    _, frozen = registered
    run = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    path = claim_for(verify_draft_context(run)["reference"], "a" * 64, tmp_path / "a")
    path.rename(path.with_name("incorrect.json"))
    with pytest.raises(ValueError, match="identidad"):
        prepare_draft_context(frozen, output_dir=tmp_path / "contexts")


def test_location_change_cannot_silently_rebind_context(registered, tmp_path):
    _, frozen = registered
    run = prepare_draft_context(frozen, output_dir=tmp_path / "contexts")
    copied = tmp_path / "copied"
    shutil.copytree(run, copied)
    with pytest.raises(ValueError): verify_draft_context(copied)


def test_cli_prepares_and_verifies_without_enabling_generation(registered, tmp_path, capsys):
    _, frozen = registered
    main(["prepare", "--frozen-run", str(frozen), "--output-dir", str(tmp_path / "contexts")])
    run = capsys.readouterr().out.strip()
    main(["verify", "--run", run])
    assert json.loads(capsys.readouterr().out)["generation_ready"] is False
