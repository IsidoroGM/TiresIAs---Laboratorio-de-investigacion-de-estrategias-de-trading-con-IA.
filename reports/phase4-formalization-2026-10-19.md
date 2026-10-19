# FASE 4 — Vínculo entre ideas y reglas propuestas

Fecha: 19 de octubre de 2026. Desarrollo de herramientas; fase abierta.
**623 pruebas aprobadas**, incluidas 36 nuevas de traducción y trazabilidad.

Se añadió `trading_ai.formalization`. Verifica una idea pendiente de la bandeja,
su respuesta original y su procedencia de desarrollo. Pide como máximo una
traducción al lenguaje de reglas. No calcula señales ni invoca el simulador.
El agente sigue proponiendo estrategias; el desarrollador no elige una nueva.

## Prueba local

Se utilizó la idea ya registrada «Cruces SMA/EMA con ventana BCE fija», sin
reescribirla ni solicitar otra idea. Su identificador es:
`a59f988282c8de81e0aff2695e55147cd024a6cd7d2ab55acba31be2aa826d7e`.

Una consulta a Qwen3.5:4b local, CPU, contexto 4096, salida máxima 384 tokens,
temperatura 0: **443 tokens de entrada, 167 de salida, 0 USD de API**.
Duración informada por el proveedor: 36,223 segundos; intento completo:
36,983 segundos. No hubo reintentos ni solicitudes de pago. El modelo local
consume recursos del equipo aunque no cobre por API.

Resultado: **`needs_clarification`**, con `spec: null`. No se obtuvo una
especificación ni se calcularon resultados. La salida original «al cierre del
día o al siguiente cruce inverso» sigue pendiente de una definición explícita.

La explicación del modelo es una declaración no verificada. Identifica dudas
de salida y del parámetro `reference_series`, pero también interpreta mal la
ejecución del motor: este sigue ejecutando en la siguiente observación y no
exige que una señal se ejecute inmediatamente. Además, asociar un cierre a la
necesidad de volumen no es una regla del sistema. No se adoptan estas
afirmaciones ni se cambia el simulador para ajustarlo a ellas.

La explicación ocupa los 600 caracteres permitidos y termina con una frase
incompleta. Se conserva íntegra tal como se recibió; el JSON es válido y no se
registra una truncación por límite de tokens. No se fuerza otra consulta para
mejorar la explicación. Este resultado comprueba el registro de una duda; no
demuestra comprensión fiable del modelo ni una estrategia nueva o mejor.

## Controles y límites

- Datos declarados ausentes: bloqueo previo con cero consultas, sin descargarlos.
- Ambigüedad o capacidad no implementada: pendiente, sin reglas parciales.
- Reglas válidas en estructura: `pending_semantic_review`, sin permiso de ejecutar.
- Todos los registros aceptados: `executable: false`, resultados `null` y
  equivalencia de significado no verificada.
- JSON o reglas inválidas: se guardan respuesta, error y consumo conocido;
  no se crea una traducción aceptada y no hay reintento automático.

Las reglas no pueden añadir capital, costes, tamaño, posiciones ni código libre.
La compilación verifica formato y límites, no demuestra equivalencia con el
lenguaje natural. La detección de dudas por el modelo puede fallar.

El origen se comprueba otra vez antes de guardar; si cambia durante la consulta,
se conserva el error y el consumo. Los hashes enlazan archivos locales y
permiten comparar copias; no constituyen una firma contra manipulación conjunta.

La ejecución real tuvo bloqueados los accesos a `evaluation.xml`, comparaciones
y registros de evaluación exterior, además de la generación de señales.
La auditoría contiene 26 rutas leídas. Solo se verificó la procedencia anterior
al corte 2020; el modelo recibió el texto de la idea, sin precios ni métricas.
No se reutilizó la evaluación exterior ni se abrió un nuevo backtest.

## Comprobaciones y evidencias

Las 36 pruebas nuevas cubren vínculo exacto, conservación del origen, estados
pendientes, bloqueo por datos, ausencia de señales y backtests, rechazo de
fuentes alteradas o incompletas, cambios durante la consulta, límites de reglas,
campos prohibidos, JSON repetido o inválido, errores del proveedor, consumo
desconocido, ausencia de reintentos y conservación de intentos repetidos.

Suite completa: **623 passed**, sin caché y con temporal exclusivo nuevo según
`AGENTS.md`. No se modificaron los módulos del motor ligados al registro previo.

- [Idea original](phase4-formalization-2026-10-19/source-idea.json).
- [Eventos originales de la idea](phase4-formalization-2026-10-19/source-events.jsonl).
- [Registro de traducción pendiente](phase4-formalization-2026-10-19/translation.json).
- [Solicitud, respuesta, consumo y cierre](phase4-formalization-2026-10-19/events.jsonl).
- [Auditoría de accesos](phase4-formalization-2026-10-19/io-audit.json).
- [Correspondencia de archivos y hashes](phase4-formalization-2026-10-19/snapshot.json).

Son copias exactas del intento
`.local/formalization/0199d06d32b649139c0ad9b96c559d5b`, sin normalizar finales
de línea. SHA-256 de `translation.json`:
`b5dfad1148faec6c015f8e76520efe7d02324faf6666cc1b5743e8fcd5c1fe22`.

Uso y próximos controles en [FORMALIZATION.md](../docs/FORMALIZATION.md).
Faltan la revisión del significado y el registro previo de experimentos acotados.
El histórico sigue siendo conocido; una nueva idea no lo convierte en evidencia
inédita. FASE 4 permanece abierta; `PROJECT_STATUS.md` conserva el cierre de
FASE 3. Sin commits, pushes, dependencias nuevas u operaciones reales.
