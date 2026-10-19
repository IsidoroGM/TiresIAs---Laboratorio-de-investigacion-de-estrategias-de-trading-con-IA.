# Trading AI — Informe educativo SMA10/SMA40

Formato de informe: 5. Fuente: Banco Central Europeo (BCE).
[Histórico oficial](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml).
SHA-256 de la copia analizada: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

## Reglas y supuestos

- Referencias diarias informativas, no velas OHLC ni precios ejecutables.
- EUR/USD directo; GBP/USD = USD/GBP, USD/JPY = JPY/USD y USD/CHF = CHF/USD
  a partir de las referencias BCE de la misma fecha, todas expresadas por euro.
- Medias de 10 y 40 observaciones publicadas, no días naturales.
- Primera señal posible desde la observación 41; requiere medias actuales y anteriores.
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
| EUR/USD | 1999-01-04 | 2026-10-16 | 7116 | 105 | 34 | 71 | 0 | No |
| GBP/USD | 1999-01-04 | 2026-10-16 | 7116 | 109 | 37 | 72 | 0 | No |
| USD/JPY | 1999-01-04 | 2026-10-16 | 7116 | 126 | 41 | 85 | 0 | Sí |
| USD/CHF | 1999-01-04 | 2026-10-16 | 7116 | 122 | 37 | 85 | 0 | Sí |

## Tamaño de las entradas ejecutadas

Incluye las operaciones cerradas y la posición abierta; cantidades en moneda base.

| Par | Moneda base | Cantidad mínima | Cantidad máxima |
|---|---|---:|---:|
| EUR/USD | EUR | 64.652685 | 115.000037 |
| GBP/USD | GBP | 48.911409 | 84.750834 |
| USD/JPY | USD | 0.614683 | 1.237929 |
| USD/CHF | USD | 56.416414 | 121.264544 |

## Métricas de cierres — después de costes

| Par | Moneda | % ganadoras | Resultado | Media/cierre | Ganancias | Pérdidas (magnitud) | Profit factor |
|---|---|---:|---:|---:|---:|---:|---:|
| EUR/USD | USD | 32.38 | 5.717657 | 0.054454 | 118.508150 | 112.790493 | 1.0507 |
| GBP/USD | USD | 33.94 | -11.904348 | -0.109214 | 98.353983 | 110.258330 | 0.8920 |
| USD/JPY | JPY | 32.54 | -20.249963 | -0.160714 | 121.874622 | 142.124585 | 0.8575 |
| USD/CHF | CHF | 30.33 | -65.722128 | -0.538706 | 75.204798 | 140.926925 | 0.5336 |

N/D: porcentaje y media no disponibles sin cierres; profit factor no disponible
sin pérdidas. Cierres a cero incluidos en el denominador del porcentaje ganador.
Profit factor = ganancias / magnitud de pérdidas, ambas netas de costes de cierres.
Importes en moneda cotizada. Ganadoras y perdedoras se clasifican después de costes.

## Comparación de resultados y costes

| Par | Moneda | Cierres antes de costes | Costes de cierres | Cierres después de costes | Costes incurridos totales | Resultado tras costes incurridos* |
|---|---|---:|---:|---:|---:|---:|
| EUR/USD | USD | 26.844956 | 21.127299 | 5.717657 | 21.127299 | 5.717657 |
| GBP/USD | USD | 9.708580 | 21.612928 | -11.904348 | 21.612928 | -11.904348 |
| USD/JPY | JPY | 4.294109 | 24.544072 | -20.249963 | 24.641950 | -20.347840 |
| USD/CHF | CHF | -42.249615 | 23.472513 | -65.722128 | 23.565847 | -65.815462 |

* Cierres netos menos el coste de entrada de la posición abierta, si existe.
No incluye su variación de precio ni supone que se haya vendido. No es el patrimonio total.

## Capital y drawdown (incluyen posiciones abiertas)

| Par | Moneda | Capital inicial | Capital final | Drawdown máximo | Drawdown máximo % | Entradas rechazadas |
|---|---|---:|---:|---:|---:|---:|
| EUR/USD | USD | 1000.000000 | 1005.717657 | 36.540558 | 3.554368 | 0 |
| GBP/USD | USD | 1000.000000 | 988.095652 | 39.993062 | 3.934387 | 0 |
| USD/JPY | JPY | 1000.000000 | 979.609763 | 51.764715 | 5.151225 | 0 |
| USD/CHF | CHF | 1000.000000 | 935.040981 | 74.952628 | 7.475242 | 0 |

Drawdowns positivos medidos en cada observación, incluyendo el capital inicial como máximo de partida.
Los máximos absoluto y porcentual pueden corresponder a fechas distintas. No se miden caídas intradiarias.
La exposición depende del modo de tamaño configurado; asignar el mismo porcentaje no iguala el riesgo.
Un drawdown pequeño no demuestra que la estrategia sea segura con otro tamaño de posición.

