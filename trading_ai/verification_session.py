"""Reutilización explícita de una verificación guiada, con guardas de lectura.

No guarda permisos, SQLite, cálculos ni decisiones. Cada acierto vuelve a leer
los bytes, rutas y listados observados; una variación detiene la sesión.
"""

from contextvars import ContextVar
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sys
from threading import RLock
from types import FunctionType

from trading_ai import guided_compact_request as guided


_ORIGINAL = guided.verify_guided_request
_PATH = {name: getattr(Path, name) for name in ("open", "exists", "is_file", "is_dir", "glob", "rglob", "iterdir")}
_ACTIVE = ContextVar("tiresias_verification_session", default=None)
_RECORDER = ContextVar("tiresias_verification_reads", default=None)
_LOCK = RLock()
_USERS = 0
MAX_FILES = 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_ENTRIES = 4096


def _bytes(path):
    with _PATH["open"](path, "rb") as stream:
        content = stream.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES: raise ValueError("Fuente demasiado grande para esta sesión de verificación.")
    return content


def _file(path):
    path = Path(path).absolute()
    target = path.resolve()
    content = _bytes(path)
    return str(target), sha256(content).hexdigest(), len(content)


def _value(value, depth=0):
    if depth > 12: raise TypeError
    if value is None or type(value) in (str, int, bool, float, bytes): return value
    if isinstance(value, Path): return ("path", str(value))
    if isinstance(value, FunctionType): return ("function", id(value), id(value.__code__))
    if type(value) in (list, tuple, set, frozenset):
        if len(value) > MAX_ENTRIES: raise TypeError
        items = tuple(_value(item, depth + 1) for item in value)
        return (type(value).__name__, tuple(sorted(items, key=repr)) if isinstance(value, (set, frozenset)) else items)
    if type(value) is dict:
        if len(value) > MAX_ENTRIES: raise TypeError
        return ("dict", tuple(sorted((repr(key), _value(item, depth + 1)) for key, item in value.items())))
    raise TypeError


def _configuration():
    result = []
    for name, module in sorted(tuple(sys.modules.items())):
        if not name.startswith("trading_ai.") or module is None: continue
        source = getattr(module, "__file__", None)
        if source and source.endswith(".py"):
            result.append((name, "source", _file(Path(source))))
        if name == __name__: continue
        for key, value in sorted(tuple(vars(module).items())):
            if key.startswith("__"): continue
            try: frozen = _value(value)
            except TypeError: continue
            result.append((name, key, frozen))
    return result


class _Reads:
    def __init__(self):
        self.files, self.probes, self.listings = {}, {}, {}
        self.total = 0

    def opened(self, path):
        path = Path(path).absolute()
        if path in self.files: return
        if len(self.files) >= MAX_FILES: raise ValueError("Demasiadas fuentes; no se omitirá ninguna.")
        try: fingerprint = _file(path)
        except FileNotFoundError:
            self.probes[("exists", path, (), ())] = False
            return
        self.total += fingerprint[2]
        if self.total > MAX_TOTAL_BYTES: raise ValueError("Las fuentes exceden el límite de lectura de la sesión.")
        self.files[path] = fingerprint

    def guard(self):
        for path, expected in self.files.items():
            if _file(path) != expected: raise ValueError("Cambió una fuente ya verificada: " + str(path))
        for (name, path, args, kwargs), expected in self.probes.items():
            if _PATH[name](path, *args, **dict(kwargs)) != expected: raise ValueError("Cambió la presencia de una fuente: " + str(path))
        for (name, path, args, kwargs), expected in self.listings.items():
            current = tuple(sorted(str(item.absolute()) for item in _PATH[name](path, *args, **dict(kwargs))))
            if current != expected: raise ValueError("Cambió un listado de fuentes o reservas: " + str(path))


def _open(path, *args, **kwargs):
    reads = _RECORDER.get()
    if reads is not None:
        mode = args[0] if args else kwargs.get("mode", "r")
        if any(char in mode for char in "wax+"):
            raise ValueError("El verificador de lectura no puede escribir archivos.")
        reads.opened(path)
    return _PATH["open"](path, *args, **kwargs)


