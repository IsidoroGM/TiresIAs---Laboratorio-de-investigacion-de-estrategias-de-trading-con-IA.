"""Medidas HTTP explícitas de consulta, sin cambiar fuentes o datos históricos."""

import argparse
from hashlib import sha256
import http.client
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import threading
import time
import types
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from trading_ai.lab import create_server

BASELINE = "47d2fc5158de4be2926ad683484d40eb2cee0984"
ROUTES = ("/api/home", "/api/experiments", "/api/consumption")


def factory(baseline):
    if not baseline: return create_server, None
    # Solo la versión conocida del cierre de FASE 5, leída de Git local.
    # Se cargan definiciones en este proceso temporal; ningún checkout se modifica.
    previous, sources = {}, {}
    try:
        for name in ("lab_catalog", "lab_query", "lab"):
            key = "trading_ai." + name
            previous[key] = sys.modules.get(key)
            path = "trading_ai/" + name + ".py"
            raw = subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT)
            sources[path] = sha256(raw).hexdigest()
            module = types.ModuleType(key)
            module.__file__ = str(ROOT / path)
            sys.modules[key] = module
            exec(compile(raw, str(ROOT / path), "exec"), module.__dict__)
        return module.create_server, sources
    finally:
        for key, module in previous.items():
            if module is None: sys.modules.pop(key, None)
            else: sys.modules[key] = module


def request(server, route):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=60)
    started = time.perf_counter()
    try:
        connection.request("GET", route)
        response = connection.getresponse()
        raw = response.read()
        elapsed = time.perf_counter() - started
        if response.status != 200: raise ValueError(f"HTTP {response.status}: {route}")
        return elapsed, json.loads(raw), len(raw)
    finally: connection.close()


def summary(values):
    return {"samples_s": values, "median_s": statistics.median(values),
            "p95_s": sorted(values)[math.ceil(.95 * len(values)) - 1],
            "min_s": min(values), "max_s": max(values)}


def benchmark(*, baseline, workers, samples):
    build, baseline_sources = factory(baseline)
    server = build(root=ROOT, port=0) if baseline else build(root=ROOT, port=0, workers=workers)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        initial, home, _ = request(server, "/api/home")
        values = {route: [] for route in ROUTES}
        for index in range(samples):
            for route in ROUTES:
                elapsed, value, size = request(server, route)
                values[route].append(elapsed)
            if not baseline: time.sleep(.15)  # Incluye comprobaciones periódicas del índice.
            if (index + 1) % 10 == 0:
                print(json.dumps({"baseline": baseline, "workers": workers, "samples_per_route": index + 1}), flush=True)
        rows = request(server, "/api/experiments")[1]["items"]
        detailed = {}
        for origin in ("local", "archive"):
            row = next(item for item in rows if item["origin"] == origin and item["kind"] == "walk-forward-runs")
            route = "/api/experiments/" + row["id"]
            runs = [request(server, route) for _ in range(3)]
            detailed[origin + "_detail"] = summary([value[0] for value in runs])
            detail = runs[-1][1]
            key = detail["accounts"][0]["id"]
            detailed[origin + "_account"] = summary([request(server, route + "/accounts/" + key)[0] for _ in range(3)])
            other = detail["accounts"][1]["id"]
            compare = "/api/compare?left=" + row["id"] + ":" + key + "&right=" + row["id"] + ":" + other
            detailed[origin + "_comparison"] = summary([request(server, compare)[0] for _ in range(3)])
        if not baseline:
            # Esperar la comprobación ya iniciada sin generar nuevas solicitudes.
            with server.service._condition:
                server.service._condition.wait_for(lambda: not server.service._refreshing, timeout=30)
            diagnostics = server.service.diagnostics()
        else: diagnostics = None
        result = {"baseline": baseline, "baseline_commit": BASELINE if baseline else None,
                  "baseline_sources_sha256": baseline_sources, "workers": 1 if baseline else workers,
                  "first_request_s": initial, "dataset": home["counts"],
                  "overview": {route: summary(v) for route, v in values.items()},
                  "detail": detailed, "cache": diagnostics}
    finally:
        server.shutdown(); server.server_close(); thread.join(5)
    result["temporary_server_closed"] = not thread.is_alive()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Archivo JSON nuevo; no se sobrescribe")
    parser.add_argument("--baseline-phase5", action="store_true")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--workers", type=int, nargs="+", default=[2, 4])
    args = parser.parse_args()
    if args.samples < 30: parser.error("Usa al menos 30 muestras para el p95.")
    if args.output.exists(): parser.error("La salida debe ser un archivo nuevo.")
    files = [path for directory in ("trading_ai", "tests") for path in (ROOT / directory).rglob("*")
             if path.is_file() and path.suffix in (".py", ".js", ".css", ".html")]
    hashes = {p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()).hexdigest() for p in files}
    results = [benchmark(baseline=args.baseline_phase5, workers=workers, samples=args.samples)
               for workers in ([1] if args.baseline_phase5 else args.workers)]
    # La referencia usa los tres módulos antiguos y el motor previo, conservado.
    # Cambios en archivos nuevos de FASE 5.1 no modifican esa referencia histórica.
    stable = all(sha256((ROOT / p).read_bytes()).hexdigest() == digest for p, digest in hashes.items())
    report = {"measured_at": datetime.now(timezone.utc).isoformat(), "method": {
        "samples_per_overview": args.samples, "p95": "nearest_rank", "filesystem_cache": "not_controlled",
        "first_request": "first HTTP query in a new server instance, not a cold filesystem cache",
        "scope": "loopback HTTP and response body; browser rendering measured separately",
        "reference": "server, query and catalog from phase5 Git commit; historical engine unchanged"},
        "source_sha256_at_start": hashes, "current_sources_unchanged_during_measurement": stable, "runs": results}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2); stream.write("\n")
    print(json.dumps({"output": str(args.output), "sources_stable": stable,
                      "median_ms": [{route: round(run["overview"][route]["median_s"] * 1000, 2) for route in ROUTES} for run in results]}), flush=True)
    if not stable and not args.baseline_phase5: raise SystemExit("Las fuentes cambiaron durante la medición.")


if __name__ == "__main__": main()
