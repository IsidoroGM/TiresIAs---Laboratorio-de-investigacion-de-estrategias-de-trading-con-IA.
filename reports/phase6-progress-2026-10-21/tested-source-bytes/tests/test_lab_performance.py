"""Frescura, aislamiento y límites de la optimización de consulta."""

from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import os
from pathlib import Path
import threading
import time

import pytest

from test_lab import lab, local, request, save
from trading_ai.lab import create_server
from trading_ai.lab_catalog import Catalog
from trading_ai.lab_query import LabQuery
from trading_ai.lab_service import LabService, MetadataCache


@pytest.fixture
def service(lab):
    result = LabService(lab[0], interval=60)
    try: yield result
    finally: result.close()


def wait_refresh(service):
    with service._condition:
        assert service._condition.wait_for(lambda: not service._refreshing, timeout=5)


def test_warm_views_do_not_reopen_files(service, monkeypatch):
    original = service.overview("experiments")
    def denied(*args, **kwargs): raise AssertionError("Lectura innecesaria")
    monkeypatch.setattr(Path, "open", denied)
    for name in ("home", "experiments", "consumption"):
        assert service.overview(name)["index"]["generation"] == original["index"]["generation"]
    assert service.overview("experiments", filters={"origin": "local", "pair": "EUR/USD"})["items"]


def test_published_views_and_query_contexts_are_isolated(service):
    first = service.overview("home")
    first["counts"]["experiments"] = -1
    query, _ = service.query()
    query.catalog.files.clear()
    assert service.overview("home")["counts"]["experiments"] == 2
    assert service.query()[0].catalog.files


def test_detail_rechecks_same_size_bytes_with_restored_mtime(service, lab):
    _, run, _ = lab
    row = next(x for x in service.overview("experiments")["items"] if x["origin"] == "local")
    path = run / "results.json"
    before, raw = path.stat(), path.read_bytes()
    replacement = raw.replace(b"executed", b"ExecutEd")
    assert len(replacement) == len(raw) and replacement != raw
    path.write_bytes(replacement)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    query, _ = service.query()
    detail = query.detail(row["id"])
    assert detail["integrity"]["state"] == "changed"
    assert "ExecutEd" in detail["hypothesis"]


def test_accounts_are_never_served_from_metadata_cache(service, lab):
    _, run, _ = lab
    row = next(x for x in service.overview("experiments")["items"] if x["origin"] == "local")
    query, _ = service.query()
    detail = query.detail(row["id"])
    key = detail["accounts"][0]["id"]
    assert query.account(row["id"], key)["backtest"]
    value = json.loads((run / "baseline.json").read_text())
    value["backtest"]["equity_curve"][-1]["equity"] = "991"
    save(run / "baseline.json", value)
    query, _ = service.query()
    account = query.account(row["id"], key)
    assert account["backtest"] is None
    assert account["integrity"]["state"] == "unverifiable"


@pytest.mark.parametrize("change", ["add", "delete", "modify"])
def test_background_refresh_observes_file_changes(service, lab, change):
    root, run, _ = lab
    initial = service.overview("experiments")
    row = next(x for x in initial["items"] if x["origin"] == "local")
    if change == "add":
        save(root / ".local/research/new/results.json", {"status": "new_record"})
    elif change == "delete": (run / "results.json").unlink()
    else:
        value = json.loads((run / "results.json").read_text())
        value["status"] = "changed_record"
        save(run / "results.json", value)
    service.interval = 0
    service.overview("home")
    wait_refresh(service)
    service.interval = 60
    refreshed = service.overview("experiments")
    assert refreshed["index"]["generation"] > initial["index"]["generation"]
    if change == "add": assert len(refreshed["items"]) == 3
    elif change == "delete": assert row["id"] not in {x["id"] for x in refreshed["items"]}
    else: assert any(x["state"] == "changed_record" for x in refreshed["items"])


def test_existing_empty_report_directory_becomes_an_archive(service, lab):
    root, _, archive = lab
    empty = root / "reports/new-archive"
    empty.mkdir()
    first = service.overview("home")
    # Inventario válido con una copia de un registro sin necesidad de modelos.
    raw = (archive / "run/results.json").read_bytes()
    target = empty / "results.json"
    target.write_bytes(raw)
    from hashlib import sha256
    save(empty / "snapshot.json", {"schema_version": 1, "files": {"results.json": {
        "source": ".local/research/new/results.json", "sha256": sha256(raw).hexdigest()}}})
    service.interval = 0
    service.overview("home"); wait_refresh(service)
    service.interval = 60
    assert service.overview("home")["counts"]["archives"] == first["counts"]["archives"] + 1


def test_forced_refresh_bypasses_metadata_cache(service, lab, monkeypatch):
    first = service.overview("home")
    calls = []
    original = Path.open
    def opened(path, *args, **kwargs):
        if path == lab[1] / "results.json": calls.append(path)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", opened)
    result = service.overview("home", force=True)
    assert result["index"]["generation"] > first["index"]["generation"]
    assert calls


