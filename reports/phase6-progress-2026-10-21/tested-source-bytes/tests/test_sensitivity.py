"""Escenarios controlados, límites, contabilidad e integración del informe."""

from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256

import pytest

from trading_ai.__main__ import main
from trading_ai.backtesting import run_backtest
from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates
from trading_ai.sensitivity import build_sensitivity_report, sensitivity_scenarios, write_sensitivity_report
from trading_ai.strategies import create_strategy


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "known.xml"
    days = []
    for index, price in enumerate((3, 2, 1, 2, 3, 2, 1), start=1):
        days.append(f'<Cube time="2025-01-{index:02d}"><Cube currency="USD" rate="{price}"/>'
                    '<Cube currency="GBP" rate="1"/><Cube currency="JPY" rate="100"/>'
                    '<Cube currency="CHF" rate="1"/></Cube>')
    path.write_text('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
                    '<Cube>' + ''.join(days) + '</Cube></Envelope>', encoding="utf-8")
    return path


def test_scenarios_change_exactly_one_factor_in_fixed_order():
    scenarios, omitted = sensitivity_scenarios(20, 60, Decimal("0.001"))
    assert not omitted
    assert [(s.fast_window, s.slow_window, s.cost_rate) for s in scenarios] == [
        (20, 60, Decimal("0.001")), (19, 60, Decimal("0.001")),
        (21, 60, Decimal("0.001")), (20, 59, Decimal("0.001")),
        (20, 61, Decimal("0.001")), (20, 60, Decimal("0.0005")),
        (20, 60, Decimal("0.0015")),
    ]
    assert scenarios[0].name == "Base"


def test_invalid_neighbours_are_omitted_not_clamped_or_duplicated():
    scenarios, omitted = sensitivity_scenarios(1, 2, Decimal(0))
    assert [(s.fast_window, s.slow_window, s.cost_rate) for s in scenarios] == [
        (1, 2, Decimal(0)), (1, 3, Decimal(0)), (1, 2, Decimal("0.0005")),
    ]
    assert len(omitted) == 4
    assert any("Rápida -1" in item for item in omitted)
    assert any("Coste -0.05 pp" in item for item in omitted)
    scenarios, omitted = sensitivity_scenarios(20, 60, Decimal("0.9998"))
    assert len(scenarios) == 6 and len(omitted) == 1
    assert "Coste +0.05 pp" in omitted[0]


def test_known_baseline_and_cost_perturbation(source):
    report = build_sensitivity_report(source, fast_window=1, slow_window=3, initial_capital=Decimal(10))
    # SMA compra a 3 y vende a 1: -2. Coste 0.05% añade 0.002 de gastos.
    assert "| Base | 1/3 | 0 | 1 | No | 8.000000 | -2.000000 | -20.000000 | 0.000000 | 20.000000 | 0.000000 | 0 |" in report
    assert "| Coste +0.05 pp | 1/3 | 0.0500 | 1 | No | 7.998000 | -2.002000 | -20.020000 | -0.020000 | 20.020000 | 0.002000 | 0 |" in report
    # EMA compra a 2 y vende a 1: -1.
    assert "| Base | 1/3 | 0 | 1 | No | 9.000000 | -1.000000 | -10.000000 | 0.000000 | 10.000000 | 0.000000 | 0 |" in report
    assert sha256(source.read_bytes()).hexdigest() in report
    assert "Coste -0.05 pp:" in report
    assert "Escenarios válidos por estrategia y par: 5" in report


def test_no_exposure_is_reported_without_claiming_stability(source):
    report = build_sensitivity_report(source)
    assert "| EUR/USD | SMA | USD | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0/6 | 0/6 |" in report
    assert "Sin exposición no hay evidencia de estabilidad" in report


def test_open_position_counts_as_exposure_and_total_result(source):
    content = source.read_text(encoding="utf-8")
    for day, old, new in ((6, 2, 4), (7, 1, 5)):
        content = content.replace(f'time="2025-01-{day:02d}"><Cube currency="USD" rate="{old}"',
                                  f'time="2025-01-{day:02d}"><Cube currency="USD" rate="{new}"')
    source.write_text(content, encoding="utf-8")
    report = build_sensitivity_report(source, fast_window=1, slow_window=3,
                                      initial_capital=Decimal(10), cost_rate=Decimal("0.01"))
    assert "| Base | 1/3 | 1.00 | 0 | Sí | 11.970000 | 1.970000 | 19.700000 | 0.000000 | 0.300000 | 0.030000 | 0 |" in report
    # Seis escenarios, todos invierten; sus operaciones aún no han cerrado.
    summary = next(line for line in report.splitlines() if line.startswith("| EUR/USD | SMA |"))
    assert summary.endswith("| 6/6 |")


