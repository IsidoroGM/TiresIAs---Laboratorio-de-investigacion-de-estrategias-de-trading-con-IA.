# Trading AI — Sensibilidad local de SMA y EMA

Formato de sensibilidad: 1. Fuente: Banco Central Europeo (BCE).
[Histórico oficial](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml).
SHA-256 de la copia analizada: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

## Diseño del experimento

- Base: ventanas 20/60; coste por compra o venta 0.100 %.
- Se cambia un factor cada vez: rápida ±1, lenta ±1, coste ±0.05 puntos porcentuales (pp).
  Por ejemplo, un coste base de 0.1 % pasa a 0.05 % o 0.15 %; no es un cambio relativo del 5 %.
- Los escenarios inválidos se omiten explícitamente, sin recortar parámetros ni sustituirlos.
- Capital inicial por cuenta: 1000 en su moneda cotizada. Tamaño: 10.0 % del efectivo al entrar, costes incluidos.
- SMA: media de las últimas n observaciones. EMA: semilla SMA de las primeras n;
  alfa = 2/(n+1); EMA actual = anterior + alfa × (precio - anterior).
- Cruce alcista: rápida pasa de <= a > lenta; bajista: de >= a <. Sin medias completas no hay señal.
- Cada escenario empieza sin posición desde la misma fecha; la primera señal posible es lenta+1.
  Cambiar la ventana lenta también cambia el calentamiento; no se iguala artificialmente ese periodo.
- Señal ejecutada en la referencia siguiente. Una compra abierta por par; sin cortos, margen ni cierre forzado.
- Última señal sin ejecución. Cantidad fija hasta salir; solo compra con saldo para importe y coste.
- Coste proporcional por cada compra/venta ejecutada. Capital y costes independientes en cada escenario.
- Referencias BCE por euro: EUR/USD directo; GBP/USD = USD/GBP; USD/JPY = JPY/USD; USD/CHF = CHF/USD.
- Mismas referencias y fechas para todos los escenarios de un par. Cálculos Decimal con 28 dígitos.
- Escenarios válidos por estrategia y par: 7.

Omisiones: ninguna.

## Cobertura

| Par | Inicio | Fin | Observaciones |
|---|---|---|---:|
| EUR/USD | 1999-01-04 | 2026-10-16 | 7116 |
| GBP/USD | 1999-01-04 | 2026-10-16 | 7116 |
| USD/JPY | 1999-01-04 | 2026-10-16 | 7116 |
| USD/CHF | 1999-01-04 | 2026-10-16 | 7116 |

## Resumen por cuenta

| Par | Estrategia | Moneda | Base % | Mínimo % | Máximo % | Máxima desviación vs base (pp) | Escenarios positivos | Con exposición |
|---|---|---|---:|---:|---:|---:|---:|---:|
| EUR/USD | SMA | USD | 1.500933 | 0.802000 | 2.205347 | 0.704414 | 7/7 | 7/7 |
| EUR/USD | EMA | USD | 1.374002 | 0.756612 | 1.995734 | 0.621732 | 7/7 | 7/7 |
| GBP/USD | SMA | USD | -2.215519 | -2.895320 | -1.530341 | 0.685178 | 0/7 | 7/7 |
| GBP/USD | EMA | USD | -0.110213 | -0.667648 | 0.450857 | 0.561070 | 3/7 | 7/7 |
| USD/JPY | SMA | JPY | 2.944100 | 1.980761 | 3.639088 | 0.963340 | 7/7 | 7/7 |
| USD/JPY | EMA | JPY | 2.632053 | 1.995690 | 3.272965 | 0.640911 | 7/7 | 7/7 |
| USD/CHF | SMA | CHF | -6.907728 | -7.555463 | -6.254865 | 0.652863 | 0/7 | 7/7 |
| USD/CHF | EMA | CHF | -4.992750 | -5.551552 | -4.430134 | 0.562616 | 0/7 | 7/7 |

El resumen incluye la base y todos los escenarios válidos; positivos significa resultado estrictamente > 0.
Con exposición: al menos una operación cerrada o una posición abierta. No representa porcentaje de tiempo invertido.
Sin exposición no hay evidencia de estabilidad, aunque todas las rentabilidades sean cero.

## Detalle de escenarios

Capital, resultado y costes están en la moneda cotizada del par. Resultado total = capital final - inicial.
Incluye costes incurridos y valoración de posiciones abiertas, sin anticipar coste de salida.
Rentabilidad acumulada = resultado / capital inicial × 100; no anualizada. Cambios expresados en puntos porcentuales.
Drawdown: mayor caída porcentual desde un máximo previo del capital diario, incluido el capital inicial.

