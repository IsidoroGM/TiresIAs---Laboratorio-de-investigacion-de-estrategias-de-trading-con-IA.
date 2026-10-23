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

## Capturas v3 y siguiente comprobación

La estrategia actualizada captura equity/base equity/balance EOD y cada orden al
primer tick desde el corte y al detenerse. Conserva el instante real de observación,
objetivo, cotización, precios ajustados, costes agregados y exposición por historial.
`IAccount.getBalance` corresponde al cierre diario anterior; equity/base equity
pueden tener retraso según las fuentes locales de la API. El lector no los etiqueta
como efectivo actual ni mueve una captura posterior al instante solicitado.

Para obtener esta evidencia, reimporta `TiresiasSmaUtcTester.java` en JCloud,
compila con F5 y repite los mismos ajustes y parámetros. El ensayo v2 y sus
originales permanecen intactos. La revisión v3 está compilada/probada localmente,
con su ejecución nativa pendiente. La conciliación sigue marcada parcial y la
equivalencia completa de costes/motores permanece sin verificar. FASE 6 continúa
abierta, sin commit/push ni actualización de PROJECT_STATUS.
