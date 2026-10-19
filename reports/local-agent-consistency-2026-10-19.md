# Consistencia del análisis del investigador local

Fecha: 19 de octubre de 2026. FASE 3 en desarrollo.

Resultado: **4/6 respuestas correctas**, con 2/3 casos correctos con ambas preguntas.

Las respuestas fueron idénticas entre las dos preguntas en los tres casos. Esa
estabilidad no implica acierto: el modelo repitió el mismo error en las dos
preguntas sobre historia insuficiente. La aplicación rechazó ambas respuestas.

Se evalúa únicamente la interpretación de resultados previamente calculados; no se solicitan nuevas hipótesis. Las respuestas esperadas se fijaron antes de las consultas y no se enviaron al modelo. Se mantuvieron el mismo mensaje de sistema y el mismo JSON de datos para cada pareja de preguntas; solo cambió la redacción de la pregunta.

| Caso | Pregunta | Veredicto esperado | Veredicto recibido | Comprobación | Segundos |
|---|---:|---|---|---|---:|
| Mejora relativa (GBP/USD) | 1 | Apoyada en esta muestra | Apoyada en esta muestra | Correcta | 28.521 |
| Mejora relativa (GBP/USD) | 2 | Apoyada en esta muestra | Apoyada en esta muestra | Correcta | 22.712 |
| Criterio incumplido (EUR/USD) | 1 | No apoyada | No apoyada | Correcta | 22.609 |
| Criterio incumplido (EUR/USD) | 2 | No apoyada | No apoyada | Correcta | 22.889 |
| Historia insuficiente en la base (EUR/USD) | 1 | Inconclusa | No apoyada | Rechazada | 20.502 |
| Historia insuficiente en la base (EUR/USD) | 2 | Inconclusa | No apoyada | Rechazada | 20.280 |

La comprobación exige también que las comparaciones de rentabilidad y drawdown coincidan exactamente con las métricas y que el alcance sea únicamente la muestra histórica.

## Datos y controles

Los casos completos reutilizan los cálculos de GBP/USD y EUR/USD, recalculados con los mismos datos y supuestos. En GBP/USD la variante mejora relativamente, pero sigue perdiendo dinero. No se interpreta como una estrategia rentable.
El tercer caso usa las primeras 40 observaciones reales de EUR/USD, de 1999-01-04 a 1999-02-26. La base SMA20/60 no genera cierres; EMA1/2 registra cinco. Aunque las métricas difieren, falta historia para comparar la base: el resultado esperado es inconcluso.
Capital 1000 en moneda cotizada, coste de 0,1 % por ejecución y asignación del 10 % del efectivo. Qwen3.5:4b en CPU, temperatura 0, contexto 4096 y salida máxima 384 tokens. Sin reintentos ni servicios de pago.

## Consumo e incidencias

Seis consultas; 5150 tokens de entrada y 275 de salida. Tiempo acumulado de las consultas: 137.513 segundos. Coste de API: **0 USD**.
- Caso insufficient_base_history, pregunta 1: ValueError: El análisis de la IA no coincide con las métricas o con el criterio registrado.
- Caso insufficient_base_history, pregunta 2: ValueError: El análisis de la IA no coincide con las métricas o con el criterio registrado.

## Evidencia

En el caso insuficiente, la base tiene cero cierres y drawdown de 0 %; la variante
tiene cinco cierres y drawdown de 0,362930 %. Por la regla registrada, el veredicto
debe ser inconcluso y el drawdown de la variante es mayor. El modelo respondió
«no apoyada» y comparó ambos drawdowns como iguales en las dos consultas.

Estas respuestas se conservaron como errores, sin reintentar las consultas ni
modificar los resultados esperados. No hubo fallos de transporte o formato JSON;
los dos fallos fueron de interpretación de los datos.

- [Plan, casos, preguntas, respuestas esperadas y hashes](local-agent-consistency-2026-10-19/plan.json).
- [Peticiones y respuestas completas](local-agent-consistency-2026-10-19/events.jsonl).
- [Identidad y configuración del modelo](local-agent-consistency-2026-10-19/provider.json).
- [Resumen de consumo y resultados](local-agent-consistency-2026-10-19/summary.json).
- [Subconjunto derivado del BCE](local-agent-consistency-2026-10-19/ecb-first-40-observations.xml).
- [Auditoría de las seis consultas, discrepancias y hashes](local-agent-consistency-2026-10-19/audit.json).

## Límites

Antes de plantear el cierre de la FASE 3 hay que revisar el tratamiento de historia
insuficiente. Una condición previa calculada por Python puede comunicar que no es
posible comparar, conservando la validación y el registro de las respuestas del
modelo. Cualquier corrección deberá verificarse con los casos fallidos; esta tarea
solo ejecutó las seis comprobaciones acordadas y no modificó el comportamiento
del agente.

Dos preguntas por caso no demuestran fiabilidad general. Esta comprobación usa respuestas estructuradas y no evalúa explicaciones libres, estrategias nuevas, búsqueda de parámetros ni validación fuera de muestra. No se modifica el motor ni se ejecutan operaciones reales. La fase no se cierra automáticamente y PROJECT_STATUS.md conserva el cierre anterior.
