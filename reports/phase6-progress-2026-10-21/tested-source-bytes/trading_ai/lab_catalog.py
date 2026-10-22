"""Catálogo acotado de archivos existentes. No importa ejecutores ni crea registros."""

from datetime import datetime, timezone
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import re

from trading_ai.evidence import verify_evidence
from trading_ai.formalization import _strict_json


ROOT = Path(__file__).resolve().parent.parent
MAX_FILE = 32 * 1024 * 1024
MAX_ENTRIES = 4096
MAX_TOTAL = 256 * 1024 * 1024
BUCKETS = frozenset((
    "research", "chat-experiments", "holdout", "evaluations", "robustness", "discovery", "idea-revisions",
    "formalization", "research-sessions", "structured-ideas", "structured-revisions",
    "structured-sessions", "structured-drafts", "structured-review-memory",
    "compact-generations", "compact-candidates", "compact-executions", "compact-history",
    "compact-period-executions", "rule-executions", "rule-reviews", "campaign-attempts",
    "campaign-cycles", "campaign-memory", "campaign-reviews", "campaign-executions",
    "walk-forward-runs", "walk-forward-plans", "campaign-cycle-permits", "campaign-plans",
    "rule-plans", "compact-plans", "validation", "campaign-ledger",
))
PRIMARY = (
    "cycle.json", "results.json", "comparison.json", "frozen.json", "proposal.json",
    "revision.json", "candidate.json", "session.json", "idea.json", "translation.json",
    "completion.json", "attempt.json", "reservation.json", "draft.json", "memory.json",
    "history.json", "review.json", "reviews.json", "sessions.json",
)
SUPPORT_ONLY = frozenset(("walk-forward-plans", "campaign-cycle-permits", "campaign-plans",
                          "rule-plans", "compact-plans", "validation", "campaign-ledger"))
EXTENSIONS = frozenset((".json", ".jsonl", ".sha256", ".md", ".raw", ".xml", ".txt"))
ERRORS = (OSError, ValueError, TypeError, KeyError, IndexError, RecursionError, UnicodeError)


def stamp(path):
    """Metadatos de invalidación; nunca son una comprobación criptográfica."""
    try:
        value = path.lstat()
        return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
                value.st_ctime_ns, value.st_mode, getattr(value, "st_file_attributes", 0))
    except FileNotFoundError:
        return None


def identifier(value):
    return sha256(str(value).encode("utf-8")).hexdigest()[:24]


def admitted_bucket(name):
    return name in BUCKETS or re.fullmatch(r"(?:research|consistency|sufficiency)-check-2026-10-19-[0-9a-f]{32}", name) is not None


def origin_key(value):
    """Identidad histórica portable; nunca convierte una ruta declarada en una lectura."""
    parts = PureWindowsPath(str(value)).parts
    if ".." in parts:
        raise ValueError("La procedencia contiene un escape de directorio.")
    if ".local" not in parts:
        return None
    index = parts.index(".local")
    tail = parts[index:]
    if len(tail) < 3 or not admitted_bucket(tail[1]):
        return None
    return "/".join(tail)


