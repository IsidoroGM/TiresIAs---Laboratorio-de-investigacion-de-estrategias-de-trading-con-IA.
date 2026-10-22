"""Sensibilidad local de SMA/EMA: escenarios fijos, sin búsqueda de parámetros."""

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path

from trading_ai.backtesting import (
    run_backtest, validate_allocation_fraction, validate_cost_rate, validate_initial_capital,
)
from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates
from trading_ai.reporting import _number, _save_report
from trading_ai.strategies import create_strategy, validate_crossover_windows


@dataclass(frozen=True)
class Scenario:
    name: str
    fast_window: int
    slow_window: int
    cost_rate: Decimal


def sensitivity_scenarios(fast_window: int, slow_window: int, cost_rate: Decimal
                          ) -> tuple[tuple[Scenario, ...], tuple[str, ...]]:
    """Base primero; variar un factor cada vez. Declarar escenarios inválidos omitidos."""
    validate_crossover_windows(fast_window, slow_window)
    validate_cost_rate(cost_rate)
    with localcontext(Context(prec=28)):
        candidates = (
            Scenario("Base", fast_window, slow_window, cost_rate),
            Scenario("Rápida -1", fast_window - 1, slow_window, cost_rate),
            Scenario("Rápida +1", fast_window + 1, slow_window, cost_rate),
            Scenario("Lenta -1", fast_window, slow_window - 1, cost_rate),
            Scenario("Lenta +1", fast_window, slow_window + 1, cost_rate),
            Scenario("Coste -0.05 pp", fast_window, slow_window, cost_rate - Decimal("0.0005")),
            Scenario("Coste +0.05 pp", fast_window, slow_window, cost_rate + Decimal("0.0005")),
        )
    valid, omitted = [], []
    for scenario in candidates:
        try:
            validate_crossover_windows(scenario.fast_window, scenario.slow_window)
            validate_cost_rate(scenario.cost_rate)
        except ValueError as error:
            omitted.append(f"{scenario.name}: {error}")
        else:
            valid.append(scenario)
    return tuple(valid), tuple(omitted)


