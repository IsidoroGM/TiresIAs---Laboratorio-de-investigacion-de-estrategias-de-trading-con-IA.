# Trading AI — Investigación local

Proveedor: ollama. Modelo: qwen3.5:4b.
Experimento: `7a1a51fd89f840b8920b04ba9489468d`.
Fuente: BCE, 1999-01-04 a 2026-10-16.
SHA-256: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

Par: USD/CHF. Capital inicial: 1000 en moneda cotizada.
Coste por compra o venta: 0.100 %. Tamaño: 10.0 % del efectivo por entrada, costes incluidos.

## Propuesta de la IA (pendiente de contrastar al formularse)

La variante de medias móviles con ventanas ajustadas (fast_window: 15, slow_window: 45) en USD/CHF podría generar una rentabilidad estrictamente superior al mantener el drawdown igual o inferior a la estrategia base SMA.

Criterio registrado: Mayor rentabilidad sin aumentar el drawdown.

## Resultados calculados por Python

| Métrica | Base | Variante |
|---|---:|---:|
| Estrategia | SMA20/SMA60 | EMA15/EMA45 |
| Moneda | CHF | CHF |
| Capital final | 930.922718 | 935.658881 |
| Rentabilidad acumulada % | -6.907728 | -6.434112 |
| Drawdown máximo % | 7.825079 | 7.721900 |
| Costes incurridos | 13.490837 | 16.789719 |
| Cierres | 70 | 87 |
| Posición abierta | Sí | Sí |
| Entradas rechazadas | 0 | 0 |

## Conclusión contrastada

Hipótesis apoyada en esta muestra.
El análisis estructurado de la IA coincide con las métricas y el criterio registrado.
Las cifras de esta tabla proceden del motor; no se extraen del texto del modelo.
Solo se estudia la muestra histórica. No hay validación fuera de muestra ni selección automática de ganadores.
Referencias educativas del BCE, costes hipotéticos, cuentas virtuales y ejecución en la siguiente observación.

Peticiones de IA: 2. Coste de API registrado: 0 USD.
