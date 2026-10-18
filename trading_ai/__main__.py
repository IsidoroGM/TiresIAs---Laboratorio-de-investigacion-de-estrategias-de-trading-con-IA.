"""Punto de entrada de Trading AI."""

import argparse
from decimal import Context, Decimal, InvalidOperation, localcontext
from pathlib import Path

from trading_ai.reporting import write_report
from trading_ai.backtesting import validate_initial_capital


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
    parser.add_argument("--report", action="store_true", help="Generar el informe SMA20/SMA60 de los cuatro pares")
    parser.add_argument("--data", type=Path, default=Path("data/raw/ecb-eurofxref-hist-2026-10-18.xml"))
    parser.add_argument("--output", type=Path, default=Path("reports/report.md"))
    parser.add_argument("--cost-percent", type=_cost_percent, default=Decimal("0"),
                        help="Coste hipotético por compra o venta en porcentaje; 0.1 significa 0.1%% (predeterminado: 0)")
    parser.add_argument("--initial-capital", type=_initial_capital, default=Decimal("1000"),
                        help="Capital inicial de cada cuenta en su moneda cotizada (predeterminado: 1000)")
    parser.add_argument("--allocation-percent", type=_allocation_percent, default=None,
                        help="Porcentaje del efectivo actual por entrada, costes incluidos; sin esta opción: una unidad base")
    args = parser.parse_args(argv)
    if not args.report:
        print("Trading AI - laboratorio educativo")
        print("FASE 2 - capital, costes y drawdown. Genera el informe con --report.")
        return
    try:
        output = write_report(args.data, args.output, cost_rate=args.cost_percent,
                              initial_capital=args.initial_capital, allocation_fraction=args.allocation_percent)
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"No se pudo generar el informe: {error}\n")
    print(f"Informe educativo disponible en: {output.resolve()}")


if __name__ == "__main__":
    main()
