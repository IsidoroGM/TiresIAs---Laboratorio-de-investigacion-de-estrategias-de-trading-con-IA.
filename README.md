# Trading AI

Proyecto educativo de investigación y trading algorítmico asistido por agentes de
IA. Se construye paso a paso para aprender Python, arquitectura modular, pruebas
automatizadas y evaluación de estrategias.

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

La **FASE 0: preparación y fundamentos está completada**. Hemos comenzado la
FASE 1 con la descarga e inspección del histórico educativo del BCE. Están comprobados
Python 3.14.8 de 64 bits, el entorno virtual `.venv`, su uso desde la terminal de
VS Code y el repositorio Git local.

El paquete `trading_ai` dispone de un punto de entrada ejecutable que muestra la
presentación del laboratorio. Su arranque y su importación están comprobados.

La copia original, su procedencia y una muestra están en [data/README.md](data/README.md).
La descarga se realizó como preparación del ejercicio. El módulo `trading_ai.data`
lee la copia local para cualquiera de los cuatro pares y cuenta con pruebas.
El módulo `trading_ai.indicators` calcula medias móviles simples; se han
comprobado SMA20 y SMA60 sobre los cuatro históricos.
Todavía no hay un descargador integrado en la aplicación.

La estrategia inicial detecta cruces SMA20/SMA60 y genera señales de entrada
y salida. El backtest educativo gestiona una compra por par y registra cierres
y posiciones abiertas con ejecución en la referencia siguiente y costes cero.
El módulo `trading_ai.metrics` resume los cierres e indica si queda una posición abierta.
Todavía no hay API, dashboard, agentes ni conexión con un bróker. Los resultados
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
Trading AI - laboratorio educativo
Estado: FASE 0 - entorno de desarrollo.
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

Resultado comprobado de la suite completa: **156 passed** (26 del lector, 34 de
indicadores, 35 de estrategia, 37 del backtest y 24 de métricas). Las pruebas del lector usan XML pequeños en carpetas
temporales, sin red ni dependencia del histórico descargado. Comprueban las
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

- Una sola compra abierta por par, de una unidad de moneda base, sin posiciones
  cortas ni acumulación de entradas. No se modela una cuenta ni capital disponible,
  margen o financiación; se supone disponible la cantidad necesaria para esa unidad.
- Entradas estando dentro y salidas estando fuera se ignoran.
- Costes cero: no se aplican spread, comisiones, slippage ni swaps.
- Precio simulado: referencia del BCE de la siguiente observación. Retrasar la
  ejecución evita usar la señal antes de conocerla, pero no convierte esa
  referencia en un precio ejecutable.
- Una posición abierta al final permanece abierta, sin cierre forzado ni
  valoración de su ganancia/pérdida latente.
- Resultado de cada cierre: precio de salida menos precio de entrada, por una
  unidad base. Se expresa en moneda cotizada; no es un porcentaje de rentabilidad.

Tres `@dataclass(frozen=True)` representan los resultados. Una dataclass genera
el constructor y la comparación de campos, parecida a un `record` de Java;
`frozen=True` impide reasignar sus campos normalmente:

- `Position`: fecha de señal de entrada, fecha de ejecución y precio de compra.
- `Trade`: posición cerrada, fecha de señal de salida, fecha de ejecución, precio
  de venta y `pnl` (ganancia o pérdida).
- `BacktestResult`: par, moneda cotizada, tupla de operaciones cerradas, posición
  abierta opcional y `realized_pnl`, suma de resultados de los cierres.

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
comparación de rentabilidad: todavía faltan capital, costes, exposición y riesgo.
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
Todavía no hay rentabilidad sobre capital, curva de capital, drawdown ni valoración
de la posición abierta. Tampoco validación fuera de muestra. El porcentaje de
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
tests/
    test_data.py
    test_indicators.py
    test_strategies.py
    test_backtesting.py
    test_metrics.py
trading_ai/
    __init__.py
    __main__.py
    data.py
    indicators.py
    strategies.py
    backtesting.py
    metrics.py
```

El paquete está directamente en la raíz del repositorio. `__init__.py` contiene
su descripción y lo identifica como un paquete convencional. `__main__.py`
define la función de arranque `main()`, sin parámetros y con retorno `None`.

La arquitectura prevista es un monolito modular, con responsabilidades separadas
para datos, indicadores, señales, simulación e informes. Por ahora existe el
lector de datos, el indicador SMA, las señales de cruce, el backtest educativo
y las métricas de cierres con sus pruebas; los demás módulos quedan
para tareas posteriores.

## Evolución y controles

En la FASE 3 se construirá un agente investigador que proponga hipótesis y
solicite experimentos mediante herramientas controladas. En la FASE 4 se añadirá
optimización y validación fuera de muestra. Los cálculos y backtests verificarán
las propuestas con resultados reproducibles; el juicio del LLM no sustituye
esa evidencia. SMA20/SMA60 es el primer ejemplo educativo, no la estrategia
definitiva, y una propuesta de mejora puede ser rechazada por los resultados.

La aplicación deberá distinguir entre backtesting histórico, paper trading y una
posible ejecución real en una fase avanzada. Esta última requerirá una nueva
autorización explícita y estará deshabilitada por defecto cuando se implemente.

Los agentes accederán a herramientas controladas. Las órdenes deberán pasar por
validaciones y un motor de riesgo cuyos límites no podrá modificar el LLM.
La confianza expresada por un agente no sustituye la validación de una estrategia.

Se registrarán las fuentes, los costes y las hipótesis de los experimentos. No se
utilizará información futura para generar señales. Los resultados simulados no
garantizan rentabilidad futura. Las credenciales nunca deben incluirse en Git.

## Continuidad

Consulta [el estado del proyecto](docs/PROJECT_STATUS.md) para conocer el último
cierre de fase. Ese documento solo se actualiza al completar una fase; este
README describe el uso del código actual.
