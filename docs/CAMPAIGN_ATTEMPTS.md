# Capturas de respuestas, errores y consumo

Cada reserva de propuesta puede vincularse a una captura duradera de su petición
y del resultado observado por el controlador. Este módulo guarda información;
no consulta modelos, aprueba reglas o ejecuta cálculos.

La CLI disponible solo consulta:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_attempts --scope <identidad-de-campana>
```

## Flujo previsto para el controlador

1. Obtener una reserva contable de propuesta en el registro compartido.
2. `prepare_attempt`: conservar los bytes de petición y vincularlos por SHA-256
   al recibo. Crear una captura exclusiva por recibo.
3. Comprobar por separado permiso de campaña, proveedor y memoria vigente.
4. `mark_submission_intent`: guardar una marca exclusiva antes de llamar al
   proveedor. La marca no prueba que el envío haya ocurrido ni lo autoriza.
5. Tras la llamada, `record_observation`: guardar los bytes originales de la
   observación antes de interpretarlos y registrar el análisis de consumo.

Las tres API de escritura son internas; no hay comandos de envío, captura de
respuestas arbitrarias, reinicio o liberación de intentos. La campaña continúa
inactiva y todos los registros mantienen `execution_authorized: false`.

## Qué se conserva

La observación procede del llamador controlado: declaración de si intentó la
consulta, texto recibido, modelo, uso comunicado, error y respuesta del proveedor
cuando esté disponible. No es una prueba independiente del transporte. El módulo
conserva el bloque recibido en `observation.raw`, incluso si contiene JSON
malformado, texto incompleto o consumo inválido. No completa o corrige la prosa.

Se registran petición, recibo, huellas, código, eventos, marca previa y cierre.
El cierre separa consumo del intento, consumo heredado y consumo nuevo del acto
de registrar, que es cero. Los valores desconocidos permanecen desconocidos.
Un error explícito anterior a la consulta puede registrar cero llamadas sin
devolver la plaza contable ya reservada.

La captura admite peticiones de hasta 12.288 bytes y observaciones de hasta
256 KiB. Rechaza tamaños mayores sin recortar. Conservar datos no equivale a
validar una propuesta: `proposal_validation` sigue en `not_performed` y no hay
resultados calculados. El controlador deberá validar reglas y revisión aparte.

## Interrupciones y repetición

La reserva global de captura está en `.local/campaign-attempt-access`; las
capturas están en `.local/campaign-attempts`. Cambiar la carpeta de los archivos
no libera esa reserva. La marca previa al envío solo puede crearse una vez,
también cuando compiten varios procesos.

La misma observación completa puede volver a guardarse sin crear otra consulta
o modificar archivos. Una observación diferente se rechaza. Escrituras parciales,
un bloqueo interrumpido o una captura alterada se conservan y requieren detenerse;
no se reconstruye un cierre ni se reenvía automáticamente. Un fallo tras guardar
la fuente conserva esos bytes aunque todavía no exista un cierre verificable.

## Interpretar la consulta

La consulta muestra únicamente observaciones de propuestas de esta campaña.
No mezcla costes heredados con los nuevos ni pretende resumir toda la aplicación.
Sin reservas, el total de ese ámbito es cero. Con una captura pendiente, ausente
o no verificable, el total afectado queda desconocido y `requires_stop` es verdadero.
Los subtotales conocidos aparecen por separado y no sustituyen un total incompleto.

Un cierre con consumo desconocido, límites excedidos, coste inesperado o campos
incompatibles también exige detenerse. Un cierre con contabilidad completa no
significa que la respuesta contenga reglas válidas o una estrategia mejor.
La consulta no concede permisos ni comprueba vigencia de la memoria viva.

La [comprobación local](../reports/phase4-campaign-attempts-2026-10-20.md) consulta
la campaña de la aplicación sin inventar observaciones. Las capturas de éxito,
error y fallo parcial se prueban exclusivamente con datos artificiales.
