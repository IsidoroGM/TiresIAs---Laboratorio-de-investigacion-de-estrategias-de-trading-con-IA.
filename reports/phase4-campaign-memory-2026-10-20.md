# TiresIAs — memoria de resultados y verificación reutilizable

20/10/2026. FASE 4 abierta. HEAD inicial: `3d0fa83`, rama `main`; 24 entradas
pendientes conservadas. No se modifican módulos o pruebas de las evidencias
históricas, ni `docs/PROJECT_STATUS.md`.

## Resultado

`campaign_memory.py` reúne registro contable, propuestas y sus reglas, consumo,
revisiones, permisos y comparaciones. Incorpora resúmenes y criterio de Python
únicamente tras verificar la ejecución y sus fuentes. Mantiene resultados
negativos o inconclusos, sin selección o adopción automática. No recalcula backtests.

Los fallos conservan errores, intentos observados y huellas de contabilidad parcial;
no se presentan como resultados completos. Se detectan reservas del motor sin
recibo SQLite, reservas contables sin cálculo y protocolos desconocidos de una
reserva vinculada al permiso. Una fuente desconocida o alterada detiene el flujo.
No se liberan intentos ni se reconstruye lo que el motor no dejó calculado.

La consulta compara dos lecturas. El documento de memoria se guarda en una carpeta
exclusiva, con SHA-256 y eventos; al verificarlo se exige coincidencia con el estado
actual. Límite: 120.000 bytes sin recortar entradas. Se mantienen separados el
consumo de la campaña, los desconocidos, los subtotales y el ámbito compacto heredado.

`VerificationSession` reutiliza explícitamente la verificación guiada dentro de
una operación. En cada acierto comprueba bytes, rutas, presencia, listados y
código/configuración. Devuelve copias independientes, restaura lectores al salir
y descarta la caché. No guarda autorizaciones, SQLite, cálculos o resultados en
caché; sus verificadores siguen consultándose. No exige instalar dependencias.

## Pruebas y rendimiento

Se han verificado **29 pruebas distintas** en pases focalizados, sin afirmar un
pase global verde. Cubren memoria de resultados y descartes, errores parciales,
reservas, desconocidos, memoria obsoleta, alteraciones, guardas de bytes con la
misma fecha/tamaño, listados, configuración, limpieza y aislamiento entre hilos.
La integración conserva los validadores y el motor real sobre datos artificiales,
bloqueando red, proveedor, presupuestos heredados y evaluación exterior.

El primer pase fue de 24 aprobadas en 206,23 s. Una integración detectó una
incompatibilidad de los listados `rglob`/`glob` de Python 3.14 con las guardas;
se corrigió sin cambiar los validadores históricos. La integración pasó después
en 177,17 s; la captura inicial de tiempos produjo un aviso de JUnit no fatal.
El pase posterior de las 12 pruebas de sesión pasó en 7,22 s.

Tras añadir los controles de reservas desconocidas, el pase conjunto quedó en
27 aprobadas y una fallida en 481,69 s. El fallo fue una comparación de
`code_sha256`: se editó el nuevo módulo mientras corrían las pruebas. No se
presenta ese pase como verde. La prueba afectada y la de JSON no objeto se
repitieron con fuentes estables: dos aprobadas en 58,39 s. La prueba de JSON no
objeto también tuvo un pase separado aprobado en 18,04 s. La unión de los casos
aprobados en los XML finales contiene 29 pruebas distintas; hay solapamiento.

En la integración final, la primera validación guiada **con seguimiento de
lecturas** tardó 6,43 s y una reutilización protegida de la misma entrada 1,22 s.
La sesión hizo una validación completa y 84 reutilizaciones con guardas. No es
una comparación entre el tiempo de una simulación y el de una consulta, ni una
garantía de rendimiento general. El pase completo incluye preparación y cálculos.

Pytest usa caché desactivada y temporales exclusivos según `AGENTS.md`.
La última suite global ejecutada y comprobada sigue en 1253 pruebas; los pases
de este bloque no se suman a ella como una nueva suite global ejecutada.
Recolección global actual: 1516 pruebas en 1,07 s, sin ejecución global.

## Consumo y límites

Consumo nuevo de investigación de la aplicación: **cero consultas al modelo,
tokens, coste de API y backtests**. Los cálculos reales del motor sobre referencias
artificiales pertenecen exclusivamente a las pruebas. El ámbito compacto heredado
conserva 2262 tokens de entrada, 176 de salida y 0 USD; no representa el total
histórico de la aplicación.

La memoria no modifica la petición inicial congelada ni se envía al modelo.
`future_model_context_integrated` y `automatic_local_cycle_enabled` siguen en
`false`. El contrato inicial de permiso conserva su restricción de una comparación;
este bloque no habilita ensayos adicionales. Autoría y transporte del modelo
siguen sin acreditarse. Las guardas son locales y optimistas, sin firma externa
o bloqueo global frente a cualquier escritor.

Siguiente desarrollo: preparar el contexto renovado con estos resultados y su
control de tamaño; después conectar el transporte local verificado y el controlador
con los presupuestos y revisiones separados. No se repite la reformulación
`2d0040bbd7184c1d9cbde9a8eef3ce3b`, se simulan propuestas reales pendientes o
se considera inédita la evaluación ya conocida.

Sin instalaciones, servicios nuevos, operaciones reales, commits o pushes.
Guía de uso: [memoria de campaña](../docs/CAMPAIGN_MEMORY.md).

## Auditoría del estado real

Auditoría final `d4c89640027443bf8debb71d948f0afd`. Se consultó la campaña real
vacía sin conceder permisos, crear propuestas o calcular candidatas. La memoria
actual se guardó en `.local/campaign-memory/00b3e4e65fde4f59aae5f18c3ec81880`.
La consulta sin caché, la inicial con caché y la repetida devolvieron exactamente
el mismo documento. Tiempos observados: **149,39 s**, **80,50 s** y **4,81 s**,
respectivamente. Una validación guiada completa y siete reutilizaciones protegidas
durante las consultas y guardado/verificación. Son medidas de lectura de esta
campaña vacía; no miden backtests o inferencia del modelo.

Los nueve contadores de acciones bloqueadas quedaron en cero. SQLite conserva sus
bytes, los nueve archivos históricos de reservas sus huellas y las tres raíces de
permisos/ejecuciones siguen sin crearse. `PROJECT_STATUS.md` conserva SHA-256
`53bcda9b54a6cc70a016da47e99d5023f646aed90c3d6277e4d0abf7cc72417e`.

Se conservan 317 copias y referencias previas y se añaden 15: **332 entre 24
inventarios concretos**, sin presentarlas como archivos físicos únicos. El
[inventario](phase4-campaign-memory-2026-10-20/snapshot.json) permite comprobar
copias y originales; contiene el
[registro de auditoría](phase4-campaign-memory-2026-10-20/audit.json) y la
[memoria guardada](phase4-campaign-memory-2026-10-20/memory/memory.json).

La auditoría preliminar `36b4c2155e434dd5a64dc0aa4c8541f2` también conservó los
registros, pero se sustituyó tras añadir el control de protocolo desconocido.
Su borrador está en `.local/campaign-memory-initial-audit-36b4c2155e434dd5a64dc0aa4c8541f2`,
fuera del inventario final. La primera memoria guardada queda obsoleta por el
cambio de código; se conserva y no se reutiliza como contexto vigente.
