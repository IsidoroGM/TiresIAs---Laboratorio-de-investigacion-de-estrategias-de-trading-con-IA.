# Trading AI — Investigación local

Proveedor: ollama. Modelo: qwen3.5:4b.
Experimento: `57b6c01002564c3391bd134a4f063e87`.
Fuente: BCE, 1999-01-04 a 1999-02-26.
SHA-256: `c8f0119fd08f552a00c28ba7b2bcd17e5fd75cd810fe159e0bed7d2005dafcd1`.

Par: EUR/USD. Capital inicial: 1000 en moneda cotizada.
Coste por compra o venta: 0.100 %. Tamaño: 10.0 % del efectivo por entrada, costes incluidos.

## Propuesta de la IA (pendiente de contrastar al formularse)

La estrategia EMA con ventanas rápidas de 1 y lentas de 2 podría generar una rentabilidad estrictamente superior a la SMA (ventanas 20, 60) sin incrementar el drawdown máximo en muestras del par EUR/USD.

Criterio registrado: Mayor rentabilidad sin aumentar el drawdown.

## Resultados calculados por Python

| Métrica | Base | Variante |
|---|---:|---:|
| Estrategia | SMA20/SMA60 | EMA1/EMA2 |
| Moneda | USD | USD |
| Capital final | 1000.000000 | 996.370700 |
| Rentabilidad acumulada % | 0.000000 | -0.362930 |
| Drawdown máximo % | 0.000000 | 0.362930 |
| Costes incurridos | 0.000000 | 1.094807 |
| Cierres | 0 | 5 |
| Posición abierta | No | Sí |
| Entradas rechazadas | 0 | 0 |

## Conclusión contrastada

Resultado inconcluso.
Origen de la conclusión: Python (control previo).
Motivo: sin operaciones cerradas en la base. La comparación se considera inconclusa.
No se ha solicitado un análisis a la IA para este experimento.
Cero cierres no excluye posiciones abiertas; las métricas calculadas se conservan.
Las cifras de esta tabla proceden del motor; no se extraen del texto del modelo.
Solo se estudia la muestra histórica. No hay validación fuera de muestra ni selección automática de ganadores.
Referencias educativas del BCE, costes hipotéticos, cuentas virtuales y ejecución en la siguiente observación.

Peticiones de IA: 1. Coste de API registrado: 0 USD.
