# FASE 4 — Controlador de sesiones de investigación

Fecha: 19 de octubre de 2026. Desarrollo de herramientas; fase abierta.
**761 pruebas aprobadas**, incluidas 30 nuevas.

Se partió del commit `ed31448` aportado por el usuario, con árbol de trabajo
limpio. Se añadió `trading_ai.research_session` sin modificar los módulos
vinculados a los registros anteriores. No se realizaron nuevos commits o pushes.

## Ciclo y límites

El controlador conecta idea, traducción, una posible reformulación, nueva
traducción, revisión técnica, plan, ejecución y lectura contrastada. Separa
creación, propuesta, finalización y consulta de estado en cuatro comandos.

El manifiesto fija antes de consultar una idea inicial, una reformulación como
máximo, cinco consultas de generación y dos simulaciones. Limita la salida a
384 tokens por consulta y el contexto a 4096. El máximo predeterminado de salida
reservada es 1920 tokens; no equivale al consumo medido. No hay reintentos
automáticos, búsqueda continua ni presupuesto de pago habilitado.

El investigador no aprueba sus reglas: la propuesta se detiene para una revisión
técnica explícita. Un rechazo válido termina sin simular. Un error de formato o
hash en la revisión puede corregirse sin regenerar la propuesta. La aceptación
sigue siendo una declaración técnica, no una prueba automática de significado
ni una autenticación del revisor.

Cada consulta reserva un slot antes de enviarse. Los errores y reservas sin
respuesta no devuelven el presupuesto; si falta información, el consumo queda
desconocido. Se reservan también las dos simulaciones antes de llamar al ejecutor.
Si falla el análisis después de calcular, se conservan los resultados del motor.

Un bloqueo impide acciones simultáneas. Cada acción reclamada admite un intento;
copiar o mover una sesión no crea otro presupuesto válido. Se mantienen además
los registros compartidos de duplicados del ejecutor y del feedback. Son
controles de archivos locales, no firmas contra manipulación deliberada conjunta
ni un límite entre todas las sesiones o llamadas manuales a otras herramientas.

## Sesión real preparada, sin iniciar investigación

Se creó la sesión
`.local/research-sessions/6fad6f1f23324fdb9e69c0ae71f77e1d` con el registro de
desarrollo existente. Estado: **`prepared`**. Consumo: **cero consultas de
generación, cero simulaciones y 0 USD de API**.

Durante la comprobación se deshabilitaron el proveedor, las señales y los
backtests, y se bloquearon aperturas de evaluación exterior. La auditoría
contiene 30 rutas de lectura. Preparar y consultar el estado verifican los datos
y el código, pero no inician servicios ni contactan al modelo.

No se volvió a pedir una propuesta real para probar el controlador. El borrador
anterior sigue con las dudas documentadas y no recibió permisos de ejecución.
El presupuesto sellado es revisable antes de iniciar esa sesión.

## Ciclo completo comprobado con datos artificiales

Se conservaron los artefactos del test
`test_revision_path_uses_four_calls_before_review_and_five_in_total`. Utiliza
datos artificiales de `tests/test_holdout.py::setup`, en formato del lector BCE,
y un proveedor en memoria. No son precios históricos reales ni consultas a
Ollama, aunque los contratos de datos conserven etiquetas de formato BCE.

El ejemplo recorrió idea, traducción con duda, reformulación y traducción válida:
cuatro llamadas simuladas y ninguna simulación antes de la revisión. Una revisión
técnica artificial explícita permitió ejecutar las dos cuentas y contrastar el
análisis: cinco llamadas simuladas en total y dos backtests dentro de la sesión.

El estado final fue `completed`. Los 125 tokens de entrada y 200 de salida
registrados en ese ejemplo son valores constantes del proveedor de prueba,
**no consumo medido de un modelo real**. La reserva fue de 1920 tokens de salida.
El ejemplo comprueba el procedimiento y los límites, sin elegir una estrategia
para el histórico real ni demostrar rentabilidad o robustez.

## Comprobaciones

