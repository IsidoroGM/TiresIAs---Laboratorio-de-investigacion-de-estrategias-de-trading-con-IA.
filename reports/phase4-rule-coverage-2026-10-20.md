# Cobertura de las reglas capturadas — 20/10/2026

El diagnóstico encontró **tres registros, dos identidades de regla y una plantilla**
al ignorar los números solo para agrupar plantillas. El tercer registro repite las
reglas originales. Las dos identidades conservan sus parámetros de retardo; no se
consideran equivalentes por compartir estructura.

[Perfil y parámetros](phase4-rule-coverage-2026-10-20/coverage/coverage.json),
[descripción](phase4-rule-coverage-2026-10-20/coverage/report.md),
[auditoría](phase4-rule-coverage-2026-10-20/audit/audit.json) e
[inventario](phase4-rule-coverage-2026-10-20/snapshot.json).

Los tipos directos observados son `ema` y `sma`. En esos campos no aparecen
`constant`, `reference`, `rolling_max` o `rolling_min`. Esto solo describe las
reglas tipadas capturadas; las medias sí utilizan referencias subyacentes. No se
analizan las ideas de texto libre ni se declaran estrategias nuevas, mejores o
recomendadas a partir de esta lista.

Consumo nuevo: **cero consultas, tokens, señales, backtests y 0 USD de API**.
Las cuatro rutas bloqueadas quedaron sin invocaciones. Se verificaron **236
copias anteriores y sus referencias originales**, además de **ocho copias nuevas**.
El presupuesto compacto y PROJECT_STATUS.md permanecieron intactos.

El módulo pasó 19 pruebas iniciales en 57,53 s. Tras aplicar el límite al JSON
almacenado con indentación y añadir su regresión, pasó **20 pruebas en 63,07 s**.
La última suite completa anterior al módulo fue **1.213 pruebas en 789,22 s**.
No se presenta la suma de esos grupos como una suite global ya ejecutada.

FASE 4 permanece abierta. La propuesta real sigue duplicada y no se simula o
reformula. No se han hecho commits, pushes, instalaciones, servicios nuevos,
llamadas de pago u operaciones con dinero real.