### EUR/USD — SMA

| Escenario | Rápida/lenta | Coste % | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Cambio vs base (pp) | Drawdown máximo % | Costes incurridos | Rechazos |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Base | 20/60 | 0.100 | 69 | No | 1015.009331 | 15.009331 | 1.500933 | 0.000000 | 2.508037 | 14.053751 | 0 |
| Rápida -1 | 19/60 | 0.100 | 71 | No | 1013.160303 | 13.160303 | 1.316030 | -0.184903 | 2.827180 | 14.447101 | 0 |
| Rápida +1 | 21/60 | 0.100 | 69 | No | 1017.594773 | 17.594773 | 1.759477 | 0.258544 | 2.302161 | 14.069995 | 0 |
| Lenta -1 | 20/59 | 0.100 | 72 | No | 1013.766850 | 13.766850 | 1.376685 | -0.124248 | 2.573451 | 14.637298 | 0 |
| Lenta +1 | 20/61 | 0.100 | 68 | No | 1013.877517 | 13.877517 | 1.387752 | -0.113181 | 2.481106 | 13.843128 | 0 |
| Coste -0.05 pp | 20/60 | 0.0500 | 69 | No | 1022.053470 | 22.053470 | 2.205347 | 0.704414 | 2.305081 | 7.054472 | 0 |
| Coste +0.05 pp | 20/60 | 0.1500 | 69 | No | 1008.020003 | 8.020003 | 0.802000 | -0.698933 | 2.861789 | 20.998314 | 0 |

### EUR/USD — EMA

| Escenario | Rápida/lenta | Coste % | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Cambio vs base (pp) | Drawdown máximo % | Costes incurridos | Rechazos |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Base | 20/60 | 0.100 | 61 | No | 1013.740017 | 13.740017 | 1.374002 | 0.000000 | 3.627450 | 12.458430 | 0 |
| Rápida -1 | 19/60 | 0.100 | 64 | No | 1013.462415 | 13.462415 | 1.346242 | -0.027760 | 3.629931 | 13.076057 | 0 |
| Rápida +1 | 21/60 | 0.100 | 57 | No | 1011.339519 | 11.339519 | 1.133952 | -0.240050 | 3.543635 | 11.625364 | 0 |
| Lenta -1 | 20/59 | 0.100 | 63 | No | 1011.354239 | 11.354239 | 1.135424 | -0.238578 | 3.630211 | 12.844995 | 0 |
| Lenta +1 | 20/61 | 0.100 | 59 | No | 1012.929315 | 12.929315 | 1.292932 | -0.081070 | 3.645412 | 12.044885 | 0 |
| Coste -0.05 pp | 20/60 | 0.0500 | 61 | No | 1019.957341 | 19.957341 | 1.995734 | 0.621732 | 3.349447 | 6.251156 | 0 |
| Coste +0.05 pp | 20/60 | 0.1500 | 61 | No | 1007.566125 | 7.566125 | 0.756612 | -0.617389 | 3.904405 | 18.622166 | 0 |

### GBP/USD — SMA

| Escenario | Rápida/lenta | Coste % | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Cambio vs base (pp) | Drawdown máximo % | Costes incurridos | Rechazos |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Base | 20/60 | 0.100 | 70 | No | 977.844806 | -22.155194 | -2.215519 | 0.000000 | 4.729938 | 13.940866 | 0 |
| Rápida -1 | 19/60 | 0.100 | 69 | No | 979.372196 | -20.627804 | -2.062780 | 0.152739 | 4.373641 | 13.725530 | 0 |
| Rápida +1 | 21/60 | 0.100 | 68 | No | 974.121777 | -25.878223 | -2.587822 | -0.372303 | 4.932424 | 13.483633 | 0 |
| Lenta -1 | 20/59 | 0.100 | 69 | No | 976.329754 | -23.670246 | -2.367025 | -0.151505 | 4.726803 | 13.718546 | 0 |
| Lenta +1 | 20/61 | 0.100 | 68 | No | 976.062822 | -23.937178 | -2.393718 | -0.178198 | 4.873302 | 13.477928 | 0 |
| Coste -0.05 pp | 20/60 | 0.0500 | 70 | No | 984.696587 | -15.303413 | -1.530341 | 0.685178 | 4.386275 | 6.997856 | 0 |
| Coste +0.05 pp | 20/60 | 0.1500 | 70 | No | 971.046796 | -28.953204 | -2.895320 | -0.679801 | 5.115784 | 20.829508 | 0 |

