"""Divide la colección exacta en tres procesos pytest aislados; no instala nada."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import uuid4

root = Path.cwd()
temporary = Path(tempfile.gettempdir()) / ("trading-ai-codex-" + uuid4().hex)
result = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "--basetemp", str(temporary)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
if result.returncode: raise ValueError(result.stdout + result.stderr)
nodes = sorted(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip().replace("\\", "/").startswith("tests/") and "::" in line)
if not nodes or len(nodes) != len(set(nodes)): raise ValueError("Colección vacía o duplicada.")
files = sorted({node.split("::")[0] for node in nodes})
weights = {"test_campaign_execution.py": 741, "test_campaign_experiment.py": 271,
           "test_campaign_memory.py": 210, "test_campaign_memory_integration.py": 177,
           "test_campaign_review.py": 88, "test_campaign_permission.py": 130,
           "test_campaign_controller.py": 100, "test_campaign_cycle.py": 90, "test_campaign_cycle_integration.py": 70}
def weight(file):
    name = Path(file).name
    if name in weights: return weights[name]
    return 45 if any(word in name for word in ("compact", "guided", "coverage", "cache")) else 20 if "structured" in name else 3
groups = [{"files": [], "estimated_weight": 0} for _ in range(3)]
for file in sorted(files, key=lambda item: (-weight(item), item)):
    group = min(groups, key=lambda item: item["estimated_weight"])
    group["files"].append(file)
    group["estimated_weight"] += weight(file)
for group in groups:
    group["files"].sort()
    group["expected_nodes"] = [node for node in nodes if node.split("::")[0] in group["files"]]
sources = {str(path.relative_to(root)).replace("\\", "/"): sha256(path.read_bytes()).hexdigest()
           for directory in ("trading_ai", "tests") for path in (root / directory).glob("*.py")}
manifest = {"schema_version": 1, "collected_test_count": len(nodes), "all_nodes": nodes,
            "groups": groups, "source_sha256": sources, "pytest_cache": False, "temporary_policy": "exclusive_guid_per_process"}
output = root / ".local/phase4-suite-manifest.json"
with output.open("x", encoding="utf-8") as stream: json.dump(manifest, stream, ensure_ascii=False, indent=2)
print(json.dumps({"collected": len(nodes), "files": len(files), "groups": [{"files": len(group["files"]), "tests": len(group["expected_nodes"]), "weight": group["estimated_weight"]} for group in groups]}))