Las 30 pruebas nuevas cubren preparación sin IA, ciclo completo, pausa para
revisión, ruta de cinco consultas, rechazos, datos ausentes, ambigüedad persistente,
corrección de una revisión inválida y bloqueo de una sexta consulta. También
verifican presupuesto tras errores o respuestas ausentes, copias, alteraciones
de manifiesto, proveedores y límites no permitidos, acciones repetidas,
concurrencia, bloqueos previos, inconclusos, fallos de análisis y motor, archivos
modificados y CLI sin opciones para ampliar el presupuesto.

La primera pasada detectó rutas demasiado anidadas para Windows. Los artefactos
se trasladaron a rutas compactas dentro de la sesión, manteniendo los registros
de sus orígenes. No se cambiaron ajustes del sistema ni permisos. La pasada final
completa dio **761 passed en 52,17 segundos**, sin caché y con temporal exclusivo
nuevo según `AGENTS.md`.

Se verificaron los 18 hashes de código de la sesión preparada. No se instalaron
dependencias ni se activaron servicios. Los cálculos, las reglas y los controles
del simulador siguen separados del investigador.

## Evidencias conservadas

- [Manifiesto real preparado](phase4-research-session-2026-10-19/prepared-session.json), [sello](phase4-research-session-2026-10-19/prepared-session.sha256), [evento de preparación](phase4-research-session-2026-10-19/prepared-events.jsonl) y [auditoría](phase4-research-session-2026-10-19/prepared-io-audit.json).
- [Contexto: sesión real y ejemplo artificial](phase4-research-session-2026-10-19/evidence-context.json).
- [Manifiesto del ejemplo](phase4-research-session-2026-10-19/fixture-session.json), [propuesta](phase4-research-session-2026-10-19/fixture-proposal.json) y [resultado del ciclo](phase4-research-session-2026-10-19/fixture-outcome.json).
- [Eventos de propuesta](phase4-research-session-2026-10-19/fixture-propose-events.jsonl) y [finalización](phase4-research-session-2026-10-19/fixture-finish-events.jsonl).
- [Idea inicial](phase4-research-session-2026-10-19/fixture-root-idea-idea.json), [traducción](phase4-research-session-2026-10-19/fixture-root-translation-translation.json), [reformulación](phase4-research-session-2026-10-19/fixture-revised-idea-idea.json) y [nueva traducción](phase4-research-session-2026-10-19/fixture-revised-translation-translation.json).
- [Revisión artificial](phase4-research-session-2026-10-19/fixture-review-review.json), [plan](phase4-research-session-2026-10-19/fixture-plan-plan.json), [resultados artificiales del motor](phase4-research-session-2026-10-19/fixture-execution-results.json) y [lectura contrastada](phase4-research-session-2026-10-19/fixture-analysis-analysis.json).
- [Reserva de simulaciones](phase4-research-session-2026-10-19/fixture-backtests-reservation.json) y [primera](phase4-research-session-2026-10-19/fixture-model-1.json) y [quinta reserva de generación](phase4-research-session-2026-10-19/fixture-model-5.json).
- [Correspondencia completa de las 38 copias y hashes](phase4-research-session-2026-10-19/snapshot.json).

Las copias conservan exactamente sus bytes, sin normalizar finales de línea.
Los manifiestos archivados no son sesiones movidas que se puedan ejecutar con
otro presupuesto. SHA-256 del manifiesto real preparado:
`b3c9ef9d7fe4b9cada028730a1dffb6e3f461067453b9e191778e5caa3f20482`.

Uso y límites en [RESEARCH_SESSION.md](../docs/RESEARCH_SESSION.md). El siguiente
paso operativo será iniciar una propuesta dentro de la sesión preparada. La
investigación de nuevas reglas todavía requerirá revisión, robustez y un
protocolo prospectivo; este desarrollo no convierte el histórico conocido en
evidencia inédita. FASE 4 continúa abierta y `PROJECT_STATUS.md` no se modifica.
Sin conexión TradingView, llamadas de pago u operaciones reales.
