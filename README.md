# TiresIAs - Laboratorio de investigación de estrategias de trading con IA

Proyecto educativo de investigación y trading algorítmico asistido por agentes de
IA. Se construye paso a paso para aprender Python, arquitectura modular, pruebas
automatizadas y evaluación de estrategias.

El proyecto, anteriormente llamado Trading AI, adopta el nombre **TiresIAs**.
El paquete `trading_ai`, los comandos y las rutas existentes se conservan para
mantener la compatibilidad. Los informes, registros y módulos vinculados a
evidencias anteriores mantienen sus referencias originales para preservar la
trazabilidad.

## Objetivo y alcance inicial

El primer objetivo es obtener datos históricos, validarlos y desarrollar un
backtest educativo reproducible.

- Mercado: Forex, con EUR/USD, GBP/USD, USD/JPY y USD/CHF.
- Temporalidad: D1 (diaria), con enfoque de swing trading.
- Estrategia didáctica prevista: cruce de medias móviles simples SMA20/SMA60.
- Evaluación: resultados, costes, riesgo y limitaciones de cada simulación.

La fuente de datos educativa aprobada es el Banco Central Europeo. Sus tipos de
referencia no son cotizaciones negociables ni equivalen
necesariamente al cierre diario del mercado.
EUR/USD se obtiene directamente; los otros tres pares se calculan cruzando
referencias del mismo día respecto al euro. Las fórmulas y la cobertura
comprobada se describen en [data/README.md](data/README.md).

## Estado actual

Las **FASES 0, 1, 2, 3 y 4 están completadas**. El motor incorpora costes, capital,
drawdown, tamaño por porcentaje de capital, estrategias SMA/EMA configurables,
comparación y sensibilidad local. La FASE 3 incorpora un primer
investigador local mediante Ollama; OpenAI queda previsto como proveedor futuro
desactivado. Consulta [la preparación y los controles](docs/LOCAL_AI.md).
La FASE 4 añade validación cronológica, memoria, ciclo local acotado y walk-forward
descriptivo sobre desarrollo conocido. El [cierre de fase](reports/phase4-completion-2026-10-20.md)
conserva resultados negativos y **1547 pruebas aprobadas**, sin afirmar rentabilidad
o validación independiente. La FASE 5 de interfaz es el siguiente paso y aún no se inicia.
El laboratorio produce un informe
reproducible para los cuatro pares. Están comprobados
Python 3.14.8 de 64 bits, el entorno virtual `.venv`, su uso desde la terminal de
VS Code y el repositorio Git local.

El paquete `trading_ai` dispone de un punto de entrada ejecutable que muestra la
presentación del laboratorio. Su arranque y su importación están comprobados.

La copia original, su procedencia y una muestra están en [data/README.md](data/README.md).
La descarga se realizó como preparación del ejercicio. El módulo `trading_ai.data`
lee la copia local para cualquiera de los cuatro pares y cuenta con pruebas.
El módulo `trading_ai.indicators` calcula medias móviles simples y exponenciales;
se han comprobado SMA20/60 y EMA20/60 sobre los cuatro históricos.
Todavía no hay un descargador integrado en la aplicación.

La estrategia inicial detecta cruces SMA20/SMA60 y genera señales de entrada
y salida. El backtest educativo gestiona una compra por par y registra cierres
y posiciones abiertas con ejecución en la referencia siguiente y costes
proporcionales configurables (cero por defecto).
El módulo `trading_ai.metrics` resume los cierres e indica si queda una posición abierta.
El investigador se ejecuta por separado del motor. Todavía no hay dashboard
ni conexión con un bróker. Los resultados
actuales son ejercicios con referencias informativas, no validación de viabilidad.

## Trabajar con el entorno preparado

Abre en VS Code la carpeta raíz del proyecto, que contiene este README y
`.gitignore`, y abre una terminal de PowerShell. Los siguientes comandos utilizan
el entorno `.venv` que ya está creado; ejecútalos uno por uno:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
python -c "import sys; print(sys.executable); print(sys.prefix != sys.base_prefix)"
python -m pip --version
```

Resultados esperados:

- Python muestra `3.14.8`.
- La ruta del ejecutable termina en `.venv\Scripts\python.exe` dentro del proyecto.
- La comparación de los prefijos muestra `True`: se está usando un entorno virtual.
- La ruta de `pip` pertenece a `.venv\Lib\site-packages`.

Para salir del entorno en esa terminal, ejecuta `deactivate`. También puedes
ejecutar el Python del proyecto sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe --version
```

`.venv` es local y está excluido de Git. En otra copia del repositorio será
necesario preparar su propio entorno; estas instrucciones describen el entorno
actual. Se ha incorporado pytest 9.1.1 para pruebas, junto con sus dependencias
auxiliares. Pandas y NumPy siguen pendientes. Para instalar la dependencia de
desarrollo en un entorno nuevo:

```powershell
python -m pip install -r requirements-dev.txt
```

El lector solo utiliza la biblioteca estándar y puede ejecutarse sin pytest.

## Ejecutar el laboratorio

Desde la raíz del proyecto, con el entorno virtual activo:

```powershell
python -m trading_ai
```

La salida esperada es:

```text
TiresIAs - Laboratorio de investigación de estrategias de trading con IA
FASE 2 completada - simulación educativa. Usa --report, --compare o --sensitivity.
```

`-m` busca el paquete y ejecuta su archivo `__main__.py`. También puedes ejecutar
el laboratorio sin activar previamente el entorno:

```powershell
.\.venv\Scripts\python.exe -m trading_ai
```

Para comprobar que importar el paquete no inicia el programa:

```powershell
python -c "import trading_ai; import trading_ai.__main__"
```

Este último comando debe terminar sin imprimir mensajes. La llamada a `main()`
está protegida por `if __name__ == "__main__"`, que distingue la ejecución como
programa de la importación del módulo.

## Leer el histórico y ejecutar las pruebas

Desde la raíz del proyecto y con `.venv` activo, abre la consola de Python con
`python` y ejecuta estas líneas:

```python
from trading_ai.data import load_ecb_rates

rates = load_ecb_rates("data/raw/ecb-eurofxref-hist-2026-10-18.xml", "EUR/USD")
print(len(rates))  # 7116
print(rates[0])    # (datetime.date(1999, 1, 4), Decimal('1.1789'))
print(rates[-1])   # (datetime.date(2026, 10, 16), Decimal('1.1253'))
exit()
```

Puedes sustituir el par por `GBP/USD`, `USD/JPY` o `USD/CHF`. La función no hace
peticiones de red ni modifica el archivo. Devuelve una lista de tuplas
`(fecha, valor)`, ordenada cronológicamente. Los valores son referencias
educativas expresadas en unidades de la moneda cotizada por unidad de la base.

Conceptos del lector:

- `path: str | Path` admite una ruta como texto o como objeto `Path`.
- `list[tuple[date, Decimal]]` describe el resultado: una lista de parejas de
  fecha y número decimal. Son anotaciones de tipos, no validación automática.
- `Decimal` se construye desde el texto original, evitando introducir la
  aproximación binaria de `float`. Los cocientes usan 28 dígitos significativos
  en un contexto local; no son aritmética de precisión infinita.
- `_read_rate` es un ayudante interno (el guion bajo expresa esa convención):
  obtiene la referencia de una moneda y comprueba que sea única, finita y positiva.
- `load_ecb_rates` valida el par, lee el XML con su espacio de nombres, valida
  fechas y calcula `referencia_cotizada / referencia_base` dentro de cada día.
  Para EUR se usa 1. Finalmente ordena las observaciones.
- `raise ValueError(...)` comunica datos inválidos; `raise ... from error`
  conserva la causa original. Los fallos de acceso, como `FileNotFoundError`,
  se propagan para que quien llame a la función pueda gestionarlos.

En Java, la función equivaldría a un método de servicio que devuelve una lista
de observaciones con `LocalDate` y `BigDecimal`. Aquí usamos tuplas sencillas
antes de introducir clases propias.

De vuelta en PowerShell, ejecuta:

```powershell
python -m pytest -q
```

