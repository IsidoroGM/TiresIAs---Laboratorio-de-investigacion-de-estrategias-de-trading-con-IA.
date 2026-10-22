"""Reglas declarativas acotadas: señales puras, sin código del modelo ni gestión de dinero."""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import operator
from pathlib import Path
import re

from trading_ai.indicators import (_validate_inputs, exponential_moving_average,
                                   simple_moving_average)
from trading_ai.strategies import Signal


MAX_SPEC_BYTES = 16384
MAX_CONDITIONS = 4
MAX_WINDOW = 252
MAX_LAG = 252
SERIES = ("reference", "sma", "ema", "rolling_min", "rolling_max")
COMPARISONS = {"gt": operator.gt, "gte": operator.ge, "lt": operator.lt,
               "lte": operator.le, "eq": operator.eq}
OPERATORS = (*COMPARISONS, "crosses_above", "crosses_below")


def _object(properties: dict) -> dict:
    return {"type": "object", "additionalProperties": False, "properties": properties,
            "required": list(properties)}


_lag_schema = {"type": "integer", "minimum": 0, "maximum": MAX_LAG}
_operand_schema = {"oneOf": [
    _object({"kind": {"const": "reference"}, "lag": _lag_schema}),
    _object({"kind": {"enum": ["sma", "ema", "rolling_min", "rolling_max"]},
             "window": {"type": "integer", "minimum": 1, "maximum": MAX_WINDOW}, "lag": _lag_schema}),
    _object({"kind": {"const": "constant"}, "value": {"type": "string", "minLength": 1, "maxLength": 48}}),
]}
_condition_schema = _object({"left": _operand_schema, "operator": {"enum": list(OPERATORS)}, "right": _operand_schema})
_group_schema = _object({"match": {"enum": ["all", "any"]},
                         "conditions": {"type": "array", "minItems": 1, "maxItems": MAX_CONDITIONS,
                                        "items": _condition_schema}})
RULE_SCHEMA = _object({"schema_version": {"type": "integer", "const": 1},
                       "name": {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,63}$"},
                       "entry": _group_schema, "exit": _group_schema})


@dataclass(frozen=True)
class _Operand:
    kind: str
    window: int = 1
    lag: int = 0
    value: Decimal | None = None


@dataclass(frozen=True)
class _Condition:
    left: _Operand
    operator: str
    right: _Operand


@dataclass(frozen=True)
class _Group:
    match: str
    conditions: tuple[_Condition, ...]


