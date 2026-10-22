"""Integridad de copias archivadas; no recalcula estrategias ni interpreta resultados."""

import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import re

from trading_ai.formalization import _read, _strict_json
from trading_ai.research import ROOT


MAX_FILES = 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024


def _digest(path: Path) -> tuple[str, int]:
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Archivo ausente, no regular o demasiado grande: " + str(path))
    total, digest = 0, sha256()
    with path.open("rb") as stream:
        while raw := stream.read(65536):
            total += len(raw)
            if total > MAX_FILE_BYTES: raise ValueError("El archivo creció por encima del límite: " + str(path))
            digest.update(raw)
    return digest.hexdigest(), total


def _copy_path(directory: Path, name: str) -> Path:
    if (not isinstance(name, str) or not name or Path(name).is_absolute() or PureWindowsPath(name).drive
            or ".." in Path(name).parts or ".." in PureWindowsPath(name).parts):
        raise ValueError("Nombre de copia fuera del directorio de evidencia.")
    path = (directory / name).resolve()
    if not path.is_relative_to(directory) or path == directory:
        raise ValueError("Una copia no puede salir de su directorio de evidencia.")
    return path


def verify_evidence(snapshots: list[str | Path], *, with_originals: bool = False,
                    source_root: str | Path = ROOT) -> dict:
    """Las copias pueden verificarse sin disponer de los originales locales ignorados por Git."""
    if not snapshots or type(with_originals) is not bool:
        raise ValueError("Indica al menos un inventario y una modalidad de verificación válida.")
    paths = [Path(path).resolve() for path in snapshots]
    if len(set(paths)) != len(paths): raise ValueError("No se debe contar dos veces el mismo inventario.")
    source_root = Path(source_root).resolve()
    reports, copies, bytes_read = [], 0, 0
    for snapshot in paths:
        raw = _read(snapshot, 512 * 1024)
        manifest = _strict_json(raw)
        if (not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int
                or manifest["schema_version"] != 1 or not isinstance(manifest.get("files"), dict) or not manifest["files"]
                or copies + len(manifest["files"]) > MAX_FILES):
            raise ValueError("Inventario incompatible: se requiere versión 1 con mapa de archivos, sin omisiones.")
        destinations = set()
        entries = []
        for name, item in manifest["files"].items():
            if (not isinstance(item, dict) or set(item) != {"source", "sha256"}
                    or not isinstance(item["source"], str) or not item["source"] or "://" in item["source"]
                    or not isinstance(item["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None):
                raise ValueError("Fuente o huella inválida: " + str(name))
            destination = _copy_path(snapshot.parent, name)
            if destination in destinations: raise ValueError("Dos nombres apuntan a la misma copia.")
            destinations.add(destination)
            digest, size = _digest(destination)
            bytes_read += size
            if digest != item["sha256"]: raise ValueError("La copia no conserva sus bytes: " + str(destination))
            original_checked = False
            if with_originals:
                source = Path(item["source"])
                if not source.is_absolute(): source = source_root / source
                source = source.resolve()
                if not source.is_relative_to(source_root):
                    raise ValueError("El original queda fuera de la raíz de fuentes permitida: " + str(source))
                original_digest, original_size = _digest(source)
                bytes_read += original_size
                if original_digest != item["sha256"]:
                    raise ValueError("El original no coincide con la copia: " + str(source))
                original_checked = True
            if bytes_read > MAX_TOTAL_BYTES: raise ValueError("La verificación supera el límite total de lectura.")
            entries.append({"name": name, "sha256": digest, "bytes": size, "original_checked": original_checked})
        copies += len(entries)
        reports.append({"snapshot": str(snapshot), "manifest_sha256": sha256(raw).hexdigest(), "files": entries})
    return {"schema_version": 1, "protocol": "evidence_integrity_v1", "status": "verified",
            "mode": "copies_and_originals" if with_originals else "copies_only",
            "copies_verified": copies, "original_references_verified": copies if with_originals else None,
            "bytes_read": bytes_read, "scope": "file_integrity_only_not_recalculation_or_semantic_review",
            "snapshots": reports, "model_requests": 0, "backtests": 0, "api_cost_usd": "0"}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — verificar copias sin consultar modelos o recalcular")
    parser.add_argument("--snapshot", type=Path, action="append", required=True)
    parser.add_argument("--with-originals", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = verify_evidence(args.snapshot, with_originals=args.with_originals, source_root=args.source_root)
        if args.json: print(json.dumps(result, ensure_ascii=True))
        else:
            print(f"Copias verificadas: {result['copies_verified']}.")
            print("Originales: " + (str(result["original_references_verified"]) + " referencias verificadas." if args.with_originals else "no inspeccionados."))
            print("Integridad de archivos; cero consultas de modelo y backtests.")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Verificación detenida: {error}\n")


if __name__ == "__main__": main()
