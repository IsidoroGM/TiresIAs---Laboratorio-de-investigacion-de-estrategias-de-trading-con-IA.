"""Contratos versionados para intercambio de simulaciones; sin acceso a cuentas."""

from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from pathlib import Path

from trading_ai.data import SUPPORTED_PAIRS
from trading_ai.strategies import validate_crossover_windows


PROTOCOL = "tiresias_tradingview_contract_v1"
LEGACY_RENDERER = "tiresias_pine_crossover_v1"
RENDERER = "tiresias_pine_crossover_v2"
EXECUTION = {"direction": "long_only", "order_type": "market", "signal": "confirmed_close",
             "fill": "next_bar_open", "ema_seed": "sma", "warmup": "reset_at_start",
             "end": "stop_signals_keep_pending_and_open_position", "sizing": "fixed_base_units",
             "pyramiding": 0, "slippage_ticks": 0, "point_value": "1", "leverage": "1"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def checksum(value): return sha256(canonical(value)).hexdigest()


def strict_json(raw):
    if not isinstance(raw, (str, bytes)): raise ValueError("JSON textual requerido.")
    text = raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == '"': quoted = False
        elif char == '"': quoted = True
        elif char in "[{":
            depth += 1
            if depth > 64: raise ValueError("JSON demasiado profundo.")
        elif char in "]}": depth -= 1
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError("Campo JSON duplicado.")
            result[key] = value
        return result
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Número JSON no finito.")))
    except RecursionError as error: raise ValueError("JSON demasiado profundo.") from error


def fields(value, expected, name):
    if not isinstance(value, dict) or set(value) != set(expected): raise ValueError(f"Campos incompatibles en {name}.")


def number(value, name, *, minimum=Decimal("0"), maximum=Decimal("1e12"), positive=False):
    if not isinstance(value, str) or not 1 <= len(value) <= 64 or not re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", value):
        raise ValueError(f"{name}: se requiere un decimal textual acotado.")
    try: decimal = Decimal(value)
    except InvalidOperation as error: raise ValueError(f"{name}: decimal inválido.") from error
    if not decimal.is_finite() or not minimum <= decimal <= maximum or positive and decimal == 0:
        raise ValueError(f"{name}: valor fuera de límites.")
    if abs(decimal.as_tuple().exponent) > 28: raise ValueError(f"{name}: precisión excesiva.")
    return decimal


def decimal_text(value):
    # format(f) conserva el significado sin depender del contexto Decimal global.
    if value == 0: return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,3})?(?:Z|[+-][0-9]{2}:[0-9]{2})", value): raise ValueError("Instante ISO-8601 con segundos, zona y hasta milisegundos requerido.")
    try: parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error: raise ValueError("Instante ISO-8601 inválido.") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None: raise ValueError("El instante necesita zona horaria explícita.")
    if parsed.microsecond % 1000: raise ValueError("El contrato admite precisión hasta milisegundos, sin recortes silenciosos.")
    return parsed.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def milliseconds(value):
    delta = datetime.fromisoformat(instant(value).replace("Z", "+00:00")) - datetime(1970, 1, 1, tzinfo=UTC)
    return delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000


def hash_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value): raise ValueError("Huella SHA-256 inválida.")
    return value


