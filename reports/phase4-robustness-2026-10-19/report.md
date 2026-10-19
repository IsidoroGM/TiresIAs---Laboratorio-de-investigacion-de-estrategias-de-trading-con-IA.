# Trading AI — Robustez interna en desarrollo

Par: EUR/USD. Capital inicial por escenario y periodo: 1000 en moneda cotizada.
Tamaño: 10.0 % del efectivo por entrada, costes incluidos. Coste original por ejecución: 0.100 %.
Configuración de partida: EMA20/60.
Selección fijada antes de comprobar: `Ninguna elegible`.
La selección exige cumplir el criterio frente a la base al coste original; costes alternativos solo son sensibilidad.
Se conservan todos los escenarios, sin elegir de nuevo después de la comprobación interna.

## Selección interna: 1999-01-04 a 2009-12-31

| Escenario | Ventanas | Coste por ejecución % | Rent. base % | Rent. variante % | DD base % | DD variante % | Cierres base/variante | Criterio |
|---|---|---:|---:|---:|---:|---:|---:|---|
| reference__reference | EMA20/EMA60 | 0.100 | 2.695764 | 3.743915 | 1.746293 | 1.933161 | 26/22 | No cumple |
| reference__cost_minus | EMA20/EMA60 | 0.0500 | 2.965675 | 3.975889 | 1.728027 | 1.914104 | 26/22 | No cumple |
| reference__cost_plus | EMA20/EMA60 | 0.1500 | 2.426801 | 3.512665 | 1.764538 | 1.952198 | 26/22 | No cumple |
| fast_minus__reference | EMA19/EMA60 | 0.100 | 2.695764 | 3.688348 | 1.746293 | 1.914928 | 26/23 | No cumple |
| fast_minus__cost_minus | EMA19/EMA60 | 0.0500 | 2.965675 | 3.930552 | 1.728027 | 1.895998 | 26/23 | No cumple |
| fast_minus__cost_plus | EMA19/EMA60 | 0.1500 | 2.426801 | 3.446926 | 1.764538 | 1.933836 | 26/23 | No cumple |
| fast_plus__reference | EMA21/EMA60 | 0.100 | 2.695764 | 3.582790 | 1.746293 | 1.956062 | 26/20 | No cumple |
| fast_plus__cost_minus | EMA21/EMA60 | 0.0500 | 2.965675 | 3.793488 | 1.728027 | 1.936917 | 26/20 | No cumple |
| fast_plus__cost_plus | EMA21/EMA60 | 0.1500 | 2.426801 | 3.372708 | 1.764538 | 1.975187 | 26/20 | No cumple |
| slow_minus__reference | EMA20/EMA59 | 0.100 | 2.695764 | 3.525123 | 1.746293 | 1.929042 | 26/24 | No cumple |
| slow_minus__cost_minus | EMA20/EMA59 | 0.0500 | 2.965675 | 3.777179 | 1.728027 | 1.910128 | 26/24 | No cumple |
| slow_minus__cost_plus | EMA20/EMA59 | 0.1500 | 2.426801 | 3.273904 | 1.764538 | 1.947935 | 26/24 | No cumple |
| slow_plus__reference | EMA20/EMA61 | 0.100 | 2.695764 | 3.723813 | 1.746293 | 1.938474 | 26/20 | No cumple |
| slow_plus__cost_minus | EMA20/EMA61 | 0.0500 | 2.965675 | 3.934923 | 1.728027 | 1.919309 | 26/20 | No cumple |
| slow_plus__cost_plus | EMA20/EMA61 | 0.1500 | 2.426801 | 3.513321 | 1.764538 | 1.957618 | 26/20 | No cumple |
## Comprobación interna: 2010-01-04 a 2019-12-31

| Escenario | Ventanas | Coste por ejecución % | Rent. base % | Rent. variante % | DD base % | DD variante % | Cierres base/variante | Criterio |
|---|---|---:|---:|---:|---:|---:|---:|---|
| reference__reference | EMA20/EMA60 | 0.100 | -0.773994 | -1.978800 | 2.380588 | 3.079101 | 24/26 | No cumple |
| reference__cost_minus | EMA20/EMA60 | 0.0500 | -0.531254 | -1.720383 | 2.216157 | 2.920920 | 24/26 | No cumple |
| reference__cost_plus | EMA20/EMA60 | 0.1500 | -1.015924 | -2.236305 | 2.544595 | 3.241406 | 24/26 | No cumple |
| fast_minus__reference | EMA19/EMA60 | 0.100 | -0.773994 | -1.973542 | 2.380588 | 2.964434 | 24/27 | No cumple |
| fast_minus__cost_minus | EMA19/EMA60 | 0.0500 | -0.531254 | -1.705272 | 2.216157 | 2.796238 | 24/27 | No cumple |
| fast_minus__cost_plus | EMA19/EMA60 | 0.1500 | -1.015924 | -2.240838 | 2.544595 | 3.136717 | 24/27 | No cumple |
| fast_plus__reference | EMA21/EMA60 | 0.100 | -0.773994 | -1.837646 | 2.380588 | 3.088812 | 24/23 | No cumple |
| fast_plus__cost_minus | EMA21/EMA60 | 0.0500 | -0.531254 | -1.608264 | 2.216157 | 2.933604 | 24/23 | No cumple |
| fast_plus__cost_plus | EMA21/EMA60 | 0.1500 | -1.015924 | -2.066287 | 2.544595 | 3.251091 | 24/23 | No cumple |
| slow_minus__reference | EMA20/EMA59 | 0.100 | -0.773994 | -1.951882 | 2.380588 | 3.073729 | 24/25 | No cumple |
| slow_minus__cost_minus | EMA20/EMA59 | 0.0500 | -0.531254 | -1.703205 | 2.216157 | 2.915535 | 24/25 | No cumple |
| slow_minus__cost_plus | EMA20/EMA59 | 0.1500 | -1.015924 | -2.199708 | 2.544595 | 3.236048 | 24/25 | No cumple |
| slow_plus__reference | EMA20/EMA61 | 0.100 | -0.773994 | -1.958810 | 2.380588 | 3.083928 | 24/25 | No cumple |
| slow_plus__cost_minus | EMA20/EMA61 | 0.0500 | -0.531254 | -1.710157 | 2.216157 | 2.925760 | 24/25 | No cumple |
| slow_plus__cost_plus | EMA20/EMA61 | 0.1500 | -1.015924 | -2.206612 | 2.544595 | 3.246221 | 24/25 | No cumple |

## Límites

Las variantes de ventanas proceden de cambios mecánicos de Python, no de nuevas propuestas del modelo.
Cada escenario y periodo empieza con su propio capital, sin posiciones, señales ni indicadores heredados.
Rentabilidades acumuladas no anualizadas; no se suman cuentas ni se equiparan periodos distintos.
El histórico ya se había explorado y este análisis se diseñó después de la evaluación exterior: no es evidencia inédita ni confirmación independiente.
Este flujo no lee datos ni resultados de la evaluación exterior. Sus resultados no permiten ajustar una propuesta y volver a evaluarla allí.
Un escenario favorable o una selección interna no demuestran robustez ni rentabilidad real.
Cumplir el criterio relativo puede mantener pérdidas; no se exige ni se demuestra beneficio absoluto.
Referencias BCE y costes hipotéticos. Peticiones de IA: 0. Coste de API: 0 USD.
