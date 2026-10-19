# FASE 4 — Reformulaciones y lectura contrastada

Fecha: 19 de octubre de 2026. Desarrollo de herramientas; fase abierta.
**731 pruebas aprobadas**, incluidas 32 nuevas.

Se añadió `trading_ai.agent_feedback`, con tareas independientes de reformulación
y análisis. Conserva antecedentes y limita a una consulta por origen o cálculo,
sin bucles de corrección, simulaciones nuevas o permisos para aprobar reglas.

## Reformulación real conservada

Se verificó la traducción anterior en `needs_clarification` y se solicitó una
única revisión al modelo local Qwen3.5:4b, CPU, contexto 4096, salida máxima
384 tokens y temperatura 0. Consumo medido: **760 tokens de entrada y 193 de
salida; coste de API 0 USD**. Duración del proveedor: 79,871 segundos; intento
completo: 82,263 segundos. No hubo otra consulta ni reintento automático.

La nueva propuesta se tituló «Entrada SMA/EMA BCE confirmada». Su identidad es
`5b3da89c8ccac17ea2b9aeb0185ab2dbc578c47610db1739f594d7cbce053a45`.
Conserva como origen la idea
`a59f988282c8de81e0aff2695e55147cd024a6cd7d2ab55acba31be2aa826d7e`,
con la propuesta original, hashes de archivos y traducción y profundidad uno.
La idea y la traducción anteriores permanecieron intactas.

**La prueba no resolvió todas las dudas.** El modelo mantuvo una entrada referida
al próximo dato, sin aclarar bien confirmación y ejecución, conservó el parámetro
`reference_series: 1` sin significado suficiente y propuso «Cerrar al siguiente
cruce inverso o al final del periodo de datos». Ese cierre al final del periodo
no pertenece al contrato actual, que valora posiciones abiertas sin forzarlo.
Tampoco queda completamente explicitado qué media corresponde a cada ventana.

El JSON es válido solo en formato: queda `pending_tool_mapping`, con permisos de
ejecución ausentes y resultados `null`. No se tradujo, revisó como aceptado ni
simuló. No se declara que esta propuesta sea más clara, novedosa o rentable.
La hipótesis es una declaración del modelo, no un resultado calculado.

El intento de reformulación queda consumido para ese origen y desarrollo.
Copiar archivos o pedir otra traducción de la misma idea no libera otra consulta.
Una idea ya reformulada no inicia una cadena automática. Estos límites no son
un presupuesto global entre todas las ideas distintas.

La comprobación real deshabilitó generación de señales y backtests y rechazó
aperturas de evaluación exterior. Su auditoría contiene 33 rutas; el único XML
abierto fue desarrollo. El contexto enviado al modelo solo incluye metadatos
de desarrollo, reglas originales y el motivo previo marcado como no verificado,
sin precios ni métricas de estrategias. El linaje se verificó sin otra consulta.

## Lectura de resultados verificados

El analizador exige una ejecución completa que pase el verificador de datos,
fuentes, código, reserva, archivos y cierre. Envía resúmenes calculados de base
y candidata, criterio y controles. Acepta solo cuatro campos coincidentes con
Python: estado del criterio, comparación de rentabilidad, comparación de drawdown
y alcance conocido. Una conclusión inventada o con métricas añadidas se rechaza,
conservando respuesta y consumo. No se aceptan explicaciones libres de causas.

Si la conclusión de Python ya es inconclusa, no contacta al proveedor y registra
el resultado con cero consultas. El análisis no ejecuta backtests ni permite
modificar parámetros. Una lectura aceptada requiere su evento de cierre y hash;
un archivo parcial o un error no bastan.

La evidencia positiva procede de pytest: datos artificiales del fixture
`tests/test_holdout.py::setup` y un proveedor en memoria. No son referencias
históricas reales aunque el lector utilice el formato y las etiquetas BCE.
Los valores de tokens del proveedor de prueba son constantes simuladas para
comprobar registros; **no se suman al consumo medido de la consulta real**.
No se consultó otro modelo para leer resultados en este desarrollo.

