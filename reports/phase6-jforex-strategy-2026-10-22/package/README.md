# Estrategia SMA UTC para Strategy Tester

`TiresiasSmaUtcTester.java` es una estrategia de investigación para el probador
histórico de JForex. Rechaza **DEMO y LIVE** antes de suscripciones, archivos u
órdenes. Compila con `javac --release 21` y la API 4.9.8 de JForex 4.23 instalada.
La compilación dentro del editor de JForex y su ejecución nativa siguen pendientes.

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

La referencia Python nueva es `4e59e20a16b74fc7bd16ea7dad80d02d`; usa la misma
estrategia y precios que la anterior, con capital y cantidad multiplicados por
1.000. La comisión Python sigue siendo una hipótesis de `0.001` por importe. No
se declara igual a la tarifa del tester y no se reparte una comisión agregada
entre fills. El caso de 1 EUR permanece intacto.

## Reglas de la estrategia

Las sesiones se reconstruyen de los ticks que entregue el tester, agrupados por
fecha UTC, incluidos domingos y días parciales. Al llegar la primera cotización
de otra fecha se completa la sesión anterior y se calcula la SMA sobre sus cierres
BID con Decimal de 28 dígitos y redondeo HALF_EVEN. Se requiere un cruce real entre
medias actual y anterior; no hay entrada inicial por tendencia.

Un cruce alcista pide compra de 1.000 EUR, convertido a `0.001` millones para la
API; uno bajista pide cerrar la posición larga propia. No se abre una posición
corta ni se acumulan entradas. Solicitar una orden no se registra como fill: se
exportan las partes confirmadas del historial de la orden con su cantidad, precio
y fecha nativos. No se fuerza un cierre desde `onStop`.

La petición ocurre al primer tick de la siguiente sesión observada. El engine de
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
| `executions.csv` | Partes nativas de entrada y cierre, sin fusionarlas |
| `orders.csv` | Estado de cada orden, cantidad restante y comisión agregada USD |
| `failure.txt` | Motivo si se detecta un fallo y se puede guardar el diagnóstico |

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

Fuentes de capacidades del proveedor:
[tester](https://www.dukascopy.com/wiki/en/manuals/jforex4-desktop/strategy-tester/),
[modo TEST](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IEngine.html),
[historial de entradas](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IFillOrder.html),
[historial de cierres](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/ICloseOrder.html),
[directorio autorizado](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IContext.html).
Se han contrastado las firmas usadas con las fuentes locales de API 4.9.8.
