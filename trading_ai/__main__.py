"""Punto de entrada de Trading AI."""

import argparse
from decimal import Context, Decimal, InvalidOperation, localcontext
from pathlib import Path

from trading_ai.reporting import write_comparison_report, write_report
from trading_ai.sensitivity import write_sensitivity_report
from trading_ai.backtesting import validate_initial_capital
from trading_ai.strategies import validate_crossover_windows


def _allocation_percent(text: str) -> Decimal:
    try:
        percent = Decimal(text)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError("Indica un porcentaje de asignación decimal, por ejemplo 10.") from error
    if not percent.is_finite() or not Decimal("0") < percent <= Decimal("100"):
        raise argparse.ArgumentTypeError("La asignación debe ser mayor que 0 y como máximo 100 %.")
    with localcontext(Context(prec=28)):
        return percent / 100


def _initial_capital(text: str) -> Decimal:
    try:
        capital = Decimal(text)
        validate_initial_capital(capital)
    except (InvalidOperation, ValueError) as error:
        raise argparse.ArgumentTypeError("Indica un capital inicial decimal, finito y positivo.") from error
    return capital


def _cost_percent(text: str) -> Decimal:
    try:
        percent = Decimal(text)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError("Indica un porcentaje decimal, por ejemplo 0.1.") from error
    if not percent.is_finite() or not Decimal("0") <= percent < Decimal("100"):
        raise argparse.ArgumentTypeError("El porcentaje debe estar entre 0 (incluido) y 100 (excluido).")
    with localcontext(Context(prec=28)):
        return percent / 100


def main(argv: list[str] | None = None) -> None:
    """Muestra la presentación o genera el informe educativo solicitado."""
    parser = argparse.ArgumentParser(description="Trading AI - laboratorio educativo")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--report", action="store_true", help="Generar el informe de cruces de medias de los cuatro pares")
    mode.add_argument("--compare", action="store_true", help="Comparar SMA y EMA bajo los mismos supuestos")
    mode.add_argument("--sensitivity", action="store_true", help="Variar ventanas y costes de SMA y EMA, un factor cada vez")
    parser.add_argument("--strategy", choices=("sma", "ema"), default=None,
                        help="Estrategia de medias simples o exponenciales (predeterminado: sma)")
    parser.add_argument("--fast-window", type=int, default=20, help="Ventana rápida en observaciones (predeterminado: 20)")
    parser.add_argument("--slow-window", type=int, default=60, help="Ventana lenta en observaciones (predeterminado: 60)")
    parser.add_argument("--data", type=Path, default=Path("data/raw/ecb-eurofxref-hist-2026-10-18.xml"))
    parser.add_argument("--output", type=Path, default=None,
                        help="Salida: reports/report.md, reports/comparison.md o reports/sensitivity.md según el modo")
    parser.add_argument("--cost-percent", type=_cost_percent, default=Decimal("0"),
                        help="Coste hipotético por compra o venta en porcentaje; 0.1 significa 0.1%% (predeterminado: 0)")
    parser.add_argument("--initial-capital", type=_initial_capital, default=Decimal("1000"),
                        help="Capital inicial de cada cuenta en su moneda cotizada (predeterminado: 1000)")
    parser.add_argument("--allocation-percent", type=_allocation_percent, default=None,
                        help="Porcentaje del efectivo actual por entrada, costes incluidos; sin esta opción: una unidad base")
    args = parser.parse_args(argv)
    if (args.compare or args.sensitivity) and args.strategy is not None:
        parser.error("--compare y --sensitivity incluyen SMA y EMA; no admiten --strategy.")
    try:
        validate_crossover_windows(args.fast_window, args.slow_window)
    except (ValueError, TypeError) as error:
        parser.error(str(error))
    if not args.report and not args.compare and not args.sensitivity:
        print("Trading AI - laboratorio educativo")
        print("FASE 2 completada - simulación educativa. Usa --report, --compare o --sensitivity.")
        return
    try:
        default_output = ("reports/sensitivity.md" if args.sensitivity else
                          "reports/comparison.md" if args.compare else "reports/report.md")
        output_path = args.output or Path(default_output)
        options = dict(cost_rate=args.cost_percent, initial_capital=args.initial_capital,
                       allocation_fraction=args.allocation_percent,
                       fast_window=args.fast_window, slow_window=args.slow_window)
        if args.sensitivity:
            output = write_sensitivity_report(args.data, output_path, **options)
        elif args.compare:
            output = write_comparison_report(args.data, output_path, **options)
        else:
            output = write_report(args.data, output_path, strategy_name=args.strategy or "sma", **options)
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"No se pudo generar el informe: {error}\n")
    print(f"Informe educativo disponible en: {output.resolve()}")


if __name__ == "__main__":
    main()
