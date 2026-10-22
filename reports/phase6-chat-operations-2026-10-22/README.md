# Intenciones y operaciones virtuales manuales desde el chat

22/10/2026. Primer recorrido manual de FASE 6.6, sin cierre de fase.
`protocol.json` fija la demostración antes de ejecutar acciones con la interfaz.

## Implementación

`conversation_operations` conserva cuentas manuales, intenciones y asientos en
`.local/manual-simulation/ledger.sqlite3`. No cambia el motor contable anterior,
sus cuentas, contratos Pine, fills o inbox. Reutiliza las transiciones puras de
saldo y riesgo del simulador existente con una configuración de cuenta manual,
sin presentar estas operaciones como ejecuciones de una estrategia.

El campo **Petición de operación virtual** admite «simula comprar/vender cantidad
EUR/USD» y rechaza condiciones adicionales. Es un recorrido explícito dentro de
la conversación, separado del envío al modelo. No interpreta lenguaje arbitrario,
invoca el LLM, obtiene precios automáticamente ni consume sus presupuestos.

La cuenta revisada fija capital USD, cantidad máxima EUR, comisión proporcional
y riesgo: pausa al 20 % de caída, hasta 1.000 compras, precio de hasta 48 horas.
Guardar una intención conserva texto, cantidad, BID/ASK aportado, instante UTC,
fuente no verificada, cuenta, versión y estado revisados, sin mover saldo.

Otra aprobación identifica la intención y su huella. El simulador comprueba saldo,
posición, límite de cantidad, acumulación, riesgo, código y antigüedad del precio.
Compra ASK y valora inmediatamente BID; vende BID y cobra comisión por separado.
La aprobación y asiento se confirman en una sola transacción SQLite, con identidad
única, cadena de hashes y recuperación por consulta. Repetir no duplica efectos.
Los fallos de precondición exigen revisión; los rechazos de riesgo se registran
sin fill ni coste. Una cancelación no revierte un asiento confirmado.

La interfaz muestra revisión, previsión, resultado confirmado, efectivo, EUR,
patrimonio al último BID, resultado realizado y costes. Las intenciones pertenecen
a su conversación; las cuentas manuales son seleccionables explícitamente en otras.
No se crean fondos nuevos al reintentar la misma cuenta ni al reutilizar su nombre.

## Demostración con precios artificiales

Desde la interfaz se crea `manual-verificacion-20261022`, capital 1.000 USD, máximo
1 EUR, comisión 0,001. Se guarda la compra con BID 1,1 / ASK 1,1002 y el saldo sigue
en 1.000 USD, sin posición. Tras revisar y aprobar, efectivo 998,8986998 USD,
posición 1 EUR y patrimonio 999,9986998 USD valorado BID. Se guarda y aprueba otra
intención para vender a BID 1,101 / ASK 1,1012. Termina con 999,9985988 USD, posición
cero, comisiones 0,0022012 USD y resultado realizado −0,0014012 USD.

Se usan precios artificiales para comprobar contabilidad. El instante es el de
introducción del ejemplo, no el de una supuesta observación de mercado. Este
resultado no se mezcla con los backtests ni se presenta como evidencia de estrategia.
La pequeña subida no cubre spread y comisiones. La cuenta de ejemplo queda cerrada
de posición y visible; no se borran sus asientos. Una reconstrucción independiente
con Decimal verifica los dos movimientos desde las peticiones y precios conservados.

Las conversaciones, revisiones, trabajos y resultados anteriores permanecen iguales.
Se mantienen reservas de tres respuestas y una comparación; no hay inferencias ni
backtests nuevos. Las cuentas e inbox de estrategia siguen vacíos. Se verifica la
conservación de nueve informes previos y sus originales.

## Validación

562 pruebas seleccionadas aprobadas, incluidas 37 nuevas. Cubren petición estricta,
cotización inválida/caducada/futura, revisión sin efectos, aprobación explícita,
cantidades/saldo/posición/riesgo, compra ASK y valoración BID, rechazo, cancelación,
cambio de cuenta/motor, repetición concurrente, reinicio, fallo atómico y alteración
de entradas/cadena/resultados. Prueba HTTP con controles de origen/token y presupuestos
sin cambios. No se ejecuta la colección completa. Caché desactivada y temporal GUID
exclusivo según AGENTS.md. Sintaxis JavaScript y espacios de Git comprobados.

Se guarda estado previo, estado tras compra, estado final, registro contable,
auditoría independiente, pruebas, fuentes y capturas con manifiesto de huellas.
La navegación de la pestaña del usuario se conserva; la comprobación continúa en
una pestaña independiente. No se guarda el token HTTP de acciones.

FASE 6 sigue abierta por el contraste externo y tratamiento de novedades pendientes.
No se modifica PROJECT_STATUS, realiza commit/push ni envía una orden externa.
