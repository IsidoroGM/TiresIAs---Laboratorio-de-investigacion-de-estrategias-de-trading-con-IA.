# Trading AI — Comparación SMA y EMA

Formato de comparación: 1. Fuente: Banco Central Europeo (BCE).
[Histórico oficial](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml).
SHA-256 de la copia analizada: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

## Condiciones comunes

- Ventanas rápida/lenta: 20/60 observaciones publicadas, no días naturales.
- SMA: promedio de las últimas n observaciones. EMA: semilla SMA de las primeras n;
  alfa = 2/(n+1); EMA actual = anterior + alfa × (precio - anterior).
  EMA conserva influencia de observaciones anteriores a n; la fecha inicial afecta a su semilla.
- Primera señal posible desde la observación 61; sin señales con medias incompletas.
- Entrada cuando rápida cruza de <= a > lenta; salida de >= a <; igualdad actual sin señal.
- Ejecución en la referencia siguiente. Inicio sin posición; una compra por par, sin cortos ni margen.
- Última señal sin ejecución; no se fuerza cierre al final. Capital y costes independientes por estrategia y par.
- Capital inicial: 1000 en la moneda cotizada de cada cuenta.
- Tamaño: 10.0 % del efectivo disponible en cada entrada, costes incluidos.
- Coste hipotético por compra o venta: 0.100 % del importe ejecutado.
- Solo compra con saldo suficiente; una entrada rechazada no se aplaza ni genera coste.
- Mismos precios y fechas para ambas estrategias en cada par. Decimal con 28 dígitos significativos.
- EUR/USD directo; GBP/USD = USD/GBP, USD/JPY = JPY/USD, USD/CHF = CHF/USD desde las referencias por euro.

## Cobertura por par

| Par | Inicio | Fin | Observaciones |
|---|---|---|---:|
| EUR/USD | 1999-01-04 | 2026-10-16 | 7116 |
| GBP/USD | 1999-01-04 | 2026-10-16 | 7116 |
| USD/JPY | 1999-01-04 | 2026-10-16 | 7116 |
| USD/CHF | 1999-01-04 | 2026-10-16 | 7116 |

## Resultados por cuenta

| Par | Estrategia | Moneda | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Drawdown máximo % | Costes incurridos | Entradas rechazadas |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| EUR/USD | SMA20/SMA60 | USD | 69 | No | 1015.009331 | 15.009331 | 1.500933 | 2.508037 | 14.053751 | 0 |
| EUR/USD | EMA20/EMA60 | USD | 61 | No | 1013.740017 | 13.740017 | 1.374002 | 3.627450 | 12.458430 | 0 |
| GBP/USD | SMA20/SMA60 | USD | 70 | No | 977.844806 | -22.155194 | -2.215519 | 4.729938 | 13.940866 | 0 |
| GBP/USD | EMA20/EMA60 | USD | 56 | No | 998.897874 | -1.102126 | -0.110213 | 2.899616 | 11.188538 | 0 |
| USD/JPY | SMA20/SMA60 | JPY | 67 | No | 1029.441001 | 29.441001 | 2.944100 | 3.674652 | 13.401913 | 0 |
| USD/JPY | EMA20/EMA60 | JPY | 62 | No | 1026.320534 | 26.320534 | 2.632053 | 5.073104 | 12.324971 | 0 |
| USD/CHF | SMA20/SMA60 | CHF | 70 | Sí | 930.922718 | -69.077282 | -6.907728 | 7.825079 | 13.490837 | 0 |
| USD/CHF | EMA20/EMA60 | CHF | 59 | Sí | 950.072500 | -49.927500 | -4.992750 | 6.237574 | 11.520639 | 0 |

Resultado total = capital final - capital inicial: incluye la variación latente de posiciones abiertas
y todos los costes incurridos; no equivale solo al beneficio realizado de cierres.
Rentabilidad = resultado total / capital inicial × 100, acumulada durante todo el periodo, no anualizada.
La posición abierta se valora a la última referencia; no se anticipa coste de salida.
Drawdown máximo: mayor caída porcentual desde un máximo previo del capital diario, incluido el inicial.
Costes ya descontados del capital; no restarlos otra vez. Cero cierres no implica ausencia de exposición.

## Límites de la comparación

Referencias informativas, no precios ejecutables ni velas OHLC. No se valida el calendario ni se rellenan fechas.
Faltan spreads, slippage, swaps y restricciones reales de bróker. No hay órdenes reales ni conexión con un bróker.
Comparar dentro de cada par; no sumar monedas distintas. Igual asignación no implica igual riesgo.
Sin búsqueda de parámetros, ranking ni validación fuera de muestra. El resultado histórico no garantiza rentabilidad futura.

## Reproducción

`python -m trading_ai --compare --fast-window 20 --slow-window 60 --cost-percent 0.100 --initial-capital 1000 --allocation-percent 10.0 --data RUTA_XML --output RUTA_MD`
Usar la misma copia (SHA-256), código y reglas. Sin hora de ejecución ni rutas locales en el contenido.