## Evolución del capital (resumen anual de la curva diaria)

Última observación disponible de cada año; año final posiblemente incompleto.
La curva diaria completa queda en BacktestResult.equity_curve; el drawdown usa todos sus puntos.

| Par | Fecha | Efectivo | Valor posición | Capital | Moneda |
|---|---|---:|---:|---:|---|
| EUR/USD | 1999-12-30 | 994.731370 | 0.000000 | 994.731370 | USD |
| EUR/USD | 2000-12-29 | 889.281351 | 104.256482 | 993.537833 | USD |
| EUR/USD | 2001-12-28 | 891.446496 | 96.722734 | 988.169229 | USD |
| EUR/USD | 2002-12-31 | 897.401055 | 105.050988 | 1002.452043 | USD |
| EUR/USD | 2003-12-31 | 907.986349 | 106.978282 | 1014.964631 | USD |
| EUR/USD | 2004-12-31 | 906.928000 | 112.782853 | 1019.710853 | USD |
| EUR/USD | 2005-12-30 | 911.188083 | 99.621935 | 1010.810019 | USD |
| EUR/USD | 2006-12-29 | 912.027650 | 104.488025 | 1016.515674 | USD |
| EUR/USD | 2007-12-31 | 1018.819990 | 0.000000 | 1018.819990 | USD |
| EUR/USD | 2008-12-31 | 916.337749 | 104.777799 | 1021.115548 | USD |
| EUR/USD | 2009-12-31 | 1015.915482 | 0.000000 | 1015.915482 | USD |
| EUR/USD | 2010-12-31 | 1018.320901 | 0.000000 | 1018.320901 | USD |
| EUR/USD | 2011-12-30 | 1012.809557 | 0.000000 | 1012.809557 | USD |
| EUR/USD | 2012-12-31 | 912.564659 | 102.083968 | 1014.648627 | USD |
| EUR/USD | 2013-12-31 | 907.453067 | 101.233891 | 1008.686958 | USD |
| EUR/USD | 2014-12-31 | 1005.162242 | 0.000000 | 1005.162242 | USD |
| EUR/USD | 2015-12-31 | 900.577931 | 99.543656 | 1000.121587 | USD |
| EUR/USD | 2016-12-30 | 996.842467 | 0.000000 | 996.842467 | USD |
| EUR/USD | 2017-12-29 | 901.458402 | 101.286577 | 1002.744979 | USD |
| EUR/USD | 2018-12-31 | 902.891275 | 100.537131 | 1003.428406 | USD |
| EUR/USD | 2019-12-31 | 899.751111 | 100.660987 | 1000.412098 | USD |
| EUR/USD | 2020-12-31 | 898.683925 | 103.814903 | 1002.498829 | USD |
| EUR/USD | 2021-12-31 | 999.030007 | 0.000000 | 999.030007 | USD |
| EUR/USD | 2022-12-30 | 893.894974 | 106.748695 | 1000.643668 | USD |
| EUR/USD | 2023-12-29 | 901.160799 | 103.436261 | 1004.597060 | USD |
| EUR/USD | 2024-12-31 | 1001.293469 | 0.000000 | 1001.293469 | USD |
| EUR/USD | 2025-12-31 | 910.132541 | 101.935728 | 1012.068269 | USD |
| EUR/USD | 2026-10-16 | 1005.717657 | 0.000000 | 1005.717657 | USD |
| GBP/USD | 1999-12-30 | 995.477560 | 0.000000 | 995.477560 | USD |
| GBP/USD | 2000-12-29 | 888.977462 | 101.587932 | 990.565393 | USD |
| GBP/USD | 2001-12-28 | 885.083895 | 98.159228 | 983.243123 | USD |
| GBP/USD | 2002-12-31 | 888.023406 | 100.203139 | 988.226545 | USD |
| GBP/USD | 2003-12-31 | 890.765143 | 107.657562 | 998.422704 | USD |
| GBP/USD | 2004-12-31 | 898.225265 | 105.438936 | 1003.664200 | USD |
| GBP/USD | 2005-12-30 | 894.306617 | 96.372212 | 990.678829 | USD |
| GBP/USD | 2006-12-29 | 898.492857 | 102.994088 | 1001.486945 | USD |
| GBP/USD | 2007-12-31 | 998.681614 | 0.000000 | 998.681614 | USD |
| GBP/USD | 2008-12-31 | 996.751466 | 0.000000 | 996.751466 | USD |
| GBP/USD | 2009-12-31 | 1009.630450 | 0.000000 | 1009.630450 | USD |
| GBP/USD | 2010-12-31 | 1006.420810 | 0.000000 | 1006.420810 | USD |
| GBP/USD | 2011-12-30 | 999.507367 | 0.000000 | 999.507367 | USD |
| GBP/USD | 2012-12-31 | 901.390959 | 100.400509 | 1001.791468 | USD |
| GBP/USD | 2013-12-31 | 898.216704 | 102.057948 | 1000.274652 | USD |
| GBP/USD | 2014-12-31 | 997.383940 | 0.000000 | 997.383940 | USD |
| GBP/USD | 2015-12-31 | 988.465357 | 0.000000 | 988.465357 | USD |
| GBP/USD | 2016-12-30 | 981.409752 | 0.000000 | 981.409752 | USD |
| GBP/USD | 2017-12-29 | 881.190740 | 99.209526 | 980.400266 | USD |
| GBP/USD | 2018-12-31 | 976.816980 | 0.000000 | 976.816980 | USD |
| GBP/USD | 2019-12-31 | 882.690459 | 103.186449 | 985.876907 | USD |
| GBP/USD | 2020-12-31 | 886.205683 | 102.686438 | 988.892121 | USD |
| GBP/USD | 2021-12-31 | 885.673845 | 98.309895 | 983.983740 | USD |
| GBP/USD | 2022-12-30 | 882.232943 | 101.919248 | 984.152191 | USD |
| GBP/USD | 2023-12-29 | 883.038013 | 102.002875 | 985.040888 | USD |
| GBP/USD | 2024-12-31 | 981.125089 | 0.000000 | 981.125089 | USD |
| GBP/USD | 2025-12-31 | 889.325039 | 99.747906 | 989.072944 | USD |
| GBP/USD | 2026-10-16 | 988.095652 | 0.000000 | 988.095652 | USD |
| USD/JPY | 1999-12-30 | 991.546236 | 0.000000 | 991.546236 | JPY |
| USD/JPY | 2000-12-29 | 887.659991 | 103.213094 | 990.873084 | JPY |
| USD/JPY | 2001-12-28 | 893.745092 | 107.899262 | 1001.644353 | JPY |
| USD/JPY | 2002-12-31 | 993.081500 | 0.000000 | 993.081500 | JPY |
| USD/JPY | 2003-12-31 | 985.155954 | 0.000000 | 985.155954 | JPY |
| USD/JPY | 2004-12-31 | 977.660684 | 0.000000 | 977.660684 | JPY |
| USD/JPY | 2005-12-30 | 980.411368 | 0.000000 | 980.411368 | JPY |
| USD/JPY | 2006-12-29 | 879.134510 | 98.319948 | 977.454458 | JPY |
| USD/JPY | 2007-12-31 | 880.544591 | 96.914046 | 977.458637 | JPY |
| USD/JPY | 2008-12-31 | 971.867672 | 0.000000 | 971.867672 | JPY |
| USD/JPY | 2009-12-31 | 872.342720 | 97.575765 | 969.918485 | JPY |
| USD/JPY | 2010-12-31 | 965.643589 | 0.000000 | 965.643589 | JPY |
| USD/JPY | 2011-12-30 | 859.139625 | 94.863410 | 954.003036 | JPY |
| USD/JPY | 2012-12-31 | 858.199472 | 103.954896 | 962.154368 | JPY |
| USD/JPY | 2013-12-31 | 872.006776 | 103.679892 | 975.686668 | JPY |
| USD/JPY | 2014-12-31 | 877.997315 | 102.427404 | 980.424719 | JPY |
| USD/JPY | 2015-12-31 | 976.174292 | 0.000000 | 976.174292 | JPY |
| USD/JPY | 2016-12-30 | 869.782930 | 109.310948 | 979.093878 | JPY |
| USD/JPY | 2017-12-29 | 871.321733 | 95.934615 | 967.256349 | JPY |
| USD/JPY | 2018-12-31 | 968.861644 | 0.000000 | 968.861644 | JPY |
| USD/JPY | 2019-12-31 | 869.615103 | 95.606800 | 965.221903 | JPY |
| USD/JPY | 2020-12-31 | 957.634749 | 0.000000 | 957.634749 | JPY |
| USD/JPY | 2021-12-31 | 865.939374 | 96.436954 | 962.376328 | JPY |
| USD/JPY | 2022-12-30 | 972.474372 | 0.000000 | 972.474372 | JPY |
| USD/JPY | 2023-12-29 | 976.964559 | 0.000000 | 976.964559 | JPY |
| USD/JPY | 2024-12-31 | 881.968149 | 97.756402 | 979.724551 | JPY |
| USD/JPY | 2025-12-31 | 879.912266 | 102.872006 | 982.784272 | JPY |
| USD/JPY | 2026-10-16 | 881.775033 | 97.834730 | 979.609763 | JPY |
| USD/CHF | 1999-12-30 | 896.478042 | 103.632600 | 1000.110642 | CHF |
| USD/CHF | 2000-12-29 | 995.985293 | 0.000000 | 995.985293 | CHF |
| USD/CHF | 2001-12-28 | 995.258440 | 0.000000 | 995.258440 | CHF |
| USD/CHF | 2002-12-31 | 991.609507 | 0.000000 | 991.609507 | CHF |
| USD/CHF | 2003-12-31 | 986.502402 | 0.000000 | 986.502402 | CHF |
| USD/CHF | 2004-12-31 | 981.914610 | 0.000000 | 981.914610 | CHF |
| USD/CHF | 2005-12-30 | 986.547582 | 0.000000 | 986.547582 | CHF |
| USD/CHF | 2006-12-29 | 985.110776 | 0.000000 | 985.110776 | CHF |
| USD/CHF | 2007-12-31 | 883.197822 | 95.491592 | 978.689415 | CHF |
| USD/CHF | 2008-12-31 | 978.054799 | 0.000000 | 978.054799 | CHF |
| USD/CHF | 2009-12-31 | 875.276012 | 96.205118 | 971.481130 | CHF |
| USD/CHF | 2010-12-31 | 974.491595 | 0.000000 | 974.491595 | CHF |
| USD/CHF | 2011-12-30 | 880.756988 | 99.952404 | 980.709392 | CHF |
| USD/CHF | 2012-12-31 | 979.982522 | 0.000000 | 979.982522 | CHF |
| USD/CHF | 2013-12-31 | 963.292346 | 0.000000 | 963.292346 | CHF |
| USD/CHF | 2014-12-31 | 864.675370 | 105.341886 | 970.017256 | CHF |
| USD/CHF | 2015-12-31 | 954.794448 | 0.000000 | 954.794448 | CHF |
| USD/CHF | 2016-12-30 | 854.872427 | 96.493271 | 951.365699 | CHF |
| USD/CHF | 2017-12-29 | 945.370753 | 0.000000 | 945.370753 | CHF |
| USD/CHF | 2018-12-31 | 947.612661 | 0.000000 | 947.612661 | CHF |
| USD/CHF | 2019-12-31 | 943.884507 | 0.000000 | 943.884507 | CHF |
| USD/CHF | 2020-12-31 | 939.445404 | 0.000000 | 939.445404 | CHF |
| USD/CHF | 2021-12-31 | 938.587562 | 0.000000 | 938.587562 | CHF |
| USD/CHF | 2022-12-30 | 930.514682 | 0.000000 | 930.514682 | CHF |
| USD/CHF | 2023-12-29 | 929.446360 | 0.000000 | 929.446360 | CHF |
| USD/CHF | 2024-12-31 | 838.485393 | 98.345564 | 936.830957 | CHF |
| USD/CHF | 2025-12-31 | 932.466035 | 0.000000 | 932.466035 | CHF |
| USD/CHF | 2026-10-16 | 840.850085 | 94.190896 | 935.040981 | CHF |

