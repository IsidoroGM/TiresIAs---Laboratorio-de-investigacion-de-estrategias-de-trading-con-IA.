"""Caché acotada por lectura: reutiliza desarrollo validado solo tras contrastar sus fuentes."""

import argparse
from contextvars import ContextVar
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from threading import RLock

from trading_ai import robustness
from trading_ai.guided_compact_request import verify_guided_request
from trading_ai.formalization import _read


_ORIGINAL = robustness._development
_ACTIVE = ContextVar("trading_ai_validated_read_cache", default=None)
_LOCK = RLock()
_USERS = 0
MAX_DATASETS = 8
MAX_CONTENT_BYTES = 16 * 1024 * 1024
DEPENDENCY_FUNCTIONS = ("_frozen_hashes", "_json", "_policy", "validate_proposal", "load_ecb_rates")


def _aliases(old, new):
    for name, module in tuple(sys.modules.items()):
        if name.startswith("trading_ai.") and module is not None and module.__dict__.get("_development") is old:
            module.__dict__["_development"] = new


def _wrapped(frozen_dir):
    active = _ACTIVE.get()
    return _ORIGINAL(frozen_dir) if active is None else active.development(frozen_dir)


class ValidatedReadCache:
    """Solo metadatos de desarrollo; nunca conserva propuestas, revisiones o permisos globales."""

    def __init__(self):
        self.entries = {}
        self.stats = {"full_validations": 0, "guarded_hits": 0, "uncached_large_or_limit": 0}
        self._token = None
        self._helper_sha = None
        self._data_lock = RLock()
        self._closed = False

    def __enter__(self):
        global _USERS
        if self._token is not None or self._closed: raise ValueError("Una instancia solo admite un ámbito de lectura.")
        self._helper_sha = sha256(Path(robustness.__file__).read_bytes()).hexdigest()
        with _LOCK:
            if robustness._development not in (_ORIGINAL, _wrapped):
                raise ValueError("Otro envoltorio de desarrollo está activo; no se sustituirá.")
            _aliases(_ORIGINAL, _wrapped)
            _USERS += 1
        self._token = _ACTIVE.set(self)
        return self

    def __exit__(self, *_):
        global _USERS
        _ACTIVE.reset(self._token)
        self._token = None
        with _LOCK:
            _USERS -= 1
            if _USERS == 0: _aliases(_wrapped, _ORIGINAL)
        with self._data_lock:
            self._closed = True
            self.entries.clear()

    def _globals(self):
        namespace = _ORIGINAL.__globals__
        return {"functions": {name: namespace[name] for name in DEPENDENCY_FUNCTIONS},
                "execution_policy": deepcopy(namespace["EXECUTION_POLICY"]),
                "research_files": tuple(namespace["RESEARCH_FILES"])}

    def _guard(self, entry):
        if (self._globals() != entry["globals"] or sha256(Path(robustness.__file__).read_bytes()).hexdigest() != self._helper_sha
                or _ORIGINAL.__globals__["_frozen_hashes"]() != entry["value"][0]["code_sha256"]):
            raise ValueError("Código o dependencias de desarrollo cambiaron durante la lectura.")
        for declared, target, expected in entry["files"]:
            if declared.resolve() != target or sha256(_read(target, 32 * 1024 * 1024)).hexdigest() != expected:
                raise ValueError("Una fuente de desarrollo cambió; la caché no se reutilizará.")

    def _entry(self, frozen_dir, value, globals_before):
        frozen, reference, content = value
        events_path = frozen_dir / "events.jsonl"
        events_raw = _read(events_path, 2 * 1024 * 1024)
        events = [json.loads(line) for line in events_raw.splitlines()]
        checksum_path = frozen_dir / "frozen.sha256"
        checksum_raw = _read(checksum_path, 128)
        if (not events or events[-1]["event"] != "proposal_frozen"
                or events[-1]["data"]["frozen_sha256"] != reference["frozen_sha256"]
                or checksum_raw.decode("ascii").strip() != reference["frozen_sha256"]
                or sha256(content).hexdigest() != reference["development_sha256"]):
            raise ValueError("Las fuentes cambiaron al capturar la validación de desarrollo.")
        files = [(frozen_dir / "frozen.json", reference["frozen_sha256"]),
                 (checksum_path, sha256(checksum_raw).hexdigest()), (events_path, sha256(events_raw).hexdigest())]
        research_dir, split_dir = Path(frozen["research"]["directory"]), Path(frozen["split"]["directory"])
        files += [(research_dir / name, frozen["research"]["sha256"][name]) for name in globals_before["research_files"]]
        files += [(split_dir / "manifest.json", reference["manifest_sha256"]),
                  (split_dir / "development.xml", reference["development_sha256"])]
        entry = {"value": (deepcopy(frozen), deepcopy(reference), content), "globals": globals_before,
                 "files": [(path, path.resolve(), expected) for path, expected in files]}
        self._guard(entry)
        return entry

    def development(self, frozen_dir):
        with self._data_lock:
            return self._development(frozen_dir)

    def _development(self, frozen_dir):
        if self._closed or _ACTIVE.get() is not self: raise ValueError("La caché solo puede usarse dentro de su ámbito de lectura.")
        if not isinstance(frozen_dir, Path): return _ORIGINAL(frozen_dir)
        key = (str(frozen_dir), str(frozen_dir.resolve()))
        if key in self.entries:
            entry = self.entries[key]
            self._guard(entry)
            self.stats["guarded_hits"] += 1
        else:
            globals_before = self._globals()
            value = _ORIGINAL(frozen_dir)
            self.stats["full_validations"] += 1
            if len(self.entries) >= MAX_DATASETS or len(value[2]) > MAX_CONTENT_BYTES:
                self.stats["uncached_large_or_limit"] += 1
                return value
            entry = self._entry(frozen_dir, value, globals_before)
            self.entries[key] = entry
        frozen, reference, content = entry["value"]
        return deepcopy(frozen), deepcopy(reference), content


def verify_guided_with_cache(run_dir: str | Path) -> dict:
    with ValidatedReadCache() as cache:
        packet = verify_guided_request(run_dir)
        stats = dict(cache.stats)
    return {"schema_version": 1, "protocol": "cached_guided_read_v1", "method": "guarded_frozen_development_cache",
            "packet": packet, "cache": stats, "cache_scope": "this_read_only_call", "read_only": True,
            "cache_code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "new_generation_permission": False, "executable": False,
            "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0}}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — lectura guiada con caché local y fuentes revalidadas")
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try: print(json.dumps(verify_guided_with_cache(args.run), ensure_ascii=True))
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Lectura no verificable: {error}\n")


if __name__ == "__main__": main()
