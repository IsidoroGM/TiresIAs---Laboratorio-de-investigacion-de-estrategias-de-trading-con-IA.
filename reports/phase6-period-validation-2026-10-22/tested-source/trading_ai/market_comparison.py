"""Compare stored historical runs without recalculating signals or combining accounts."""

from hashlib import sha256
from pathlib import Path
import re

from trading_ai.dukascopy_backtest import PROTOCOL as RUN_PROTOCOL, read_bounded
from trading_ai.dukascopy_history import save_json
from trading_ai.market_history import PROFILE as HISTORY_PROFILE, selection
from trading_ai.tv_contracts import canonical, checksum, safe_under, strict_json


PROTOCOL = "tiresias_independent_period_comparison_v1"
FILES = (("simulation.json", 8 * 1024 * 1024), ("input-manifest.json", 256 * 1024),
         ("input-daily.json", 8 * 1024 * 1024))


def record(raws, identity):
    try:
        return _record(raws, identity)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Estructura del resultado o de sus entradas inválida.") from error


def _record(raws, identity):
    result, manifest, daily = (strict_json(raw) for raw in raws)
    if (not isinstance(result, dict) or result.get("protocol") != RUN_PROTOCOL
            or result.get("result_sha256") != checksum({key: value for key, value in result.items() if key != "result_sha256"})):
        raise ValueError("El resultado guardado no coincide con su huella.")
    source = result["source"]
    if (sha256(raws[1]).hexdigest() != source["manifest_sha256"]
            or sha256(raws[2]).hexdigest() != source["daily_file_sha256"]):
        raise ValueError("Las copias de entrada no coinciden con el resultado.")
    if not isinstance(manifest, dict) or manifest.get("profile") != HISTORY_PROFILE:
        raise ValueError("La comparación requiere históricos aportados con fechas UTC explícitas.")
    selection(manifest["start_date"], manifest["end_date_exclusive"])
    if (not isinstance(daily, dict) or daily.get("sessions_sha256") != checksum(daily.get("sessions"))
            or daily["sessions_sha256"] != result["sessions_sha256"]
            or manifest["sessions_sha256"] != result["sessions_sha256"]
            or len(daily["sessions"]) != result["daily_sessions"]
            or manifest["daily_sessions"] != result["daily_sessions"]
            or any(source.get(key) != manifest.get(key) for key in
                   ("start_date", "end_date_exclusive", "provider", "source_format"))):
        raise ValueError("Sesiones o procedencia incompatibles con el resultado.")
    status = result.get("status")
    expected_status = ("blocked_coverage_gaps" if daily.get("blocking_gaps") else
                       "blocked_internal_gaps" if any(day["internal_gaps"] for day in daily["sessions"]) else
                       "insufficient_history" if len(daily["sessions"]) < result["configuration"]["slow"] + 1 else "simulated")
    if (status not in ("simulated", "blocked_internal_gaps", "blocked_coverage_gaps", "insufficient_history")
            or status != expected_status
            or (status == "simulated") != isinstance(result.get("summary"), dict)
            or status != "simulated" and (result["hypothetical_fills"] or result["equity_curve"])):
        raise ValueError("Estado o métricas de resultado incompatibles.")
    return {"raws": raws, "identity": identity, "result": result, "manifest": manifest, "daily": daily}


def read_run(directory):
    directory = Path(directory)
    if not re.fullmatch(r"[0-9a-f]{32}", directory.name):
        raise ValueError("Identificador de cálculo inválido.")
    directory = safe_under(directory.parent.resolve(), directory.name)
    return record([read_bounded(safe_under(directory, name), maximum) for name, maximum in FILES], directory.name)


