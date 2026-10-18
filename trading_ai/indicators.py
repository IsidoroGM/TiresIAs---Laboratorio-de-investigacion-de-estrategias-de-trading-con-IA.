"""Indicadores deterministas sobre observaciones ordenadas cronológicamente."""

from collections.abc import Sequence
from decimal import Context, Decimal, localcontext


def simple_moving_average(
    values: Sequence[Decimal], window: int
) -> list[Decimal | None]:
    """Promedia la observación actual y las anteriores de cada ventana completa.

    Conserva longitud y orden; devuelve None mientras falten observaciones.
    Una entrada vacía devuelve []; si window supera la longitud, todos son None.
    Requiere una ventana entera positiva (no bool) y valores Decimal finitos.
    Admite cero y negativos: es un promedio genérico, no un validador de precios.
    Usa 28 dígitos significativos, sin modificar la entrada ni el contexto externo.
    El llamante debe proporcionar los valores del más antiguo al más reciente.
    """
    if isinstance(window, bool) or not isinstance(window, int):
        raise TypeError("La ventana debe ser un entero positivo, no un booleano.")
    if window <= 0:
        raise ValueError("La ventana debe ser mayor que cero.")
    for index, value in enumerate(values):
        if not isinstance(value, Decimal):
            raise TypeError(f"El valor en la posición {index} debe ser Decimal.")
        if not value.is_finite():
            raise ValueError(f"El valor en la posición {index} debe ser finito.")

    averages: list[Decimal | None] = [None] * len(values)
    with localcontext(Context(prec=28)):
        for index in range(window - 1, len(values)):
            # El límite derecho del slice es exclusivo: incluye el valor actual.
            current_window = values[index - window + 1 : index + 1]
            averages[index] = sum(current_window, Decimal("0")) / window
    return averages