def _probe(name):
    def call(path, *args, **kwargs):
        result = _PATH[name](path, *args, **kwargs)
        reads = _RECORDER.get()
        if reads is not None:
            key = (name, path.absolute(), args, tuple(sorted(kwargs.items())))
            if key in reads.probes and reads.probes[key] != result: raise ValueError("Una ruta cambió durante la lectura.")
            reads.probes[key] = result
        return result
    return call


def _listing(name):
    def call(path, *args, **kwargs):
        reads = _RECORDER.get()
        if reads is None: return _PATH[name](path, *args, **kwargs)
        items = []
        for item in _PATH[name](path, *args, **kwargs):
            items.append(item)
            if len(items) > MAX_ENTRIES: raise ValueError("Demasiadas entradas; no se recortará el listado.")
        key = (name, path.absolute(), args, tuple(sorted(kwargs.items())))
        value = tuple(sorted(str(item.absolute()) for item in items))
        if key in reads.listings and reads.listings[key] != value: raise ValueError("Un listado cambió durante la lectura.")
        reads.listings[key] = value
        return iter(items)
    return call


_WRAPPERS = {"open": _open, **{name: _probe(name) for name in ("exists", "is_file", "is_dir")},
             **{name: _listing(name) for name in ("glob", "rglob", "iterdir")}}


def _dispatch(run_dir):
    session = _ACTIVE.get()
    return _ORIGINAL(run_dir) if session is None else session.verify(run_dir)


def _aliases(old, new):
    for name, module in tuple(sys.modules.items()):
        if not name.startswith("trading_ai.") or module is None or name == __name__: continue
        for key, value in tuple(vars(module).items()):
            if value is old: setattr(module, key, new)


class VerificationSession:
    """Un solo uso y sin persistencia. Activación explícita por el llamador."""

    def __init__(self):
        self.entries, self.stats = {}, {"full_guided_validations": 0, "guarded_guided_hits": 0}
        self.closed, self.token, self.lock = False, None, RLock()

    def __enter__(self):
        global _USERS
        with _LOCK:
            if self.closed or self.token is not None or _ACTIVE.get() is not None:
                raise ValueError("Las sesiones de verificación no se anidan ni se reutilizan.")
            if _USERS == 0:
                if guided.verify_guided_request is not _ORIGINAL or any(getattr(Path, name) is not value for name, value in _PATH.items()):
                    raise ValueError("Hay verificadores o lectores sustituidos; no se activa la sesión.")
                _aliases(_ORIGINAL, _dispatch)
                for name, wrapper in _WRAPPERS.items(): setattr(Path, name, wrapper)
            _USERS += 1
            self.token = _ACTIVE.set(self)
        return self

    def __exit__(self, *_):
        global _USERS
        with _LOCK:
            _ACTIVE.reset(self.token)
            self.token = None
            _USERS -= 1
            if _USERS == 0:
                _aliases(_dispatch, _ORIGINAL)
                for name, original in _PATH.items(): setattr(Path, name, original)
            self.entries.clear()
            self.closed = True

    def verify(self, run_dir):
        if self.token is None or self.closed or _ACTIVE.get() is not self:
            raise ValueError("La sesión de verificación no está activa en este contexto.")
        with self.lock:
            path = Path(run_dir).absolute()
            key = (str(path), str(path.resolve()))
            if key in self.entries:
                record, reads, configuration = self.entries[key]
                reads.guard()
                if _configuration() != configuration: raise ValueError("Cambió el código o la configuración del verificador.")
                self.stats["guarded_guided_hits"] += 1
                return deepcopy(record)
            if len(self.entries) >= 4: raise ValueError("Demasiadas peticiones guiadas en una sesión.")
            reads = _Reads()
            before = _configuration()
            token = _RECORDER.set(reads)
            try: record = _ORIGINAL(path)
            finally: _RECORDER.reset(token)
            reads.guard()
            configuration = _configuration()
            if before != configuration: raise ValueError("Cambió la configuración durante la verificación guiada.")
            self.entries[key] = (deepcopy(record), reads, configuration)
            self.stats["full_guided_validations"] += 1
            return deepcopy(record)