def build_sensitivity_report(path: str | Path, *, cost_rate: Decimal = Decimal("0"),
                             initial_capital: Decimal = Decimal("1000"),
                             allocation_fraction: Decimal | None = None,
                             fast_window: int = 20, slow_window: int = 60) -> str:
    """Recalcula todos los escenarios; resume cambios frente a la base de cada cuenta."""
    scenarios, omitted = sensitivity_scenarios(fast_window, slow_window, cost_rate)
    validate_initial_capital(initial_capital)
    validate_allocation_fraction(allocation_fraction)
    path = Path(path)
    checksum = sha256(path.read_bytes()).hexdigest()
    with localcontext(Context(prec=28)):
        cost_percent = format(cost_rate * 100, "f")
        allocation_percent = (format(allocation_fraction * 100, "f")
                              if allocation_fraction is not None else None)
    allocation_option = f" --allocation-percent {allocation_percent}" if allocation_percent is not None else ""
    sizing = ("una unidad base fija" if allocation_percent is None else
              f"{allocation_percent} % del efectivo al entrar, costes incluidos")
    lines = [
        "# Trading AI — Sensibilidad local de SMA y EMA", "",
        "Formato de sensibilidad: 1. Fuente: Banco Central Europeo (BCE).",
        "[Histórico oficial](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml).",
        f"SHA-256 de la copia analizada: `{checksum}`.", "",
        "## Diseño del experimento", "",
        f"- Base: ventanas {fast_window}/{slow_window}; coste por compra o venta {cost_percent} %.",
        "- Se cambia un factor cada vez: rápida ±1, lenta ±1, coste ±0.05 puntos porcentuales (pp).",
        "  Por ejemplo, un coste base de 0.1 % pasa a 0.05 % o 0.15 %; no es un cambio relativo del 5 %.",
        "- Los escenarios inválidos se omiten explícitamente, sin recortar parámetros ni sustituirlos.",
        f"- Capital inicial por cuenta: {format(initial_capital, 'f')} en su moneda cotizada. Tamaño: {sizing}.",
        "- SMA: media de las últimas n observaciones. EMA: semilla SMA de las primeras n;",
        "  alfa = 2/(n+1); EMA actual = anterior + alfa × (precio - anterior).",
        "- Cruce alcista: rápida pasa de <= a > lenta; bajista: de >= a <. Sin medias completas no hay señal.",
        "- Cada escenario empieza sin posición desde la misma fecha; la primera señal posible es lenta+1.",
        "  Cambiar la ventana lenta también cambia el calentamiento; no se iguala artificialmente ese periodo.",
        "- Señal ejecutada en la referencia siguiente. Una compra abierta por par; sin cortos, margen ni cierre forzado.",
        "- Última señal sin ejecución. Cantidad fija hasta salir; solo compra con saldo para importe y coste.",
        "- Coste proporcional por cada compra/venta ejecutada. Capital y costes independientes en cada escenario.",
        "- Referencias BCE por euro: EUR/USD directo; GBP/USD = USD/GBP; USD/JPY = JPY/USD; USD/CHF = CHF/USD.",
        "- Mismas referencias y fechas para todos los escenarios de un par. Cálculos Decimal con 28 dígitos.",
        f"- Escenarios válidos por estrategia y par: {len(scenarios)}.", "",
        "Omisiones: " + ("ninguna." if not omitted else ""),
        *[f"- {reason}" for reason in omitted], "",
        "## Cobertura", "", "| Par | Inicio | Fin | Observaciones |", "|---|---|---|---:|",
    ]
    summaries, details = [], []
    for pair in SUPPORTED_PAIRS:
        rates = load_ecb_rates(path, pair)
        prices = [price for _, price in rates]
        lines.append(f"| {pair} | {rates[0][0]} | {rates[-1][0]} | {len(rates)} |")
        for name in ("sma", "ema"):
            details += ["", f"### {pair} — {name.upper()}", "",
                        "| Escenario | Rápida/lenta | Coste % | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Cambio vs base (pp) | Drawdown máximo % | Costes incurridos | Rechazos |",
                        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
            returns, activity, signals_cache = [], 0, {}
            for scenario in scenarios:
                key = (scenario.fast_window, scenario.slow_window)
                if key not in signals_cache:
                    signals_cache[key] = create_strategy(name, *key).generate_signals(prices)
                result = run_backtest(rates, signals_cache[key], pair, cost_rate=scenario.cost_rate,
                                      initial_capital=initial_capital, allocation_fraction=allocation_fraction)
                with localcontext(Context(prec=28)):
                    pnl = result.final_equity - initial_capital
                    return_percent = pnl / initial_capital * 100
                    delta = return_percent - (returns[0] if returns else return_percent)
                    scenario_cost_percent = scenario.cost_rate * 100
                returns.append(return_percent)
                activity += bool(result.closed_trades or result.open_position is not None)
                details.append(
                    f"| {scenario.name} | {key[0]}/{key[1]} | {scenario_cost_percent:f} | "
                    f"{len(result.closed_trades)} | {'Sí' if result.open_position is not None else 'No'} | "
                    f"{_number(result.final_equity)} | {_number(pnl)} | {_number(return_percent)} | {_number(delta)} | "
                    f"{_number(result.max_drawdown_percent)} | {_number(result.total_costs)} | {result.rejected_entries} |"
                )
            with localcontext(Context(prec=28)):
                deviation = max(abs(value - returns[0]) for value in returns)
            summaries.append(
                f"| {pair} | {name.upper()} | {pair.split('/')[1]} | {_number(returns[0])} | "
                f"{_number(min(returns))} | {_number(max(returns))} | {_number(deviation)} | "
                f"{sum(value > 0 for value in returns)}/{len(returns)} | {activity}/{len(returns)} |"
            )
    lines += [
        "", "## Resumen por cuenta", "",
        "| Par | Estrategia | Moneda | Base % | Mínimo % | Máximo % | Máxima desviación vs base (pp) | Escenarios positivos | Con exposición |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|", *summaries, "",
        "El resumen incluye la base y todos los escenarios válidos; positivos significa resultado estrictamente > 0.",
        "Con exposición: al menos una operación cerrada o una posición abierta. No representa porcentaje de tiempo invertido.",
        "Sin exposición no hay evidencia de estabilidad, aunque todas las rentabilidades sean cero.",
        "", "## Detalle de escenarios", "",
        "Capital, resultado y costes están en la moneda cotizada del par. Resultado total = capital final - inicial.",
        "Incluye costes incurridos y valoración de posiciones abiertas, sin anticipar coste de salida.",
        "Rentabilidad acumulada = resultado / capital inicial × 100; no anualizada. Cambios expresados en puntos porcentuales.",
        "Drawdown: mayor caída porcentual desde un máximo previo del capital diario, incluido el capital inicial.",
        *details, "", "## Interpretación y límites", "",
        "Una gran variación frente a la base indica sensibilidad local; no se impone un umbral de aprobación.",
        "Cambios de signo muestran que el resultado depende de estos supuestos. El número de escenarios positivos no es una probabilidad.",
        "No se elige ganador ni se ordena por rendimiento ni se buscan parámetros. No mide interacciones entre cambios simultáneos.",
        "Reutiliza el mismo histórico: no es validación fuera de muestra ni prueba suficiente de robustez o rentabilidad futura.",
        "Comparar dentro de cada par; no sumar monedas distintas. Igual asignación no iguala riesgo.",
        "Referencias informativas, no precios ejecutables ni OHLC. Sin validación completa del calendario ni relleno de fechas.",
        "Faltan spreads, slippage, swaps y restricciones reales del bróker. No hay órdenes reales ni conexión con un bróker.",
        "", "## Reproducción", "",
        f"`python -m trading_ai --sensitivity --fast-window {fast_window} --slow-window {slow_window} --cost-percent {cost_percent} --initial-capital {format(initial_capital, 'f')}{allocation_option} --data RUTA_XML --output RUTA_MD`",
        "Usar la misma copia (SHA-256), código y reglas; sin hora de ejecución ni rutas locales en el contenido.", "",
    ]
    if sha256(path.read_bytes()).hexdigest() != checksum:
        raise ValueError("El archivo de datos cambió durante el cálculo; repite con una copia estable.")
    return "\n".join(lines)


def write_sensitivity_report(source: str | Path, output: str | Path, *, cost_rate: Decimal = Decimal("0"),
                             initial_capital: Decimal = Decimal("1000"),
                             allocation_fraction: Decimal | None = None,
                             fast_window: int = 20, slow_window: int = 60) -> Path:
    """Guarda un informe nuevo o idéntico, conservando otras salidas y los datos."""
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError("La salida no puede ser el archivo de datos.")
    report = build_sensitivity_report(source, cost_rate=cost_rate, initial_capital=initial_capital,
                                      allocation_fraction=allocation_fraction,
                                      fast_window=fast_window, slow_window=slow_window)
    return _save_report(output, report)
