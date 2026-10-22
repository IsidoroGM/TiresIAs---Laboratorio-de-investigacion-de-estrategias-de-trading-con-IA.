# Operaciones virtuales manuales desde la conversación

22/10/2026. Primer recorrido local de FASE 6.6. En **Conversar con el agente**, bajo
**Estrategia y prueba histórica**, aparece **Operaciones virtuales manuales**.
Son cuentas independientes de los backtests y del inbox de ejecuciones Pine.

## Recorrido

1. Abrir **Crear otra cuenta virtual manual**. Revisar nombre, capital hipotético
   USD, cantidad máxima EUR por operación, comisión proporcional y límites fijos.
   Marcar la revisión y crear la cuenta. Su saldo no procede de ningún bróker.
2. Elegir una cuenta manual y escribir **simula comprar 1 EUR/USD** o
   **simula vender 1 EUR/USD** en **Petición de operación virtual**. Se admite
   cantidad decimal con punto o coma. Este campo es distinto del envío al modelo.
3. Aportar BID, ASK e instante UTC del precio. La aplicación no obtiene ni verifica
   una cotización de mercado: estos valores son supuestos del usuario. Los ejemplos
   artificiales sirven para comprobar contabilidad, no para evaluar una estrategia.
4. Marcar la revisión y pulsar **Revisar intención virtual**. Se conserva la petición
   original, cantidad normalizada, cuenta, precio, fecha, estado y huellas. Aparece
   la previsión de efectivo, posición, patrimonio y posibles bloqueos. El saldo
   todavía no cambia.
5. Revisar la ficha guardada, marcar su aprobación y pulsar
   **Aprobar y ejecutar solo en cuenta virtual**. Se comprueban de nuevo estado,
   precio, versión del motor y límites. El resultado confirmado queda enlazado a
   esa conversación y conserva la aprobación. Una intención pendiente puede cancelarse.

Las cuentas manuales son seleccionables desde otras conversaciones; las intenciones
y sus aprobaciones pertenecen a la conversación donde se revisaron. No se pueden
aprobar desde otra conversación. El mismo nombre no permite reiniciar un saldo.

## Precio y contabilidad

La compra usa ASK; la venta y valoración usan BID. El spread se refleja en los
precios y la comisión proporcional se cobra aparte. El patrimonio es efectivo
más EUR valorados al último BID aportado; puede estar desactualizado. Se muestra
resultado realizado, comisiones y posición. La comisión de compra se incorpora
al coste de adquisición; el resultado realizado se reconoce al vender.

Se reutiliza la transición contable y de riesgo del simulador existente, sin
cambiarlo ni representar esta operación como un fill de estrategia. Límites:
largos, EUR/USD, sin apalancamiento ni compras acumuladas; máximo por orden revisado
al crear la cuenta, hasta 1.000 compras y pausa al alcanzar caída del 20 %.
Precios futuros o de más de 48 horas se bloquean. Las ventas para reducir posición
siguen permitidas durante una pausa de riesgo, sujetas a cantidad y costes.

Las condiciones adicionales, otros instrumentos, stops, órdenes pendientes y
peticiones fuera de la gramática se rechazan, sin omitir condiciones silenciosamente.
El recorrido no necesita al modelo ni consume sus 24 respuestas o cuatro comparaciones.
La interpretación libre de operaciones por el LLM y las cotizaciones automáticas
siguen pendientes; escribir «compra ahora» en el mensaje general no opera una cuenta.

## Duplicados y recuperación

Revisión, cuenta y aprobación usan identidades persistidas. La aprobación y el
asiento se confirman en una única transacción SQLite: una repetición, doble clic,
petición simultánea o reinicio no vuelve a aplicar la misma intención. Si cambia
el estado de la cuenta, el código o caduca el precio, hace falta otra revisión.
Un rechazo de riesgo queda registrado una sola vez, sin ejecución ni comisión,
con la pausa prevista por el simulador. Una cancelación no revierte operaciones
ya aplicadas. GET y recargar solo consultan.

El registro independiente está en `.local/manual-simulation/ledger.sqlite3`, con
cadena de asientos y huellas de configuración, intención, aprobación y resultados.
Las cuentas, eventos e inbox de `.local/simulation/` permanecen independientes.

## Comprobación

562 pruebas seleccionadas aprobadas, incluidas 37 nuevas. El recorrido de navegador
crea `manual-verificacion-20261022`, capital 1.000 USD, máximo 1 EUR, comisión 0,001.
Con precios artificiales fijados antes del ensayo compra 1 EUR a ASK 1,1002 y vende
a BID 1,101: termina con **999,9985988 USD**, sin posición y resultado realizado
**−0,0014012 USD**. La subida del precio no cubre spread y comisiones del ejemplo.
No es una prueba de rentabilidad del agente. Las pérdidas de los backtests anteriores
no cambian. No se consumen respuestas ni comparaciones adicionales.

Evidencia en `reports/phase6-chat-operations-2026-10-22/`. FASE 6 sigue abierta:
el contraste externo y el tratamiento de novedades siguen pendientes. No hay cierre,
cambio de PROJECT_STATUS, commit ni push.
