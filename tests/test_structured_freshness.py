"""Peticiones íntegras que pueden quedar antiguas por nuevo historial o reservas."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from test_discovery import Provider, idea, registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from test_structured_draft_context import claim_for
from trading_ai.discovery import discover_idea
from trading_ai.rule_planning import _canonical
from trading_ai.structured_draft_request import prepare_draft_request
from trading_ai.structured_ideas import propose_structured_idea
from trading_ai.structured_freshness import (capture_request_freshness, inspect_request_freshness, main,
                                           require_current_request, verify_request_freshness)
from trading_ai import structured_freshness as freshness
from trading_ai import structured_session as sessions


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr("trading_ai.structured_ideas.ACCESS_ROOT", tmp_path / "ideas-access")
    monkeypatch.setattr("trading_ai.rule_execution.ACCESS_ROOT", tmp_path / "execution-access")
    monkeypatch.setattr(sessions, "ACCESS_ROOT", tmp_path / "sessions-access")


@pytest.fixture
def prepared_request(memory, tmp_path):
    return prepare_draft_request(memory, output_dir=tmp_path / "requests")


def test_current_request_has_a_stable_fingerprint_without_generation_permission(prepared_request):
    first = require_current_request(prepared_request)
    second = require_current_request(prepared_request, expected_fingerprint=first["fingerprint"])
    assert first == second and first["status"] == "current"
    assert all(value["matches"] for value in first["comparisons"].values())
    assert first["comparison_mode"] == "optimistic_double_read_not_transactional"
    assert first["generation_ready"] is first["submitted"] is first["executable"] is False
    assert first["provider_context_fit_verified"] is False


def test_unfinished_rule_reservation_makes_old_request_stale(prepared_request, tmp_path):
    record = inspect_request_freshness(prepared_request)
    path = claim_for(record["reference"], "a" * 64, tmp_path / "interrupted")
    before = path.read_bytes()
    changed = inspect_request_freshness(prepared_request)
    assert changed["status"] == "stale" and not changed["comparisons"]["rule_claims"]["matches"]
    assert changed["comparisons"]["rules"]["matches"]
    with pytest.raises(ValueError, match="rule_claims"): require_current_request(prepared_request)
    assert path.read_bytes() == before and not (tmp_path / "interrupted").exists()


def test_new_session_reservation_is_seen_even_without_a_completed_session(prepared_request, tmp_path):
    record = inspect_request_freshness(prepared_request)
    identity = {"schema_version": 1, "reference": record["reference"], "proposal_sha256": "a" * 64}
    claim = {"schema_version": 1, "identity": identity, "session_dir": str(tmp_path / "unfinished-session")}
    path = sessions.ACCESS_ROOT / (sha256(_canonical(identity)).hexdigest() + ".json")
    path.write_bytes(_canonical(claim))
    changed = inspect_request_freshness(prepared_request)
    assert not changed["comparisons"]["session_claims"]["matches"]
    assert changed["comparisons"]["rule_claims"]["matches"]
    with pytest.raises(ValueError, match="session_claims"): require_current_request(prepared_request)


def test_new_legacy_idea_cannot_be_silently_left_out(prepared_request, idea, tmp_path):
    record = inspect_request_freshness(prepared_request)
    discover_idea(Provider(idea), Path(record["reference"]["frozen_dir"]), output_dir=tmp_path / "memory/discovery")
    changed = inspect_request_freshness(prepared_request)
    assert not changed["comparisons"]["legacy"]["matches"]
    with pytest.raises(ValueError, match="legacy"): require_current_request(prepared_request)


def test_new_registered_rule_changes_both_rules_and_consumed_identities(prepared_request, proposal, tmp_path):
    record = inspect_request_freshness(prepared_request)
    proposal["entry"]["right"]["value"] = "2"
    propose_structured_idea(Provider(proposal), record["reference"]["frozen_dir"], output_dir=tmp_path / "new-rules")
    changed = inspect_request_freshness(prepared_request)
    assert not changed["comparisons"]["rules"]["matches"]
    assert not changed["comparisons"]["rule_claims"]["matches"]


def test_fingerprint_from_another_check_cannot_be_substituted(prepared_request):
    with pytest.raises(ValueError, match="huella"):
        require_current_request(prepared_request, expected_fingerprint="0" * 64)


def test_history_change_during_double_read_is_rejected(prepared_request, monkeypatch):
    original, calls = freshness._current, []
    def changing(reference):
        value = original(reference)
        calls.append(reference)
        if len(calls) == 2:
            value = deepcopy(value)
            value["session_claims"].append({"changed_during_read": True})
        return value
    monkeypatch.setattr(freshness, "_current", changing)
    with pytest.raises(ValueError, match="durante"):
        inspect_request_freshness(prepared_request)


def test_capture_does_not_use_model_network_signals_or_outer_data(prepared_request, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail("Solo verificar vigencia")
    for name in ("trading_ai.ai.create_provider", "socket.create_connection", "socket.socket.connect",
                 "trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.experiments.run_backtest"):
        monkeypatch.setattr(name, forbidden)
    actual_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.name not in ("evaluation.xml", "comparison.json", "outcome.json")
        return actual_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    run = capture_request_freshness(prepared_request, output_dir=tmp_path / "freshness")
    assert verify_request_freshness(run)["new_usage"]["model_requests"] == 0


@pytest.mark.parametrize("filename", ["freshness.json", "freshness.json.sha256", "events.jsonl"])
def test_changed_freshness_records_fail_verification(prepared_request, tmp_path, filename):
    run = capture_request_freshness(prepared_request, output_dir=tmp_path / "freshness")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_request_freshness(run)


def test_new_history_invalidates_previous_capture_and_can_be_captured_as_stale(prepared_request, tmp_path):
    run = capture_request_freshness(prepared_request, output_dir=tmp_path / "freshness")
    record = verify_request_freshness(run)
    claim_for(record["reference"], "a" * 64, tmp_path / "later")
    with pytest.raises(ValueError): verify_request_freshness(run)
    newer = capture_request_freshness(prepared_request, output_dir=tmp_path / "freshness")
    assert verify_request_freshness(newer)["status"] == "stale"


def test_changed_source_and_changed_location_are_rejected(prepared_request, tmp_path):
    run = capture_request_freshness(prepared_request, output_dir=tmp_path / "freshness")
    copied = tmp_path / "copied"
    shutil.copytree(run, copied)
    with pytest.raises(ValueError): verify_request_freshness(copied)
    with (prepared_request / "request.json").open("ab") as stream: stream.write(b' ')
    with pytest.raises(ValueError): inspect_request_freshness(prepared_request)


def test_cli_does_not_convert_current_into_permission(prepared_request, tmp_path, capsys):
    main(["capture", "--request-run", str(prepared_request), "--output-dir", str(tmp_path / "freshness")])
    main(["verify", "--run", capsys.readouterr().out.strip()])
    assert json.loads(capsys.readouterr().out)["generation_ready"] is False