### GBP/USD — EMA

| Escenario | Rápida/lenta | Coste % | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Cambio vs base (pp) | Drawdown máximo % | Costes incurridos | Rechazos |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Base | 20/60 | 0.100 | 56 | No | 998.897874 | -1.102126 | -0.110213 | 0.000000 | 2.899616 | 11.188538 | 0 |
| Rápida -1 | 19/60 | 0.100 | 56 | No | 997.161919 | -2.838081 | -0.283808 | -0.173596 | 2.998066 | 11.165952 | 0 |
| Rápida +1 | 21/60 | 0.100 | 56 | No | 1001.390086 | 1.390086 | 0.139009 | 0.249221 | 2.764873 | 11.202150 | 0 |
| Lenta -1 | 20/59 | 0.100 | 54 | No | 998.145739 | -1.854261 | -0.185426 | -0.075214 | 3.050580 | 10.777031 | 0 |
| Lenta +1 | 20/61 | 0.100 | 56 | No | 1000.400566 | 0.400566 | 0.040057 | 0.150269 | 2.781471 | 11.197389 | 0 |
| Coste -0.05 pp | 20/60 | 0.0500 | 56 | No | 1004.508571 | 4.508571 | 0.450857 | 0.561070 | 2.609667 | 5.612474 | 0 |
| Coste +0.05 pp | 20/60 | 0.1500 | 56 | No | 993.323516 | -6.676484 | -0.667648 | -0.557436 | 3.188442 | 16.728458 | 0 |

### USD/JPY — SMA

| Escenario | Rápida/lenta | Coste % | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Cambio vs base (pp) | Drawdown máximo % | Costes incurridos | Rechazos |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Base | 20/60 | 0.100 | 67 | No | 1029.441001 | 29.441001 | 2.944100 | 0.000000 | 3.674652 | 13.401913 | 0 |
| Rápida -1 | 19/60 | 0.100 | 68 | No | 1033.888505 | 33.888505 | 3.388851 | 0.444750 | 3.669931 | 13.619782 | 0 |
| Rápida +1 | 21/60 | 0.100 | 68 | No | 1019.807606 | 19.807606 | 1.980761 | -0.963340 | 3.986002 | 13.541887 | 0 |
| Lenta -1 | 20/59 | 0.100 | 68 | No | 1029.136534 | 29.136534 | 2.913653 | -0.030447 | 3.356375 | 13.624685 | 0 |
| Lenta +1 | 20/61 | 0.100 | 67 | No | 1028.258346 | 28.258346 | 2.825835 | -0.118266 | 3.795449 | 13.373161 | 0 |
| Coste -0.05 pp | 20/60 | 0.0500 | 67 | No | 1036.390883 | 36.390883 | 3.639088 | 0.694988 | 3.426564 | 6.726626 | 0 |
| Coste +0.05 pp | 20/60 | 0.1500 | 67 | No | 1022.543903 | 22.543903 | 2.254390 | -0.689710 | 3.921881 | 20.026297 | 0 |

### USD/JPY — EMA

| Escenario | Rápida/lenta | Coste % | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Cambio vs base (pp) | Drawdown máximo % | Costes incurridos | Rechazos |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Base | 20/60 | 0.100 | 62 | No | 1026.320534 | 26.320534 | 2.632053 | 0.000000 | 5.073104 | 12.324971 | 0 |
| Rápida -1 | 19/60 | 0.100 | 62 | No | 1026.954287 | 26.954287 | 2.695429 | 0.063375 | 4.973211 | 12.320242 | 0 |
| Rápida +1 | 21/60 | 0.100 | 61 | No | 1025.981103 | 25.981103 | 2.598110 | -0.033943 | 4.923391 | 12.146522 | 0 |
| Lenta -1 | 20/59 | 0.100 | 62 | No | 1026.059942 | 26.059942 | 2.605994 | -0.026059 | 5.043215 | 12.325109 | 0 |
| Lenta +1 | 20/61 | 0.100 | 62 | No | 1022.439803 | 22.439803 | 2.243980 | -0.388073 | 5.156203 | 12.303248 | 0 |
| Coste -0.05 pp | 20/60 | 0.0500 | 62 | No | 1032.729647 | 32.729647 | 3.272965 | 0.640911 | 4.801301 | 6.184451 | 0 |
| Coste +0.05 pp | 20/60 | 0.1500 | 62 | No | 1019.956897 | 19.956897 | 1.995690 | -0.636364 | 5.343887 | 18.421910 | 0 |

