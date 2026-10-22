"""Lectura local de referencias educativas del BCE; no descarga ni opera."""

from datetime import date
from decimal import Context, Decimal, InvalidOperation, localcontext
from pathlib import Path
import xml.etree.ElementTree as ET


SUPPORTED_PAIRS = ("EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF")
_NAMESPACE = {"ecb": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}


def _read_rate(day: ET.Element, currency: str, day_date: date) -> Decimal:
    """Obtiene una única referencia positiva para la moneda y fecha indicadas."""
    if currency == "EUR":
        return Decimal("1")

    nodes = day.findall(f"ecb:Cube[@currency='{currency}']", _NAMESPACE)
    if len(nodes) != 1:
        raise ValueError(f"{day_date}: se requiere una única referencia {currency}.")
    try:
        rate = Decimal(nodes[0].attrib["rate"])
    except (KeyError, InvalidOperation) as error:
        raise ValueError(f"{day_date}: referencia {currency} inválida.") from error
    if not rate.is_finite() or rate <= 0:
        raise ValueError(f"{day_date}: referencia {currency} debe ser finita y positiva.")
    return rate


def load_ecb_rates(path: str | Path, pair: str) -> list[tuple[date, Decimal]]:
    """Devuelve (fecha, unidades de cotizada por unidad base), en orden ascendente.

    Acepta los cuatro pares de SUPPORTED_PAIRS. Valida las monedas necesarias
    para el par solicitado y rechaza fechas repetidas o datos inválidos con
    ValueError. Los errores de acceso al archivo se propagan como OSError.
    Los cocientes usan 28 dígitos significativos, sin redondear a pips.
    No rellena fechas ausentes ni comprueba el calendario de publicación.
    """
    if pair not in SUPPORTED_PAIRS:
        raise ValueError(f"Par no admitido: {pair}. Opciones: {', '.join(SUPPORTED_PAIRS)}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise ValueError(f"XML inválido: {path}") from error

    days = root.findall("./ecb:Cube/ecb:Cube", _NAMESPACE)
    if not days:
        raise ValueError("El archivo no contiene observaciones diarias del BCE.")

    base, quote = pair.split("/")
    observations: list[tuple[date, Decimal]] = []
    seen_dates: set[date] = set()
    with localcontext(Context(prec=28)):
        for day in days:
            raw_date = day.get("time", "")
            try:
                day_date = date.fromisoformat(raw_date)
                if day_date.isoformat() != raw_date:
                    raise ValueError("Se requiere YYYY-MM-DD.")
            except ValueError as error:
                raise ValueError(f"Fecha inválida: {raw_date!r}; se requiere YYYY-MM-DD.") from error
            if day_date in seen_dates:
                raise ValueError(f"Fecha duplicada: {day_date}.")
            seen_dates.add(day_date)

            base_rate = _read_rate(day, base, day_date)
            quote_rate = _read_rate(day, quote, day_date)
            observations.append((day_date, quote_rate / base_rate))

    return sorted(observations, key=lambda observation: observation[0])
