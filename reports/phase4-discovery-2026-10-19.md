# FASE 4 — Bandeja de ideas del investigador

Fecha: 19 de octubre de 2026. Desarrollo de herramientas; fase abierta.
**520 pruebas aprobadas**, incluidas 35 nuevas de la bandeja.

Por decisión del usuario, el agente propondrá estrategias; el desarrollo se
centra en herramientas para contrastarlas. Se añadió `trading_ai.discovery`,
que pide una idea declarativa y la guarda pendiente, sin ejecutar estrategias
ni modificar el simulador o los módulos vinculados a registros anteriores.

## Verificaciones locales conservadas

| Contrato | Resultado | Entrada / salida, tokens | Duración | Coste de API |
|---|---|---:|---:|---:|
| Versión inicial: lista de datos | Rechazado por tipos repetidos | 424 / 175 | 40,749 s | 0 USD |
| Versión 2: campos sí/no | Borrador registrado, pendiente | 445 / 228 | 45,521 s | 0 USD |

Una petición por ejecución, con Qwen3.5:4b en CPU, contexto 4096, salida máxima
384 tokens y temperatura 0. No hubo reintentos automáticos ni búsqueda masiva.
La segunda llamada comprobó un contrato modificado durante el desarrollo; no
se reescribió la primera. Total: **869 tokens de entrada, 403 de salida** y
**86,270 segundos**, con coste de API de **0 USD**.

La primera respuesta repitió OHLC y volumen en `data_requirements`. El validador
la rechazó y registró la respuesta completa y el consumo; no creó una idea
aceptada. El contrato versión 2 sustituye esa lista por cinco booleanos
explícitos. Una regresión reproduce la lista rechazada y conserva su rechazo.

## Borrador recibido y límites de su aceptación

La segunda respuesta se tituló «Cruces SMA/EMA con ventana BCE fija». Propuso
una entrada por cruce EMA/SMA y una salida «al cierre del día o al siguiente
cruce inverso». Declaró necesarias solo referencias, sin OHLC ni volumen.

El JSON cumple los límites de formato, **no acredita una estrategia nueva,
coherente o mejor**. Sigue basado en medias y la salida contiene alternativas
sin una prioridad precisa. Además, su hipótesis habla de cambiar a la fuente
BCE, que ya era la fuente utilizada. No se presenta ese cambio como realizado
ni sus posibles mejoras como resultados comprobados.

El estado es `pending_tool_mapping`, con `executable: false` y
`calculated_results: null`. No se ejecuta por su nombre ni se traduce
automáticamente el texto a código. Declarar los datos como suficientes solo
registra la declaración del modelo; no comprueba que las reglas sean calculables
con ellos. Estas observaciones de claridad y contexto quedan pendientes de la
especificación formal de reglas, sin cambiar ni ocultar la respuesta original.

Este paso prueba la bandeja y sus límites, no demuestra que el agente ya pueda
buscar y comprobar autónomamente familias nuevas de estrategias. El siguiente
desarrollo será un vocabulario de condiciones e indicadores que Python pueda
validar y calcular de forma determinista.

## Datos y controles

El contexto enviado al modelo contiene solo par, fuente, cobertura, hash y
controles de desarrollo: EUR/USD, 5375 observaciones entre 1999-01-04 y
2019-12-31. No se envían precios, métricas de estrategias ni resultados de
evaluación exterior. Este paso es ideación, no análisis empírico de precios.

El flujo valida la procedencia de desarrollo sin abrir `evaluation.xml` o sus
comparaciones. No ejecuta backtests ni descarga datos. El capital, costes y
tamaño permanecen bajo control del simulador. Si una propuesta declara OHLC,
volumen, intradía u otros datos, se marca `needs_data_and_tool_mapping`, sin
obtenerlos automáticamente.

## Pruebas

Las 35 pruebas nuevas verifican una petición por intento, ausencia de backtests
y acceso a evaluación exterior, estados pendientes, requisitos de datos,
tratamiento del texto como entrada no ejecutable, rechazo de campos de control
o resultados añadidos, parámetros reservados, valores finitos y límites.
También cubren entradas inválidas, respuestas y consumo conservados ante errores,
truncamiento sin reintentos, datos alterados, conservación de intentos repetidos
y OpenAI desactivado antes de crear una ejecución.

Suite completa: **520 passed**, sin caché pytest y con temporal nuevo exclusivo
según `AGENTS.md`. Sin dependencias nuevas, servicios adicionales, llamadas de
pago ni operaciones reales. Las pruebas de calidad del contenido del modelo no
se confunden con las de formato o permisos.

## Evidencias

- [Intento inicial rechazado: solicitud, respuesta y error](phase4-discovery-2026-10-19/contract-v1-failed-events.jsonl).
- [Contrato corregido: solicitud, respuesta y registro](phase4-discovery-2026-10-19/contract-v2-events.jsonl).
- [Borrador completo pendiente](phase4-discovery-2026-10-19/idea.json).
- [Correspondencia de copias y hashes](phase4-discovery-2026-10-19/snapshot.json).

Son copias exactas de `.local/discovery/34481bd5c2884da3b902cdbf9a148f62/`
y `.local/discovery/f99dc2258e2b4b3bb799af9a85dd8f2e/`, conservadas sin convertir
finales de línea mediante `.gitattributes`.

Las comprobaciones previas siguen siendo históricas conocidas. Nuevas ideas
no convierten 2020–2026 o la división interna anterior en evidencia inédita.
FASE 4 continúa abierta; `PROJECT_STATUS.md` conserva el cierre de FASE 3.
Sin commits ni pushes. Alcance y próximos pasos en el
[plan del investigador](../docs/AGENT_RESEARCH_PLAN.md).