Resultado comprobado al cerrar FASE 2: **343 passed** (26 del lector, 34 de
indicadores, 56 de estrategia, 37 del backtest, 24 de métricas, 19 de costes
y 22 de capital/drawdown, 25 de tamaño, 21 de EMA, 47 del informe/CLI,
15 de comparación y 17 de sensibilidad).
Las pruebas del lector usan XML pequeños en carpetas
temporales, sin red ni dependencia del histórico descargado. Las pruebas de los
tres informes comprueban también que su redondeo no dependa del contexto Decimal
del código que los invoque. Comprueban las
cuatro conversiones con resultados conocidos, orden y correspondencia por fecha,
datos ausentes o duplicados, números inválidos, fechas erróneas, XML vacío o
mal formado, par no admitido y archivo inexistente. También comprueban que la
precisión del llamante no altere los cocientes.

En `tests/test_data.py`, `tmp_path` proporciona una carpeta temporal de pytest;
`parametrize` ejecuta una prueba con varios casos; `assert` compara resultados y
`pytest.raises` comprueba el error esperado. Un fallo muestra el caso y la
comparación que no se cumplieron; hay que investigar la causa antes de cambiar
el resultado esperado.

Además se ejecutó el lector sobre la copia real: 7.116 observaciones por par,
desde 1999-01-04 hasta 2026-10-16, ordenadas y positivas. Todavía no se contrasta
el calendario de publicación ni se rellenan fechas ausentes.

Ejercicio: lee `USD/JPY` y muestra solo las tres primeras observaciones con
`rates[:3]`. Explica en qué moneda están expresados esos valores.

## Calcular medias móviles simples (SMA)

`simple_moving_average(values, window)` recibe una secuencia de `Decimal` en
orden cronológico y el tamaño entero positivo de la ventana. Devuelve una lista
de la misma longitud: cada posición contiene el promedio de esa observación y
las anteriores necesarias para completar la ventana. Las posiciones iniciales
sin suficientes observaciones contienen `None`, no cero.

Por ejemplo, una ventana de 3 sobre `[2, 4, 6, 8]` da `[None, None, 4, 6]`.
SMA20 y SMA60 cuentan observaciones publicadas, no días naturales.

Con el entorno activo, abre `python` desde la raíz del proyecto y ejecuta:

```python
from trading_ai.data import load_ecb_rates
from trading_ai.indicators import simple_moving_average

rates = load_ecb_rates("data/raw/ecb-eurofxref-hist-2026-10-18.xml", "EUR/USD")
values = [value for _, value in rates]
sma20 = simple_moving_average(values, 20)
sma60 = simple_moving_average(values, 60)
print(sma20[:20])  # 19 posiciones None y el primer promedio
print(rates[-1][0], f"SMA20={sma20[-1]:.6f}", f"SMA60={sma60[-1]:.6f}")
exit()
```

La última línea de resultados para esta copia debe ser:

```text
2026-10-16 SMA20=1.129060 SMA60=1.147388
```

La comprensión de lista `[value for _, value in rates]` extrae los valores de las
tuplas; `_` indica que no usamos la fecha en ese cálculo. Las fechas se conservan
en `rates`, y las posiciones coinciden con las listas de medias. `:.6f` redondea
solo la representación para mostrar seis decimales.

En `indicators.py`, `Sequence[Decimal]` permite listas o tuplas; el retorno
`list[Decimal | None]` expresa que cada elemento puede ser un decimal o la
ausencia de resultado. `enumerate` permite informar de la posición de un valor
inválido. `values[index - window + 1 : index + 1]` selecciona una ventana que
termina en la observación actual: el extremo derecho del slice es exclusivo.

Se recalcula la suma de cada ventana para que la implementación sea fácil de
seguir y no arrastre redondeos de sumas de ventanas anteriores. El coste es
proporcional al número de observaciones por el tamaño de la ventana, adecuado
para estos históricos y ventanas de 20/60. Las sumas y divisiones usan un
contexto decimal local de 28 dígitos significativos. No se modifica la entrada
ni el contexto decimal del llamante.

Una serie vacía produce `[]`; una ventana mayor que la serie produce solo
`None`. Se rechazan ventanas no enteras, booleanas o menores que 1, valores
que no sean `Decimal` y valores no finitos. Se admiten cero y negativos porque
la función es un promedio genérico; el lector valida las referencias positivas.

Las 34 pruebas nuevas comprueban resultados conocidos, alineación, entrada
vacía, datos insuficientes, ventanas 1/20/60, entradas inválidas y precisión.
También comprueban que añadir o cambiar observaciones posteriores no modifica
las medias anteriores. Puedes ejecutarlas solas con:

```powershell
python -m pytest tests/test_indicators.py -q
```

Comprobación sobre los cuatro históricos: cada serie tiene 7.116 posiciones,
con 7.097 promedios SMA20 y 7.057 promedios SMA60. Los primeros corresponden
al 1999-01-29 y 1999-03-26, respectivamente. Estos indicadores no generan
señales ni operaciones. La media de una fecha usa su referencia actual y solo
está disponible cuando esa referencia se haya publicado.

Ejercicio: antes de ejecutarlo, calcula a mano la SMA de ventana 2 sobre
`[Decimal("10"), Decimal("12"), Decimal("14"), Decimal("16")]`.
Después compara tu resultado con el de la función.

## Señales de cruce SMA20/SMA60

`trading_ai.strategies.sma_crossover_signals(fast, slow)` recibe las dos series
de medias alineadas por fecha, de la más antigua a la más reciente. Devuelve
una lista de `Signal` con igual longitud. `Signal` es una enumeración, similar
a un `enum` de Java, que limita los resultados a tres valores:

- `Signal.ENTER_LONG`: la rápida estaba por debajo o igual a la lenta y ahora
  está estrictamente por encima.
- `Signal.EXIT_LONG`: la rápida estaba por encima o igual y ahora está
  estrictamente por debajo. Representa cerrar una compra, no abrir un corto.
- `Signal.NONE`: no hay cruce o falta alguna media necesaria.

Se comparan las cuatro medias de las posiciones anterior y actual. La primera
posición nunca genera una señal; tampoco la primera con ambas medias disponibles
si en la anterior faltaba una. Con SMA60, la primera señal posible corresponde
a la observación 61. Una igualdad actual no genera señal; abandonar una igualdad
sí puede hacerlo. Los huecos no se saltan para buscar una media anterior.

Ejemplo en la consola de Python, desde la raíz del proyecto:

```python
from trading_ai.data import load_ecb_rates
from trading_ai.indicators import simple_moving_average
from trading_ai.strategies import Signal, sma_crossover_signals

rates = load_ecb_rates("data/raw/ecb-eurofxref-hist-2026-10-18.xml", "EUR/USD")
values = [value for _, value in rates]
signals = sma_crossover_signals(
    simple_moving_average(values, 20), simple_moving_average(values, 60)
)
events = [(day, signal.value) for (day, _), signal in zip(rates, signals)
          if signal != Signal.NONE]
print(events[:5])
print(sum(signal == Signal.ENTER_LONG for signal in signals))  # 69
exit()
```

`zip` recorre las observaciones y señales emparejadas por posición; `.value`
obtiene el texto de la enumeración. La función comprueba longitudes, tipos y
valores finitos, pero no recibe fechas: el llamante debe garantizar su alineación.

Comprobación del histórico descargado (7.116 posiciones por par):

| Par | Eventos de entrada | Eventos de salida |
|---|---:|---:|
| EUR/USD | 69 | 69 |
| GBP/USD | 70 | 70 |
| USD/JPY | 67 | 68 |
| USD/CHF | 71 | 71 |

Son eventos, no operaciones ejecutadas ni resultados de rentabilidad. Puede
haber una salida sin posición abierta o entradas repetidas tras tocar la
igualdad. El backtest ignora salidas estando fuera y entradas estando dentro.
No se fuerza el cierre al terminar el histórico.

Las señales solo se conocen después de publicarse la referencia actual; el
backtest procesa la señal en la observación siguiente, usando su referencia
como precio simulado. Es una simplificación educativa, no un precio negociable.
No se envían órdenes.

