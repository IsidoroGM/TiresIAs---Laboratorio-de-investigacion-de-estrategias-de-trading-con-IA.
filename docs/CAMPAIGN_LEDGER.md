# Registro compartido de reservas de campaña

El registro cuenta los huecos reservados para propuestas y comparaciones.
Utiliza SQLite, incluido en Python, en un único archivo local:
`.local/campaign-ledger/registry.sqlite3`. No necesita instalación o servicio.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_ledger register --plan-run <plan-campana>
.\.venv\Scripts\python.exe -m trading_ai.campaign_ledger status --scope <identidad-de-64-caracteres>
```

`register` comprueba el plan y sus fuentes vigentes antes de registrar sus
términos. La primera inscripción fija límites, objetivo, controles y proveedor
previsto para el ámbito de datos/par. Otro plan con la misma identidad conserva
el registro inicial; no reinicia sus contadores. Si cambia los términos se rechaza.
La CLI no permite elegir otra base, reiniciar o liberar reservas.

## Reservar sin ejecutar

Las API internas `reserve_proposal` y `reserve_comparison` se reservan para el
controlador futuro. Una propuesta ocupa un hueco; una comparación ocupa dos
backtests juntos y requiere una propuesta reservada. Cada propuesta admite una
sola comparación. El contador se deriva de los recibos guardados.

Cada operación utiliza una identidad estable: huella de petición o identidad de
cálculo. Repetir la misma operación devuelve el recibo anterior sin gastar otro
hueco. Cambiar la carpeta del plan no concede capacidad nueva. Una transacción
SQLite reserva de forma indivisible: procesos que comparten este archivo no
pueden superar juntos los límites, ni reservar medio par de backtests.

Un fallo del llamador después de guardar la reserva conserva el hueco ocupado.
Si la transacción falla antes de confirmarse, no entrega un recibo y se deshace
entera. No hay devolución automática por errores, duplicados o propuestas
descartadas. Los fallos de registro o reserva se comunican como errores al
llamador, que deberá conservarlos en el diario del controlador futuro.

**Estos recibos son contables y la campaña sigue inactiva.** Incluyen
`execution_authorized: false`; no envían peticiones o ejecutan cálculos.
Las identidades recibidas no prueban que una petición sea válida o que una
candidata tenga una revisión aceptada. El controlador deberá comprobar ambas,
además del plan y la reserva compartida del motor, antes de usar herramientas.

## Qué comprueba la consulta

`status` consulta sin escribir y no crea una base ausente. Un ámbito desconocido
devuelve capacidad desconocida y ningún permiso. Un ámbito registrado muestra
reservas, huecos contables restantes y capacidad ejecutable cero. El consumo
real de esta operación es cero; el consumo heredado se conserva por separado.

Se contrastan esquema, recibos, huellas, código y archivos del plan inicial.
Cambios o corrupción detectados detienen la consulta o reserva; no reconstruyen
una base vacía para conceder presupuesto. Las comprobaciones de archivos son
optimistas y no bloquean todos los escritores externos.

La consulta no vuelve a validar la memoria viva del investigador: lo declara con
`current_source_freshness_verified: false`. Conserva el plan comprobado al
registrar. El controlador deberá renovar la memoria completa antes de cada
petición y detenerse ante datos, código, controles o consumo no verificables.

La base es estado local mutable y está excluida de Git. Las copias archivadas
comprueban un momento concreto; no restauran o sincronizan presupuestos. Las
huellas locales detectan cambios ordinarios, sin ser una firma externa o una
protección contra reescrituras deliberadas del registro completo.

La [comprobación local](../reports/phase4-campaign-ledger-2026-10-20.md) registra
el plan de la aplicación sin ocupar huecos ni activar herramientas. Las pruebas
de agotamiento y concurrencia usan únicamente bases temporales y datos artificiales.
Las [capturas de intentos](CAMPAIGN_ATTEMPTS.md) ya conservan respuestas, errores
y consumo por reserva, sin consultar al modelo. Siguen pendientes el permiso de
ejecución de campaña y el controlador que enlace propuesta, revisión, cálculo y análisis.
