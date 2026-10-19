# FASE 4 — Robustez y selección internas en desarrollo

Fecha: 19 de octubre de 2026. Cuarto paso completado; fase abierta.
**485 pruebas aprobadas**, incluidas 18 nuevas de este flujo.

Se calcularon las **30 comparaciones previstas**, 15 por tramo, cada una con
base y variante: 60 simulaciones. No hubo errores ni escenarios omitidos en la
ejecución real. **Ninguna configuración fue elegible para selección** según el
criterio fijado y no se forzó una elección.

## Protocolo fijado antes del cálculo

Fuente: exclusivamente las 5375 observaciones de desarrollo de EUR/USD,
1999-01-04 a 2019-12-31, SHA-256
`9b703b20333ef2d962d372fdfb9bf6c700f44ad2dace3d63e4d7ecf4edae58a5`.
El registro de partida conserva EMA20/60 frente a SMA20/60; no se modifica.

| Elemento | Configuración |
|---|---|
| Selección interna | 1999-01-04 a 2009-12-31; 2816 observaciones |
| Comprobación interna | 2010-01-04 a 2019-12-31; 2559 observaciones |
| Corte interno | 2010-01-01; siguiente observación publicada el día 4 |
| Variantes | EMA20/60, EMA19/60, EMA21/60, EMA20/59 y EMA20/61 |
| Costes por ejecución | 0,05 %, 0,10 % y 0,15 %; base y variante usan el mismo coste |
| Base | SMA20/60 |
| Capital y tamaño | 1000 USD por cuenta; 10 % del efectivo, costes incluidos |

Las ventanas cambian mecánicamente una observación respecto a la configuración
de partida. La selección considera solo el primer tramo al coste original de
0,10 %; los otros costes describen sensibilidad. Exige mayor rentabilidad sin
aumentar el drawdown frente a la base y cierres en ambas estrategias. Ordena
las elegibles por rentabilidad descendente, drawdown ascendente y ventanas
rápida/lenta e identificador para desempatar. Si no hay elegibles, guarda una
selección vacía. No exige beneficios absolutos ni declara viabilidad.

Se fijaron y guardaron estas reglas, los escenarios, las particiones y sus
hashes antes de calcular métricas. El evento `selection_fixed` y el archivo
`selection.json` son anteriores al primer cálculo del segundo tramo. Después
se muestran todos sus escenarios sin volver a elegir parámetros.

## Resultados conservados

Las 15 variantes por coste del primer tramo no cumplen el criterio relativo;
ninguna de las cinco ventanas al coste original es elegible. Aunque la
rentabilidad es positiva, el drawdown es mayor que el de la base. La selección
queda vacía y no se reemplaza tras observar el segundo tramo.

En 2010–2019, las cinco ventanas pierden capital con cada uno de los tres
costes. Las 15 comparaciones tampoco cumplen el criterio. Rentabilidad acumulada
de las variantes entre **−2,240838 % y −1,608264 %**, incluyendo la valoración de
posiciones abiertas. No se ha descartado ningún resultado negativo.

Ejemplo de la configuración original EMA20/60 con coste del 0,10 %:

| Tramo y métrica | Base SMA20/60 | Variante EMA20/60 |
|---|---:|---:|
| 1999–2009: capital final USD | 1026.957638 | 1037.439147 |
| 1999–2009: rentabilidad acumulada % | 2.695764 | 3.743915 |
| 1999–2009: drawdown máximo % | 1.746293 | 1.933161 |
| 1999–2009: cierres | 26 | 22 |
| 2010–2019: capital final USD | 992.260061 | 980.212004 |
| 2010–2019: rentabilidad acumulada % | -0.773994 | -1.978800 |
| 2010–2019: drawdown máximo % | 2.380588 | 3.079101 |
| 2010–2019: cierres | 24 | 26 |

No hay posiciones abiertas al terminar el primer tramo; base y variante las
mantienen al terminar el segundo. Su valoración se incluye en el capital, sin
cierre forzado. Cada escenario y tramo empieza desde cero con capital y
calentamiento propios; no hereda posiciones, indicadores ni señales. Las
rentabilidades no están anualizadas y las cuentas no forman una curva continua.