def _fields(value, required: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(f"{label}: campos ausentes o no autorizados.")


def _integer(value, minimum: int, maximum: int, label: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{label} debe ser un entero entre {minimum} y {maximum}.")
    return value


def _operand(value) -> _Operand:
    if not isinstance(value, dict):
        raise ValueError("El operando debe ser un objeto declarativo.")
    kind = value.get("kind")
    if kind == "constant":
        _fields(value, {"kind", "value"}, "Constante")
        text = value["value"]
        if not isinstance(text, str) or not 1 <= len(text) <= 48:
            raise ValueError("La constante debe ser un decimal como texto de hasta 48 caracteres.")
        if re.fullmatch(r"[+-]?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", text) is None:
            raise ValueError("Formato de constante decimal no admitido.")
        try:
            constant = Decimal(text)
        except InvalidOperation as error:
            raise ValueError("Constante decimal inválida.") from error
        if (not constant.is_finite() or constant.copy_abs() > Decimal("1000000")
                or len(constant.as_tuple().digits) > 28 or not -28 <= constant.as_tuple().exponent <= 28):
            raise ValueError("Constante fuera de los límites de precisión o magnitud.")
        return _Operand(kind, value=constant)
    if not isinstance(kind, str) or kind not in SERIES:
        raise ValueError("Serie no admitida; no se permiten datos externos ni expresiones libres.")
    required = {"kind", "lag"} if kind == "reference" else {"kind", "window", "lag"}
    _fields(value, required, "Serie")
    lag = _integer(value["lag"], 0, MAX_LAG, "lag")
    window = 1 if kind == "reference" else _integer(value["window"], 1, MAX_WINDOW, "window")
    return _Operand(kind, window, lag)


def _group(value) -> _Group:
    _fields(value, {"match", "conditions"}, "Grupo")
    if value["match"] not in ("all", "any"):
        raise ValueError("El grupo debe usar all o any.")
    conditions = value["conditions"]
    if not isinstance(conditions, list) or not 1 <= len(conditions) <= MAX_CONDITIONS:
        raise ValueError(f"Cada grupo requiere entre 1 y {MAX_CONDITIONS} condiciones, sin anidamiento.")
    parsed = []
    for condition in conditions:
        _fields(condition, {"left", "operator", "right"}, "Condición")
        name = condition["operator"]
        if not isinstance(name, str) or name not in OPERATORS:
            raise ValueError("Operación no admitida.")
        parsed.append(_Condition(_operand(condition["left"]), name, _operand(condition["right"])))
    return _Group(value["match"], tuple(parsed))


def _specification(spec) -> tuple[str, _Group, _Group]:
    _fields(spec, {"schema_version", "name", "entry", "exit"}, "Especificación")
    if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
        raise ValueError("Versión de reglas no admitida.")
    if not isinstance(spec["name"], str) or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", spec["name"]) is None:
        raise ValueError("name debe ser un identificador de hasta 64 caracteres en minúsculas.")
    return spec["name"], _group(spec["entry"]), _group(spec["exit"])


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("No se admiten claves JSON repetidas.")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"Literal JSON no admitido: {value}.")


def _parse_json(text: str) -> dict:
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_SPEC_BYTES:
        raise ValueError("La especificación debe ser JSON de hasta 16384 bytes.")
    try:
        return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
    except RecursionError as error:
        raise ValueError("Anidamiento JSON no admitido.") from error


def _series(operand: _Operand, prices: Sequence[Decimal]) -> list[Decimal | None]:
    if operand.kind == "constant":
        return [operand.value] * len(prices)
    if operand.kind == "reference":
        values = list(prices)
    elif operand.kind == "sma":
        values = simple_moving_average(prices, operand.window)
    elif operand.kind == "ema":
        values = exponential_moving_average(prices, operand.window)
    else:
        choose = min if operand.kind == "rolling_min" else max
        values = [None] * len(prices)
        for index in range(operand.window - 1, len(prices)):
            values[index] = choose(prices[index - operand.window + 1:index + 1])
    return [None if index < operand.lag else values[index - operand.lag] for index in range(len(prices))]


def _evaluate(group: _Group, cache: dict, index: int) -> bool | None:
    checks = []
    for condition in group.conditions:
        first, second = cache[condition.left], cache[condition.right]
        left, right = first[index], second[index]
        if left is None or right is None:
            return None
        if condition.operator in COMPARISONS:
            checks.append(COMPARISONS[condition.operator](left, right))
        else:
            if index == 0 or first[index - 1] is None or second[index - 1] is None:
                return None
            if condition.operator == "crosses_above":
                checks.append(first[index - 1] <= second[index - 1] and left > right)
            else:
                checks.append(first[index - 1] >= second[index - 1] and left < right)
    return all(checks) if group.match == "all" else any(checks)


@dataclass(frozen=True)
class RuleStrategy:
    """Strategy inmutable: JSON validado, series causales y prioridad fija de salida."""

    spec_json: str = field(repr=False)
    _identifier: str = field(init=False)
    _entry: _Group = field(init=False, repr=False)
    _exit: _Group = field(init=False, repr=False)

    def __post_init__(self):
        spec = _parse_json(self.spec_json)
        identifier, entry, exit_rule = _specification(spec)
        canonical = json.dumps(spec, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        object.__setattr__(self, "spec_json", canonical)
        object.__setattr__(self, "_identifier", identifier)
        object.__setattr__(self, "_entry", entry)
        object.__setattr__(self, "_exit", exit_rule)

    @property
    def name(self) -> str:
        return "RULE:" + self._identifier

    @property
    def spec_sha256(self) -> str:
        return sha256(self.spec_json.encode("utf-8")).hexdigest()

    def to_spec(self) -> dict:
        return json.loads(self.spec_json)

    def generate_signals(self, prices: Sequence[Decimal]) -> list[Signal]:
        _validate_inputs(prices, 1)
        operands = {operand for group in (self._entry, self._exit)
                    for condition in group.conditions for operand in (condition.left, condition.right)}
        cache = {operand: _series(operand, prices) for operand in operands}
        signals = []
        for index in range(len(prices)):
            entry, exit_rule = _evaluate(self._entry, cache, index), _evaluate(self._exit, cache, index)
            if entry is None or exit_rule is None:
                signals.append(Signal.NONE)
            elif exit_rule:
                signals.append(Signal.EXIT_LONG)
            elif entry:
                signals.append(Signal.ENTER_LONG)
            else:
                signals.append(Signal.NONE)
        return signals


def compile_rule_strategy(spec: dict) -> RuleStrategy:
    """Compila únicamente el vocabulario conocido; no traduce ideas en lenguaje natural."""
    _specification(spec)
    return RuleStrategy(json.dumps(spec, sort_keys=True, ensure_ascii=False, allow_nan=False))


def load_rule_strategy(path: str | Path) -> RuleStrategy:
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_SPEC_BYTES + 1)
    if len(raw) > MAX_SPEC_BYTES:
        raise ValueError("La especificación supera 16384 bytes.")
    return RuleStrategy(raw.decode("utf-8"))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — validar reglas declarativas sin backtest ni IA")
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        strategy = load_rule_strategy(args.spec)
    except (ValueError, TypeError, OSError) as error:
        parser.exit(1, f"Reglas rechazadas: {error}\n")
    print(f"Reglas válidas: {strategy.name}. SHA-256: {strategy.spec_sha256}")
    print("Sin ejecutar backtests ni validar rentabilidad; el simulador conserva los controles.")


if __name__ == "__main__":
    main()
