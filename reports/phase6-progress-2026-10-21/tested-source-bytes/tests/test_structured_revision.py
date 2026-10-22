"""Reformulación tipada: un intento por origen, linaje conservado y ninguna cadena o simulación."""

from copy import deepcopy
from pathlib import Path

import pytest

from test_discovery import Provider, events, read_json, registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_pipeline import assessment_for
from trading_ai.ai import ProviderError, ProviderReply
from trading_ai.structured_planning import review_structured_idea
from trading_ai.structured_revision import (StructuredRevisionError, revise_structured_idea, verify_structured_revision)


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr("trading_ai.structured_ideas.ACCESS_ROOT", tmp_path / "ideas-access")
    monkeypatch.setattr("trading_ai.structured_revision.ACCESS_ROOT", tmp_path / "revision-access")


@pytest.fixture
def unclear(generated, tmp_path):
    split, frozen, original, _ = generated
    assessment = assessment_for(original, "needs_clarification")
    assessment["checks"]["exit_matches_hypothesis"] = False
    assessment["rationale"] = "La hipótesis necesita precisar la condición de salida, sin cambiar controles."
    review = review_structured_idea(original, frozen, assessment=assessment, output_dir=tmp_path / "reviews")
    return split, frozen, original, review


def test_one_revised_proposal_links_review_actual_prompt_and_consumption(unclear, proposal, tmp_path, monkeypatch):
    _, frozen, original, review = unclear
    before = {path: path.read_bytes() for folder in (original, review) for path in folder.iterdir()}
    proposal["exit"]["operator"] = "lt"
    provider = Provider(proposal)
    monkeypatch.setattr("trading_ai.rules.RuleStrategy.generate_signals", lambda *a: pytest.fail("Sin señales"))
    monkeypatch.setattr("trading_ai.experiments.run_backtest", lambda *a, **k: pytest.fail("Sin simulación"))
    run = revise_structured_idea(provider, review, frozen, output_dir=tmp_path / "revisions")
    record = verify_structured_revision(run, frozen)
    assert provider.calls == record["new_model_requests"] == record["inherited_model_requests"] == 1
    assert record["new_api_cost_usd"] == record["lineage_api_cost_usd"] == "0"
    assert record["depth"] == 1 and record["backtests"] == 0 and record["executable"] is False
    assert record["parent_review"]["directory"] == str(review)
    child = Path(record["child"]["directory"])
    assert read_json(child / "proposal.json")["proposal"] == proposal
    assert read_json(child / "proposal.json")["question"] == record["question"]
    assert record["question"] in provider.messages[-1]["content"] or "Reformular" in provider.messages[-1]["content"]
    assert all(path.read_bytes() == raw for path, raw in before.items())


def test_changing_review_reason_or_output_folder_does_not_release_second_attempt(unclear, proposal, tmp_path):
    _, frozen, original, review = unclear
    proposal["exit"]["operator"] = "lt"
    provider = Provider(proposal)
    revise_structured_idea(provider, review, frozen, output_dir=tmp_path / "first")
    assessment = assessment_for(original, "needs_clarification")
    assessment["rationale"] = "Otra explicación para el mismo origen."
    other = review_structured_idea(original, frozen, assessment=assessment, output_dir=tmp_path / "more-reviews")
    with pytest.raises(StructuredRevisionError, match="no se repetirá"):
        revise_structured_idea(provider, other, frozen, output_dir=tmp_path / "another")
    assert provider.calls == 1


def test_revised_child_cannot_start_a_revision_chain(unclear, proposal, tmp_path):
    _, frozen, _, review = unclear
    proposal["exit"]["operator"] = "lt"
    provider = Provider(proposal)
    run = revise_structured_idea(provider, review, frozen, output_dir=tmp_path / "revisions")
    child = Path(verify_structured_revision(run, frozen)["child"]["directory"])
    assessment = assessment_for(child, "needs_clarification")
    child_review = review_structured_idea(child, frozen, assessment=assessment, output_dir=tmp_path / "more-reviews")
    with pytest.raises(StructuredRevisionError, match="cadenas"):
        revise_structured_idea(provider, child_review, frozen, output_dir=tmp_path / "chain")
    assert provider.calls == 1


