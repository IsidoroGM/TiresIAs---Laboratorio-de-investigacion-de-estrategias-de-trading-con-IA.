# TiresIAs: primer control de campañas — 20/10/2026

Se añade una consulta que contrasta el plan registrado, la memoria guiada vigente,
las reservas y las capturas antes de considerar sus reglas pendientes de revisión.
No consulta modelos, escribe capturas, acepta revisiones o ejecuta cálculos.

## Pruebas con datos artificiales

El primer pase aprobó 31 pruebas en 94,31 segundos. Tras ampliar los casos del
contrato de petición, la comprobación conjunta aprobó **144 pruebas en 230,06
segundos**: 39 de planes, 29 del registro, 41 de capturas y 35 nuevas del control.
Se usaron temporales exclusivos y caché de pytest desactivada según AGENTS.md.

Se comprobaron reglas válidas pendientes de revisión, descripciones mecánicas sin
prosa inventada, JSON incompleto, código o controles introducidos en las reglas,
referencias futuras, duplicados, peticiones ajenas al plan, contratos incompatibles,
errores del proveedor, consumo desconocido y reservas de comparación sin revisión.
También cambios de memoria, reservas o bytes durante la consulta y ausencia de
escrituras, envíos o cálculos. La integración usa las fuentes guiadas completas,
transporte falso y bases temporales, sin modificar los registros de la aplicación.

La recolección global identificó 1.397 pruebas en 0,76 segundos. Es una recolección,
no una nueva suite global ejecutada; la última global comprobada sigue siendo la
de 1.253 pruebas. No se suman pases focalizados para afirmar una global aprobada.

## Consulta de la campaña real

La auditoría `.local/campaign-controller-audits/389adb9a10f1408ea0fb17609bbd4f6b`
consultó la campaña registrada sin inventar capturas o propuestas. El resultado
sigue inactivo, con cero reservas y cero candidatas pendientes de revisión.
Se verificó la vigencia del plan y de sus fuentes guiadas.

Los siete contadores de red, proveedor, cálculo, reserva heredada, evaluación
exterior, reserva de campaña y escritura de capturas quedaron a cero. La base
SQLite mantuvo sus bytes, los nueve archivos históricos de reservas quedaron
intactos y no se crearon las raíces de capturas. PROJECT_STATUS.md conserva su
SHA-256 y la FASE 4 permanece abierta.

Las 289 copias y referencias originales previas se verificaron antes y después.
El [inventario nuevo](phase4-campaign-controller-2026-10-20/snapshot.json) añade
ocho copias: **297 copias y referencias entre 21 inventarios concretos**. No se
presentan como archivos físicos únicos. Conserva consulta, auditoría, huellas,
eventos, script, código y pruebas con nombre no recolectable por pytest.

## Consumo y límites

Consumo nuevo del investigador: **0 consultas, 0 tokens, 0 USD API y 0 backtests**.
El consumo compacto heredado de 2.262 tokens de entrada y 176 de salida, con
0 USD de API, permanece separado; no resume toda la aplicación. Los datos de
pruebas y sus observaciones artificiales no se suman al consumo real.

Una captura con reglas válidas no acredita su transporte, autoría, revisión o
rentabilidad. Se conserva el origen declarado por el llamador y no se completan
respuestas. Solo se admite la petición del plan registrado; faltan peticiones
sucesivas con toda la memoria de campaña. La comprobación de fuentes es optimista,
sin un bloqueo global, y no sustituye el control previo al uso de herramientas.

Siguen pendientes el permiso de campaña, el envío controlado y la conexión de
revisión aceptada, plan y reserva compartida del motor. No se reabren los intentos
consumidos. No hubo instalaciones, servicios nuevos, operaciones con dinero real,
commits o pushes. Uso: [primer control de campañas](../docs/CAMPAIGN_CONTROLLER.md).
