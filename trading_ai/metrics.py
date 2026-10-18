"""Resumen de cierres del backtest educativo; no valora posiciones abiertas."""

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext

from trading_ai.backtesting import BacktestResult


@dataclass(frozen=True)
class BacktestMetrics:
    pair: str
    quote_currency: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate_percent: Decimal | None
    total_pnl: Decimal
    average_pnl: Decimal | None
    gross_profit: Decimal
    gross_loss: Decimal
    profit_factor: Decimal | None
    has_open_position: bool


def calculate_metrics(result: BacktestResult) -> BacktestMetrics:
    """Resume únicamente las operaciones cerradas, usando sus pnl ya calculados.

    El porcentaje ganador incluye los cierres a cero en el denominador.
    Sin cierres, porcentaje y promedio son None. Gross_loss es la magnitud
    positiva de las pérdidas. Profit_factor es None cuando no hay pérdidas,
    incluso si existen ganancias; nunca se presenta un infinito como puntuación.
    Las sumas vacías son cero. Importes netos de costes de los cierres en moneda
    cotizada; no son rentabilidades sobre capital ni métricas de riesgo.
    Gross_profit/loss suman ganancias/pérdidas de cierres ya netos de costes.
    Rechaza pnl no Decimal, no finitos o un total incoherente con los cierres.
    """
    winning = losing = breakeven = 0
    total = gross_profit = gross_loss = Decimal("0")
    with localcontext(Context(prec=28)):
        for index, trade in enumerate(result.closed_trades):
            pnl = trade.pnl
            if not isinstance(pnl, Decimal):
                raise TypeError(f"Operación {index}: pnl debe ser Decimal.")
            if not pnl.is_finite():
                raise ValueError(f"Operación {index}: pnl debe ser finito.")
            total += pnl
            if pnl > 0:
                winning += 1
                gross_profit += pnl
            elif pnl < 0:
                losing += 1
                gross_loss -= pnl
            else:
                breakeven += 1

        if not isinstance(result.realized_pnl, Decimal):
            raise TypeError("realized_pnl debe ser Decimal.")
        if not result.realized_pnl.is_finite() or result.realized_pnl != total:
            raise ValueError("realized_pnl debe ser finito y coincidir con la suma de cierres.")
        count = len(result.closed_trades)
        win_rate = Decimal(winning) * 100 / count if count else None
        average = total / count if count else None
        factor = gross_profit / gross_loss if gross_loss else None

    return BacktestMetrics(
        pair=result.pair,
        quote_currency=result.quote_currency,
        total_trades=count,
        winning_trades=winning,
        losing_trades=losing,
        breakeven_trades=breakeven,
        win_rate_percent=win_rate,
        total_pnl=total,
        average_pnl=average,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=factor,
        has_open_position=result.open_position is not None,
    )
