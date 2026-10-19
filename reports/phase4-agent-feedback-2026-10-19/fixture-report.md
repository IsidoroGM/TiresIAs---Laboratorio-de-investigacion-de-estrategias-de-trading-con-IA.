# Trading AI — Experimento de reglas revisadas

Identidad del cálculo: `6788da8c51cb467ad2b6712555c73c4d9a9e04a8f1b5d0dee6fedab70d05fd1a`.
Plan SHA-256: `4ef052266aff4b96649d43d91dc3a324510147338efccb9a9cd4fdaa1c878f65`.
Datos BCE: 2025-01-01 a 2025-01-22; 22 observaciones. Par: EUR/USD.
Datos SHA-256: `4b59d2f1877476051fd012517b657361e4bac75c2c0578361d9e257e9dd79496`.
Capital inicial por cuenta: 1000; coste proporcional por ejecución: 0.001; fracción del efectivo por entrada: 0.1.
Criterio fijado: `higher_return_without_more_drawdown`.

| Métrica | Base | Candidata |
|---|---:|---:|
| Estrategia | SMA2/SMA4 | RULE:test_only |
| Capital final | 826.9008846835818191136199802 | 902.6523551187884044777334498 |
| Rentabilidad acumulada % | -17.30991153164181808863800198 | -9.734764488121159552226655020 |
| Drawdown máximo % | 17.30991153164181808863800198 | 15.61395745173661909969725012 |
| Costes incurridos | 0.3905172217052020565190711726 | 0.7728582030400721442830172399 |
| Cierres | 3 | 4 |
| Posición abierta | False | True |
| Entradas rechazadas | 0 | 0 |

Estado del criterio: `met`. Calculado por Python.

Dos cuentas independientes, con el mismo capital, costes y tamaño; ejecución en la siguiente observación.
Las posiciones abiertas se valoran sin cierre forzado. Cero cierres o ambas métricas iguales: inconcluso.
Histórico de desarrollo ya conocido: no es evidencia inédita ni prueba de una estrategia mejor o robusta.
La revisión técnica es una declaración, no una prueba automática de equivalencia de significado.
Referencias educativas, costes hipotéticos y dinero virtual; sin operaciones reales.
El intento queda consumido aunque falle una comprobación posterior; no hay reintentos automáticos.
Solicitudes de IA: 0. Coste de API: 0 USD.
