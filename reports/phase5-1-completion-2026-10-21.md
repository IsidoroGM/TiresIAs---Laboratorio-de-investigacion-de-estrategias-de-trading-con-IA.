# FASE 5.1 — Rendimiento y fluidez de TiresIAs

21/10/2026, Europe/Madrid. **FASE 5.1 completada.** Diagnóstico iniciado el día 20;
la carpeta de evidencias conserva esa fecha. Implementación local sobre `47d2fc5`,
sin commit o push nuevos y sin iniciar FASE 6.

## Resultado medido

Mismo conjunto de referencia: 92 registros y 805 archivos catalogados. Treinta
muestras HTTP por pantalla, p95 por rango más próximo, conexiones nuevas en
loopback. Referencia: servidor, catálogo y consultas del cierre de FASE 5 cargados
desde Git, con el motor histórico conservado. Versión final: cuatro hilos.

| Pantalla | Mediana anterior | Mediana FASE 5.1 | p95 FASE 5.1 |
| --- | --- | --- | --- |
| Inicio | 3155,18 ms | 1,98 ms | 19,38 ms |
| Experimentos | 3196,91 ms | 2,33 ms | 22,66 ms |
| Consumo | 2426,35 ms | 2,18 ms | 15,29 ms |

Los valores de FASE 5.1 corresponden al índice preparado e incluyen las
comprobaciones periódicas de cambios. Primera consulta en una instancia nueva:
3,262 s antes y 2,402 s después. La caché del sistema operativo no se controla;
estos valores no se presentan como arranque en frío del disco. Son medidas HTTP,
no tiempo de pintado de pantalla. Dependen del conjunto y del equipo.

También se midieron dos hilos. La configuración de cuatro mantiene las medianas
y permite atender más de una consulta junto a lecturas lentas, con trabajo y cola
acotados. Detalles locales finales: ficha 80,03 ms, cuenta 111,59 ms y comparación
123,22 ms de mediana. Las copias archivadas mantienen la verificación completa de
bytes: 294,89, 331,99 y 349,80 ms, respectivamente. Cada caso de detalle tiene tres
muestras; sus p95 no se utilizan como objetivo estadístico de aceptación.

- [Referencia final, 30 muestras](phase5-1-completion-2026-10-20/http-before-30-final.json).
- [Resultado final, dos/cuatro hilos](phase5-1-completion-2026-10-20/http-after-30-final.json).
- [Huellas finales de fuentes y configuración](phase5-1-completion-2026-10-20/verified-sources.json).

Las dos series finales confirman fuentes sin cambios durante su ejecución.
Las series preliminares sin sufijo `final` se conservan como desarrollo; en la
primera referencia hubo cambios en archivos de FASE 5.1 mientras se medía el
código histórico. No se usa esa serie para la tabla final.

## Cambios entregados

- Índice de resúmenes en memoria, con generaciones independientes, una sola
  actualización en curso y publicación atómica. Se revisan cambios cada dos
  segundos mientras hay consultas. El refresco forzado relee las fuentes.
- Caché de metadatos con límite de 32 MiB e índice de hasta 16 MiB de peso estimado
  de objetos. En el ensayo final retienen aproximadamente 1,51 y 1,48 MiB. Una
  lectura puntual del proceso de previsualización mostró 37,4 MiB de memoria
  residente y 69,8 MiB de pico; no es un límite garantizado para otros conjuntos.
- Lectores por petición: presupuesto, bytes y avisos independientes. El detalle
  y los archivos ya leídos se comparten dentro de una consulta, sin saltarse los
  límites de lectura. Las comprobaciones de rutas durante el escaneo evitan trabajo
  duplicado; abrir fuentes conserva validaciones actuales de enlaces y junctions.
- Servidor local con cuatro hilos como máximo, espera de conexión limitada y
  respuesta 503 reintentable ante saturación. Una lectura de detalle no bloquea
  las demás pantallas. Un 404 conocido no reconstruye el catálogo.