def test_refresh_failure_is_visible_and_force_does_not_claim_success(service, monkeypatch):
    first = service.overview("home")
    def failed(*args): raise ValueError("fallo de lectura controlado")
    monkeypatch.setattr(service, "_build", failed)
    with pytest.raises(ValueError, match="fallo de lectura"): service.overview("home", force=True)
    result = service.overview("home")
    assert result["counts"] == first["counts"]
    assert result["index"]["generation"] == first["index"]["generation"]
    assert "fallo de lectura" in result["index"]["refresh_error"]


def test_one_initial_build_for_simultaneous_requests(service, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    original, calls = service._build, []
    def blocked(force):
        calls.append(force); entered.set()
        assert release.wait(3)
        return original(force)
    monkeypatch.setattr(service, "_build", blocked)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(service.overview, "home") for _ in range(4)]
        try:
            assert entered.wait(2)
            assert len(calls) == 1
        finally: release.set()
        assert {future.result()["index"]["generation"] for future in futures} == {1}
    assert len(calls) == 1


def test_background_update_does_not_block_or_duplicate_builds(service, lab, monkeypatch):
    first = service.overview("home")
    save(lab[1] / "new.json", {"changed": True})
    entered, release = threading.Event(), threading.Event()
    original, calls = service._build, []
    def blocked(force):
        calls.append(force); entered.set()
        assert release.wait(3)
        return original(force)
    monkeypatch.setattr(service, "_build", blocked)
    service.interval = 0
    try:
        service.overview("home")
        assert entered.wait(2)
        for _ in range(8):
            response = service.overview("home")
            assert response["index"]["refreshing"]
            assert response["index"]["generation"] == first["index"]["generation"]
        assert len(calls) == 1
    finally: release.set(); wait_refresh(service)


def test_unchanged_sources_do_not_rebuild(service, monkeypatch):
    first = service.overview("home")
    def denied(*args): raise AssertionError("No hubo cambios")
    monkeypatch.setattr(service, "_build", denied)
    service.interval = 0
    service.overview("home"); wait_refresh(service)
    service.interval = 60
    result = service.overview("home")
    assert result["index"]["generation"] == first["index"]["generation"]
    assert result["index"]["refresh_error"] is None


def test_comparison_reads_each_source_once_per_operation(lab, monkeypatch):
    root, run, _ = lab
    query = LabQuery(root)
    detail = query.detail(local(query)["id"])
    original, reads = Path.open, []
    def opened(path, *args, **kwargs):
        if path == run / "results.json": reads.append(path)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", opened)
    result = query.compare(detail["id"], detail["accounts"][0]["id"], detail["id"], detail["accounts"][1]["id"])
    assert result["compatible"]
    assert len(reads) == 1
    query.detail(detail["id"])
    assert len(reads) == 2


def test_cached_bytes_cannot_bypass_reading_budget(lab, monkeypatch):
    from trading_ai import lab_catalog
    root, _, _ = lab
    one, two = root / "reports/one.txt", root / "reports/two.txt"
    one.write_bytes(b"123"); two.write_bytes(b"456")
    catalog = Catalog(root)
    catalog.begin_read()
    monkeypatch.setattr(lab_catalog, "MAX_TOTAL", 4)
    assert catalog.read(one) == catalog.read(one) == b"123"
    with pytest.raises(ValueError, match="límite"): catalog.read(two)
    with pytest.raises(ValueError, match="límite"): catalog.read(one)


@pytest.mark.parametrize("guard", ["is_symlink", "is_junction"])
def test_replacing_parent_with_link_is_rejected_after_indexing(service, lab, monkeypatch, guard):
    service.overview("home")
    query, _ = service.query()
    original = getattr(Path, guard)
    monkeypatch.setattr(Path, guard, lambda path: path == lab[1] or original(path))
    with pytest.raises(ValueError, match="enlaces"): query.catalog.read(lab[1] / "results.json")


def test_file_changed_while_open_is_rejected(lab, monkeypatch):
    root, run, _ = lab
    catalog, original = Catalog(root), Path.open
    target = run / "results.json"
    class Changing:
        def __enter__(self): self.stream = original(target, "rb"); return self
        def __exit__(self, *args): self.stream.close()
        def fileno(self): return self.stream.fileno()
        def read(self, limit):
            raw = self.stream.read(limit)
            with original(target, "ab") as writer: writer.write(b" ")
            return raw
    def opened(path, *args, **kwargs):
        return Changing() if path == target else original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", opened)
    with pytest.raises(ValueError, match="cambió"): catalog.read(target)


def test_metadata_cache_is_bounded_and_replaces_old_versions():
    cache = MetadataCache(limit=1500)
    cache.put(Path("one"), (1,), b"x" * 700)
    cache.put(Path("two"), (1,), b"y" * 700)
    assert cache.bytes <= cache.limit
    assert cache.get(Path("one"), (1,)) is None
    cache.put(Path("two"), (2,), b"new")
    assert cache.get(Path("two"), (1,)) is None
    assert cache.get(Path("two"), (2,)) == b"new"


