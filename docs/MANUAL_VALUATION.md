# Valorar una cuenta manual sin comprar ni vender

Incremento local posterior al commit publicado `0bd9011`, 22/10/2026. En el modo
manual del chat, abrir **Valoración de nombre-de-cuenta**. La ficha muestra último
BID aportado, fecha UTC, antigüedad, resultado no realizado y pausa de riesgo.

Para actualizarla, aportar BID, ASK de referencia e instante UTC, marcar la revisión
y pulsar **Actualizar valoración de nombre-de-cuenta**. El precio sigue siendo un
supuesto aportado, sin verificación de mercado. La valoración usa BID; ASK se
conserva como referencia y permite comprobar que el spread no esté cruzado.

El estado consultado queda fechado. La antigüedad avanza mientras la pantalla
permanece abierta, sin recargar formularios ni generar operaciones. Los avisos
distinguen falta de precio, fecha futura, precio de más de 48 horas y precio dentro
del límite. Estar dentro del límite no acredita que la cotización sea auténtica.

## Efectos y controles

- Actualiza precio, patrimonio, máximo de patrimonio, caída y posible pausa de
  riesgo. El resultado no realizado es cantidad por BID menos coste de adquisición.
- Mantiene efectivo, EUR, coste de adquisición, resultado realizado, comisiones,
  número de operaciones y secuencia. No aplica una comisión nueva ni crea un fill.
- Comprueba aprobación explícita, estado de cuenta y huellas de código revisadas,
  precio positivo, ASK mayor o igual a BID, antigüedad y orden de los instantes.
  Un instante ya usado con otro BID requiere una observación posterior.
- Conserva la valoración y aprobación en un asiento atómico del mismo registro
  manual. Repetir una identidad con los mismos datos devuelve el asiento original;
  usarla con otros datos o conversación se rechaza. No se migra ni reinicia la base.
- Cambiar la valoración invalida las intenciones pendientes revisadas con la
  cadena anterior. Las ventas para reducir posición siguen permitidas durante una
  pausa, con los controles del simulador. No se reactivan compras automáticamente.

Las cuentas anteriores conservan compatibilidad: no se cambian el motor manual
de operaciones, el simulador, sus límites ni sus huellas previas. El nuevo componente
tiene su propia huella y la incorpora a cada aprobación de valoración. La interfaz
muestra las últimas 200 valoraciones de esa conversación, con sus originales.
Las lecturas comparten una instantánea de estado, intenciones e historial.

## Comprobación

586 pruebas seleccionadas aprobadas, incluidas 24 nuevas. En navegador se crea
`manual-valoracion-20261022`, con capital hipotético 1.000 USD, máximo 1 EUR y
comisión 0,001. Una compra artificial a ASK 1,1002 deja 998,8986998 USD y 1 EUR,
valorado inicialmente a BID 1,1. Un BID posterior de ejemplo 1,09 actualiza el
patrimonio a **999,9886998 USD** y el resultado no realizado a **−0,0113002 USD**.
Siguen existiendo una sola compra y comisiones de 0,0011002 USD. La posición de
ejemplo queda abierta en su cuenta virtual independiente; no hay cuenta externa.

Este ensayo verifica contabilidad y presentación, no rendimiento de una estrategia.
No consulta al modelo ni calcula otra estrategia. Se detectó una petición adicional
del usuario en la aplicación antes del ensayo y se conserva sin reintentarla ni
atribuir su consumo a esta comprobación. Evidencia en
`reports/phase6-manual-valuation-2026-10-22/`. FASE 6 permanece abierta, PROJECT_STATUS
no cambia. Este incremento es local y posterior al commit/push solicitado.
