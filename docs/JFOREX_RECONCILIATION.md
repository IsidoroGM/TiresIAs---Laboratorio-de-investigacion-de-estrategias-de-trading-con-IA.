# Conciliación de JForex al mismo corte

La pantalla **Simulación → Conciliar costes y valoración de JForex** incorpora
el HTML original del tester junto con las exportaciones de nuestra estrategia.
Es un adaptador acotado a EUR/USD, USD, TEST, H1 BID y 4 ticks at OHLC, protocolos
v2/v3. No es un lector genérico de cualquier informe JForex.

## Paquete y recorrido

El ZIP debe contener, directamente en su raíz:

- `report.html`: copia binaria del HTML original, con este nombre dentro del ZIP.
- `metadata.json`, `daily.csv`, `hourly.csv`, `calendar.csv`, `events.csv`,
  `executions.csv` y `orders.csv` de la misma ejecución.
- En v3, también `account-snapshots.csv` y `order-snapshots.csv`.

Límites: 2 MiB de ZIP, 4 MiB descomprimidos, 2 MiB por archivo, nombres exactos,
sin duplicados, cifrado, directorios o rutas adicionales. Se leen bytes sin extraer
rutas ni ejecutar HTML, scripts, enlaces o contenido del informe.

Selecciona una referencia Python guardada con el mismo capital, cantidad,
SMA y fechas. La interfaz declara UTC para las fechas del HTML y el lector contrasta
sus horas de entrada/cierre con los fills ISO. No infiere una zona regional.
Revisa el resultado antes de guardar. Cambiar referencia o archivo invalida la
vista previa; el guardado exige la huella concreta revisada. Repetirlo es idempotente.

Se conserva `.local/jforex-reconciliations/<sha256>/` con el ZIP original, informe
de conciliación, resumen, manifiesto y copias de resultado/entradas Python. GET
verifica los bytes archivados sin recalcular el contraste, estrategias o cuentas.
El catálogo solo lee resúmenes y manifiestos acotados. Vista previa/guardado son
POST con origen/token y el bloqueo de escritura existente. No invocan modelos,
descargas, órdenes ni procesamiento contable.

## Qué se calcula

Los intervalos de calendario nativos identifican las horas cerradas en este método
de interpolación. Las H1 admitidas reconstruyen sesiones UTC y una huella canónica
independiente. Se contrasta con la referencia, con sus SMA/señales y con daily.csv.
No se copia la huella de Python para declarar equivalencia.

Las ejecuciones se emparejan dentro de una vela H1 (3.600 s), manteniendo tolerancia
temporal cero. La ventana sirve para identificar parejas únicas; no borra el
desfase observado de 450 s. Los costes por fill ausentes quedan desconocidos.

