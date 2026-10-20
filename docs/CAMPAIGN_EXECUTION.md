# Permiso y ejecución virtual de TiresIAs

Un plan aceptado puede recibir un permiso explícito para **una sola comparación
virtual de dos backtests**: base y candidata. El permiso no permite consultas al
modelo, costes de API, cambios de parámetros, evaluación exterior u operaciones
con un bróker. Concederlo no ejecuta ni reserva la comparación.

## Origen declarado y alcance del permiso

Esta ruta es `offline_virtual_evaluation_of_declared_source`: permite calcular
reglas declaradas y técnicamente revisadas. Comprueba la cadena local de petición,
recibo, bytes originales, revisión y plan. Esa comprobación de procedencia no
acredita transporte o autoría del modelo, que permanecen en `transport_verified:
false`. El permiso exige reconocer expresamente esa limitación.

Se distingue así el cálculo offline del futuro ciclo de investigación con un
proveedor verificado. Los requisitos de identidad y transporte de ese ciclo
siguen pendientes; este permiso no los declara resueltos ni habilita generación.
No se convierte una fuente declarada en una llamada al modelo acreditada.

La declaración JSON debe contener exactamente:

- `schema_version`: entero `1`.
- `scope_id`, `plan_sha256`, `calculation_id`: identidades exactas del plan.
- `purpose`: `offline_virtual_evaluation_of_declared_source`.
- `allowed_backtests`: entero `2`; `allowed_model_requests`: entero `0`.
- `api_cost_usd`: cadena `"0"`.
- `acknowledge_caller_declared_source`: booleano `true`.
- `authorizer` y `rationale`: identificación y motivo no vacíos y acotados.

El autor es una declaración del llamador local, sin autenticación externa. El
permiso se solicita por la interfaz de control, separada de las propuestas del
modelo: no se deriva de su confianza, su texto o su decisión de revisión.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_permission grant --plan-run <plan> --declaration <permiso.json>
.\.venv\Scripts\python.exe -m trading_ai.campaign_permission status --scope <campana>
```

## Controles de la memoria y las reservas

Se verifican el plan y sus fuentes, las reservas de propuestas, los bytes y consumo
de todas las capturas y las revisiones registradas. Un estado pendiente o desconocido
exige parar. El permiso fija las huellas de esa memoria; un cambio posterior lo
invalida. El primer contrato admite una comparación sin otras comparaciones cuyo
resultado no esté incorporado. Todavía no administra un ciclo de múltiples ensayos.

La reserva de permiso está en `.local/campaign-calculation-permissions`, identificada
por el mismo cálculo que utiliza el motor. Cambiar carpeta o crear otro documento
no reinicia el permiso o un cálculo anterior. Un fallo tras guardar la reserva deja
su diario y bloquea una nueva concesión automática.

Los controles son optimistas y usan huellas locales: detectan cambios ordinarios,
sin ser firmas externas o una transacción global contra cualquier escritor. El
ejecutor repite las comprobaciones antes de cada cálculo y antes del cierre.

## Ejecutar y verificar

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_execution execute --permission-run <permiso>
.\.venv\Scripts\python.exe -m trading_ai.campaign_execution verify --run <ejecucion>
```

El ejecutor valida datos, reglas y permiso. Primero ocupa la reserva compartida del
motor y después reserva los dos backtests juntos en SQLite. Ambos registros deben
estar confirmados antes de calcular. Dos procesos no pueden completar dos pares con
el mismo permiso. El recibo contable por sí solo continúa sin ser una autorización.

El motor existente calcula la base y la candidata con cuentas independientes y
los mismos controles congelados. Se guardan contabilidad, señales por huella,
resúmenes, criterio calculado por Python, informe, recibo y eventos. Se mantienen
los resultados negativos o inconclusos; no hay selección o adopción automática.

Un error del registro después de ocupar la reserva del motor conserva esa reserva,
aunque no se hayan gastado huecos contables. Un error del motor conserva los dos
huecos y cualquier cálculo completado. No se repite el par, no se liberan reservas,
no se reconstruye un resultado y no se reinicia cambiando la carpeta.

La verificación contrasta integridad, resúmenes y criterio de Python sin recalcular
los backtests. `calculation_claimed` en la consulta de permisos significa intento
ocupado, incluso si se interrumpió; no afirma una ejecución completa o exitosa.

La [memoria de resultados](CAMPAIGN_MEMORY.md) incorpora ahora resultados
verificados y conserva fallos e intentos pendientes, sin repetir cálculos. Ofrece
verificación guiada reutilizable con guardas de fuentes durante una consulta.
El contrato de este permiso conserva su límite inicial de una comparación.

La [ruta nueva del ciclo local](PHASE4_COMPLETION.md) añade contexto renovado,
transporte controlado y revisión mecánica para experimentos virtuales. Es un
contrato distinto: este permiso v1 conserva su revisión manual y una comparación,
y no interpreta o ejecuta las propuestas del ciclo nuevo. No hay integración
con TradingView ni bróker. Incorporar los módulos no activa permisos por sí solo.

La [comprobación del bloque](../reports/phase4-campaign-execution-2026-10-20.md)
documenta las pruebas sobre datos artificiales y la consulta real sin activar
permisos o simular propuestas pendientes.
