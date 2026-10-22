"""Planes sin motor: metadatos artificiales y una integración de fuentes completas."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from test_campaign_review import campaign_fixture, review_roots, reviewed, assessment
from test_campaign_controller import captured
from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews
from test_compact_request import duplicate_memory
from test_discovery import registered
from test_guided_compact_request import sources
from test_holdout import setup
from test_structured_draft import draft
from test_structured_draft_request import memory
from test_structured_ideas import generated, proposal
from test_structured_session import session
from trading_ai import campaign_experiment as plans
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_plan as campaigns
from trading_ai import campaign_review as reviews
from trading_ai import rule_execution as engine
from trading_ai.guided_compact_request import prepare_guided_request
from trading_ai.holdout import EXECUTION_POLICY
from trading_ai.rule_planning import BUDGET, _canonical
from trading_ai.structured_draft import describe_draft
from trading_ai.validated_read_cache import ValidatedReadCache


def test_plan_keeps_frozen_controls_data_and_shared_identity_without_reservations(reviewed, tmp_path, monkeypatch):
    review_dir, fixture = reviewed
    before = ledger.LEDGER_PATH.read_bytes()
    def forbidden(*args, **kwargs): pytest.fail("Planificar no puede enviar, reservar o calcular.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.campaign_ledger.reserve_comparison", "trading_ai.campaign_ledger.reserve_proposal",
                 "trading_ai.rule_execution._calculate", "trading_ai.rules.RuleStrategy.generate_signals"):
        monkeypatch.setattr(name, forbidden)
    directory = plans.prepare_plan(review_dir, output_dir=tmp_path / "plans")
    plan = plans.verify_plan(directory)
    assert plan["policy"] == fixture["frozen"]["policy"]
    assert plan["criterion"] == fixture["frozen"]["proposal"]["criterion"]
    assert plan["candidate"]["spec_sha256"] == plan["binding"]["spec_sha256"]
    assert plan["data"]["sha256"] == sha256((directory / "development.xml").read_bytes()).hexdigest()
    assert plan["execution_policy"] == EXECUTION_POLICY and plan["execution_timing"] == "next_observation"
    assert plan["budget"] == BUDGET and plan["calculation_id"] == sha256(_canonical(engine._identity(plan))).hexdigest()
    assert plan["execution_authorized"] is plan["outer_evaluation_allowed"] is plan["executable"] is False
    assert plan["shared_calculation_claimed"] is False and plan["new_comparison_reservation"] is None
    assert plan["calculated_results"] is None and plan["new_usage"] == reviews.ZERO_USAGE
    assert ledger.LEDGER_PATH.read_bytes() == before and not engine.ACCESS_ROOT.exists()


@pytest.mark.parametrize("decision", ["rejected", "needs_clarification"])
def test_only_accepted_review_can_prepare_a_plan(campaign_fixture, tmp_path, decision):
    fixture = campaign_fixture
    candidate = reviews.inspect_candidate(fixture["scope"], fixture["key"])
    directory = reviews.review_capture(fixture["scope"], fixture["key"], assessment(candidate, decision), output_dir=tmp_path / "reviews")
    with pytest.raises(plans.CampaignPlanError, match="aceptada") as failure:
        plans.prepare_plan(directory, output_dir=tmp_path / "plans")
    assert not (failure.value.directory / "plan.json").exists()
    events = [json.loads(line) for line in (failure.value.directory / "events.jsonl").read_bytes().splitlines()]
    assert events[-1]["event"] == "campaign_experiment_plan_failed" and events[-1]["data"]["new_usage"] == reviews.ZERO_USAGE


@pytest.mark.parametrize("campaign_fixture", [{"limits": {"max_proposals": 1, "max_backtests": 0}}], indirect=True)
def test_zero_backtest_campaign_cannot_prepare_comparison(reviewed, tmp_path):
    with pytest.raises(plans.CampaignPlanError, match="dos backtests"):
        plans.prepare_plan(reviewed[0], output_dir=tmp_path / "plans")
    assert not engine.ACCESS_ROOT.exists()


def test_new_directory_or_technical_name_does_not_reset_shared_calculation_identity(reviewed, tmp_path):
    directory = plans.prepare_plan(reviewed[0], output_dir=tmp_path / "plans")
    plan = plans.verify_plan(directory)
    same = plans.verify_plan(plans.prepare_plan(reviewed[0], output_dir=tmp_path / "other-plans"))
    assert plan["calculation_id"] == same["calculation_id"]
    changed = deepcopy(plan)
    changed["candidate"]["spec"]["name"] = "other_name"
    changed["criterion"] = "ignored_for_calculation_identity"
    assert engine._identity(changed) == engine._identity(plan)
    engine.ACCESS_ROOT.mkdir()
    (engine.ACCESS_ROOT / (plan["calculation_id"] + ".json")).write_bytes(b'interrupted')
    assert plans.verify_plan(directory) == plan
    with pytest.raises(plans.CampaignPlanError, match="motor"):
        plans.prepare_plan(reviewed[0], output_dir=tmp_path / "cannot-reopen")


def test_existing_comparison_blocks_preparation_but_not_verification_of_existing_plan(reviewed, tmp_path):
    review_dir, fixture = reviewed
    directory = plans.prepare_plan(review_dir, output_dir=tmp_path / "plans")
    plan = plans.verify_plan(directory)
    ledger.reserve_comparison(fixture["scope"], fixture["key"], plan["calculation_id"])
    assert plans.verify_plan(directory) == plan
    with pytest.raises(plans.CampaignPlanError, match="reservada"):
        plans.prepare_plan(review_dir, output_dir=tmp_path / "blocked")
    assert ledger.inspect_campaign(fixture["scope"])["reserved_backtests"] == 2


@pytest.mark.parametrize("filename", ["plan.json", "plan.json.sha256", "events.jsonl", "development.xml"])
def test_plan_artifact_tampering_is_detected(reviewed, tmp_path, filename):
    directory = plans.prepare_plan(reviewed[0], output_dir=tmp_path / "plans")
    with (directory / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): plans.verify_plan(directory)


@pytest.mark.parametrize("change", ["capital", "criterion", "reference", "content"])
def test_changed_frozen_sources_cannot_be_planned(reviewed, tmp_path, monkeypatch, change):
    review_dir, fixture = reviewed
    original = plans._development
    def changed(path):
        frozen, reference, content = original(path)
        if change == "capital": frozen["policy"]["initial_capital"] = "999999"
        if change == "criterion": frozen["proposal"]["criterion"] = "lower_drawdown_without_lower_return"
        if change == "reference": reference["development_sha256"] = "f" * 64
        if change == "content": content += b' changed'
        return frozen, reference, content
    monkeypatch.setattr(plans, "_development", changed)
    with pytest.raises(plans.CampaignPlanError): plans.prepare_plan(review_dir, output_dir=tmp_path / "plans")
    assert not engine.ACCESS_ROOT.exists()


def test_reservation_race_after_copy_leaves_failed_journal_without_plan(reviewed, tmp_path, monkeypatch):
    review_dir, fixture = reviewed
    original = plans._available
    seen = []
    def changed(record):
        seen.append(None)
        if len(seen) == 2: ledger.reserve_comparison(fixture["scope"], fixture["key"], record["calculation_id"])
        return original(record)
    monkeypatch.setattr(plans, "_available", changed)
    with pytest.raises(plans.CampaignPlanError) as failure:
        plans.prepare_plan(review_dir, output_dir=tmp_path / "plans")
    assert (failure.value.directory / "development.xml").exists() and not (failure.value.directory / "plan.json").exists()
    assert ledger.inspect_campaign(fixture["scope"])["reserved_backtests"] == 2


def test_cli_prepares_and_verifies_but_cannot_execute(reviewed, tmp_path, capsys):
    plans.main(["prepare", "--review-run", str(reviewed[0]), "--output-dir", str(tmp_path / "plans")])
    directory = capsys.readouterr().out.strip()
    plans.main(["verify", "--run", directory])
    assert json.loads(capsys.readouterr().out)["executable"] is False
    with pytest.raises(SystemExit): plans.main(["execute", "--run", directory])


def test_legacy_executors_reject_new_campaign_contract_before_any_calculation(reviewed, tmp_path, monkeypatch):
    from trading_ai.compact_execution import execute_compact_plan
    review_dir, fixture = reviewed
    directory = plans.prepare_plan(review_dir, output_dir=tmp_path / "plans")
    before = ledger.LEDGER_PATH.read_bytes()
    def forbidden(*args, **kwargs): pytest.fail("Un contrato nuevo no puede activar un ejecutor histórico.")
    for name in ("socket.socket.connect", "trading_ai.rule_execution._calculate",
                 "trading_ai.compact_execution.compile_rule_strategy", "trading_ai.campaign_ledger.reserve_comparison"):
        monkeypatch.setattr(name, forbidden)
    with pytest.raises((ValueError, OSError)):
        execute_compact_plan(directory, output_dir=tmp_path / "old-compact")
    with pytest.raises((ValueError, OSError)):
        engine.execute_rule_plan(directory, Path(fixture["reference"]["frozen_dir"]), output_dir=tmp_path / "old-rules")
    assert not engine.ACCESS_ROOT.exists() and ledger.LEDGER_PATH.read_bytes() == before


def test_complete_guided_capture_review_plan_integration_uses_only_known_development(
        sources, tmp_path, transport, monkeypatch, review_roots):
    def forbidden(*args, **kwargs): pytest.fail("La integración no debe consultar modelos o calcular.")
    original_open = Path.open
    def guarded(path, *args, **kwargs):
        if path.name in ("evaluation.xml", "comparison.json"): pytest.fail("No se permite evaluación exterior.")
        return original_open(path, *args, **kwargs)
    with ValidatedReadCache():
        guided = prepare_guided_request(*sources, output_dir=tmp_path / "guided-real-contract")
        campaign = campaigns.prepare_campaign_plan(guided, {"max_proposals": 1, "max_backtests": 2}, output_dir=tmp_path / "campaign")
        scope = ledger.register_campaign(campaign)["scope_id"]
        draft = {"entry": {"left": {"kind": "reference", "lag": 0}, "operator": "gt",
                           "right": {"kind": "constant", "value": "2"}},
                 "exit": {"left": {"kind": "reference", "lag": 0}, "operator": "lte",
                          "right": {"kind": "constant", "value": "2"}}}
        # Regla artificial para el contrato, sin buscar ni calcular su rendimiento.
        key, _, _ = captured((scope, (campaign / "request.json").read_bytes()), content=json.dumps(draft))
        for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                     "trading_ai.compact_ollama.CompactOllamaProvider.describe", "trading_ai.rule_execution._calculate",
                     "trading_ai.structured_generation.reserve_compact_generation", "trading_ai.campaign_ledger.reserve_comparison"):
            monkeypatch.setattr(name, forbidden)
        monkeypatch.setattr(Path, "open", guarded)
        candidate = reviews.inspect_candidate(scope, key)
        review = reviews.review_capture(scope, key, assessment(candidate), output_dir=tmp_path / "reviews")
        directory = plans.prepare_plan(review, output_dir=tmp_path / "plans")
        plan = plans.verify_plan(directory)
        assert plan["candidate"]["spec_sha256"] == describe_draft(draft)["spec_sha256"]
        assert plan["execution_authorized"] is False and plan["new_usage"] == reviews.ZERO_USAGE
        assert ledger.inspect_campaign(scope)["reserved_backtests"] == 0 and len(transport.model_calls) == 1
        assert not engine.ACCESS_ROOT.exists()