Las 35 pruebas de estrategia cubren cruces en ambos sentidos, igualdades,
ausencia de cruce, huecos, longitudes distintas, tipos y números inválidos,
integración con las SMA y estabilidad de las señales ante cambios en datos futuros.
Para ejecutarlas solas: `python -m pytest tests/test_strategies.py -q`.

Ejercicio: si la rápida ya estaba por encima de la lenta y sigue por encima,
¿debería aparecer otra señal de entrada? Compruébalo en las pruebas.

## Primer backtest educativo

`trading_ai.backtesting.run_backtest(rates, signals, pair)` recibe las referencias
cronológicas, las señales alineadas por posición y el nombre del par. Empieza
sin posición. Una señal en la posición `i` se procesa en la observación `i+1`,
que puede estar varios días después. La última señal no se ejecuta porque no hay
una referencia posterior.

Reglas de esta versión:

- Una sola compra abierta por par, sin posiciones
  cortas ni acumulación de entradas. Cuenta en moneda cotizada con capital
  inicial configurable (1000 por defecto), sin margen ni financiación.
  Tamaño predeterminado de una unidad base; alternativamente porcentaje del
  efectivo actual incluyendo el coste de compra.
  Si no alcanza para precio y coste, la entrada se rechaza sin dejarla pendiente.
- Entradas estando dentro y salidas estando fuera se ignoran.
- Costes proporcionales opcionales por ejecución, cero por defecto. No se
  modelan por separado spread, comisiones, slippage ni swaps reales.
- Precio simulado: referencia del BCE de la siguiente observación. Retrasar la
  ejecución evita usar la señal antes de conocerla, pero no convierte esa
  referencia en un precio ejecutable.
- Una posición abierta al final permanece abierta, sin cierre forzado. Su valor
  a la referencia actual se incluye en el capital diario y su variación se
  registra como resultado latente, separado de las métricas de cierres.
- Resultado de cada cierre: importe de venta menos importe de compra y costes
  de ambas ejecuciones, para la cantidad comprada. Se expresa en moneda cotizada;
  no es un porcentaje de rentabilidad.

Las `@dataclass(frozen=True)` representan los resultados. Una dataclass genera
el constructor y la comparación de campos, parecida a un `record` de Java;
`frozen=True` impide reasignar sus campos normalmente:

- `Position`: fecha de señal de entrada, fecha de ejecución, precio, coste y cantidad comprada.
- `Trade`: posición cerrada, fecha de señal de salida, fecha de ejecución, precio
  de venta, coste de salida y `pnl` (ganancia o pérdida después de ambos costes).
- `BacktestResult`: par, moneda cotizada, tupla de operaciones cerradas, posición
  abierta opcional, `realized_pnl`, capital inicial, curva diaria y entradas rechazadas.
- `EquityPoint`: fecha, efectivo, valor de posición, capital, drawdown absoluto y porcentual.

La variable local `position` vale `None` estando fuera y contiene una `Position`
estando dentro. El bucle lee `signals[index - 1]` y ejecuta con `rates[index]`.
Esto hace explícita la separación temporal. No modifica las entradas. Valida
longitudes, par, fechas estrictamente crecientes, precios positivos y señales
del enum. El llamante sigue siendo responsable de alinear ambas series y
seleccionar el par correcto. Los cálculos usan 28 dígitos significativos locales.

Ejemplo en la consola de Python, desde la raíz del proyecto:

```python
from trading_ai.data import load_ecb_rates
from trading_ai.indicators import simple_moving_average
from trading_ai.strategies import sma_crossover_signals
from trading_ai.backtesting import run_backtest

pair = "EUR/USD"
rates = load_ecb_rates("data/raw/ecb-eurofxref-hist-2026-10-18.xml", pair)
values = [value for _, value in rates]
signals = sma_crossover_signals(
    simple_moving_average(values, 20), simple_moving_average(values, 60)
)
result = run_backtest(rates, signals, pair)
print(len(result.closed_trades))  # 69
print(result.realized_pnl, result.quote_currency)  # 0.2616 USD
print(result.open_position)  # None
print(result.closed_trades[0])  # Fechas de señal y ejecución separadas
exit()
```

Resultados comprobados sobre la copia 1999-01-04 a 2026-10-16, SMA20/SMA60,
una unidad base por operación y costes cero (redondeados aquí a seis decimales):

| Par | Operaciones cerradas | Posición abierta al final | Resultado de cierres |
|---|---:|---|---:|
| EUR/USD | 69 | No | 0.261600 USD |
| GBP/USD | 70 | No | -0.175555 USD |
| USD/JPY | 67 | No | 44.600130 JPY |
| USD/CHF | 70 | Sí | -0.616511 CHF |

No sumar directamente monedas diferentes ni interpretar esta tabla como una
comparación de rentabilidad: son importes en monedas distintas y exposiciones diferentes;
todavía faltan costes reales y validación adicional.
El resultado USD/CHF excluye la posición abierta. No se ha optimizado la estrategia.

Las 37 pruebas nuevas comprueban ganancias, pérdidas y resultado cero conocidos,
retraso de ejecución, señales repetidas, saltos de calendario, múltiples cierres,
última señal sin ejecución, conservación de posiciones abiertas, errores de
entrada y estabilidad de cierres pasados ante datos futuros. Para ejecutarlas:

```powershell
python -m pytest tests/test_backtesting.py -q
```

Ejercicio: con referencias `[10, 12, 99, 15]` y señales
`[ENTER_LONG, NONE, EXIT_LONG, NONE]`, identifica los precios de compra y venta
y calcula el resultado. Puedes contrastarlo con la primera prueba del backtest.

## Métricas de operaciones cerradas

`trading_ai.metrics.calculate_metrics(result)` recibe el `BacktestResult` y
devuelve una dataclass inmutable `BacktestMetrics`. No ejecuta operaciones ni
valora la posición abierta. Recorre los cierres, clasifica sus resultados y
calcula las métricas con un contexto decimal local de 28 dígitos significativos.

| Campo | Significado |
|---|---|
| `pair`, `quote_currency` | Par y moneda de los importes |
| `total_trades` | Número de operaciones cerradas |
| `winning_trades`, `losing_trades`, `breakeven_trades` | Cierres con resultado positivo, negativo y cero |
| `win_rate_percent` | Ganadoras / total de cierres × 100; incluye cierres a cero en el denominador |
| `total_pnl` | Suma de ganancias y pérdidas de los cierres |
| `average_pnl` | Resultado total / número de cierres |
| `gross_profit` | Suma de resultados positivos |
| `gross_loss` | Magnitud positiva de las pérdidas acumuladas |
| `profit_factor` | `gross_profit / gross_loss`, sin unidades |
| `has_open_position` | Indica si el backtest terminó con una posición abierta |

Sin operaciones cerradas, los contadores y sumas valen cero, pero porcentaje
ganador y promedio son `None`. El profit factor es `None` siempre que no haya
pérdidas: no existe un denominador válido. Con pérdidas y ninguna ganancia,
vale cero. Una serie de cierres a cero tiene un porcentaje ganador y promedio
de cero, pero su profit factor no está disponible. `None` no debe sustituirse
por cero en un informe.

Ejemplo calculado a mano: cierres `[6, 4, -2, 0]` producen 4 operaciones,
2 ganadoras, 1 perdedora y 1 sin resultado; 50 % de aciertos, resultado total 8,
promedio 2, ganancias acumuladas 10, pérdidas de magnitud 2 y profit factor 5.

Tras obtener `result` con el ejemplo del backtest, en la consola de Python:

```python
from trading_ai.metrics import calculate_metrics

metrics = calculate_metrics(result)
print(metrics)
print(metrics.total_pnl, metrics.quote_currency)
print(metrics.win_rate_percent)  # Porcentaje de cierres ganadores, no rentabilidad
print(metrics.profit_factor)     # Puede ser None si no hay pérdidas
```

Si saliste de Python con `exit()`, vuelve a crear `result` antes de ejecutar
este ejemplo. El objeto de métricas conserva la moneda y no mezcla pares.
La función valida que cada `pnl` sea un Decimal finito y que la suma de los
cierres coincida con `realized_pnl` del backtest; rechaza resultados incoherentes.
`Decimal | None` indica un número o un resultado no disponible, como ya usamos
durante el periodo inicial de las SMA.

