# Trading AI — Informe educativo SMA20/SMA60

Formato de informe: 4. Fuente: Banco Central Europeo (BCE).
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
- Inicio sin posición; una sola compra abierta por par, sin cortos.
- Tamaño: 10.0 % del efectivo disponible al ejecutar cada entrada, incluyendo su coste.
- Modo porcentual: presupuesto = efectivo × asignación; cantidad = presupuesto / (precio × (1 + tasa de coste)).
- La cantidad se ajusta hacia abajo para no superar el presupuesto y no se rebalancea mientras está abierta.
- Asignación es capital invertido, no pérdida máxima; no hay stop-loss ni restricciones de lotes de bróker.
- Entradas estando dentro y salidas estando fuera se ignoran.
- Coste hipotético por compra o venta: 0.100 % del importe simulado.
- Coste = precio de ejecución simulado × cantidad base × tasa; moneda cotizada.
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

## Tamaño de las entradas ejecutadas

Incluye las operaciones cerradas y la posición abierta; cantidades en moneda base.

| Par | Moneda base | Cantidad mínima | Cantidad máxima |
|---|---|---:|---:|
| EUR/USD | EUR | 65.696756 | 113.094678 |
| GBP/USD | GBP | 49.626808 | 82.818711 |
| USD/JPY | USD | 0.643408 | 1.248120 |
| USD/CHF | USD | 58.575454 | 117.357800 |

## Métricas de cierres — después de costes

| Par | Moneda | % ganadoras | Resultado | Media/cierre | Ganancias | Pérdidas (magnitud) | Profit factor |
|---|---|---:|---:|---:|---:|---:|---:|
| EUR/USD | USD | 37.68 | 15.009331 | 0.217527 | 116.489799 | 101.480468 | 1.1479 |
| GBP/USD | USD | 37.14 | -22.155194 | -0.316503 | 82.655633 | 104.810826 | 0.7886 |
| USD/JPY | JPY | 37.31 | 29.441001 | 0.439418 | 112.503387 | 83.062386 | 1.3544 |
| USD/CHF | CHF | 25.71 | -68.793119 | -0.982759 | 36.070736 | 104.863855 | 0.3440 |

N/D: porcentaje y media no disponibles sin cierres; profit factor no disponible
sin pérdidas. Cierres a cero incluidos en el denominador del porcentaje ganador.
Profit factor = ganancias / magnitud de pérdidas, ambas netas de costes de cierres.
Importes en moneda cotizada. Ganadoras y perdedoras se clasifican después de costes.

## Comparación de resultados y costes

| Par | Moneda | Cierres antes de costes | Costes de cierres | Cierres después de costes | Costes incurridos totales | Resultado tras costes incurridos* |
|---|---|---:|---:|---:|---:|---:|
| EUR/USD | USD | 29.063082 | 14.053751 | 15.009331 | 14.053751 | 15.009331 |
| GBP/USD | USD | -8.214327 | 13.940866 | -22.155194 | 13.940866 | -22.155194 |
| USD/JPY | JPY | 42.842915 | 13.401913 | 29.441001 | 13.401913 | 29.441001 |
| USD/CHF | CHF | -55.395309 | 13.397810 | -68.793119 | 13.490837 | -68.886147 |

* Cierres netos menos el coste de entrada de la posición abierta, si existe.
No incluye su variación de precio ni supone que se haya vendido. No es el patrimonio total.

## Capital y drawdown (incluyen posiciones abiertas)

| Par | Moneda | Capital inicial | Capital final | Drawdown máximo | Drawdown máximo % | Entradas rechazadas |
|---|---|---:|---:|---:|---:|---:|
| EUR/USD | USD | 1000.000000 | 1015.009331 | 25.951819 | 2.508037 | 0 |
| GBP/USD | USD | 1000.000000 | 977.844806 | 48.373737 | 4.729938 | 0 |
| USD/JPY | JPY | 1000.000000 | 1029.441001 | 37.046236 | 3.674652 | 0 |
| USD/CHF | CHF | 1000.000000 | 930.922718 | 78.889850 | 7.825079 | 0 |

Drawdowns positivos medidos en cada observación, incluyendo el capital inicial como máximo de partida.
Los máximos absoluto y porcentual pueden corresponder a fechas distintas. No se miden caídas intradiarias.
La exposición depende del modo de tamaño configurado; asignar el mismo porcentaje no iguala el riesgo.
Un drawdown pequeño no demuestra que la estrategia sea segura con otro tamaño de posición.

## Evolución del capital (resumen anual de la curva diaria)

