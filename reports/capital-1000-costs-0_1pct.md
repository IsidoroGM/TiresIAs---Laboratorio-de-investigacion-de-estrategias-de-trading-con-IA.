# Trading AI — Informe educativo SMA20/SMA60

Formato de informe: 3. Fuente: Banco Central Europeo (BCE).
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
- Capital inicial por cuenta independiente: 1000 unidades de su moneda cotizada.
- Compra solo con saldo suficiente para precio más coste; sin margen ni financiación.
- Entrada rechazada por falta de saldo no queda pendiente ni genera coste.
- Última señal sin ejecución. Sin cierre forzado; posición abierta valorada a cada referencia.
- Capital diario = efectivo + valor de la posición después de ejecutar la señal anterior.
- Drawdown = máximo de capital alcanzado menos capital actual; porcentaje respecto a ese máximo.
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

## Capital y drawdown (incluyen posiciones abiertas)

| Par | Moneda | Capital inicial | Capital final | Drawdown máximo | Drawdown máximo % | Entradas rechazadas |
|---|---|---:|---:|---:|---:|---:|
| EUR/USD | USD | 1000.000000 | 1000.097081 | 0.341592 | 0.034146 | 0 |
| GBP/USD | USD | 1000.000000 | 999.609655 | 0.792183 | 0.079189 | 0 |
| USD/JPY | JPY | 1000.000000 | 1029.313503 | 39.256597 | 3.890975 | 0 |
| USD/CHF | CHF | 1000.000000 | 999.231796 | 0.914781 | 0.091466 | 0 |

Drawdowns positivos medidos en cada observación, incluyendo el capital inicial como máximo de partida.
Los máximos absoluto y porcentual pueden corresponder a fechas distintas. No se miden caídas intradiarias.
Una unidad base fija sobre cuentas de 1000 o más puede implicar exposición muy pequeña;
un drawdown pequeño no demuestra que la estrategia sea segura con otro tamaño de posición.

## Evolución del capital (resumen anual de la curva diaria)

Última observación disponible de cada año; año final posiblemente incompleto.
La curva diaria completa queda en BacktestResult.equity_curve; el drawdown usa todos sus puntos.