### USD/CHF — SMA

| Escenario | Rápida/lenta | Coste % | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Cambio vs base (pp) | Drawdown máximo % | Costes incurridos | Rechazos |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Base | 20/60 | 0.100 | 70 | Sí | 930.922718 | -69.077282 | -6.907728 | 0.000000 | 7.825079 | 13.490837 | 0 |
| Rápida -1 | 19/60 | 0.100 | 70 | Sí | 933.622107 | -66.377893 | -6.637789 | 0.269939 | 7.631831 | 13.509418 | 0 |
| Rápida +1 | 21/60 | 0.100 | 70 | Sí | 933.524870 | -66.475130 | -6.647513 | 0.260215 | 7.656155 | 13.508109 | 0 |
| Lenta -1 | 20/59 | 0.100 | 71 | Sí | 933.764182 | -66.235818 | -6.623582 | 0.284146 | 7.489902 | 13.698316 | 0 |
| Lenta +1 | 20/61 | 0.100 | 71 | Sí | 932.757464 | -67.242536 | -6.724254 | 0.183475 | 7.851151 | 13.712000 | 0 |
| Coste -0.05 pp | 20/60 | 0.0500 | 70 | Sí | 937.451346 | -62.548654 | -6.254865 | 0.652863 | 7.202158 | 6.771753 | 0 |
| Coste +0.05 pp | 20/60 | 0.1500 | 70 | Sí | 924.445370 | -75.554630 | -7.555463 | -0.647735 | 8.443263 | 20.157708 | 0 |

### USD/CHF — EMA

| Escenario | Rápida/lenta | Coste % | Cierres | Abierta | Capital final | Resultado total | Rentabilidad % | Cambio vs base (pp) | Drawdown máximo % | Costes incurridos | Rechazos |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| Base | 20/60 | 0.100 | 59 | Sí | 950.072500 | -49.927500 | -4.992750 | 0.000000 | 6.237574 | 11.520639 | 0 |
| Rápida -1 | 19/60 | 0.100 | 60 | Sí | 953.550834 | -46.449166 | -4.644917 | 0.347833 | 5.894298 | 11.728823 | 0 |
| Rápida +1 | 21/60 | 0.100 | 60 | Sí | 952.742662 | -47.257338 | -4.725734 | 0.267016 | 6.011681 | 11.742394 | 0 |
| Lenta -1 | 20/59 | 0.100 | 61 | Sí | 947.955428 | -52.044572 | -5.204457 | -0.211707 | 6.446507 | 11.887229 | 0 |
| Lenta +1 | 20/61 | 0.100 | 64 | Sí | 952.840745 | -47.159255 | -4.715925 | 0.276824 | 6.002005 | 12.530978 | 0 |
| Coste -0.05 pp | 20/60 | 0.0500 | 59 | Sí | 955.698657 | -44.301343 | -4.430134 | 0.562616 | 5.696856 | 5.779784 | 0 |
| Coste +0.05 pp | 20/60 | 0.1500 | 59 | Sí | 944.484483 | -55.515517 | -5.551552 | -0.558802 | 6.774710 | 17.222862 | 0 |

## Interpretación y límites

Una gran variación frente a la base indica sensibilidad local; no se impone un umbral de aprobación.
Cambios de signo muestran que el resultado depende de estos supuestos. El número de escenarios positivos no es una probabilidad.
No se elige ganador ni se ordena por rendimiento ni se buscan parámetros. No mide interacciones entre cambios simultáneos.
Reutiliza el mismo histórico: no es validación fuera de muestra ni prueba suficiente de robustez o rentabilidad futura.
Comparar dentro de cada par; no sumar monedas distintas. Igual asignación no iguala riesgo.
Referencias informativas, no precios ejecutables ni OHLC. Sin validación completa del calendario ni relleno de fechas.
Faltan spreads, slippage, swaps y restricciones reales del bróker. No hay órdenes reales ni conexión con un bróker.

## Reproducción

`python -m trading_ai --sensitivity --fast-window 20 --slow-window 60 --cost-percent 0.100 --initial-capital 1000 --allocation-percent 10.0 --data RUTA_XML --output RUTA_MD`
Usar la misma copia (SHA-256), código y reglas; sin hora de ejecución ni rutas locales en el contenido.
