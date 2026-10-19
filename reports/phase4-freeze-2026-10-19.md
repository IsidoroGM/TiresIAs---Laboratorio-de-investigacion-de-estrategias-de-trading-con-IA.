# FASE 4 — Propuesta registrada antes de evaluar

Fecha: 19 de octubre de 2026. Segundo paso comprobado; fase abierta.
**449 pruebas aprobadas**, incluidas 26 nuevas del registro.

Una investigación local sobre desarrollo propuso **EMA20/60 para EUR/USD**,
comparada con la base SMA20/60. El criterio fijado es mayor rentabilidad sin
aumentar el drawdown. Solo se usaron las 5375 observaciones de desarrollo,
entre 1999-01-04 y 2019-12-31, de la
[separación preparada](phase4-split-2026-10-19.md).

## Resultado de desarrollo conservado

| Métrica | Base SMA20/60 | Variante EMA20/60 |
|---|---:|---:|
| Capital final USD | 1019.009049 | 1017.261426 |
| Rentabilidad acumulada % | 1.900905 | 1.726143 |
| Drawdown máximo % | 2.508037 | 3.283961 |
| Cierres | 50 | 47 |
| Posición abierta al final | Sí | Sí |

Capital inicial 1000 USD, costes del 0,1 % por ejecución y tamaño del 10 % del
efectivo, costes incluidos. Los capitales finales incluyen la valoración de
posiciones abiertas; las rentabilidades no están anualizadas.

La hipótesis **no está apoyada en desarrollo**: la variante obtiene menor
rentabilidad y mayor drawdown. El análisis de IA coincidió con los cálculos y
Python lo verificó. Se conservó la propuesta sin reemplazarla ni buscar otra
conclusión favorable. No hay selección automática de ganadores.

## Registro e integridad

Investigación: `.local/research/32f2bb61010644a59639db330a2b0eaa/`.
Registro: `.local/holdout/f74895dfc72d41b1867f11401cd384f2/`.
Fecha UTC de registro: `2026-10-19T10:37:30.458339+00:00`.
SHA-256 de `frozen.json`:
`1f64b917cc88993ca496798ef98e4aadf8a266f7b7f3fce9cf45d6b86d61483a`.

El comando `freeze` recalculó desarrollo y vinculó propuesta, criterio,
controles, resultados y hashes del código, manifiesto e investigación. Después,
`verify` confirmó el registro y sus referencias. Ambos comandos comprobaron los
hashes de los XML, sin calcular métricas de evaluación. No se ha ejecutado un
backtest de evaluación ni enviado sus datos al modelo en este paso.

Las 26 pruebas nuevas verifican rechazos de investigaciones sobre evaluación
o el histórico completo, investigaciones incompletas, resultados inventados,
controles inválidos, rutas ajenas a las particiones y cambios posteriores en
propuesta, criterio, controles, resultados, manifiesto, datos, investigación o
código. También comprueban la conservación de registros anteriores y que solo
se recalcula desarrollo. La suite se ejecutó sin caché y con temporal nuevo y
exclusivo según `AGENTS.md`.

## Consumo y evidencia

Ollama local con Qwen3.5:4b en CPU, contexto 4096, salida máxima 384 tokens,
temperatura 0 y sin reintentos. Dos peticiones: **1114 tokens de entrada y 161
de salida**, con duración total de investigación de **50,802 segundos** y coste
de API registrado de **0 USD**. El registro y su verificación no consultan IA.

Copias exactas para auditoría:

- [Propuesta, controles, resultados y referencias fijados](phase4-freeze-2026-10-19/frozen.json).
- [Hash del registro](phase4-freeze-2026-10-19/frozen.sha256).
- [Eventos del registro](phase4-freeze-2026-10-19/events.jsonl).
- [Resultados completos de desarrollo](phase4-freeze-2026-10-19/research-results.json).
- [Análisis verificado](phase4-freeze-2026-10-19/research-analysis.json).
- [Origen del análisis](phase4-freeze-2026-10-19/research-analysis_origin.json).
- [Peticiones, respuestas y consumo](phase4-freeze-2026-10-19/research-events.jsonl).
- [Informe de desarrollo](phase4-freeze-2026-10-19/research-report.md).
- [Correspondencia de archivos y hashes](phase4-freeze-2026-10-19/snapshot.json).

Las copias conservan sus bytes; `.gitattributes` impide cambiar sus finales de
línea al incorporarlas a Git. Las referencias absolutas del registro apuntan a
las carpetas locales originales. Estas copias no sustituyen un registro externo
inmutable: alguien con acceso completo podría reescribir datos y hashes.

## Siguiente tarea y límites

Implementar la evaluación de esta propuesta desde el registro verificado, sin
aceptar parámetros alternativos, con cuentas y calentamiento independientes.
Conservar separados los resultados de desarrollo y evaluación, y registrar los
intentos y el acceso al bloque reservado. Esta ejecución todavía no implementa
esa evaluación ni bloquea que se consulten archivos fuera de la aplicación.

El histórico completo ya se exploró en fases anteriores: esta separación no
crea datos totalmente inéditos ni demuestra robustez. Referencias BCE y costes
hipotéticos, sin operaciones reales ni APIs de pago. No se añadieron dependencias.
`PROJECT_STATUS.md` conserva el cierre de FASE 3. Sin commits ni pushes.

El [protocolo](../docs/VALIDATION_PLAN.md) describe los comandos y límites.
