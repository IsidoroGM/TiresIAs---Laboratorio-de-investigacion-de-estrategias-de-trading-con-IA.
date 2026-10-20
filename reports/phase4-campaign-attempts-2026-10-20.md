# Capturas por reserva y consumo verificable — 20/10/2026

Se implementó el registro de peticiones, observaciones, errores y consumo de
intentos de propuesta, separado del proveedor, la revisión y el motor.
Las observaciones se conservan como bytes antes de analizarlas; el texto
incompleto del modelo no se reconstruye o convierte en reglas aceptadas.

## Comprobaciones con datos artificiales

El primer pase aprobó 38 pruebas en 53,23 segundos. Tras añadir comprobaciones
de procesos y eventos, pasaron **109 pruebas conjuntas en 110,02 segundos**:
39 de planes, 29 del registro contable y 41 del módulo nuevo.
Se usaron proveedores falsos, datos artificiales y temporales exclusivos, con
caché de pytest desactivada. No se contabilizan sus cifras como consumo real.

Se comprobó la conservación de respuestas y textos incompletos, errores antes y después de
intentar una llamada, JSON ilegible, consumo desconocido o incompatible,
conservación de bytes, idempotencia y rechazo de observaciones diferentes.
También interrupciones antes del cierre, bloqueo persistente, cambio de ruta,
reserva global alterada y transiciones simultáneas en hilos y procesos Windows.
El estado se vuelve a leer dentro del bloqueo para impedir decisiones basadas
en una transición anterior.

El resultado contable puede ser completo sin que una propuesta sea válida.
La captura no aprueba una estrategia, interpreta sus reglas o verifica por sí
misma el transporte: conserva la observación suministrada por el controlador.
La marca previa tampoco demuestra que se efectuara la llamada ni la autoriza.

La última suite global verificada sigue siendo la anterior de 1.253 pruebas;
no se presenta la suma de pases focalizados como una nueva suite global.

## Consulta de la campaña de la aplicación

La auditoría `.local/campaign-attempt-audits/bca9a60c2ed845678760442b730aed63`
consultó el ámbito registrado, sin crear reservas, capturas o respuestas ficticias.
El estado sigue inactivo, sin reservas de propuestas o cálculos y sin observaciones.
El total de ese ámbito vacío es cero; el consumo heredado permanece separado.

Los siete contadores de red, proveedor, cálculo, reserva heredada, evaluación
exterior, reserva de campaña y escritura de captura quedaron a cero. El archivo
SQLite, los nueve archivos históricos de reservas y las raíces de captura
conservaron su estado. Las 281 copias previas y referencias originales se
verificaron antes y después. Se añadieron ocho copias: **289 copias y referencias
entre 20 inventarios concretos**, sin presentarlas como archivos físicos únicos.

El [inventario](phase4-campaign-attempts-2026-10-20/snapshot.json) conserva consulta,
auditoría, huellas, eventos, script, código y pruebas con nombre no recolectable.
No contiene una ejecución nueva del investigador ni resultados inventados.

Consumo nuevo de investigación: cero consultas, tokens, coste de API y backtests.
El consumo compacto heredado de 2.262 tokens de entrada y 176 de salida, con
0 USD de API, se conserva sin volver a gastarlo; no resume toda la aplicación.

La reformulación y el intento compacto consumidos siguen intactos. FASE 4 abierta
y `PROJECT_STATUS.md` sin cambios; no hubo instalaciones, servicios nuevos,
operaciones con dinero real, commits o pushes. El siguiente bloque es conectar
el controlador con permiso explícito, memoria vigente, revisión y cálculos
controlados. Uso y límites: [capturas de intentos](../docs/CAMPAIGN_ATTEMPTS.md).
