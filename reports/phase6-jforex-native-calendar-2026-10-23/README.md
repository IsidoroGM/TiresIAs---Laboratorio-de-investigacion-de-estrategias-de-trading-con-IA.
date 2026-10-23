# FASE 6: primer ensayo nativo y corrección del calendario

El informe aportado por el usuario el 23/10/2026 sí demuestra ejecución de la
versión inicial dentro del tester: USD, capital 1.000.000 y 23.137 ticks procesados.
Se interrumpe el sábado 30/08/2025 a las 00:07:30 UTC tras una petición de compra
rechazada con `ORDER_SUBMIT_REJECTED` y mensaje `System offline`. No se confirma
ninguna ejecución. La ventana histórica no se completa y no se mide rentabilidad.

Las 5.784 barras H1 exportadas contienen 1.656 barras planas con volumen cero en
ambos lados. Los ticks interpolados durante el cierre creaban sesiones ficticias
y permitían pedir una orden en sábado. El fuente inicial se conserva y su SHA-256
coincide con el paquete de preparación anterior. Los HTML, mensajes y exportaciones
nativos originales permanecen en almacenamiento local ignorado por Git; aquí se
guardan sus huellas y el diagnóstico sin identificadores de cuenta.

La revisión `sma_utc_test_v2_native_calendar` consulta el calendario histórico del
instrumento antes de incorporar un tick. Excluye los períodos cerrados de sesiones
y peticiones, conserva la fecha de una señal hasta la primera cotización admitida
tras la reapertura y registra intervalos/contador de omisiones. No deduce un cierre
solo de precios constantes ni inventa fills, comisiones o reintentos. Los H1 siguen
sin filtrar para auditar las diferencias de datos. Los mensajes incluyen ahora
contenido y motivos nativos.

35 pruebas locales aprobadas, sin omisiones, contra la API instalada y con temporal
GUID/caché desactivada. Los dobles prueban el hueco de cierre, precios constantes
durante mercado abierto, señal/fecha/precio tras reapertura, final en período
cerrado, calendario ausente/fallido y mensaje de rechazo. No ejecutan el motor de
JForex. El ZIP contiene fuente, guía y ajustes de la próxima prueba, sin JAR ni JFX.

Siguiente acción: reimportar el `.java` actualizado en JCloud, compilarlo y repetir
la prueba nativa. La corrección aún no tiene una ejecución nativa completa; la
equivalencia de datos, costes y resultados con Python permanece sin verificar.
No hay nuevo backtest Python, llamadas al modelo ni cambios de cuentas, commit,
push o cierre de fase. PROJECT_STATUS y todas las evidencias anteriores se
verifican intactos.
