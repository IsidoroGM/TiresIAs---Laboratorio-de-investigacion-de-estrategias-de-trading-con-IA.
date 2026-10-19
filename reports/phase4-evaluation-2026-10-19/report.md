# Trading AI — Evaluación de una propuesta fijada

Par: EUR/USD. Capital inicial por bloque: 1000 en moneda cotizada.
Coste por compra o venta: 0.100 %. Tamaño: 10.0 % del efectivo por entrada, costes incluidos.
Criterio fijado: `higher_return_without_more_drawdown`.
SHA-256 del registro previo: `1f64b917cc88993ca496798ef98e4aadf8a266f7b7f3fce9cf45d6b86d61483a`.
La propuesta y los controles se mantienen tal como se registraron, aunque no cumplan el criterio.

## Desarrollo

BCE: 1999-01-04 a 2019-12-31; 5375 observaciones.
SHA-256: `9b703b20333ef2d962d372fdfb9bf6c700f44ad2dace3d63e4d7ecf4edae58a5`.

| Métrica | Base | Variante |
|---|---:|---:|
| Estrategia | SMA20/SMA60 | EMA20/EMA60 |
| Capital final | 1019.009049 | 1017.261426 |
| Rentabilidad acumulada % | 1.900905 | 1.726143 |
| Drawdown máximo % | 2.508037 | 3.283961 |
| Costes incurridos | 10.292246 | 9.720936 |
| Cierres | 50 | 47 |
| Posición abierta | Sí | Sí |
| Entradas rechazadas | 0 | 0 |

Criterio no cumplido en este bloque.

## Evaluación reservada

BCE: 2020-01-02 a 2026-10-16; 1741 observaciones.
SHA-256: `d4de382e518ac7b85598ee08011fd9de91e00248611423bfc726ef306d4e7f26`.

| Métrica | Base | Variante |
|---|---:|---:|
| Estrategia | SMA20/SMA60 | EMA20/EMA60 |
| Capital final | 998.717306 | 1004.257946 |
| Rentabilidad acumulada % | -0.128269 | 0.425795 |
| Drawdown máximo % | 1.548108 | 1.031090 |
| Costes incurridos | 3.402085 | 2.417261 |
| Cierres | 17 | 12 |
| Posición abierta | No | No |
| Entradas rechazadas | 0 | 0 |

Criterio cumplido en este bloque.

## Alcance

Cálculos y conclusiones de Python; no se ha consultado IA ni cambiado la propuesta tras evaluar.
Cada bloque empieza con su propio capital, sin posiciones ni señales heredadas; indicadores calculados desde su inicio.
Las posiciones abiertas se valoran sin cierre forzado. Las cuentas no forman una curva continua.
Rentabilidades acumuladas, no anualizadas. Los periodos tienen distinta longitud; no se comparan como rendimientos equivalentes.
El histórico completo ya se exploró en fases anteriores: esta separación no crea evidencia totalmente inédita.
Cumplir un criterio no demuestra rentabilidad ni robustez; no hay selección automática de ganadores.
Con cero cierres en cualquiera de las estrategias, o con ambas métricas iguales, la comparación es inconclusa.
Referencias educativas del BCE y costes hipotéticos; sin operaciones con dinero real.
Este bloque queda registrado como consultado por el flujo, incluso si el cálculo posterior falla.
Peticiones de IA: 0. Coste de API registrado: 0 USD.
