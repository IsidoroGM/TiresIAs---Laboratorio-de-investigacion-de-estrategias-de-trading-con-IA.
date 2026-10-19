# Trading AI — Informe educativo EMA20/EMA60

Formato de informe: 6. Fuente: Banco Central Europeo (BCE).
[Histórico oficial](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml).
SHA-256 de la copia analizada: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

## Reglas y supuestos

- Referencias diarias informativas, no velas OHLC ni precios ejecutables.
- EUR/USD directo; GBP/USD = USD/GBP, USD/JPY = JPY/USD y USD/CHF = CHF/USD
  a partir de las referencias BCE de la misma fecha, todas expresadas por euro.
- Medias de 20 y 60 observaciones publicadas, no días naturales.
- EMA: semilla = SMA de las primeras n observaciones; alfa = 2/(n+1); EMA actual = EMA anterior + alfa × (precio actual - EMA anterior). El periodo n controla el suavizado; la memoria se extiende más allá de n observaciones.
- Primera señal posible desde la observación 61; requiere medias actuales y anteriores.
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
| EUR/USD | 1999-01-04 | 2026-10-16 | 7116 | 61 | 20 | 41 | 0 | No |
| GBP/USD | 1999-01-04 | 2026-10-16 | 7116 | 56 | 19 | 37 | 0 | No |
| USD/JPY | 1999-01-04 | 2026-10-16 | 7116 | 62 | 17 | 45 | 0 | No |
| USD/CHF | 1999-01-04 | 2026-10-16 | 7116 | 59 | 15 | 44 | 0 | Sí |

## Tamaño de las entradas ejecutadas

Incluye las operaciones cerradas y la posición abierta; cantidades en moneda base.

| Par | Moneda base | Cantidad mínima | Cantidad máxima |
|---|---|---:|---:|
| EUR/USD | EUR | 72.158371 | 112.494393 |
| GBP/USD | GBP | 49.327024 | 84.082499 |
| USD/JPY | USD | 0.656352 | 1.242912 |
| USD/CHF | USD | 58.528324 | 119.963094 |

## Métricas de cierres — después de costes

| Par | Moneda | % ganadoras | Resultado | Media/cierre | Ganancias | Pérdidas (magnitud) | Profit factor |
|---|---|---:|---:|---:|---:|---:|---:|
| EUR/USD | USD | 32.79 | 13.740017 | 0.225246 | 104.901690 | 91.161673 | 1.1507 |
| GBP/USD | USD | 33.93 | -1.102126 | -0.019681 | 77.009830 | 78.111956 | 0.9859 |
| USD/JPY | JPY | 27.42 | 26.320534 | 0.424525 | 114.920596 | 88.600062 | 1.2971 |
| USD/CHF | CHF | 25.42 | -54.191176 | -0.918495 | 27.683518 | 81.874694 | 0.3381 |

N/D: porcentaje y media no disponibles sin cierres; profit factor no disponible
sin pérdidas. Cierres a cero incluidos en el denominador del porcentaje ganador.
Profit factor = ganancias / magnitud de pérdidas, ambas netas de costes de cierres.
Importes en moneda cotizada. Ganadoras y perdedoras se clasifican después de costes.

## Comparación de resultados y costes

| Par | Moneda | Cierres antes de costes | Costes de cierres | Cierres después de costes | Costes incurridos totales | Resultado tras costes incurridos* |
|---|---|---:|---:|---:|---:|---:|
| EUR/USD | USD | 26.198447 | 12.458430 | 13.740017 | 12.458430 | 13.740017 |
| GBP/USD | USD | 10.086412 | 11.188538 | -1.102126 | 11.188538 | -1.102126 |
| USD/JPY | JPY | 38.645505 | 12.324971 | 26.320534 | 12.324971 | 26.320534 |
| USD/CHF | CHF | -42.765023 | 11.426153 | -54.191176 | 11.520639 | -54.285662 |

* Cierres netos menos el coste de entrada de la posición abierta, si existe.
No incluye su variación de precio ni supone que se haya vendido. No es el patrimonio total.

## Capital y drawdown (incluyen posiciones abiertas)

| Par | Moneda | Capital inicial | Capital final | Drawdown máximo | Drawdown máximo % | Entradas rechazadas |
|---|---|---:|---:|---:|---:|---:|
| EUR/USD | USD | 1000.000000 | 1013.740017 | 37.973408 | 3.627450 | 0 |
| GBP/USD | USD | 1000.000000 | 998.897874 | 29.423021 | 2.899616 | 0 |
| USD/JPY | JPY | 1000.000000 | 1026.320534 | 51.478619 | 5.073104 | 0 |
| USD/CHF | CHF | 1000.000000 | 950.072500 | 62.913935 | 6.237574 | 0 |