## Posiciones abiertas (excluidas de las métricas de cierres)

- EUR/USD: ninguna.
- GBP/USD: ninguna.
- USD/JPY: 0.6191284530549254278900907850 USD; señal 2026-10-05; entrada simulada 2026-10-06 a 158.088562 JPY por unidad base. Coste de entrada ya incurrido: 0.097877 JPY. Variación de precio latente: -0.042397 JPY, incluida en el capital final. El coste de entrada ya está descontado del efectivo; no se anticipa un coste de salida.
- USD/CHF: 114.3151589349296693813514920 USD; señal 2026-09-11; entrada simulada 2026-09-14 a 0.816466 CHF por unidad base. Coste de entrada ya incurrido: 0.093334 CHF. Variación de precio latente: 0.856443 CHF, incluida en el capital final. El coste de entrada ya está descontado del efectivo; no se anticipa un coste de salida.

## Limitaciones

No sumar cuentas de monedas distintas ni comparar su exposición como si fueran equivalentes.
El coste proporcional es hipotético: faltan spreads, comisiones, slippage y swaps reales,
No se ajusta el precio simulado por liquidez; la valoración usa referencias informativas.
No se ha contrastado el calendario completo de publicación ni rellenado fechas ausentes.
Sin optimización ni validación fuera de muestra; estas métricas no demuestran viabilidad real.
No hay órdenes reales ni conexión con un bróker. Informe educativo, sin recomendación de inversión.

## Reproducción

Desde la raíz: `python -m trading_ai --report --fast-window 10 --slow-window 40 --cost-percent 0.100 --initial-capital 1000 --allocation-percent 10.0 --data RUTA_XML --output RUTA_MD`.
Usar la misma copia (SHA-256), código y reglas. El informe no incluye hora de ejecución
ni rutas locales, para obtener el mismo contenido al repetir el cálculo.