## Integridad, acceso y pruebas

Plan local: `.local/robustness/2101bd559f1e4483a2ead79d606924b7/`.
SHA-256 del plan:
`2553c8acfb238b7c09c6c0e046ca8daedd87d44db6942e0b29976ac0ff57db4f`.
Intento completado: `attempts/0f5c09829eec44a48ee0d88a118f4e3d/`.
SHA-256 de `results.json`:
`56b45a0ee99bdaffa3f6945d406304dfdf4434ee384dc03bac72be0a49e1ac1a`.

La ejecución real comprobó las aperturas mediante `builtins.open` e `io.open`:
rechazaba el XML exterior, sus comparaciones, resultados y marcas de acceso.
Terminó correctamente y registró las 26 rutas leídas para auditoría. El flujo
solo usó desarrollo y sus referencias; no reabrió evaluación 2020–2026 ni cambió
la propuesta registrada o sus resultados anteriores. Esta comprobación cubre
el código ejecutado, no constituye un aislamiento de permisos del ordenador.

Las 18 pruebas nuevas verifican preparación sin cálculos, conservación de datos,
ausencia de acceso exterior, omisiones explícitas, escenarios completos,
selección previa al segundo tramo, coste original, desempates y selección vacía.
También comprueban que cambiar solo los precios del segundo tramo no cambia
los resultados del primero ni la selección; entradas inválidas, errores,
conservación de escenarios previos, bloqueo de reintentos del mismo plan,
integridad y redondeo independiente del contexto Decimal.

Suite completa: **485 passed**, caché pytest desactivada y temporal nuevo
exclusivo según `AGENTS.md`. Ejecución real: **8,963 segundos**, sin consultas de
IA, sin nuevas dependencias y con coste de API de **0 USD**.

## Evidencias

- [Plan previo](phase4-robustness-2026-10-19/plan.json), [hash](phase4-robustness-2026-10-19/plan.sha256)
  y [eventos de preparación](phase4-robustness-2026-10-19/preparation-events.jsonl).
- [Selección fijada, vacía](phase4-robustness-2026-10-19/selection.json).
- [Todos los resultados y parámetros](phase4-robustness-2026-10-19/results.json).
- [Informe de los 30 escenarios](phase4-robustness-2026-10-19/report.md).
- [Eventos del intento](phase4-robustness-2026-10-19/events.jsonl)
  y [marca de intento único](phase4-robustness-2026-10-19/run_claim.json).
- [Auditoría de lecturas](phase4-robustness-2026-10-19/io-audit.json).
- [Correspondencia de copias y hashes](phase4-robustness-2026-10-19/snapshot.json).

Son copias exactas, con bytes conservados por `.gitattributes`. Los XML internos
permanecen en la carpeta local y sus hashes y coberturas figuran en el plan;
no se duplican en este informe. Los registros y hashes locales no son firmas
ni impiden que alguien con acceso completo reescriba archivos.

## Conclusión y límites

Esta comprobación no permite sostener que las configuraciones estudiadas
mantengan el criterio entre los dos tramos internos. Se conserva ese resultado
sin ampliar la rejilla ni cambiar la regla para obtener una selección favorable.

El histórico ya se había explorado y este análisis se diseñó después de ver la
evaluación exterior. Es sensibilidad local y validación interna descriptiva,
no confirmación independiente ni evidencia totalmente inédita. Tampoco
demuestra que ninguna otra estrategia pueda funcionar. Los resultados del
segundo tramo ya son conocidos; no se reutilizarán como prueba inédita para
una selección posterior.

Continúan las limitaciones del BCE y los costes hipotéticos; no hay dinero
real ni conexiones nuevas con TradingView o APIs. Faltan más periodos y un
protocolo previo para walk-forward o datos prospectivos, sin ajustar cambios
a la evaluación exterior ya consultada. La FASE 4 sigue abierta;
`PROJECT_STATUS.md` conserva el cierre de FASE 3. Sin commits ni pushes.

Reglas y comandos en el [protocolo de FASE 4](../docs/VALIDATION_PLAN.md).