| Par | Fecha | Efectivo | Valor posición | Capital | Moneda |
|---|---|---:|---:|---:|---|
| EUR/USD | 1999-12-30 | 999.919644 | 0.000000 | 999.919644 | USD |
| EUR/USD | 2000-12-29 | 998.966488 | 0.930500 | 999.896988 | USD |
| EUR/USD | 2001-12-28 | 999.925075 | 0.000000 | 999.925075 | USD |
| EUR/USD | 2002-12-31 | 999.037257 | 1.048700 | 1000.085957 | USD |
| EUR/USD | 2003-12-31 | 998.961090 | 1.263000 | 1000.224090 | USD |
| EUR/USD | 2004-12-31 | 998.935660 | 1.362100 | 1000.297760 | USD |
| EUR/USD | 2005-12-30 | 1000.143297 | 0.000000 | 1000.143297 | USD |
| EUR/USD | 2006-12-29 | 998.902096 | 1.317000 | 1000.219096 | USD |
| EUR/USD | 2007-12-31 | 998.798643 | 1.472100 | 1000.270743 | USD |
| EUR/USD | 2008-12-31 | 998.875272 | 1.391700 | 1000.266972 | USD |
| EUR/USD | 2009-12-31 | 1000.261643 | 0.000000 | 1000.261643 | USD |
| EUR/USD | 2010-12-31 | 1000.235331 | 0.000000 | 1000.235331 | USD |
| EUR/USD | 2011-12-30 | 1000.218049 | 0.000000 | 1000.218049 | USD |
| EUR/USD | 2012-12-31 | 998.936889 | 1.319400 | 1000.256289 | USD |
| EUR/USD | 2013-12-31 | 998.843872 | 1.379100 | 1000.222972 | USD |
| EUR/USD | 2014-12-31 | 1000.181676 | 0.000000 | 1000.181676 | USD |
| EUR/USD | 2015-12-31 | 1000.090925 | 0.000000 | 1000.090925 | USD |
| EUR/USD | 2016-12-30 | 1000.085486 | 0.000000 | 1000.085486 | USD |
| EUR/USD | 2017-12-29 | 998.981506 | 1.199300 | 1000.180806 | USD |
| EUR/USD | 2018-12-31 | 1000.193751 | 0.000000 | 1000.193751 | USD |
| EUR/USD | 2019-12-31 | 999.029293 | 1.123400 | 1000.152693 | USD |
| EUR/USD | 2020-12-31 | 998.987618 | 1.227100 | 1000.214718 | USD |
| EUR/USD | 2021-12-31 | 1000.173576 | 0.000000 | 1000.173576 | USD |
| EUR/USD | 2022-12-30 | 999.081508 | 1.066600 | 1000.148108 | USD |
| EUR/USD | 2023-12-29 | 999.026122 | 1.105000 | 1000.131122 | USD |
| EUR/USD | 2024-12-31 | 1000.048861 | 0.000000 | 1000.048861 | USD |
| EUR/USD | 2025-12-31 | 998.988357 | 1.175000 | 1000.163357 | USD |
| EUR/USD | 2026-10-16 | 1000.097081 | 0.000000 | 1000.097081 | USD |
| GBP/USD | 1999-12-30 | 999.986076 | 0.000000 | 999.986076 | USD |
| GBP/USD | 2000-12-29 | 998.444640 | 1.490947 | 999.935587 | USD |
| GBP/USD | 2001-12-28 | 999.918755 | 0.000000 | 999.918755 | USD |
| GBP/USD | 2002-12-31 | 998.470876 | 1.612145 | 1000.083020 | USD |
| GBP/USD | 2003-12-31 | 998.404732 | 1.791998 | 1000.196730 | USD |
| GBP/USD | 2004-12-31 | 998.417285 | 1.931920 | 1000.349205 | USD |
| GBP/USD | 2005-12-30 | 1000.166580 | 0.000000 | 1000.166580 | USD |
| GBP/USD | 2006-12-29 | 998.259179 | 1.961281 | 1000.220460 | USD |
| GBP/USD | 2007-12-31 | 1000.170679 | 0.000000 | 1000.170679 | USD |
| GBP/USD | 2008-12-31 | 1000.044425 | 0.000000 | 1000.044425 | USD |
| GBP/USD | 2009-12-31 | 1000.148710 | 0.000000 | 1000.148710 | USD |
| GBP/USD | 2010-12-31 | 1000.139645 | 0.000000 | 1000.139645 | USD |
| GBP/USD | 2011-12-30 | 1000.041313 | 0.000000 | 1000.041313 | USD |
| GBP/USD | 2012-12-31 | 998.377331 | 1.616714 | 999.994045 | USD |
| GBP/USD | 2013-12-31 | 998.328497 | 1.654192 | 999.982689 | USD |
| GBP/USD | 2014-12-31 | 999.997453 | 0.000000 | 999.997453 | USD |
| GBP/USD | 2015-12-31 | 999.892060 | 0.000000 | 999.892060 | USD |
| GBP/USD | 2016-12-30 | 998.450499 | 1.231166 | 999.681666 | USD |
| GBP/USD | 2017-12-29 | 998.292051 | 1.351735 | 999.643786 | USD |
| GBP/USD | 2018-12-31 | 999.632290 | 0.000000 | 999.632290 | USD |
| GBP/USD | 2019-12-31 | 998.355599 | 1.320404 | 999.676003 | USD |
| GBP/USD | 2020-12-31 | 998.337944 | 1.364916 | 999.702860 | USD |
| GBP/USD | 2021-12-31 | 999.676152 | 0.000000 | 999.676152 | USD |
| GBP/USD | 2022-12-30 | 998.431757 | 1.202575 | 999.634333 | USD |
| GBP/USD | 2023-12-29 | 998.387662 | 1.271503 | 999.659165 | USD |
| GBP/USD | 2024-12-31 | 999.632818 | 0.000000 | 999.632818 | USD |
| GBP/USD | 2025-12-31 | 998.308603 | 1.346551 | 999.655154 | USD |
| GBP/USD | 2026-10-16 | 999.609655 | 0.000000 | 999.609655 | USD |
| USD/JPY | 1999-12-30 | 994.275131 | 0.000000 | 994.275131 | JPY |
| USD/JPY | 2000-12-29 | 881.293442 | 114.905965 | 996.199407 | JPY |
| USD/JPY | 2001-12-28 | 874.100984 | 130.863497 | 1004.964481 | JPY |
| USD/JPY | 2002-12-31 | 1002.191027 | 0.000000 | 1002.191027 | JPY |
| USD/JPY | 2003-12-31 | 996.800407 | 0.000000 | 996.800407 | JPY |
| USD/JPY | 2004-12-31 | 985.346871 | 0.000000 | 985.346871 | JPY |
| USD/JPY | 2005-12-30 | 875.594866 | 117.741799 | 993.336664 | JPY |
| USD/JPY | 2006-12-29 | 987.030664 | 0.000000 | 987.030664 | JPY |
| USD/JPY | 2007-12-31 | 981.622826 | 0.000000 | 981.622826 | JPY |
| USD/JPY | 2008-12-31 | 983.958984 | 0.000000 | 983.958984 | JPY |
| USD/JPY | 2009-12-31 | 890.320571 | 92.433708 | 982.754279 | JPY |
| USD/JPY | 2010-12-31 | 894.569012 | 81.312678 | 975.881690 | JPY |
| USD/JPY | 2011-12-30 | 893.669301 | 77.440297 | 971.109598 | JPY |
| USD/JPY | 2012-12-31 | 890.533665 | 86.107322 | 976.640986 | JPY |
| USD/JPY | 2013-12-31 | 883.081045 | 104.938003 | 988.019048 | JPY |
| USD/JPY | 2014-12-31 | 881.143522 | 119.619471 | 1000.762993 | JPY |
| USD/JPY | 2015-12-31 | 872.276743 | 120.391292 | 992.668035 | JPY |
| USD/JPY | 2016-12-30 | 886.944715 | 117.066692 | 1004.011407 | JPY |
| USD/JPY | 2017-12-29 | 993.595670 | 0.000000 | 993.595670 | JPY |
| USD/JPY | 2018-12-31 | 992.669021 | 0.000000 | 992.669021 | JPY |
| USD/JPY | 2019-12-31 | 882.385113 | 108.545487 | 990.930599 | JPY |
| USD/JPY | 2020-12-31 | 986.715009 | 0.000000 | 986.715009 | JPY |
| USD/JPY | 2021-12-31 | 879.017086 | 115.115663 | 994.132749 | JPY |
| USD/JPY | 2022-12-30 | 1016.233016 | 0.000000 | 1016.233016 | JPY |
| USD/JPY | 2023-12-29 | 1019.814479 | 0.000000 | 1019.814479 | JPY |
| USD/JPY | 2024-12-31 | 873.950787 | 156.954471 | 1030.905258 | JPY |
| USD/JPY | 2025-12-31 | 877.368706 | 156.672340 | 1034.041046 | JPY |
| USD/JPY | 2026-10-16 | 1029.313503 | 0.000000 | 1029.313503 | JPY |
| USD/CHF | 1999-12-30 | 998.381980 | 1.597750 | 999.979730 | CHF |
| USD/CHF | 2000-12-29 | 1000.003124 | 0.000000 | 1000.003124 | CHF |
| USD/CHF | 2001-12-28 | 998.376177 | 1.682628 | 1000.058805 | CHF |
| USD/CHF | 2002-12-31 | 1000.030976 | 0.000000 | 1000.030976 | CHF |
| USD/CHF | 2003-12-31 | 999.891978 | 0.000000 | 999.891978 | CHF |
| USD/CHF | 2004-12-31 | 999.848609 | 0.000000 | 999.848609 | CHF |
| USD/CHF | 2005-12-30 | 998.582802 | 1.318216 | 999.901019 | CHF |
| USD/CHF | 2006-12-29 | 999.802720 | 0.000000 | 999.802720 | CHF |
| USD/CHF | 2007-12-31 | 999.750550 | 0.000000 | 999.750550 | CHF |
| USD/CHF | 2008-12-31 | 999.703811 | 0.000000 | 999.703811 | CHF |
| USD/CHF | 2009-12-31 | 998.632199 | 1.029849 | 999.662047 | CHF |
| USD/CHF | 2010-12-31 | 999.602596 | 0.000000 | 999.602596 | CHF |
| USD/CHF | 2011-12-30 | 998.719559 | 0.939485 | 999.659044 | CHF |
| USD/CHF | 2012-12-31 | 999.654259 | 0.000000 | 999.654259 | CHF |
| USD/CHF | 2013-12-31 | 999.569704 | 0.000000 | 999.569704 | CHF |
| USD/CHF | 2014-12-31 | 998.664025 | 0.990363 | 999.654388 | CHF |
| USD/CHF | 2015-12-31 | 998.449958 | 0.995224 | 999.445182 | CHF |
| USD/CHF | 2016-12-30 | 998.387708 | 1.018784 | 999.406491 | CHF |
| USD/CHF | 2017-12-29 | 998.388561 | 0.975736 | 999.364297 | CHF |
| USD/CHF | 2018-12-31 | 999.378105 | 0.000000 | 999.378105 | CHF |
| USD/CHF | 2019-12-31 | 999.318616 | 0.000000 | 999.318616 | CHF |
| USD/CHF | 2020-12-31 | 999.268700 | 0.000000 | 999.268700 | CHF |
| USD/CHF | 2021-12-31 | 999.256909 | 0.000000 | 999.256909 | CHF |
| USD/CHF | 2022-12-30 | 999.301611 | 0.000000 | 999.301611 | CHF |
| USD/CHF | 2023-12-29 | 999.256392 | 0.000000 | 999.256392 | CHF |
| USD/CHF | 2024-12-31 | 998.395746 | 0.905958 | 999.301704 | CHF |
| USD/CHF | 2025-12-31 | 999.237887 | 0.000000 | 999.237887 | CHF |
| USD/CHF | 2026-10-16 | 998.407838 | 0.823958 | 999.231796 | CHF |

