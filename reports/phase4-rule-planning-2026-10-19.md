# FASE 4 — Revisión técnica y registro previo de reglas

Fecha: 19 de octubre de 2026. Desarrollo de herramientas; fase abierta.
**669 pruebas aprobadas**, incluidas 46 nuevas.

Se añadió `trading_ai.rule_planning` con cuatro comandos: `review`,
`verify-review`, `prepare` y `verify-plan`. No consulta IA, genera señales ni
ejecuta backtests. Conserva los borradores y los registros anteriores.

## Qué permite el desarrollo

Una revisión técnica identifica la traducción y las reglas exactas mediante
hashes. Declara quién la realizó, su justificación y cinco comprobaciones:
entrada, salida, parámetros, suficiencia de datos y ausencia de ambigüedad.
Aceptar requiere las cinco, sin convertir la confianza del modelo en aprobación.

La revisión es una declaración técnica. El programa comprueba identidad de los
archivos y consistencia del registro, pero no autentica al revisor ni demuestra
la verdad de sus comprobaciones. El contrato declara esa limitación; no se
presenta como una prueba automática de equivalencia con el lenguaje natural.

Una revisión aceptada permite registrar un plan con una candidata y una base,
el par y los controles del protocolo existente, el criterio previo y una copia
exacta de desarrollo. Fija como máximo dos backtests por plan, cero consultas
de IA, variaciones de parámetros y reintentos automáticos. No admite cambiar
esos límites mediante opciones de la CLI.

Los planes permanecen `registered_not_run`, con `executable: false` y resultados
`null`. Todavía no existe su ejecutor: este paso registra el presupuesto para
que una herramienta posterior lo consuma y evite repetir ejecuciones. No
establece un presupuesto global ni limita usos manuales del motor.

## Comprobación con el borrador real

Se utilizó la traducción anterior en `needs_clarification`, vinculada a la idea
`a59f988282c8de81e0aff2695e55147cd024a6cd7d2ab55acba31be2aa826d7e`.
La salida «al cierre del día o al siguiente cruce inverso» sigue sin definición
precisa y no hay reglas propuestas que revisar. No se eligió una interpretación
por parte del desarrollador ni se solicitó otra estrategia.

El comando de revisión, sin evaluación de aceptación añadida, registró
**`blocked_by_translation`**, `assessment: null` y `eligible_for_plan: false`.
El intento de preparar un plan fue rechazado y conservó el error. No produjo
`plan.json` ni copió datos al intento fallido.

**Cero solicitudes de IA, cero coste de API y cero simulaciones.** La prueba
deshabilitó expresamente el proveedor, la generación de señales y los backtests.
Además bloqueó aperturas de datos, resultados y marcas de evaluación exterior.
La auditoría contiene 31 rutas leídas; el único XML leído fue desarrollo.
No se modificaron la idea, la traducción ni los módulos del motor registrados.

La rama aceptada y la preparación correcta del plan se comprueban con ejemplos
artificiales en las pruebas. No se afirma haber revisado o registrado una
estrategia real nueva, ni haber obtenido mejoras de rentabilidad.

## Verificación y evidencias

Las 46 pruebas nuevas cubren revisión explícita, bloqueo de borradores sin
reglas, decisiones no aceptadas, hashes de destino, campos y comprobaciones
obligatorias, conservación de fuentes y ausencia de llamadas o simulaciones.
También verifican controles y presupuesto fijos, sellos y cierres, fuentes
alteradas, fallos de escritura, conservación de intentos y comandos CLI.

Cambiar presupuesto, criterio, capital, reglas, base, datos, ejecución, alcance,
código o permisos invalida un plan incluso si se recalcula solo su sello.
La verificación reconstruye el registro esperado y contrasta sus fuentes. Los
hashes no son una firma contra modificar coherentemente todas las evidencias.

Suite completa: **669 passed en 22,89 segundos**, con caché desactivada y
temporal exclusivo nuevo según `AGENTS.md`. No se instalaron dependencias ni
se activaron servicios. `PROJECT_STATUS.md` permanece sin cambios.

- [Revisión bloqueada](phase4-rule-planning-2026-10-19/review.json).
- [Sello de revisión](phase4-rule-planning-2026-10-19/review.json.sha256).
- [Eventos de revisión](phase4-rule-planning-2026-10-19/review-events.jsonl).
- [Error de preparación del plan](phase4-rule-planning-2026-10-19/blocked-plan-events.jsonl).
- [Traducción original](phase4-rule-planning-2026-10-19/source-translation.json).
- [Eventos originales de traducción](phase4-rule-planning-2026-10-19/source-translation-events.jsonl).
- [Auditoría de accesos](phase4-rule-planning-2026-10-19/io-audit.json).
- [Correspondencia de copias y hashes](phase4-rule-planning-2026-10-19/snapshot.json).

Copias exactas de `.local/rule-reviews/76bede728e3748d7a77072b86f2d7d4c`
y del intento fallido `.local/rule-plans/168b298f29544173b7d8b1f266e8b39b`,
con sus fuentes de traducción. Se conservan los bytes mediante `.gitattributes`.
SHA-256 de `review.json`:
`d1a86728dcc2d791e3dc07d0b5375f5ef02a3470de628d89d0b038ab2e5b5018`.

Uso y límites en [RULE_PLANNING.md](../docs/RULE_PLANNING.md).
Quedan pendientes propuestas explícitas que resuelvan las dudas del agente y
el ejecutor de planes con consumo controlado. El histórico sigue siendo conocido;
este desarrollo no crea evidencia inédita. FASE 4 continúa abierta.
Sin commits, pushes, llamadas de pago, conexión TradingView ni operaciones reales.