Última observación disponible de cada año; año final posiblemente incompleto.
La curva diaria completa queda en BacktestResult.equity_curve; el drawdown usa todos sus puntos.

| Par | Fecha | Efectivo | Valor posición | Capital | Moneda |
|---|---|---:|---:|---:|---|
| EUR/USD | 1999-12-30 | 992.609451 | 0.000000 | 992.609451 | USD |
| EUR/USD | 2000-12-29 | 887.537627 | 103.057739 | 990.595366 | USD |
| EUR/USD | 2001-12-28 | 993.760557 | 0.000000 | 993.760557 | USD |
| EUR/USD | 2002-12-31 | 903.962542 | 107.264524 | 1011.227066 | USD |
| EUR/USD | 2003-12-31 | 913.842715 | 109.771639 | 1023.614354 | USD |
| EUR/USD | 2004-12-31 | 917.695793 | 111.777500 | 1029.473293 | USD |
| EUR/USD | 2005-12-30 | 1017.044516 | 0.000000 | 1017.044516 | USD |
| EUR/USD | 2006-12-29 | 918.411829 | 104.857860 | 1023.269690 | USD |
| EUR/USD | 2007-12-31 | 918.782394 | 108.187679 | 1026.970073 | USD |
| EUR/USD | 2008-12-31 | 924.756221 | 102.200087 | 1026.956308 | USD |
| EUR/USD | 2009-12-31 | 1026.957638 | 0.000000 | 1026.957638 | USD |
| EUR/USD | 2010-12-31 | 1024.912557 | 0.000000 | 1024.912557 | USD |
| EUR/USD | 2011-12-30 | 1023.918093 | 0.000000 | 1023.918093 | USD |
| EUR/USD | 2012-12-31 | 923.528413 | 103.428930 | 1026.957342 | USD |
| EUR/USD | 2013-12-31 | 921.895518 | 102.449364 | 1024.344882 | USD |
| EUR/USD | 2014-12-31 | 1021.278623 | 0.000000 | 1021.278623 | USD |
| EUR/USD | 2015-12-31 | 1013.143256 | 0.000000 | 1013.143256 | USD |
| EUR/USD | 2016-12-30 | 1012.768566 | 0.000000 | 1012.768566 | USD |
| EUR/USD | 2017-12-29 | 918.137450 | 103.431236 | 1021.568686 | USD |
| EUR/USD | 2018-12-31 | 1022.656411 | 0.000000 | 1022.656411 | USD |
| EUR/USD | 2019-12-31 | 915.886048 | 103.123001 | 1019.009049 | USD |
| EUR/USD | 2020-12-31 | 918.921172 | 105.463964 | 1024.385135 | USD |
| EUR/USD | 2021-12-31 | 1020.853101 | 0.000000 | 1020.853101 | USD |
| EUR/USD | 2022-12-30 | 914.033154 | 104.869532 | 1018.902686 | USD |
| EUR/USD | 2023-12-29 | 914.156594 | 103.132808 | 1017.289402 | USD |
| EUR/USD | 2024-12-31 | 1009.631362 | 0.000000 | 1009.631362 | USD |
| EUR/USD | 2025-12-31 | 918.588818 | 102.207018 | 1020.795836 | USD |
| EUR/USD | 2026-10-16 | 1015.009331 | 0.000000 | 1015.009331 | USD |
| GBP/USD | 1999-12-30 | 999.142083 | 0.000000 | 999.142083 | USD |
| GBP/USD | 2000-12-29 | 895.850330 | 100.155052 | 996.005382 | USD |
| GBP/USD | 2001-12-28 | 994.935463 | 0.000000 | 994.935463 | USD |
| GBP/USD | 2002-12-31 | 901.635759 | 104.372312 | 1006.008071 | USD |
| GBP/USD | 2003-12-31 | 903.684711 | 109.162603 | 1012.847314 | USD |
| GBP/USD | 2004-12-31 | 914.462039 | 107.103043 | 1021.565083 | USD |
| GBP/USD | 2005-12-30 | 1011.586173 | 0.000000 | 1011.586173 | USD |
| GBP/USD | 2006-12-29 | 911.024763 | 103.652655 | 1014.677418 | USD |
| GBP/USD | 2007-12-31 | 1012.159024 | 0.000000 | 1012.159024 | USD |
| GBP/USD | 2008-12-31 | 1005.714038 | 0.000000 | 1005.714038 | USD |
| GBP/USD | 2009-12-31 | 1013.334740 | 0.000000 | 1013.334740 | USD |
| GBP/USD | 2010-12-31 | 1012.760651 | 0.000000 | 1012.760651 | USD |
| GBP/USD | 2011-12-30 | 1006.713509 | 0.000000 | 1006.713509 | USD |
| GBP/USD | 2012-12-31 | 903.716471 | 100.028304 | 1003.744775 | USD |
| GBP/USD | 2013-12-31 | 896.703038 | 106.451263 | 1003.154302 | USD |
| GBP/USD | 2014-12-31 | 1004.104382 | 0.000000 | 1004.104382 | USD |
| GBP/USD | 2015-12-31 | 997.282701 | 0.000000 | 997.282701 | USD |
| GBP/USD | 2016-12-30 | 886.844305 | 95.366579 | 982.210884 | USD |
| GBP/USD | 2017-12-29 | 880.628646 | 98.732364 | 979.361010 | USD |
| GBP/USD | 2018-12-31 | 978.500318 | 0.000000 | 978.500318 | USD |
| GBP/USD | 2019-12-31 | 878.824477 | 103.194958 | 982.019435 | USD |
| GBP/USD | 2020-12-31 | 882.839388 | 101.100837 | 983.940225 | USD |
| GBP/USD | 2021-12-31 | 982.110628 | 0.000000 | 982.110628 | USD |
| GBP/USD | 2022-12-30 | 879.771915 | 99.595726 | 979.367641 | USD |
| GBP/USD | 2023-12-29 | 882.275166 | 99.035576 | 981.310742 | USD |
| GBP/USD | 2024-12-31 | 979.278019 | 0.000000 | 979.278019 | USD |
| GBP/USD | 2025-12-31 | 882.488682 | 98.657080 | 981.145762 | USD |
| GBP/USD | 2026-10-16 | 977.844806 | 0.000000 | 977.844806 | USD |
| USD/JPY | 1999-12-30 | 995.338677 | 0.000000 | 995.338677 | JPY |
| USD/JPY | 2000-12-29 | 891.497914 | 105.735068 | 997.232982 | JPY |
| USD/JPY | 2001-12-28 | 898.629425 | 106.317939 | 1004.947364 | JPY |
| USD/JPY | 2002-12-31 | 1002.684219 | 0.000000 | 1002.684219 | JPY |
| USD/JPY | 2003-12-31 | 998.172117 | 0.000000 | 998.172117 | JPY |
| USD/JPY | 2004-12-31 | 987.862924 | 0.000000 | 987.862924 | JPY |
| USD/JPY | 2005-12-30 | 892.931191 | 102.108509 | 995.039700 | JPY |
| USD/JPY | 2006-12-29 | 989.711985 | 0.000000 | 989.711985 | JPY |
| USD/JPY | 2007-12-31 | 985.165471 | 0.000000 | 985.165471 | JPY |
| USD/JPY | 2008-12-31 | 987.376959 | 0.000000 | 987.376959 | JPY |
| USD/JPY | 2009-12-31 | 887.618413 | 98.525742 | 986.144156 | JPY |
| USD/JPY | 2010-12-31 | 883.962139 | 94.580282 | 978.542421 | JPY |
| USD/JPY | 2011-12-30 | 876.244630 | 96.654752 | 972.899382 | JPY |
| USD/JPY | 2012-12-31 | 874.871152 | 104.732762 | 979.603914 | JPY |
| USD/JPY | 2013-12-31 | 889.757196 | 103.739958 | 993.497154 | JPY |
| USD/JPY | 2014-12-31 | 890.214350 | 115.538633 | 1005.752983 | JPY |
| USD/JPY | 2015-12-31 | 900.998333 | 97.820614 | 998.818948 | JPY |
| USD/JPY | 2016-12-30 | 897.834389 | 112.061127 | 1009.895516 | JPY |
| USD/JPY | 2017-12-29 | 1000.303993 | 0.000000 | 1000.303993 | JPY |
| USD/JPY | 2018-12-31 | 999.521583 | 0.000000 | 999.521583 | JPY |
| USD/JPY | 2019-12-31 | 897.528457 | 100.469487 | 997.997944 | JPY |
| USD/JPY | 2020-12-31 | 994.097325 | 0.000000 | 994.097325 | JPY |
| USD/JPY | 2021-12-31 | 900.841540 | 100.105248 | 1000.946788 | JPY |
| USD/JPY | 2022-12-30 | 1020.104381 | 0.000000 | 1020.104381 | JPY |
| USD/JPY | 2023-12-29 | 1022.762498 | 0.000000 | 1022.762498 | JPY |
| USD/JPY | 2024-12-31 | 922.891211 | 107.513735 | 1030.404947 | JPY |
| USD/JPY | 2025-12-31 | 926.996833 | 105.582007 | 1032.578840 | JPY |
| USD/JPY | 2026-10-16 | 1029.441001 | 0.000000 | 1029.441001 | JPY |
| USD/CHF | 1999-12-30 | 896.576866 | 102.008143 | 998.585009 | CHF |
| USD/CHF | 2000-12-29 | 1000.127707 | 0.000000 | 1000.127707 | CHF |
| USD/CHF | 2001-12-28 | 901.830722 | 101.625155 | 1003.455877 | CHF |
| USD/CHF | 2002-12-31 | 1001.655974 | 0.000000 | 1001.655974 | CHF |
| USD/CHF | 2003-12-31 | 991.601666 | 0.000000 | 991.601666 | CHF |
| USD/CHF | 2004-12-31 | 988.289065 | 0.000000 | 988.289065 | CHF |
| USD/CHF | 2005-12-30 | 891.934604 | 100.554672 | 992.489276 | CHF |
| USD/CHF | 2006-12-29 | 984.957799 | 0.000000 | 984.957799 | CHF |
| USD/CHF | 2007-12-31 | 980.812985 | 0.000000 | 980.812985 | CHF |
| USD/CHF | 2008-12-31 | 976.521884 | 0.000000 | 976.521884 | CHF |
| USD/CHF | 2009-12-31 | 876.817989 | 96.066576 | 972.884564 | CHF |
| USD/CHF | 2010-12-31 | 967.272883 | 0.000000 | 967.272883 | CHF |
| USD/CHF | 2011-12-30 | 870.545595 | 102.910620 | 973.456215 | CHF |
| USD/CHF | 2012-12-31 | 972.865872 | 0.000000 | 972.865872 | CHF |
| USD/CHF | 2013-12-31 | 964.176576 | 0.000000 | 964.176576 | CHF |
| USD/CHF | 2014-12-31 | 866.532407 | 106.784663 | 973.317071 | CHF |
| USD/CHF | 2015-12-31 | 856.820723 | 95.089804 | 951.910527 | CHF |
| USD/CHF | 2016-12-30 | 851.006073 | 97.242072 | 948.248145 | CHF |
| USD/CHF | 2017-12-29 | 849.732461 | 94.475470 | 944.207931 | CHF |
| USD/CHF | 2018-12-31 | 945.594126 | 0.000000 | 945.594126 | CHF |
| USD/CHF | 2019-12-31 | 940.047051 | 0.000000 | 940.047051 | CHF |
| USD/CHF | 2020-12-31 | 935.197765 | 0.000000 | 935.197765 | CHF |
| USD/CHF | 2021-12-31 | 934.079168 | 0.000000 | 934.079168 | CHF |
| USD/CHF | 2022-12-30 | 938.609599 | 0.000000 | 938.609599 | CHF |
| USD/CHF | 2023-12-29 | 934.013643 | 0.000000 | 934.013643 | CHF |
| USD/CHF | 2024-12-31 | 841.340695 | 97.532941 | 938.873636 | CHF |
| USD/CHF | 2025-12-31 | 931.636335 | 0.000000 | 931.636335 | CHF |
| USD/CHF | 2026-10-16 | 838.086193 | 92.836525 | 930.922718 | CHF |

