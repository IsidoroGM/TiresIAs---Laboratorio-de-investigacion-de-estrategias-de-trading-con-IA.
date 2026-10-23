# Contraste de informes de ejecuciones

FASE 6 añade un comparador de campos entre un resultado BID/ASK guardado y un CSV
aportado. Detecta operaciones que faltan o sobran, diferencias y datos desconocidos.
Conserva los originales y controles revisados. No acredita por sí mismo el origen
externo ni la equivalencia de motores. No calcula otra estrategia ni procesa cuentas.

## Recorrido en la interfaz

1. En **Simulación y TradingView**, abre una prueba histórica BID/ASK calculada y
   pulsa **Contrastar estas ejecuciones con un informe aportado**. También existe
   **Contrastar informes de operaciones** en la pantalla principal.
2. Selecciona el resultado Python y un CSV de ejecuciones UTF-8 de hasta 2 MiB y
   1.000 filas. Un archivo de precios o una fila agregada por operación cerrada no
   representa una lista de ejecuciones individuales.
3. Declara el mapa de columnas, unidades, separadores, acciones y formato horario.
   Los controles son JSON explícito; este primer lector no interpreta formatos de
   proveedores automáticamente.
4. Identifica el productor y el origen: `user_supplied_external`,
   `synthetic_fixture` o `python_reexport`. Declara solo los metadatos conocidos.
   Los valores `null` siguen siendo desconocidos; no se copian desde Python.
5. Fija tolerancias y pulsa **Mostrar contraste sin guardar**. Revisa las fechas
   UTC, cantidades, precios, comisiones, ausencias y ambigüedades.
6. Marca la revisión y pulsa **Guardar contraste revisado**. Un cambio posterior
   del archivo o controles exige otra vista previa. La ficha guardada verifica sus
   copias sin ejecutar de nuevo el comparador o la estrategia.

## Contrato del CSV

| Campo | Significado |
| --- | --- |
| `executed_at` | Instante de cada ejecución; obligatorio |
| `side` | Acción mapeada explícitamente a `buy` o `sell` |
| `quantity` | Cantidad ejecutada, normalizada a EUR, positiva |
| `price` | Precio de ejecución USD/EUR, positivo |
| `fee` | Comisión de esa ejecución en USD; opcional y no negativa |
| `signal_at` | Instante de señal, si el informe lo contiene; opcional |
| `external_id` | Identificador único de ejecución, si existe; opcional |

En `mapping.columns` cada significado apunta al encabezado correspondiente.
Las columnas opcionales ausentes se declaran `null`; una celda opcional vacía
también conserva ausencia. Una comisión desconocida no equivale a cero. No se
reparten costes agregados ni se inventa una señal o un identificador.

`quantity_multiplier` convierte cantidades a unidades base: debe proceder de la
definición de unidades del informe. No se deduce el tamaño de un lote. No hay
conversión automática de monedas o del signo de un coste.

Se admiten delimitadores coma, punto y coma o tabulador; punto o coma decimal y un
separador de miles declarado. Las monedas incrustadas y agrupaciones ambiguas se
rechazan. `sides` declara las etiquetas exactas del archivo. `time_format` admite
`iso8601` con zona, `unix_ms`, `utc_ymd_hm` o `utc_dmy_hm`; estos dos últimos
declaran UTC expresamente. No se adivina la zona del bróker ni el horario de verano.

Cada fila representa un fill, no una orden solicitada o un resumen de posición.
Las ejecuciones parciales no se fusionan. Si un informe repite el identificador de
orden para varios fills, ese campo no sirve como `external_id` único: hay que
conservar la distinción en el adaptador o declararlo ausente.

## Alineación y resultados

Se buscan primero parejas únicas con igual acción e instante UTC. Una ventana
adicional, fijada en `alignment_window_seconds`, solo permite parejas mutuamente
únicas; las ambigüedades quedan visibles. Una ejecución ausente no desplaza las
siguientes parejas. La tolerancia temporal aceptada se declara aparte mediante
`time_tolerance_seconds`. Alinear una fila desplazada no hace desaparecer su
diferencia de hora.

Las tolerancias de precio, cantidad y comisión son diferencias absolutas en las
unidades declaradas; empiezan en cero. No son porcentajes ni ticks. La aritmética
decimal evita redondear una diferencia justo en el umbral. Las señales disponibles
se contrastan exactamente. Los identificadores externos no se consideran iguales
a identificadores de otro motor.

Un informe inválido bloquea la comparación de su subconjunto válido. Los resultados
separan configuración incompatible, diferencias, ausencia de ejecuciones para
concluir, evidencia incompleta y coincidencia de campos con origen sin verificar.
Incluso si todos coinciden, `external_origin_verified`, `external_format_verified`
y `external_equivalence_verified` permanecen en `false`.

