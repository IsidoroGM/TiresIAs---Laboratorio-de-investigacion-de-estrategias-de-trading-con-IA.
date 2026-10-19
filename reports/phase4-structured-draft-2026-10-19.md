# FASE 4 — Contrato compacto experimental

Fecha: 19 de octubre de 2026. Comprobación sin modelo; FASE 4 abierta.

Se añadió `structured_draft`, un prototipo de entrada con solo `entry` y `exit`.
Valida las condiciones con el lenguaje existente y genera descripciones
completas desde sus campos exactos. No pide ni atribuye al modelo título o
hipótesis. Este paso prepara una posible salida más pequeña para el investigador;
no demuestra todavía ahorro de tokens o calidad de generación en una consulta.

La vista previa no fija pregunta de investigación, fuente o presupuesto, no
consulta la memoria de duplicados y no puede adoptarse en una sesión. No
reemplaza propuestas existentes ni libera intentos consumidos. El protocolo
actual de investigación sigue separado y exige su origen y revisión.

## Comprobación artificial

Se usó referencia actual mayor que `1.00` para entrada y menor o igual que
`1e0` para salida. Es un ejemplo de contrato creado para la comprobación, sin
datos de mercado o resultados. La normalización conserva el valor `1` y la
identidad existente de esas reglas:
`8730076caaab37fadd9ace1574d62c58691eb38e56b0d405bf2da100cb8e4c73`.

Se bloquearon red, proveedores, señales, simulaciones, lectura de XML, contexto
de desarrollo y acceso a reservas durante la vista previa. Se conservaron 29
archivos protegidos de reservas y del linaje pendiente. La reformulación
`2d0040bbd7184c1d9cbde9a8eef3ce3b` no se repitió ni encadenó.

El consumo de la tarea es cero consultas de proveedor, cero tokens y 0 USD
nuevo de API. La vista previa no puede atribuir la autoría ni conocer el coste
anterior de cualquier archivo externo: `source_usage` permanece desconocido y
`new_usage` contiene los ceros comprobados. La cuota de Codex es independiente.
No se ejecutaron nuevas simulaciones de investigación.

## Pruebas y evidencia

Se añadieron 37 pruebas: contrato y límites, campos prohibidos, identidad
numérica, conservación de bytes, consumo desconocido, ausencia de red/datos,
JSON duplicado o incompleto, registros de fallo, tamaño máximo, alteraciones,
ubicación sellada, aislamiento del flujo y CLI. La primera ejecución focalizada
aprobó 36; se añadió después el caso de identidad numérica. La suite completa
aprobó **941 pruebas en 79,21 s**, incluyendo las 37 nuevas, con temporal
exclusivo y caché desactivada. No quedaron fallos.

Registro `.local/structured-drafts/cf542656670d4bb4b5b00627bf5dfd55`:

- [Entrada exacta del ejemplo](phase4-structured-draft-2026-10-19/input.json).
- [Vista previa verificada](phase4-structured-draft-2026-10-19/draft.json).
- [Descripción resultante](phase4-structured-draft-2026-10-19/report.md).
- [Auditoría de lecturas](phase4-structured-draft-2026-10-19/io-audit.json).
- [Contexto y archivos protegidos](phase4-structured-draft-2026-10-19/check-context.json).
- [Inventario de siete copias](phase4-structured-draft-2026-10-19/snapshot.json).

Se verificaron 161 copias históricas y sus originales sin cambios. Tampoco se
modificaron módulos ya sellados. No hubo commits, pushes, instalaciones,
servicios nuevos, API de pago, TradingView u operaciones reales.

Pendiente: integrar este contrato solo con origen registrado, contexto de
investigación, memoria compartida de reglas e intentos y revisión separada.
El prototipo no autoriza usar una propuesta pendiente, no hace equivalencia
semántica y no constituye una estrategia aprobada.
