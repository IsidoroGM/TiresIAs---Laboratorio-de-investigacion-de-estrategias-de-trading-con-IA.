# TiresIAs: permiso y ejecutor virtual — 20/10/2026

Se añade una ruta de cálculo offline para un plan revisado, con permiso explícito,
reserva compartida del motor y dos huecos contables indivisibles. El motor calcula
base y candidata con los controles congelados; Python determina el criterio sin
adopción automática. No se modifican los módulos anteriores sellados.

## Pruebas verificadas

Se aprobaron **42 pruebas nuevas distintas en dos pases**:

- Permisos: 25 aprobadas en 130,17 segundos.
- Ejecutor, fallos, concurrencia e integración: 17 aprobadas en 741,11 segundos.

Los 12 minutos y 21 segundos corresponden al pase completo de 17 pruebas, que
incluye la integración; no son una medición aislada del backtest o de producción.
El recorrido repetido de verificaciones es costoso y queda pendiente optimizarlo
sin perder comprobaciones. La integración utiliza caché de lectura validada
explícita; no se activa por defecto en las API de producción.

Se verificaron límites y tipos de la declaración, identificación exacta del plan,
reconocimiento del origen declarado, consumo de permisos, fuentes alteradas,
capturas pendientes, cálculos anteriores, fallos después de reservar, conservación
de resultados parciales y rechazo de reintentos. Un error del registro conserva
el intento compartido; un error del motor mantiene los dos huecos contables.
Dos ejecutores concurrentes completan como máximo una comparación con ese permiso.

Las pruebas del ejecutor usan el motor real sobre referencias artificiales.
La prueba integrada conserva los validadores completos de las fuentes guiadas,
revisión, plan, permiso y cálculo; el transporte es falso. No abre evaluación
exterior, llama modelos o reserva presupuestos heredados. Se comprobó un resultado
inconcluso sin convertirlo en mejora. La verificación de resultados no recalcula
los backtests y se mantiene separada de su ejecución.

Se usaron temporales nuevos exclusivos y caché de pytest desactivada según
AGENTS.md. La recolección global identificó 1.487 pruebas en 0,88 segundos, sin
ejecución global. Los dos pases focalizados no se presentan como una nueva global;
la última suite global comprobada sigue siendo la de 1.253 pruebas.

## Alcance y procedencia

El propósito del permiso es `offline_virtual_evaluation_of_declared_source`.
Comprueba el vínculo local de la captura y exige reconocer su origen declarado;
no da por acreditados transporte o autoría del modelo, que permanecen explícitamente
en falso. Esta ruta offline es distinta del futuro ciclo de investigación con un
proveedor verificado y no declara resueltos sus requisitos de transporte.

El permiso no concede consultas de IA, API de pago, variaciones, evaluación exterior
o operaciones reales. La memoria fijada incluye reservas de propuestas, capturas,
consumo y revisiones. Un cambio exige detenerse. Este primer contrato rechaza otras
comparaciones cuyos resultados aún no estén incorporados y no implementa un ciclo
de múltiples ensayos. Las huellas son locales y los controles optimistas, sin
autenticación externa del llamador ni bloqueo global de archivos.

## Consulta de la aplicación

La auditoría `.local/campaign-execution-audits/0dd9454d25784c9d936cc397cc84c4c1`
consultó únicamente el registro real de permisos. La campaña continúa inactiva,
con cero reservas, permisos o ejecuciones nuevas. No se fabricó una revisión
aceptada para simular las candidatas pendientes de la aplicación.

Los nueve contadores de red, proveedor, cálculo, reserva heredada, evaluación
exterior, reserva de campaña, escritura de capturas, escritura de revisión o plan
y escritura de permiso o ejecución quedaron a cero. SQLite y los nueve archivos
históricos de reservas mantienen sus bytes. Las tres nuevas raíces locales siguen
sin crear; PROJECT_STATUS.md conserva su SHA-256 y la FASE 4 permanece abierta.

Se verificaron las 307 copias y referencias originales previas antes y después.
El [inventario](phase4-campaign-execution-2026-10-20/snapshot.json) añade diez:
**317 copias y referencias entre 23 inventarios concretos**, sin presentarlas como
archivos físicos únicos. Conserva consulta, auditoría, huellas, eventos, script,
código y pruebas con nombres no recolectables por pytest.

Consumo nuevo del investigador en la aplicación: **0 llamadas, 0 tokens, 0 USD API
y 0 backtests de investigación**. Los cálculos del motor y cifras artificiales de
las pruebas se mantienen aparte. El consumo compacto heredado de 2.262 tokens de
entrada y 176 de salida, con 0 USD de API, no se repite ni representa toda la aplicación.

No se reabren la reformulación o los intentos consumidos, ni se presenta evaluación
conocida como inédita. Sin instalaciones, servicios nuevos, dinero real, commits
o pushes. Uso y límites: [permiso y ejecución virtual](../docs/CAMPAIGN_EXECUTION.md).
