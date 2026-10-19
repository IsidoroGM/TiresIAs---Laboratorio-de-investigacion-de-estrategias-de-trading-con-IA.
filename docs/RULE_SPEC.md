# Reglas declarativas — versión 1

Este formato convierte condiciones explícitas en señales calculables. Es una
herramienta para el investigador, no una estrategia elegida por el desarrollador
ni una garantía de utilidad. `trading_ai.rules` compila JSON a una implementación
del contrato `Strategy`, sin interpretar Python ni ejecutar texto del modelo.
Los módulos anteriores de estrategias, indicadores y simulación no se modifican.

## Documento y ejemplo técnico

El objeto contiene exactamente `schema_version: 1`, `name`, `entry` y `exit`.
`name` es un identificador de hasta 64 caracteres: letra minúscula inicial,
seguida de minúsculas, números o guiones bajos.

Cada grupo contiene `match` (`all` o `any`) y entre una y cuatro `conditions`.
No hay grupos anidados. `all` exige todas las condiciones; `any` exige alguna,
una vez disponible toda la historia necesaria. Cada condición tiene exactamente
`left`, `operator` y `right`. Ambos lados son operandos del vocabulario siguiente.

El [ejemplo JSON](../config/rules.example.json) reproduce SMA20/60 para comprobar
compatibilidad. No es una propuesta nueva ni se considera mejor. Validación:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.rules --spec config/rules.example.json
```

La CLI muestra nombre y hash, sin leer precios, ejecutar backtests, consultar IA
o iniciar servicios. Capital, costes, cantidad y credenciales no son campos del
documento: siguen perteneciendo al simulador y a sus controles.

## Operandos

| `kind` | Campos exactos | Valor en la observación `t` |
|---|---|---|
| `reference` | `kind`, `lag` | Referencia de `t - lag` |
| `sma` | `kind`, `window`, `lag` | SMA de la ventana terminada en `t - lag` |
| `ema` | `kind`, `window`, `lag` | EMA disponible en `t - lag`, con semilla SMA |
| `rolling_min` | `kind`, `window`, `lag` | Mínimo de la ventana terminada en `t - lag` |
| `rolling_max` | `kind`, `window`, `lag` | Máximo de la ventana terminada en `t - lag` |
| `constant` | `kind`, `value` | Decimal fijo expresado como texto |

`window` admite enteros de 1 a 252 observaciones y `lag` de 0 a 252. Se rechazan
booleanos como enteros, desplazamientos negativos y datos futuros. Las ventanas
incluyen su observación final: un máximo con `lag: 0` incluye la referencia
actual; con `lag: 1` usa una ventana terminada en la observación anterior.

Una constante es texto decimal finito de hasta 48 caracteres y 28 dígitos,
valor absoluto máximo 1.000.000 y exponente Decimal entre −28 y 28. Ejemplo:
`{"kind":"constant","value":"1.25"}`. Se rechazan expresiones, `NaN`, infinito
y números JSON aproximados como valor de constante.

OHLC, volumen, RSI y datos externos no forman parte del vocabulario inicial.
Una idea que los necesite permanece pendiente de herramientas o datos; no se
sustituye su significado por otra regla.

## Operaciones

| `operator` | Condición |
|---|---|
| `gt`, `gte` | Izquierda mayor, o mayor/igual, que derecha |
| `lt`, `lte` | Izquierda menor, o menor/igual, que derecha |
| `eq` | Igualdad decimal exacta |
| `crosses_above` | Antes izquierda ≤ derecha; ahora izquierda > derecha |
| `crosses_below` | Antes izquierda ≥ derecha; ahora izquierda < derecha |

Los cruces necesitan los valores actuales y anteriores de ambos operandos. No
se infiere un cruce al aparecer el primer valor ni se salta historia ausente.
Las comparaciones son exactas, sin tolerancia o redondeo añadidos.

## Historia y prioridad

Mientras falte historia para cualquier condición de entrada **o de salida**,
la señal es `NONE`. Un cruce también necesita la observación anterior válida.
La regla es conservadora: impide entrar antes de poder comprobar la salida y
que un grupo `any` eluda el calentamiento de sus otras condiciones. Cada
periodo reinicia indicadores según el [protocolo de validación](VALIDATION_PLAN.md).

Cuando todos los valores necesarios están disponibles, si coinciden entrada
y salida tiene prioridad fija **salir**. El modelo no puede cambiarla. Una
salida estando fuera se ignora en el simulador; no abre cortos.

Se produce una señal por observación, sin mantener posiciones o estado entre
llamadas. Puede haber señales repetidas: el simulador decide cuáles aplicar.
Una condición ordinaria sin historia puede producir señal en la primera
observación. Las reglas solo forman señales; la ejecución sigue ocurriendo en
la siguiente referencia, dentro del motor existente. No se trasladan cuentas,
posiciones ni señales de un periodo a otro por usar este formato.

## API y validación

```python
from trading_ai.rules import compile_rule_strategy, load_rule_strategy

strategy = load_rule_strategy("config/rules.example.json")
# O bien: strategy = compile_rule_strategy(specification_dict)
signals = strategy.generate_signals(decimal_prices)
```

Una herramienta Python autorizada puede suministrar esas señales a
`run_backtest` con sus controles. La CLI de reglas solo valida. Las
[propuestas de traducción](FORMALIZATION.md) vinculan ideas a especificaciones
pendientes de revisión; no invocan esta API para generar señales o simular.

La estrategia compilada y sus condiciones son inmutables. `to_spec()` devuelve
una copia; `spec_sha256` identifica el JSON canónico, sin depender del orden
de sus claves. No detecta equivalencias semánticas entre reglas diferentes.

Se rechazan campos desconocidos, versiones distintas, operadores no permitidos,
anidamiento, valores fuera de límites y claves JSON repetidas. Los archivos se
limitan a 16.384 bytes. `RULE_SCHEMA` expone el contrato para la integración
posterior; Python aplica también restricciones como precisión decimal y tipos
exactos que el esquema no expresa completamente.

`generate_signals` recibe `Decimal` finitos y no modifica entrada ni contexto
Decimal exterior. Como los indicadores existentes, admite valores genéricos;
el lector y el backtest siguen exigiendo referencias positivas para simular.

Validar establece un significado computable dentro del vocabulario. No prueba
utilidad, novedad, cierres suficientes, robustez ni rentabilidad. Una condición
que nunca se cumpla puede seguir siendo una regla bien definida.

## Integración con ideas

La bandeja `discovery` conserva los borradores sin ejecutar y el contrato de
experimentos SMA/EMA permanece igual. `formalization` registra una propuesta
vinculada o una duda, sin modificar la idea original. Python comprueba estructura
y procedencia; la equivalencia de significado sigue pendiente incluso cuando
las reglas compilan. La [revisión técnica y el plan previo](RULE_PLANNING.md)
registran esa comprobación declarada y límites fijos. La ejecución corresponde
al [ejecutor separado](RULE_EXECUTION.md), que verifica el plan y reserva un solo intento.

La comprobación original del lenguaje no consultó IA. La traducción posterior
puede consultar el modelo local, sin dependencias nuevas ni operaciones reales.
FASE 4 permanece abierta y `PROJECT_STATUS.md` conserva el cierre de FASE 3.
Este paso no autoriza commits ni pushes.
