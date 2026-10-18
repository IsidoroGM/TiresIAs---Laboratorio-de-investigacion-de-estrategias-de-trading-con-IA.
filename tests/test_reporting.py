"""Informe reproducible, cifras del cálculo y escritura sin sobrescribir trabajo."""

from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256

import pytest

from trading_ai.__main__ import main
from trading_ai.backtesting import run_backtest
from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates
from trading_ai.indicators import simple_moving_average
from trading_ai.metrics import calculate_metrics
from trading_ai.reporting import build_report, write_report
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
