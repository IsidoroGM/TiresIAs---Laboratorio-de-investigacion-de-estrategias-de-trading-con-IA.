# Consulta compacta local — 20/10/2026

La respuesta contiene reglas completas y se registra como **duplicate_rules**:
repite la propuesta estructurada original. No se aprueba, no se simula y no se
repite la consulta. El formato compacto evita tener que completar una frase del
modelo; esta comprobación no aporta una estrategia nueva o mejor.

Las reglas recibidas indican entrada cuando EMA20 actual cruza sobre SMA60
actual y salida cuando EMA20 de una observación atrás cruza bajo SMA60 de una
observación atrás. La [descripción completa](phase4-compact-candidate-2026-10-20/candidate/report.md)
la deriva Python de esos campos. No hay título o hipótesis atribuidos al modelo.
El retardo de la salida ya figuraba en la propuesta original pendiente.

## Evidencia y consumo

[Candidata](phase4-compact-candidate-2026-10-20/candidate/candidate.json),
[respuesta original y eventos](phase4-compact-candidate-2026-10-20/candidate/events.jsonl),
[trabajo y proveedor](phase4-compact-candidate-2026-10-20/candidate/job.json),
[reserva](phase4-compact-candidate-2026-10-20/reservation/reservation.json),
[auditoría](phase4-compact-candidate-2026-10-20/audit/audit.json) e
[inventario de copias](phase4-compact-candidate-2026-10-20/snapshot.json).

| Origen | Consultas | Entrada | Salida | API USD |
|---|---:|---:|---:|---:|
| Propuesta anterior heredada | 1 | 1257 | 248 | 0 |
| Reformulación anterior heredada | 1 | 1289 | 239 | 0 |
| Consulta compacta nueva | 1 | 2262 | 176 | 0 |

El consumo heredado no se vuelve a producir. Esta tabla cubre ese linaje, no
todos los intentos históricos de la aplicación. La nueva consulta utilizó el
servicio existente Ollama 0.40.6, Qwen3.5:4b y CPU solicitada, con un límite de
4.096 tokens de contexto y 384 de salida. El servidor declaró finalización
normal, 0 tokens de entrada en caché y 71,45 s de duración. La menor salida de
este intento no demuestra una reducción general de consumo; el contexto difiere.

Hubo seis solicitudes de metadatos en el controlador y una comprobación anterior
independiente de versión. No son inferencias ni llamadas de pago. Los recursos
del equipo no se han medido como coste monetario.

La auditoría bloqueó las rutas controladas de señales, backtests, acciones de
sesión y archivos de evaluación exterior; sus cuatro contadores quedaron en
cero. Verificó **205 copias históricas y sus originales** antes y después, y
**20 copias nuevas**, todas con los bytes y SHA-256 esperados.

La petición seguía vigente al finalizar porque el duplicado conservó la reserva
de reglas original. **El intento de generación compacto sí queda consumido**:
la vigencia del contexto no concede otro envío. La reformulación
`2d0040bbd7184c1d9cbde9a8eef3ce3b` y ambas sesiones anteriores permanecen intactas.

## Comprobaciones y pendientes

Antes de la consulta pasó la suite completa: **1.104 pruebas en 268,20 s**, con
caché desactivada y temporal exclusivo según AGENTS.md. Los módulos productores
existentes y sus registros se conservaron. El ejecutor compacto añadido después
se está comprobando por separado con datos artificiales; no se ha aplicado a
esta candidata duplicada.

Pendientes: integrar la memoria de intentos y revisiones compactas en una futura
petición, y definir cualquier ampliación del presupuesto sin reiniciar intentos
consumidos. La evaluación histórica ya es conocida y no se presenta como inédita.
FASE 4 sigue abierta; PROJECT_STATUS.md permanece intacto. Sin commits, pushes,
instalaciones, servicios nuevos, TradingView, API de pago o dinero real.
