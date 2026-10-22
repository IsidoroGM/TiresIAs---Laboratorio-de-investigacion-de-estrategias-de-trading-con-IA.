# Cierre de FASE 5.2 — Conversación con el agente

21/10/2026. **FASE 5.2 implementada y comprobada localmente**, sobre `47d2fc5`,
con el trabajo de FASE 5.1 conservado. Sin commit ni push nuevos. FASE 6 pendiente.

## Entrega

Se añade Conversar con el agente: sesiones persistentes, historial, elección
explícita de contexto y de un resultado como evidencia, propuestas versionadas,
revisión humana, aprobación de una comparación histórica y consulta de resultados.
Las cinco pantallas anteriores mantienen su función de consulta.

`conversation.py` conserva sesiones, mensajes, revisiones y trabajos en SQLite,
con transacciones y sincronización FULL. Una identidad de petición no puede cambiar
su contenido ni repetir efectos. Un trabajador separado atiende la cola; un bloqueo
del sistema operativo limita las escrituras a una instancia. Tras un reinicio,
trabajos pendientes o en ejecución requieren revisión y no se reenvían.

`conversation_provider.py` mantiene un contrato distinto del ciclo de campañas:
Ollama 0.40.6 local, CPU, contexto hasta 4096, salida hasta 384, rechazo de recortes,
sin descargas, servicios de pago o reintentos. La entrega final conserva identidad
y digest del modelo, contrato, contexto elegido, respuesta original y consumo.

La prueba histórica exige una revisión con huella, fuente y código vigentes,
controles humanos, suficientes observaciones y aprobación explícita. Usa el motor
existente para una base y una variante; conserva copia del intervalo BCE, aprobación,
resultados y conclusión determinista. El enlace abre ambas cuentas y sus evidencias.
Este formato guarda resúmenes; no se inventan curvas ni operaciones detalladas.

Los límites iniciales son compartidos por todas las conversaciones: 24 intentos
de respuesta y cuatro comparaciones de dos backtests; ocho trabajos activos/en cola,
100 conversaciones y 128 revisiones. Cambiar de sesión, redacción, criterio o
representación decimal no permite repetir una comparación ni recuperar intentos.
Los presupuestos y permisos de campañas anteriores no se modifican ni se aceptan
como entrada del chat. El nuevo alcance es exploración de históricos conocidos.

Las acciones POST exigen origen/Host local, token de acción y JSON acotado. Las
consultas GET/HEAD no generan respuestas ni cálculos. No se permiten rutas libres,
ejecución de texto del modelo, órdenes de bróker o adopción automática de reglas.

## Comprobaciones automatizadas

Selección final: **267 aprobadas, cero fallos, errores o saltos, 56,099 s**. Incluye
conversación, consulta, rendimiento, proveedor, backtest, investigación, evidencias
y registro de campañas. Son **46 casos nuevos** de conversación. La colección
completa conserva exactamente los 1598 nodos de FASE 5, los 29 de FASE 5.1 y los
46 nuevos: **1673 nodos** sin errores de colección.

No se presenta como una ejecución completa de 1673 pruebas. Una ejecución amplia
inicial se interrumpió y no se cuenta como éxito; se completó la selección de
componentes afectados. Un primer lanzamiento del comprobador tenía una ruta de
pruebas inexistente y no ejecutó casos: se conserva como diagnóstico. Tras corregir
la ruta, la selección pasó; se repitió por la mejora final de procedencia del modelo.
Los manifiestos distinguen esas ejecuciones y las fuentes finales permanecieron
idénticas durante la última prueba. Cada proceso usó caché desactivada y temporal
GUID exclusivo según AGENTS.md.

- [Manifiesto final](phase5-2-completion-2026-10-21/suite-manifest.json).
- [Salida final](phase5-2-completion-2026-10-21/suite.log) y
  [JUnit](phase5-2-completion-2026-10-21/suite.xml).
- [Comprobador reproducible](../scripts/check_conversation_suite.py).

Se comprueban doble envío, contexto ajeno o excesivo, respuestas incompatibles,
contradicción EMA/SMA, origen y token de acción, propuestas incompletas, revisión
sustituida, fuente alterada, historia insuficiente, manipulación del contexto,
presupuestos compartidos, cola llena, cancelación, segundo servidor, SQLite corrupto,
reinicio sin reenvío, resultado alterado y disponibilidad de consulta durante inferencia.

## Ensayo real y limitaciones observadas

