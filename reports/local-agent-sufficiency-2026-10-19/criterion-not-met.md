# Trading AI — Investigación local

Proveedor: ollama. Modelo: qwen3.5:4b.
Experimento: `91570c2ee9fa4b4b93e2861e72f775a5`.
Fuente: BCE, 1999-01-04 a 2026-10-16.
SHA-256: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

Par: EUR/USD. Capital inicial: 1000 en moneda cotizada.
Coste por compra o venta: 0.100 %. Tamaño: 10.0 % del efectivo por entrada, costes incluidos.

## Propuesta de la IA (pendiente de contrastar al formularse)

La estrategia EMA con ventanas rápidas de 15 y lentas de 45 podría generar una rentabilidad estrictamente superior a la SMA (ventanas 20, 60) sin incrementar el drawdown máximo en muestras del par EUR/USD.

Criterio registrado: Mayor rentabilidad sin aumentar el drawdown.

## Resultados calculados por Python

| Métrica | Base | Variante |
|---|---:|---:|
| Estrategia | SMA20/SMA60 | EMA15/EMA45 |
| Moneda | USD | USD |
| Capital final | 1015.009331 | 1000.689190 |
| Rentabilidad acumulada % | 1.500933 | 0.068919 |
| Drawdown máximo % | 2.508037 | 4.500939 |
| Costes incurridos | 14.053751 | 17.927228 |
| Cierres | 69 | 89 |
| Posición abierta | No | No |
| Entradas rechazadas | 0 | 0 |

## Conclusión contrastada

Hipótesis no apoyada en esta muestra.
Origen de la conclusión: IA, verificada por Python.
El análisis estructurado de la IA coincide con las métricas y el criterio registrado.
Las cifras de esta tabla proceden del motor; no se extraen del texto del modelo.
Solo se estudia la muestra histórica. No hay validación fuera de muestra ni selección automática de ganadores.
Referencias educativas del BCE, costes hipotéticos, cuentas virtuales y ejecución en la siguiente observación.

Peticiones de IA: 2. Coste de API registrado: 0 USD.
