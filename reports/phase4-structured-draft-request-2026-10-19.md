# FASE 4 — Petición compacta sin enviar

Fecha: 19 de octubre de 2026. `structured_draft_request` prepara mensajes y
esquema desde el contexto y la memoria de revisiones verificados. El sistema
mantiene instrucciones fijas; las declaraciones heredadas se codifican como
datos no fiables. No se convierten motivos del revisor en hechos o instrucciones.

Registro `.local/structured-draft-requests/1646833181eb44c386eb32872f245afa`:
**10.970 bytes**, cuatro ideas heredadas, dos reglas registradas, dos reservas
consumidas y dos revisiones. No se omiten entradas o truncan motivos. Si la
petición supera 12.288 bytes, la preparación falla antes de producirla.

El recuento de tokens sigue desconocido; no se ha verificado que encaje en la
ventana de un proveedor. `submitted`, `provider_configured` y `generation_ready`
son falsos. No se envió la petición, reservó un intento o modificó una sesión.
Las propuestas pendientes no se reformularon o simularon.

Consumo nuevo: cero consultas o tokens de proveedor, 0 USD de API y cero nuevas
simulaciones de investigación. El consumo anterior permanece en sus fuentes:
1257/248 tokens del origen y 1289/239 de la hija, sin volver a consumirlos.
La cuota de Codex es independiente del contador del proyecto.

Se añadieron 10 pruebas: separación de instrucciones y datos, cobertura,
ausencia de envío, conservación de fuentes, límite sin truncamiento,
manipulación, ubicación y CLI. Suite completa: **993 aprobadas en 101,27 s**,
con temporal exclusivo y caché desactivada. No quedaron errores.

La comprobación bloqueó proveedores, red, acciones, señales, backtests,
evaluación exterior y archivos financieros de las sesiones. Conservó 29
archivos protegidos. Se verificaron 195 copias históricas y sus originales.
Se guardan seis copias nuevas:

- [Petición exacta sin enviar](phase4-structured-draft-request-2026-10-19/request.json).
- [Metadatos verificables](phase4-structured-draft-request-2026-10-19/preview.json).
- [Contexto y consumo](phase4-structured-draft-request-2026-10-19/check-context.json).
- [Auditoría](phase4-structured-draft-request-2026-10-19/io-audit.json).
- [Inventario SHA-256](phase4-structured-draft-request-2026-10-19/snapshot.json).

Pendientes: vigencia del contexto, límites reales y reserva controlada antes de
una generación futura. Este paso no demuestra ahorro de tokens o calidad de
una respuesta. FASE 4 sigue abierta; no se modificaron módulos sellados o
`PROJECT_STATUS.md`. Sin commits, pushes, instalaciones, servicios nuevos,
APIs de pago, TradingView u operaciones reales.
