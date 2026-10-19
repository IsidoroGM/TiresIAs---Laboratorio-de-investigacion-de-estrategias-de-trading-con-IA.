"""Informe reproducible, cifras del cálculo y escritura sin sobrescribir trabajo."""

from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256

import pytest

from trading_ai.__main__ import main
from trading_ai.backtesting import run_backtest
from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates
from trading_ai.indicators import simple_moving_average
from trading_ai.metrics import calculate_metrics
from trading_ai.reporting import build_comparison_report, build_report, write_report
from trading_ai.sensitivity import build_sensitivity_report
from trading_ai.strategies import sma_crossover_signals


@pytest.fixture
def source(tmp_path):
    # Tendencia ascendente, descendente y ascendente: produce cierres y entradas.
    values = list(range(100, 180)) + list(range(180, 100, -1)) + list(range(100, 180))
    days = []
    for index, value in enumerate(values):
        day = date(2025, 1, 1) + timedelta(days=index)
        days.append(f'<Cube time="{day}"><Cube currency="USD" rate="{value}"/>'
                    '<Cube currency="GBP" rate="1"/><Cube currency="JPY" rate="100"/>'
                    '<Cube currency="CHF" rate="1"/></Cube>')
    path = tmp_path / "sample.xml"
    path.write_text('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
                    '<Cube>' + ''.join(reversed(days)) + '</Cube></Envelope>', encoding="utf-8")
    return path


def test_report_matches_computed_results_and_provenance(source):
    report = build_report(source)
    assert sha256(source.read_bytes()).hexdigest() in report
    for pair in SUPPORTED_PAIRS:
        rates = load_ecb_rates(source, pair)
        values = [value for _, value in rates]
        result = run_backtest(rates, sma_crossover_signals(simple_moving_average(values, 20),
                              simple_moving_average(values, 60)), pair)
        m = calculate_metrics(result)
        assert f"| {pair} | {rates[0][0]} | {rates[-1][0]} | 240 | {m.total_trades} |" in report
        if m.total_trades:
            assert f"| {pair} | {m.quote_currency} | {m.win_rate_percent:.2f} | {m.total_pnl:.6f} | {m.average_pnl:.6f} |" in report
        else:
            assert f"| {pair} | {m.quote_currency} | N/D | 0.000000 | N/D |" in report
        if result.open_position:
            assert f"entrada simulada {result.open_position.entry_date}" in report
    assert "costes cero" in report
    assert "fuera de muestra" in report
    assert "Variación de precio latente" in report


def test_same_data_produces_identical_report(source):
    assert build_report(source) == build_report(source)


def test_unavailable_metrics_are_not_rendered_as_zero(source):
    # Un solo día: no hay medias completas ni operaciones.
    source.write_text('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
                      '<Cube><Cube time="2026-01-01">'
                      '<Cube currency="USD" rate="1.2"/><Cube currency="GBP" rate="0.8"/>'
                      '<Cube currency="JPY" rate="120"/><Cube currency="CHF" rate="1"/>'
                      '</Cube></Cube></Envelope>', encoding="utf-8")
    report = build_report(source)
    assert "| EUR/USD | USD | N/D | 0.000000 | N/D | 0.000000 | 0.000000 | N/D |" in report
    assert "EUR/USD: ninguna" in report


def test_cli_generates_report_and_identical_repeat_is_allowed(source, tmp_path, capsys):
    output = tmp_path / "reports" / "summary.md"
    argv = ["--report", "--data", str(source), "--output", str(output)]
    main(argv)
    assert "Informe educativo disponible" in capsys.readouterr().out
    original = output.read_bytes()
    main(argv)
    assert output.read_bytes() == original
    assert output.read_text(encoding="utf-8") == build_report(source)