def test_oversized_index_is_not_published(lab):
    service = LabService(lab[0], max_index_bytes=1)
    try:
        with pytest.raises(ValueError, match="memoria"): service.overview("home")
        assert service.diagnostics()["generation"] == 0
    finally: service.close()


@pytest.fixture
def server(lab):
    result = create_server(root=lab[0], port=0)
    thread = threading.Thread(target=result.serve_forever, daemon=True)
    thread.start()
    try: yield result
    finally:
        result.shutdown(); result.server_close(); thread.join(3)
        assert not thread.is_alive()
        assert result.service.diagnostics()["closed"]


@pytest.mark.parametrize("asset", ["/", "/app.js", "/style.css"])
def test_static_etag_revalidation_and_head(server, asset):
    status, headers, raw = request(server, asset)
    assert status == 200 and raw
    assert headers["Cache-Control"] == "private, no-cache"
    tag = headers["ETag"]
    status, repeated, body = request(server, asset, headers={"If-None-Match": '"other", W/' + tag})
    assert status == 304 and body == b""
    assert repeated["ETag"] == tag
    assert request(server, asset, "HEAD")[2] == b""
    assert request(server, asset, headers={"If-None-Match": '"old"'})[0] == 200


def test_http_dynamic_sources_remain_fresh_and_no_store(server, lab):
    result = json.loads(request(server, "/api/experiments")[2])
    row = next(x for x in result["items"] if x["origin"] == "local")
    query, _ = server.service.query()
    detail = query.detail(row["id"])
    file = next(x for x in detail["files"] if x["path"].endswith("results.json"))
    path = lab[0] / file["path"]
    value = json.loads(path.read_text()); value["marker"] = "fresh_bytes"; save(path, value)
    status, headers, raw = request(server, "/sources/" + file["id"])
    assert status == 200 and b"fresh_bytes" in raw
    assert headers["Cache-Control"] == "no-store"
    status, headers, raw = request(server, "/api/home?refresh=1")
    assert status == 200 and json.loads(raw)["index"]["generation"] > result["index"]["generation"]
    assert headers["Cache-Control"] == "no-store"


def test_unknown_routes_and_host_rejection_do_not_build_index(server, monkeypatch):
    def denied(*args): raise AssertionError("Ruta rechazada antes de catalogar")
    monkeypatch.setattr(server.service, "_build", denied)
    assert request(server, "/api/unknown")[0] == 404
    assert request(server, "/api/home", headers={"Host": "external.example"})[0] == 403
    assert request(server, "/")[0] == 200
    assert server.service.diagnostics()["generation"] == 0


def test_slow_detail_does_not_block_overview(server, monkeypatch):
    request(server, "/api/home")
    entered, release = threading.Event(), threading.Event()
    original = server.service.query
    def blocked(**kwargs):
        entered.set(); assert release.wait(3)
        return original(**kwargs)
    monkeypatch.setattr(server.service, "query", blocked)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(request, server, "/api/experiments/unknown")
        try:
            assert entered.wait(2)
            assert request(server, "/api/home")[0] == 200
            assert not future.done()
        finally: release.set()
        assert future.result()[0] == 404


def test_overload_returns_retryable_response_and_releases_workers(lab, monkeypatch):
    server = create_server(root=lab[0], port=0, workers=1)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    entered, release = threading.Event(), threading.Event()
    original = server.service.overview
    def blocked(*args, **kwargs):
        entered.set(); assert release.wait(3)
        return original(*args, **kwargs)
    monkeypatch.setattr(server.service, "overview", blocked)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(request, server, "/api/home")
            try:
                assert entered.wait(2)
                status, headers, _ = request(server, "/")
                assert status == 503 and headers["Retry-After"] == "1"
            finally: release.set()
            assert future.result()[0] == 200
        assert request(server, "/")[0] == 200
    finally: server.shutdown(); server.server_close(); thread.join(3)


def test_closed_service_cannot_be_reused(service):
    service.overview("home"); service.close()
    assert service.diagnostics()["metadata_weight_bytes"] == 0
    with pytest.raises(ValueError, match="cerrado"): service.overview("home")


def test_cached_service_has_no_execution_or_write_side_effects(service, lab, monkeypatch):
    from test_lab import fingerprint
    from trading_ai import ai, backtesting, campaign_ledger
    before = fingerprint(lab[0])
    original = Path.open
    def denied(*args, **kwargs): raise AssertionError("Acción fuera de la consulta")
    def readonly(path, mode="r", *args, **kwargs):
        if any(char in mode for char in "wax+"): return denied()
        return original(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", readonly)
    monkeypatch.setattr(ai, "create_provider", denied)
    monkeypatch.setattr(ai.OllamaProvider, "complete", denied)
    monkeypatch.setattr(backtesting, "run_backtest", denied)
    monkeypatch.setattr(campaign_ledger, "_reserve", denied)
    for force in (False, False, True):
        service.overview("home", force=force)
        rows = service.overview("experiments")["items"]
        service.overview("consumption")
        for row in rows:
            query, _ = service.query()
            detail = query.detail(row["id"])
            for account in detail["accounts"]:
                query.account(row["id"], account["id"])
    assert fingerprint(lab[0]) == before
