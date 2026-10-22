"""Reviewed chat comparisons on supplied BID/ASK prices, using the existing SMA engine."""

from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from trading_ai.dukascopy_backtest import load_history, read_bounded, simulate
from trading_ai.dukascopy_history import save_json
from trading_ai.dukascopy_service import DukascopyResearch, dataset_id
from trading_ai.experiments import CRITERIA, expected_assessment
from trading_ai.market_history import PROFILE
from trading_ai.strategies import validate_crossover_windows
from trading_ai.tv_contracts import checksum, decimal_text, fields, number, safe_under, strict_json


REVISION = "conversation_price_proposal_v1"
RESULT = "conversation_price_result_v1"
FILES = ("conversation_prices.py", "dukascopy_backtest.py", "market_history.py", "dukascopy_history.py",
         "dukascopy.py", "indicators.py", "strategies.py", "tv_contracts.py")


def catalog(root):
    value = DukascopyResearch(root).overview()
    return {"datasets": [item for item in value["datasets"] if item.get("start_date")],
            "supported_strategies": ["sma"], "pair": "EUR/USD", "metadata_only": True,
            "warnings": value["warnings"]}


def load_source(root, identity):
    directory = safe_under(Path(root).resolve(), ".local", "dukascopy", dataset_id(identity))
    daily, provenance, manifest_raw, daily_raw = load_history(directory)
    manifest = strict_json(manifest_raw)
    if manifest.get("profile") != PROFILE:
        raise ValueError("El chat BID/ASK requiere un histórico aportado con fechas UTC explícitas.")
    info = {"id": identity, "sha256": provenance["manifest_sha256"], "source": provenance,
        "first_date": manifest["start_date"], "end_date_exclusive": manifest["end_date_exclusive"],
        "daily_sessions": len(daily["sessions"]), "internal_gap_count": manifest["internal_gap_count"],
        "coverage_gap_count": manifest["coverage_gap_count"], "session_policy": daily["session_policy"]}
    return info, daily, manifest_raw, daily_raw


def sma(value):
    fields(value, ("strategy", "fast_window", "slow_window"), "cruce BID/ASK")
    if value["strategy"] != "sma":
        raise ValueError("Los históricos BID/ASK del chat admiten SMA; EMA sigue disponible con BCE. No se convierte la estrategia.")
    validate_crossover_windows(value["fast_window"], value["slow_window"])
    if value["fast_window"] > 120 or value["slow_window"] > 252:
        raise ValueError("Ventanas fuera de límites: rápida hasta 120 y lenta hasta 252.")
    return dict(value)


def prepare(root, body, engine_hashes):
    fields(body, ("request_id", "previous", "candidate", "baseline", "policy", "dataset", "source_sha256",
                  "criterion", "acknowledge_rules"), "revisión de precios")
    if body["acknowledge_rules"] is not True or body["criterion"] not in CRITERIA:
        raise ValueError("Revisa las reglas de precios y el criterio antes de guardar.")
    candidate = sma({key: body["candidate"][key] for key in ("strategy", "fast_window", "slow_window")})
    baseline = sma(body["baseline"])
    if candidate == baseline:
        raise ValueError("La variante debe ser distinta de la base.")
    fields(body["policy"], ("initial_capital", "quantity", "cost_rate"), "capital y costes BID/ASK")
    policy = {key: decimal_text(number(body["policy"][key], key, maximum=Decimal("0.1") if key == "cost_rate" else Decimal("1e9"),
                                       positive=key != "cost_rate")) for key in body["policy"]}
    info, daily, _, _ = load_source(root, body["dataset"])
    if info["sha256"] != body["source_sha256"]:
        raise ValueError("La fuente ha cambiado; recarga y revisa.")
    if info["internal_gap_count"] or info["coverage_gap_count"]:
        raise ValueError("El histórico tiene huecos bloqueantes; el chat no omite el control de calidad.")
    required = max(candidate["slow_window"], baseline["slow_window"])+2
    if len(daily["sessions"]) < required:
        raise ValueError(f"Histórico insuficiente: se necesitan {required} sesiones para ambos cruces y una apertura posterior.")
    return {"protocol": REVISION, "status": "ready_for_review", "candidate": dict(body["candidate"]),
        "proposal": {"hypothesis": body["candidate"]["hypothesis"], "criterion": body["criterion"],
                     "tool": "run_price_experiment", "arguments": candidate},
        "baseline": baseline, "policy": policy, "dataset": info["id"], "source": info,
        "selection": {"observations": len(daily["sessions"]), "sessions_sha256": daily["sessions_sha256"]},
        "rules": {"direction": "long_only", "pair": "EUR/USD", "session_policy": daily["session_policy"],
                  "signal": "utc_bid_close", "execution": "next_observed_session_first_hour_open",
                  "buy_quote": "ask", "sell_and_mark_quote": "bid", "forced_final_close": False,
                  "sizing": "fixed_eur_units", "slippage_and_swaps_modelled": False},
        "origin": "human_review", "previous": body["previous"], "engine_sha256": engine_hashes}


