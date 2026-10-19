# FASE 4 — Memoria de revisiones estructuradas

Fecha: 19 de octubre de 2026. Sin nuevas consultas o simulaciones de investigación.

`structured_review_memory` conserva las decisiones y motivos de las revisiones
vinculadas a sesiones registradas del mismo desarrollo. Verifica la reserva,
propuesta y revisión de origen. No reabre acciones ni consulta el resultado
financiero de la sesión; una revisión aceptada no se presenta como un cierre
completo o una estrategia rentable.

Un cierre consumido sin revisión registrada sigue consumido. Las sesiones
pendientes no se aprueban. Si una propuesta queda fuera de las reservas del
contexto base, exige actualizarlo antes de capturar su sesión. No hay permisos
de generación, revisión o simulación.

## Comprobación sobre las revisiones anteriores

Registro `.local/structured-review-memory/ad12b5680d6a4cb3aab5fa7d6f0fec7a`.
Las dos sesiones conservan `needs_clarification` y su cierre consumido:
`fd10b4fe5d4a4201a1bec4f78a1e61ca` y `bb2880ffb7c74c37abcece9c5275ffc2`.
No se repitió o encadenó la reformulación `2d0040bbd7184c1d9cbde9a8eef3ce3b`.

Los motivos se conservan como texto del revisor sin verificar su exactitud,
junto a longitudes calculadas de la propuesta. El motivo original de la hija
decía 160 caracteres; la longitud comprobada es 159. La memoria no reescribe
ese motivo ni cambia la decisión. Se adjunta la fe de erratas ya existente.

La captura bloqueó red, proveedores, acciones, señales, backtests,
`evaluation.xml`, `comparison.json`, `outcome.json` y los archivos de resultados
financieros de las sesiones. Conservó 29 archivos protegidos sin cambios.

| Consumo de proveedor | Heredado de ambas propuestas | Nuevo en esta tarea |
|---|---:|---:|
| Consultas | 2 | 0 |
| Tokens de entrada | 2546 | 0 |
| Tokens de salida | 487 | 0 |
| Coste de API | 0 USD | 0 USD |

El consumo heredado incluye 1257/248 del origen y 1289/239 de la hija. Copiar
sus registros no vuelve a consumirlo. El módulo también conserva valores
desconocidos como desconocidos. La cuota usada por Codex es independiente.

## Pruebas y evidencia

20 pruebas nuevas. La primera ejecución focalizada aprobó 19 en 7,81 s; después
se añadió el caso de consumo heredado desconocido. La suite completa aprobó
**983 pruebas en 91,50 s**, incluyendo las 20 nuevas, con temporal exclusivo
y caché desactivada. No quedaron errores de implementación o pruebas fallidas.

Los casos cubren sesiones pendientes, aclaradas o rechazadas, revisión aceptada
seguida de fallo del plan, cierre consumido sin revisión, origen desconocido,
separación del cálculo, contexto desactualizado, fuentes alteradas, cambio de
etapa, límites, ubicación y CLI. Las interrupciones artificiales son casos de
prueba controlados, sin llamadas reales al modelo.

Dieciséis copias nuevas con referencias y SHA-256; se verificaron 179 copias
históricas y sus originales sin cambios:

- [Memoria verificada](phase4-structured-review-memory-2026-10-19/reviews.json).
- [Informe con los motivos originales](phase4-structured-review-memory-2026-10-19/report.md).
- [Reservas de sesión](phase4-structured-review-memory-2026-10-19/sessions.json).
- [Auditoría de lecturas](phase4-structured-review-memory-2026-10-19/io-audit.json).
- [Contexto y consumo](phase4-structured-review-memory-2026-10-19/check-context.json).
- [Fe de erratas conservada](phase4-structured-review-memory-2026-10-19/known-review-erratum.json).
- [Inventario](phase4-structured-review-memory-2026-10-19/snapshot.json).

El alcance se limita a las sesiones registradas capturadas; no incluye todas
las revisiones independientes ni las sesiones posteriores. Si una sesión cambia
de etapa, la captura puede necesitar renovación. Sigue pendiente preparar la
petición compacta sin convertir motivos heredados en instrucciones confiables.

FASE 4 sigue abierta. No se modificaron módulos sellados, decisiones o
`PROJECT_STATUS.md`. Sin commits, pushes, instalaciones, servicios nuevos,
APIs de pago, TradingView u operaciones reales.