Resultados comprobados del histórico 1999-01-04 a 2026-10-16 con SMA20/SMA60,
una unidad base y costes cero (redondeados solo para presentación):

| Par | Ganadoras / perdedoras / cero | % ganadoras | Media por cierre | Profit factor | Posición abierta |
|---|---|---:|---:|---:|---|
| EUR/USD | 26 / 43 / 0 | 37.68 | 0.003791 USD | 1.2351 | No |
| GBP/USD | 27 / 43 / 0 | 38.57 | -0.002508 USD | 0.8823 | No |
| USD/JPY | 28 / 39 / 0 | 41.79 | 0.665674 JPY | 1.5392 | No |
| USD/CHF | 20 / 50 / 0 | 28.57 | -0.008807 CHF | 0.4223 | Sí |

Estos valores describen únicamente los cierres del modelo educativo sin costes.
La valoración de la cuenta y el drawdown están en una sección separada del informe;
estas métricas de cierres no incluyen la posición abierta. Falta validación fuera de muestra. El porcentaje de
aciertos y el profit factor no bastan para decidir si una estrategia es viable.

Las 24 pruebas nuevas cubren resultados conocidos, cierres a cero, series sin
operaciones, solo ganancias o solo pérdidas, posiciones abiertas excluidas,
moneda de los resultados, integración con el backtest, precisión y datos inválidos.
Para ejecutarlas solas:

```powershell
python -m pytest tests/test_metrics.py -q
```

Ejercicio: con cierres `[3, -1, -1, 0]`, calcula el porcentaje ganador y el profit
factor. Observa que ganar pocas veces no determina por sí solo el resultado total.

## Generar el informe completo

Desde la raíz del proyecto, con `.venv` activo:

```powershell
python -m trading_ai --report
```

Genera `reports/report.md` con el histórico local, los cuatro
pares, reglas SMA20/SMA60, métricas, posición abierta y limitaciones. Incluye el
SHA-256 de los datos. No descarga nada ni necesita dependencias nuevas.

Para elegir otras rutas:

```powershell
python -m trading_ai --report --data data/raw/ecb-eurofxref-hist-2026-10-18.xml --output reports/otro-informe.md
```

`argparse` interpreta las opciones de la terminal. `build_report(path)` conecta
lector, indicadores, estrategia, backtest y métricas, y devuelve texto Markdown.
`write_report(source, output)` lo guarda en UTF-8. Repetir el mismo contenido
está permitido; si la salida contiene otro texto, el comando pide otra ruta
mediante un error y conserva el archivo. Nunca puede sobrescribir el XML de entrada.

El informe es determinista para la misma copia y código: no añade marcas de
tiempo de ejecución ni rutas personales. Los errores de datos o escritura se
comunican en la terminal con código de salida 1. `python -m trading_ai --help`
muestra las opciones. Las 28 pruebas comprueban cifras, fuente, valores N/D,
repetición idéntica, costes, capital y tamaño configurados, CLI y conservación de archivos existentes.

## Costes hipotéticos por ejecución (FASE 2)

```powershell
python -m trading_ai --report --cost-percent 0.1 --output reports/costs-0_1pct.md
```

`0.1` significa **0,1 % en cada compra y cada venta**, no un coste total por
operación completa. Es un escenario hipotético elegido para comprobar sensibilidad,
no una tarifa de bróker ni una estimación de los costes reales de Forex.
El [informe con costes](reports/costs-0_1pct.md) compara resultados antes y después.
El [informe de FASE 1](reports/phase1.md) se conserva como registro sin costes.
El formato nuevo usa `reports/report.md` por defecto; para cambiar supuestos,
elige otro `--output` si ese archivo ya existe con contenido distinto.

En Python:

```python
from decimal import Decimal
result = run_backtest(rates, signals, pair, cost_rate=Decimal("0.001"))
```

El parámetro Python es una **fracción**: `0.001 = 0.1 %`. La CLI divide el
porcentaje entre 100. Se rechazan valores negativos, no finitos o iguales o
superiores al 100 %; Python requiere `Decimal`. No hay dependencias nuevas.

Por una unidad base, el coste en moneda cotizada es `precio × cost_rate`.
Comprar a 100 y vender a 110 con coste del 1 % produce: resultado bruto 10,
coste de entrada 1, coste de salida 1,10 y resultado neto 7,90.
Las señales ignoradas o sin ejecución no generan costes; el precio simulado
no cambia. Los costes se descuentan del resultado, no alteran las SMA.

- `Trade.pnl` y `BacktestResult.realized_pnl` son netos de costes de cierres.
- `Trade.gross_pnl` y `result.gross_realized_pnl` son resultados antes de costes.
- `result.closed_costs` suma los costes de las operaciones cerradas.
- `result.total_costs` incluye también la entrada de una posición todavía abierta.
- `result.pnl_after_incurred_costs` resta ese coste abierto de los cierres netos,
  sin valorar su variación de precio. No representa patrimonio total.

Los campos calculados usan `@property`: se leen como atributos, pero se calculan
a partir de los datos guardados, evitando mantener totales duplicados. Las nuevas
tasas y costes tienen valor predeterminado cero para conservar las llamadas anteriores.

Las métricas clasifican las operaciones por su resultado **después de costes**;
una ganadora bruta puede convertirse en perdedora. Los campos `gross_profit` y
`gross_loss` de métricas mantienen sus nombres, pero suman respectivamente pnl
positivos y negativos ya netos; no confundirlos con resultados antes de costes.
Las tablas históricas anteriores de este README siguen correspondiendo a tasa cero.

Las 19 pruebas de costes cubren importes conocidos, coste cero, cambios de signo,
posiciones abiertas, señales ignoradas, tasas inválidas, contexto decimal y el
efecto de aumentar costes. El informe registra la tasa exacta para reproducirlo.
Con `--cost-percent 0.1`, los cierres simulados resultan en 0.097081 USD (EUR/USD),
-0.390345 USD (GBP/USD), 29.313503 JPY (USD/JPY) y -0.765682 CHF (USD/CHF).
En este último, al descontar además la entrada abierta, quedan -0.766507 CHF,
sin incluir la variación de precio de esa posición.

## Capital diario y drawdown

```powershell
python -m trading_ai --report --cost-percent 0.1 --initial-capital 1000 --output reports/capital-1000-costs-0_1pct.md
```

[Informe con capital y drawdown](reports/capital-1000-costs-0_1pct.md).
Cada par tiene su propia cuenta: 1000 USD para EUR/USD, otra de 1000 USD para
GBP/USD, 1000 JPY para USD/JPY y 1000 CHF para USD/CHF. No forman una cartera
compartida ni tienen exposiciones monetarias equivalentes.

En Python, `run_backtest(..., initial_capital=Decimal("1000"))` requiere un
Decimal finito y positivo. Sin opción de asignación, el tamaño es una unidad base por compra.
La compra resta precio y coste del efectivo; la venta suma precio menos coste.
Una compra sin saldo suficiente se rechaza, no genera coste y no se reintenta
automáticamente. Una señal nueva puede volver a solicitar entrada.

Después de cada observación se guarda un `EquityPoint` en `result.equity_curve`:

- `cash`: efectivo restante.
- `position_value`: referencia actual multiplicada por la cantidad, o cero estando fuera.
- `equity`: efectivo más valor de posición.
- `drawdown`: máximo de capital alcanzado hasta entonces menos capital actual.
- `drawdown_percent`: drawdown dividido entre ese máximo, multiplicado por 100.

El capital inicial se incluye como máximo de partida. Por ejemplo, si el
capital sube a 1100 y luego baja a 990, el drawdown es 110 y el 10 %.
`result.max_drawdown` y `result.max_drawdown_percent` toman sus máximos por
separado: pueden ocurrir en fechas distintas. Sin datos, el capital final es
el inicial y los drawdowns son cero.

`result.final_equity` incluye la posición abierta valorada a la última referencia.
`result.unrealized_pnl` representa su variación de precio desde la entrada;
el coste de entrada ya está en el efectivo y no se cobra una salida inexistente.
La identidad comprobada es capital final = inicial + cierres netos − coste de
entrada abierta + variación de precio abierta, con precisión decimal de 28 dígitos.