def check_source(root, data):
    source, daily, manifest_raw, daily_raw = load_source(root, data["dataset"])
    if source != data["source"]:
        raise ValueError("La fuente BID/ASK cambió; revisa una propuesta nueva.")
    return daily, manifest_raw, daily_raw


def identity(data):
    return checksum({"backend": "prices_bidask", "sessions_sha256": data["selection"]["sessions_sha256"],
        "candidate": data["proposal"]["arguments"], "baseline": data["baseline"], "policy": data["policy"],
        "rules": data["rules"], "engine_sha256": data["engine_sha256"]})


def metrics(value):
    summary, config = value["summary"], value["configuration"]
    return {"strategy": f'SMA{config["fast"]}/SMA{config["slow"]}', "quote_currency": "USD",
        "final_equity": summary["final_equity"], "return_percent": summary["return_percent"],
        "max_drawdown_percent": summary["max_observed_drawdown_percent"], "total_costs": summary["assumed_commissions"],
        "closed_trades": summary["closed_trades"], "has_open_position": Decimal(summary["open_quantity"]) > 0,
        "rejected_entries": len(value["rejected_orders"])}


def execute(root, data, prepared, session, job):
    daily, manifest_raw, daily_raw = check_source(root, data)
    calculations = {}
    for role, choice in (("baseline", data["baseline"]), ("candidate", data["proposal"]["arguments"])):
        calculations[role] = simulate(daily, capital=data["policy"]["initial_capital"], quantity=data["policy"]["quantity"],
            commission_rate=data["policy"]["cost_rate"], fast=choice["fast_window"], slow=choice["slow_window"])
        if calculations[role]["status"] != "simulated":
            raise ValueError("No se pueden publicar métricas de una comparación BID/ASK bloqueada.")
    source = data["source"]
    result = {"protocol": RESULT, "source": {"name": source["source"]["provider"], "sha256": sha256(daily_raw).hexdigest(),
        "first_date": daily["sessions"][0]["date"], "last_date": daily["sessions"][-1]["date"],
        "end_date_exclusive": source["end_date_exclusive"], "requested_start": source["first_date"],
        "observations": len(daily["sessions"]), "kind": "prices_bidask", "dataset": data["dataset"]},
        "original_source": source, "policy": data["policy"], "proposal": data["proposal"],
        "baseline": metrics(calculations["baseline"]), "candidate": metrics(calculations["candidate"]),
        "price_calculations": calculations, "conversation": session, "job": job,
        "revision_sha256": prepared["revision_sha256"], "engine_sha256": data["engine_sha256"],
        "accounting_processed": False, "external_orders_sent": False}
    result["assessment"] = expected_assessment(result)
    directory = safe_under(Path(root).resolve(), ".local", "chat-price-experiments", uuid4().hex)
    directory.mkdir(parents=True)
    for name, raw in (("input-manifest.json", manifest_raw), ("input-daily.json", daily_raw)):
        with (directory / name).open("xb") as stream:
            stream.write(raw)
    save_json(directory / "approval.json", prepared)
    save_json(directory / "results.json", result)
    return {"backend": "prices_bidask", "directory": directory.name, "sha256": sha256((directory / "results.json").read_bytes()).hexdigest(),
        "revision_sha256": prepared["revision_sha256"], "assessment": result["assessment"],
        "input_manifest_sha256": sha256(manifest_raw).hexdigest(), "input_daily_sha256": sha256(daily_raw).hexdigest(),
        "approval_sha256": sha256((directory / "approval.json").read_bytes()).hexdigest()}


def read_result(directory, saved):
    raw = read_bounded(safe_under(directory, "results.json"), 16 * 1024 * 1024)
    if sha256(raw).hexdigest() != saved["sha256"]:
        raise ValueError("Resultado alterado; no se usa como evidencia.")
    for name, key in (("input-manifest.json", "input_manifest_sha256"), ("input-daily.json", "input_daily_sha256"),
                      ("approval.json", "approval_sha256")):
        if sha256(read_bounded(safe_under(directory, name), 8 * 1024 * 1024)).hexdigest() != saved[key]:
            raise ValueError("La copia BID/ASK no coincide con la entrada del cálculo.")
    return strict_json(raw)