Drawdowns positivos medidos en cada observación, incluyendo el capital inicial como máximo de partida.
Los máximos absoluto y porcentual pueden corresponder a fechas distintas. No se miden caídas intradiarias.
La exposición depende del modo de tamaño configurado; asignar el mismo porcentaje no iguala el riesgo.
Un drawdown pequeño no demuestra que la estrategia sea segura con otro tamaño de posición.

## Evolución del capital (resumen anual de la curva diaria)

Última observación disponible de cada año; año final posiblemente incompleto.
La curva diaria completa queda en BacktestResult.equity_curve; el drawdown usa todos sus puntos.

| Par | Fecha | Efectivo | Valor posición | Capital | Moneda |
|---|---|---:|---:|---:|---|
| EUR/USD | 1999-12-30 | 993.351370 | 0.000000 | 993.351370 | USD |
| EUR/USD | 2000-12-29 | 890.619424 | 104.484512 | 995.103936 | USD |
| EUR/USD | 2001-12-28 | 991.278434 | 0.000000 | 991.278434 | USD |
| EUR/USD | 2002-12-31 | 892.150590 | 117.972870 | 1010.123461 | USD |
| EUR/USD | 2003-12-31 | 915.645197 | 111.691617 | 1027.336814 | USD |
| EUR/USD | 2004-12-31 | 918.024659 | 113.351681 | 1031.376340 | USD |
| EUR/USD | 2005-12-30 | 1019.905967 | 0.000000 | 1019.905967 | USD |
| EUR/USD | 2006-12-29 | 920.335285 | 105.143161 | 1025.478446 | USD |
| EUR/USD | 2007-12-31 | 921.773629 | 115.135927 | 1036.909555 | USD |
| EUR/USD | 2008-12-31 | 935.161302 | 103.350012 | 1038.511314 | USD |
| EUR/USD | 2009-12-31 | 1037.439147 | 0.000000 | 1037.439147 | USD |
| EUR/USD | 2010-12-31 | 1035.587870 | 0.000000 | 1035.587870 | USD |
| EUR/USD | 2011-12-30 | 1035.330312 | 0.000000 | 1035.330312 | USD |
| EUR/USD | 2012-12-31 | 926.949690 | 107.930569 | 1034.880259 | USD |
| EUR/USD | 2013-12-31 | 926.689460 | 107.094864 | 1033.784324 | USD |
| EUR/USD | 2014-12-31 | 1031.254176 | 0.000000 | 1031.254176 | USD |
| EUR/USD | 2015-12-31 | 1020.919240 | 0.000000 | 1020.919240 | USD |
| EUR/USD | 2016-12-30 | 1014.706397 | 0.000000 | 1014.706397 | USD |
| EUR/USD | 2017-12-29 | 919.624463 | 103.075394 | 1022.699857 | USD |
| EUR/USD | 2018-12-31 | 1020.527980 | 0.000000 | 1020.527980 | USD |
| EUR/USD | 2019-12-31 | 915.135804 | 102.125622 | 1017.261426 | USD |
| EUR/USD | 2020-12-31 | 908.497681 | 111.321399 | 1019.819080 | USD |
| EUR/USD | 2021-12-31 | 1015.088038 | 0.000000 | 1015.088038 | USD |
| EUR/USD | 2022-12-30 | 913.579234 | 103.961101 | 1017.540335 | USD |
| EUR/USD | 2023-12-29 | 914.964205 | 102.694955 | 1017.659160 | USD |
| EUR/USD | 2024-12-31 | 1011.421478 | 0.000000 | 1011.421478 | USD |
| EUR/USD | 2025-12-31 | 916.963924 | 102.095902 | 1019.059825 | USD |
| EUR/USD | 2026-10-16 | 1013.740017 | 0.000000 | 1013.740017 | USD |
| GBP/USD | 1999-12-30 | 1000.166884 | 0.000000 | 1000.166884 | USD |
| GBP/USD | 2000-12-29 | 897.521034 | 101.303776 | 998.824810 | USD |
| GBP/USD | 2001-12-28 | 893.640621 | 99.194208 | 992.834830 | USD |
| GBP/USD | 2002-12-31 | 892.203578 | 111.276956 | 1003.480534 | USD |
| GBP/USD | 2003-12-31 | 899.881985 | 107.985524 | 1007.867508 | USD |
| GBP/USD | 2004-12-31 | 905.180107 | 105.610983 | 1010.791090 | USD |
| GBP/USD | 2005-12-30 | 997.627195 | 0.000000 | 997.627195 | USD |
| GBP/USD | 2006-12-29 | 900.215898 | 103.621865 | 1003.837764 | USD |
| GBP/USD | 2007-12-31 | 1004.355468 | 0.000000 | 1004.355468 | USD |
| GBP/USD | 2008-12-31 | 998.091300 | 0.000000 | 998.091300 | USD |
| GBP/USD | 2009-12-31 | 1003.153377 | 0.000000 | 1003.153377 | USD |
| GBP/USD | 2010-12-31 | 1007.433459 | 0.000000 | 1007.433459 | USD |
| GBP/USD | 2011-12-30 | 1003.074708 | 0.000000 | 1003.074708 | USD |
| GBP/USD | 2012-12-31 | 902.367305 | 100.473221 | 1002.840526 | USD |
| GBP/USD | 2013-12-31 | 895.488810 | 105.905947 | 1001.394757 | USD |
| GBP/USD | 2014-12-31 | 1002.791551 | 0.000000 | 1002.791551 | USD |
| GBP/USD | 2015-12-31 | 1001.326596 | 0.000000 | 1001.326596 | USD |
| GBP/USD | 2016-12-30 | 987.465677 | 0.000000 | 987.465677 | USD |
| GBP/USD | 2017-12-29 | 887.305056 | 106.859102 | 994.164158 | USD |
| GBP/USD | 2018-12-31 | 991.064665 | 0.000000 | 991.064665 | USD |
| GBP/USD | 2019-12-31 | 890.351643 | 102.454389 | 992.806032 | USD |
| GBP/USD | 2020-12-31 | 888.341752 | 106.388364 | 994.730117 | USD |
| GBP/USD | 2021-12-31 | 995.901908 | 0.000000 | 995.901908 | USD |
| GBP/USD | 2022-12-30 | 893.584975 | 101.115526 | 994.700501 | USD |
| GBP/USD | 2023-12-29 | 898.040202 | 100.805205 | 998.845407 | USD |
| GBP/USD | 2024-12-31 | 998.323148 | 0.000000 | 998.323148 | USD |
| GBP/USD | 2025-12-31 | 901.600572 | 100.995099 | 1002.595670 | USD |
| GBP/USD | 2026-10-16 | 998.897874 | 0.000000 | 998.897874 | USD |
| USD/JPY | 1999-12-30 | 1000.000000 | 0.000000 | 1000.000000 | JPY |
| USD/JPY | 2000-12-29 | 895.706822 | 105.225629 | 1000.932452 | JPY |
| USD/JPY | 2001-12-28 | 904.494474 | 107.011840 | 1011.506314 | JPY |
| USD/JPY | 2002-12-31 | 1003.692535 | 0.000000 | 1003.692535 | JPY |
| USD/JPY | 2003-12-31 | 997.288666 | 0.000000 | 997.288666 | JPY |
| USD/JPY | 2004-12-31 | 987.961639 | 0.000000 | 987.961639 | JPY |
| USD/JPY | 2005-12-30 | 889.970718 | 108.699702 | 998.670420 | JPY |
| USD/JPY | 2006-12-29 | 892.643383 | 99.674583 | 992.317966 | JPY |
| USD/JPY | 2007-12-31 | 989.016582 | 0.000000 | 989.016582 | JPY |
| USD/JPY | 2008-12-31 | 987.960471 | 0.000000 | 987.960471 | JPY |
| USD/JPY | 2009-12-31 | 883.123150 | 98.161162 | 981.284312 | JPY |
| USD/JPY | 2010-12-31 | 971.821818 | 0.000000 | 971.821818 | JPY |
| USD/JPY | 2011-12-30 | 867.885531 | 96.251458 | 964.136989 | JPY |
| USD/JPY | 2012-12-31 | 868.379855 | 103.948664 | 972.328519 | JPY |
| USD/JPY | 2013-12-31 | 882.779260 | 103.506258 | 986.285518 | JPY |
| USD/JPY | 2014-12-31 | 882.506185 | 114.199255 | 996.705440 | JPY |
| USD/JPY | 2015-12-31 | 994.707090 | 0.000000 | 994.707090 | JPY |
| USD/JPY | 2016-12-30 | 895.236381 | 111.814619 | 1007.051000 | JPY |
| USD/JPY | 2017-12-29 | 897.017332 | 100.097817 | 997.115149 | JPY |
| USD/JPY | 2018-12-31 | 996.049925 | 0.000000 | 996.049925 | JPY |
| USD/JPY | 2019-12-31 | 893.139818 | 99.418039 | 992.557858 | JPY |
| USD/JPY | 2020-12-31 | 987.269536 | 0.000000 | 987.269536 | JPY |
| USD/JPY | 2021-12-31 | 891.821716 | 102.748053 | 994.569768 | JPY |
| USD/JPY | 2022-12-30 | 1015.044096 | 0.000000 | 1015.044096 | JPY |
| USD/JPY | 2023-12-29 | 1019.761998 | 0.000000 | 1019.761998 | JPY |
| USD/JPY | 2024-12-31 | 919.063808 | 106.154105 | 1025.217913 | JPY |
| USD/JPY | 2025-12-31 | 919.286100 | 108.058943 | 1027.345044 | JPY |
| USD/JPY | 2026-10-16 | 1026.320534 | 0.000000 | 1026.320534 | JPY |
| USD/CHF | 1999-12-30 | 896.253249 | 102.725742 | 998.978991 | CHF |
| USD/CHF | 2000-12-29 | 999.963951 | 0.000000 | 999.963951 | CHF |
| USD/CHF | 2001-12-28 | 999.900613 | 0.000000 | 999.900613 | CHF |
| USD/CHF | 2002-12-31 | 1000.822855 | 0.000000 | 1000.822855 | CHF |
| USD/CHF | 2003-12-31 | 995.145915 | 0.000000 | 995.145915 | CHF |
| USD/CHF | 2004-12-31 | 987.271863 | 0.000000 | 987.271863 | CHF |
| USD/CHF | 2005-12-30 | 888.957159 | 102.357820 | 991.314979 | CHF |
| USD/CHF | 2006-12-29 | 986.054555 | 0.000000 | 986.054555 | CHF |
| USD/CHF | 2007-12-31 | 982.107492 | 0.000000 | 982.107492 | CHF |
| USD/CHF | 2008-12-31 | 979.624081 | 0.000000 | 979.624081 | CHF |
| USD/CHF | 2009-12-31 | 876.609857 | 95.474252 | 972.084109 | CHF |
| USD/CHF | 2010-12-31 | 975.092529 | 0.000000 | 975.092529 | CHF |
| USD/CHF | 2011-12-30 | 877.583276 | 103.671176 | 981.254452 | CHF |
| USD/CHF | 2012-12-31 | 980.358890 | 0.000000 | 980.358890 | CHF |
| USD/CHF | 2013-12-31 | 974.752120 | 0.000000 | 974.752120 | CHF |
| USD/CHF | 2014-12-31 | 877.276908 | 107.911100 | 985.188008 | CHF |
| USD/CHF | 2015-12-31 | 869.475438 | 97.648802 | 967.124240 | CHF |
| USD/CHF | 2016-12-30 | 863.123509 | 99.387560 | 962.511068 | CHF |
| USD/CHF | 2017-12-29 | 861.937998 | 96.197451 | 958.135450 | CHF |
| USD/CHF | 2018-12-31 | 959.129710 | 0.000000 | 959.129710 | CHF |
| USD/CHF | 2019-12-31 | 957.506703 | 0.000000 | 957.506703 | CHF |
| USD/CHF | 2020-12-31 | 956.185845 | 0.000000 | 956.185845 | CHF |
| USD/CHF | 2021-12-31 | 951.640772 | 0.000000 | 951.640772 | CHF |
| USD/CHF | 2022-12-30 | 951.312440 | 0.000000 | 951.312440 | CHF |
| USD/CHF | 2023-12-29 | 950.112679 | 0.000000 | 950.112679 | CHF |
| USD/CHF | 2024-12-31 | 856.009399 | 99.113388 | 955.122787 | CHF |
| USD/CHF | 2025-12-31 | 947.741588 | 0.000000 | 947.741588 | CHF |
| USD/CHF | 2026-10-16 | 851.227942 | 98.844558 | 950.072500 | CHF |

