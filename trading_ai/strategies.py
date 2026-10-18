"""Señales deterministas de cruce; no gestionan posiciones ni envían órdenes."""

from collections.abc import Sequence
from decimal import Decimal
from enum import Enum


class Signal(Enum):
    """Intención de una estrategia de compra y cierre, sin posiciones cortas."""

    NONE = "none"
    ENTER_LONG = "enter_long"
    EXIT_LONG = "exit_long"


def sma_crossover_signals(
    fast: Sequence[Decimal | None], slow: Sequence[Decimal | None]
) -> list[Signal]:
    """Compara las medias actual y anterior, conservando longitud y orden.

    Requiere series alineadas por fecha y ordenadas cronológicamente. Un cruce
    alcista pasa de fast <= slow a fast > slow; el bajista, de >= a <.
    Si falta cualquiera de las cuatro medias necesarias, no emite señal.
    No infiere un cruce al empezar ni salta huecos. Una igualdad actual no
    emite señal. Los eventos no dependen de si existe una posición abierta.
    """
    if len(fast) != len(slow):
        raise ValueError("Las dos series de medias deben tener la misma longitud.")
    for name, values in (("rápida", fast), ("lenta", slow)):
        for index, value in enumerate(values):
            if value is None:
                continue
            if not isinstance(value, Decimal):
                raise TypeError(f"Media {name}, posición {index}: se requiere Decimal o None.")
            if not value.is_finite():
                raise ValueError(f"Media {name}, posición {index}: se requiere un valor finito.")

    signals = [Signal.NONE] * len(fast)
    for index in range(1, len(fast)):
        previous_fast, previous_slow = fast[index - 1], slow[index - 1]
        current_fast, current_slow = fast[index], slow[index]
        if (previous_fast is None or previous_slow is None
                or current_fast is None or current_slow is None):
            continue
        if previous_fast <= previous_slow and current_fast > current_slow:
            signals[index] = Signal.ENTER_LONG
        elif previous_fast >= previous_slow and current_fast < current_slow:
            signals[index] = Signal.EXIT_LONG
    return signals
