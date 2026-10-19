# FASE 4 — Reformulación estructurada y ayudas de revisión

Fecha: 19 de octubre de 2026. Continuación autónoma autorizada, sin cerrar fase.

## Cambio comprobado

`structured_revision` admite un intento por propuesta y desarrollo, solamente
desde una revisión `needs_clarification`. Mantiene la respuesta original y
registra por separado linaje, pregunta, extracto del motivo, respuesta hija,
consumo nuevo y heredado. Bloquea reintentos por cambiar motivo o carpeta y
prohíbe reformular una hija. No consulta precios de evaluación o simula.

`structured_diagnostics` añade ayudas estáticas: longitudes exactas, indicios
de descripción incompleta, retardos, calentamiento y condiciones constantes o
idénticas. Estas propiedades no aprueban una propuesta ni calculan rentabilidad.

## Único intento con Ollama local

Registro `.local/structured-revisions/2d0040bbd7184c1d9cbde9a8eef3ce3b`.
Hija `a1bacf3e52c743c2b4088cad0c82ee45`, con identidad de reglas
`7371635017c0d0fe8501735d32d0724ec87b181676dd6a03840355b4da568946`.

El modelo mantuvo EMA20/SMA60 y cambió ambas series de salida a `lag=0`.
Así eliminó el retardo adicional señalado en la revisión anterior. No se
modificaron reglas después de recibir la respuesta ni se supuso equivalencia.

La respuesta de API terminó correctamente y produjo JSON válido, pero su
descripción era incompleta: el título acaba en «y re» y la hipótesis en
«por debajo de la». La revisión separada conservó **`needs_clarification`**.
No se completó el texto por inferencia, no se simuló y no se hizo otro intento.

La sesión hija es `.local/structured-sessions/bb2880ffb7c74c37abcece9c5275ffc2`.
Atribuye la consulta de la hija sin volver a generarla. Su reserva de simulaciones
es cero y no conserva bloqueos activos.

| Consumo | Original heredado | Reformulación nueva | Linaje total |
|---|---:|---:|---:|
| Consultas de generación | 1 | 1 | 2 |
| Tokens de entrada | 1257 | 1289 | 2546 |
| Tokens de salida | 248 | 239 | 487 |
| Duración del proveedor | 68,694 s | 62,952 s | 131,646 s |
| Coste de API | 0 USD | 0 USD | 0 USD |

La columna heredada corresponde a una generación anterior; no se consumió de
nuevo en este desarrollo. Durante esta continuación solo se hizo la consulta
de reformulación nueva. Cero simulaciones sobre mercado o histórico real.

## Diagnóstico y corrección descriptiva

Los registros estáticos verificaron las propiedades siguientes, sin generar
señales o calcular resultados:

| Propiedad | Original | Hija |
|---|---:|---:|
| Longitud del título | 60 | 60 |
| Longitud de hipótesis | 159 | 159 |
| Retardos de entrada | 0, 0 | 0, 0 |
| Retardos de salida | 1, 1 | 0, 0 |
| Primer índice de señal disponible, base 0 | 61 | 60 |
| Primer índice de ejecución posible, base 0 | 62 | 61 |

Son cotas de disponibilidad, no operaciones previstas. La hija recibe indicios
de ausencia de terminador de frase y palabra de enlace final. No son una prueba
automática de significado o truncamiento de API.

La justificación original de la revisión hija decía 160 caracteres para la
hipótesis. El recuento exacto es 159, con límite 160. Una
[fe de erratas vinculada por hash](phase4-structured-revision-2026-10-19/review-erratum.json)
corrige ese dato conservando la revisión sellada. La decisión pendiente no cambia.

## Evidencias y trabajo restante

**886 pruebas aprobadas** en la comprobación final, con caché desactivada y
temporal exclusivo. La reformulación tiene 12 pruebas y los diagnósticos 10.
También se comprobó que una sesión conserva coste y tokens heredados
desconocidos como desconocidos, sin convertirlos en cero. En total hay 67
pruebas nuevas desde las 819 del punto de partida de esta continuación.

[31 copias exactas y hashes](phase4-structured-revision-2026-10-19/snapshot.json)
incluyen [linaje](phase4-structured-revision-2026-10-19/revision.json),
[respuesta hija](phase4-structured-revision-2026-10-19/child-proposal.json),
[solicitud y consumo](phase4-structured-revision-2026-10-19/child-events.jsonl),
[revisión](phase4-structured-revision-2026-10-19/child-review-review.json),
[estado de sesión](phase4-structured-revision-2026-10-19/child-review-context.json) y
[diagnóstico](phase4-structured-revision-2026-10-19/child-diagnostics.json).
Los 119 artefactos anteriores comprobados y sus originales permanecen intactos.

El siguiente problema es obtener descripciones breves completas sin aumentar
consumo ni eludir los límites de esta reformulación. La definición formal, la
explicación del modelo y los resultados deben seguir distinguiéndose. Faltan
también robustez de futuras candidatas aceptadas y validación prospectiva.

Sin cambios en `PROJECT_STATUS.md`, commits, pushes, instalaciones, servicios
nuevos, APIs de pago, TradingView o dinero real.
