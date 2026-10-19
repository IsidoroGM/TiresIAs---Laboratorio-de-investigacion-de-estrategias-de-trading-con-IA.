# FASE 4 — Revisión, plan, ejecución y sesión estructurados

Fecha: 19 de octubre de 2026. Desarrollo autónomo autorizado, sin solicitudes
de validación intermedias. No cierra FASE 4.

## Integración comprobada

Se añadieron `structured_planning`, `structured_execution` y `structured_session`.
La revisión identifica la propuesta real y comprueba también los retardos.
Aceptar exige seis declaraciones técnicas; una decisión pendiente o negativa
no genera un plan. No se fabrican traducciones ni respuestas del modelo.

El plan fija controles y datos del desarrollo anterior. El ejecutor reutiliza
cálculos y conclusión del motor y comparte la reserva de identidad con el
ejecutor anterior. La sesión atribuye la consulta que ya generó la propuesta,
reserva dos simulaciones como máximo y no hace llamadas nuevas al modelo.
Los intentos no se repiten al fallar ni al cambiar carpeta o protocolo.

**863 pruebas aprobadas**, incluidas 44 nuevas: 27 del flujo y 17 de la sesión.
Se probaron revisión incompleta, controles alterados incluso con sello rehecho,
concurrencia, identidad compartida, fallos del motor, fuentes alteradas y
verificación sin repetir cálculos. Caché desactivada y temporal exclusivo.

## Propuesta local existente: pendiente, sin forzar ejecución

Sesión `.local/structured-sessions/fd10b4fe5d4a4201a1bec4f78a1e61ca`.
La revisión separada del investigador identificó el retardo `lag=1` de la salida
que la hipótesis no explicaba. Se registró **`needs_clarification`**, con
`exit_matches_hypothesis=false` y `no_unresolved_ambiguity=false`.

No se modificó la propuesta, no se supuso equivalencia y no se abrió el plan.
Cero simulaciones reservadas, cero llamadas nuevas y 0 USD nuevos de API.
Se atribuyeron los 1257 tokens de entrada y 248 de salida de su generación
anterior, sin volver a consumirlos ni ocultarlos.

## Demostración artificial completa

Carpeta `.local/sd/8b966cb869ab4c46a2ceec99fd706206`.
Son 44 observaciones inventadas en formato XML, divididas en bloques artificiales.
No son precios de mercado ni evidencia histórica. Las respuestas de proveedor
son programadas, sin un modelo real. La preparación también calcula ejemplos;
el contador siguiente se refiere solo al ejecutor estructurado comprobado.

La hipótesis artificial declara entrada con referencia >1 y salida <=1,
ambas con `lag=0`. Se revisó y aceptó ese contrato antes de consultar el resultado.
Se completaron plan, dos cuentas independientes y conclusión de Python, sin
alterar capital, costes, tamaño o criterio al ver las métricas.

| Resultado del ejemplo artificial | Base SMA2/SMA4 | Candidata de umbral |
|---|---:|---:|
| Capital inicial | 1000 | 1000 |
| Capital final | 826,900885 | 902,652355 |
| Rentabilidad % | -17,309912 | -9,734764 |
| Drawdown máximo % | 17,309912 | 15,613957 |
| Cierres | 3 | 4 |
| Posición abierta final | No | Sí |

Python indicó `met` para el criterio relativo de mayor rentabilidad sin más
drawdown. **Ambas rentabilidades son negativas.** El ejemplo comprueba el
procedimiento; no establece una estrategia rentable o superior.

Dos simulaciones del ejecutor, cero llamadas reales a modelos y 0 USD de API.
La valoración final conserva la posición abierta sin forzar su cierre.

## Evidencia y continuidad

[52 copias exactas y hashes](phase4-structured-pipeline-2026-10-19/snapshot.json):
caso [local pendiente](phase4-structured-pipeline-2026-10-19/live/context.json),
[revisión técnica](phase4-structured-pipeline-2026-10-19/live/technical-assessment.json),
caso [artificial completo](phase4-structured-pipeline-2026-10-19/synthetic/context.json),
[plan](phase4-structured-pipeline-2026-10-19/synthetic/plan-plan.json),
[resultados](phase4-structured-pipeline-2026-10-19/synthetic/execution-results.json) e
[informe calculado](phase4-structured-pipeline-2026-10-19/synthetic/execution-report.md).
Se conservaron los 67 artefactos anteriores comprobados y sus originales.

Las auditorías bloquearon evaluación exterior durante el flujo estructurado.
En el caso local también se desactivaron IA, señales y backtests. El caso
artificial bloqueó proveedores reales; su preparación está delimitada aparte.

El uso se documenta en [STRUCTURED_WORKFLOW.md](../docs/STRUCTURED_WORKFLOW.md).
Continúan pendientes la reformulación estructurada acotada y las comprobaciones
de robustez de futuras propuestas aceptadas. No se reabre la evaluación conocida.
Sin cambios en `PROJECT_STATUS.md`, commits, pushes, instalaciones, servicios
nuevos, APIs de pago, TradingView o dinero real.
