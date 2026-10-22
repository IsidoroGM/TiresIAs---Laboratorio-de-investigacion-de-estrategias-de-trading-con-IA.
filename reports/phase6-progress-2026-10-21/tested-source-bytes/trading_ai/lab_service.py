"""Índice descartable de consulta; sin escrituras ni acciones de investigación."""

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import sys
import threading
import time

from trading_ai.lab_catalog import Catalog, ERRORS, ROOT, stamp
from trading_ai.lab_query import LabQuery


def now():
    return datetime.now(timezone.utc).isoformat()


def weight(value, seen=None):
    """Peso de objetos Python retenidos, sin contar dos veces referencias compartidas."""
    seen = set() if seen is None else seen
    if id(value) in seen: return 0
    seen.add(id(value))
    total = sys.getsizeof(value)
    if isinstance(value, dict):
        total += sum(weight(k, seen) + weight(v, seen) for k, v in value.items())
    elif isinstance(value, (list, tuple, set, frozenset)):
        total += sum(weight(item, seen) for item in value)
    elif isinstance(value, Path):
        total += sys.getsizeof(str(value))
    return total


class MetadataCache:
    """Solo para construir resúmenes, nunca para verificar fichas u originales."""

    def __init__(self, limit=32 * 1024 * 1024):
        self.limit, self.bytes = limit, 0
        self.entries = OrderedDict()

    def get(self, path, version):
        item = self.entries.get(path)
        if item is None or item[0] != version: return None
        self.entries.move_to_end(path)
        return item[1]

    def put(self, path, version, raw):
        previous = self.entries.pop(path, None)
        if previous: self.bytes -= previous[2]
        size = weight((path, version, raw))
        if size > self.limit: return
        self.entries[path] = (version, raw, size)
        self.bytes += size
        while self.bytes > self.limit:
            _, old = self.entries.popitem(last=False)
            self.bytes -= old[2]

    def clear(self):
        self.entries.clear()
        self.bytes = 0


class LabService:
    """Una actualización en curso y publicación atómica de cada generación."""

    def __init__(self, root=ROOT, *, interval=2.0, max_index_bytes=16 * 1024 * 1024):
        self.root, self.interval = Path(root).resolve(), interval
        self.max_index_bytes = max_index_bytes
        self._condition = threading.Condition()
        self._index, self._thread = None, None
        self._refreshing, self._closed = False, False
        self._checked, self._checked_at, self._error = 0.0, None, None
        self._sequence = 0
        self._metadata = MetadataCache()

    def _unchanged(self, dependencies):
        # Los padres se comprueban antes: un padre cambiado detiene la inspección.
        for path in sorted(dependencies, key=lambda p: (len(p.parts), str(p))):
            if stamp(path) != dependencies[path]: return False
        return True

    def _build(self, force):
        if force: self._metadata.clear()
        for attempt in range(2):
            catalog = Catalog(self.root, metadata_cache=self._metadata)
            query = LabQuery(catalog=catalog)
            views = query.overviews()
            if self._unchanged(catalog.dependencies): break
            if attempt: raise ValueError("Las fuentes cambiaron durante la actualización del índice.")
        index = {"snapshot": catalog.snapshot(), "views": views, "indexed_at": now()}
        index["weight_bytes"] = weight(index)
        if index["weight_bytes"] > self.max_index_bytes:
            raise ValueError("El índice supera su límite de memoria; no se publica una instantánea parcial.")
        return index

    def _refresh(self, force):
        index, error = None, None
        try:
            with self._condition: previous = self._index
            if force or previous is None or not self._unchanged(previous["snapshot"]["dependencies"]):
                index = self._build(force)
        except ERRORS as exception:
            error = str(exception)
        except Exception:
            error = "No se pudo actualizar el índice de consulta."
        finally:
            with self._condition:
                if index is not None and not self._closed:
                    self._sequence += 1
                    index["generation"] = self._sequence
                    self._index = index
                self._error, self._checked, self._checked_at = error, time.monotonic(), now()
                self._refreshing = False
                self._condition.notify_all()

    def _obtain(self, force=False):
        deadline = time.monotonic() + 30
        with self._condition:
            while self._refreshing and (self._index is None or force):
                remaining = deadline - time.monotonic()
                if remaining <= 0: raise ValueError("La actualización del índice sigue en curso; vuelve a intentarlo.")
                self._condition.wait(remaining)
            if self._closed: raise ValueError("El servicio de consulta está cerrado.")
            if self._index is None or force:
                self._refreshing = True
                synchronous = True
            else:
                synchronous = False
                if not self._refreshing and time.monotonic() - self._checked >= self.interval:
                    self._refreshing = True
                    self._thread = threading.Thread(target=self._refresh, args=(False,), name="tiresias-index", daemon=True)
                    self._thread.start()
        if synchronous: self._refresh(force)
        with self._condition:
            if self._index is None or force and self._error:
                raise ValueError(self._error or "Índice no disponible.")
            status = {"generation": self._index["generation"], "indexed_at": self._index["indexed_at"],
                      "checked_at": self._checked_at, "refreshing": self._refreshing,
                      "refresh_error": self._error, "metadata_max_age_seconds": self.interval,
                      "notice": "Índice de resúmenes; su fecha no es una verificación actual de integridad."}
            return self._index, status

    def overview(self, name, *, force=False, filters=None):
        index, status = self._obtain(force)
        result = deepcopy(index["views"][name])
        if name == "experiments" and filters:
            for key in ("pair", "origin", "state", "strategy", "date", "q"):
                value = str(filters.get(key, "")).casefold()
                if not value: continue
                if key == "q":
                    import json
                    result["items"] = [item for item in result["items"] if value in json.dumps(item, ensure_ascii=False).casefold()]
                elif key in ("strategy", "date"):
                    result["items"] = [item for item in result["items"] if value in str(item.get(key) or "").casefold()]
                else:
                    result["items"] = [item for item in result["items"] if value == str(item.get(key) or "").casefold()]
        result.update(queried_at=now(), index=status)
        return result

    def query(self, *, force=False):
        index, status = self._obtain(force)
        return LabQuery(catalog=Catalog.from_snapshot(index["snapshot"])), status

    def diagnostics(self):
        with self._condition:
            return {"generation": self._sequence, "refreshing": self._refreshing,
                    "index_weight_bytes": self._index["weight_bytes"] if self._index else 0,
                    "index_limit_bytes": self.max_index_bytes, "metadata_weight_bytes": self._metadata.bytes,
                    "metadata_limit_bytes": self._metadata.limit, "closed": self._closed}

    def close(self):
        with self._condition:
            self._closed = True
            thread = self._thread
            self._condition.notify_all()
        if thread is not None and thread is not threading.current_thread(): thread.join()
        self._metadata.clear()
        with self._condition: self._index = None
