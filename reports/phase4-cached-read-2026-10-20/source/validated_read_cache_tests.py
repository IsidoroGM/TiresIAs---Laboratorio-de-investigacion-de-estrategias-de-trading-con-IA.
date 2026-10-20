"""Reutilización de desarrollo con fuentes y código contrastados en cada acceso."""

from concurrent.futures import ThreadPoolExecutor
from contextvars import Context
from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews
from test_compact_request import duplicate_memory
from test_guided_compact_request import sources
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from trading_ai import robustness
from trading_ai import validated_read_cache as cache_module
from trading_ai.guided_compact_request import prepare_guided_request, verify_guided_request
from trading_ai.validated_read_cache import ValidatedReadCache, verify_guided_with_cache


@pytest.fixture
def observed_load(monkeypatch):
    actual, calls = robustness.load_ecb_rates, []
    def observed(*args, **kwargs):
        calls.append(None)
        return actual(*args, **kwargs)
    monkeypatch.setattr(robustness, "load_ecb_rates", observed)
    return calls


def test_repeated_access_validates_prices_once_and_returns_independent_copies(registered, observed_load):
    _, frozen_dir = registered
    original = robustness._development
    with ValidatedReadCache() as cache:
        first = robustness._development(frozen_dir)
        unchanged = deepcopy(first)
        first[0]["policy"]["cost_rate"] = "999"
        second = robustness._development(frozen_dir)
        third = robustness._development(frozen_dir)
        assert second == third == unchanged
        assert cache.stats == {"full_validations": 1, "guarded_hits": 2, "uncached_large_or_limit": 0}
        assert len(observed_load) == 1
    assert robustness._development is original
    robustness._development(frozen_dir)
    assert len(observed_load) == 2


@pytest.mark.parametrize("source", ["development", "research"])
def test_changed_source_is_rejected_even_with_restored_mtime(registered, source):
    _, frozen_dir = registered
    with ValidatedReadCache():
        frozen, _, _ = robustness._development(frozen_dir)
        path = (Path(frozen["split"]["directory"]) / "development.xml" if source == "development"
                else Path(frozen["research"]["directory"]) / "results.json")
        metadata = path.stat()
        path.write_bytes(path.read_bytes() + b' changed')
        os.utime(path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
        with pytest.raises(ValueError, match="fuente"): robustness._development(frozen_dir)


def test_mutable_execution_policy_is_not_hidden_by_cache(registered, monkeypatch):
    _, frozen_dir = registered
    with ValidatedReadCache():
        robustness._development(frozen_dir)
        changed = {**robustness.EXECUTION_POLICY, "unexpected_policy": True}
        monkeypatch.setattr(robustness, "EXECUTION_POLICY", changed)
        with pytest.raises(ValueError, match="dependencias"): robustness._development(frozen_dir)


def test_current_code_fingerprint_is_rechecked_on_every_hit(registered, monkeypatch):
    _, frozen_dir = registered
    original = robustness._frozen_hashes
    changed = []
    def current():
        result = original()
        return {**result, "changed_code.py": "f" * 64} if changed else result
    monkeypatch.setattr(robustness, "_frozen_hashes", current)
    with ValidatedReadCache():
        robustness._development(frozen_dir)
        changed.append(True)
        with pytest.raises(ValueError, match="Código"): robustness._development(frozen_dir)


def test_scope_cleanup_after_exception_and_instance_cannot_reopen(registered):
    _, frozen_dir = registered
    original, cache = robustness._development, ValidatedReadCache()
    with pytest.raises(RuntimeError):
        with cache:
            robustness._development(frozen_dir)
            raise RuntimeError("Interrupción artificial")
    assert robustness._development is original and not cache.entries
    with pytest.raises(ValueError):
        with cache: pass
    with pytest.raises(ValueError): cache.development(frozen_dir)


def test_nested_scopes_are_isolated_and_restore_outer_cache(registered, observed_load):
    _, frozen_dir = registered
    with ValidatedReadCache() as outer:
        robustness._development(frozen_dir)
        with ValidatedReadCache() as inner:
            robustness._development(frozen_dir)
            robustness._development(frozen_dir)
        robustness._development(frozen_dir)
        assert outer.stats["guarded_hits"] == inner.stats["guarded_hits"] == 1
    assert len(observed_load) == 2


def test_another_thread_without_context_still_runs_full_validation(registered, observed_load):
    _, frozen_dir = registered
    with ValidatedReadCache() as cache:
        first = robustness._development(frozen_dir)
        with ThreadPoolExecutor(max_workers=1) as executor:
            second = executor.submit(lambda: Context().run(robustness._development, frozen_dir)).result()
        assert first == second
        assert cache.stats["full_validations"] == 1 and len(observed_load) == 2


def test_cache_limit_falls_back_to_full_validation_without_skipping_checks(registered, observed_load, monkeypatch):
    monkeypatch.setattr(cache_module, "MAX_DATASETS", 0)
    _, frozen_dir = registered
    with ValidatedReadCache() as cache:
        first = robustness._development(frozen_dir)
        second = robustness._development(frozen_dir)
        assert first == second and len(observed_load) == 2
        assert cache.stats["uncached_large_or_limit"] == 2 and not cache.entries


def test_guided_read_has_identical_result_and_never_calls_model_or_engine(sources, tmp_path, monkeypatch, observed_load):
    run = prepare_guided_request(*sources, output_dir=tmp_path / "guided")
    expected = verify_guided_request(run)
    observed_load.clear()
    def forbidden(*args, **kwargs): pytest.fail("Una lectura no puede consultar modelos o calcular")
    for name in ("trading_ai.compact_ollama.CompactOllamaProvider.complete", "trading_ai.rule_execution._calculate", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    actual = verify_guided_with_cache(run)
    assert actual["packet"] == expected and actual["cache"]["full_validations"] == 1
    assert actual["cache"]["guarded_hits"] > 1 and len(observed_load) == 1
    assert actual["new_generation_permission"] is actual["executable"] is False
    assert actual["new_usage"]["model_requests"] == actual["new_usage"]["backtests"] == 0
    assert robustness._development is cache_module._ORIGINAL
