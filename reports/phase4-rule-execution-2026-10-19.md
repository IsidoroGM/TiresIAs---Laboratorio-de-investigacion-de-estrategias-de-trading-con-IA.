# FASE 4 — Ejecutor de planes de reglas

Fecha: 19 de octubre de 2026. Desarrollo de herramientas; fase abierta.
**699 pruebas aprobadas**, incluidas 30 nuevas del ejecutor.

`trading_ai.rule_execution` verifica un plan revisado, reserva un único intento
y ejecuta una base y una candidata con el motor existente. Conserva las dos
contabilidades completas, datos utilizados, conclusiones de Python y errores.
No consulta al modelo ni cambia controles o reglas para mejorar el resultado.

## Presupuesto y repeticiones

La reserva exclusiva se guarda antes de generar señales o simular en
`.local/rule-execution-access`. La identidad combina datos, reglas, base,
controles y supuestos de ejecución. El nombre técnico y el criterio no cambian
los cálculos y no liberan otro intento. Tampoco lo hacen copiar un plan, usar
otra carpeta de salida o registrar una revisión nueva con las mismas reglas.

Dos intentos concurrentes no pueden reservar la misma identidad. Un fallo tras
reservar consume el intento, aunque queden simulaciones sin completar. No se
borra la marca ni hay reintentos automáticos. Una interrupción abrupta tampoco
libera el intento. Las marcas son archivos locales: no impiden su borrado o una
manipulación deliberada, ni detectan toda equivalencia matemática entre reglas.

Se comprueban otra vez fuentes, plan, datos, código y reserva antes de cada
backtest y al terminar. Ambas cuentas usan las mismas observaciones inmutables,
capital, costes y tamaño. La ejecución sigue siendo en la referencia siguiente,
sin posiciones heredadas ni cierre forzado de posiciones abiertas.

## Evidencia positiva con datos artificiales

Se conservó una ejecución de la suite pytest, identificada expresamente como
**ejemplo artificial**: 22 observaciones, base SMA2/4 y una regla sintética de
umbral. El proveedor del test es un objeto en memoria; no se consultó Ollama
ni ningún otro servicio. Este ejemplo comprueba contratos y contabilidad,
sin elegir una estrategia nueva para el histórico real.

Los precios proceden de `tests/test_holdout.py::setup`, no del BCE. El XML usa
el formato del lector BCE; las etiquetas de fuente de ese contrato no convierten
estos valores artificiales en referencias históricas reales. El contexto de la
evidencia declara esta procedencia de forma separada y explícita.

El ejecutor completó exactamente sus dos simulaciones: tres cierres de base
y cuatro de candidata. La conclusión calculada fue `met` en ese ejemplo
artificial, sin significado para rentabilidad real. Pytest contrastó además las
dos contabilidades completas con llamadas de referencia al motor, verificó
fechas de ejecución posteriores a sus señales y comprobó que las fuentes
quedaron intactas. Esos cálculos de comprobación pertenecen a las pruebas.

Identidad del ejemplo:
`6788da8c51cb467ad2b6712555c73c4d9a9e04a8f1b5d0dee6fedab70d05fd1a`.
Se usó un registro temporal exclusivo del test, no la carpeta de reservas de
la aplicación. La lectura verificada posterior no ejecutó otras simulaciones.

## Borrador real todavía bloqueado

La propuesta anterior continúa en `needs_clarification`. Su revisión bloqueó
la preparación y no creó un plan. Se comprobó que el ejecutor rechaza ese
intento incompleto antes de reservar: sin generar señales, abrir XML históricos
ni simular. No se fabricó un plan aceptado para poder pasar la prueba.

El registro contiene `execution_failed`, `access_claimed: false`, cero slots
consumidos y cero consultas de IA. La comprobación deshabilitó expresamente el
proveedor y las funciones de cálculo y bloqueó aperturas de evaluación exterior.
Su auditoría registra 18 rutas de apertura, incluida la del plan inexistente.
No se ejecutó una estrategia nueva sobre el histórico real ni se modificó el
simulador, la idea o los registros anteriores.

