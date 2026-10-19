# Comprobación funcional del investigador local

Fecha: 19 de octubre de 2026. FASE 3 en desarrollo.

Las tres investigaciones nuevas han terminado con 3/3 análisis validados. EUR/USD se incorpora desde la comprobación anterior, sin repetir su consulta a la IA.

## Supuestos comunes

Ollama 0.40.6 y Qwen3.5:4b en CPU, contexto de 4096 tokens y salida máxima de 384 tokens por petición. Hasta dos peticiones de IA por investigación, sin reintentos automáticos ni API de pago.
Digest del modelo: `d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`.

Base SMA20/60; capital inicial 1000 en la moneda cotizada de cada cuenta; coste de 0,1 % por compra y venta; asignación del 10 % del efectivo, incluidos costes. La variante comparte estos controles.
Copia BCE de 7116 observaciones por par, de 1999-01-04 a 2026-10-16. Ejecución en la referencia siguiente, sin cerrar posiciones al terminar.

## Resultados calculados

Rentabilidades acumuladas de toda la muestra, no anualizadas. El capital final incluye posiciones abiertas. Cada comparación se realiza dentro de su par; las cuentas no forman una cartera compartida.

| Par | Variante | Rentabilidad base % | Rentabilidad variante % | Drawdown base % | Drawdown variante % | Hipótesis |
|---|---|---:|---:|---:|---:|---|
| EUR/USD | EMA15/EMA45 | 1.500933 | 0.068919 | 2.508037 | 4.500939 | No apoyada |
| GBP/USD | EMA15/EMA45 | -2.215519 | -1.529609 | 4.729938 | 4.038446 | Apoyada en esta muestra |
| USD/JPY | SMA15/SMA45 | 2.944100 | 0.306718 | 3.674652 | 4.456884 | No apoyada |
| USD/CHF | EMA15/EMA45 | -6.907728 | -6.434112 | 7.825079 | 7.721900 | Apoyada en esta muestra |

En GBP/USD y USD/CHF la variante cumple el criterio relativo, pero ambas cuentas
siguen acumulando pérdidas. Cumplirlo no implica rentabilidad positiva ni aptitud
para operar. EUR/USD y USD/JPY no apoyan la hipótesis propuesta.

## Criterios y trazabilidad

- [EUR/USD: informe](local-agent-check-2026-10-19/eur-usd.md). Criterio: Mayor rentabilidad sin aumentar el drawdown.
- [GBP/USD: informe](local-agent-check-2026-10-19/gbp-usd.md). Criterio: Mayor rentabilidad sin aumentar el drawdown.
- [USD/JPY: informe](local-agent-check-2026-10-19/usd-jpy.md). Criterio: Mayor rentabilidad sin aumentar el drawdown.
- [USD/CHF: informe](local-agent-check-2026-10-19/usd-chf.md). Criterio: Mayor rentabilidad sin aumentar el drawdown.

Se conservan copias exactas de los informes y [evidencia estructurada](local-agent-check-2026-10-19/evidence.json)
con resultados, análisis, consumo y hashes dentro de `reports/`. Los registros
completos de peticiones, respuestas y eventos siguen en sus carpetas `.local/`.

Los cuatro registros conservan parámetros, fuentes y hashes del código. Se ha comprobado que los módulos de cálculo son idénticos y que recalcular cada experimento reproduce íntegramente sus resultados. El formato del informe y el registro agregado de costes se ampliaron después de la primera prueba EUR/USD.

## Funcionamiento y consumo

| Par | Procedencia | Peticiones IA | Tokens entrada/salida | Segundos | Errores |
|---|---|---:|---:|---:|---|
| EUR/USD | Anterior | 2 | 1102/170 | 46.033 | Ninguno |
| GBP/USD | Nueva | 2 | 1097/167 | 53.337 | Ninguno |
| USD/JPY | Nueva | 2 | 1104/169 | 42.437 | Ninguno |
| USD/CHF | Nueva | 2 | 1100/168 | 41.794 | Ninguno |

Coste de consultas API: **0 USD**. El consumo eléctrico no está estimado.

Las tres ejecuciones nuevas utilizaron seis peticiones de IA, 3301 tokens de
entrada y 504 de salida. Su duración acumulada fue de 137,568 segundos.

## Alcance de la comprobación

Una investigación por par solo comprueba estas ejecuciones. No mide la tasa de acierto general del modelo ni demuestra robustez o viabilidad de las estrategias. Las referencias BCE son educativas y los costes hipotéticos. La validación fuera de muestra corresponde a FASE 4.

No se detectaron errores funcionales en estas tres investigaciones. Las cuatro
propuestas eligieron ventanas 15/45; queda pendiente evaluar la consistencia del
agente con otras preguntas y casos antes de ampliar su autonomía.

No se han modificado el motor, sus controles, las dependencias ni el acceso a proveedores. No se ejecutan operaciones reales. La FASE 3 continúa abierta y PROJECT_STATUS.md conserva su cierre anterior.
