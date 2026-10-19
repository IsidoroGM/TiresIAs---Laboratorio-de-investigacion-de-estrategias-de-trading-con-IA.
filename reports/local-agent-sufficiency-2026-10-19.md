# Control previo de operaciones cerradas

Fecha: 19 de octubre de 2026. FASE 3 en desarrollo.

**3/3 comprobaciones del flujo completo correctas.** El caso insuficiente se resuelve desde Python; los dos casos evaluables mantienen el análisis de IA verificado.

| Caso | Resultado | Origen de la conclusión | Peticiones IA | Segundos |
|---|---|---|---:|---:|
| Historia insuficiente (EUR/USD) | Inconcluso | Python: control previo | 1 | 29.397 |
| Mejora relativa (GBP/USD) | Apoyada en esta muestra | IA verificada por Python | 2 | 43.687 |
| Criterio incumplido (EUR/USD) | No apoyada | IA verificada por Python | 2 | 43.075 |

## Cambio comprobado

Después de calcular el experimento, Python comprueba los cierres de ambas estrategias. Si alguna tiene cero, genera un resultado inconcluso, registra el motivo y evita pedir el análisis al modelo. La propuesta sigue procediendo de una petición de IA.

El caso insuficiente reutiliza las mismas 40 observaciones del BCE: la base SMA20/60 tiene cero cierres y EMA1/2 tiene cinco y una posición abierta. Se conservan sus métricas: rentabilidad variante -0,362930 % y drawdown 0,362930 %, frente a cero en la base. Python registra correctamente menor rentabilidad, mayor drawdown y veredicto inconcluso.

Los casos normales reutilizan las mismas bases, variantes, parámetros y datos de la evaluación previa. El caso GBP/USD cumple el criterio relativo pero sigue teniendo pérdidas; EUR/USD no lo cumple. Los resultados numéricos coinciden íntegramente con los anteriores.

La conclusión y su autoría se guardan separadamente en analysis.json y analysis_origin.json. El registro incluye los cierres, el control previo y la omisión de análisis cuando procede. El informe distingue una conclusión de Python de una respuesta de IA comprobada.

## Validación

- Tres regresiones nuevas fallaban antes del cambio y pasan después: cero cierres en la base, en la variante o en ambas.
- Suite completa: **399 pruebas aprobadas**, con caché desactivada y carpeta temporal exclusiva según AGENTS.md.
- Tres ejecuciones completas con propuestas nuevas del modelo local y variantes fijadas para reproducir los casos. Sin reintentos.
- Verificados el número real de peticiones, los datos, los parámetros, las métricas, las conclusiones y su autoría.
- La evidencia anterior se conserva byte a byte; el motor de cálculos y el proveedor no se han modificado.

Cinco peticiones de IA: 2518 tokens de entrada y 469 de salida. Duración acumulada: 116.159 segundos. Coste de API: **0 USD**.

## Informes y evidencia

- [Historia insuficiente (EUR/USD)](local-agent-sufficiency-2026-10-19/insufficient-history.md).
- [Mejora relativa (GBP/USD)](local-agent-sufficiency-2026-10-19/relative-improvement.md).
- [Criterio incumplido (EUR/USD)](local-agent-sufficiency-2026-10-19/criterion-not-met.md).
- [Resultados, autoría, eventos, consumo y hashes](local-agent-sufficiency-2026-10-19/evidence.json).
- [Evaluación aislada anterior del modelo: 4/6](local-agent-consistency-2026-10-19.md).

## Límites

Estas tres comprobaciones validan el comportamiento de la aplicación, no una mejora de las respuestas aisladas del modelo. El resultado anterior de 4/6 sigue vigente. En el caso insuficiente no se pidió al modelo un nuevo veredicto ni se atribuyó la respuesta de Python a la IA.

Esta regla de cero cierres no demuestra suficiencia estadística cuando hay cierres ni sustituye la validación fuera de muestra de FASE 4. Se mantienen referencias educativas, cuentas virtuales y costes hipotéticos. La FASE 3 continúa abierta; PROJECT_STATUS.md no se ha actualizado. No se han instalado dependencias ni realizado commits o pushes.