def test_existing_different_output_is_preserved(source, tmp_path):
    output = tmp_path / "notes.md"
    output.write_text("Mis notas", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_report(source, output)
    assert output.read_text(encoding="utf-8") == "Mis notas"


def test_source_cannot_be_output(source):
    original = source.read_bytes()
    with pytest.raises(ValueError, match="archivo de datos"):
        write_report(source, source)
    assert source.read_bytes() == original


def test_cli_missing_source_has_clear_error_and_no_output(tmp_path, capsys):
    output = tmp_path / "report.md"
    with pytest.raises(SystemExit) as error:
        main(["--report", "--data", str(tmp_path / "absent.xml"), "--output", str(output)])
    assert error.value.code == 1
    assert "No se pudo generar" in capsys.readouterr().err
    assert not output.exists()


def test_invalid_data_does_not_create_output(source, tmp_path):
    source.write_text("<broken>", encoding="utf-8")
    output = tmp_path / "report.md"
    with pytest.raises(ValueError, match="XML inválido"):
        write_report(source, output)
    assert not output.exists()


def test_cli_default_only_shows_presentation(capsys):
    main([])
    assert "--report" in capsys.readouterr().out


def test_report_cost_option_reaches_calculations_and_reproduction(source, tmp_path):
    output = tmp_path / "cost-report.md"
    main(["--report", "--data", str(source), "--output", str(output), "--cost-percent", "0.1"])
    report = output.read_text(encoding="utf-8")
    assert report == build_report(source, cost_rate=Decimal("0.001"))
    assert "Coste hipotético por compra o venta: 0.100 %" in report
    assert "--cost-percent 0.100" in report
    rates = load_ecb_rates(source, "EUR/USD")
    values = [value for _, value in rates]
    result = run_backtest(rates, sma_crossover_signals(simple_moving_average(values, 20),
                          simple_moving_average(values, 60)), "EUR/USD", cost_rate=Decimal("0.001"))
    assert f"| EUR/USD | USD | {result.gross_realized_pnl:.6f} | {result.closed_costs:.6f} | {result.realized_pnl:.6f} | {result.total_costs:.6f} | {result.pnl_after_incurred_costs:.6f} |" in report
    assert "Coste de entrada ya incurrido" in report


@pytest.mark.parametrize("value", ["-1", "100", "NaN", "Infinity", "abc"])
def test_cli_invalid_cost_produces_no_report(value, tmp_path):
    output = tmp_path / "report.md"
    with pytest.raises(SystemExit) as error:
        main(["--report", f"--cost-percent={value}", "--output", str(output)])
    assert error.value.code == 2
    assert not output.exists()


def test_cli_capital_reaches_account_and_report(source, tmp_path):
    output = tmp_path / "capital.md"
    main(["--report", "--data", str(source), "--output", str(output), "--initial-capital", "1"])
    report = output.read_text(encoding="utf-8")
    assert report == build_report(source, initial_capital=Decimal("1"))
    assert "Capital inicial por cuenta independiente: 1" in report
    assert "--initial-capital 1" in report
    # Una unidad EUR cuesta más que el saldo de 1 USD: sus compras se rechazan.
    # La subida inicial no es un cruce: al completar SMA60 ya estaba por encima.
    assert "| EUR/USD | USD | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 1 |" in report
    assert "resumen anual de la curva diaria" in report


@pytest.mark.parametrize("value", ["0", "-1", "NaN", "Infinity", "abc"])
def test_cli_invalid_capital_is_rejected(value, tmp_path):
    output = tmp_path / "capital.md"
    with pytest.raises(SystemExit) as error:
        main(["--report", f"--initial-capital={value}", "--output", str(output)])
    assert error.value.code == 2
    assert not output.exists()


def test_cli_percentage_sizing_reaches_report_and_engine(source, tmp_path):
    output = tmp_path / "allocation.md"
    main(["--report", "--data", str(source), "--output", str(output),
          "--allocation-percent", "10", "--cost-percent", "0.1"])
    report = output.read_text(encoding="utf-8")
    assert report == build_report(source, allocation_fraction=Decimal("0.1"), cost_rate=Decimal("0.001"))
    assert "Tamaño: 10.0 % del efectivo disponible" in report
    assert "--allocation-percent 10.0" in report
    assert "Cantidad mínima" in report and "no pérdida máxima" in report
    observations = load_ecb_rates(source, "EUR/USD")
    values = [value for _, value in observations]
    result = run_backtest(observations, sma_crossover_signals(simple_moving_average(values, 20),
                          simple_moving_average(values, 60)), "EUR/USD", allocation_fraction=Decimal("0.1"), cost_rate=Decimal("0.001"))
    quantities = [t.position.quantity for t in result.closed_trades] + [result.open_position.quantity]
    assert f"| EUR/USD | EUR | {min(quantities):.6f} | {max(quantities):.6f} |" in report
    assert f"{result.final_equity:.6f}" in report


@pytest.mark.parametrize("value", ["0", "-1", "100.1", "NaN", "Infinity", "abc"])
def test_cli_invalid_allocation_is_rejected(value, tmp_path):
    output = tmp_path / "allocation.md"
    with pytest.raises(SystemExit) as error:
        main(["--report", f"--allocation-percent={value}", "--output", str(output)])
    assert error.value.code == 2 and not output.exists()


def test_default_windows_remain_20_60(source):
    assert build_report(source) == build_report(source, fast_window=20, slow_window=60)


def test_cli_windows_reach_calculations_and_reproduction(source, tmp_path):
    output = tmp_path / "windows.md"
    main(["--report", "--data", str(source), "--output", str(output),
          "--fast-window", "10", "--slow-window", "40"])
    report = output.read_text(encoding="utf-8")
    assert report == build_report(source, fast_window=10, slow_window=40)
    assert "Informe educativo SMA10/SMA40" in report
    assert "Medias de 10 y 40 observaciones" in report
    assert "Primera señal posible desde la observación 41" in report
    assert "--fast-window 10 --slow-window 40" in report
    for pair in SUPPORTED_PAIRS:
        rates = load_ecb_rates(source, pair)
        values = [value for _, value in rates]
        result = run_backtest(rates, sma_crossover_signals(simple_moving_average(values, 10),
                              simple_moving_average(values, 40)), pair)
        m = calculate_metrics(result)
        if m.total_trades:
            assert f"| {pair} | {m.quote_currency} | {m.win_rate_percent:.2f} | {m.total_pnl:.6f} | {m.average_pnl:.6f} |" in report
        else:
            assert f"| {pair} | {m.quote_currency} | N/D | 0.000000 | N/D |" in report


def test_custom_windows_produce_known_trade_and_long_windows_wait(tmp_path):
    source = tmp_path / "known.xml"
    days = []
    for index, price in enumerate((3, 2, 1, 2, 3, 2, 1), start=1):
        days.append(f'<Cube time="2025-01-{index:02d}"><Cube currency="USD" rate="{price}"/>'
                    '<Cube currency="GBP" rate="1"/><Cube currency="JPY" rate="100"/>'
                    '<Cube currency="CHF" rate="1"/></Cube>')
    source.write_text('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
                      '<Cube>' + ''.join(days) + '</Cube></Envelope>', encoding="utf-8")
    report = build_report(source, fast_window=1, slow_window=2)
    # Cruces el 4 y el 6; ejecución el 5 a 3 USD y el 7 a 1 USD: pérdida de 2 USD.
    assert "| EUR/USD | 2025-01-01 | 2025-01-07 | 7 | 1 |" in report
    assert "| EUR/USD | USD | 0.00 | -2.000000 | -2.000000 |" in report
    assert "EUR/USD: ninguna" in report
    default_report = build_report(source)
    assert "| EUR/USD | 2025-01-01 | 2025-01-07 | 7 | 0 |" in default_report
    assert "| EUR/USD | USD | N/D | 0.000000 | N/D |" in default_report


@pytest.mark.parametrize("fast, slow", [("0", "60"), ("-1", "60"), ("20", "0"),
                                         ("20", "20"), ("60", "20"), ("1.5", "60"),
                                         ("20", "abc")])
def test_cli_invalid_windows_fail_before_reading_data(fast, slow, tmp_path, capsys):
    output = tmp_path / "windows.md"
    with pytest.raises(SystemExit) as error:
        main(["--report", "--data", str(tmp_path / "missing.xml"), "--output", str(output),
              f"--fast-window={fast}", f"--slow-window={slow}"])
    assert error.value.code == 2
    assert "No se pudo generar" not in capsys.readouterr().err
    assert not output.exists()


def test_report_api_validates_windows_before_reading_data(tmp_path):
    with pytest.raises(ValueError, match="menor"):
        build_report(tmp_path / "missing.xml", fast_window=60, slow_window=20)


def test_cli_ema_selection_and_all_assumptions_reach_report(source, tmp_path):
    output = tmp_path / "ema.md"
    main(["--report", "--strategy", "ema", "--fast-window", "10", "--slow-window", "40",
          "--cost-percent", "0.1", "--initial-capital", "200", "--allocation-percent", "10",
          "--data", str(source), "--output", str(output)])
    report = output.read_text(encoding="utf-8")
    assert report == build_report(source, strategy_name="ema", fast_window=10, slow_window=40,
                                  cost_rate=Decimal("0.001"), initial_capital=Decimal(200),
                                  allocation_fraction=Decimal("0.1"))
    assert "Informe educativo EMA10/EMA40" in report
    assert "semilla = SMA de las primeras n observaciones" in report
    assert "alfa = 2/(n+1)" in report
    assert "--strategy ema --fast-window 10 --slow-window 40" in report


def test_default_strategy_remains_sma(source):
    assert build_report(source) == build_report(source, strategy_name="sma")


def test_unknown_strategy_rejected_before_io(tmp_path):
    missing = tmp_path / "missing.xml"
    output = tmp_path / "report.md"
    with pytest.raises(ValueError, match="no admitida"):
        build_report(missing, strategy_name="unknown")
    with pytest.raises(SystemExit) as error:
        main(["--report", "--strategy", "unknown", "--data", str(missing), "--output", str(output)])
    assert error.value.code == 2 and not output.exists()


def test_ema_report_known_trade_differs_from_sma_at_same_windows(tmp_path):
    source = tmp_path / "known.xml"
    days = []
    for index, price in enumerate((3, 2, 1, 2, 3, 2, 1), start=1):
        days.append(f'<Cube time="2025-01-{index:02d}"><Cube currency="USD" rate="{price}"/>'
                    '<Cube currency="GBP" rate="1"/><Cube currency="JPY" rate="100"/>'
                    '<Cube currency="CHF" rate="1"/></Cube>')
    source.write_text('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
                      '<Cube>' + ''.join(days) + '</Cube></Envelope>', encoding="utf-8")
    ema_report = build_report(source, strategy_name="ema", fast_window=1, slow_window=3)
    sma_report = build_report(source, strategy_name="sma", fast_window=1, slow_window=3)
    # EMA compra el 6 a 2 y vende el 7 a 1. SMA compra el 5 a 3 y vende el 7 a 1.
    assert "| EUR/USD | USD | 0.00 | -1.000000 | -1.000000 |" in ema_report
    assert "| EUR/USD | USD | 0.00 | -2.000000 | -2.000000 |" in sma_report
    assert "EUR/USD: ninguna" in ema_report


def test_switching_strategy_cannot_overwrite_sma_report(source, tmp_path):
    output = tmp_path / "report.md"
    write_report(source, output)
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        write_report(source, output, strategy_name="ema")
    assert output.read_bytes() == original


@pytest.mark.parametrize("builder", [build_report, build_comparison_report, build_sensitivity_report])
def test_report_rounding_is_independent_of_callers_decimal_context(source, builder):
    params = dict(initial_capital=Decimal("1000.1234567"), cost_rate=Decimal("0.001"),
                  allocation_fraction=Decimal("0.123456789"))
    expected = builder(source, **params)
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        assert builder(source, **params) == expected
        assert context.prec == 6 and context.rounding == ROUND_DOWN
