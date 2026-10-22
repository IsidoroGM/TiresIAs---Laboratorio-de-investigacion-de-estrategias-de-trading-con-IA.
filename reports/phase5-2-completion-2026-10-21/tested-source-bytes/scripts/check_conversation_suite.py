"""Comprobación reproducible de FASE 5.2 con temporales exclusivos por proceso."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import uuid4
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "reports/phase5-2-completion-2026-10-21"
FILES = ["tests/test_conversation.py", "tests/test_lab.py", "tests/test_lab_performance.py",
         "tests/test_ai.py", "tests/test_backtesting.py", "tests/test_research.py",
         "tests/test_evidence.py", "tests/test_campaign_ledger.py"]


def sources():
    paths = [path for folder in ("trading_ai", "tests", "scripts") for path in (ROOT / folder).rglob("*")
             if path.is_file() and path.suffix in (".py", ".js", ".html", ".css", ".ps1")]
    paths.append(ROOT / "pytest.ini")
    return {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def command(*args):
    temporary = Path(tempfile.gettempdir()) / ("trading-ai-codex-" + uuid4().hex)
    assert not temporary.exists()
    return [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(temporary), *args]


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    before = sources()
    collected = subprocess.run(command("--collect-only"), cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (OUTPUT / "collection.log").write_text(collected.stdout + collected.stderr, encoding="utf-8")
    if collected.returncode: raise ValueError("Falló la colección completa.")
    nodes = sorted(line.strip().replace("\\", "/") for line in collected.stdout.splitlines() if line.startswith("tests") and "::" in line)
    old = json.loads((ROOT / "reports/phase5-completion-2026-10-20/suite-manifest.json").read_text(encoding="utf-8"))["nodes"]
    assert set(old) <= set(nodes)
    assert all(node.startswith(("tests/test_conversation.py::", "tests/test_lab_performance.py::")) for node in set(nodes) - set(old))
    with (OUTPUT / "suite.log").open("w", encoding="utf-8") as log:
        print("Pruebas de conversación, consulta, proveedor, cálculos, evidencias y registro...", flush=True)
        run = subprocess.run(command("--junitxml", str(OUTPUT / "suite.xml"), *FILES), cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    suite = ET.parse(OUTPUT / "suite.xml").getroot().find("testsuite")
    stable = before == sources()
    result = {"collected": len(nodes), "previous_phase5_nodes_preserved": len(old),
              "phase5_1_nodes": sum(node.startswith("tests/test_lab_performance.py::") for node in nodes),
              "phase5_2_nodes": sum(node.startswith("tests/test_conversation.py::") for node in nodes),
              "tested_files": FILES, "selected_suite": suite.attrib, "returncode": run.returncode,
              "source_bytes_stable": stable, "source_sha256": before, "full_suite_executed": False,
              "cache": False, "temporary_policy": "new_guid_per_process"}
    (OUTPUT / "suite-manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "source_sha256"}, ensure_ascii=False), flush=True)
    assert run.returncode == 0 and stable and suite.get("failures") == suite.get("errors") == suite.get("skipped") == "0"


if __name__ == "__main__": main()
