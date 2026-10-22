# Referencias y sensibilidad a comisiones

22/10/2026. Incremento de FASE 6, sin cierre de fase. Se mantienen los períodos
01/01–24/12 de 2024 y 2025, SMA 20/60, largos, 1.000 USD hipotéticos y cantidad
fija de 1 EUR. No se modifican el motor anterior ni sus resultados.

## Hipótesis fijadas antes de calcular

El [protocolo conservado](../reports/phase6-reference-costs-2026-10-22/protocol.json)
define cuatro tasas proporcionales por ejecución: **0; 0,0005; 0,001; 0,002**,
equivalentes a **0 %, 0,05 %, 0,1 % y 0,2 %**. Son supuestos de comparación, no
tarifas verificadas del proveedor. No se elige una tasa ganadora.

Las referencias son:

- **Efectivo:** mantener el capital en USD, con interés cero y sin operaciones.
- **Comprar y mantener:** comprar la cantidad fija en ASK en la primera apertura
  observada después de 61 sesiones UTC completas y mantenerla valorada a BID.
  Es la primera apertura en la que podría ejecutarse una decisión SMA 20/60 tras
  su calentamiento; no se escoge la fecha por su precio. Se necesitan 62 sesiones.

SMA conserva su ejecución en la siguiente apertura observada. Cada escenario
empieza con capital y posición propios, sin reinversión ni apalancamiento. El
spread permanece incluido con comisión cero. No se fuerza una venta final ni
se carga su comisión; la referencia termina con 1 EUR abierto en ambos años.
No se modelan swaps, deslizamiento o liquidez. El tiempo de exposición difiere:
la diferencia de patrimonio no es una medida ajustada por riesgo o exposición.

## Resultado bajo la comisión base de 0,1 %

| Período hasta el 24/12 | SMA 20/60, USD | Comprar y mantener, USD | Efectivo, USD |
| --- | ---: | ---: | ---: |
| 2024 | 999,96832951 | 999,94493691 | 1000 |
| 2025 | 999,98870447 | 1000,08745140 | 1000 |

La entrada de referencia es el 12/03/2024 y el 13/03/2025 a las 00:00 UTC.
SMA presenta mayor patrimonio que comprar y mantener en 2024 y menor en 2025,
en las cuatro tasas. Queda por debajo del efectivo en los ocho escenarios,
incluido cero comisión: el resultado negativo no se explica solo por la comisión.
Son importes pequeños porque la exposición es de solo 1 EUR frente a 1.000 USD.
No demuestran robustez o rentabilidad fuera de estos períodos conocidos.

Los años completos siguen bloqueados por sus huecos del 25/12. Esta entrega no
rellena precios, cambia fechas ni publica métricas sobre esos años bloqueados.

## Uso en la interfaz

En **Simulación y TradingView → Comparar con referencias y comisiones**, elegir
el histórico, capital y cantidad. **Calcular referencias y costes** verifica los
originales y guarda los cuatro escenarios y sus entradas exactas. Consultar un
ensayo guardado no vuelve a ejecutar estrategias ni modifica cuentas virtuales.

La ficha muestra patrimonio para las cuatro comisiones, la referencia en efectivo
y un selector de escenario con retorno, caída observada, comisiones, cierres,
posición y diferencias en USD. Permite revisar operaciones y rechazos, procedencia
y descargar el JSON. Si no hay saldo para la compra de referencia, se conserva
el rechazo y el efectivo; no se reduce la cantidad para forzar una entrada.

El listado usa un resumen acotado. Abrir la ficha contrasta el resultado, sus copias
de entrada y el resumen, sin recalcular señales. Las huellas detectan cambios;
no autentican al proveedor ni sustituyen la comprobación aritmética independiente.

## Verificación

391 pruebas seleccionadas aprobadas: 28 nuevas y las 363 seleccionadas anteriores.
No se ejecuta toda la colección. Un programa independiente con stdlib/Decimal
reproduce desde los gzip los ocho escenarios: **4.920 puntos de patrimonio y 44
ejecuciones**, incluyendo las referencias. La tasa base reproduce exactamente
los cálculos SMA anteriores. Se comprueba también el formulario y el cambio de
comisión en navegador. Evidencia en el [informe](../reports/phase6-reference-costs-2026-10-22/README.md).

El incremento posterior ya conecta la [conversación con los nuevos históricos](CHAT_PRICES.md)
y sus pruebas revisadas. La equivalencia externa Pine, importaciones de operaciones
y el puente a operaciones virtuales siguen pendientes. No se habilita una demo
externa ni se realiza commit o push.