El informe muestra el resumen de capital, rechazos y drawdown, y una tabla de
evolución con la última observación de cada año. La curva diaria completa queda
disponible en `result.equity_curve`; los máximos usan todos los días publicados,
no solo la muestra anual. No se mide drawdown intradiario ni hay gráfico todavía.

Con la copia actual y el comando anterior:

| Par | Capital final | Drawdown máximo | Drawdown máximo % |
|---|---:|---:|---:|
| EUR/USD | 1000.097081 USD | 0.341592 USD | 0.034146 |
| GBP/USD | 999.609655 USD | 0.792183 USD | 0.079189 |
| USD/JPY | 1029.313503 JPY | 39.256597 JPY | 3.890975 |
| USD/CHF | 999.231796 CHF | 0.914781 CHF | 0.091466 |

No se rechazó ninguna entrada en este escenario. Son resultados con exposición
de una unidad base: un porcentaje de caída pequeño no permite inferir que la
estrategia sea segura al aumentar el tamaño. Siguen siendo referencias educativas.
Los informes anteriores conservan sus supuestos originales y no se sobrescriben.

Las 22 pruebas nuevas verifican efectivo, valoración, costes, pérdidas abiertas,
saldo exacto e insuficiente, rechazo sin reintento, reutilización del efectivo,
drawdowns conocidos, entradas inválidas y que el futuro no altere la curva pasada.

## Tamaño por porcentaje del capital disponible

```powershell
python -m trading_ai --report --cost-percent 0.1 --initial-capital 1000 --allocation-percent 10 --output reports/allocation-10pct.md
```

[Informe con asignación del 10 %](reports/allocation-10pct.md). Sin
`--allocation-percent` se conserva el modo anterior de una unidad base.
Se admite un porcentaje mayor que cero y como máximo 100. En Python, el
equivalente es `run_backtest(..., allocation_fraction=Decimal("0.1"))`;
`None` significa una unidad fija.

El porcentaje se aplica al efectivo disponible **al ejecutar** la entrada, no
al capital inicial. Como solo compramos estando fuera, en ese momento efectivo
y capital coinciden. El presupuesto incluye el coste de entrada:

```text
presupuesto = efectivo actual × fracción asignada
cantidad = presupuesto / (precio de entrada × (1 + tasa de coste))
```

Por ejemplo, con capital 1010, asignación 10 %, precio 10 y coste 1 %:
presupuesto 101, cantidad 10, importe comprado 100 y coste 1; quedan 909 en
efectivo. Si se vende a 12, entran 120 menos coste 1,20, y el capital termina
en 1027,80. Cada nueva compra recalcula el tamaño con el saldo actualizado.

`Position.quantity` guarda las unidades base. La cantidad se mantiene hasta
el cierre: no se rebalancea diariamente. Costes, ingresos de venta, valor de
posición y resultados abiertos/cerrados utilizan esa cantidad. Se admiten
fracciones sin mínimos, lotes ni incrementos de bróker: es una simplificación.
La asignación es capital invertido, **no riesgo máximo ni stop-loss**.

`_entry_quantity` calcula la cantidad con redondeo hacia abajo y comprueba que
el importe más coste no exceda el presupuesto; si hace falta reduce la última
cifra representable. Evita gastar más de lo permitido por redondeo decimal.
El informe muestra cantidades mínima/máxima de las entradas y la cantidad
exacta de la posición abierta, además del porcentaje para reproducir el cálculo.

Con el comando anterior, sobre la misma copia histórica:

| Par | Capital final | Drawdown máximo % |
|---|---:|---:|
| EUR/USD | 1015.009331 USD | 2.508037 |
| GBP/USD | 977.844806 USD | 4.729938 |
| USD/JPY | 1029.441001 JPY | 3.674652 |
| USD/CHF | 930.922718 CHF | 7.825079 |

Las cuentas siguen separadas por moneda. La fracción de capital común permite
comparar bajo un criterio de exposición más consistente, pero no iguala la
volatilidad ni el riesgo de los pares. Los informes anteriores conservan su
modo de una unidad fija y no se sobrescriben.

Las 25 pruebas nuevas comprueban cantidades conocidas, costes dentro del
presupuesto, valoración proporcional, ganancias/pérdidas y reinversión,
compatibilidad del modo fijo, asignación del 100 %, redondeos, capital pequeño,
parámetros inválidos y causalidad. Se comprobó además el presupuesto de todas
las entradas de los cuatro históricos, sin efectivo negativo.

## Ventanas SMA configurables

`--fast-window` y `--slow-window` permiten cambiar las ventanas de la estrategia.
Por defecto siguen siendo 20 y 60. Ambas deben ser enteros positivos y la rápida
debe ser menor que la lenta; los valores inválidos se rechazan antes de leer datos.

Ejemplo con 10/40, conservando capital, costes y asignación del ejemplo anterior:

```powershell
python -m trading_ai --report --fast-window 10 --slow-window 40 --cost-percent 0.1 --initial-capital 1000 --allocation-percent 10 --output reports/sma10-40-allocation10.md
```

El informe registra las ventanas en el título, las reglas y el comando de
reproducción. Cuentan observaciones publicadas: con una ventana lenta de 40,
la primera señal posible es la observación 41 y se ejecutaría en la 42.
Si el histórico no alcanza para un cruce, no se inventan señales ni operaciones.

Las ventanas modifican las medias y, por tanto, las entradas y salidas simuladas.
Este ejemplo no selecciona una configuración ganadora ni realiza optimización.
Los informes anteriores se conservan: utiliza otro `--output` al cambiar parámetros.

## Interfaz común de estrategias

`Strategy` define un contrato con un nombre (`name`) y un método
`generate_signals(prices)`: recibe precios en orden cronológico y devuelve una
señal por observación. En Python, `Protocol` describe ese contrato; una clase
compatible no necesita heredarlo explícitamente. Es parecido a una interfaz de Java.

`SmaCrossoverStrategy` es la primera implementación. Valida sus ventanas al
crearse y su configuración es inmutable. No conserva posiciones entre llamadas:
el backtest sigue gestionando ejecuciones, capital y costes.

```python
from decimal import Decimal
from trading_ai.strategies import SmaCrossoverStrategy

strategy = SmaCrossoverStrategy(fast_window=1, slow_window=2)
signals = strategy.generate_signals([Decimal(n) for n in (3, 2, 1, 2, 3, 2, 1)])
print(strategy.name, [signal.value for signal in signals])
```

El informe utiliza esta clase y conserva los resultados y comandos anteriores.
El contrato no garantiza por sí solo que una estrategia ignore el futuro:
cada implementación debe demostrarlo con pruebas. Las de SMA comprueban que
añadir o cambiar precios posteriores no altera las señales anteriores.

## Segunda estrategia: cruce EMA

La EMA da más peso a las observaciones recientes. Nuestra implementación empieza
con la SMA de las primeras `n` observaciones y después aplica:
`alfa = 2 / (n + 1)` y `EMA = anterior + alfa × (precio - anterior)`.
Antes de completar la semilla devuelve `None`. El periodo controla el suavizado;
la EMA conserva influencia de precios anteriores a las últimas `n` observaciones.
Con `n = 1` coincide con cada precio. Se usa precisión Decimal de 28 dígitos.

`EmaCrossoverStrategy` cumple el mismo contrato que SMA. Comparte las reglas de
cruce y ejecuta la señal en la observación siguiente. No cambia capital, costes
ni tamaño. `--strategy ema` la selecciona; sin esa opción se mantiene SMA.

Comparación reproducible con ventanas 20/60, capital 1000, coste 0.1 % por
operación y asignación del 10 % del efectivo, costes incluidos:

```powershell
python -m trading_ai --report --strategy sma --fast-window 20 --slow-window 60 --cost-percent 0.1 --initial-capital 1000 --allocation-percent 10 --output reports/sma20-60-allocation10.md
python -m trading_ai --report --strategy ema --fast-window 20 --slow-window 60 --cost-percent 0.1 --initial-capital 1000 --allocation-percent 10 --output reports/ema20-60-allocation10.md
```

