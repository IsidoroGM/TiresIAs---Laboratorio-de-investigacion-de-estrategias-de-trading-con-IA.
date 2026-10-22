"""Fuentes reales del protocolo sobre XML artificial y transporte simulado."""

import io
import json
from pathlib import Path

import pytest

from test_campaign_review import review_roots
from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews
from test_compact_request import duplicate_memory
from test_discovery import registered
from test_guided_compact_request import sources
from test_holdout import setup
from test_structured_draft_request import memory
from test_structured_ideas import generated, proposal
from test_structured_session import session
from trading_ai import campaign_cycle as cycle
from trading_ai import campaign_ledger as ledger
from trading_ai import campaign_plan as campaigns
from trading_ai import guided_compact_request as guided
from trading_ai.ai import OllamaProvider
from trading_ai.verification_session import VerificationSession


def test_full_sources_transport_review_engine_memory_cycle(sources, transport, tmp_path, monkeypatch, review_roots):
    monkeypatch.setattr(cycle, "ACCESS_ROOT", tmp_path / "cycle-access")
    guided_dir = guided.prepare_guided_request(*sources, output_dir=tmp_path / "guided")
    calls = []
    draft = {"entry": {"left": {"kind": "reference", "lag": 0}, "operator": "gt", "right": {"kind": "constant", "value": "2"}},
             "exit": {"left": {"kind": "reference", "lag": 0}, "operator": "lt", "right": {"kind": "constant", "value": "2"}}}
    def local(self, method, path, payload):
        if path == "/api/version": return {"version": "0.40.6"}
        if path == "/api/tags": return {"models": [{"name": "qwen3.5:4b", "digest": "a"*64}]}
        calls.append(payload)
        assert payload["truncate"] is payload["shift"] is False
        return {"model": "qwen3.5:4b", "done": True, "done_reason": "stop", "message": {"content": json.dumps(draft)}, "prompt_eval_count": 100, "eval_count": 50}
    monkeypatch.setattr(OllamaProvider, "_request", local)
    monkeypatch.setattr("socket.socket.connect", lambda *args: pytest.fail("Sin red real."))
    original_open = io.open
    def guarded(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path).name in ("evaluation.xml", "comparison.json"):
            pytest.fail("No se debe abrir evaluación exterior.")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(io, "open", guarded)
    with VerificationSession() as cache:
        campaign = campaigns.prepare_campaign_plan(guided_dir, {"max_proposals": 1, "max_backtests": 2}, output_dir=tmp_path / "campaign")
        scope = ledger.register_campaign(campaign)["scope_id"]
        permit = cycle.prepare_cycle(scope, output_dir=tmp_path / "permits")
        run = cycle.run_cycle(permit, allow_local_generation=True, allow_virtual_calculations=True, output_dir=tmp_path / "runs")
        result = cycle.inspect_cycle(run)
        assert result["entries"][0]["results"]["assessment"]["origin"] == "python"
        assert result["entries"][0]["review"]["semantic_acceptance"] is False
        assert len(calls) == 1 and len(transport.model_calls) == 1
        assert result["state"]["reserved_model_requests"] == 1 and result["state"]["reserved_backtests"] == 2
        assert cache.stats["full_guided_validations"] == 1 and cache.stats["guarded_guided_hits"] > 5
