"""Colección completa, tres procesos aislados, cotejo exacto y fuentes estables."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import uuid4
import xml.etree.ElementTree as ET

ROOT = Path.cwd()
OUTPUT = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else Path(__file__).resolve().parent


def temporary():
    path = Path(tempfile.gettempdir()) / ("trading-ai-codex-" + uuid4().hex)
    if path.exists(): raise ValueError("El temporal debe ser nuevo y exclusivo.")
    return str(path)


def sources():
    paths = [path for directory in ("trading_ai", "tests") for path in (ROOT / directory).rglob("*")
             if path.is_file() and path.suffix in (".py", ".js", ".css", ".html")]
    paths.append(ROOT / "scripts/check_lab_readonly.py")
    return {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


before = sources()
result = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "--basetemp", temporary()],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
if result.returncode: raise ValueError(result.stdout + result.stderr)
nodes = sorted(line.strip().replace("\\", "/") for line in result.stdout.splitlines()
               if line.strip().replace("\\", "/").startswith("tests/") and "::" in line)
if not nodes or len(nodes) != len(set(nodes)): raise ValueError("Colección vacía o duplicada.")
files = {node.split("::")[0] for node in nodes}
prior = json.loads((ROOT / "reports/phase4-completion-2026-10-20/checks/phase4-suite-manifest.json").read_text(encoding="utf-8"))
groups = [{"files": sorted(set(group["files"]) & files)} for group in prior["groups"]]
assigned = {file for group in groups for file in group["files"]}
for file in sorted(files - assigned):
    min(groups, key=lambda group: len(group["files"]))["files"].append(file)
manifest = {"collected": len(nodes), "nodes": nodes, "source_sha256": before, "groups": groups,
            "cache": False, "temporary_policy": "new_guid_per_process"}
with (OUTPUT / "suite-manifest.json").open("x", encoding="utf-8") as stream: json.dump(manifest, stream, ensure_ascii=False, indent=2)
running = []
for index, group in enumerate(groups, 1):
    path = OUTPUT / f"suite-{index}.xml"
    log = (OUTPUT / f"suite-{index}.log").open("x", encoding="utf-8")
    process = subprocess.Popen([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", temporary(),
                                "--junitxml", str(path), *sorted(group["files"])], stdout=log, stderr=subprocess.STDOUT)
    running.append((process, log, path))
    print(json.dumps({"partition": index, "tests": sum(node.split("::")[0] in group["files"] for node in nodes), "started": True}), flush=True)

results = []
actual = []
for index, (process, log, path) in enumerate(running, 1):
    status = process.wait()
    log.close()
    tree = ET.parse(path)
    suite = tree.find("testsuite")
    result = {"partition": index, "returncode": status, **suite.attrib}
    results.append(result)
    actual.extend((case.attrib["classname"], case.attrib["name"].replace("\\", "/")) for case in tree.iter("testcase"))
    print(json.dumps(result), flush=True)


def junit_key(node):
    file, *parts = node.split("::")
    return (".".join([file[:-3].replace("/", "."), *parts[:-1]]), parts[-1])


expected = [junit_key(node) for node in nodes]
if len(set(expected)) != len(expected): raise ValueError("Colisión en las identidades normalizadas.")
stable = before == sources()
matched = Counter(expected) == Counter(actual)
passed = all(result["returncode"] == 0 and all(int(result.get(field, 0)) == 0 for field in ("errors", "failures", "skipped")) for result in results)
summary = {"status": "passed" if passed and stable and matched else "failed", "collected": len(nodes),
           "sources_unchanged": stable, "source_files": len(before), "exact_collection_match": matched, "partitions": results}
with (OUTPUT / "suite-result.json").open("x", encoding="utf-8") as stream: json.dump(summary, stream, ensure_ascii=False, indent=2)
print(json.dumps(summary), flush=True)
if summary["status"] != "passed": sys.exit(1)