Resultados sobre la misma copia BCE, del 1999-01-04 al 2026-10-16:

| Par | Capital final SMA | Capital final EMA | Drawdown máximo SMA % | Drawdown máximo EMA % |
|---|---:|---:|---:|---:|
| EUR/USD | 1015.009331 USD | 1013.740017 USD | 2.508037 | 3.627450 |
| GBP/USD | 977.844806 USD | 998.897874 USD | 4.729938 | 2.899616 |
| USD/JPY | 1029.441001 JPY | 1026.320534 JPY | 3.674652 | 5.073104 |
| USD/CHF | 930.922718 CHF | 950.072500 CHF | 7.825079 | 6.237574 |

El capital final incluye la valoración de posiciones abiertas. Las cuentas son
independientes: no se suman monedas diferentes. EMA mejora algunos resultados y
empeora otros; esta comparación histórica no selecciona una estrategia ni aporta
validación fuera de muestra. Ambas parten sin posición ni historial previo a la
copia; la semilla y la fecha de inicio pueden influir en los resultados de EMA.

El formato 6 registra el tipo de media, su cálculo y `--strategy` para reproducirlo.
Los informes antiguos no se sobrescriben: si cambia el contenido, elige otra ruta
en `--output`. Las pruebas incluyen cálculos manuales, cruces conocidos,
causalidad, reutilización sin estado y selección desde la terminal.

## Comparación en un solo informe

`--compare` ejecuta SMA y EMA con las mismas ventanas, referencias, fechas,
capital inicial, costes y regla de tamaño. Cada combinación de par y estrategia
mantiene su propia cuenta. No selecciona ganadores ni busca parámetros.

```powershell
python -m trading_ai --compare --fast-window 20 --slow-window 60 --cost-percent 0.1 --initial-capital 1000 --allocation-percent 10 --output reports/comparison20-60-allocation10.md
```

La tabla reúne cierres, posición abierta, capital final, resultado total,
rentabilidad acumulada, drawdown máximo, costes incurridos y entradas rechazadas.
Resultado total = capital final menos capital inicial: incluye posiciones abiertas
y costes ya descontados. La rentabilidad porcentual corresponde a todo el periodo;
no es anualizada. Se comparan estrategias dentro de cada par, sin sumar monedas.

Sin `--output`, la comparación usa `reports/comparison.md`; `--report` conserva
`reports/report.md`. `--compare` no admite `--report` ni `--strategy` a la vez,
porque incluye ambas estrategias. Se conserva la protección contra sobrescrituras
y se registran el SHA-256 de los datos y el comando para reproducir los resultados.

## Sensibilidad local de ventanas y costes

`--sensitivity` compara el caso base con seis variaciones, cambiando un único
factor cada vez: rápida ±1, lenta ±1 y coste ±0.05 puntos porcentuales.
Con ventanas 20/60 y coste 0.1 %, prueba 19/60, 21/60, 20/59, 20/61 y costes
0.05 % y 0.15 %. Son siete escenarios por estrategia y par: 56 simulaciones.
Si una variación resulta inválida, se omite y explica, sin corregirla silenciosamente.

```powershell
python -m trading_ai --sensitivity --fast-window 20 --slow-window 60 --cost-percent 0.1 --initial-capital 1000 --allocation-percent 10 --output reports/sensitivity20-60-allocation10.md
```

El informe muestra el rango de rentabilidades, la máxima diferencia frente a
la base en puntos porcentuales, cuántos escenarios tienen resultado positivo y
cuántos llegaron a invertir. Incluye el detalle de capital, costes, cierres,
posiciones abiertas y drawdown de cada escenario. No confunde una cuenta sin
operaciones con evidencia de estabilidad. Todos los rendimientos son acumulados,
no anualizados, e incluyen posiciones abiertas y costes incurridos.

En este histórico, GBP/USD con EMA cambia de signo: sus resultados van de
-0.667648 % a +0.450857 %. Esta sensibilidad a los supuestos merece atención;
el informe no elige parámetros ganadores ni certifica robustez. No estudia cambios
simultáneos ni datos fuera de muestra. Cambiar la ventana lenta también cambia
su calentamiento; todos los escenarios empiezan desde la misma fecha.

Sin `--output` se guarda en `reports/sensitivity.md`. El modo incluye SMA y EMA
y es incompatible con `--strategy`, `--report` y `--compare`. Se conserva la
protección de datos y salidas existentes y la comprobación del SHA-256.

## Organización

```text
.gitignore
README.md
requirements-dev.txt
data/
    README.md
    raw/
docs/
    PROJECT_STATUS.md
    TRADINGVIEW_PLAN.md
    LOCAL_AI.md
config/
    ai.example.json
scripts/
    Install-LocalAI.ps1
    Start-LocalAI.ps1
    Stop-LocalAI.ps1
tests/
    test_data.py
    test_indicators.py
    test_strategies.py
    test_backtesting.py
    test_metrics.py
    test_reporting.py
    test_costs.py
    test_equity.py
    test_sizing.py
    test_ema.py
    test_comparison.py
    test_sensitivity.py
    test_ai.py
    test_research.py
reports/
    phase1.md
    costs-0_1pct.md
    capital-1000-costs-0_1pct.md
    allocation-10pct.md
    sma10-40-allocation10.md
    sma20-60-allocation10.md
    ema20-60-allocation10.md
    comparison20-60-allocation10.md
    sensitivity20-60-allocation10.md
trading_ai/
    __init__.py
    __main__.py
    data.py
    indicators.py
    strategies.py
    backtesting.py
    metrics.py
    reporting.py
    sensitivity.py
    ai.py
    experiments.py
    research.py
    validation.py
    holdout.py
    evaluation.py
    robustness.py
    discovery.py
    rules.py
```

El paquete está directamente en la raíz del repositorio. `__init__.py` contiene
su descripción y lo identifica como un paquete convencional. `__main__.py`
define `main(argv=None)`, con argumentos opcionales para pruebas y retorno `None`.

La arquitectura prevista es un monolito modular, con responsabilidades separadas
para datos, indicadores, señales, simulación e informes. Por ahora existe el
lector de datos, los indicadores SMA/EMA, las señales de cruce, el backtest educativo
y las métricas de cierres con sus pruebas, además del investigador, su contrato
de proveedores y la herramienta de experimentos controlados.

## Primer investigador local (FASE 3 completada)

Tras preparar Ollama y el modelo según [docs/LOCAL_AI.md](docs/LOCAL_AI.md):

```powershell
.\scripts\Start-LocalAI.ps1
.\.venv\Scripts\python.exe -m trading_ai.research --check
.\.venv\Scripts\python.exe -m trading_ai.research --pair EUR/USD
```

La IA propone una variante acotada, solicita un experimento y analiza los
resultados del motor. Python valida los parámetros y contrasta las conclusiones.
Si la base o la variante tiene cero cierres, Python marca la comparación como
inconclusa, registra el motivo y omite el análisis de IA. El informe identifica
si la conclusión procede de Python o de una respuesta de IA verificada.
Se registran datos, hashes, parámetros, resultados, errores y consumo en `.local/`.
La ejecución local no tiene cargos por consultas a una API. El contrato de
proveedores permite añadir OpenAI posteriormente; esa opción está desactivada
y requiere acordar credenciales y presupuesto antes de implementarla.

Comprobación al cerrar FASE 3: **399 pruebas aprobadas**, incluidas las pruebas del
investigador con respuestas simuladas y sin red. Una ejecución real con
`qwen3.5:4b` en CPU completó propuesta, cálculo y análisis contrastado sobre EUR/USD.

## Evolución y controles

