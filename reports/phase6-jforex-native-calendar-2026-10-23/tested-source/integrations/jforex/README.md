# Estrategia SMA UTC para Strategy Tester

`TiresiasSmaUtcTester.java` es una estrategia de investigación para el probador
histórico de JForex. Rechaza **DEMO y LIVE** antes de suscripciones, archivos u
órdenes. Compila con `javac --release 21` y la API 4.9.8 de JForex 4.23 instalada.
La versión inicial se ha compilado dentro de JForex y ha recibido datos del tester.
La revisión actual `sma_utc_test_v2_native_calendar` corrige el tratamiento de
cotizaciones interpoladas durante cierres; falta volver a importarla, compilarla
y completar una prueba nativa con ella. La ejecución anterior quedó interrumpida.

## Primera prueba

1. Abre el `.java` en el editor de JForex, compílalo y selecciónalo en
   **View → Strategy Tester**. Usa una instancia nueva, sin optimización.
2. En **Account**, configura **USD**, depósito inicial **1000000** y apalancamiento
   **1:1**. La estrategia comprueba esos valores y que no haya órdenes activas.
   El saldo de tu acceso demo no sustituye el depósito simulado del tester.
3. Selecciona **EUR/USD**. Para el primer diagnóstico usa período de datos **1 Hour**,
   base **Bid** e interpolación **4 ticks at OHLC**. Conserva también esos ajustes:
   el código no puede verificar automáticamente la interpolación seleccionada.
4. Configura el intervalo del tester desde **2025-01-01 00:00 UTC** hasta
   **2025-12-27 00:00 UTC**. El margen posterior sirve para observar el final de
   la última sesión; el código no solicita operaciones desde el 25/12.
5. En los parámetros de la estrategia conserva estos valores:

| Campo | Valor |
| --- | --- |
| Inicio UTC incluido | `2025-01-01` |
| Fin UTC excluido | `2025-12-25` |
| SMA rápida / lenta | `20` / `60` |
| Cantidad EUR, en unidades | `1000` |
| Capital inicial USD exigido | `1000000` |
| Método de datos declarado | `candles_h1_4ohlc_bid` |

6. Activa el guardado de mensajes e informes del tester. Ejecuta una sola prueba.
   Conserva el HTML original y el registro, incluidos errores y rechazos. No
   cambies parámetros durante la ejecución: el código bloquea la continuación.

Si ya importaste la versión anterior en JCloud, importa de nuevo el `.java`
actualizado y compílalo: la copia de JCloud no se actualiza al modificar el archivo
del proyecto. Conserva el importe de operación en EUR y la moneda de cuenta en USD.
Si el selector de fechas usa Madrid, en estas dos fechas de enero/diciembre de
2025 las `01:00 Europe/Madrid` equivalen a las `00:00 UTC` previstas.

La referencia Python nueva es `4e59e20a16b74fc7bd16ea7dad80d02d`; usa la misma
estrategia y precios que la anterior, con capital y cantidad multiplicados por
1.000. La comisión Python sigue siendo una hipótesis de `0.001` por importe. No
se declara igual a la tarifa del tester y no se reparte una comisión agregada
entre fills. El caso de 1 EUR permanece intacto.

## Reglas de la estrategia

Las sesiones se reconstruyen de los ticks que entregue el tester, agrupados por
fecha UTC, incluidos domingos y días parciales. Antes de incorporar cada tick se
consulta `IDataService.isOfflineTime(time, Instrument.EURUSD)`. Los ticks de períodos
cerrados se omiten y no crean sesiones ni solicitudes. No se descartan precios
constantes, volúmenes cero o días por su nombre: decide el calendario nativo.
Un calendario ausente o que falla bloquea la continuación.
Al llegar la primera cotización admitida
de otra fecha se completa la sesión anterior y se calcula la SMA sobre sus cierres
BID con Decimal de 28 dígitos y redondeo HALF_EVEN. Se requiere un cruce real entre
medias actual y anterior; no hay entrada inicial por tendencia.

Un cruce alcista pide compra de 1.000 EUR, convertido a `0.001` millones para la
API; uno bajista pide cerrar la posición larga propia. No se abre una posición
corta ni se acumulan entradas. Solicitar una orden no se registra como fill: se
exportan las partes confirmadas del historial de la orden con su cantidad, precio
y fecha nativos. No se fuerza un cierre desde `onStop`.

La petición ocurre al primer tick admitido de la siguiente sesión observada; por
ejemplo, una señal del viernes espera a la reapertura del domingo. El engine de
JForex decide cuándo y a qué precio se ejecuta: no se sustituye su fill por la
apertura prevista de Python. La base de sesiones de ticks y los datos BID/ASK de
JForex todavía deben contrastarse con nuestra agrupación de H1. Un ensayo con
interpolación no demuestra equivalencia con datos de ticks reales.

## Archivos para aportar a TiresIAs

El mensaje `TIRESIAS TEST export:` indica la carpeta nueva `tiresias-test-<uuid>`
dentro del directorio de archivos autorizado por JForex (`IContext.getFilesDir`).
No se necesita `@RequiresFullAccess` ni un cambio de permisos globales de Windows.

