# FASE 4 — Memoria de propuestas y detección temprana de duplicados

Fecha: 19 de octubre de 2026. Corrección del reinicio sin contexto observado en
el [primer inicio operativo](phase4-session-proposal-2026-10-19.md).

## Cambio y comprobaciones

Las nuevas sesiones capturan propuestas y motivos de traducción del mismo
desarrollo en `memory.json`, con fuentes verificadas y un hash en el manifiesto.
La solicitud real registra ese contexto antes de consultar. No incorpora
evaluación exterior ni selecciona ideas por resultados. El módulo de memoria
queda separado del motor y de los controles del simulador.

La comparación previa a traducir ignora cambios de título, hipótesis, espacios,
mayúsculas, orden de parámetros y representaciones como `20`/`20.0`. Un duplicado
inicial termina como `duplicate_idea` después de una consulta. Una reformulación
que solo retitula la idea se detiene antes de otra traducción. No es una prueba
de equivalencia matemática: una paráfrasis puede escapar al filtro.

**782 pruebas aprobadas**, incluidas 21 nuevas: detección, avance de propuestas
distintas, registro del contexto real, integridad de memoria y fuentes,
respuestas inválidas con consumo conservado y ausencia de simulaciones antes
de revisión. Se utilizó temporal exclusivo y caché de pytest desactivada.

La sesión anterior conserva sus archivos, intento y reservas. Las doce copias
de su evidencia y sus originales siguen coincidiendo con sus hashes. Una sesión
de protocolo anterior se conserva como historial y no se reinicia bajo el
protocolo nuevo.

## Comprobación con el modelo local

Sesión nueva: `.local/research-sessions/869b4d81509e490399a4e5d102a8235b`.
Ollama local `qwen3.5:4b`, contexto 4096, salida máxima 384, temperatura cero.
Memoria inicial: dos ideas distintas según la huella y cinco fuentes verificadas.

El ciclo terminó de forma registrada en **`needs_clarification`**, sin bloqueo
activo ni error del controlador. Generó una idea, pidió una traducción, empleó
su única reformulación y pidió la segunda traducción. No tropezó con la reserva
ya consumida del origen anterior; tampoco la borró o amplió sus límites.

El modelo recibió la memoria, pero siguió usando SMA/EMA y el parámetro
`reference_series: 1`. No concretó suficientemente qué indicador usa cada
ventana. Por tanto, la memoria **no ha resuelto la precisión de las propuestas**
ni demuestra exploración de nuevas familias de estrategias.

Los motivos de traducción son texto del modelo sin verificar. Incluyen
afirmaciones incorrectas sobre necesitar OHLC para un cruce y sobre que
`reference` deba ser un indicador calculado. El lenguaje del motor sí admite
referencias y cruces con datos actuales y pasados. Esas explicaciones no se
aceptaron como hechos ni motivaron cambios del simulador.

| Etapa | Entrada | Salida | Duración del proveedor |
|---|---:|---:|---:|
| Idea con memoria | 1138 | 183 | 77,840 s |
| Traducción | 419 | 183 | 40,704 s |
| Reformulación | 754 | 188 | 49,391 s |
| Segunda traducción | 424 | 167 | 37,724 s |
| Total | 2735 | 721 | 205,660 s |

Cuatro consultas; 1536 tokens de salida reservados y 721 informados como usados.
**0 USD de API y cero simulaciones reservadas o ejecutadas.** No hubo reintentos,
servicios nuevos, dependencias instaladas o APIs de pago. El uso local consume
recursos del equipo.

## Evidencias y alcance

Las [29 copias exactas y sus hashes](phase4-idea-memory-2026-10-19/snapshot.json)
incluyen [memoria](phase4-idea-memory-2026-10-19/memory.json), fuentes anteriores,
[manifiesto](phase4-idea-memory-2026-10-19/session.json), solicitudes y respuestas,
reservas, [cierre de propuesta](phase4-idea-memory-2026-10-19/proposal.json),
[estado final](phase4-idea-memory-2026-10-19/check-context.json) y
[auditoría](phase4-idea-memory-2026-10-19/io-audit.json).
Se bloquearon aperturas de evaluación exterior y se desactivaron señales y
backtests en esta comprobación. El patrón de `.gitattributes` conserva los bytes.

El siguiente problema es exigir propuestas más estructuradas desde su origen
para reducir la ambigüedad, manteniendo la revisión técnica. No se resolvió
mediante intentos sucesivos hasta obtener una respuesta aceptable.

FASE 4 sigue abierta y `PROJECT_STATUS.md` no se modifica. Sin commits, pushes,
conexión TradingView ni operaciones reales.