## Posiciones abiertas (excluidas de las métricas de cierres)

- EUR/USD: ninguna.
- GBP/USD: ninguna.
- USD/JPY: ninguna.
- USD/CHF: 112.6714213072172343853174781 USD; señal 2026-09-17; entrada simulada 2026-09-18 a 0.825654 CHF por unidad base. Coste de entrada ya incurrido: 0.093028 CHF. Variación de precio latente: -0.191135 CHF, incluida en el capital final. El coste de entrada ya está descontado del efectivo; no se anticipa un coste de salida.

## Limitaciones

No sumar cuentas de monedas distintas ni comparar su exposición como si fueran equivalentes.
El coste proporcional es hipotético: faltan spreads, comisiones, slippage y swaps reales,
No se ajusta el precio simulado por liquidez; la valoración usa referencias informativas.
No se ha contrastado el calendario completo de publicación ni rellenado fechas ausentes.
Sin optimización ni validación fuera de muestra; estas métricas no demuestran viabilidad real.
No hay órdenes reales ni conexión con un bróker. Informe educativo, sin recomendación de inversión.

## Reproducción

Desde la raíz: `python -m trading_ai --report --cost-percent 0.100 --initial-capital 1000 --allocation-percent 10.0 --data RUTA_XML --output RUTA_MD`.
Usar la misma copia (SHA-256), código y reglas. El informe no incluye hora de ejecución
ni rutas locales, para obtener el mismo contenido al repetir el cálculo.