| Archivo | Contenido |
| --- | --- |
| `metadata.json` | Parámetros originales, método declarado, final observado y estado de revisión |
| `hourly.csv` | Barras H1 BID y ASK nativas, separadas de los ticks reconstruidos |
| `daily.csv` | Sesiones UTC, primeras/últimas fechas, SMA y señales |
| `events.csv` | Peticiones etiquetadas como tales y mensajes de confirmación/rechazo |
| `calendar.csv` | Intervalos de ticks omitidos por el calendario nativo, con fechas y cantidad |
| `executions.csv` | Partes nativas de entrada y cierre, sin fusionarlas |
| `orders.csv` | Estado de cada orden, cantidad restante y comisión agregada USD |
| `failure.txt` | Motivo si se detecta un fallo y se puede guardar el diagnóstico |

El protocolo v2 registra `offline_ticks_skipped` y el origen del calendario en
`metadata.json`; `events.csv` conserva también contenido y motivos de mensajes
nativos. El CSV H1 sigue siendo una exportación sin filtrar para auditar los datos.
El final de la ventana puede observarse mediante un tick cerrado; en ese punto solo
se completa la sesión previa, sin abrir una orden ni añadir una sesión ficticia.

En `executions.csv`, `quantity` ya está en EUR y `price` en USD/EUR. `external_id`
queda vacío porque el historial parcial no proporciona aquí un identificador único
de ejecución; se conservan orden e índice como procedencia, sin inventar un ID.
`fee` queda vacío: la comisión agregada de una orden no es una comisión conocida de
cada ejecución. `signal_at` procede de nuestra petición, no de una señal nativa;
`signal_binding` conserva esa limitación. Los cierres anteriores a nuestra petición
o sin señal disponible no reciben una fecha inventada. Las partes
fuera del intervalo de estrategia se conservan con `in_strategy_window=false`.

La suma de posiciones, valoración final, posibles costes posteriores al 25/12 o
liquidaciones automáticas del tester deben conciliarse con el HTML nativo. El margen
del intervalo del tester no equivale a ampliar el período de la estrategia. Los
indicadores `native_final_report_reconciled` y `external_equivalence_verified`
permanecen en `false`; no comparar directamente el patrimonio final del HTML con
una referencia cuyo período termina antes. Si no se observa el final, la última
sesión queda `unconfirmed_last_session` y no genera una orden final inventada.

Conserva y aporta la carpeta completa junto con el HTML y la configuración del
tester. Primero revisaremos precios/sesiones y después ejecuciones y costes. El
CSV de esta estrategia propia puede mapearse en el comparador genérico; esto no
significa que se haya implementado o validado el importador del HTML de JForex.

## Comprobación local sin conexión

`tests/test_jforex_strategy.py` compila contra el JAR local y ejecuta
`tests/jforex/JForexHarness.java`. El harness usa dobles de las interfaces; no inicia
un cliente, lee credenciales ni reproduce el engine de JForex. Comprueba guardas,
unidades, causalidad, órdenes pendientes/rechazadas, parciales, exportaciones y
paridad de señales sobre precios iguales. Sus fills y comisiones son artificiales.

Requiere JDK 21+ en PATH y el JAR de la API instalado. En otra ubicación puede
indicarse `TIRESIAS_JFOREX_API_JAR`. No descarga dependencias; si faltan, los casos
se marcan omitidos. En la sesión aislada de Codex se respeta el temporal GUID y
la caché desactivada de AGENTS.md.

### Primer intento nativo y corrección del 23/10/2026

El informe `TiresiasSmaUtcTester_23102026_114721.html` y los archivos de estrategia
muestran 23.137 ticks procesados, una solicitud de compra el sábado 30/08/2025 a
las 00:07:30 UTC y rechazo `ORDER_SUBMIT_REJECTED`, con mensaje `System offline`.
No se confirmó ninguna ejecución. Había 1.656 barras H1 planas con volumen cero en
ambos lados entre las 5.784 exportadas. No se atribuye ese rechazo a la conexión
actual del usuario. Los originales permanecen en `.local/jforex/`.

La revisión v2 usa el calendario histórico del instrumento para excluir esos ticks
de las sesiones. Se comprueba localmente con 35 pruebas contra la API instalada,
incluidos cierre/reapertura, conservación de la señal y su fecha, fin de ventana
durante el cierre, calendario ausente/fallido y texto nativo del rechazo. Son dobles
de las interfaces, no una nueva ejecución del motor de JForex ni una validación
de rentabilidad o equivalencia. Las evidencias anteriores permanecen intactas.

Fuentes de capacidades del proveedor:
[tester](https://www.dukascopy.com/wiki/en/manuals/jforex4-desktop/strategy-tester/),
[modo TEST](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IEngine.html),
[historial de entradas](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IFillOrder.html),
[historial de cierres](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/ICloseOrder.html),
[directorio autorizado](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IContext.html).
[Calendario nativo](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IDataService.html).
Se han contrastado las firmas usadas con las fuentes locales de API 4.9.8.