## Posiciones abiertas (excluidas de las métricas de cierres)

- EUR/USD: ninguna.
- GBP/USD: ninguna.
- USD/JPY: ninguna.
- USD/CHF: 119.9630944653871308897097959 USD; señal 2026-06-03; entrada simulada 2026-06-04 a 0.787629 CHF por unidad base. Coste de entrada ya incurrido: 0.094486 CHF. Variación de precio latente: 4.358162 CHF, incluida en el capital final. El coste de entrada ya está descontado del efectivo; no se anticipa un coste de salida.

## Limitaciones

No sumar cuentas de monedas distintas ni comparar su exposición como si fueran equivalentes.
El coste proporcional es hipotético: faltan spreads, comisiones, slippage y swaps reales,
No se ajusta el precio simulado por liquidez; la valoración usa referencias informativas.
No se ha contrastado el calendario completo de publicación ni rellenado fechas ausentes.
Sin optimización ni validación fuera de muestra; estas métricas no demuestran viabilidad real.
No hay órdenes reales ni conexión con un bróker. Informe educativo, sin recomendación de inversión.

## Reproducción

Desde la raíz: `python -m trading_ai --report --strategy ema --fast-window 20 --slow-window 60 --cost-percent 0.100 --initial-capital 1000 --allocation-percent 10.0 --data RUTA_XML --output RUTA_MD`.
Usar la misma copia (SHA-256), código y reglas. El informe no incluye hora de ejecución
ni rutas locales, para obtener el mismo contenido al repetir el cálculo.