## Archivo y efectos

El guardado aprobado crea `.local/execution-comparisons/<sha256>/` con el CSV
original, resultado, resumen, manifiesto y copias del resultado Python y sus dos
entradas de precios. Las huellas verifican todos los bytes; el identificador
depende del resultado y controles. Repetir exactamente el guardado no lo duplica.
El catálogo consulta solo metadatos acotados; abrir la ficha verifica las copias
sin depender de que siga existiendo el directorio de la simulación original.

Vista previa y guardado son POST locales protegidos por origen y token. GET no
calcula ni escribe. No se accede al modelo, a descargas, al inbox o a cuentas.
Los motores y las huellas de las cuentas manuales existentes no cambian.

## Siguiente adaptador: JForex/Dukascopy

El usuario ha elegido JForex/Dukascopy. La documentación oficial del
[Strategy Tester de JForex 4](https://www.dukascopy.com/wiki/en/manuals/jforex4-desktop/strategy-tester/)
describe configuración e informes de backtest. La documentación de
[ITesterClient](https://www.dukascopy.com/wiki/en/development/get-started-api/use-jforex-sdk/back-testing/)
indica que `createReport` escribe un informe HTML. Esto no establece un contrato
CSV de fills para el lector genérico implementado aquí.

Para desarrollar y comprobar ese adaptador hace falta un HTML original del tester,
sin convertir o editar, junto con versión de JForex, estrategia/parámetros, período,
zona, cantidad/unidades, moneda, comisiones y configuración de velas/precios. Si el
HTML no incluye detalle suficiente, se deberá aportar también el registro de eventos
o exportación que corresponda. Se conservarán original y conversión identificables,
sin ejecutar scripts, enlaces o instrucciones presentes en el informe.

Después se contrastarán calentamiento, señales, sesiones UTC, BID/ASK, ejecuciones,
posición final abierta y costes con reglas equivalentes. No se ha instalado JForex,
conectado una cuenta ni ejecutado una estrategia externa en este incremento. El
CSV de QA deriva de Python y contiene alteraciones deliberadas; no sustituye esa
validación pendiente. FASE 6 permanece abierta.

La [preparación de JForex](JFOREX_SETUP.md) conserva la descarga oficial verificada,
los ajustes de la referencia y la diferencia de tamaño mínimo. La referencia de
1 EUR no se considera directamente reproducible con el mínimo de 1.000 unidades
documentado para la API. Después se calcula una referencia escalada independiente
y se prepara la [estrategia TEST](../integrations/jforex/README.md). Su ejecución
nativa y el contraste externo siguen pendientes.

### Primer contraste de archivos nativos: 23/10/2026

Se recibe un ensayo completo de JForex v2: 307 sesiones y tres ejecuciones. Sus
sesiones reconstruidas de H1, tras aplicar los intervalos del calendario nativo,
producen independientemente el SHA-256 de la referencia. Los OHLC diarios, SMA y
señales coinciden; hay cinco diferencias de precio en tres H1 originales.

Se ejecutan las funciones puras del comparador sobre `executions.csv`, sin registrar
un contraste en la app. La declaración usa la huella reconstruida de sesiones,
no una huella copiada a ciegas. La ventana de alineación de una vela H1 (3.600 s)
solo empareja candidatos únicos; la tolerancia temporal sigue siendo cero. Los
tres pares conservan diferencias de +450 s, con precio, cantidad y señal iguales.
Las comisiones por fill quedan desconocidas y el estado es `differences`.

La revisión del HTML es específica de este archivo y no constituye un importador
genérico validado. Quedan pendientes los costes, swaps, precisión y valoración
al mismo corte. El informe nativo sigue hasta el 27/12 frente al corte de estrategia
del 25/12; sus patrimonios finales no se declaran directamente equivalentes.
La revisión está en `reports/phase6-jforex-native-review-2026-10-23/` y conserva
huellas de los originales privados. Ninguna cuenta, orden o modelo se modifica.

### Conciliación nativa integrada

El [adaptador acotado de JForex](JFOREX_RECONCILIATION.md) admite ZIP de HTML y
exportaciones v2/v3 de nuestra estrategia TEST. El primer ensayo v2 ya se conserva
en su catálogo independiente, con originales privados, referencia congelada y
estado parcial. Se reconstruye el corte común y se separan swaps/cargos posteriores;
la discrepancia de totales de comisión no se distribuye entre fills ni se oculta.
La estrategia v3 aporta capturas informativas cerca del corte y al final, con fechas
reales. Su ensayo nativo ya está guardado y conserva la lectura posterior al objetivo
y las diferencias de reconstrucción. El comparador genérico anterior conserva su
contrato; la equivalencia completa de motores/costes sigue sin verificarse.
