# Memoria de resultados de TiresIAs

La memoria reúne las propuestas registradas, las capturas con su consumo, las
revisiones y los resultados del motor. Consultarla o guardarla no envía peticiones,
concede permisos, reserva intentos ni repite simulaciones. La campaña sigue inactiva.

Los resultados solo se incorporan como `completed_verified` si se verifican los
archivos de la ejecución, permiso, plan, controles y reserva compartida. Se guardan
los resúmenes de base y candidata y el criterio calculado por Python. Una conclusión
negativa o inconclusa se conserva; no se elige automáticamente una estrategia.
La verificación comprueba la integridad guardada y el criterio, sin recalcular
los backtests ni acreditar autoría o transporte del modelo.

| Estado | Qué conserva |
| --- | --- |
| `completed_verified` | Resultados, criterio, datos, controles y huellas de la ejecución. |
| `failed_consumed` | Error e intentos/completados observados; resultado final desconocido. |
| `interrupted_or_in_progress` | Diario parcial y contadores observados; obliga a detenerse. |
| `unverifiable_execution` | Error de verificación; nunca incorpora un resultado como válido. |
| `reserved_without_verified_execution` | Reserva contable sin ejecución verificable; no libera el intento. |
| `unverifiable_shared_claim` | Reserva vinculada con protocolo desconocido; obliga a detenerse. |

También se detecta el intento ocupado en el motor antes de un fallo al reservar en
SQLite, aunque no exista recibo contable. Un permiso o captura sin verificar bloquea
la memoria para continuar. Los consumos desconocidos permanecen desconocidos, los
subtotales conocidos van aparte y el consumo compacto heredado mantiene su ámbito.
Los contadores de eventos parciales no son telemetría independiente del proceso.

## Consultar y guardar

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_memory --cached inspect --scope <campana>
.\.venv\Scripts\python.exe -m trading_ai.campaign_memory --cached save --scope <campana>
.\.venv\Scripts\python.exe -m trading_ai.campaign_memory --cached verify --run <memoria>
```

`save` escribe `memory.json`, su SHA-256 y eventos en una carpeta exclusiva de
`.local/campaign-memory`. La consulta compara dos lecturas completas. `verify`
contrasta el documento con las fuentes actuales: una nueva reserva o un cambio
posterior lo vuelve obsoleto. No se sobrescribe el historial ni se usa una memoria
obsoleta como contexto vigente. El límite de documento es 120.000 bytes y se
rechaza el exceso sin recortar errores o resultados. No hay bloqueo global de
escritores ni firma externa: las guardas detectan cambios ordinarios entre lecturas.

## Verificaciones más rápidas

`--cached` abre una `VerificationSession` explícita y limitada a esa operación.
La primera lectura verifica íntegramente la petición guiada; las siguientes
reutilizan su resultado solo después de volver a comprobar los bytes y rutas de
todos los archivos leídos, las consultas de presencia, los listados observados
y el código/configuración del verificador. No se confía solo en tamaño o fecha
de modificación. Un cambio detiene la sesión; no provoca un reintento automático.

Se conservan siempre las consultas actuales a SQLite y las verificaciones de
capturas, revisiones, permisos y resultados. No se guardan autorizaciones o cálculos
en caché. Las respuestas son copias independientes. Al terminar, incluso por error,
se descarta la memoria temporal y se restauran los lectores. Otros hilos sin una
sesión activa realizan la verificación original. Las sesiones no se anidan y esta
ruta no requiere activar la caché anterior de XML. Sin `--cached` se verifica todo
de nuevo. Los productores históricos y sus evidencias conservan sus bytes.

## Contrato v1 y ciclo local nuevo

Esta memoria v1 prepara los resultados para futuros ensayos. No modifica la petición
inicial congelada ni la introduce todavía en una nueva llamada al modelo.
El primer contrato de permiso sigue rechazando otras comparaciones: esta tarea
no lo amplía ni reinicia intentos consumidos. En este contrato v1,
`automatic_local_cycle_enabled` y `future_model_context_integrated` permanecen en
`false`. La [ruta nueva de ciclo local](PHASE4_COMPLETION.md) integra historial y
resultados mediante un contexto reversible, con control de tamaño, transporte
local identificado y revisión mecánica solo para experimentos virtuales. Sus
resultados se consultan con su propio inspector; no se migran pendientes de v1.

La FASE 4 se cierra en la [integración final](PHASE4_COMPLETION.md). El histórico
es desarrollo conocido; no hay evaluación
inédita, TradingView o bróker habilitados. Véanse la
[ejecución virtual](CAMPAIGN_EXECUTION.md) y la
[comprobación de este bloque](../reports/phase4-campaign-memory-2026-10-20.md).