La FASE 4 ha comenzado con la preparación de bloques cronológicos de desarrollo
y evaluación. El corte acordado es el 1 de enero de 2020:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.validation --cutoff 2020-01-01
```

Se generan dos XML locales y un manifiesto con hashes, sin consultar IA ni
evaluar estrategias. El [protocolo de FASE 4](docs/VALIDATION_PLAN.md) explica
la separación, el arranque independiente de cada bloque y los pasos pendientes
para evaluar una propuesta registrada. Esta copia ya se exploró durante
las fases anteriores; la división comprueba el procedimiento, sin convertirla
en evidencia inédita.

Comprobación del primer paso: **423 pruebas aprobadas**. El
[registro de preparación](reports/phase4-split-2026-10-19.md) recoge las fechas,
los recuentos y los hashes comprobados sobre los cuatro pares.

El segundo paso añade `python -m trading_ai.holdout freeze` y `verify` para
registrar una investigación completada sobre desarrollo antes de evaluar.
Vincula la propuesta, sus controles y los resultados de desarrollo a los hashes
de datos, manifiesto y código. Rechaza cambios posteriores; no calcula métricas
del bloque reservado ni requiere nuevas consultas de IA. Los comandos completos
y sus límites están en el protocolo de FASE 4.

Comprobación del segundo paso: **449 pruebas aprobadas**, incluidas 26 nuevas.
Una investigación local propuso EMA20/60 para EUR/USD; su criterio no se cumplió
en desarrollo y la propuesta quedó registrada igualmente. La
[evidencia del registro](reports/phase4-freeze-2026-10-19.md) conserva propuesta,
resultados de desarrollo y consumo. En ese paso aún no se había ejecutado evaluación.

El tercer paso añade `python -m trading_ai.evaluation --frozen-run <ruta>`:
evalúa exclusivamente los parámetros registrados, con capital y calentamiento
independientes, sin consultas de IA. Registra el acceso al archivo reservado y
bloquea repeticiones automáticas de sus mismos bytes. **467 pruebas aprobadas**,
incluidas 18 nuevas. La [primera evaluación](reports/phase4-evaluation-2026-10-19.md)
conserva resultados separados: EMA20/60 no cumple el criterio en desarrollo y
sí lo cumple en evaluación. Esto no demuestra robustez ni cierra la fase.

El cuarto paso añade `python -m trading_ai.robustness prepare` y `run`:
fija cinco configuraciones de ventanas y tres costes por ejecución sobre
desarrollo, selecciona solo con 1999–2009 y comprueba todos los escenarios en
2010–2019. Guarda la selección antes de esa comprobación, sin volver a elegir
después ni acceder al bloque exterior 2020–2026. El protocolo detalla las reglas,
los desempates y las limitaciones de este análisis interno.

Resultado de este cuarto paso: **485 pruebas aprobadas**. Se calcularon las
30 comparaciones previstas; ninguna variante cumplió el criterio en selección
y no se forzó una elección. Las cinco variantes perdieron capital en 2010–2019
con los tres costes probados. El [informe de robustez interna](reports/phase4-robustness-2026-10-19.md)
conserva todos los escenarios y la comprobación de que no se abrió evaluación
exterior. Son resultados descriptivos de un histórico conocido, sin nuevas
consultas de IA.

Por decisión del usuario, las nuevas ideas de estrategia corresponderán al
agente; el desarrollo se centra en herramientas y controles. La bandeja
`python -m trading_ai.discovery --frozen-run <ruta>` permite proponer reglas
distintas de SMA/EMA y registrar sus datos necesarios. Toda idea queda pendiente,
sin permisos de ejecución ni resultados calculados. El
[plan del investigador](docs/AGENT_RESEARCH_PLAN.md) describe este paso y las
herramientas pendientes para convertir ideas en experimentos verificables.

Comprobación de la bandeja: **520 pruebas aprobadas**, incluidas 35 nuevas.
Dos verificaciones locales durante el desarrollo conservaron un rechazo del
formato inicial y un borrador del formato corregido, todavía ambiguo y basado
en medias. El [registro de pruebas de ideas](reports/phase4-discovery-2026-10-19.md)
distingue formato aceptado de estrategia validada; no se calcularon resultados
ni se ejecutaron reglas nuevas.

El [formato declarativo de reglas](docs/RULE_SPEC.md) añade condiciones precisas,
comparaciones, cruces y ventanas de referencias, medias y extremos pasados.
Python lo valida y calcula señales sin ejecutar código generado. El archivo
`config/rules.example.json` reproduce la base existente para comprobar el formato:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.rules --spec config/rules.example.json
```

La CLI solo valida. La bandeja conserva sus borradores pendientes y el
simulador conserva capital, costes, tamaño y ejecución posterior. **587 pruebas
aprobadas**, incluidas 67 nuevas. La [comprobación técnica](reports/phase4-rules-2026-10-19.md)
reprodujo SMA/EMA con contabilidad idéntica sobre desarrollo, sin consultar IA
ni evaluación exterior. Aquel paso no cerraba FASE 4; el cierre posterior se recoge
en el informe enlazado en el estado actual.