def test_cli_all_scenarios_match_independent_runs_and_repeat(source, tmp_path):
    output = tmp_path / "sensitivity.md"
    args = ["--sensitivity", "--fast-window", "1", "--slow-window", "3", "--cost-percent", "0.1",
            "--initial-capital", "100", "--allocation-percent", "10", "--data", str(source),
            "--output", str(output)]
    main(args)
    original = output.read_bytes()
    report = output.read_text(encoding="utf-8")
    params = dict(fast_window=1, slow_window=3, cost_rate=Decimal("0.001"),
                  initial_capital=Decimal(100), allocation_fraction=Decimal("0.1"))
    assert report == build_sensitivity_report(source, **params)
    assert "--sensitivity --fast-window 1 --slow-window 3 --cost-percent 0.100" in report
    assert "--initial-capital 100 --allocation-percent 10.0" in report
    scenarios, _ = sensitivity_scenarios(1, 3, Decimal("0.001"))
    for pair in SUPPORTED_PAIRS:
        rates = load_ecb_rates(source, pair)
        for name in ("sma", "ema"):
            section = report.split(f"### {pair} — {name.upper()}\n", 1)[1].split("\n### ")[0]
            returns, activity = [], 0
            for scenario in scenarios:
                strategy = create_strategy(name, scenario.fast_window, scenario.slow_window)
                result = run_backtest(rates, strategy.generate_signals([p for _, p in rates]), pair,
                                      cost_rate=scenario.cost_rate, initial_capital=Decimal(100),
                                      allocation_fraction=Decimal("0.1"))
                pnl = result.final_equity - Decimal(100)
                returns.append(pnl)  # Con capital 100, coincide numéricamente con el porcentaje.
                activity += bool(result.closed_trades or result.open_position is not None)
                assert (f"| {scenario.name} | {scenario.fast_window}/{scenario.slow_window} | "
                        f"{scenario.cost_rate * 100:f} | {len(result.closed_trades)} | "
                        f"{'Sí' if result.open_position else 'No'} | {result.final_equity:.6f} | "
                        f"{pnl:.6f} | {pnl:.6f} | {pnl - returns[0]:.6f} | "
                        f"{result.max_drawdown_percent:.6f} | {result.total_costs:.6f} | {result.rejected_entries} |") in section
            deviation = max(abs(value - returns[0]) for value in returns)
            assert (f"| {pair} | {name.upper()} | {pair.split('/')[1]} | {returns[0]:.6f} | "
                    f"{min(returns):.6f} | {max(returns):.6f} | {deviation:.6f} | "
                    f"{sum(value > 0 for value in returns)}/6 | {activity}/6 |") in report
    main(args)
    assert output.read_bytes() == original


def test_report_and_scenarios_ignore_external_decimal_context(source):
    params = dict(fast_window=1, slow_window=3, cost_rate=Decimal("0.001"))
    expected = build_sensitivity_report(source, **params)
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        assert build_sensitivity_report(source, **params) == expected
        assert context.prec == 6 and context.rounding == ROUND_DOWN


@pytest.mark.parametrize("params", [{"fast_window": 60}, {"fast_window": True},
                                    {"cost_rate": Decimal("NaN")}, {"initial_capital": Decimal(0)},
                                    {"allocation_fraction": Decimal(2)}])
def test_invalid_base_is_rejected_before_io(tmp_path, params):
    with pytest.raises((ValueError, TypeError)):
        build_sensitivity_report(tmp_path / "missing.xml", **params)


@pytest.mark.parametrize("other", [["--compare"], ["--report"], ["--strategy", "ema"]])
def test_cli_incompatible_options_fail_before_io(tmp_path, other):
    output = tmp_path / "out.md"
    with pytest.raises(SystemExit) as error:
        main(["--sensitivity", "--output", str(output), "--data", str(tmp_path / "missing.xml")] + other)
    assert error.value.code == 2 and not output.exists()


def test_default_output_and_protection(source, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["--sensitivity", "--data", str(source)])
    assert (tmp_path / "reports/sensitivity.md").exists()
    assert not (tmp_path / "reports/comparison.md").exists()
    with pytest.raises(ValueError, match="archivo de datos"):
        write_sensitivity_report(source, source)
    output = tmp_path / "notes.md"
    output.write_text("Mis notas", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_sensitivity_report(source, output)
    assert output.read_text(encoding="utf-8") == "Mis notas"


def test_changing_source_prevents_output(source, tmp_path, monkeypatch):
    from trading_ai import sensitivity

    loader = sensitivity.load_ecb_rates

    def changing_loader(path, pair):
        rates = loader(path, pair)
        path.write_bytes(path.read_bytes() + b"\n")
        return rates

    monkeypatch.setattr(sensitivity, "load_ecb_rates", changing_loader)
    output = tmp_path / "out.md"
    with pytest.raises(ValueError, match="cambió"):
        write_sensitivity_report(source, output)
    assert not output.exists()
