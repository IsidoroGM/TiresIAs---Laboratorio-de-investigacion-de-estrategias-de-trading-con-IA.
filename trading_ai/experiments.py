"""Herramienta de investigación acotada: una base y una variante sobre la misma copia."""

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path

from trading_ai.backtesting import (run_backtest, validate_allocation_fraction,
                                    validate_cost_rate, validate_initial_capital)
from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates
from trading_ai.metrics import calculate_metrics
from trading_ai.strategies import create_strategy, validate_crossover_windows


CRITERIA = ("higher_return_without_more_drawdown", "lower_drawdown_without_lower_return")
VERDICTS = ("supported_in_sample", "not_supported_in_sample", "inconclusive")
RELATIONS = ("higher", "lower", "equal")
PROPOSAL_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "hypothesis": {"type": "string", "maxLength": 400},
        "criterion": {"type": "string", "enum": list(CRITERIA)},
        "tool": {"type": "string", "enum": ["run_experiment"]},
        "arguments": {
            "type": "object", "additionalProperties": False,
            "properties": {"strategy": {"type": "string", "enum": ["sma", "ema"]},
                           "fast_window": {"type": "integer", "minimum": 1, "maximum": 120},
                           "slow_window": {"type": "integer", "minimum": 2, "maximum": 252}},
            "required": ["strategy", "fast_window", "slow_window"],
        },
    }, "required": ["hypothesis", "criterion", "tool", "arguments"],
}
ASSESSMENT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"verdict": {"type": "string", "enum": list(VERDICTS)},
                   "return_comparison": {"type": "string", "enum": list(RELATIONS)},
                   "drawdown_comparison": {"type": "string", "enum": list(RELATIONS)},
                   "scope": {"type": "string", "enum": ["historical_sample_only"]}},
    "required": ["verdict", "return_comparison", "drawdown_comparison", "scope"],
}


@dataclass(frozen=True)
class ExperimentPolicy:
    """Supuestos del usuario. El modelo solo puede cambiar estrategia y ventanas."""

    pair: str = "EUR/USD"
    baseline_strategy: str = "sma"
    fast_window: int = 20
    slow_window: int = 60
    cost_rate: Decimal = Decimal("0.001")
    initial_capital: Decimal = Decimal("1000")
    allocation_fraction: Decimal | None = Decimal("0.1")

    def __post_init__(self):
        if self.pair not in SUPPORTED_PAIRS:
            raise ValueError("Par no admitido.")
        create_strategy(self.baseline_strategy, self.fast_window, self.slow_window)
        validate_cost_rate(self.cost_rate)
        validate_initial_capital(self.initial_capital)
        validate_allocation_fraction(self.allocation_fraction)

    def parameters(self) -> dict:
        return {key: str(value) if isinstance(value, Decimal) else value
                for key, value in asdict(self).items()}


def validate_proposal(proposal: dict, policy: ExperimentPolicy) -> None:
    if not isinstance(proposal, dict) or set(proposal) != set(PROPOSAL_SCHEMA["required"]):
        raise ValueError("Propuesta con campos ausentes o no autorizados.")
    if proposal["tool"] != "run_experiment" or proposal["criterion"] not in CRITERIA:
        raise ValueError("Herramienta o criterio no permitido.")
    text = proposal["hypothesis"]
    if not isinstance(text, str) or not text.strip() or len(text) > 400:
        raise ValueError("La hipótesis debe ser texto no vacío de hasta 400 caracteres.")
    args = proposal["arguments"]
    if not isinstance(args, dict) or set(args) != {"strategy", "fast_window", "slow_window"}:
        raise ValueError("Argumentos no autorizados; el modelo no controla datos, rutas, capital ni costes.")
    if args["strategy"] not in ("sma", "ema"):
        raise ValueError("Estrategia no autorizada.")
    validate_crossover_windows(args["fast_window"], args["slow_window"])
    if args["fast_window"] > 120 or args["slow_window"] > 252:
        raise ValueError("Ventanas fuera de los límites del experimento.")
    if (args["strategy"], args["fast_window"], args["slow_window"]) == (
            policy.baseline_strategy, policy.fast_window, policy.slow_window):
        raise ValueError("La variante debe ser distinta de la base.")


def _summary(rates, policy: ExperimentPolicy, strategy: str, fast: int, slow: int) -> dict:
    selected = create_strategy(strategy, fast, slow)
    result = run_backtest(rates, selected.generate_signals([value for _, value in rates]),
                          policy.pair, cost_rate=policy.cost_rate,
                          initial_capital=policy.initial_capital,
                          allocation_fraction=policy.allocation_fraction)
    metrics = calculate_metrics(result)
    with localcontext(Context(prec=28)):
        total_return = (result.final_equity - result.initial_capital) / result.initial_capital * 100
    return {"strategy": selected.name, "quote_currency": result.quote_currency,
            "final_equity": str(result.final_equity), "return_percent": str(total_return),
            "max_drawdown_percent": str(result.max_drawdown_percent),
            "total_costs": str(result.total_costs), "closed_trades": metrics.total_trades,
            "has_open_position": metrics.has_open_position,
            "rejected_entries": result.rejected_entries}


def strategies_without_closed_trades(result: dict) -> list[str]:
    """Identifica las estrategias que no permiten comparar cierres en esta versión."""
    return [name for name in ("baseline", "candidate") if result[name]["closed_trades"] == 0]


def expected_assessment(result: dict) -> dict:
    base, candidate = result["baseline"], result["candidate"]
    def relation(field):
        first, second = Decimal(candidate[field]), Decimal(base[field])
        return "higher" if first > second else "lower" if first < second else "equal"
    returns = relation("return_percent")
    drawdown = relation("max_drawdown_percent")
    if strategies_without_closed_trades(result) or returns == drawdown == "equal":
        verdict = "inconclusive"
    else:
        supported = ((returns == "higher" and drawdown != "higher")
                     if result["proposal"]["criterion"] == CRITERIA[0]
                     else (drawdown == "lower" and returns != "lower"))
        verdict = "supported_in_sample" if supported else "not_supported_in_sample"
    return {"verdict": verdict, "return_comparison": returns,
            "drawdown_comparison": drawdown, "scope": "historical_sample_only"}


def validate_assessment(assessment: dict, result: dict) -> None:
    if assessment != expected_assessment(result):
        raise ValueError("El análisis de la IA no coincide con las métricas o con el criterio registrado.")


def run_experiment(source: str | Path, proposal: dict,
                   policy: ExperimentPolicy = ExperimentPolicy()) -> dict:
    validate_proposal(proposal, policy)
    path = Path(source)
    checksum = sha256(path.read_bytes()).hexdigest()
    rates = load_ecb_rates(path, policy.pair)
    if not rates:
        raise ValueError("No hay observaciones para el experimento.")
    if sha256(path.read_bytes()).hexdigest() != checksum:
        raise ValueError("Los datos cambiaron al cargarlos; experimento cancelado.")
    args = proposal["arguments"]
    return {
        "source": {"name": "BCE", "sha256": checksum, "first_date": rates[0][0].isoformat(),
                   "last_date": rates[-1][0].isoformat(), "observations": len(rates)},
        "policy": policy.parameters(), "proposal": proposal,
        "baseline": _summary(rates, policy, policy.baseline_strategy,
                             policy.fast_window, policy.slow_window),
        "candidate": _summary(rates, policy, args["strategy"],
                              args["fast_window"], args["slow_window"]),
    }