def build(records):
    first, second = sorted(records, key=lambda item: item["manifest"]["start_date"])
    left, right = first["result"], second["result"]
    if canonical(left["configuration"]) != canonical(right["configuration"]):
        raise ValueError("La comparación requiere la misma estrategia, capital, cantidad y costes.")
    if left["implementation_sha256"] != right["implementation_sha256"]:
        raise ValueError("Los cálculos usan versiones distintas del motor.")
    if any(first["manifest"].get(key) != second["manifest"].get(key)
           for key in ("provider", "source_format", "pair", "timezone", "interval", "identity_basis", "claimed_upstream")):
        raise ValueError("La comparación requiere el mismo mercado y procedencia declarada.")
    if first["daily"]["session_policy"] != second["daily"]["session_policy"]:
        raise ValueError("Las políticas de sesión son distintas.")
    if first["manifest"]["end_date_exclusive"] > second["manifest"]["start_date"]:
        raise ValueError("Los períodos deben ser distintos y no solaparse.")
    periods, inputs = [], []
    for index, item in enumerate((first, second)):
        r, m = item["result"], item["manifest"]
        periods.append({"run_id": item["identity"], "result_sha256": r["result_sha256"],
            "start_date": m["start_date"], "end_date_exclusive": m["end_date_exclusive"],
            "daily_sessions": r["daily_sessions"], "selected_hours": m["selected_hours"],
            "internal_gap_count": m["internal_gap_count"], "coverage_gap_count": m["coverage_gap_count"],
            "status": r["status"], "hypothetical_fills": len(r["hypothetical_fills"]),
            "rejected_orders": len(r["rejected_orders"]), "pending_order": r["pending_order"],
            "summary": r["summary"], "attribution": m["attribution"]})
        inputs.append({"run_id": item["identity"], "files": [
            {"file": f"run-{index}-{name}", "sha256": sha256(raw).hexdigest()}
            for (name, _), raw in zip(FILES, item["raws"], strict=True)]})
    result = {"protocol": PROTOCOL, "status": "compared" if all(p["status"] == "simulated" for p in periods) else "incomplete",
        "configuration": left["configuration"], "implementation_sha256": left["implementation_sha256"],
        "provider": first["manifest"]["provider"], "session_policy": first["daily"]["session_policy"],
        "periods": periods, "inputs": inputs, "independent_periods": True, "balances_combined": False,
        "prospective_validation": False, "parameter_selection": False, "strategy_recalculated_on_read": False,
        "accounting_processed": False, "external_orders_sent": False}
    return {**result, "comparison_sha256": checksum(result)}


def create_comparison(*, left, right, output):
    output = Path(output)
    output = safe_under(output.parent.resolve(), output.name)
    if output.exists():
        raise ValueError("La salida ya existe; utilizar un directorio nuevo.")
    records = sorted((read_run(left), read_run(right)), key=lambda item: item["manifest"]["start_date"])
    comparison = build(records)
    output.mkdir(parents=True)
    for index, item in enumerate(records):
        for (name, _), raw in zip(FILES, item["raws"], strict=True):
            with (output / f"run-{index}-{name}").open("xb") as stream:
                stream.write(raw)
    save_json(output / "comparison.json", comparison)
    return comparison


def validate_snapshot(stored):
    if (not isinstance(stored, dict) or stored.get("protocol") != PROTOCOL
            or stored.get("comparison_sha256") != checksum({key: value for key, value in stored.items() if key != "comparison_sha256"})
            or not isinstance(stored.get("periods"), list) or len(stored["periods"]) != 2):
        raise ValueError("La comparación guardada no coincide con su huella.")


def load_comparison(directory):
    directory = Path(directory)
    directory = safe_under(directory.parent.resolve(), directory.name)
    stored = strict_json(read_bounded(safe_under(directory, "comparison.json"), 256 * 1024))
    validate_snapshot(stored)
    if not isinstance(stored, dict) or stored.get("protocol") != PROTOCOL or not isinstance(stored.get("inputs"), list) or len(stored["inputs"]) != 2:
        raise ValueError("Comparación guardada inválida.")
    records = []
    for index, item in enumerate(stored["inputs"]):
        identity = item.get("run_id") if isinstance(item, dict) else None
        if not isinstance(identity, str) or not re.fullmatch(r"[0-9a-f]{32}", identity):
            raise ValueError("Identificador de cálculo inválido.")
        raws = [read_bounded(safe_under(directory, f"run-{index}-{name}"), maximum) for name, maximum in FILES]
        records.append(record(raws, identity))
    expected = build(records)
    if canonical(stored) != canonical(expected):
        raise ValueError("La comparación no coincide con sus resultados conservados.")
    return stored