def label(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", value): raise ValueError("Identificador de cuenta inválido.")
    return value


def safe_under(root, *parts):
    root = Path(root).resolve()
    target = root.joinpath(*parts)
    if not target.is_relative_to(root): raise ValueError("Ruta fuera del espacio local.")
    current = root
    for part in target.relative_to(root).parts:
        current /= part
        if current.is_symlink() or current.is_junction(): raise ValueError("No se admiten enlaces en el almacenamiento de simulación.")
    if not target.resolve().is_relative_to(root): raise ValueError("Ruta fuera del espacio local.")
    return target


def make_contract(*, strategy="sma", fast=20, slow=60, pair="EUR/USD", ticker="OANDA:EURUSD",
                  start="2024-01-01T00:00:00Z", end="2027-01-01T00:00:00Z", account="virtual-eurusd",
                  capital="1000", quantity="1", cost_rate="0.001"):
    value = {"protocol": PROTOCOL, "renderer": RENDERER,
             "strategy": {"kind": strategy, "fast": fast, "slow": slow},
             "market": {"pair": pair, "ticker": ticker, "timeframe": "1D", "timezone": "Etc/UTC", "chart": "standard", "quote_currency": pair.split("/")[-1]},
             "period": {"start": start, "end": end},
             "account": {"id": account, "currency": pair.split("/")[-1], "initial_capital": capital, "quantity": quantity, "cost_rate": cost_rate},
             "execution": deepcopy(EXECUTION)}
    return validate_contract(value)


def validate_contract(value):
    fields(value, ("protocol", "renderer", "strategy", "market", "period", "account", "execution"), "contrato")
    if value["protocol"] != PROTOCOL or value["renderer"] not in (LEGACY_RENDERER, RENDERER) or canonical(value["execution"]) != canonical(EXECUTION): raise ValueError("Versión o política de ejecución no admitida.")
    strategy, market, period, account = (value[key] for key in ("strategy", "market", "period", "account"))
    fields(strategy, ("kind", "fast", "slow"), "estrategia")
    if strategy["kind"] not in ("sma", "ema"): raise ValueError("Solo SMA/EMA largas.")
    validate_crossover_windows(strategy["fast"], strategy["slow"])
    if strategy["fast"] > 120 or strategy["slow"] > 252: raise ValueError("Ventanas excesivas.")
    fields(market, ("pair", "ticker", "timeframe", "timezone", "chart", "quote_currency"), "mercado")
    if market["pair"] not in SUPPORTED_PAIRS or market["quote_currency"] != market["pair"].split("/")[1]: raise ValueError("Par o moneda incompatible.")
    if not isinstance(market["ticker"], str) or not re.fullmatch(r"[A-Z0-9_]{1,24}:[A-Z0-9_.]{1,32}", market["ticker"]): raise ValueError("Símbolo y proveedor explícitos requeridos.")
    if (market["timeframe"], market["timezone"], market["chart"]) != ("1D", "Etc/UTC", "standard"): raise ValueError("Se requiere gráfico estándar diario y tiempos UTC.")
    fields(period, ("start", "end"), "período")
    first, last = instant(period["start"]), instant(period["end"])
    if not first < last or milliseconds(last) - milliseconds(first) > 3660 * 86400000: raise ValueError("Período inválido o mayor de diez años.")
    fields(account, ("id", "currency", "initial_capital", "quantity", "cost_rate"), "cuenta")
    label(account["id"])
    if account["currency"] != market["quote_currency"]: raise ValueError("La cuenta debe estar en moneda cotizada, sin conversión implícita.")
    capital = number(account["initial_capital"], "capital", maximum=Decimal("1e9"), positive=True)
    quantity = number(account["quantity"], "cantidad", maximum=Decimal("1e9"), positive=True)
    cost = number(account["cost_rate"], "coste", maximum=Decimal("0.1"))
    result = deepcopy(value)
    result["period"] = {"start": first, "end": last}
    result["account"].update(initial_capital=decimal_text(capital), quantity=decimal_text(quantity), cost_rate=decimal_text(cost))
    return result


def validate_fill(value, contract):
    fields(value, ("protocol", "contract_sha256", "execution_id", "sequence", "side", "quantity", "price", "fee", "currency", "signal_at", "executed_at"), "ejecución")
    contract = validate_contract(contract)
    if value["protocol"] != "tiresias_simulated_fill_v1" or value["contract_sha256"] != checksum(contract): raise ValueError("Ejecución de contrato desconocido.")
    if not isinstance(value["execution_id"], str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value["execution_id"]): raise ValueError("Identidad de ejecución inválida.")
    if type(value["sequence"]) is not int or not 1 <= value["sequence"] <= 1000000: raise ValueError("Secuencia inválida.")
    if value["side"] not in ("buy", "sell") or value["currency"] != contract["account"]["currency"]: raise ValueError("Acción o moneda incompatible.")
    quantity = number(value["quantity"], "cantidad", maximum=Decimal("1e9"), positive=True)
    price = number(value["price"], "precio", positive=True)
    fee = None if value["fee"] is None else decimal_text(number(value["fee"], "coste comunicado"))
    signal, executed = instant(value["signal_at"]), instant(value["executed_at"])
    if not contract["period"]["start"] <= signal < contract["period"]["end"] or executed < signal: raise ValueError("Instantes incompatibles con la señal y el contrato.")
    return {**deepcopy(value), "quantity": decimal_text(quantity), "price": decimal_text(price), "fee": fee, "signal_at": signal, "executed_at": executed}
