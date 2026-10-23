# FASE 6 — Contraste de ejecuciones, 22/10/2026

Implementación y prueba del lector CSV genérico frente a una simulación BID/ASK
guardada. No es una validación de JForex ni de otro motor externo.

El protocolo se fija antes de la prueba en navegador. Se reutiliza la simulación
72061a4aa7a0455cb400edcc580cb964, sin calcular otra estrategia. Su CSV derivado
está marcado `synthetic_fixture`: altera un precio +0,0001, otra hora +60 segundos
y deja otra comisión vacía. La ventana de alineación es 60 segundos y las
tolerancias aceptadas son cero.

Resultado esperado y comprobado: tres parejas únicas, dos filas con diferencias,
sin ausencias, excedentes o ambigüedades; comisión desconocida en la tercera fila.
El navegador muestra la vista previa, exige revisión separada y guarda las copias.
Las capturas conservan tanto procedencia artificial como diferencias.

630 pruebas seleccionadas aprobadas en 56,20 s, incluidas 44 nuevas. No se ejecutó
la colección completa. `tests-final.xml` y `tests-final.log` conservan la salida;
`tests.xml` y `tests.log` conservan las 628 anteriores a añadir dos casos de catálogo
dañado. La auditoría
independiente usa biblioteca estándar, Decimal y fechas, sin importar el motor
del comparador. Se verifican 12 manifiestos anteriores y sus evidencias.

Los archivos `results/` son copias exactas del archivo local aprobado. Incluyen
CSV original, resultado, resumen, manifiesto de archivo, simulación de referencia
y entradas de precios. `tested-source/` conserva el código utilizado. El manifiesto
de este informe enlaza sus huellas. No incluye tokens de acciones ni mensajes
adicionales del usuario en la aplicación.

No hay nuevas peticiones al modelo, backtests, asientos, órdenes externas o cambios
de cuentas. El usuario ha elegido JForex/Dukascopy; falta un HTML original del
tester con su configuración para adaptar ese formato y realizar el primer
contraste externo real. La coincidencia de campos nunca activa verificación
externa automáticamente.

El incremento queda local, sin nuevo commit/push. PROJECT_STATUS permanece intacto;
FASE 6 no se cierra. [Guía de uso](../../docs/EXECUTION_COMPARISON.md).
