"""Señales deterministas de cruce; no gestionan posiciones ni envían órdenes."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Protocol

from trading_ai.indicators import exponential_moving_average, simple_moving_average


class Signal(Enum):
    """Intención de una estrategia de compra y cierre, sin posiciones cortas."""

    NONE = "none"
    ENTER_LONG = "enter_long"
    EXIT_LONG = "exit_long"


def validate_crossover_windows(fast_window: int, slow_window: int) -> None:
    """Exige ventanas enteras positivas, con rápida menor que lenta."""
    for name, window in (("rápida", fast_window), ("lenta", slow_window)):
        if isinstance(window, bool) or not isinstance(window, int):
            raise TypeError(f"La ventana {name} debe ser un entero positivo.")
        if window <= 0:
            raise ValueError(f"La ventana {name} debe ser mayor que cero.")
    if fast_window >= slow_window:
        raise ValueError("La ventana rápida debe ser menor que la lenta.")


class Strategy(Protocol):
    """Contrato de estrategias: una señal por precio, sin usar precios futuros.

    Los precios llegan en orden cronológico. La estrategia no modifica la entrada
    ni mantiene posiciones: ejecución, capital y costes pertenecen al backtest.
    Cada implementación debe verificar su causalidad mediante pruebas.
    """

    @property
    def name(self) -> str: ...

    def generate_signals(self, prices: Sequence[Decimal]) -> list[Signal]: ...


@dataclass(frozen=True)
class SmaCrossoverStrategy:
    """Configuración inmutable del cruce SMA; cumple Strategy sin heredar de él."""

    fast_window: int = 20
    slow_window: int = 60

    def __post_init__(self) -> None:
        validate_crossover_windows(self.fast_window, self.slow_window)

    @property
    def name(self) -> str:
        return f"SMA{self.fast_window}/SMA{self.slow_window}"

    def generate_signals(self, prices: Sequence[Decimal]) -> list[Signal]:
        return moving_average_crossover_signals(
            simple_moving_average(prices, self.fast_window),
            simple_moving_average(prices, self.slow_window),
        )


@dataclass(frozen=True)
class EmaCrossoverStrategy:
    """Cruce de EMA con semilla SMA; configuración inmutable y cálculo sin estado."""

    fast_window: int = 20
    slow_window: int = 60

    def __post_init__(self) -> None:
        validate_crossover_windows(self.fast_window, self.slow_window)

    @property
    def name(self) -> str:
        return f"EMA{self.fast_window}/EMA{self.slow_window}"

    def generate_signals(self, prices: Sequence[Decimal]) -> list[Signal]:
        return moving_average_crossover_signals(
            exponential_moving_average(prices, self.fast_window),
            exponential_moving_average(prices, self.slow_window),
        )


def create_strategy(name: str, fast_window: int = 20, slow_window: int = 60) -> Strategy:
    """Selecciona una implementación conocida; rechaza nombres no admitidos."""
    if name == "sma":
        return SmaCrossoverStrategy(fast_window, slow_window)
    if name == "ema":
        return EmaCrossoverStrategy(fast_window, slow_window)
    raise ValueError(f"Estrategia no admitida: {name}. Opciones: sma, ema.")


def moving_average_crossover_signals(
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


# Compatibilidad con los nombres públicos usados en los primeros ejercicios.
validate_sma_windows = validate_crossover_windows
sma_crossover_signals = moving_average_crossover_signals