## Lectura verificada y errores

El comando `--verify-run` exige cierre `execution_completed`, hashes de los
archivos calculados y del informe, coincidencia con el plan y la reserva
original y una conclusión consistente con las métricas. No recalcula ni reserva
otro intento. Cambiar archivos o fuentes invalida la lectura verificada.

Los resultados parciales permanecen ante fallos. Si falla la escritura del
informe, puede quedar `results.json`, pero el evento final será de error: ese
archivo solo no acredita una ejecución completa. El verificador lo rechaza.
Los hashes son comprobaciones locales, no firmas contra manipulación conjunta
de archivos y evidencias.

Las 30 pruebas nuevas cubren contabilidad íntegra, controles y datos comunes,
ejecución posterior, repetición, copias, preparación duplicada, renombrado con
nueva revisión, concurrencia, cambios durante el cálculo, presupuestos alterados,
fallos de carga y motor, interrupción abrupta, contexto Decimal, cero cierres,
CLI y alteraciones de resultados, informe, datos, eventos o reserva.

Suite completa: **699 passed en 31,18 segundos**, sin caché pytest y con temporal
nuevo exclusivo según `AGENTS.md`. Se verificaron los 16 hashes de código de la
ejecución. No se instalaron dependencias ni se activaron servicios.

## Archivos conservados

- [Contexto: datos artificiales, test y consumo](phase4-rule-execution-2026-10-19/evidence-context.json).
- [Resultados del ejemplo artificial](phase4-rule-execution-2026-10-19/fixture-results.json).
- [Contabilidad base](phase4-rule-execution-2026-10-19/fixture-baseline.json).
- [Contabilidad candidata](phase4-rule-execution-2026-10-19/fixture-candidate.json).
- [Eventos de ejecución](phase4-rule-execution-2026-10-19/fixture-events.jsonl).
- [Informe del ejemplo artificial](phase4-rule-execution-2026-10-19/fixture-report.md).
- [Datos artificiales utilizados](phase4-rule-execution-2026-10-19/fixture-development.xml).
- [Plan](phase4-rule-execution-2026-10-19/fixture-plan.json), [sello](phase4-rule-execution-2026-10-19/fixture-plan.json.sha256) y [eventos](phase4-rule-execution-2026-10-19/fixture-plan-events.jsonl).
- [Revisión de prueba](phase4-rule-execution-2026-10-19/fixture-review.json), [traducción](phase4-rule-execution-2026-10-19/fixture-translation.json) e [idea sintética](phase4-rule-execution-2026-10-19/fixture-idea.json).
- [Reserva temporal del ejemplo](phase4-rule-execution-2026-10-19/fixture-access.json).
- [Rechazo del intento real sin plan](phase4-rule-execution-2026-10-19/blocked-events.jsonl) y [auditoría](phase4-rule-execution-2026-10-19/blocked-io-audit.json).
- [Correspondencia de copias y hashes](phase4-rule-execution-2026-10-19/snapshot.json).

Son copias exactas conservadas sin normalizar finales de línea. SHA-256 de
`fixture-results.json`:
`29b5e2fae40be14c1dc8574c146748926ca3cfaeb67b8302b1fc3f90a44810f7`.
Las copias son evidencia archivada; no constituyen nuevas ejecuciones con otra
reserva ni requieren que sigan existiendo los temporales originales de pytest.

Uso y límites en [RULE_EXECUTION.md](../docs/RULE_EXECUTION.md).
Cero consultas de IA y cero coste de API en este desarrollo. El siguiente paso
será vincular propuestas revisadas del agente con resultados verificados y un
presupuesto acotado de investigación. El histórico sigue siendo conocido.
FASE 4 continúa abierta; `PROJECT_STATUS.md` permanece sin cambios.
Sin commits, pushes, conexión TradingView ni operaciones reales.
