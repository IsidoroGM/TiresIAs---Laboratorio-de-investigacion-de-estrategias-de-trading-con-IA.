# Revisión técnica y plan de experimento de TiresIAs

Las reglas válidas de una captura pueden recibir una única revisión técnica.
Una decisión aceptada permite preparar un plan; no activa la campaña, acredita
el transporte del proveedor ni demuestra rentabilidad.

## Vista y declaración de revisión

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_review candidate --scope <campana> --request-sha <huella-peticion>
```

La vista conserva las reglas originales y sus descripciones mecánicas, el plan
registrado, los controles, el objetivo, los límites y las huellas de la captura.
El bloque `binding` identifica exactamente campaña, petición, recibo, observación
y reglas. No se inventa un título o una hipótesis del modelo.

La declaración JSON debe incluir `schema_version: 1`, los cinco campos de ese
`binding`, `reviewer`, `decision`, `rationale` y `checks`, sin otros campos.
El revisor y el motivo son declaraciones conservadas, no pruebas independientes.

Las seis comprobaciones booleanas de `checks` son:

- `rules_understood`: reglas entendidas.
- `windows_and_lags_understood`: ventanas y retrasos entendidos.
- `reference_data_sufficient`: las referencias disponibles bastan para esas reglas.
- `next_observation_execution_understood`: ejecución en la observación siguiente.
- `development_objective_understood`: objetivo de desarrollo entendido.
- `no_unresolved_ambiguity`: no queda una ambigüedad pendiente.

Las decisiones son `accepted`, `rejected` o `needs_clarification`. Aceptar exige
las seis comprobaciones verdaderas. Se rechazan duplicados, errores, respuestas
incompletas, consumo no verificable y declaraciones de otra captura. No se puede
aprobar retroactivamente una revisión después de reservar comparaciones.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_review review --scope <campana> --request-sha <huella-peticion> --assessment <declaracion.json>
.\.venv\Scripts\python.exe -m trading_ai.campaign_review verify --run <revision>
.\.venv\Scripts\python.exe -m trading_ai.campaign_review status --scope <campana>
```

Cada revisión guarda candidata, declaración, decisión, huellas, código y eventos.
La reserva exclusiva está en `.local/campaign-review-access` y no depende de la
carpeta elegida para el informe. Un error de declaración anterior a la reserva
queda registrado sin consumirla. Tras reservar, una interrupción o rechazo no
permite cambiar de carpeta para repetir o sustituir la decisión. No hay comandos
de reapertura o reformulación; `needs_clarification` no concede nuevos intentos.

`status` consulta sin escribir. Una revisión parcial o alterada exige parar.
La consulta de estado no es una autorización ni una comprobación completa previa
a ejecutar; cada revisión verificada vuelve a contrastar sus fuentes. El primer
[controlador](CAMPAIGN_CONTROLLER.md) conserva su inspección original de reglas;
las decisiones registradas se consultan mediante este módulo adicional.

## Plan previo sin ejecutar

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_experiment prepare --review-run <revision-aceptada>
.\.venv\Scripts\python.exe -m trading_ai.campaign_experiment verify --run <plan-experimento>
```

Se contrastan datos de desarrollo, controles y objetivo congelados con la revisión.
El plan copia los datos y fija reglas, estrategia base, capital, tamaño, costes,
criterio y ejecución en la referencia siguiente. Prevé una comparación con dos
cuentas independientes: un backtest de la base y otro de la candidata, sin
variaciones, consultas al modelo o reintentos. Una campaña con cero backtests
no puede preparar este plan aunque tenga una revisión aceptada.

Prepararlo comprueba que quedan dos huecos contables, que la propuesta no tiene
comparación reservada y que el cálculo no está consumido en el motor. Mantiene
la misma identidad de cálculo que los ejecutores anteriores: cambiar el nombre,
el criterio o la carpeta no libera un cálculo consumido. Se contrastan las fuentes
y reservas de nuevo antes de sellar el plan. Un fallo deja su diario y conserva
los archivos parciales sin ejecutar o reconstruir resultados.

La preparación no reserva ni gasta esos backtests. Verificar el artefacto tampoco
devuelve reservas ni acredita disponibilidad actual. Una reserva posterior no
borra la revisión o el plan ya registrados; el futuro ejecutor deberá comprobar
su correspondencia y su permiso antes de calcular.

Para el ciclo autónomo faltan la memoria completa de campaña para peticiones
sucesivas y el origen verificado de los envíos. Ese ciclo de investigación sigue
desactivado; el cálculo offline con permiso se describe al final de este documento.
La evaluación exterior conocida no se reutiliza como inédita, y no se conectan
TradingView o brókeres. FASE 4 permanece abierta.

La [comprobación del bloque](../reports/phase4-campaign-review-2026-10-20.md)
detalla los tres pases de pruebas y la consulta del registro real. La aceptación
y la preparación se prueban con datos artificiales; no se simulan propuestas
pendientes en la aplicación.

La [ejecución virtual con permiso](CAMPAIGN_EXECUTION.md) permite calcular una
comparación offline de esas reglas declaradas. No acredita transporte del modelo
ni activa el futuro ciclo de generación; revisión, permiso y cálculo permanecen
como operaciones distintas.
