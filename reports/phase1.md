# Trading AI — Informe educativo SMA20/SMA60

Formato de informe: 1. Fuente: Banco Central Europeo (BCE).
[Histórico oficial](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml).
SHA-256 de la copia analizada: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

## Reglas y supuestos

- Referencias diarias informativas, no velas OHLC ni precios ejecutables.
- EUR/USD directo; GBP/USD = USD/GBP, USD/JPY = JPY/USD y USD/CHF = CHF/USD
  a partir de las referencias BCE de la misma fecha, todas expresadas por euro.
- Medias de 20 y 60 observaciones publicadas, no días naturales.
- Entrada: rápida pasa de <= lenta a > lenta. Salida: pasa de >= a <.
- Sin señal si faltan medias actuales o anteriores; igualdad actual sin señal.
- Ejecución simulada en la referencia de la observación siguiente.
- Inicio sin posición; una compra de una unidad base por par, sin cortos.
- Entradas estando dentro y salidas estando fuera se ignoran.
- Costes cero; sin cuenta de capital, margen ni financiación modelados.
- Última señal sin ejecución. Sin cierre forzado ni valoración de posiciones abiertas.
- Cálculos Decimal con 28 dígitos significativos; tablas redondeadas solo al mostrar.

## Cobertura y cierres

| Par | Inicio | Fin | Observaciones | Cierres | Ganadoras | Perdedoras | A cero | Abierta |
|---|---|---|---:|---:|---:|---:|---:|---:|
| EUR/USD | 1999-01-04 | 2026-10-16 | 7116 | 69 | 26 | 43 | 0 | No |
| GBP/USD | 1999-01-04 | 2026-10-16 | 7116 | 70 | 27 | 43 | 0 | No |
| USD/JPY | 1999-01-04 | 2026-10-16 | 7116 | 67 | 28 | 39 | 0 | No |
| USD/CHF | 1999-01-04 | 2026-10-16 | 7116 | 70 | 20 | 50 | 0 | Sí |

## Métricas de cierres — costes cero

| Par | Moneda | % ganadoras | Resultado | Media/cierre | Ganancias | Pérdidas (magnitud) | Profit factor |
|---|---|---:|---:|---:|---:|---:|---:|
| EUR/USD | USD | 37.68 | 0.261600 | 0.003791 | 1.374400 | 1.112800 | 1.2351 |
| GBP/USD | USD | 38.57 | -0.175555 | -0.002508 | 1.316415 | 1.491971 | 0.8823 |
| USD/JPY | JPY | 41.79 | 44.600130 | 0.665674 | 127.310592 | 82.710461 | 1.5392 |
| USD/CHF | CHF | 28.57 | -0.616511 | -0.008807 | 0.450649 | 1.067160 | 0.4223 |

N/D: porcentaje y media no disponibles sin cierres; profit factor no disponible
sin pérdidas. Cierres a cero incluidos en el denominador del porcentaje ganador.
Profit factor = ganancias / magnitud de pérdidas. Importes en moneda cotizada.

## Posiciones abiertas (excluidas de las métricas)

- EUR/USD: ninguna.
- GBP/USD: ninguna.
- USD/JPY: ninguna.
- USD/CHF: 1 USD; señal 2026-09-17; entrada simulada 2026-09-18 a 0.825654 CHF por unidad base. Resultado latente no calculado.

## Limitaciones

No sumar importes de monedas distintas. No son rentabilidades porcentuales sobre capital.
Faltan spreads, comisiones, slippage, swaps, curva de capital y drawdown.
No se ha contrastado el calendario completo de publicación ni rellenado fechas ausentes.
Sin optimización ni validación fuera de muestra; estas métricas no demuestran viabilidad real.
No hay órdenes reales ni conexión con un bróker. Informe educativo, sin recomendación de inversión.

## Reproducción

Desde la raíz del proyecto: `python -m trading_ai --report --data RUTA_XML --output RUTA_MD`.
Usar la misma copia (SHA-256), código y reglas. El informe no incluye hora de ejecución
ni rutas locales, para obtener el mismo contenido al repetir el cálculo.
