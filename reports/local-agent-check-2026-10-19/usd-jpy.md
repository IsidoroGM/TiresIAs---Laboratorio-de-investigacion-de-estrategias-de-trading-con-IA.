# Trading AI — Investigación local

Proveedor: ollama. Modelo: qwen3.5:4b.
Experimento: `e9692c3c0b5d4dd9a79fac1427617428`.
Fuente: BCE, 1999-01-04 a 2026-10-16.
SHA-256: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

Par: USD/JPY. Capital inicial: 1000 en moneda cotizada.
Coste por compra o venta: 0.100 %. Tamaño: 10.0 % del efectivo por entrada, costes incluidos.

## Propuesta de la IA (pendiente de contrastar al formularse)

La variante de medias móviles con ventanas ajustadas (fast_window: 15, slow_window: 45) en USD/JPY podría generar una rentabilidad estrictamente superior al mantener el drawdown igual o inferior a la estrategia base.

Criterio registrado: Mayor rentabilidad sin aumentar el drawdown.

## Resultados calculados por Python

| Métrica | Base | Variante |
|---|---:|---:|
| Estrategia | SMA20/SMA60 | SMA15/SMA45 |
| Moneda | JPY | JPY |
| Capital final | 1029.441001 | 1003.067176 |
| Rentabilidad acumulada % | 2.944100 | 0.306718 |
| Drawdown máximo % | 3.674652 | 4.456884 |
| Costes incurridos | 13.401913 | 18.672349 |
| Cierres | 67 | 94 |
| Posición abierta | No | Sí |
| Entradas rechazadas | 0 | 0 |

## Conclusión contrastada

Hipótesis no apoyada en esta muestra.
El análisis estructurado de la IA coincide con las métricas y el criterio registrado.
Las cifras de esta tabla proceden del motor; no se extraen del texto del modelo.
Solo se estudia la muestra histórica. No hay validación fuera de muestra ni selección automática de ganadores.
Referencias educativas del BCE, costes hipotéticos, cuentas virtuales y ejecución en la siguiente observación.

Peticiones de IA: 2. Coste de API registrado: 0 USD.
