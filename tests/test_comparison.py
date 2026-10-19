"""Comparaciones con supuestos comunes, cifras conocidas y salida protegida."""

from decimal import Decimal
from hashlib import sha256

import pytest

from trading_ai.__main__ import main
from trading_ai.backtesting import run_backtest
from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates
from trading_ai.reporting import build_comparison_report, write_comparison_report
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


def test_comparison_known_profit_return_drawdown_and_provenance(source):
    report = build_comparison_report(source, fast_window=1, slow_window=3, initial_capital=Decimal(10))
    # SMA compra a 3 y vende a 1: -2; EMA compra a 2 y vende a 1: -1.
    assert "| EUR/USD | SMA1/SMA3 | USD | 1 | No | 8.000000 | -2.000000 | -20.000000 | 20.000000 | 0.000000 | 0 |" in report
    assert "| EUR/USD | EMA1/EMA3 | USD | 1 | No | 9.000000 | -1.000000 | -10.000000 | 10.000000 | 0.000000 | 0 |" in report
    assert sha256(source.read_bytes()).hexdigest() in report
    assert "| EUR/USD | 2025-01-01 | 2025-01-07 | 7 |" in report
    assert "no anualizada" in report and "no sumar monedas distintas" in report
    assert "--compare --fast-window 1 --slow-window 3" in report


def test_comparison_includes_open_position_and_incurred_entry_cost(source):
    content = source.read_text(encoding="utf-8")
    # Serie final ascendente: SMA compra el 5 a 3; EMA compra el 6 a 4; ambas abiertas.
    content = content.replace('time="2025-01-06"><Cube currency="USD" rate="2"',
                              'time="2025-01-06"><Cube currency="USD" rate="4"')
    content = content.replace('time="2025-01-07"><Cube currency="USD" rate="1"',
                              'time="2025-01-07"><Cube currency="USD" rate="5"')
    source.write_text(content, encoding="utf-8")
    report = build_comparison_report(source, fast_window=1, slow_window=3,
                                     initial_capital=Decimal(10), cost_rate=Decimal("0.01"))
    assert "| EUR/USD | SMA1/SMA3 | USD | 0 | Sí | 11.970000 | 1.970000 | 19.700000 | 0.300000 | 0.030000 | 0 |" in report
    assert "| EUR/USD | EMA1/EMA3 | USD | 0 | Sí | 10.960000 | 0.960000 | 9.600000 | 0.400000 | 0.040000 | 0 |" in report


def test_cli_comparison_shares_data_costs_capital_and_sizing(source, tmp_path):
    output = tmp_path / "comparison.md"
    args = ["--compare", "--data", str(source), "--output", str(output), "--fast-window", "1",
            "--slow-window", "3", "--cost-percent", "0.1", "--initial-capital", "100",
            "--allocation-percent", "10"]
    main(args)
    report = output.read_text(encoding="utf-8")
    params = dict(fast_window=1, slow_window=3, cost_rate=Decimal("0.001"),
                  initial_capital=Decimal(100), allocation_fraction=Decimal("0.1"))
    assert report == build_comparison_report(source, **params)
    for pair in SUPPORTED_PAIRS:
        rates = load_ecb_rates(source, pair)
        for name in ("sma", "ema"):
            strategy = create_strategy(name, 1, 3)
            result = run_backtest(rates, strategy.generate_signals([p for _, p in rates]), pair,
                                  cost_rate=params["cost_rate"], initial_capital=params["initial_capital"],
                                  allocation_fraction=params["allocation_fraction"])
            total = result.final_equity - Decimal(100)
            assert (f"| {pair} | {strategy.name} | {result.quote_currency} | {len(result.closed_trades)} | "
                    f"{'Sí' if result.open_position else 'No'} | {result.final_equity:.6f} | "
                    f"{total:.6f} | {total:.6f} | {result.max_drawdown_percent:.6f} | "
                    f"{result.total_costs:.6f} | {result.rejected_entries} |") in report
    original = output.read_bytes()
    main(args)
    assert output.read_bytes() == original


def test_comparison_with_insufficient_data_stays_in_cash(source):
    report = build_comparison_report(source)
    for name in ("SMA20/SMA60", "EMA20/EMA60"):
        assert f"| EUR/USD | {name} | USD | 0 | No | 1000.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 |" in report


@pytest.mark.parametrize("options", [["--report", "--compare"], ["--compare", "--strategy", "ema"],
                                     ["--compare", "--strategy", "sma"], ["--compare", "--fast-window", "60"]])
def test_cli_incompatible_or_invalid_options_fail_before_io(tmp_path, options):
    output = tmp_path / "comparison.md"
    with pytest.raises(SystemExit) as error:
        main(options + ["--data", str(tmp_path / "missing.xml"), "--output", str(output)])
    assert error.value.code == 2 and not output.exists()


def test_default_comparison_output_is_separate(source, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["--compare", "--data", str(source)])
    assert (tmp_path / "reports/comparison.md").exists()
    assert not (tmp_path / "reports/report.md").exists()


def test_comparison_protects_source_and_existing_output(source, tmp_path):
    original = source.read_bytes()
    with pytest.raises(ValueError, match="archivo de datos"):
        write_comparison_report(source, source)
    assert source.read_bytes() == original
    output = tmp_path / "notes.md"
    output.write_text("Mis notas", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_comparison_report(source, output)
    assert output.read_text(encoding="utf-8") == "Mis notas"


@pytest.mark.parametrize("params", [{"fast_window": 60}, {"cost_rate": Decimal(-1)},
                                    {"initial_capital": Decimal(0)}, {"allocation_fraction": Decimal(2)}])
def test_comparison_rejects_invalid_assumptions_before_io(tmp_path, params):
    with pytest.raises(ValueError):
        build_comparison_report(tmp_path / "missing.xml", **params)


def test_comparison_detects_changed_data(source, monkeypatch):
    from trading_ai import reporting

    original_loader = reporting.load_ecb_rates

    def changing_loader(path, pair):
        rates = original_loader(path, pair)
        path.write_bytes(path.read_bytes() + b"\n")
        return rates

    monkeypatch.setattr(reporting, "load_ecb_rates", changing_loader)
    with pytest.raises(ValueError, match="cambió"):
        build_comparison_report(source)
