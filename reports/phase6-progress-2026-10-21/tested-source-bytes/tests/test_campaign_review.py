"""Capturas y decisiones artificiales: no se afirma autoría, mejora o transporte real."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from test_campaign_attempts import observation
from test_structured_draft import draft
from test_structured_ideas import proposal
from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_experiment as plans
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_plan as campaigns
from trading_ai import campaign_review as reviews
from trading_ai import rule_execution as engine
from trading_ai.experiments import ExperimentPolicy
from trading_ai.rule_planning import _canonical
from trading_ai.structured_draft import DRAFT_SCHEMA, describe_draft


@pytest.fixture
def review_roots(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_PATH", tmp_path / "ledger/registry.sqlite3")
    monkeypatch.setattr(attempts, "ACCESS_ROOT", tmp_path / "capture-access")
    monkeypatch.setattr(attempts, "ATTEMPTS_ROOT", tmp_path / "captures")
    monkeypatch.setattr(reviews, "ACCESS_ROOT", tmp_path / "review-access")
    monkeypatch.setattr(engine, "ACCESS_ROOT", tmp_path / "engine-access")


@pytest.fixture
def campaign_fixture(tmp_path, monkeypatch, request, draft, review_roots):
    """Metadatos guiados y congelados aislados; integración completa en otro test."""
    settings = getattr(request, "param", {})
    policy = ExperimentPolicy().parameters()
    content = b'<fixture-only-no-market-prices/>'
    digest = sha256(content).hexdigest()
    reference = {"frozen_dir": str(tmp_path / "frozen"), "frozen_sha256": "b" * 64,
                 "manifest_sha256": "c" * 64, "development_sha256": digest, "outer_cutoff": "2020-01-01"}
    source = {"name": "fixture-only", "sha256": digest, "first_date": "2001-01-01",
              "last_date": "2001-01-02", "observations": 2}
    objective = {"origin": "frozen_development_registration", "criterion": "higher_return_without_more_drawdown"}
    context = {"controls": policy, "objective": objective, "data": source, "known_history": True,
               "outer_evaluation_allowed": False, "compact_generation_budget": {"consumed": True, "new_permission_granted": False},
               "untrusted_history": {}, "untrusted_compact_history": [], "typed_rule_coverage": {},
               "consumed_rule_identities": [describe_draft(draft)["spec_sha256"]] if settings.get("duplicate") else []}
    raw = _canonical({"messages": [{"role": "system", "content": "Contrato artificial."},
                                    {"role": "user", "content": _canonical(context).decode()}], "schema": DRAFT_SCHEMA})
    packet = {"reference": reference, "request_sha256": sha256(raw).hexdigest(),
              "generation_budget": {"identity": {"development_sha256": digest, "pair": policy["pair"]}, "consumed": True},
              "inherited_attempt_usage": [{"model_requests": 1, "usage": [{"input_tokens": None}], "api_cost_usd": "0"}]}
    guided = tmp_path / "guided"
    guided.mkdir()
    for name, value in {"guided.json": _canonical(packet), "guided.json.sha256": b"fixture-only\n",
                        "request.json": raw, "events.jsonl": b'{"event":"fixture_only"}\n'}.items():
        (guided / name).write_bytes(value)
    initial = {path: path.read_bytes() for path in guided.iterdir()}
    def verified(path):
        assert Path(path) == guided
        if any(path.read_bytes() != value for path, value in initial.items()): raise ValueError("Memoria artificial cambiada.")
        return deepcopy(packet)
    monkeypatch.setattr(campaigns, "verify_guided_request", verified)
    frozen = {"policy": policy, "proposal": {"criterion": objective["criterion"]}, "development_result": {"source": source}}
    def development(path):
        assert Path(path) == Path(reference["frozen_dir"])
        return deepcopy(frozen), deepcopy(reference), content
    monkeypatch.setattr(plans, "_development", development)
    campaign = campaigns.prepare_campaign_plan(guided, settings.get("limits", {"max_proposals": 3, "max_backtests": 6}),
                                               output_dir=tmp_path / "campaign")
    scope = ledger.register_campaign(campaign)["scope_id"]
    key = sha256(raw).hexdigest()
    ledger.reserve_proposal(scope, key)
    capture = attempts.prepare_attempt(scope, raw)
    attempts.mark_submission_intent(scope, key)
    observed = observation(content=json.dumps(draft))
    attempts.record_observation(scope, key, observed)
    return {"scope": scope, "key": key, "capture": capture, "raw": observed, "frozen": frozen,
            "reference": reference, "content": content, "guided": guided, "campaign": campaign}


def assessment(candidate, decision="accepted"):
    return {"schema_version": 1, **candidate["binding"], "reviewer": "Revisor artificial",
            "decision": decision, "rationale": "Comprobación técnica de reglas; no se afirma rentabilidad.",
            "checks": {name: True for name in reviews.CHECKS}}


@pytest.fixture
def reviewed(campaign_fixture, tmp_path):
    fixture = campaign_fixture
    candidate = reviews.inspect_candidate(fixture["scope"], fixture["key"])
    directory = reviews.review_capture(fixture["scope"], fixture["key"], assessment(candidate), output_dir=tmp_path / "reviews")
    return directory, fixture


@pytest.mark.parametrize("decision", ["accepted", "rejected", "needs_clarification"])
def test_explicit_review_keeps_exact_capture_and_never_authorizes_execution(campaign_fixture, tmp_path, monkeypatch, decision):
    fixture = campaign_fixture
    candidate = reviews.inspect_candidate(fixture["scope"], fixture["key"])
    before = ledger.LEDGER_PATH.read_bytes()
    def forbidden(*args, **kwargs): pytest.fail("Revisar no puede enviar, reservar cálculos o simular.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.compact_ollama.CompactOllamaProvider.describe", "trading_ai.rule_execution._calculate",
                 "trading_ai.campaign_ledger.reserve_comparison", "trading_ai.rules.RuleStrategy.generate_signals"):
        monkeypatch.setattr(name, forbidden)
    declaration = assessment(candidate, decision)
    run = reviews.review_capture(fixture["scope"], fixture["key"], declaration, output_dir=tmp_path / "reviews")
    record = reviews.verify_review(run)
    assert record["status"] == decision and record["eligible_for_plan"] == (decision == "accepted")
    assert record["execution_authorized"] is record["transport_verified"] is False
    assert record["calculated_results"] is None and record["new_usage"] == reviews.ZERO_USAGE
    assert record["reason_origin"] == "unverified_reviewer_declaration" and record["assessment"] == declaration
    assert record["prior_compact_usage"][0]["usage"][0]["input_tokens"] is None
    assert record["attempt_usage"]["model_requests"] == 1
    assert (fixture["capture"] / "observation.raw").read_bytes() == fixture["raw"]
    assert ledger.LEDGER_PATH.read_bytes() == before and not engine.ACCESS_ROOT.exists()
    assert reviews.inspect_reviews(fixture["scope"])["reviews"][0]["status"] == decision
    with pytest.raises(reviews.CampaignReviewError, match="consumida"):
        reviews.review_capture(fixture["scope"], fixture["key"], declaration, output_dir=tmp_path / "another-directory")


@pytest.mark.parametrize("invalid", ["extra", "schema_bool", *reviews.BINDING_FIELDS, "reviewer", "rationale", "decision",
                                     "missing_check", "non_bool_check", "false_accepted"])
def test_invalid_or_foreign_assessment_cannot_approve_a_capture(invalid):
    candidate = {"binding": {key: str(index) * 64 for index, key in enumerate(reviews.BINDING_FIELDS)}}
    value = assessment(candidate)
    if invalid == "extra": value["capital"] = "1000000"
    elif invalid == "schema_bool": value["schema_version"] = True
    elif invalid in reviews.BINDING_FIELDS: value[invalid] = "f" * 64
    elif invalid in ("reviewer", "rationale"): value[invalid] = " "
    elif invalid == "decision": value["decision"] = "profitable"
    elif invalid == "missing_check": value["checks"].pop(reviews.CHECKS[0])
    elif invalid == "non_bool_check": value["checks"][reviews.CHECKS[0]] = 1
    else: value["checks"][reviews.CHECKS[0]] = False
    with pytest.raises(ValueError): reviews.validate_assessment(value, candidate)


def test_invalid_assessment_is_logged_without_consuming_review(campaign_fixture, tmp_path):
    fixture = campaign_fixture
    declaration = assessment(reviews.inspect_candidate(fixture["scope"], fixture["key"]))
    declaration["checks"][reviews.CHECKS[0]] = False
    with pytest.raises(reviews.CampaignReviewError) as failure:
        reviews.review_capture(fixture["scope"], fixture["key"], declaration, output_dir=tmp_path / "reviews")
    assert not reviews.ACCESS_ROOT.exists()
    events = [json.loads(line) for line in (failure.value.directory / "events.jsonl").read_bytes().splitlines()]
    assert events[-1]["event"] == "campaign_review_failed" and events[-1]["data"]["new_usage"] == reviews.ZERO_USAGE


@pytest.mark.parametrize("campaign_fixture", [{"duplicate": True}], indirect=True)
def test_historical_duplicate_cannot_be_reviewed_or_reformulated(campaign_fixture, tmp_path):
    fixture = campaign_fixture
    with pytest.raises(reviews.CampaignReviewError, match="duplicados"):
        reviews.review_capture(fixture["scope"], fixture["key"], {}, output_dir=tmp_path / "reviews")
    assert not reviews.ACCESS_ROOT.exists() and ledger.inspect_campaign(fixture["scope"])["reserved_model_requests"] == 1


def test_failure_after_claim_is_preserved_and_cannot_be_retried(campaign_fixture, tmp_path, monkeypatch):
    fixture = campaign_fixture
    declaration = assessment(reviews.inspect_candidate(fixture["scope"], fixture["key"]))
    original = reviews._record
    def interrupted(*args): raise OSError("Interrupción artificial después de la reserva")
    monkeypatch.setattr(reviews, "_record", interrupted)
    with pytest.raises(reviews.CampaignReviewError):
        reviews.review_capture(fixture["scope"], fixture["key"], declaration, output_dir=tmp_path / "interrupted")
    monkeypatch.setattr(reviews, "_record", original)
    summary = reviews.inspect_reviews(fixture["scope"])
    assert summary["requires_stop"] is True and summary["reviews"][0]["status"] == "unverifiable_review"
    with pytest.raises(reviews.CampaignReviewError, match="consumida"):
        reviews.review_capture(fixture["scope"], fixture["key"], declaration, output_dir=tmp_path / "retry")
    assert len(list(reviews.ACCESS_ROOT.glob("*.json"))) == 1


@pytest.mark.parametrize("filename", ["review.json", "review.json.sha256", "candidate.json", "assessment.json", "events.jsonl"])
def test_tampered_review_artifact_is_detected(reviewed, filename):
    directory, _ = reviewed
    with (directory / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises((ValueError, OSError)): reviews.verify_review(directory)


def test_changed_source_or_claim_blocks_existing_review(reviewed):
    directory, fixture = reviewed
    claim, = reviews.ACCESS_ROOT.glob("*.json")
    original = claim.read_bytes()
    claim.write_bytes(original + b' ')
    with pytest.raises(ValueError): reviews.verify_review(directory)
    claim.write_bytes(original)
    with (fixture["capture"] / "observation.raw").open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): reviews.verify_review(directory)


def test_concurrent_review_cannot_override_first_decision(campaign_fixture, tmp_path):
    fixture = campaign_fixture
    declaration = assessment(reviews.inspect_candidate(fixture["scope"], fixture["key"]))
    def submit(index):
        value = deepcopy(declaration)
        value["decision"] = "accepted" if index == 0 else "rejected"
        try: return reviews.review_capture(fixture["scope"], fixture["key"], value, output_dir=tmp_path / "parallel")
        except reviews.CampaignReviewError: return None
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(submit, (0, 1)))
    successful = [path for path in results if path is not None]
    assert len(successful) == 1 and len(list(reviews.ACCESS_ROOT.glob("*.json"))) == 1
    assert reviews.verify_review(successful[0])["status"] in ("accepted", "rejected")


def test_review_cannot_be_approved_retroactively_after_comparison_reservation(campaign_fixture, tmp_path):
    fixture = campaign_fixture
    declaration = assessment(reviews.inspect_candidate(fixture["scope"], fixture["key"]))
    ledger.reserve_comparison(fixture["scope"], fixture["key"], "f" * 64)
    with pytest.raises(reviews.CampaignReviewError, match="después"):
        reviews.review_capture(fixture["scope"], fixture["key"], declaration, output_dir=tmp_path / "retroactive")
    assert not reviews.ACCESS_ROOT.exists()


def test_existing_review_remains_verifiable_after_later_reservation(reviewed):
    directory, fixture = reviewed
    original = reviews.verify_review(directory)
    ledger.reserve_comparison(fixture["scope"], fixture["key"], "f" * 64)
    assert reviews.verify_review(directory) == original


def test_status_of_no_reviews_does_not_write_or_grant_permission(campaign_fixture):
    fixture = campaign_fixture
    before = ledger.LEDGER_PATH.read_bytes()
    result = reviews.inspect_reviews(fixture["scope"])
    assert result["reviews"][0]["status"] == "not_reviewed" and result["execution_authorized"] is False
    assert result["current_source_freshness_verified"] is False and not reviews.ACCESS_ROOT.exists()
    assert ledger.LEDGER_PATH.read_bytes() == before


def test_cli_requires_explicit_assessment_and_has_no_execution(campaign_fixture, tmp_path, capsys):
    fixture = campaign_fixture
    reviews.main(["candidate", "--scope", fixture["scope"], "--request-sha", fixture["key"]])
    candidate = json.loads(capsys.readouterr().out)
    path = tmp_path / "assessment.json"
    path.write_bytes(_canonical(assessment(candidate, "rejected")))
    reviews.main(["review", "--scope", fixture["scope"], "--request-sha", fixture["key"], "--assessment", str(path),
                  "--output-dir", str(tmp_path / "reviews")])
    directory = capsys.readouterr().out.strip()
    reviews.main(["verify", "--run", directory])
    assert json.loads(capsys.readouterr().out)["status"] == "rejected"
    for action in ("activate", "execute", "retry", "generate"):
        with pytest.raises(SystemExit): reviews.main([action])
