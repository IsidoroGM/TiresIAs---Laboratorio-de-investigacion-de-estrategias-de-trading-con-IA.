# FASE 4 — Primera evaluación de la propuesta registrada

Fecha: 19 de octubre de 2026. Tercer paso completado; fase abierta.
**467 pruebas aprobadas**, incluidas 18 nuevas de evaluación.

Se evaluó la misma propuesta EMA20/60 para EUR/USD, frente a SMA20/60,
sin cambiar ventanas, criterio, capital, costes ni tamaño. El
[registro previo](phase4-freeze-2026-10-19.md) conserva el resultado negativo de
desarrollo y el SHA-256 fijado antes de esta evaluación:
`1f64b917cc88993ca496798ef98e4aadf8a266f7b7f3fce9cf45d6b86d61483a`.

## Resultados calculados por el motor

| Bloque y métrica | Base SMA20/60 | Variante EMA20/60 |
|---|---:|---:|
| Desarrollo: capital final USD | 1019.009049 | 1017.261426 |
| Desarrollo: rentabilidad acumulada % | 1.900905 | 1.726143 |
| Desarrollo: drawdown máximo % | 2.508037 | 3.283961 |
| Desarrollo: cierres | 50 | 47 |
| Desarrollo: posición abierta | Sí | Sí |
| Evaluación: capital final USD | 998.717306 | 1004.257946 |
| Evaluación: rentabilidad acumulada % | -0.128269 | 0.425795 |
| Evaluación: drawdown máximo % | 1.548108 | 1.031090 |
| Evaluación: cierres | 17 | 12 |
| Evaluación: posición abierta | No | No |

Desarrollo: 5375 observaciones, de 1999-01-04 a 2019-12-31. Evaluación: 1741,
de 2020-01-02 a 2026-10-16. Corte acordado: 2020-01-01.

Cada cuenta empieza con 1000 USD, costes del 0,1 % por compra o venta y tamaño
del 10 % del efectivo, costes incluidos. Las medias se calculan desde el inicio
de cada bloque, sin posiciones, señales ni capital heredados. Las posiciones
abiertas de desarrollo se valoran allí y no se trasladan a evaluación. Las
rentabilidades son acumuladas, no anualizadas; las cuentas no forman una curva
continua ni se comparan periodos de distinta longitud como si fueran iguales.

El criterio registrado, mayor rentabilidad sin aumentar el drawdown, **no se
cumple en desarrollo y sí se cumple en evaluación**. Las conclusiones proceden
de Python y se conservan separadas. No se elige un ganador global ni se cambia
la propuesta por haber observado estos resultados.

## Acceso, integridad y registro

Intento completado:
`.local/evaluations/e4b0dc31a25a46f0a84655d433840a67/`.
Marca de acceso UTC: `2026-10-19T10:45:17.632653+00:00`, anterior al cálculo.

El flujo verificó el registro y las referencias antes de evaluar, contrastó las
fechas reales con el manifiesto y comprobó nuevamente la integridad después del
cálculo. El registro original y los módulos vinculados a él permanecen intactos;
el evaluador es un módulo nuevo. El SHA-256 de `comparison.json` coincide con el
registrado en el evento final:
`ea565c5934e6a160a9a56fb2470a019c718446e62359178e9b411f45997b9b3f`.

El archivo reservado queda marcado como consultado en
`.local/evaluation-access/d4de382e518ac7b85598ee08011fd9de91e00248611423bfc726ef306d4e7f26.json`.
Cambiar la carpeta de salida o registrar otra propuesta no permite volver a
evaluar esos mismos bytes mediante este flujo. Un fallo después de marcar el
acceso conserva la marca; un intento rechazado conserva su propio registro.
No se ha realizado un segundo cálculo sobre el archivo reservado real.

## Pruebas y consumo

18 pruebas nuevas comprueban parámetros fijos, capital inicial y observaciones
propias de evaluación, ausencia de consultas de IA, integridad, registro previo
al cálculo, repeticiones y concurrencia. También cubren errores después del
acceso, conservación de resultados rechazados, fechas incompatibles, código
cambiante, redondeo independiente del contexto Decimal y resultado inconcluso
cuando no hay cierres.

Suite completa: **467 passed**, caché desactivada y temporal nuevo exclusivo
según `AGENTS.md`. Los tests usan registros de acceso temporales propios y no
marcan el archivo real como consultado. Se verificó después el registro real
anterior y se ejecutó una evaluación completa, sin errores.

Duración de la evaluación real: **3,567 segundos**. Peticiones de IA: **0**.
Coste de API registrado: **0 USD**. Sin dependencias nuevas ni servicios externos.

## Evidencia conservada

- [Comparación completa y referencias](phase4-evaluation-2026-10-19/comparison.json).
- [Resultado de evaluación calculado](phase4-evaluation-2026-10-19/evaluation_raw.json).
- [Informe completo](phase4-evaluation-2026-10-19/report.md).
- [Eventos del intento](phase4-evaluation-2026-10-19/events.jsonl).
- [Marca de acceso](phase4-evaluation-2026-10-19/access.json).
- [Correspondencia de copias y hashes](phase4-evaluation-2026-10-19/snapshot.json).

Estas son copias exactas de los archivos locales; `.gitattributes` conserva sus
bytes al incorporarlas a Git. El registro local y los hashes no constituyen una
firma ni evitan que alguien con acceso completo borre evidencias o consulte
datos fuera de la aplicación. La marca identifica los bytes, no todas las
representaciones equivalentes de los mismos datos.

## Límites y continuidad

El histórico completo ya se exploró en fases anteriores. Esta separación
comprueba el procedimiento, pero no crea evidencia totalmente inédita. El
cumplimiento del criterio en un periodo no demuestra robustez ni viabilidad con
dinero real. Se mantienen referencias BCE, costes hipotéticos y las limitaciones
del simulador. Faltan comprobaciones con más periodos y selección controlada de
parámetros exclusivamente en desarrollo, sin adaptar cambios a la evaluación
que acaba de consultarse.

El acceso se bloquea por archivo reservado completo, compartido por los cuatro
pares. Más propuestas o pares requerirán un protocolo previo de conjunto o una
evaluación prospectiva; este paso no abre una búsqueda repetida sobre los mismos
resultados. TradingView continúa pendiente y OpenAI desactivado.

`PROJECT_STATUS.md` conserva el cierre de FASE 3. Sin commits ni pushes.
El [protocolo de FASE 4](../docs/VALIDATION_PLAN.md) describe el uso y sus límites.
