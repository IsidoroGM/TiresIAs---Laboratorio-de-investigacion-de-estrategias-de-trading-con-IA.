"""Captura de solo lectura: sin proveedor, resultados compactos, evaluación o cálculos."""

from hashlib import sha256
import json
from pathlib import Path
import runpy
from unittest.mock import patch

from trading_ai.compact_history import capture_compact_history, verify_compact_history
from trading_ai.compact_request import prepare_compact_request, verify_compact_request
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.rule_planning import _seal
from trading_ai.structured_generation import generation_budget_status


REQUEST = ROOT / ".local/structured-draft-requests/1646833181eb44c386eb32872f245afa"
ARCHIVE = ROOT / "reports/phase4-compact-memory-request-2026-10-20"


def main():
    if ARCHIVE.exists(): raise ValueError("La evidencia de esta comprobación ya existe.")
    old = runpy.run_path(str(ROOT / ".local/audit-compact-candidate.py"))
    inventory = old["old_artifacts"]()
    first_archive = old["ARCHIVE"]
    for name, item in json.loads((first_archive / "snapshot.json").read_bytes())["files"].items():
        inventory.append({"copy": str(first_archive / name), "source": item["source"], "sha256": item["sha256"]})
    def unchanged():
        for item in inventory:
            if any(sha256(Path(item[key]).read_bytes()).hexdigest() != item["sha256"] for key in ("copy", "source")):
                raise ValueError("Una evidencia anterior cambió: " + item["copy"])
    unchanged()
    status_sha = sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest()
    journal = RunJournal(ROOT / ".local/compact-memory-request-audits")
    journal.record("compact_memory_request_audit_started", old_copies=len(inventory))
    io = {"provider_calls": 0, "backtests": 0, "signals": 0, "outer_reads": 0, "compact_result_reads": 0}
    actual_open = Path.open
    def guarded_open(path, *args, **kwargs):
        if path.name in ("evaluation.xml", "comparison.json"):
            io["outer_reads"] += 1
            raise ValueError("No se permite leer evaluación exterior.")
        if "compact-executions" in path.parts:
            io["compact_result_reads"] += 1
            raise ValueError("La memoria no puede leer resultados de ejecuciones compactas.")
        return actual_open(path, *args, **kwargs)
    def blocked(kind):
        def fail(*args, **kwargs):
            io[kind] += 1
            raise ValueError("Acción prohibida en esta auditoría: " + kind)
        return fail
    with patch.object(Path, "open", guarded_open), \
            patch("trading_ai.compact_ollama.CompactOllamaProvider.describe", blocked("provider_calls")), \
            patch("trading_ai.compact_ollama.CompactOllamaProvider.complete", blocked("provider_calls")), \
            patch("trading_ai.ai.create_provider", blocked("provider_calls")), \
            patch("socket.socket.connect", blocked("provider_calls")), \
            patch("trading_ai.rule_execution._calculate", blocked("backtests")), \
            patch("trading_ai.rules.RuleStrategy.generate_signals", blocked("signals")):
        budget_before = generation_budget_status(REQUEST)
        history_dir = capture_compact_history(REQUEST)
        history = verify_compact_history(history_dir)
        print(json.dumps({"stage": "history_verified", "entries": len(history["entries"])}), flush=True)
        output = ROOT / ".local/compact-requests"
        before_dirs = set(output.glob("*"))
        try:
            request_dir = prepare_compact_request(history_dir, output_dir=output)
            prepared, error = verify_compact_request(request_dir), None
        except ValueError as failure:
            new_dirs = set(output.glob("*")) - before_dirs
            if len(new_dirs) != 1: raise
            request_dir, = new_dirs
            prepared, error = None, str(failure)
        budget_after = generation_budget_status(REQUEST)
    if any(io.values()): raise ValueError("Una ruta prohibida fue invocada; no se publicará una auditoría limpia.")
    unchanged()
    if sha256((ROOT / "docs/PROJECT_STATUS.md").read_bytes()).hexdigest() != status_sha or budget_after != budget_before:
        raise ValueError("Se alteró el estado de fase o el presupuesto.")
    record = {"schema_version": 1, "status": "prepared_without_permission" if prepared else "preparation_blocked_preserved",
              "history_dir": str(history_dir), "request_dir": str(request_dir), "error": error,
              "entry_statuses": [entry["status"] for entry in history["entries"]],
              "request_bytes": None if prepared is None else prepared["request_bytes"],
              "token_count": None, "fits_provider_context_verified": False,
              "budget_before": budget_before, "budget_after": budget_after, "new_generation_permission": False,
              "inherited_attempt_usage": [entry["source_usage"] for entry in history["entries"]],
              "new_usage": {"model_requests": 0, "input_tokens": 0, "output_tokens": 0, "api_cost_usd": "0", "backtests": 0},
              "io_guard": io, "old_copies_and_originals_checked": len(inventory),
              "project_status_sha256": status_sha, "phase_closed": False, "executable": False}
    _seal(journal, "audit.json", record, "compact_memory_request_audit_completed")
    ARCHIVE.mkdir()
    files = {}
    def copy(source, name):
        raw = source.read_bytes()
        target = ARCHIVE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        _write_exclusive(target, raw)
        files[name] = {"source": str(source), "sha256": sha256(raw).hexdigest()}
    for prefix, directory in (("history", history_dir), ("request", request_dir), ("audit", journal.directory)):
        for path in sorted(directory.iterdir()):
            if path.is_file(): copy(path, prefix + "/" + path.name)
    copy(Path(__file__).resolve(), "audit-compact-memory-request.py")
    _write_exclusive(ARCHIVE / "snapshot.json", json.dumps({"schema_version": 1, "files": files}, ensure_ascii=False, indent=2).encode("utf-8"))
    for name, item in files.items():
        if any(sha256(path.read_bytes()).hexdigest() != item["sha256"] for path in (ARCHIVE / name, Path(item["source"]))):
            raise ValueError("La copia nueva no conserva sus bytes: " + name)
    print(json.dumps({"audit_dir": str(journal.directory), "history_dir": str(history_dir), "request_dir": str(request_dir),
                      "status": record["status"], "request_bytes": record["request_bytes"], "io_guard": io,
                      "old_copies_checked": len(inventory), "new_copies_checked": len(files)}, ensure_ascii=True))


if __name__ == "__main__": main()
