# FASE 4 — Primera propuesta con reglas estructuradas

Fecha: 19 de octubre de 2026.

## Entrega comprobada

`trading_ai.structured_ideas` solicita entrada y salida en el lenguaje de reglas
del motor, con indicador, ventana, retardo y operador explícitos. Python valida
el contrato y compila una condición por lado. No interpreta texto para completar
parámetros ni necesita otra llamada de traducción.

**819 pruebas aprobadas**, incluidas 37 nuevas. Cubren campos y tipos inválidos,
datos no disponibles, retardos futuros, controles y código no admitidos,
trazabilidad, respuestas inválidas con consumo conservado, fuentes alteradas,
memoria, identidad de reglas y concurrencia de duplicados. Se desactivó la caché
de pytest y se utilizó temporal exclusivo según `AGENTS.md`.

El historial estructurado tiene reservas exclusivas compartidas y conserva
propuestas verificadas para el contexto siguiente. Cambiar título, hipótesis,
carpeta o escritura de constantes no convierte las mismas reglas en nuevas.
La herramienta no modifica los contratos, archivos ni presupuestos del
controlador v2, del motor o de las investigaciones anteriores.

## Una comprobación con Ollama local

Registro: `.local/structured-ideas/18fdf9274baa4b96973b8c2f67dab92b`.
Modelo `qwen3.5:4b`, CPU, contexto 4096, salida máxima 384, temperatura cero.
Recibió memoria de cuatro ideas anteriores con nueve fuentes verificadas.
Era la primera propuesta estructurada, sin reglas estructuradas previas.

Resultado: **`pending_semantic_review`**, sin errores. Se compiló y verificó
el registro completo sin pedir traducción ni reformulación. Las reglas son:

- Entrada: EMA de 20 observaciones, `lag=0`, cruza por encima de SMA de 60, `lag=0`.
- Salida: EMA de 20, `lag=1`, cruza por debajo de SMA de 60, `lag=1`.

Las ventanas ya tienen significado explícito. La salida consulta series
retardadas: detecta el cruce una observación después que la misma condición con
`lag=0`, además de la ejecución posterior que aplica el motor. La hipótesis no
explica ese retardo extra. Es un punto concreto para revisión técnica; no se
cambió a cero ni se aprobó automáticamente.

El modelo continuó usando SMA/EMA. La estructura válida no demuestra exploración
de nuevas familias, equivalencia con ideas antiguas, coherencia de la hipótesis,
operaciones suficientes ni mejora de resultados.

| Medida | Consumo |
|---|---:|
| Consultas de generación | 1 |
| Tokens de entrada | 1257 |
| Tokens de salida | 248 |
| Tokens de salida reservados | 384 |
| Duración del proveedor | 68,694 s |
| Coste de API | 0 USD |
| Traducciones / simulaciones / reintentos | 0 / 0 / 0 |

No se iniciaron servicios, instalaron dependencias o consultaron APIs de pago.
La ejecución local consume recursos del equipo.

## Evidencia y límites

Las [26 copias exactas y hashes](phase4-structured-ideas-2026-10-19/snapshot.json)
incluyen [propuesta original y reglas](phase4-structured-ideas-2026-10-19/proposal.json),
[solicitud, respuesta y consumo](phase4-structured-ideas-2026-10-19/events.jsonl),
[informe](phase4-structured-ideas-2026-10-19/report.md), memorias y sus fuentes,
reserva, [estado](phase4-structured-ideas-2026-10-19/check-context.json) y
[auditoría](phase4-structured-ideas-2026-10-19/io-audit.json).
Los 41 artefactos anteriores comprobados y sus originales mantienen sus hashes.
El patrón de `.gitattributes` conserva los bytes de las nuevas copias.

Durante la comprobación se bloquearon aperturas de evaluación exterior y se
desactivaron señales, traducción y backtests. `executable` sigue en `false`, sin
resultados calculados ni equivalencia semántica verificada.

Esta entrada permanece separada del controlador v2. El siguiente desarrollo
es conectar su origen con revisión técnica, plan y presupuesto de sesión, sin
fabricar respuestas o aprobaciones del protocolo anterior. El uso y las
limitaciones se documentan en [STRUCTURED_IDEAS.md](../docs/STRUCTURED_IDEAS.md).

FASE 4 sigue abierta. `PROJECT_STATUS.md` no se modifica. Sin commits, pushes,
conexión TradingView u operaciones reales.