class Catalog:
    """Una instantánea por consulta; no hay caché persistente ni escrituras."""

    def __init__(self, root=ROOT, *, metadata_cache=None):
        self.root = Path(root).resolve()
        self.files, self.records, self.archives = {}, {}, {}
        self.warnings, self.bytes_read = [], 0
        self.by_origin = {}
        self.dependencies = {}
        self._metadata_cache = metadata_cache
        self._scan_safe = set()
        self.begin_read()
        self.queried_at = datetime.now(timezone.utc).isoformat()
        try: self._scan()
        finally: self._scan_safe = None

    def begin_read(self):
        self.bytes_read, self._reads = 0, {}
        self.queried_at = datetime.now(timezone.utc).isoformat()

    def snapshot(self):
        return deepcopy({name: getattr(self, name) for name in
                         ("root", "files", "records", "archives", "warnings", "by_origin", "dependencies")})

    @classmethod
    def from_snapshot(cls, snapshot):
        result = cls.__new__(cls)
        result.__dict__.update(deepcopy(snapshot))
        result._metadata_cache, result._scan_safe = None, None
        result.begin_read()
        return result

    def watch(self, path):
        if path not in self.dependencies: self.dependencies[path] = stamp(path)

    def safe(self, path, *, fresh=False):
        path = Path(path).absolute()
        relative = path.relative_to(self.root)
        if not relative.parts or ".." in relative.parts:
            raise ValueError("Ruta fuera de las ubicaciones admitidas.")
        if relative.parts[0] == ".local":
            if len(relative.parts) < 2 or not admitted_bucket(relative.parts[1]):
                raise ValueError("Directorio local no admitido.")
        elif relative.parts[0] != "reports":
            raise ValueError("Solo se consultan reports y registros locales admitidos.")
        current = self.root
        for part in relative.parts:
            current = current / part
            if not fresh and self._scan_safe is not None and current in self._scan_safe:
                continue
            if current.is_symlink() or current.is_junction():
                raise ValueError("No se siguen enlaces simbólicos o junctions.")
            if not fresh and self._scan_safe is not None: self._scan_safe.add(current)
        if (fresh or self._scan_safe is None) and not path.resolve().is_relative_to(self.root):
            raise ValueError("La ruta resuelta sale del proyecto.")
        return path

    def read(self, path, limit=MAX_FILE):
        if self.bytes_read > MAX_TOTAL: raise ValueError("Se supera el límite de lectura de la consulta.")
        path = self.safe(path, fresh=True)
        before = stamp(path)
        if not path.is_file() or path.stat().st_size > limit:
            raise ValueError("Archivo ausente, no regular o demasiado grande.")
        cached = self._reads.get(path)
        if cached is not None:
            if cached[0] != before: raise ValueError("El archivo cambió durante la consulta.")
            if len(cached[1]) > limit: raise ValueError("Archivo demasiado grande.")
            return cached[1]
        raw = self._metadata_cache.get(path, before) if self._metadata_cache is not None else None
        if raw is None:
            with path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                # En Windows lstat y fstat pueden dar distinta semántica a ctime.
                # La identidad y mtime se cotejan entre APIs; ctime entre fstat.
                if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != before[:4]:
                    raise ValueError("El archivo cambió antes de abrirse.")
                raw = stream.read(limit + 1)
                closed = os.fstat(stream.fileno())
            if (opened.st_ino, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (closed.st_ino, closed.st_size, closed.st_mtime_ns, closed.st_ctime_ns):
                raise ValueError("El archivo cambió durante la lectura.")
        if stamp(path) != before: raise ValueError("El archivo cambió durante la lectura.")
        self.bytes_read += len(raw)
        if len(raw) > limit or self.bytes_read > MAX_TOTAL:
            raise ValueError("Se supera el límite de lectura de la consulta.")
        self.dependencies.setdefault(path, before)
        self._reads[path] = (before, raw)
        if self._metadata_cache is not None: self._metadata_cache.put(path, before, raw)
        return raw

    def json(self, path, limit=MAX_FILE):
        value = _strict_json(self.read(path, limit))
        if not isinstance(value, dict):
            raise ValueError("Se requiere un objeto JSON.")
        return value

    def children(self, path):
        try:
            path = self.safe(path)
            self.watch(path)
            if not path.exists(): return []
            result = []
            for item in path.iterdir():
                if len(result) >= MAX_ENTRIES:
                    raise ValueError("Demasiadas entradas en un directorio; catálogo incompleto.")
                result.append(item)
            return sorted(result)
        except ERRORS as error:
            self.warnings.append(f"{path.name}: {error}")
            return []

    def add_file(self, path, *, source=None, digest=None, archive=None):
        path = self.safe(path)
        if path.suffix not in EXTENSIONS:
            return None
        relative = path.relative_to(self.root).as_posix()
        key = identifier(relative)
        if key not in self.files and len(self.files) >= MAX_ENTRIES:
            raise ValueError("Demasiados archivos; catálogo incompleto.")
        self.files[key] = {"id": key, "path": relative, "source": source or relative,
                           "expected_sha256": digest, "archive": archive}
        self.watch(path)
        return key

    def _local_files(self, directory):
        group = {}
        for path in self.children(directory):
            if path.suffix not in EXTENSIONS: continue
            try:
                if self.safe(path).is_file():
                    key = self.add_file(path)
                    group[path.name] = key
                    self.by_origin[(None, path.relative_to(self.root).as_posix())] = key
            except ERRORS as error:
                self.warnings.append(f"{path.name}: {error}")
        return group

    def _record(self, group, bucket, archive=None):
        if bucket in SUPPORT_ONLY: return
        name = next((name for name in PRIMARY if name in group), None)
        if name is None and "events.jsonl" not in group: return
        key = group[name or "events.jsonl"]
        record = {"id": key, "file": key, "files": group, "bucket": bucket, "archive": archive,
                  "missing_primary": name is None}
        self.records[key] = record

    def _scan(self):
        local = self.root / ".local"
        self.watch(local)
        # El directorio .local solo se lista; no se abre ninguna carpeta excluida.
        if local.is_symlink() or local.is_junction():
            self.warnings.append(".local es un enlace; no se consulta.")
        elif local.is_dir():
            for bucket in sorted(local.iterdir()):
                if not admitted_bucket(bucket.name): continue
                try:
                    if not self.safe(bucket).is_dir(): continue
                    for run in self.children(bucket):
                        if self.safe(run).is_dir():
                            self._record(self._local_files(run), bucket.name)
                            if bucket.name == "robustness":
                                for attempt in self.children(run / "attempts"):
                                    if self.safe(attempt).is_dir(): self._record(self._local_files(attempt), bucket.name)
                    # Algunas comprobaciones históricas son ellas mismas una ejecución.
                    if bucket.name.startswith(("research-check-", "consistency-check-", "sufficiency-check-")):
                        self._record(self._local_files(bucket), bucket.name)
                except ERRORS as error:
                    self.warnings.append(f"{bucket.name}: {error}")
        for directory in self.children(self.root / "reports"):
            try:
                if directory.suffix == ".md" and self.safe(directory).is_file():
                    self.add_file(directory)
                    continue
                if not self.safe(directory).is_dir(): continue
                self.watch(directory)
                manifest = directory / "snapshot.json"
                self.watch(manifest)
                if not manifest.exists(): continue
                value = self.json(manifest, 512 * 1024)
                legacy = isinstance(value.get("files"), list) and isinstance(value.get("date"), str)
                if not legacy and (value.get("schema_version") != 1 or not isinstance(value.get("files"), dict)):
                    raise ValueError("Inventario incompatible.")
                entries = value["files"]
                if legacy:
                    entries = {}
                    for item in value["files"]:
                        if not isinstance(item, dict) or not isinstance(item.get("snapshot"), str) or item["snapshot"] in entries:
                            raise ValueError("Inventario histórico incompatible o con copias duplicadas.")
                        entries[item["snapshot"]] = {key: item.get(key) for key in ("source", "sha256")}
                archive = self.add_file(manifest)
                self.archives[archive] = {"manifest": manifest, "groups": {}, "legacy": legacy, "entries": entries}
                for name, entry in entries.items():
                    if (not isinstance(name, str) or PureWindowsPath(name).is_absolute()
                            or PureWindowsPath(name).drive or ".." in PureWindowsPath(name).parts
                            or not isinstance(entry, dict) or not isinstance(entry.get("source"), str)
                            or re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256"))) is None):
                        raise ValueError("Entrada de inventario incompatible.")
                    path = self.safe(directory / name)
                    if not path.is_relative_to(directory): raise ValueError("Copia fuera de su inventario.")
                    key = self.add_file(path, source=entry["source"], digest=entry["sha256"], archive=archive)
                    origin = origin_key(entry["source"])
                    if key and origin:
                        self.by_origin[(archive, origin)] = key
                        parent, filename = origin.rsplit("/", 1)
                        self.archives[archive]["groups"].setdefault(parent, {})[filename] = key
                for parent, group in self.archives[archive]["groups"].items():
                    self._record(group, parent.split("/")[1], archive)
            except ERRORS as error:
                self.warnings.append(f"{directory.name}: {error}")

    def file(self, key):
        if key not in self.files: raise KeyError("Archivo no catalogado.")
        entry = self.files[key]
        raw = self.read(self.root / entry["path"])
        digest = sha256(raw).hexdigest()
        return {**entry, "sha256": digest, "bytes": len(raw)}, raw

    def events(self, record):
        key = record["files"].get("events.jsonl")
        if key is None: return []
        _, raw = self.file(key)
        events = [_strict_json(line) for line in raw.splitlines() if line.strip()]
        if not events or any(not isinstance(event, dict) or not isinstance(event.get("event"), str) for event in events):
            raise ValueError("Eventos incompletos o incompatibles.")
        return events

    def payload(self, record):
        entry, raw = self.file(record["file"])
        if entry["path"].endswith(".jsonl"): return {}
        value = _strict_json(raw)
        if not isinstance(value, dict): raise ValueError("Registro JSON incompatible.")
        return value

    def linked(self, record, reference, filename):
        if not isinstance(reference, dict) or not isinstance(reference.get("directory"), str): return None
        origin = origin_key(str(PureWindowsPath(reference["directory"]) / filename))
        key = self.by_origin.get((record["archive"], origin))
        if key is None: return None
        value = _strict_json(self.file(key)[1])
        if not isinstance(value, dict): raise ValueError("Referencia JSON incompatible.")
        return value

    def integrity(self, record):
        """Integridad de archivos, sin afirmar vigencia o certificación de resultados."""
        key = record["file"]
        entry, raw = self.file(key)
        if record["missing_primary"]:
            return {"state": "incomplete", "label": "Falta el registro principal; solo hay eventos"}
        if record["archive"]:
            archive = self.archives[record["archive"]]
            try:
                # Prevalidar TODAS las rutas antes del lector existente (también las no visibles).
                # El inventario vuelve a leerse: no se verifica una lista antigua tras un cambio.
                current = self.json(archive["manifest"], 512 * 1024)
                original = archive["entries"]
                if archive["legacy"]:
                    current_entries = {item["snapshot"]: {key: item.get(key) for key in ("source", "sha256")} for item in current["files"]}
                else: current_entries = current["files"]
                if current_entries != original: raise ValueError("El inventario cambió durante la consulta.")
                for name in original:
                    target = self.safe(archive["manifest"].parent / name)
                    if not target.is_relative_to(archive["manifest"].parent):
                        raise ValueError("La copia sale del inventario.")
                if archive["legacy"]:
                    for name, item in original.items():
                        if sha256(self.read(archive["manifest"].parent / name)).hexdigest() != item["sha256"]:
                            raise ValueError("Copia histórica ausente o alterada: " + name)
                    result = {"scope": "legacy_file_integrity_only", "copies_verified": len(original)}
                else: result = verify_evidence([archive["manifest"]])
                return {"state": "copies_verified", "label": "Integridad de copias comprobada",
                        "scope": result["scope"], "copies": result["copies_verified"]}
            except ERRORS as error:
                return {"state": "unverifiable", "label": "Inventario incompleto o alterado", "reason": str(error)}
        # No se sustituye el original por una copia si sus bytes no coinciden.
        origin = entry["path"]
        expected = {item["expected_sha256"] for item in self.files.values()
                    if item["archive"] and origin_key(item["source"]) == origin}
        if expected:
            if sha256(raw).hexdigest() not in expected:
                return {"state": "changed", "label": "Original diferente de las copias archivadas"}
            return {"state": "matches_archive", "label": "Registro cotejado con una huella archivada",
                    "scope": "primary_file_integrity_only_not_current_execution_status"}
        return {"state": "unverified", "label": "Registro sin verificación completa"}
