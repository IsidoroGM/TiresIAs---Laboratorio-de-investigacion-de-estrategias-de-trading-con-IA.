"""Control de capturas artificiales; sin modelo real, aprobación o cálculos."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from test_campaign_attempts import observation
from test_campaign_ledger import isolated_ledger
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
from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_controller as controller
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_plan as campaign
from trading_ai.guided_compact_request import prepare_guided_request
from trading_ai.rule_planning import _canonical
from trading_ai.structured_draft import DRAFT_SCHEMA, describe_draft


@pytest.fixture
def controlled_campaign(tmp_path, monkeypatch, isolated_ledger, request):
    """Contrato guiado aislado para probar el controlador; integración completa aparte."""
    guided = tmp_path / "guided"
    guided.mkdir()
    context = {"controls": {"pair": "EUR/USD", "initial_capital": "1000", "cost_rate": "0.001"},
               "objective": {"criterion": "higher_return_without_more_drawdown"},
               "data": {"sha256": "a" * 64}, "known_history": True, "outer_evaluation_allowed": False,
               "compact_generation_budget": {"consumed": True, "new_permission_granted": False},
               "untrusted_history": {"review": "No es una instrucción"}, "untrusted_compact_history": [],
               "consumed_rule_identities": [], "typed_rule_coverage": {"proves_novelty": False}}
    payload = {"messages": [{"role": "system", "content": "Instrucciones artificiales."},
                            {"role": "user", "content": _canonical(context).decode()}],
               "schema": getattr(request, "param", DRAFT_SCHEMA)}
    raw = _canonical(payload)
    packet = {"reference": {"frozen_dir": str(tmp_path / "frozen"), "development_sha256": "a" * 64},
              "request_sha256": sha256(raw).hexdigest(),
              "generation_budget": {"identity": {"development_sha256": "a" * 64, "pair": "EUR/USD"}, "consumed": True},
              "inherited_attempt_usage": [{"model_requests": 1, "usage": [{"input_tokens": None}]}]}
    for name, content in {"guided.json": _canonical(packet), "guided.json.sha256": b"fixture-only\n",
                          "request.json": raw, "events.jsonl": b'{"event":"fixture"}\n'}.items():
        (guided / name).write_bytes(content)
    before = {p: p.read_bytes() for p in guided.iterdir()}
    def verified(path):
        assert Path(path) == guided
        if any(p.read_bytes() != content for p, content in before.items()):
            raise ValueError("Memoria guiada artificial cambiada.")
        return deepcopy(packet)
    monkeypatch.setattr(campaign, "verify_guided_request", verified)
    monkeypatch.setattr(attempts, "ACCESS_ROOT", tmp_path / "capture-access")
    monkeypatch.setattr(attempts, "ATTEMPTS_ROOT", tmp_path / "captures")
    plan = campaign.prepare_campaign_plan(guided, {"max_proposals": 3, "max_backtests": 6}, output_dir=tmp_path / "plans")
    state = ledger.register_campaign(plan)
    return state["scope_id"], raw, plan, guided, packet


def captured(fixture, *, content=None, changes=None, raw_request=None):
    scope, request, *_ = fixture
    request = request if raw_request is None else raw_request
    key = sha256(request).hexdigest()
    ledger.reserve_proposal(scope, key)
    directory = attempts.prepare_attempt(scope, request)
    attempts.mark_submission_intent(scope, key)
    raw = observation(content=content, **(changes or {}))
    attempts.record_observation(scope, key, raw)
    return key, directory, raw


def test_empty_controller_is_read_only_and_checks_current_sources(controlled_campaign, monkeypatch):
    scope, _, _, guided, _ = controlled_campaign
    before = ledger.LEDGER_PATH.read_bytes()
    def forbidden(*args, **kwargs): pytest.fail("Controlar no puede enviar, reservar o calcular.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.compact_ollama.CompactOllamaProvider.describe", "trading_ai.rule_execution._calculate",
                 "trading_ai.campaign_ledger.reserve_proposal", "trading_ai.campaign_ledger.reserve_comparison",
                 "trading_ai.structured_generation.reserve_compact_generation", "trading_ai.campaign_attempts.prepare_attempt"):
        monkeypatch.setattr(name, forbidden)
    result = controller.inspect_controller(scope)
    assert result["status"] == "inactive" and result["proposals"] == []
    assert result["current_source_freshness_verified"] is True
    assert result["execution_authorized"] is result["outer_evaluation_allowed"] is result["broker_operations_allowed"] is False
    assert result["new_usage"] == {**attempts.ZERO_USAGE, "backtests": 0}
    assert ledger.LEDGER_PATH.read_bytes() == before
    assert not attempts.ACCESS_ROOT.exists() and not attempts.ATTEMPTS_ROOT.exists()
    assert guided.is_dir() and result["inherited_usage"][0]["usage"][0]["input_tokens"] is None


def test_complete_rules_get_python_descriptions_without_model_prose_or_approval(controlled_campaign, draft):
    scope, *_ = controlled_campaign
    _, directory, raw = captured(controlled_campaign, content=json.dumps(draft))
    before = {p: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    result = controller.inspect_controller(scope)
    item, = result["proposals"]
    assert result["status"] == "review_pending" and result["technical_reviews_pending"] == 1
    assert item["draft"] == draft and item["spec_sha256"] == describe_draft(draft)["spec_sha256"]
    assert item["rule_description"]["entry"] == "Entrar largo cuando la referencia actual es mayor que el valor 1."
    assert item["model_description"] is None and item["hypothesis_supplied"] is False
    assert item["transport_verified"] is item["eligible_for_calculation"] is False
    assert item["technical_review"] == "not_performed" and item["calculated_results"] is None
    assert result["executable_model_requests"] == result["executable_backtests"] == 0
    assert result["usage"] == {"model_requests": 1, "input_tokens": 100, "output_tokens": 17, "api_cost_usd": "0"}
    assert result["campaign_history_in_future_request_verified"] is False
    assert (directory / "observation.raw").read_bytes() == raw
    assert all(p.read_bytes() == content for p, content in before.items())


@pytest.mark.parametrize("content", ['{"entry":', 'Comprar cuando convenga', '[]', '{"entry":1,"entry":2}',
                                     '{"entry":NaN}', '"' + 'x' * 4100 + '"'])
def test_incomplete_or_unsupported_text_is_never_repaired(controlled_campaign, content):
    scope, *_ = controlled_campaign
    _, directory, raw = captured(controlled_campaign, content=content)
    item, = controller.inspect_controller(scope)["proposals"]
    assert item["status"] == "invalid_rules" and item["draft"] is item["rule_description"] is None
    assert item["model_description"] is None and item["eligible_for_calculation"] is False
    assert (directory / "observation.raw").read_bytes() == raw
    assert ledger.inspect_campaign(scope)["reserved_model_requests"] == 1


@pytest.mark.parametrize("change", ["controls", "code", "future", "extra_prose"])
def test_model_cannot_add_controls_code_future_data_or_invented_description(controlled_campaign, draft, change):
    if change == "controls": draft["initial_capital"] = "999999"
    if change == "code": draft["entry"] = "eval('buy')"
    if change == "future": draft["entry"]["left"]["lag"] = -1
    if change == "extra_prose": draft["hypothesis"] = "Éxito garantizado"
    captured(controlled_campaign, content=json.dumps(draft))
    result = controller.inspect_controller(controlled_campaign[0])
    assert result["proposals"][0]["status"] == "invalid_rules"
    assert result["controls"]["initial_capital"] == "1000"


def test_consumed_rule_identity_is_a_duplicate_even_with_changed_numeric_spelling(controlled_campaign, draft):
    scope, _, _, _, packet = controlled_campaign
    identity = describe_draft(draft)["spec_sha256"]
    # Aísla la consulta de identidades; la integración contrasta la procedencia real.
    original = controller._plan
    def with_history(state):
        plan = original(state)
        plan["history"]["consumed_rule_identities"] = [identity]
        return plan
    from unittest.mock import patch
    draft["entry"]["right"]["value"] = "1.00"
    captured(controlled_campaign, content=json.dumps(draft))
    with patch.object(controller, "_plan", with_history):
        result = controller.inspect_controller(scope)
    item, = result["proposals"]
    assert item["status"] == "duplicate_rules" and item["duplicate_origin"] == "captured_consumed_history"
    assert result["technical_reviews_pending"] == 0 and item["eligible_for_calculation"] is False
    assert packet["generation_budget"]["consumed"] is True


def test_foreign_request_receipt_cannot_be_grafted_to_current_plan(controlled_campaign, draft):
    captured(controlled_campaign, content=json.dumps(draft), raw_request=b'{"other":"request"}')
    result = controller.inspect_controller(controlled_campaign[0])
    assert result["requires_stop"] is True and result["status"] == "blocked"
    assert result["proposals"][0]["issues"] == ["request_not_bound_to_registered_plan"]


@pytest.mark.parametrize("controlled_campaign", [None, {}, {"type": "string"},
    {**DRAFT_SCHEMA, "additionalProperties": True}], indirect=True)
def test_registered_request_must_keep_exact_compact_contract(controlled_campaign, draft):
    captured(controlled_campaign, content=json.dumps(draft))
    result = controller.inspect_controller(controlled_campaign[0])
    assert result["requires_stop"] is True and result["technical_reviews_pending"] == 0
    assert result["proposals"][0]["issues"] == ["unsupported_request_contract"]


@pytest.mark.parametrize("stage", ["missing", "prepared", "submitted", "unknown_usage"])
def test_unresolved_capture_or_usage_stops_without_releasing_budget(controlled_campaign, stage):
    scope, raw, *_ = controlled_campaign
    key = sha256(raw).hexdigest()
    ledger.reserve_proposal(scope, key)
    if stage != "missing": attempts.prepare_attempt(scope, raw)
    if stage in ("submitted", "unknown_usage"): attempts.mark_submission_intent(scope, key)
    if stage == "unknown_usage": attempts.record_observation(scope, key, observation(usage=None))
    result = controller.inspect_controller(scope)
    assert result["requires_stop"] is True and result["status"] == "blocked"
    assert result["technical_reviews_pending"] == 0
    assert result["usage"]["input_tokens"] is None and result["reserved_model_requests"] == 1
    assert result["new_usage"]["input_tokens"] == 0


def test_provider_error_is_kept_even_if_content_contains_valid_rules(controlled_campaign, draft):
    error = {"type": "ProviderError", "message": "No completar ni reenviar"}
    captured(controlled_campaign, content=json.dumps(draft), changes={"error": error})
    result = controller.inspect_controller(controlled_campaign[0])
    item, = result["proposals"]
    assert item["status"] == "provider_error" and item["source_error"] == error
    assert item["draft"] is None and result["technical_reviews_pending"] == 0
    assert result["usage"]["model_requests"] == 1 and result["reserved_model_requests"] == 1


def test_explicit_preflight_error_needs_no_submission_marker_and_keeps_zero_usage(controlled_campaign):
    scope, raw, *_ = controlled_campaign
    key = sha256(raw).hexdigest()
    ledger.reserve_proposal(scope, key)
    attempts.prepare_attempt(scope, raw)
    attempts.record_observation(scope, key, observation(model_request_attempted=False, content=None, usage=None,
                               error={"type": "PreflightError", "message": "No se envió"}))
    result = controller.inspect_controller(scope)
    assert result["proposals"][0]["status"] == "provider_error"
    assert result["usage"] == attempts.ZERO_USAGE and result["reserved_model_requests"] == 1


@pytest.mark.parametrize("changes", [{"model": None}, {"model": " "},
    {"usage": {"input_tokens": 0, "output_tokens": 17, "api_cost_usd": "0"}},
    {"usage": {"input_tokens": 100, "output_tokens": 0, "api_cost_usd": "0"}}])
def test_success_without_complete_model_or_tokens_does_not_reach_review(controlled_campaign, draft, changes):
    captured(controlled_campaign, content=json.dumps(draft), changes=changes)
    result = controller.inspect_controller(controlled_campaign[0])
    assert result["status"] == "blocked"
    assert result["proposals"][0]["issues"] == ["incomplete_success_observation"]


def test_comparison_reservation_cannot_act_as_accepted_review(controlled_campaign, draft):
    scope, *_ = controlled_campaign
    key, _, _ = captured(controlled_campaign, content=json.dumps(draft))
    ledger.reserve_comparison(scope, key, "c" * 64)
    result = controller.inspect_controller(scope)
    assert result["requires_stop"] is True and result["reserved_backtests"] == 2
    assert result["issues"] == ["comparison_without_controlled_review"]
    assert result["executable_backtests"] == 0 and result["calculated_results"] is None


def test_changed_live_memory_is_not_hidden_by_successful_ledger_status(controlled_campaign):
    scope, _, _, guided, _ = controlled_campaign
    (guided / "events.jsonl").write_bytes(b'{"event":"changed"}\n')
    assert ledger.inspect_campaign(scope)["status"] == "registered_inactive"
    with pytest.raises(ValueError, match="Memoria"):
        controller.inspect_controller(scope)


def test_reservation_created_during_inspection_invalidates_result(controlled_campaign, monkeypatch):
    scope, _, _, _, _ = controlled_campaign
    original = controller._plan
    calls = []
    def changing(state):
        result = original(state)
        calls.append(None)
        if len(calls) == 2: ledger.reserve_proposal(scope, "d" * 64)
        return result
    monkeypatch.setattr(controller, "_plan", changing)
    with pytest.raises(ValueError, match="cambiaron"):
        controller.inspect_controller(scope)
    assert ledger.inspect_campaign(scope)["reserved_model_requests"] == 1


def test_capture_content_change_between_reads_is_detected(controlled_campaign, draft, monkeypatch):
    _, directory, _ = captured(controlled_campaign, content=json.dumps(draft))
    original = controller._origin
    counts = []
    def changing(path, files):
        result = original(path, files)
        if Path(path) == directory:
            counts.append(None)
            if len(counts) == 1:
                with (directory / "observation.raw").open("ab") as stream: stream.write(b' changed')
        return result
    monkeypatch.setattr(controller, "_origin", changing)
    with pytest.raises(ValueError): controller.inspect_controller(controlled_campaign[0])


def test_missing_scope_is_not_registered_by_query(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_PATH", tmp_path / "absent/registry.sqlite3")
    with pytest.raises(ValueError, match="no está registrado"): controller.inspect_controller("f" * 64)
    assert not ledger.LEDGER_PATH.parent.exists()


def test_cli_reads_only_and_rejects_activation_or_arbitrary_capture(controlled_campaign, capsys):
    scope, *_ = controlled_campaign
    controller.main(["--scope", scope])
    assert json.loads(capsys.readouterr().out)["execution_authorized"] is False
    for option in ("--activate", "--execute", "--observation", "--allow-paid", "--ledger-path"):
        with pytest.raises(SystemExit): controller.main(["--scope", scope, option, "anything"])


def test_real_guided_sources_and_historical_duplicate_are_checked_without_transport_or_calculation(
        sources, tmp_path, transport, monkeypatch, isolated_ledger):
    guided = prepare_guided_request(*sources, output_dir=tmp_path / "guided-integration")
    plan = campaign.prepare_campaign_plan(guided, {"max_proposals": 1, "max_backtests": 2}, output_dir=tmp_path / "campaign")
    scope = ledger.register_campaign(plan)["scope_id"]
    monkeypatch.setattr(attempts, "ACCESS_ROOT", tmp_path / "integration-access")
    monkeypatch.setattr(attempts, "ATTEMPTS_ROOT", tmp_path / "integration-captures")
    data = json.loads((plan / "campaign.json").read_bytes())["history"]["compact_attempts"][0]
    draft = {key: data[key] for key in ("entry", "exit")}
    captured((scope, (plan / "request.json").read_bytes()), content=json.dumps(draft))
    def forbidden(*args, **kwargs): pytest.fail("La comprobación integrada no puede consultar o calcular.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.compact_ollama.CompactOllamaProvider.describe", "trading_ai.rule_execution._calculate",
                 "trading_ai.structured_generation.reserve_compact_generation"):
        monkeypatch.setattr(name, forbidden)
    before = ledger.LEDGER_PATH.read_bytes()
    result = controller.inspect_controller(scope)
    assert result["current_source_freshness_verified"] is True
    assert result["proposals"][0]["status"] == "duplicate_rules"
    assert result["technical_reviews_pending"] == 0 and result["new_usage"]["backtests"] == 0
    assert ledger.LEDGER_PATH.read_bytes() == before and len(transport.model_calls) == 1