Al corte común se reconstruyen efectivo bruto de fills, exposición y valoración
BID. Los swaps del log se derivan usando el ajuste EUR/USD de 0,0001 por punto y
las cantidades trazadas; los anteriores y posteriores al corte quedan separados.
Se valida que cada swap corresponde a una posición abierta de esa cantidad.
No se restan otra vez del P/L que ya refleja el precio ajustado de una posición.
La [documentación del proveedor](https://www.dukascopy.com/wiki/en/forex-cfds/account-management/rollovers/)
explica el ajuste del precio por rollover; no se usa una tarifa actual para inventar
un coste histórico.

Cuando no hay fills ni cargos publicados posteriores al corte, se muestran dos
reconstrucciones usando por separado el total de comisión del HTML y el de las
órdenes. Son escenarios diagnósticos, no patrimonio nativo observado ni un intervalo
garantizado. Los redondeos y la precisión disponible quedan pendientes.

## Resultado real conservado del 23/10/2026

Referencia `4e59e20a16b74fc7bd16ea7dad80d02d`; conciliación
`e09d030c7635c6542cd53b030874afb51ad162b8305853a2d13b55e42ff96681`.

| Magnitud | USD |
| --- | ---: |
| P/L final publicado por JForex, al final del tester | -11,32 |
| P/L bruto reconstruido al 25/12/2025 00:00 UTC | -7,79 |
| Swaps derivados anteriores al corte | -3,01376 |
| Swaps derivados posteriores al corte | -0,12354 |
| Comisión publicada HTML / eventos | 0,06 |
| Suma de agregados de órdenes | 0,05 |
| P/L al corte reconstruido usando comisión HTML | -10,86376 |
| P/L al corte reconstruido usando agregados de órdenes | -10,85376 |
| P/L Python al corte, con su comisión hipotética | -11,29553 |

Los dos resultados reconstruidos no prueban cuál fue el patrimonio exacto del
tester a ese corte. El informe final llega al 27/12 y su último tick es del 26/12;
no se presenta como una valoración a la misma fecha que Python.

## Capturas v3 verificadas: 23/10/2026

La estrategia actualizada captura equity/base equity/balance EOD y cada orden al
primer tick desde el corte y al detenerse. Conserva el instante real de observación,
objetivo, cotización, precios ajustados, costes agregados y exposición por historial.
`IAccount.getBalance` corresponde al cierre diario anterior; equity/base equity
pueden tener retraso según las fuentes locales de la API. El lector no los etiqueta
como efectivo actual ni mueve una captura posterior al instante solicitado.

El informe `TiresiasSmaUtcTester_23102026_125636.html` completa la ejecución v3 sin
errores y queda conservado como conciliación
`3594870d86b9d25e902b5b22ccf9774fdd1b3eee3e5f9fec317b1db8c6d15d8a`.
Mantiene las 307 sesiones y señales de la referencia, los mismos tres fills y los
1.000 EUR abiertos. Los originales v2 y sus registros guardados permanecen intactos.

| Observación nativa | Fecha real UTC | Patrimonio USD | Variación frente al capital inicial USD |
| --- | --- | ---: | ---: |
| Primer tick desde el corte solicitado | 25/12/2025 00:07:30 | 999.989,14 | -10,86 |
| Fin del tester | 26/12/2025 23:52:30 | 999.988,68 | -11,32 |

La primera lectura se obtiene 450 segundos después del objetivo, con BID 1,17708,
frente a 1,17714 al cierre H1 del corte. No prueba el patrimonio exacto de las
00:00. La última lectura coincide con el patrimonio final del HTML a la precisión
publicada. Esta coincidencia no certifica la conciliación completa de la cuenta.

`snapshot_valuations` reconstruye cada instante usando sus fills, BID y swaps
publicados hasta esa fecha. Compara, por separado, comisiones de eventos HTML hasta
la observación y agregados de órdenes capturados; conserva API menos reconstrucción.
El P/L ajustado de órdenes se muestra como dato nativo y no recibe otro descuento
de swaps. El balance EOD previo no entra como efectivo en ningún cálculo.

Al primer tick, los patrimonios reconstruidos son 999.989,07624 y 999.989,08624 USD:
las diferencias frente a la API son +0,06376 y +0,05376 USD. Al final son
999.988,6727 y 999.988,6827 USD; las diferencias son +0,0073 y -0,0027 USD. Estas
cifras diagnostican precisión y posible desfase de actualización; no identifican
por sí solas su causa ni certifican un intervalo de patrimonio. Se mantienen los
totales de comisión discordantes (0,06 frente a 0,05 USD) y el detalle por fill
desconocido. No se elige un escenario para declarar la cuenta reconciliada.

La interfaz muestra fechas, importes, retraso respecto al objetivo y tablas por
captura. 117 pruebas seleccionadas aprobadas, incluidas 46 de conciliación y sus
casos de cotización propia, cargos posteriores, diferencias y lectura final.
Evidencia en `reports/phase6-jforex-cutoff-validation-2026-10-23/`. No hace falta
repetir otra vez este mismo ensayo para conservar estas capturas.

Siguiente trabajo: resolver el desfase de ejecución frente a las aperturas Python
y documentar qué costes pueden compararse con la precisión real disponible, antes
de ampliar la validación a otros períodos o estrategias. La equivalencia completa
permanece sin verificar; FASE 6 continúa abierta, sin commit/push ni actualización
de PROJECT_STATUS.
