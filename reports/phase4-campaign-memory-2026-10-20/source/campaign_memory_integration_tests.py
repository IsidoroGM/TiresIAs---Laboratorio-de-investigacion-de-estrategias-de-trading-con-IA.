"""Cadena completa con fuentes artificiales y guardas; ninguna llamada real al modelo."""

import io
import json
from pathlib import Path
from time import perf_counter

import pytest

from test_campaign_controller import captured
from test_campaign_permission import declaration
from test_campaign_review import review_roots, assessment
from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews
from test_compact_request import duplicate_memory
from test_discovery import registered
from test_guided_compact_request import sources
from test_holdout import setup
from test_structured_draft_request import memory
from test_structured_ideas import generated, proposal
from test_structured_session import session
from trading_ai import campaign_execution as execution
from trading_ai import campaign_experiment as experiments
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_memory as result_memory
from trading_ai import campaign_permission as permissions
from trading_ai import campaign_plan as campaigns
from trading_ai import campaign_review as reviews
from trading_ai import guided_compact_request as guided
from trading_ai import rule_execution as engine
from trading_ai.research_session import _origin
from trading_ai.verification_session import VerificationSession


def test_complete_chain_reuses_guided_verification_but_rechecks_live_reservations_and_results(
        sources, tmp_path, transport, monkeypatch, review_roots, record_property):
    monkeypatch.setattr(permissions, "ACCESS_ROOT", tmp_path / "permissions-access")
    guided_dir = guided.prepare_guided_request(*sources, output_dir=tmp_path / "guided")
    execution_root = tmp_path / "executions"
    def forbidden(*args, **kwargs): pytest.fail("No se permiten modelos, red o presupuestos heredados.")
    for name in ("socket.socket.connect", "trading_ai.compact_ollama.CompactOllamaProvider.complete",
                 "trading_ai.compact_ollama.CompactOllamaProvider.describe", "trading_ai.structured_generation.reserve_compact_generation"):
        monkeypatch.setattr(name, forbidden)
    original_open = io.open
    def guarded(path, *args, **kwargs):
        if isinstance(path, (str, Path)):
            source = Path(path)
            if source.name == "evaluation.xml" or (source.name == "comparison.json" and not source.resolve().is_relative_to(execution_root.resolve())):
                pytest.fail("No se permite abrir evaluación exterior.")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(io, "open", guarded)
    with VerificationSession() as cache:
        start = perf_counter()
        first = guided.verify_guided_request(guided_dir)
        full_seconds = perf_counter() - start
        start = perf_counter()
        assert guided.verify_guided_request(guided_dir) == first
        guarded_seconds = perf_counter() - start
        campaign = campaigns.prepare_campaign_plan(guided_dir, {"max_proposals": 1, "max_backtests": 2}, output_dir=tmp_path / "campaign")
        scope = ledger.register_campaign(campaign)["scope_id"]
        draft = {"entry": {"left": {"kind": "reference", "lag": 0}, "operator": "gt", "right": {"kind": "constant", "value": "2"}},
                 "exit": {"left": {"kind": "reference", "lag": 0}, "operator": "lte", "right": {"kind": "constant", "value": "2"}}}
        key, _, _ = captured((scope, (campaign / "request.json").read_bytes()), content=json.dumps(draft))
        view = reviews.inspect_candidate(scope, key)
        review = reviews.review_capture(scope, key, assessment(view), output_dir=tmp_path / "reviews")
        plan_dir = experiments.prepare_plan(review, output_dir=tmp_path / "plans")
        plan = experiments.verify_plan(plan_dir)
        permit = permissions.grant_permission(plan_dir, declaration(plan, _origin(plan_dir, permissions.PLAN_FILES)), output_dir=tmp_path / "permissions")
        run = execution.execute(permit, output_dir=execution_root)
        result = result_memory.inspect_memory(scope)
        assert result["comparisons"][0]["status"] == "completed_verified"
        assert result["comparisons"][0]["assessment"]["origin"] == "python"
        assert ledger.inspect_campaign(scope)["remaining_accounting_slots"] == {"proposals": 0, "backtests": 0}
        assert not result["requires_stop"] and not result["automatic_local_cycle_enabled"]
        assert cache.stats["full_guided_validations"] == 1 and cache.stats["guarded_guided_hits"] > 10
        # La caché guiada no conserva resultados, permisos o decisiones de adopción.
        with (run / "report.md").open("ab") as stream: stream.write(b' changed')
        stale = result_memory.inspect_memory(scope)
        assert stale["requires_stop"] and stale["comparisons"][0]["status"] == "unverifiable_execution"
        assert len(transport.model_calls) == 1 and len(list(engine.ACCESS_ROOT.glob("*.json"))) == 1
        record_property("verification_measurement", json.dumps({"full_seconds": full_seconds,
                        "guarded_seconds": guarded_seconds, "stats": cache.stats}))