El test verificó que el contexto contiene exactamente los resúmenes calculados,
que la lectura coincide con Python, que no se recalcula y que los archivos de
la ejecución permanecen intactos. El caso artificial cumplió el criterio; esto
no aporta evidencia sobre una estrategia real. Otros tests rechazan conclusiones
incorrectas y comprueban el caso inconcluso sin contactar al proveedor.

## Presupuestos, errores y comprobaciones

Las reservas exclusivas se guardan en `.local/agent-feedback-access`. Son
independientes de la salida y sobreviven a errores posteriores; no hay borrado
o reintento automáticos. Se conservan uso conocido y respuestas inválidas;
ausencia de información de consumo se registra como desconocida.

Las 32 pruebas nuevas cubren conservación de antecedentes, compatibilidad con
el traductor, verificación de linaje, cambios de fuentes y reserva, duplicados,
copias y motivos alternativos, cadenas bloqueadas incluso sin el campo de linaje,
respuesta idéntica, JSON inválido, errores y consumo. También verifican lectura
de resúmenes, conclusiones incorrectas o inventadas, resultados modificados,
inconclusos, concurrencia, CLI y OpenAI desactivado antes de crear el intento.

Suite completa: **731 passed en 78,88 segundos**, sin caché y con temporal
exclusivo nuevo según `AGENTS.md`. Se conservaron los módulos vinculados al
registro previo; no hubo dependencias nuevas, servicios adicionales ni llamadas
de pago. El modelo local sí consume recursos del equipo.

## Evidencias

- [Contexto: consulta real y proveedor simulado](phase4-agent-feedback-2026-10-19/evidence-context.json).
- [Reformulación pendiente](phase4-agent-feedback-2026-10-19/revised-idea.json), [solicitud y respuesta](phase4-agent-feedback-2026-10-19/revision-events.jsonl), [reserva](phase4-agent-feedback-2026-10-19/revision-access.json) y [auditoría](phase4-agent-feedback-2026-10-19/revision-io-audit.json).
- [Idea original](phase4-agent-feedback-2026-10-19/parent-idea.json), [eventos](phase4-agent-feedback-2026-10-19/parent-idea-events.jsonl), [traducción con dudas](phase4-agent-feedback-2026-10-19/parent-translation.json) y [eventos de traducción](phase4-agent-feedback-2026-10-19/parent-translation-events.jsonl).
- [Lectura artificial contrastada](phase4-agent-feedback-2026-10-19/fixture-analysis.json), [eventos](phase4-agent-feedback-2026-10-19/fixture-analysis-events.jsonl) y [reserva temporal](phase4-agent-feedback-2026-10-19/fixture-analysis-access.json).
- [Resultados artificiales de entrada](phase4-agent-feedback-2026-10-19/fixture-results.json), [eventos de ejecución](phase4-agent-feedback-2026-10-19/fixture-events.jsonl), [plan](phase4-agent-feedback-2026-10-19/fixture-plan.json) y [datos artificiales](phase4-agent-feedback-2026-10-19/fixture-development.xml).
- [Contabilidad base](phase4-agent-feedback-2026-10-19/fixture-baseline.json), [contabilidad candidata](phase4-agent-feedback-2026-10-19/fixture-candidate.json) e [informe del ejemplo](phase4-agent-feedback-2026-10-19/fixture-report.md).
- [Correspondencia de copias y hashes](phase4-agent-feedback-2026-10-19/snapshot.json).

Son copias exactas conservadas sin normalizar finales de línea. La reformulación
real está en `.local/idea-revisions/625561cd5fd64933a702ebff1c8ccfb0`.
SHA-256 de su `idea.json`:
`bedc34c0ff43fe8903ee4eeae0e775442623bf9dd78c0acf9cc736723ae0d220`.
Los hashes comparan archivos locales; no son firmas contra manipulación conjunta.

Uso y límites en [AGENT_FEEDBACK.md](../docs/AGENT_FEEDBACK.md). Queda pendiente
el controlador con presupuesto global de investigación y el flujo completo para
propuestas precisas, revisión y experimentos. El histórico sigue siendo conocido.
FASE 4 permanece abierta; `PROJECT_STATUS.md` conserva el cierre de FASE 3.
Sin commits, pushes, conexión TradingView ni operaciones reales.
