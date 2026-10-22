# TradingView y contabilidad virtual: implementación local de FASE 6

21/10/2026. **FASE 6 en desarrollo.** Estos componentes se pueden probar con
archivos y eventos artificiales. No se ha compilado Pine en TradingView, validado
una exportación real de Strategy Report ni conectado una cuenta externa. El
receptor incluido escucha exclusivamente en `127.0.0.1`.

## Interfaz

Arranca el laboratorio con `python -m trading_ai.lab`, utilizando el entorno
virtual del proyecto. Si el servidor estaba abierto antes de estos cambios,
reinícialo. La opción **Simulación y TradingView** añade:

1. **Paquetes de estrategia.** Preparar un contrato SMA/EMA, revisar sus parámetros
   y descargar Pine, contrato y plantilla de mensaje. Prepararlo no crea cuenta,
   llama al modelo ni publica el código.
2. **Cuenta virtual.** Después de revisar capital, moneda, cantidad, costes y
   límites, registrarla explícitamente. Se identifica por la huella del contrato;
   cambiar parámetros exige otro contrato y conserva la cuenta anterior.
3. **CSV.** Seleccionar el original y declarar sus columnas, separadores numéricos,
   acciones y fechas. La vista previa muestra filas normalizadas, errores y
   SHA-256. Una aprobación posterior guarda las filas en el inbox. Si hay errores,
   no se importa ninguna. El original conserva también BOM y saltos de línea.
4. **Inbox.** Conservar un JSON simulado y consultar original, huella, transporte,
   recepción y estado de normalización. Una recepción no es una contabilización.
5. **Revisión y procesamiento.** En la cuenta se muestran eventos pendientes,
   conflictos y errores asociados. Autorizar procesa hasta cien eventos en
   secuencia, con comprobaciones independientes de saldo, tamaño, costes y riesgo.
   La aprobación identifica estado e inbox concretos; cualquier cambio relevante
   obliga a recargar y revisar.
6. **Valoración y conciliación.** Aportar manualmente un precio fechado, sin generar
   operaciones; comparar efectivo, cantidad y patrimonio con un estado externo
   aportado. Los datos desconocidos siguen siendo `null`. La comparación no
   reemplaza el capital local.

Las cinco pantallas originales y la conversación mantienen sus funciones. Abrir,
refrescar o cambiar de pantalla no registra eventos, procesa cuentas ni llama a IA.
Las acciones utilizan POST con origen y token locales. No se inicia un receptor
de alertas al visitar la interfaz.

## Contrato y modelo de ejecución

`tiresias_tradingview_contract_v1` fija estrategia y ventanas, par, proveedor y
símbolo exactos, gráfico diario estándar, tiempos UTC, período de generación de
señales, cuenta y moneda cotizada, capital, cantidad fija y coste proporcional.
Admite EUR/USD, GBP/USD, USD/JPY y USD/CHF. No convierte monedas ni suma cuentas.

La política inicial es larga, de mercado, sin piramidación ni apalancamiento,
con valor por punto igual a uno y sin deslizamiento adicional. El cruce se decide
en cierre confirmado y la orden se intenta en la apertura siguiente. No existe
liquidación forzada final: una señal al final puede quedar pendiente y una posición
abierta sigue abierta. `period.end` detiene señales; las velas aportadas posteriores
pueden completar una orden pendiente y valorar una posición que permanezca abierta.

El calentamiento comienza en la primera vela cuya apertura alcanza el inicio.
EMA utiliza semilla SMA, igual que el indicador Python; no llama a `ta.ema`.
Pine usa coma flotante y Python Decimal de precisión 28: la equivalencia de señales
y sus casos límite todavía debe comprobarse en el compilador y gráfico reales.
Un saldo insuficiente puede impedir una orden y dejar un hueco de secuencia que
deberá revisarse; no se inventa una ejecución para cerrar ese hueco.

El tamaño se expresa en unidades base y exige verificar las unidades efectivas del
símbolo. El script comprueba símbolo, D1, gráfico estándar, moneda y valor por punto;
la verificación local del archivo no acredita las propiedades efectivas del gráfico.
No modificar el código o las propiedades y seguir usando la identidad anterior.

Los nuevos paquetes usan el generador `tiresias_pine_crossover_v2`: si el gráfico
es incompatible, el error muestra cada discrepancia con el valor recibido y el
requerido (símbolo/proveedor, intervalo, tipo de gráfico, moneda y valor por punto).
Los paquetes v1 mantienen exactamente sus bytes y su identidad. En TradingView,
`1` significa un minuto; seleccionar **1D / 1 día** para estos contratos diarios.
Una discrepancia de unidades no se corrige desactivando el control de valor por punto.

## Archivos y CLI