Se usó una raíz aislada bajo `.local/phase5-2-check/`, con una copia del BCE. No se
creó la base de conversaciones del proyecto de uso habitual. El ensayo total fue
**cuatro peticiones de modelo, una comparación histórica y dos backtests**:
1800 tokens de entrada, 680 de salida y coste API de 0 USD. No hubo reintentos
automáticos. Los tiempos comunicados por Ollama fueron aproximadamente 59, 35,
29 y 23 segundos; no representan una latencia garantizada.

La primera respuesta confundió SMA con EMA y declaró incorrectamente limitaciones
del ejecutor. Se conservó como borrador incompleto; la propuesta histórica se corrigió
y revisó explícitamente. Se añadió un rechazo de contradicciones entre tipo e hipótesis.
La segunda respuesta fue rechazada por un control demasiado estricto que confundía
los números de EMA15/EMA45 con cifras libres de rendimiento. Se conserva el fallo
y su consumo; la corrección admite solo identificadores de estrategias comprobados.

La tercera consulta explicó el resultado, con una comparación calculada por Python
separada de la interpretación del modelo. La cuarta comprobó una nueva propuesta
EMA15/45 y la identidad duradera del proveedor; la hipótesis fue poco informativa
y siguió como borrador incompleto. **Este ensayo demuestra el flujo y sus controles,
no fiabilidad semántica general del modelo.** El usuario debe revisar las reglas;
las afirmaciones libres del modelo no certifican robustez ni rentabilidad.

La revisión histórica comparó SMA20/60 con EMA15/45, EUR/USD, 2024-10-16 a
2026-10-16, 1000 USD virtuales, coste 0,001 y asignación 0,1. La variante obtuvo
0,693614 % frente a 0,532667 %, drawdown de 0,575080 % frente a 0,789256 %,
y cuatro cierres frente a cinco. Solo describe ese histórico y esos supuestos;
no se eligieron parámetros ganadores ni se realizó evaluación independiente.

- [Comprobación del flujo y consumo](phase5-2-completion-2026-10-21/real-flow-check.json).
- [Conversación y trabajos](phase5-2-completion-2026-10-21/real-conversation.json).
- [Resultado original](phase5-2-completion-2026-10-21/historical-experiment/results.json).
- [Aprobación y revisión originales](phase5-2-completion-2026-10-21/historical-experiment/approval.json).

Se revisaron en el navegador propuesta, aprobación, tabla de resultados, enlace
a la ficha y sus fuentes, historial tras reiniciar y consumo separado. Sin errores
de consola. La [captura](phase5-2-completion-2026-10-21/conversation-result.png)
conserva los estados del ensayo, incluido el intento fallido.

## Fluidez y conservación

Durante una inferencia real intermedia se midieron 30 consultas por ruta sobre
el catálogo habitual, con el índice preparado y la ejecución amplia de pytest
también activa. La inferencia seguía en ejecución en las 30 muestras:

| Ruta | p95 |
| --- | ---: |
| Inicio | 23,70 ms |
| Experimentos | 3,40 ms |
| Consumo | 20,26 ms |

Es una medida HTTP en este equipo, no pintado físico ni tiempo del modelo. Supera
el objetivo de mantener las consultas calientes por debajo de 500 ms. La selección
final también comprueba que el trabajo del modelo no ocupa un manejador de consulta.
[Muestras y condiciones](phase5-2-completion-2026-10-21/performance-model-busy.json).

La auditoría de consulta mantiene 92 registros, 40 cuentas detalladas y 150 con
resumen, 47 fuentes de consumo y cero acciones prohibidas. Sus 839 archivos no
cambiaron durante la auditoría. Las 838 fuentes del inventario de FASE 5.1 también
siguen idénticas; las cinco fuentes previas modificadas son exclusivamente servidor,
catálogo, consultas, JavaScript e índice HTML de la interfaz.

- [Auditoría de consulta](phase5-2-completion-2026-10-21/read-only-check.json).
- [Conservación de fuentes y evidencias](phase5-2-completion-2026-10-21/preservation-check.json).

Las pestañas y servidores temporales quedaron cerrados. No se intervino en un
servidor del usuario en 8765; al comprobar el cierre, ese puerto no estaba escuchando.
Para usar la versión nueva, arranca `python -m trading_ai.lab` desde el entorno
del proyecto. La instancia local de Ollama anterior se conserva.

Uso: [guía de conversación](../docs/CONVERSATION.md). Alcance:
[plan de FASE 5.2](../docs/PHASE5_2_PLAN.md). Siguiente trabajo:
[FASE 6.1, contratos y primeras estrategias Pine](../docs/NEXT_PHASES.md).