La [traducción de ideas a reglas](docs/FORMALIZATION.md) registra una propuesta
formal vinculada al borrador o una duda sin resolver, con una consulta local
como máximo. Los datos declarados que faltan bloquean la consulta. Una regla
compilable queda pendiente de revisión de significado y no se simula:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.formalization --idea-run <carpeta-idea> --frozen-run <carpeta-registro-previo>
```

**623 pruebas aprobadas**, incluidas 36 nuevas. La
[prueba local](reports/phase4-formalization-2026-10-19.md) conservó una solicitud
de aclaración del modelo, sin reglas nuevas ni resultados simulados.

La [revisión técnica y el plan previo](docs/RULE_PLANNING.md) añaden una
comprobación explícita del significado y registran reglas, datos, controles y
presupuesto: una candidata y una base, sin consultas de IA ni variaciones.
El borrador ambiguo permanece bloqueado. La preparación del plan no lo ejecuta.
**669 pruebas aprobadas**, incluidas 46 nuevas. La
[comprobación del bloqueo](reports/phase4-rule-planning-2026-10-19.md) se realizó
sin consultas de IA ni simulaciones y conserva las evidencias.

El [ejecutor separado de planes](docs/RULE_EXECUTION.md) verifica datos, revisión
y límites antes de simular. Una reserva compartida bloquea repeticiones incluso
al copiar o renombrar planes. Guarda la contabilidad completa y conclusiones de
Python, con lectura verificable sin recalcular. **699 pruebas aprobadas**,
incluidas 30 nuevas. La [comprobación de desarrollo](reports/phase4-rule-execution-2026-10-19.md)
usa datos artificiales en pytest; el borrador real sigue sin plan válido.

Las [reformulaciones y lecturas contrastadas](docs/AGENT_FEEDBACK.md) permiten
al agente proponer una revisión vinculada a una idea con dudas y leer resultados
verificados. Una consulta como máximo por origen o cálculo, sin reintentos
automáticos, simulaciones adicionales ni permisos para aprobar sus reglas.
**731 pruebas aprobadas**, incluidas 32 nuevas. Una
[prueba local](reports/phase4-agent-feedback-2026-10-19.md) conservó la propuesta
anterior y una reformulación todavía pendiente, sin traducirla ni simularla.

El [controlador de sesiones](docs/RESEARCH_SESSION.md) conecta idea, traducción,
una posible reformulación, revisión técnica, simulación y lectura contrastada.
Fija un presupuesto global por sesión de cinco consultas y dos simulaciones,
sin reintentos automáticos. La revisión sigue separada del modelo.
**761 pruebas aprobadas**, incluidas 30 nuevas. La
[comprobación](reports/phase4-research-session-2026-10-19.md) conserva un ciclo
artificial completo y una sesión real preparada sin consultas ni simulaciones.
El [primer inicio operativo](reports/phase4-session-proposal-2026-10-19.md)
se detuvo al repetir una idea ambigua cuya reformulación ya estaba consumida:
dos consultas locales, 0 USD de API y ninguna simulación. Se conservó el intento
sin ampliar límites ni reiniciarlo.

Las nuevas sesiones añaden [memoria de ideas y dudas](docs/RESEARCH_SESSION.md#memoria-de-ideas-y-dudas-anteriores)
y detectan repeticiones antes de traducir. Se conservan las reservas anteriores;
el presupuesto y la revisión técnica siguen vigentes. **782 pruebas aprobadas**,
incluidas 21 nuevas para esta corrección. El filtro detecta cambios cosméticos,
sin demostrar equivalencia matemática o mejora de resultados.
La [comprobación local](reports/phase4-idea-memory-2026-10-19.md) recibió esa
memoria, pero siguió necesitando aclaraciones: cuatro consultas, 0 USD de API y
cero simulaciones. Aún queda por mejorar la precisión de las propuestas.

La nueva [entrada de propuestas estructuradas](docs/STRUCTURED_IDEAS.md) pide
indicadores, ventanas, retardos y operadores explícitos desde el origen. Python
los valida con una consulta al modelo, sin otra llamada para traducirlos.
**819 pruebas aprobadas**, incluidas 37 nuevas. Esta entrada está separada del
controlador v2; las propuestas siguen pendientes de revisión y no se simulan.
La [primera comprobación local](reports/phase4-structured-ideas-2026-10-19.md)
produjo reglas válidas con una consulta y 0 USD de API. La salida incluye un
retardo explícito pendiente de revisión; no se presentan resultados calculados.

El [flujo estructurado](docs/STRUCTURED_WORKFLOW.md) ya conecta propuesta,
revisión, plan y sesión de ejecución. Atribuye la consulta original sin repetirla
y admite dos simulaciones controladas con conclusión de Python. **993 pruebas
aprobadas**, incluidas 174 nuevas desde el formato estructurado inicial. La
[comprobación de integración](reports/phase4-structured-pipeline-2026-10-19.md)
conserva el caso local pendiente y un ciclo artificial completo. La reformulación
estructurada permite un intento por origen y no admite cadenas.
La [comprobación de reformulación](reports/phase4-structured-revision-2026-10-19.md)
conserva la corrección de `lag=1` a `lag=0` y una descripción todavía incompleta,
sin simularla. Hay ayudas estáticas para revisar texto, retardos y calentamiento.
La [descripción mecánica](reports/phase4-structured-brief-2026-10-19.md) expresa
las reglas completas desde sus campos verificados, conservando intacta la prosa
del modelo. No cambia la revisión pendiente ni consume consultas de IA.
Un [contrato compacto experimental](docs/STRUCTURED_DRAFTS.md) permite validar
reglas sin prosa libre y describirlas con Python. La vista previa no consulta
modelos ni puede adoptarse en una sesión.
La preparación de contexto conserva objetivo, controles, ideas anteriores y
reservas compartidas. Detecta identidades consumidas sin generar o simular;
no encontrar una identidad tampoco concede aprobación.
Una memoria complementaria conserva decisiones y motivos de revisión de las
sesiones registradas, con consumo heredado separado y sin reabrir acciones.
La petición compacta puede prepararse e inspeccionarse sin enviarla; conserva
el historial capturado y registra tamaño en bytes, sin estimar tokens.
El [flujo de candidatas compactas](docs/COMPACT_CANDIDATES.md) añade vigencia,
reserva exclusiva y una consulta local acotada, con respuesta original y consumo
conservados. Exige revisión independiente antes de preparar un plan con controles
congelados. Su ejecutor explícito usa el mismo motor y la reserva compartida de
cálculos; generar o revisar no simula ni demuestra mejora. No reabre la
reformulación consumida ni incorpora credenciales de pago. Una memoria compacta
conserva intentos y revisiones sin volver a consultarlos o aprobarlos.
Los [diagnósticos por periodos](docs/PERIOD_DIAGNOSTICS.md) separan bloques
conocidos para un plan aceptado, con cuentas independientes y límites previos;
no entrenan o seleccionan una estrategia. El [verificador de evidencias](docs/EVIDENCE_CHECKS.md)
comprueba las copias archivadas sin depender siempre de los originales locales.
La [petición guiada](docs/GUIDED_REQUESTS.md) conserva el historial y añade
cobertura de reglas sin habilitar envío. La [lectura con caché opcional](docs/VALIDATED_READ_CACHE.md)
evita interpretar repetidamente el histórico, contrastando sus fuentes en cada acceso.
El [plan de campaña local](docs/LOCAL_CAMPAIGNS.md) registra límites de propuestas
y backtests con toda la memoria anterior. Prepararlo no activa consultas o cálculos.
Su [registro contable compartido](docs/CAMPAIGN_LEDGER.md) evita superar los
límites entre procesos y conserva los huecos consumidos, sin activar la campaña.
Las [capturas de intentos](docs/CAMPAIGN_ATTEMPTS.md) guardan respuestas, errores
y consumo sin completar textos del modelo o convertirlos en resultados aprobados.
El [primer control de campañas](docs/CAMPAIGN_CONTROLLER.md) contrasta esas
capturas con el plan y la memoria vigentes, valida reglas y separa duplicados
de candidatas pendientes de revisión, con la ejecución todavía desactivada.
La [revisión de capturas y su plan](docs/CAMPAIGN_REVIEW.md) registra una decisión
técnica única y permite preparar la comparación de una candidata aceptada,
con controles congelados y sin reservar o ejecutar backtests.
Un [permiso de cálculo virtual](docs/CAMPAIGN_EXECUTION.md) permite al ejecutor
reservar una comparación y usar el motor, conservando intentos y fallos sin
reintentos. No concede llamadas al modelo, adopción automática u operaciones reales.
La [memoria de resultados](docs/CAMPAIGN_MEMORY.md) reúne propuestas, revisiones,
errores y comparaciones verificadas por el motor. Su verificación opcional reutiliza
el recorrido guiado con guardas de fuentes y conserva las comprobaciones actuales
de permisos y resultados. El [ciclo local acotado](docs/PHASE4_COMPLETION.md) ya
incorpora historial y resultados a nuevas peticiones, separa revisión mecánica,
motor y controles, y se detiene ante duplicados o errores. Requiere habilitación
explícita y no adopta estrategias. La comprobación real rechazó un duplicado sin
simularlo. El walk-forward añade tres ventanas expansivas sobre desarrollo conocido,
sin forzar una selección ni declarar validación independiente.

En la FASE 3 se incorporó un agente investigador que propone hipótesis y
solicita experimentos mediante herramientas controladas. La FASE 4 incorpora
selección interna, evaluación cronológica y walk-forward sobre histórico conocido.
Los cálculos y backtests verifican
las propuestas con resultados reproducibles; el juicio del LLM no sustituye
esa evidencia. SMA20/SMA60 es el primer ejemplo educativo, no la estrategia
definitiva, y una propuesta de mejora puede ser rechazada por los resultados.

La aplicación deberá distinguir entre backtesting histórico, paper trading y una
posible ejecución real en una fase avanzada. Esta última requerirá una nueva
autorización explícita y estará deshabilitada por defecto cuando se implemente.

Se han acordado dos objetivos para la integración futura con TradingView:

1. Generar estrategias Pine Script, probarlas sobre el gráfico y consultar
   información actualizada de señales, operaciones simuladas y resultados.
2. Recibir esa información mediante alertas e importaciones para registrar
   compras, ventas, posiciones y capital virtual en nuestro simulador.

El [plan de TradingView](docs/TRADINGVIEW_PLAN.md) detalla el flujo, las etapas y
las condiciones de aceptación. Las consultas mostrarán la fuente y la fecha de
actualización; se verificarán las capacidades oficiales antes de automatizarlas.
Se usará el emulador de estrategias Pine y la cuenta virtual de TiresIAs:
las estrategias Pine no ejecutan órdenes en la cuenta Paper Trading integrada.
Esta integración está planificada y todavía no está implementada.

Los agentes accederán a herramientas controladas. Las órdenes deberán pasar por
validaciones y un motor de riesgo cuyos límites no podrá modificar el LLM.
La confianza expresada por un agente no sustituye la validación de una estrategia.

Se registrarán las fuentes, los costes y las hipótesis de los experimentos. No se
utilizará información futura para generar señales. Los resultados simulados no
garantizan rentabilidad futura. Las credenciales nunca deben incluirse en Git.

## Continuidad

Consulta [el estado del proyecto](docs/PROJECT_STATUS.md) para conocer el último
cierre de fase. Ese documento solo se actualiza al completar una fase; este
README describe el uso del código actual. Para la decisión posterior al cierre
sobre TradingView, consulta [su plan de integración](docs/TRADINGVIEW_PLAN.md).
