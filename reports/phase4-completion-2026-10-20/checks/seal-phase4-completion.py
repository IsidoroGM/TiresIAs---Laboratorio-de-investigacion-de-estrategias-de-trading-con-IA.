"""Cierra evidencia únicamente si toda la colección ejecutada está aprobada."""

from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
import runpy
import socket
import sys
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
from trading_ai import campaign_cycle as cycle
from trading_ai import campaign_ledger as ledger
from trading_ai import rule_execution as engine
from trading_ai import walk_forward as walk
from trading_ai.ai import OllamaProvider
from trading_ai.evidence import verify_evidence
from trading_ai.holdout import _write_exclusive
from trading_ai.research import RunJournal
from trading_ai.rule_planning import _seal
from trading_ai.validated_read_cache import ValidatedReadCache
from trading_ai.verification_session import VerificationSession

ARCHIVE = ROOT / "reports/phase4-completion-2026-10-20"
CHECK = ROOT / ".local/phase4-completion-checks/bdd6a55c937f4f2abc272a9ad2d64625"


def main():
    if ARCHIVE.exists(): raise ValueError("La evidencia ya está sellada; no se sobrescribe.")
    manifest = json.loads((ROOT / ".local/phase4-suite-manifest.json").read_bytes())
    for name, digest in manifest["source_sha256"].items():
        if sha256((ROOT / name).read_bytes()).hexdigest() != digest: raise ValueError("Las fuentes cambiaron durante la suite: " + name)
    verified, suites = set(), []
    for index, group in enumerate(manifest["groups"], 1):
        xml = ROOT / f".local/phase4-suite-{index}.xml"
        tree = ET.parse(xml)
        nodes = set()
        for case in tree.findall(".//testcase"):
            if any(case.find(tag) is not None for tag in ("failure", "error", "skipped")):
                raise ValueError("La colección no está íntegramente aprobada: " + case.attrib["name"])
            module = case.attrib["classname"]
            file = next((file for file in group["files"] if module == file[:-3].replace("/", ".") or module.startswith(file[:-3].replace("/", ".") + ".")), None)
            if file is None: raise ValueError("Prueba sin origen en la partición: " + module)
            prefix = file[:-3].replace("/", ".")
            suffix = module[len(prefix):].strip(".")
            node = file + "::" + (suffix.replace(".", "::") + "::" if suffix else "") + case.attrib["name"]
            # La colección normalizó barras de Windows, incluidos IDs parametrizados.
            # Aplicar exactamente la misma comparación y rechazar colisiones.
            node = node.replace("\\", "/")
            if node in nodes or node in verified: raise ValueError("Prueba duplicada entre procesos.")
            nodes.add(node)
        if nodes != set(group["expected_nodes"]): raise ValueError("La partición no coincide con la colección prevista.")
        verified.update(nodes)
        suites.append({"index": index, "passed": len(nodes), "time_seconds": tree.find("testsuite").attrib["time"]})
    if verified != set(manifest["all_nodes"]): raise ValueError("Faltan pruebas de la colección global.")
    old = runpy.run_path(str(ROOT / ".local/audit-campaign-plan.py"))
    names = (*old["HISTORY"], "phase4-campaign-plan-2026-10-20", "phase4-campaign-ledger-2026-10-20",
             "phase4-campaign-attempts-2026-10-20", "phase4-campaign-controller-2026-10-20",
             "phase4-campaign-review-2026-10-20", "phase4-campaign-execution-2026-10-20", "phase4-campaign-memory-2026-10-20")
    snapshots = [ROOT / "reports" / name / "snapshot.json" for name in names]
    prior = verify_evidence(snapshots, with_originals=True)
    check = json.loads((CHECK / "application-check.json").read_bytes())
    journal = RunJournal(ROOT / ".local/phase4-final-audits")
    forbidden_calls = []
    def forbidden(*args, **kwargs):
        forbidden_calls.append(True)
        raise AssertionError("No hay consultas o recálculos en el sellado.")
    with ExitStack() as stack:
        for obj, name in ((socket.socket, "connect"), (engine, "_calculate"), (OllamaProvider, "complete"),
                          (ledger, "reserve_proposal"), (ledger, "reserve_comparison")):
            stack.enter_context(patch.object(obj, name, forbidden))
        with VerificationSession(): cycle_result = cycle.inspect_cycle(check["cycle_run"])
        with ValidatedReadCache(): walk_result = walk.verify_run(check["walk_forward_run"])
    if forbidden_calls: raise ValueError("El sellado intentó nuevas acciones.")
    if ledger.inspect_campaign(check["scope_id"]) != cycle_result["state"]: raise ValueError("La suite cambió la campaña real.")
    audit = {"schema_version": 1, "status": "phase4_development_scope_completed", "passed": len(verified), "suite_partitions": suites,
             "source_files_unchanged": len(manifest["source_sha256"]), "prior_copies_verified": prior["copies_verified"],
             "prior_inventories": len(snapshots), "application_check": str(CHECK), "new_research_usage": cycle_result["usage"]["usage"],
             "inherited_compact_usage": cycle_result["usage"]["inherited_usage"], "cycle_outcome": cycle_result["stop_reason"],
             "walk_forward_backtests": walk_result["completed_backtests"], "forbidden_calls_during_seal": 0,
             "remaining_accounting_slots": cycle_result["state"]["remaining_accounting_slots"],
             "api_cost_usd": "0", "scope": "known_development_history_only", "independent_validation": False,
             "automatic_adoption": False, "real_money_operations": False, "commits": 0, "pushes": 0}
    audit["node_id_comparison"] = "same_windows_separator_normalization_in_collection_and_junit_no_collisions"
    _seal(journal, "closure.json", audit, "phase4_development_closed")
    sources = {"closure/" + name: journal.directory / name for name in ("closure.json", "closure.json.sha256", "events.jsonl")}
    for name in ("application-check.json", "application-check.json.sha256", "local-cycle-status.json", "walk-forward-result.json", "events.jsonl"):
        sources["application-check/" + name] = CHECK / name
    for name in ("campaign_context", "campaign_cycle", "walk_forward"):
        sources["source/" + name + ".py"] = ROOT / "trading_ai" / (name + ".py")
    for name in ("campaign_cycle", "campaign_cycle_integration", "walk_forward"):
        sources["source/" + name + "_tests.py"] = ROOT / "tests" / ("test_" + name + ".py")
    for name in ("partition-phase4-suite.py", "check-phase4-completion.py", "seal-phase4-completion.py", "phase4-suite-manifest.json", "phase4-cycle-tests.xml",
                 "phase4-suite-1.xml", "phase4-suite-2.xml", "phase4-suite-3.xml"):
        sources["checks/" + name] = ROOT / ".local" / name
    for prefix, directory in (("cycle-permit", check["cycle_permit"]), ("cycle", check["cycle_run"]),
                              ("walk-plan", check["walk_forward_plan"]), ("walk-run", check["walk_forward_run"])):
        for path in sorted(Path(directory).iterdir()):
            if path.is_file(): sources[prefix + "/" + path.name] = path
    for entry in cycle_result["entries"]:
        for name in entry["capture_source"]["sha256"]:
            sources[f"capture-{entry['number']:02d}/" + name] = Path(entry["capture_source"]["directory"]) / name
    for path in sorted(engine.ACCESS_ROOT.glob("*.json")):
        value = json.loads(path.read_bytes())
        if value.get("run_dir") == check["walk_forward_run"]: sources["calculation-claims/" + path.name] = path
    sources["cycle-scope-claim.json"] = cycle.ACCESS_ROOT / (check["scope_id"] + ".json")
    contents = {name: path.read_bytes() for name, path in sources.items()}
    ARCHIVE.mkdir(exist_ok=False)
    files = {}
    for name, raw in contents.items():
        destination = ARCHIVE / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        _write_exclusive(destination, raw)
        files[name] = {"source": str(sources[name]), "sha256": sha256(raw).hexdigest()}
    _write_exclusive(ARCHIVE / "snapshot.json", (json.dumps({"schema_version": 1, "files": files}, ensure_ascii=False, indent=2) + "\n").encode())
    checked = verify_evidence(snapshots + [ARCHIVE / "snapshot.json"], with_originals=True)
    print(json.dumps({"audit_run": str(journal.directory), "passed": len(verified), "partitions": suites,
                      "new_inventory_entries": len(files), "copies_verified": checked["copies_verified"],
                      "inventories": len(snapshots)+1, "archive_bytes": sum(map(len, contents.values())),
                      "cycle_outcome": cycle_result["stop_reason"], "new_research_usage": audit["new_research_usage"],
                      "walk_forward_backtests": audit["walk_forward_backtests"]}, ensure_ascii=True))


if __name__ == "__main__": main()