## Posiciones abiertas (excluidas de las métricas de cierres)

- EUR/USD: ninguna.
- GBP/USD: ninguna.
- USD/JPY: ninguna.
- USD/CHF: 1 USD; señal 2026-09-17; entrada simulada 2026-09-18 a 0.825654 CHF por unidad base. Coste de entrada ya incurrido: 0.000826 CHF. Variación de precio latente: -0.001696 CHF, incluida en el capital final. El coste de entrada ya está descontado del efectivo; no se anticipa un coste de salida.

## Limitaciones

No sumar cuentas de monedas distintas ni comparar su exposición como si fueran equivalentes.
El coste proporcional es hipotético: faltan spreads, comisiones, slippage y swaps reales,
No se ajusta el precio simulado por liquidez; la valoración usa referencias informativas.
No se ha contrastado el calendario completo de publicación ni rellenado fechas ausentes.
Sin optimización ni validación fuera de muestra; estas métricas no demuestran viabilidad real.
No hay órdenes reales ni conexión con un bróker. Informe educativo, sin recomendación de inversión.

## Reproducción

Desde la raíz: `python -m trading_ai --report --cost-percent 0.100 --initial-capital 1000 --data RUTA_XML --output RUTA_MD`.
Usar la misma copia (SHA-256), código y reglas. El informe no incluye hora de ejecución
ni rutas locales, para obtener el mismo contenido al repetir el cálculo.