- Navegación con cancelación de peticiones abandonadas; la ficha no espera a la
  primera cuenta. Los listados conservan filtros y muestran fechas y errores de
  actualización. HTML/CSS/JavaScript usan ETag; datos y originales, `no-store`.
- `pytest.ini` limita el descubrimiento a `tests`, conservando las copias históricas
  de pruebas en informes. No modifica la política de caché del usuario.

Los resúmenes fechados no se presentan como verificación actual de integridad.
Las fichas, cuentas y originales leen sus bytes actuales; SQLite mantiene lectura
vigente con conexión propia en modo de solo lectura. Cambios con tamaño y mtime
conservados no eluden las comprobaciones de detalle.

## Comprobaciones y límites

**128 pruebas aprobadas**: 80 de interfaz —51 anteriores y 29 nuevas— en 18,18 s,
y 48 de evidencias/registro contable en 22,65 s. Caché pytest desactivada y temporal
GUID nuevo por ejecución conforme a AGENTS.md. No es una nueva ejecución completa
de los 1598 casos históricos. La colección actual contiene 1627 nodos: exactamente
los 1598 anteriores más los 29 nuevos, sin errores, omisiones o duplicados.

- [80 casos de interfaz](phase5-1-completion-2026-10-20/lab-tests-verified.xml).
- [48 casos de evidencias y registro](phase5-1-completion-2026-10-20/evidence-ledger-tests.xml).
- [Colección completa comprobada](phase5-1-completion-2026-10-20/collection-check.json).
- [Frescura con intervalo por defecto](phase5-1-completion-2026-10-20/freshness-check.json):
  una fuente artificial añadida aparece por HTTP en 2,170 s.
- [Auditoría final](phase5-1-completion-2026-10-20/read-only-check-final.json): 838
  archivos controlados conservan sus huellas, 92 registros, 40 cuentas con detalle
  y 150 con resumen; 47 fuentes de consumo. Cero acciones prohibidas, inferencias,
  backtests, reservas o escrituras en fuentes desde la consulta. Los estados de
  integridad siguen siendo 52 copias verificadas, 23 originales cotejados, ocho
  sin verificación completa y nueve incompletos.
- [Navegador](phase5-1-completion-2026-10-20/browser-check.json): cinco pantallas,
  navegación rápida, filtros conservados tras sondeo/refresco forzado, cambio de
  cuenta, dos gráficos y comparaciones admitidas/bloqueadas, sin errores de consola.
  Observaciones individuales: listados de 8,9–37,6 ms; ficha de 80,9 ms y primera
  cuenta de 123,3 ms. La instrumentación incluye petición y construcción del DOM,
  no el pintado físico ni una distribución de percentiles del navegador.
- Capturas: [explorador](phase5-1-completion-2026-10-20/explorer-top.png),
  [fecha y refresco](phase5-1-completion-2026-10-20/explorer.png) y
  [cuenta y curva](phase5-1-completion-2026-10-20/account.png).
- [Cierre de previsualización](phase5-1-completion-2026-10-20/shutdown-check.json):
  servidor y pestaña de pruebas cerrados. El servidor y Chrome del usuario en
  8765 no se han detenido ni modificado.

Se conservan los diagnósticos fallidos: un pase detectó semánticas distintas de
ctime entre lstat/fstat en Windows; la colección general detectó una prueba
archivada entre los informes. Las comprobaciones finales usan las correcciones;
los diagnósticos anteriores no se cuentan como aprobados. La condición de
saturación también se prueba tras corregir el cierre TCP con RST de Windows.

Los 131 archivos anteriores del motor y sus pruebas, y las evidencias históricas
seguidas por Git, permanecen intactos. No se reabren presupuestos o reformulaciones,
ni se recalculan estrategias. La primera carga y la verificación completa de
archivos siguen teniendo un coste explícito. Sin dependencias o servicios externos
nuevos. **TradingView y FASE 6 siguen pendientes.**

Para aplicar la versión nueva en la sesión abierta: cerrar el servidor anterior
con Ctrl+C, ejecutar de nuevo `python -m trading_ai.lab` desde el entorno virtual
y recargar el navegador. [Guía](../docs/LAB_INTERFACE.md).