La entrada es `python -m trading_ai.tradingview --help`. El parámetro global
`--root` permite utilizar un espacio aislado. Los archivos de salida se crean
exclusivamente: no se sobrescriben resultados previos.

Ejemplo artificial en PowerShell, ejecutado desde la raíz del proyecto:

```powershell
New-Item -ItemType Directory -Force .local/tv-demo
.\.venv\Scripts\python.exe -m trading_ai.tradingview new-contract `
  --strategy sma --fast 2 --slow 3 --pair EUR/USD --ticker SYNTH:EURUSD `
  --start 2020-01-01T00:00:00Z --end 2021-01-01T00:00:00Z `
  --account ejemplo-artificial --capital 100 --quantity 1 --cost-rate 0.01 `
  --output .local/tv-demo/contract.json
.\.venv\Scripts\python.exe -m trading_ai.tradingview prepare --contract .local/tv-demo/contract.json
.\.venv\Scripts\python.exe -m trading_ai.tradingview register --contract .local/tv-demo/contract.json
.\.venv\Scripts\python.exe -m trading_ai.tradingview overview
```

`SYNTH:EURUSD` identifica datos artificiales y no es un gráfico que deba instalarse
en TradingView. Para una prueba externa habrá que preparar otro contrato con el
proveedor y símbolo verificados del usuario.

| Comando | Función |
| --- | --- |
| `new-contract`, `prepare`, `verify` | Contrato nuevo, paquete Pine y verificación local de sus bytes |
| `reference` | Referencia Python sobre OHLC normalizado aportado |
| `compare-observations` | Alinear y comparar medias y señales aportadas; no ejecuta Pine |
| `preview-csv`, `import-csv` | Revisar mapa y filas; importar con SHA-256 aprobado de la vista previa |
| `register`, `overview`, `account`, `receipt` | Alta explícita y consultas locales |
| `receive`, `process` | Conservar un JSON; procesar después una cuenta explícita |
| `mark`, `reconcile` | Precio fechado y comparación con estado aportado |
| `serve` | Receptor HTTP de ensayo local, sin procesamiento automático |

Los parámetros de cada comando se consultan con `--help`. La referencia necesita
CSV UTF-8 con cabecera exacta:

```csv
open_at,close_at,open,high,low,close
2020-01-01T00:00:00Z,2020-01-01T23:00:00Z,3,3,3,3
```

Son velas artificiales, no referencias BCE ni prueba de una sesión real D1. Se
comprueban orden, solapes, precios positivos y coherencia OHLC. El formato temporal
canónico exige segundos, zona explícita y hasta milisegundos; no recorta nanosegundos.

## Importación mediante mapa explícito

El lector genérico no es todavía un adaptador validado de Strategy Report. El mapa
declara una columna por identidad, secuencia, lado, cantidad, precio, coste,
instante de señal e instante de ejecución. `fee: null` en el mapa significa que el
archivo no aporta costes, no que sean cero. Admite CSV con coma, punto y coma o
tabulador; punto/coma decimal y agrupación de miles declarada. No elimina monedas,
adivina idiomas ni interpreta fechas sin zona como UTC salvo en los dos formatos
UTC elegidos explícitamente.

`sequence_mode: trade_number` convierte un número de operación en dos secuencias
(entrada `2*n-1`, salida `2*n`), únicamente cuando ese significado se ha comprobado.
Identidades y secuencias duplicadas dentro del archivo son errores. No se deben
inventar campos ausentes para conseguir que una exportación pase la validación.
Métricas, IDs, comentarios y fechas reales requieren inspección del archivo real
y un adaptador que conserve su procedencia; esta parte sigue pendiente.

`preview-csv` crea un JSON con `preview` y `approval_sha256`. Para importar, pasar
esa última huella a `--approve-preview`, después de revisar las filas. Se conserva
original, mapa, vista previa y progreso por fila. Un bloqueo del sistema operativo
impide dos importadores simultáneos. Tras una interrupción se puede repetir
explícitamente la misma importación; no se reprocesa automáticamente al arrancar.
Un progreso alterado o incompleto se comunica para revisión.

## Eventos, precios, costes y riesgo

El evento normalizado `tiresias_simulated_fill_v1` exige contrato SHA-256,
`execution_id`, `sequence`, lado `buy/sell`, cantidad, precio, coste o `null`,
moneda, `signal_at` y `executed_at`. Precios, cantidades y costes son cadenas
decimales. JSON con claves duplicadas, números no finitos o profundidad excesiva
se rechaza. Los eventos de un contrato desconocido se conservan sin ejecutarlos.

