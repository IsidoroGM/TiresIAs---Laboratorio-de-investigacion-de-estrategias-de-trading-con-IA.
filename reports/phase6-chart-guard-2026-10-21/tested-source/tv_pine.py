"""Generación determinista de Pine v6. No compila ni publica en TradingView."""

from hashlib import sha256
import json
from pathlib import Path

from trading_ai.tv_contracts import LEGACY_RENDERER, canonical, checksum, decimal_text, milliseconds, validate_contract
from decimal import Context, Decimal, localcontext


def chart_guard(contract):
    """Mensajes accionables. No se relajan ni normalizan los requisitos del feed."""
    c = validate_contract(contract)
    ticker, quote = c["market"]["ticker"], c["account"]["currency"]
    if c["renderer"] == LEGACY_RENDERER:
        return (f'if syminfo.tickerid != "{ticker}" or timeframe.period != "1D" or not chart.is_standard or syminfo.currency != "{quote}" or syminfo.pointvalue != 1\n'
                '    runtime.error("Gráfico incompatible: revisar proveedor, símbolo, D1, moneda y valor por punto.")')
    return f'''string chartMismatch = ""
if syminfo.tickerid != "{ticker}"
    chartMismatch += "Simbolo/proveedor recibido: " + syminfo.tickerid + "; requerido: {ticker}.\\n"
if timeframe.period != "1D"
    chartMismatch += "Temporalidad recibida: " + timeframe.period + "; requerida: 1D (un dia, no un minuto).\\n"
if not chart.is_standard
    chartMismatch += "Tipo de grafico: no estandar; se requieren velas o barras estandar.\\n"
if syminfo.currency != "{quote}"
    chartMismatch += "Moneda recibida: " + syminfo.currency + "; requerida: {quote}.\\n"
if syminfo.pointvalue != 1
    chartMismatch += "Valor por punto recibido: " + str.tostring(syminfo.pointvalue) + "; requerido: 1. Revisar unidades del simbolo.\\n"
if str.length(chartMismatch) > 0
    runtime.error("TiresIAs: configuracion del grafico incompatible.\\n" + chartMismatch)'''


def render(contract):
    c = validate_contract(contract)
    identity = checksum(c)
    strategy, market, account = c["strategy"], c["market"], c["account"]
    with localcontext(Context(prec=28)): commission = decimal_text(Decimal(account["cost_rate"]) * 100)
    quote = account["currency"]
    # No se interpola texto libre: el contrato limita símbolos, identificadores y
    # números. La configuración es constante; modificar Properties requiere otra versión.
    text = f'''//@version=6
// TiresIAs: borrador generado; compilación externa pendiente.
// Contrato SHA-256: {identity}
strategy("TiresIAs {strategy['kind'].upper()} {identity[:12]}", overlay=true, initial_capital={account['initial_capital']}, currency=currency.{quote}, default_qty_type=strategy.fixed, default_qty_value={account['quantity']}, pyramiding=0, commission_type=strategy.commission.percent, commission_value={commission}, slippage=0, margin_long=100, margin_short=100, calc_on_every_tick=false, calc_on_order_fills=false, process_orders_on_close=false, use_bar_magnifier=false)

const string CONTRACT = "{identity}"
const int START = {milliseconds(c['period']['start'])}
const int END = {milliseconds(c['period']['end'])}
const int FAST = {strategy['fast']}
const int SLOW = {strategy['slow']}
const float QUANTITY = {account['quantity']}

{chart_guard(c)}

// Semilla SMA, reiniciada al inicio del contrato; no se utiliza ta.ema.
var int observations = 0
var float sumFast = 0.0
var float sumSlow = 0.0
var float fast = na
var float slow = na
var int sequence = 0
var string activeEntry = ""
var string pendingMetadata = ""

if time >= START
    observations += 1
    if observations <= FAST
        sumFast += close
    if observations <= SLOW
        sumSlow += close
    if observations == FAST
        fast := sumFast / FAST
    else if observations > FAST
        fast := {('fast + (2.0 / (FAST + 1)) * (close - fast)' if strategy['kind']=='ema' else '(fast * FAST + close - close[FAST]) / FAST')}
    if observations == SLOW
        slow := sumSlow / SLOW
    else if observations > SLOW
        slow := {('slow + (2.0 / (SLOW + 1)) * (close - slow)' if strategy['kind']=='ema' else '(slow * SLOW + close - close[SLOW]) / SLOW')}

bool up = not na(fast[1]) and not na(slow[1]) and fast[1] <= slow[1] and fast > slow
bool down = not na(fast[1]) and not na(slow[1]) and fast[1] >= slow[1] and fast < slow
bool eligible = barstate.isconfirmed and time >= START and time_close < END

// Los mensajes incluyen metadatos; precio/cantidad de ejecución deben proceder
// de placeholders de order-fill en el diálogo de alerta, nunca de la señal.
metadata(int seq, string key, int signalTime) =>
    '{{"sequence":' + str.tostring(seq) + ',"execution_id":"' + key + '","signal_time_ms":' + str.tostring(signalTime) + '}}'

if eligible and up and strategy.position_size == 0
    sequence += 1
    string key = "TI-B-" + str.tostring(time_close)
    activeEntry := key
    pendingMetadata := metadata(sequence, key, time_close)
    strategy.entry(activeEntry, strategy.long, qty=QUANTITY, comment=key, alert_message=pendingMetadata)
if eligible and down and strategy.position_size > 0
    sequence += 1
    string key = "TI-S-" + str.tostring(time_close)
    pendingMetadata := metadata(sequence, key, time_close)
    strategy.close(activeEntry, comment=key, alert_message=pendingMetadata)

plot(fast, "TiresIAs fast", color=color.teal)
plot(slow, "TiresIAs slow", color=color.orange)
plot(up ? 1 : down ? -1 : 0, "TiresIAs signal", display=display.data_window)
plot(observations, "TiresIAs observations", display=display.data_window)
'''
    return text


