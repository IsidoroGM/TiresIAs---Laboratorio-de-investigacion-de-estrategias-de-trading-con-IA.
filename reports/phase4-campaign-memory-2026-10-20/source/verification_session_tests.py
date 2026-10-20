"""Guardas de bytes y presencia: ninguna autorización queda en caché."""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path

import pytest

from trading_ai import guided_compact_request as guided
from trading_ai import verification_session as sessions


@pytest.fixture
def simple(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    source.write_bytes(b'{"value":1}')
    calls = []
    def verify(directory):
        calls.append(None)
        return {"raw": (directory / "source.json").read_bytes(),
                "missing": (directory / "missing.lock").exists(),
                "files": [str(path) for path in directory.rglob("*.json") if path.is_file()], "nested": {"value": 1}}
    monkeypatch.setattr(sessions, "_ORIGINAL", verify)
    monkeypatch.setattr(guided, "verify_guided_request", verify)
    return tmp_path, source, calls


def test_one_validation_then_guarded_independent_copies_and_cleanup(simple):
    root, _, calls = simple
    original = guided.verify_guided_request
    original_open = Path.open
    with sessions.VerificationSession() as cache:
        first = guided.verify_guided_request(root)
        first["nested"]["value"] = 99
        assert guided.verify_guided_request(root)["nested"]["value"] == 1
        assert cache.stats == {"full_guided_validations": 1, "guarded_guided_hits": 1}
    assert len(calls) == 1 and cache.entries == {} and cache.closed
    assert guided.verify_guided_request is original and Path.open is original_open
    with pytest.raises(ValueError): cache.verify(root)
    with pytest.raises(ValueError): cache.__enter__()


@pytest.mark.parametrize("change", ["bytes_same_stat", "delete", "listing", "presence", "configuration", "function"])
def test_changed_source_presence_listing_or_code_stops_reuse(simple, monkeypatch, change):
    root, source, calls = simple
    with sessions.VerificationSession():
        guided.verify_guided_request(root)
        if change == "bytes_same_stat":
            before = source.stat()
            source.write_bytes(b'{"value":2}')
            os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
        elif change == "delete": source.unlink()
        elif change == "listing": (root / "added.json").write_bytes(b'{}')
        elif change == "presence": (root / "missing.lock").write_bytes(b'held')
        elif change == "configuration": monkeypatch.setattr(guided, "NOTE", "changed")
        else: monkeypatch.setattr(guided, "_build", lambda *args: None)
        with pytest.raises((ValueError, OSError)): sessions._dispatch(root)
        assert len(calls) == 1


def test_unscoped_thread_does_not_use_another_context_cache(simple):
    root, _, calls = simple
    with sessions.VerificationSession() as cache:
        guided.verify_guided_request(root)
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(guided.verify_guided_request, root).result()["nested"] == {"value": 1}
        guided.verify_guided_request(root)
        assert cache.stats["guarded_guided_hits"] == 1 and len(calls) == 2


def test_nested_session_rejected_without_breaking_outer(simple):
    root, _, _ = simple
    with sessions.VerificationSession():
        with pytest.raises(ValueError): sessions.VerificationSession().__enter__()
        guided.verify_guided_request(root)
        guided.verify_guided_request(root)


def test_full_verifier_failure_and_write_attempt_restore_readers(simple, monkeypatch):
    root, source, _ = simple
    original_open = Path.open
    def writes(directory):
        (directory / "source.json").write_bytes(b'changed')
    monkeypatch.setattr(sessions, "_ORIGINAL", writes)
    monkeypatch.setattr(guided, "verify_guided_request", writes)
    with pytest.raises(ValueError, match="escribir"):
        with sessions.VerificationSession(): guided.verify_guided_request(root)
    assert source.read_bytes() == b'{"value":1}' and Path.open is original_open


def test_size_limit_refuses_omission(simple, monkeypatch):
    root, _, _ = simple
    monkeypatch.setattr(sessions, "MAX_FILE_BYTES", 2)
    with pytest.raises(ValueError, match="grande"):
        with sessions.VerificationSession(): guided.verify_guided_request(root)


def test_change_during_first_validation_is_not_stored(simple, monkeypatch):
    root, source, _ = simple
    def changes(directory):
        before = source.read_bytes()
        # Un escritor externo al lector instrumentado cambia la fuente.
        with sessions._PATH["open"](source, "wb") as stream: stream.write(b'{"value":2}')
        return {"raw": before}
    monkeypatch.setattr(sessions, "_ORIGINAL", changes)
    monkeypatch.setattr(guided, "verify_guided_request", changes)
    with sessions.VerificationSession() as cache:
        with pytest.raises(ValueError, match="fuente"): guided.verify_guided_request(root)
        assert cache.entries == {} and cache.stats["full_guided_validations"] == 0
