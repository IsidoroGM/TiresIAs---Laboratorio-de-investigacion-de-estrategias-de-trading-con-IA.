# FASE 6: validación de las capturas nativas v3

El usuario aporta TiresiasSmaUtcTester_23102026_125636.html y exportaciones v3.
Se verifica una ejecución TEST completada sin errores. Trece originales/archivos
revisados se preservan byte a byte bajo .local/, sin publicar el HTML o mensajes
con posibles identificadores privados. Aquí se conservan sus huellas y resultados.
Las huellas de daily/hourly/calendar/executions coinciden exactamente con v2.
Las 307 sesiones y señales coinciden con la referencia Python; los tres fills
mantienen el desfase de +450 s y queda posición abierta de 1.000 EUR.

La API publica 999.989,14 USD al 25/12/2025 00:07:30 UTC y 999.988,68 USD al
26/12/2025 23:52:30 UTC. El primero es 450 s posterior al corte objetivo y no se
retrodata. El último coincide con el patrimonio final del HTML, a su precisión
publicada: pérdida de 11,32 USD. El balance EOD previo no se trata como efectivo.

El lector añade reconstrucciones a cada fecha real con su BID, fills, swaps y
eventos publicados hasta ese instante. Los agregados de órdenes capturados son
otro escenario de comisión; no se suman al coste de los eventos. Las diferencias
API menos reconstrucción son +0,06376/+0,05376 USD cerca del corte y
+0,0073/-0,0027 USD al final. Se conservan sin atribuir su causa a redondeos o
retraso de API de forma concluyente. No se descuentan dos veces los swaps.
La discrepancia de comisiones 0,06/0,05 USD y los costes por fill desconocidos
mantienen parcial la conciliación, sin equivalencia completa certificada.

La app conserva el nuevo registro
3594870d86b9d25e902b5b22ccf9774fdd1b3eee3e5f9fec317b1db8c6d15d8a
y presenta fechas, valores, retraso y tablas por captura. GET coincide con el
archivo guardado; repetir el guardado es idempotente. Se comprueban las dieciocho
huellas previas de almacenes/registro v2/PROJECT_STATUS y el presupuesto 4/1.
No hay nuevos backtests Python, llamadas al modelo u operaciones propias.

117 pruebas seleccionadas aprobadas sin omisiones: 46 de conciliación, 51 del
laboratorio y 20 del servicio. Se verifican sintaxis JavaScript y ficha en el
navegador, con capturas. Los casos nuevos comprueban cotización propia con
posición abierta, cargos posteriores, diferencias API y valoración final. Las
248 pruebas anteriores se conservan como evidencia de aquel incremento.

Se verifican 19 manifiestos previos, motores y estrategia Java sin cambios y
referencias intactas. FASE 6 permanece abierta: no hay commit/push ni actualización
de PROJECT_STATUS. No se necesita otro ensayo idéntico para capturas ya recibidas.
Siguiente trabajo: diferencias temporales de ejecución y alcance de costes antes
de ampliar el contraste a otros períodos o estrategias.
