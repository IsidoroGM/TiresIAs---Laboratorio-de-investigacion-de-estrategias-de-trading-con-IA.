# Registro contable compartido — 20/10/2026

Se implementó el registro SQLite y se inscribió el plan de campaña de la
aplicación sin activar herramientas ni ocupar huecos. SQLite 3.50.4 ya estaba
incluido en el Python del proyecto; no se instaló una dependencia o servicio.

- Plan: `.local/campaign-plans/37316f24fb92479aa7b9af4ab8134ed0`.
- Registro local mutable: `.local/campaign-ledger/registry.sqlite3`.
- Auditoría: `.local/campaign-ledger-audits/261a7f9f850e425f906a78148e04add9`.
- Estado: `registered_inactive`; límites contables de tres propuestas y seis backtests.
- Reservas nuevas en la aplicación: cero propuestas y cero backtests.
- Capacidad ejecutable y permiso de ejecución: cero y desactivado.

El registro fija los primeros términos de un ámbito de datos/par. Otro plan no
los sustituye o reinicia. Las reservas internas son exclusivas e idempotentes:
una propuesta ocupa una plaza y una comparación ocupa dos backtests juntos.
Se conserva la plaza tras un fallo del llamador; una transacción sin confirmar
se deshace sin entregar un recibo. No existe una herramienta de liberación,
reinicio o cambio de base por CLI.

Los recibos son únicamente contables. No validan una petición, revisión o plan
de cálculo ni sustituyen la reserva compartida del motor. El estado tampoco
afirma vigencia de la memoria viva del investigador. El permiso de ejecución,
los resultados y el controlador siguen pendientes.

## Comprobaciones

Pasaron **68 pruebas focalizadas en 51,16 segundos**: las 39 de planes y 29 del
nuevo registro. Incluyen hilos y procesos Windows con `spawn`, claves repetidas,
competencia por el último par de backtests, fallos antes y después del compromiso,
cambios de términos, corrupción y consultas sin escritura. Utilizaron únicamente
datos artificiales y bases temporales exclusivas, con caché de pytest desactivada.

La última suite global verificada sigue siendo la anterior de 1.253 pruebas;
los 68 pases conjuntos no se presentan como una suite global nueva.

La auditoría sobre el plan de la aplicación mantuvo los cinco contadores
red/proveedor/cálculo/reserva heredada/evaluación exterior a cero. Los nueve
archivos de reservas anteriores y las 273 copias de evidencia anteriores
conservaron sus bytes y referencias originales. Se añadieron ocho copias:
**281 copias y 281 referencias originales entre 19 inventarios concretos**.
Las referencias pueden repetirse; no se presentan como archivos físicos únicos.

El [inventario](phase4-campaign-ledger-2026-10-20/snapshot.json) contiene estado,
auditoría, huella, eventos, script, código, pruebas e instantánea SQLite. La
instantánea se generó con la copia de seguridad de SQLite y se contrastó con el
estado lógico original. Su fuente archivada es independiente de la base viva:
reservas futuras legítimas no reescriben esta evidencia. No restaura presupuesto.

## Consumo y límites

Consumo nuevo de investigación: **cero consultas, tokens, coste de API y
backtests**. El registro conserva por separado el consumo heredado del intento
compacto: 2.262 tokens de entrada, 176 de salida y 0 USD de API. Es un subtotal
histórico de ese ámbito, no consumo de toda la aplicación ni una consulta repetida.

El intento compacto y la reformulación anterior siguen consumidos. No se revisó,
reformuló o simuló la candidata real duplicada. No se reinterpretó evaluación
conocida como inédita. FASE 4 abierta y `PROJECT_STATUS.md` intacto; sin dinero
real, servicios nuevos, commits o pushes.

Uso y límites: [registro de campañas](../docs/CAMPAIGN_LEDGER.md).
