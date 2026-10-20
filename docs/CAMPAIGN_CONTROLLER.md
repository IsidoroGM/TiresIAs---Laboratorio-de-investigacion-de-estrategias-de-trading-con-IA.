# Primer control de campañas de TiresIAs

El controlador contrasta el plan registrado, la memoria vigente y las capturas
de respuestas antes de permitir que se consideren candidatas para revisión.
Esta primera entrega solo consulta; no escribe reservas, revisiones o resultados.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_controller --scope <identidad-de-campana>
```

## Comprobaciones implementadas

- Verifica íntegramente el plan guiado y sus fuentes actuales. Compara la identidad,
  los controles y los límites con la inscripción original del registro compartido.
- Contrasta el consumo de todas las capturas. Una respuesta ausente, interrumpida,
  alterada o con consumo desconocido detiene el control; no recupera el hueco usado.
- Exige que los bytes de la petición capturada sean los del plan registrado y
  que su contrato corresponda a reglas compactas. Una reserva contable arbitraria
  no permite incorporar una respuesta ajena a ese plan.
- Separa error del proveedor, reglas inválidas, duplicado histórico y reglas
  pendientes de revisión técnica. Los errores del proveedor se conservan aunque
  acompañen reglas aparentemente válidas.
- Usa el compilador existente para validar las condiciones y producir descripciones
  mecánicas completas. No completa JSON truncado, atribuye hipótesis al modelo,
  ejecuta código recibido o admite controles de capital y costes dentro de las reglas.
- Contrasta las identidades de reglas consumidas del historial verificado. Una
  expresión tipada válida puede ser un duplicado y no llega a revisión.
- Repite las lecturas de registro, memoria, consumo y huellas de las capturas para
  detectar cambios durante la consulta. Es una comprobación optimista, sin bloqueo
  global; el futuro ejecutor deberá volver a comprobarlo antes de usar herramientas.

`review_pending` significa que hay reglas válidas pendientes de revisión. No es una
aceptación técnica, una prueba de novedad o un resultado de simulación.
`inactive` tampoco significa éxito: puede haber errores o propuestas descartadas,
que se detallan por separado. `requires_stop` identifica información no verificable
o reservas de comparación sin un flujo de revisión controlado.

## Límites de esta entrega

Las observaciones conservan su origen declarado por el llamador. El controlador
no acredita que hubiera transporte real ni que la identidad del proveedor esté
vinculada al envío. Comprobar reglas permite revisar su significado sin dar por
verificada su autoría. Los bytes originales permanecen en la captura.

Solo se admite la petición del plan registrado. Falta preparar y vincular peticiones
sucesivas con toda la memoria de campaña, sin omitir intentos nuevos. Este control
no reutiliza el intento compacto ni la reformulación estructurada consumidos.

La capacidad ejecutable permanece en cero. Siguen pendientes el permiso explícito
de campaña, el envío controlado y la conexión de revisión, plan y reserva compartida
del motor antes de calcular. El registro de revisión y el plan ya están disponibles
en el módulo adicional enlazado al final. Una reserva de comparación ya
presente exige parar porque este controlador aún no puede justificar su revisión.
No hay comandos de activación, envío, aprobación, simulación o reinicio.

El consumo heredado se mantiene separado del de las capturas y del consumo nuevo
de esta consulta, que es cero. Los subtotales conocidos no sustituyen un total
incompleto. Los fallos de la consulta se comunican al llamador o por stderr en CLI;
esta consulta no crea un diario oculto. El futuro ejecutor deberá registrarlos.

FASE 4 sigue abierta. La evaluación exterior permanece desactivada; el desarrollo
conocido no se presenta como datos inéditos. No se conectan TradingView o brókeres.
Véanse [el plan de campaña](LOCAL_CAMPAIGNS.md), [el registro](CAMPAIGN_LEDGER.md)
y [las capturas](CAMPAIGN_ATTEMPTS.md).

La [comprobación del bloque](../reports/phase4-campaign-controller-2026-10-20.md)
incluye las pruebas y la consulta de la campaña real, sin respuestas ficticias
en los registros de la aplicación.

La [revisión de capturas y preparación del experimento](CAMPAIGN_REVIEW.md)
amplía el flujo con decisiones separadas y un plan previo. Este primer inspector
mantiene su función original; la revisión se consulta en el nuevo registro.
