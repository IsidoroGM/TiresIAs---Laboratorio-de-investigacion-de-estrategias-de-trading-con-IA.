"""Pruebas sin red con referencias pequeñas y resultados conocidos."""

from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from trading_ai.data import load_ecb_rates


RATES = ('<Cube currency="USD" rate="1.2"/>'
         '<Cube currency="GBP" rate="0.8"/>'
         '<Cube currency="JPY" rate="120"/>'
         '<Cube currency="CHF" rate="0.96"/>')


def write_xml(tmp_path: Path, days: str) -> Path:
    path = tmp_path / "rates.xml"
    path.write_text(
        '<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
        f'<Cube>{days}</Cube></Envelope>', encoding="utf-8"
    )
    return path


@pytest.mark.parametrize("pair, expected", [
    ("EUR/USD", "1.2"), ("GBP/USD", "1.5"),
    ("USD/JPY", "100"), ("USD/CHF", "0.8"),
])
def test_known_conversions(tmp_path, pair, expected):
    path = write_xml(tmp_path, f'<Cube time="2026-10-16">{RATES}</Cube>')
    assert load_ecb_rates(path, pair) == [(date(2026, 10, 16), Decimal(expected))]


def test_orders_dates_and_uses_rates_from_same_day(tmp_path):
    older = RATES.replace('rate="1.2"', 'rate="1.6"')
    path = write_xml(tmp_path,
                     f'<Cube time="2026-10-16">{RATES}</Cube>'
                     f'<Cube time="2026-10-14">{older}</Cube>')
    assert load_ecb_rates(str(path), "GBP/USD") == [
        (date(2026, 10, 14), Decimal("2")),
        (date(2026, 10, 16), Decimal("1.5")),
    ]  # No inventa una observación para el día 15.


@pytest.mark.parametrize("value", ["0", "-1", "NaN", "Infinity", "-Infinity", "abc", ""])
def test_rejects_invalid_rate(tmp_path, value):
    rates = RATES.replace('rate="1.2"', f'rate="{value}"')
    path = write_xml(tmp_path, f'<Cube time="2026-10-16">{rates}</Cube>')
    with pytest.raises(ValueError, match="referencia USD"):
        load_ecb_rates(path, "USD/JPY")


@pytest.mark.parametrize("usd", ["", '<Cube currency="USD"/>',
    '<Cube currency="USD" rate="1.2"/><Cube currency="USD" rate="1.3"/>'])
def test_rejects_missing_or_duplicate_required_rate(tmp_path, usd):
    rates = RATES.replace('<Cube currency="USD" rate="1.2"/>', usd)
    path = write_xml(tmp_path, f'<Cube time="2026-10-16">{rates}</Cube>')
    with pytest.raises(ValueError, match="USD"):
        load_ecb_rates(path, "EUR/USD")


@pytest.mark.parametrize("raw_date", ["2026-02-30", "", "20261016", "ayer"])
def test_rejects_invalid_date(tmp_path, raw_date):
    path = write_xml(tmp_path, f'<Cube time="{raw_date}">{RATES}</Cube>')
    with pytest.raises(ValueError, match="Fecha inválida"):
        load_ecb_rates(path, "EUR/USD")


def test_rejects_duplicate_date(tmp_path):
    day = f'<Cube time="2026-10-16">{RATES}</Cube>'
    path = write_xml(tmp_path, day + day)
    with pytest.raises(ValueError, match="Fecha duplicada"):
        load_ecb_rates(path, "EUR/USD")


def test_rejects_unsupported_pair_before_reading(tmp_path):
    with pytest.raises(ValueError, match="Par no admitido"):
        load_ecb_rates(tmp_path / "not_present.xml", "EUR/JPY")


def test_rejects_empty_dataset(tmp_path):
    with pytest.raises(ValueError, match="no contiene observaciones"):
        load_ecb_rates(write_xml(tmp_path, ""), "EUR/USD")


def test_rejects_malformed_xml(tmp_path):
    path = tmp_path / "broken.xml"
    path.write_text("<Envelope>", encoding="utf-8")
    with pytest.raises(ValueError, match="XML inválido"):
        load_ecb_rates(path, "EUR/USD")


def test_missing_file_keeps_os_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_ecb_rates(tmp_path / "not_present.xml", "EUR/USD")


def test_only_requires_currencies_for_selected_pair(tmp_path):
    path = write_xml(tmp_path, '<Cube time="2026-10-16">'
                     '<Cube currency="USD" rate="1.2"/></Cube>')
    assert load_ecb_rates(path, "EUR/USD")[0][1] == Decimal("1.2")
    with pytest.raises(ValueError, match="GBP"):
        load_ecb_rates(path, "GBP/USD")


def test_conversion_precision_is_independent_of_caller(tmp_path):
    rates = RATES.replace('rate="1.2"', 'rate="3"').replace('rate="0.96"', 'rate="1"')
    path = write_xml(tmp_path, f'<Cube time="2026-10-16">{rates}</Cube>')
    with localcontext() as context:
        context.prec = 3
        assert load_ecb_rates(path, "USD/CHF")[0][1] == Decimal("0.3333333333333333333333333333")
        assert context.prec == 3