def alert_template(contract):
    c = validate_contract(contract)
    # Sustituir order_meta como JSON, no dentro de comillas. TradingView no permite
    # anidar placeholders en alert_message; la plantilla pertenece al diálogo.
    return ('{"protocol":"tiresias_pine_fill_v1","contract_sha256":"' + checksum(c)
            + '","ticker":"{{exchange}}:{{ticker}}","timeframe":"1D",'
            '"side":"{{strategy.order.action}}","quantity":"{{strategy.order.contracts}}",'
            '"price":"{{strategy.order.price}}","executed_at":"{{time}}",'
            '"execution_time_basis":"bar_open_by_contract","alert_fired_at":"{{timenow}}",'
            '"currency":"' + c["account"]["currency"] + '","order_meta":{{strategy.order.alert_message}}}')


def write_bundle(directory, contract):
    directory = Path(directory)
    c = validate_contract(contract)
    directory.mkdir(parents=True, exist_ok=False)
    files = {"contract.json": canonical(c), "strategy.pine": render(c).encode("utf-8"),
             "alert-message.json.txt": alert_template(c).encode("utf-8")}
    for name, raw in files.items(): (directory / name).write_bytes(raw)
    manifest = {"protocol": "tiresias_pine_bundle_v1", "contract_sha256": checksum(c),
                "files_sha256": {name: sha256(raw).hexdigest() for name, raw in files.items()},
                "pine_compiled": False, "chart_verified": False, "external_connection": False}
    (directory / "manifest.json").write_bytes(canonical(manifest))
    return manifest


def verify_bundle(directory):
    from trading_ai.tv_contracts import fields, strict_json
    directory = Path(directory)
    manifest = strict_json((directory / "manifest.json").read_bytes())
    fields(manifest, ("protocol", "contract_sha256", "files_sha256", "pine_compiled", "chart_verified", "external_connection"), "manifiesto Pine")
    if any(manifest[name] is not False for name in ("pine_compiled", "chart_verified", "external_connection")): raise ValueError("Un paquete generado no acredita una comprobación externa.")
    expected = {"contract.json", "strategy.pine", "alert-message.json.txt"}
    if manifest.get("protocol") != "tiresias_pine_bundle_v1" or set(manifest.get("files_sha256", {})) != expected: raise ValueError("Paquete Pine incompatible.")
    for name, expected_hash in manifest["files_sha256"].items():
        if sha256((directory / name).read_bytes()).hexdigest() != expected_hash: raise ValueError("Paquete Pine alterado.")
    contract = validate_contract(strict_json((directory / "contract.json").read_bytes()))
    if manifest["contract_sha256"] != checksum(contract) or (directory / "strategy.pine").read_bytes() != render(contract).encode("utf-8"):
        raise ValueError("El script no corresponde al contrato y generador conocidos.")
    if (directory / "alert-message.json.txt").read_bytes() != alert_template(contract).encode("utf-8"): raise ValueError("Plantilla de alerta alterada.")
    return contract