def test_unchanged_rules_are_recorded_as_duplicate_not_better(unclear, proposal, tmp_path):
    _, frozen, _, review = unclear
    proposal["title"] = "Solo otro título"
    run = revise_structured_idea(Provider(proposal), review, frozen, output_dir=tmp_path / "revisions")
    assert verify_structured_revision(run, frozen)["status"] == "duplicate_rules"


@pytest.mark.parametrize("decision", ["accepted", "rejected"])
def test_only_needs_clarification_review_can_request_revision(generated, proposal, tmp_path, decision):
    _, frozen, source, _ = generated
    review = review_structured_idea(source, frozen, assessment=assessment_for(source, decision), output_dir=tmp_path / "reviews")
    provider = Provider(proposal)
    with pytest.raises(StructuredRevisionError, match="needs_clarification"):
        revise_structured_idea(provider, review, frozen, output_dir=tmp_path / "revisions")
    assert provider.calls == 0


def test_failed_child_generation_keeps_claim_raw_usage_and_child_error_path(unclear, tmp_path):
    _, frozen, _, review = unclear
    provider = Provider(ProviderError("truncada", {"output_tokens": 384, "api_cost_usd": "0"}))
    with pytest.raises(StructuredRevisionError) as failure:
        revise_structured_idea(provider, review, frozen, output_dir=tmp_path / "revisions")
    data = events(failure.value.directory)[-1]["data"]
    assert data["access_claimed"] is True and data["child_run"]
    child = Path(data["child_run"])
    assert events(child)[-1]["data"]["usage"][0]["output_tokens"] == 384
    with pytest.raises(StructuredRevisionError, match="no se repetirá"):
        revise_structured_idea(provider, review, frozen, output_dir=tmp_path / "again")
    assert provider.calls == 1


@pytest.mark.parametrize("name", ["lineage.json", "revision.json", "events.jsonl"])
def test_changed_lineage_or_artifact_is_not_verified(unclear, proposal, tmp_path, name):
    _, frozen, _, review = unclear
    proposal["exit"]["operator"] = "lt"
    run = revise_structured_idea(Provider(proposal), review, frozen, output_dir=tmp_path / "revisions")
    with (run / name).open("ab") as stream: stream.write(b' ')
    with pytest.raises((ValueError, KeyError)): verify_structured_revision(run, frozen)


def test_history_capacity_is_checked_before_claiming_or_contacting_model(unclear, proposal, tmp_path, monkeypatch):
    _, frozen, _, review = unclear
    monkeypatch.setattr("trading_ai.structured_revision.MAX_CLAIMS", 0)
    provider = Provider(proposal)
    with pytest.raises(StructuredRevisionError, match="límite"):
        revise_structured_idea(provider, review, frozen, output_dir=tmp_path / "revisions")
    assert provider.calls == 0 and list((tmp_path / "revision-access").glob("*.json")) == []


def test_unknown_child_cost_remains_unknown_for_the_whole_lineage(unclear, proposal, tmp_path):
    _, frozen, _, review = unclear
    proposal["exit"]["operator"] = "lt"
    class PartialUsage(Provider):
        def complete(self, messages, schema):
            reply = super().complete(messages, schema)
            return ProviderReply(reply.content, reply.model, {"input_tokens": 25, "output_tokens": 40})
    run = revise_structured_idea(PartialUsage(proposal), review, frozen, output_dir=tmp_path / "revisions")
    record = verify_structured_revision(run, frozen)
    assert record["new_api_cost_usd"] is None and record["lineage_api_cost_usd"] is None
    assert record["inherited_usage"][0]["api_cost_usd"] == "0"
