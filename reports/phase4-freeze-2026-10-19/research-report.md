# Trading AI — Investigación local

Proveedor: ollama. Modelo: qwen3.5:4b.
Experimento: `32f2bb61010644a59639db330a2b0eaa`.
Fuente: BCE, 1999-01-04 a 2019-12-31.
SHA-256: `9b703b20333ef2d962d372fdfb9bf6c700f44ad2dace3d63e4d7ecf4edae58a5`.

Par: EUR/USD. Capital inicial: 1000 en moneda cotizada.
Coste por compra o venta: 0.100 %. Tamaño: 10.0 % del efectivo por entrada, costes incluidos.

## Propuesta de la IA (pendiente de contrastar al formularse)

Se propone que la variante EMA con ventanas de 20 y 60 periodos generará una rentabilidad estrictamente superior al SMA base sin incrementar el drawdown máximo en muestras de EUR/USD.

Criterio registrado: Mayor rentabilidad sin aumentar el drawdown.

## Resultados calculados por Python

| Métrica | Base | Variante |
|---|---:|---:|
| Estrategia | SMA20/SMA60 | EMA20/EMA60 |
| Moneda | USD | USD |
| Capital final | 1019.009049 | 1017.261426 |
| Rentabilidad acumulada % | 1.900905 | 1.726143 |
| Drawdown máximo % | 2.508037 | 3.283961 |
| Costes incurridos | 10.292246 | 9.720936 |
| Cierres | 50 | 47 |
| Posición abierta | Sí | Sí |
| Entradas rechazadas | 0 | 0 |

## Conclusión contrastada

Hipótesis no apoyada en esta muestra.
Origen de la conclusión: IA, verificada por Python.
El análisis estructurado de la IA coincide con las métricas y el criterio registrado.
Las cifras de esta tabla proceden del motor; no se extraen del texto del modelo.
Solo se estudia la muestra histórica. No hay validación fuera de muestra ni selección automática de ganadores.
Referencias educativas del BCE, costes hipotéticos, cuentas virtuales y ejecución en la siguiente observación.

Peticiones de IA: 2. Coste de API registrado: 0 USD.
