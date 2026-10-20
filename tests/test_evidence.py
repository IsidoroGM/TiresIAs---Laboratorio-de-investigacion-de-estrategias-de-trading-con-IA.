"""Copias portables, originales opcionales, límites y rutas sin salidas del inventario."""

from hashlib import sha256
import json

import pytest

from trading_ai.evidence import verify_evidence, main
from trading_ai import evidence


@pytest.fixture
def archive(tmp_path):
    folder = tmp_path / "archive"
    folder.mkdir()
    (folder / "nested").mkdir()
    source = tmp_path / "source.json"
    raw = b'{"value":42}\r\n'
    source.write_bytes(raw)
    (folder / "nested/data.json").write_bytes(raw)
    manifest = {"schema_version": 1, "files": {"nested/data.json": {"source": str(source), "sha256": sha256(raw).hexdigest()}}}
    path = folder / "snapshot.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, source, manifest


def test_copies_only_can_be_checked_after_original_is_missing_and_do_not_write(archive, monkeypatch):
    snapshot, source, _ = archive
    source.unlink()  # Archivo artificial creado por esta prueba, no fuente del usuario.
    before = {path: path.read_bytes() for path in snapshot.parent.rglob("*") if path.is_file()}
    def forbidden(*args, **kwargs): pytest.fail("Verificar evidencias no puede consultar o recalcular")
    for name in ("trading_ai.ai.create_provider", "socket.socket.connect", "trading_ai.experiments.run_backtest"):
        monkeypatch.setattr(name, forbidden)
    record = verify_evidence([snapshot])
    assert record["copies_verified"] == 1 and record["original_references_verified"] is None
    assert record["mode"] == "copies_only" and record["model_requests"] == record["backtests"] == 0
    assert {path: path.read_bytes() for path in snapshot.parent.rglob("*") if path.is_file()} == before


def test_optional_originals_are_verified_and_byte_changes_are_detected(archive, tmp_path):
    snapshot, source, _ = archive
    result = verify_evidence([snapshot], with_originals=True, source_root=tmp_path)
    assert result["copies_verified"] == result["original_references_verified"] == 1
    source.write_bytes(source.read_bytes().replace(b'\r\n', b'\n'))
    with pytest.raises(ValueError, match="original"): verify_evidence([snapshot], with_originals=True, source_root=tmp_path)


@pytest.mark.parametrize("name", ["../source.json", "nested/../../source.json", "C:\\outside\\file.json", "/outside/file.json", ""])
def test_copy_path_cannot_leave_its_archive(archive, name):
    snapshot, _, manifest = archive
    item, = manifest["files"].values()
    manifest["files"] = {name: item}
    snapshot.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError): verify_evidence([snapshot])


def test_originals_cannot_leave_explicit_source_root(archive):
    snapshot, _, _ = archive
    with pytest.raises(ValueError, match="fuera"): verify_evidence([snapshot], with_originals=True, source_root=snapshot.parent)


@pytest.mark.parametrize("change", ["schema_bool", "old_list", "empty", "bad_digest", "bad_source", "url"])
def test_unknown_or_invalid_manifest_is_not_silently_skipped(archive, change):
    snapshot, _, manifest = archive
    item = manifest["files"]["nested/data.json"]
    if change == "schema_bool": manifest["schema_version"] = True
    elif change == "old_list": manifest["files"] = ["nested/data.json"]
    elif change == "empty": manifest["files"] = {}
    elif change == "bad_digest": item["sha256"] = "not a digest"
    elif change == "bad_source": item["source"] = ""
    elif change == "url": item["source"] = "https://example.invalid/secret"
    snapshot.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError): verify_evidence([snapshot])


def test_corrupt_copy_and_duplicate_snapshot_are_refused(archive):
    snapshot, _, _ = archive
    with pytest.raises(ValueError, match="dos veces"): verify_evidence([snapshot, snapshot])
    with (snapshot.parent / "nested/data.json").open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError, match="copia"): verify_evidence([snapshot])


@pytest.mark.parametrize("limit", ["MAX_FILES", "MAX_FILE_BYTES", "MAX_TOTAL_BYTES"])
def test_limits_fail_without_publishing_a_partial_success(archive, monkeypatch, limit):
    monkeypatch.setattr(evidence, limit, 0)
    with pytest.raises(ValueError): verify_evidence([archive[0]])


def test_cli_explains_scope_and_optional_originals(archive, tmp_path, capsys):
    snapshot, _, _ = archive
    main(["--snapshot", str(snapshot)])
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3 and "no inspeccionados" in lines[1]
    main(["--snapshot", str(snapshot), "--with-originals", "--source-root", str(tmp_path), "--json"])
    assert json.loads(capsys.readouterr().out)["original_references_verified"] == 1