La identidad canónica es contrato y ejecución, con secuencia única. Importar y
recibir el mismo evento no duplica su efecto. Una identidad o secuencia repetida
con contenido distinto produce conflicto y conserva ambos originales; no sustituye
el primero. Si, por ejemplo, una alerta no aporta coste y una importación posterior
sí lo aporta, queda una discrepancia por conciliar, no una segunda comisión.
`queued` describe la recepción inicial: el estado contable posterior se consulta
en el historial de eventos de la cuenta.

La cuenta procesa solo secuencias contiguas. Un evento anterior al último estado
valorado se rechaza para no reescribir la historia. Los rechazos conservan el
saldo, avanzan la secuencia observada y pausan nuevas entradas. Las salidas siguen
comprobando posición y costes. No se omiten secuencias ni se desbloquea el riesgo
automáticamente. Cambiar código del contrato o motor también bloquea acciones
posteriores sobre cuentas registradas con esos bytes; su consulta sigue disponible.
No hay todavía una migración aprobada de cuentas entre versiones del motor.

Los costes aportados se contrastan con el contrato y su tolerancia. Si faltan,
se calcula una estimación identificada a partir de la tasa; se carga una sola vez.
Efectivo, cantidad, base de coste, PnL realizado, comisiones, patrimonio, máximo y
drawdown se conservan en una cadena de asientos verificable. El drawdown corresponde
a ejecuciones y valoraciones recibidas, no a todos los movimientos intravela. Un
precio antiguo no se presenta como cotización actual. No hay valoración continua
sin nuevas referencias ni rentabilidad demostrada por un caso artificial.

## Receptor y plantilla Pine

`serve` requiere `TIRESIAS_WEBHOOK_TOKEN` en el entorno (32–128 caracteres de
alfabeto URL seguro) y escucha por defecto en `127.0.0.1:8766`. El secreto no se
pasa por URL, imprime ni guarda en el repositorio. El emisor local envía
`POST /events`, `Authorization: Bearer …`, `Content-Type: application/json` y
longitud explícita; máximo 64 KiB. La respuesta 202 confirma almacenamiento
duradero, incluso de un original inválido, e indica `accounting_processed: false`.
Un 503 no confirma recepción; revisar el inbox antes de reintentar. Un navegador
con cabecera Origin no es un emisor permitido de esta ruta.

La plantilla Pine usa precio y cantidad de los placeholders de ejecución. Guarda
por separado apertura de la vela (`{{time}}`) y emisión de la alerta (`{{timenow}}`).
El instante de ejecución se interpreta como apertura **por la política fija del
contrato**, no como un reloj de tick externo verificado; la alerta declara esa base
y conserva el original. Esta interpretación requiere contraste externo. Los
metadatos de la señal se guardan al crear la orden, separados de su ejecución.

TradingView no puede alcanzar este receptor loopback. No se ha desplegado un
relay HTTPS público ni se han creado alertas. Esa conexión requiere comprobar
cuenta, permisos, datos, costes y configuración del usuario. No abrir puertos o
publicar este servidor de ensayo como si fuera el servicio externo final.

## Evidencia, límites y continuación

El [informe de avance](../reports/phase6-progress-2026-10-21.md) conserva pruebas y
ensayos artificiales. `scripts/check_tradingview_suite.py` ejecuta un recorrido
aislado con aperturas distintas del cierre de señal, webhook, duplicados,
reinicio, procesamiento, valoración y conciliación. Exige una raíz nueva y un
directorio de evidencia nuevo. Su opción `--serve` prepara una revisión manual
aislada y sustituye el proveedor por otro que falla ante cualquier llamada a IA.

La conexión real, compilación y contraste Pine/Python, importación de operaciones
y métricas reales y el puente de intenciones del chat al simulador siguen siendo
trabajo de FASE 6. Para ese puente se debe definir un modo de ejecución manual
separado del contrato de estrategia: una instrucción humana no puede presentarse
como una señal de SMA/EMA ni consumir la identidad de un fill externo.
FASE 7 (demo de bróker) y FASE 8 opcional conservan sus autorizaciones propias.

## Fuentes oficiales consultadas

- [Estrategias Pine](https://www.tradingview.com/pine-script-docs/concepts/strategies/): modelo de órdenes, ejecución, costes y propiedades.
- [Alertas Pine](https://www.tradingview.com/pine-script-docs/concepts/alerts/): mensajes de ejecuciones y creación de alertas.
- [Placeholders](https://www.tradingview.com/support/solutions/43000531021-how-to-use-a-variable-value-in-alert/): valores de vela y reloj de emisión separados.
- [Webhook](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/): restricciones de conexión externa.
- [Exportaciones](https://www.tradingview.com/support/solutions/43000613680-how-to-export-strategy-data/): pestañas de operaciones y métricas exportadas por separado; no documenta un esquema CSV suficiente para dar por validado este lector.
- [Migración a Pine v6](https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-6/): temporalidades con multiplicador explícito.
