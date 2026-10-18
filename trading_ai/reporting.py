"""Informe Markdown reproducible del laboratorio SMA20/SMA60, sin acceso a red."""

from decimal import Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path

from trading_ai.backtesting import run_backtest, validate_cost_rate, validate_initial_capital, validate_allocation_fraction
from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates
from trading_ai.indicators import simple_moving_average
from trading_ai.metrics import calculate_metrics
from trading_ai.strategies import sma_crossover_signals


def _number(value: Decimal | None, places: int = 6) -> str:
    return "N/D" if value is None else f"{value:.{places}f}"


def build_report(path: str | Path, *, cost_rate: Decimal = Decimal("0"),
                 initial_capital: Decimal = Decimal("1000"),
                 allocation_fraction: Decimal | None = None) -> str:
    """Calcula los cuatro pares y devuelve Markdown; no escribe ni cambia datos."""
    validate_cost_rate(cost_rate)
    validate_initial_capital(initial_capital)
    validate_allocation_fraction(allocation_fraction)
    with localcontext(Context(prec=28)):
        cost_percent = format(cost_rate * 100, 'f')
        allocation_percent = format(allocation_fraction * 100, 'f') if allocation_fraction is not None else None
    sizing_rule = ("Una unidad base fija por entrada" if allocation_percent is None else
                   f"{allocation_percent} % del efectivo disponible al ejecutar cada entrada, incluyendo su coste")
    allocation_option = f" --allocation-percent {allocation_percent}" if allocation_percent is not None else ""
    path = Path(path)
    checksum = sha256(path.read_bytes()).hexdigest()
    lines = [
        "# Trading AI — Informe educativo SMA20/SMA60", "",
        "Formato de informe: 4. Fuente: Banco Central Europeo (BCE).",
        "[Histórico oficial](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml).",
        f"SHA-256 de la copia analizada: `{checksum}`.", "",
        "## Reglas y supuestos", "",
        "- Referencias diarias informativas, no velas OHLC ni precios ejecutables.",
        "- EUR/USD directo; GBP/USD = USD/GBP, USD/JPY = JPY/USD y USD/CHF = CHF/USD",
        "  a partir de las referencias BCE de la misma fecha, todas expresadas por euro.",
        "- Medias de 20 y 60 observaciones publicadas, no días naturales.",
        "- Entrada: rápida pasa de <= lenta a > lenta. Salida: pasa de >= a <.",
        "- Sin señal si faltan medias actuales o anteriores; igualdad actual sin señal.",
        "- Ejecución simulada en la referencia de la observación siguiente.",
        "- Inicio sin posición; una sola compra abierta por par, sin cortos.",
        f"- Tamaño: {sizing_rule}.",
        "- Modo porcentual: presupuesto = efectivo × asignación; cantidad = presupuesto / (precio × (1 + tasa de coste)).",
        "- La cantidad se ajusta hacia abajo para no superar el presupuesto y no se rebalancea mientras está abierta.",
        "- Asignación es capital invertido, no pérdida máxima; no hay stop-loss ni restricciones de lotes de bróker.",
        "- Entradas estando dentro y salidas estando fuera se ignoran.",
        f"- Coste hipotético por compra o venta: {cost_percent} % del importe simulado.",
        "- Coste = precio de ejecución simulado × cantidad base × tasa; moneda cotizada.",
        "- No representa tarifas de un bróker. Con tasa 0 se mantienen costes cero.",
        f"- Capital inicial por cuenta independiente: {format(initial_capital, 'f')} unidades de su moneda cotizada.",
        "- Compra solo con saldo suficiente para precio más coste; sin margen ni financiación.",
        "- Entrada rechazada por falta de saldo no queda pendiente ni genera coste.",
        "- Última señal sin ejecución. Sin cierre forzado; posición abierta valorada a cada referencia.",
        "- Capital diario = efectivo + valor de la posición después de ejecutar la señal anterior.",
        "- Drawdown = máximo de capital alcanzado menos capital actual; porcentaje respecto a ese máximo.",
        "- Cálculos Decimal con 28 dígitos significativos; tablas redondeadas solo al mostrar.",
        "", "## Cobertura y cierres", "",
        "| Par | Inicio | Fin | Observaciones | Cierres | Ganadoras | Perdedoras | A cero | Abierta |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    results = []
    for pair in SUPPORTED_PAIRS:
        rates = load_ecb_rates(path, pair)
        values = [value for _, value in rates]
        signals = sma_crossover_signals(
            simple_moving_average(values, 20), simple_moving_average(values, 60)
        )
        result = run_backtest(rates, signals, pair, cost_rate=cost_rate, initial_capital=initial_capital,
                              allocation_fraction=allocation_fraction)
        metrics = calculate_metrics(result)
        results.append((result, metrics))
        lines.append(
            f"| {pair} | {rates[0][0]} | {rates[-1][0]} | {len(rates)} | "
            f"{metrics.total_trades} | {metrics.winning_trades} | {metrics.losing_trades} | "
            f"{metrics.breakeven_trades} | {'Sí' if metrics.has_open_position else 'No'} |"
        )
    lines += [
        "", "## Tamaño de las entradas ejecutadas", "",
        "Incluye las operaciones cerradas y la posición abierta; cantidades en moneda base.",
        "", "| Par | Moneda base | Cantidad mínima | Cantidad máxima |",
        "|---|---|---:|---:|",
    ]
    for result, metrics in results:
        quantities = [trade.position.quantity for trade in result.closed_trades]
        if result.open_position is not None:
            quantities.append(result.open_position.quantity)
        lines.append(f"| {result.pair} | {result.pair.split('/')[0]} | "
                     f"{_number(min(quantities, default=None))} | {_number(max(quantities, default=None))} |")
    lines += [
        "", "## Métricas de cierres — después de costes", "",
        "| Par | Moneda | % ganadoras | Resultado | Media/cierre | Ganancias | Pérdidas (magnitud) | Profit factor |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result, metrics in results:
        lines.append(
            f"| {result.pair} | {metrics.quote_currency} | {_number(metrics.win_rate_percent, 2)} | "
            f"{_number(metrics.total_pnl)} | {_number(metrics.average_pnl)} | "
            f"{_number(metrics.gross_profit)} | {_number(metrics.gross_loss)} | "
            f"{_number(metrics.profit_factor, 4)} |"
        )
    lines += [
        "", "N/D: porcentaje y media no disponibles sin cierres; profit factor no disponible",
        "sin pérdidas. Cierres a cero incluidos en el denominador del porcentaje ganador.",
        "Profit factor = ganancias / magnitud de pérdidas, ambas netas de costes de cierres.",
        "Importes en moneda cotizada. Ganadoras y perdedoras se clasifican después de costes.",
        "", "## Comparación de resultados y costes", "",
        "| Par | Moneda | Cierres antes de costes | Costes de cierres | Cierres después de costes | Costes incurridos totales | Resultado tras costes incurridos* |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result, metrics in results:
        lines.append(
            f"| {result.pair} | {result.quote_currency} | {_number(result.gross_realized_pnl)} | "
            f"{_number(result.closed_costs)} | {_number(result.realized_pnl)} | "
            f"{_number(result.total_costs)} | {_number(result.pnl_after_incurred_costs)} |"
        )
    lines += [
        "", "* Cierres netos menos el coste de entrada de la posición abierta, si existe.",
        "No incluye su variación de precio ni supone que se haya vendido. No es el patrimonio total.",
        "", "## Capital y drawdown (incluyen posiciones abiertas)", "",
        "| Par | Moneda | Capital inicial | Capital final | Drawdown máximo | Drawdown máximo % | Entradas rechazadas |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result, metrics in results:
        lines.append(
            f"| {result.pair} | {result.quote_currency} | {_number(result.initial_capital)} | "
            f"{_number(result.final_equity)} | {_number(result.max_drawdown)} | "
            f"{_number(result.max_drawdown_percent)} | {result.rejected_entries} |"
        )
    lines += [
        "", "Drawdowns positivos medidos en cada observación, incluyendo el capital inicial como máximo de partida.",
        "Los máximos absoluto y porcentual pueden corresponder a fechas distintas. No se miden caídas intradiarias.",
        "La exposición depende del modo de tamaño configurado; asignar el mismo porcentaje no iguala el riesgo.",
        "Un drawdown pequeño no demuestra que la estrategia sea segura con otro tamaño de posición.",
        "", "## Evolución del capital (resumen anual de la curva diaria)", "",
        "Última observación disponible de cada año; año final posiblemente incompleto.",
        "La curva diaria completa queda en BacktestResult.equity_curve; el drawdown usa todos sus puntos.",
        "", "| Par | Fecha | Efectivo | Valor posición | Capital | Moneda |",
        "|---|---|---:|---:|---:|---|",
    ]
    for result, metrics in results:
        yearly = {}
        for point in result.equity_curve:
            yearly[point.date.year] = point
        for point in yearly.values():
            lines.append(f"| {result.pair} | {point.date} | {_number(point.cash)} | "
                         f"{_number(point.position_value)} | {_number(point.equity)} | {result.quote_currency} |")
    lines += [
        "", "## Posiciones abiertas (excluidas de las métricas de cierres)", "",
    ]
    for result, metrics in results:
        position = result.open_position
        if position is None:
            lines.append(f"- {result.pair}: ninguna.")
        else:
            lines.append(
                f"- {result.pair}: {format(position.quantity, 'f')} {result.pair.split('/')[0]}; señal {position.entry_signal_date}; "
                f"entrada simulada {position.entry_date} a {_number(position.entry_price)} "
                f"{result.quote_currency} por unidad base. Coste de entrada ya incurrido: "
                f"{_number(position.entry_cost)} {result.quote_currency}. Variación de precio latente: "
                f"{_number(result.unrealized_pnl)} {result.quote_currency}, incluida en el capital final. "
                "El coste de entrada ya está descontado del efectivo; no se anticipa un coste de salida."
            )
    lines += [
        "", "## Limitaciones", "",
        "No sumar cuentas de monedas distintas ni comparar su exposición como si fueran equivalentes.",
        "El coste proporcional es hipotético: faltan spreads, comisiones, slippage y swaps reales,",
        "No se ajusta el precio simulado por liquidez; la valoración usa referencias informativas.",
        "No se ha contrastado el calendario completo de publicación ni rellenado fechas ausentes.",
        "Sin optimización ni validación fuera de muestra; estas métricas no demuestran viabilidad real.",
        "No hay órdenes reales ni conexión con un bróker. Informe educativo, sin recomendación de inversión.",
        "", "## Reproducción", "",
        f"Desde la raíz: `python -m trading_ai --report --cost-percent {cost_percent} --initial-capital {format(initial_capital, 'f')}{allocation_option} --data RUTA_XML --output RUTA_MD`.",
        "Usar la misma copia (SHA-256), código y reglas. El informe no incluye hora de ejecución",
        "ni rutas locales, para obtener el mismo contenido al repetir el cálculo.", "",
    ]
    if sha256(path.read_bytes()).hexdigest() != checksum:
        raise ValueError("El archivo de datos cambió durante el cálculo; repite con una copia estable.")
    return "\n".join(lines)


def write_report(source: str | Path, output: str | Path, *, cost_rate: Decimal = Decimal("0"),
                 initial_capital: Decimal = Decimal("1000"),
                 allocation_fraction: Decimal | None = None) -> Path:
    """Guarda un informe nuevo; admite repetir contenido idéntico, no sobrescribe otro."""
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError("La salida no puede ser el archivo de datos.")
    report = build_report(source, cost_rate=cost_rate, initial_capital=initial_capital,
                          allocation_fraction=allocation_fraction)
    if output.exists():
        if output.read_text(encoding="utf-8") == report:
            return output
        raise FileExistsError("La salida ya existe con otro contenido; elige otro --output.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(report)
    return output
