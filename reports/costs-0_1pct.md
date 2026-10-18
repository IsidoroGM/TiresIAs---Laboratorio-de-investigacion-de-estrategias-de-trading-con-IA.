# Trading AI — Informe educativo SMA20/SMA60

Formato de informe: 2. Fuente: Banco Central Europeo (BCE).
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
- Coste hipotético por compra o venta: 0.100 % del importe simulado.
- Coste = precio de ejecución simulado × una unidad base × tasa; moneda cotizada.
- No representa tarifas de un bróker. Con tasa 0 se mantienen costes cero.
- Sin cuenta de capital, margen ni financiación modelados.
- Última señal sin ejecución. Sin cierre forzado ni valoración de posiciones abiertas.
- Cálculos Decimal con 28 dígitos significativos; tablas redondeadas solo al mostrar.

## Cobertura y cierres

| Par | Inicio | Fin | Observaciones | Cierres | Ganadoras | Perdedoras | A cero | Abierta |
|---|---|---|---:|---:|---:|---:|---:|---:|
| EUR/USD | 1999-01-04 | 2026-10-16 | 7116 | 69 | 26 | 43 | 0 | No |
| GBP/USD | 1999-01-04 | 2026-10-16 | 7116 | 70 | 26 | 44 | 0 | No |
| USD/JPY | 1999-01-04 | 2026-10-16 | 7116 | 67 | 25 | 42 | 0 | No |
| USD/CHF | 1999-01-04 | 2026-10-16 | 7116 | 70 | 18 | 52 | 0 | Sí |

## Métricas de cierres — después de costes

| Par | Moneda | % ganadoras | Resultado | Media/cierre | Ganancias | Pérdidas (magnitud) | Profit factor |
|---|---|---:|---:|---:|---:|---:|---:|
| EUR/USD | USD | 37.68 | 0.097081 | 0.001407 | 1.311541 | 1.214460 | 1.0799 |
| GBP/USD | USD | 37.14 | -0.390345 | -0.005576 | 1.236718 | 1.627063 | 0.7601 |
| USD/JPY | JPY | 37.31 | 29.313503 | 0.437515 | 121.057744 | 91.744241 | 1.3195 |
| USD/CHF | CHF | 25.71 | -0.765682 | -0.010938 | 0.409451 | 1.175133 | 0.3484 |

N/D: porcentaje y media no disponibles sin cierres; profit factor no disponible
sin pérdidas. Cierres a cero incluidos en el denominador del porcentaje ganador.
Profit factor = ganancias / magnitud de pérdidas, ambas netas de costes de cierres.
Importes en moneda cotizada. Ganadoras y perdedoras se clasifican después de costes.

## Comparación de resultados y costes

| Par | Moneda | Cierres antes de costes | Costes de cierres | Cierres después de costes | Costes incurridos totales | Resultado tras costes incurridos* |
|---|---|---:|---:|---:|---:|---:|
| EUR/USD | USD | 0.261600 | 0.164519 | 0.097081 | 0.164519 | 0.097081 |
| GBP/USD | USD | -0.175555 | 0.214789 | -0.390345 | 0.214789 | -0.390345 |
| USD/JPY | JPY | 44.600130 | 15.286627 | 29.313503 | 15.286627 | 29.313503 |
| USD/CHF | CHF | -0.616511 | 0.149170 | -0.765682 | 0.149996 | -0.766507 |

* Cierres netos menos el coste de entrada de la posición abierta, si existe.
No incluye su variación de precio ni supone que se haya vendido. No es el patrimonio total.

## Posiciones abiertas (excluidas de las métricas)

- EUR/USD: ninguna.
- GBP/USD: ninguna.
- USD/JPY: ninguna.
- USD/CHF: 1 USD; señal 2026-09-17; entrada simulada 2026-09-18 a 0.825654 CHF por unidad base. Coste de entrada ya incurrido: 0.000826 CHF. Resultado latente no calculado.

## Limitaciones

No sumar importes de monedas distintas. No son rentabilidades porcentuales sobre capital.
El coste proporcional es hipotético: faltan spreads, comisiones, slippage y swaps reales,
además de curva de capital y drawdown. No se ajusta el precio simulado por liquidez.
No se ha contrastado el calendario completo de publicación ni rellenado fechas ausentes.
Sin optimización ni validación fuera de muestra; estas métricas no demuestran viabilidad real.
No hay órdenes reales ni conexión con un bróker. Informe educativo, sin recomendación de inversión.

## Reproducción

Desde la raíz: `python -m trading_ai --report --cost-percent 0.100 --data RUTA_XML --output RUTA_MD`.
Usar la misma copia (SHA-256), código y reglas. El informe no incluye hora de ejecución
ni rutas locales, para obtener el mismo contenido al repetir el cálculo.
