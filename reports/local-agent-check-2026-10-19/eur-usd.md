# Trading AI — Investigación local

Proveedor: ollama. Modelo: qwen3.5:4b.
Experimento: `d429de06630c47018629c19d949899ca`.
Fuente: BCE, 1999-01-04 a 2026-10-16.
SHA-256: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

## Propuesta de la IA (pendiente de contrastar al formularse)

La variante de medias móviles con ventana rápida de 15 y lenta de 45 generará una rentabilidad estrictamente superior a la base (ventana rápida de 20, lenta de 60) manteniendo un drawdown no mayor.

Criterio registrado: `higher_return_without_more_drawdown`.

## Resultados calculados por Python

| Métrica | Base | Variante |
|---|---:|---:|
| Estrategia | SMA20/SMA60 | EMA15/EMA45 |
| Moneda | USD | USD |
| Capital final | 1015.009330793108646845680949 | 1000.689189570226542973038993 |
| Rentabilidad acumulada % | 1.500933079310864684568094900 | 0.068918957022654297303899300 |
| Drawdown máximo % | 2.508037497608682586090015248 | 4.500939144856642788030413284 |
| Costes incurridos | 14.05375080356005718685929246 | 17.92722848928655055440314806 |
| Cierres | 69 | 89 |
| Posición abierta | False | False |
| Entradas rechazadas | 0 | 0 |

## Conclusión contrastada

Hipótesis no apoyada en esta muestra.
El análisis estructurado de la IA coincide con las métricas y el criterio registrado.
Las cifras de esta tabla proceden del motor; no se extraen del texto del modelo.
Solo se estudia la muestra histórica. No hay validación fuera de muestra ni selección automática de ganadores.
Referencias educativas del BCE, costes hipotéticos, cuentas virtuales y ejecución en la siguiente observación.

Peticiones de IA: 2. Coste de API: 0 USD (ejecución local).
