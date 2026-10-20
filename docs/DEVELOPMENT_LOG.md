# Registro de desarrollo autónomo

Inicio: 19 de octubre de 2026. Autorizado por el usuario para continuar sin
consultas de validación. No autoriza dinero real, APIs de pago, instalaciones,
servicios nuevos, commits o pushes. FASE 4 sigue abierta.

Punto de partida: 819 pruebas aprobadas. Hay cambios pendientes de pasos
anteriores; se conservan. `PROJECT_STATUS.md` solo se actualizará al cerrar fase.

## Trabajo en curso

Conectar el origen estructurado con revisión técnica, planes, ejecución
controlada y una sesión con presupuesto global. Mantener intactos los módulos
ya vinculados por hashes a las evidencias anteriores.

La propuesta local `18fdf9274baa4b96973b8c2f67dab92b` tiene una salida con
`lag=1` cuyo retardo no explica la hipótesis. No se aprobará automáticamente
para conseguir una simulación. Los ciclos completos se comprobarán primero
con ejemplos artificiales explícitos.

## Punto comprobado: flujo estructurado

- Añadidos `structured_planning.py`, `structured_execution.py` y
  `structured_session.py`, con sus pruebas. No se alteró código de los protocolos
  anteriores vinculado a sus evidencias.
- 863 pruebas aprobadas en suite completa: 44 nuevas en esta integración.
- Revisión local de la propuesta `18fdf9274baa4b96973b8c2f67dab92b`: salida
  pendiente de aclaración. Sesión `fd10b4fe5d4a4201a1bec4f78a1e61ca`, cero
  consultas nuevas, cero simulaciones y cero coste nuevo de API.
- Demostración artificial completa `8b966cb869ab4c46a2ceec99fd706206`: dos
  simulaciones del ejecutor y ningún modelo real. El criterio relativo se
  cumplió con ambas rentabilidades negativas; no es evidencia de una estrategia.
- 52 copias de evidencia y 67 artefactos anteriores conservados sin cambios.
  Véase [comprobación](../reports/phase4-structured-pipeline-2026-10-19.md).

## Punto comprobado: reformulación estructurada

- Añadido `structured_revision.py` y 11 pruebas. Suite completa: **874 aprobadas**.
- Un intento por propuesta y desarrollo, aunque cambien motivo o carpeta.
  No permite reformular una hija. No altera los archivos de propuesta original.
- Registra pregunta real, extracto del motivo y truncamiento, linaje sellado,
  fuentes y consumo nuevo/heredado. Reglas repetidas siguen siendo duplicadas.
- En curso: único intento de comprobación con Ollama local sobre la revisión
  anterior. Señales y backtests desactivados durante esa llamada.

Los registros anteriores no se reinician. Todavía no se ha cerrado FASE 4.

## Último punto comprobado para retomar

Suite completa final: **886 pruebas aprobadas** (67 nuevas desde 819).
Módulos nuevos en esta continuación: `structured_planning`,
`structured_execution`, `structured_session`, `structured_revision` y
`structured_diagnostics`. Pruebas nuevas: 27 del flujo, 18 de sesión, 12 de
reformulación y 10 de diagnósticos. Los costes desconocidos permanecen desconocidos.

La única consulta nueva al modelo local terminó: reformulación
`2d0040bbd7184c1d9cbde9a8eef3ce3b`, hija
`a1bacf3e52c743c2b4088cad0c82ee45`. Eliminó el retardo extra, pero dejó texto
incompleto. Revisión separada `needs_clarification`; sesión hija
`bb2880ffb7c74c37abcece9c5275ffc2`, cero simulaciones, cero llamadas nuevas de
esa sesión y sin bloqueo activo. El intento de reformular este origen está
consumido y la hija no puede iniciar otra reformulación.

Consumo nuevo real de esta continuación: una generación local, 1289 tokens de
entrada, 239 de salida, 62,952 s y 0 USD de API. El linaje incluye además la
generación original anterior (1257/248 tokens); no se volvió a consumir. Solo
se ejecutaron dos backtests en la demostración artificial, sin modelos reales;
ninguna estrategia se simuló sobre datos de mercado reales durante esta continuación.

Se añadieron ayudas estáticas de texto, retardos y calentamiento, que no aprueban
ni calculan rentabilidad. Un recuento de hipótesis en la justificación hija
decía 160; el valor exacto es 159. Hay fe de erratas vinculada por hash, sin
reescribir la revisión sellada. La decisión pendiente permanece.

Evidencia nueva: 52 copias del flujo y 31 de reformulación/diagnóstico, con
hashes y referencias originales. [Reformulación y revisión](../reports/phase4-structured-revision-2026-10-19.md).
Los artefactos y fuentes anteriores siguen conservados. Sin commits, pushes,
dependencias, servicios nuevos, APIs de pago, TradingView o dinero real.
`PROJECT_STATUS.md` no se modificó; FASE 4 sigue abierta.

Siguiente trabajo útil: prevenir descripciones incompletas sin completar texto
del modelo por inferencia, sin relajar la revisión y sin repetir este linaje.
Los registros ya sellados incluyen hashes de código: conservar esos módulos
o versionar explícitamente nuevas entradas, sin invalidar silenciosamente la evidencia.

## Seguimiento solicitado

Automatización de este mismo chat: `continuar-trading-ai-e-informar-al-renovar-cuota`,
activa cada 15 minutos. Continúa una tarea útil cuando haya cuota, conserva
avances aquí y guarda silencio sobre estados no accionables. Al observar una
ventana renovada con uso disponible, debe entregar el informe solicitado y
pausarse para no repetirlo. Requiere ordenador y aplicación en funcionamiento.

Referencia de cuota observada: ventana primaria usada al 67%, reinicio
`1792437542` (19/10/2026 19:19:02 UTC); secundaria al 26%, reinicio
`1793003653`. Estos valores no equivalen a cuota agotada ni garantizan que la
ejecución coincida exactamente con el instante de renovación.

## Reanudación e informe

Este archivo conserva cambios, pruebas, limitaciones y siguiente trabajo en un
punto comprobado. No hay un disparador nativo de renovación de cuota; el
seguimiento programado comprueba disponibilidad. Si se interrumpe, al retomar
se preparará el informe usando este registro y el estado real de Git.

## Continuación programada — 19/10/2026, disparador 16:32 UTC

Se leyeron instrucciones, registro y Git. `main` sigue en `ed31448`; se conservan
todos los cambios pendientes. La cuota permitía uso ordinario: primaria al 71%
al inicio y 76% al final, con el mismo reinicio `1792437542`; secundaria 27% y
28%, mismo reinicio `1793003653`. Son datos de cuenta, no una medición exacta de
tokens de esta tarea. No se ha observado agotamiento ni renovación. No procede
todavía el informe de renovación ni pausar el seguimiento.

Se añadió `structured_brief`, sin modificar los módulos ya sellados. Describe
reglas completas desde campos validados, con origen Python explícito; conserva
el texto original del modelo sin inferir su continuación. Genera un informe y
registro con hashes verificables, cero consultas y ninguna aprobación implícita.
El uso está documentado en `STRUCTURED_WORKFLOW.md`.

Pruebas nuevas: **18 aprobadas** en 1,19 s. Suite completa: **904 aprobadas** en
78,61 s, usando caché desactivada y temporal exclusivo según `AGENTS.md`.
Cubren operadores, indicadores, ventanas, retardos, conservación de prosa,
texto literal, aislamiento y detección de alteraciones de artefactos.

Demostración de solo descripción:
`.local/structured-briefs/b496a0e422944772964c2a948124156c`, sobre la hija
`a1bacf3e52c743c2b4088cad0c82ee45`. Las reglas EMA20/SMA60 se describen sin
frases incompletas; la hipótesis real sigue intacta y con 159 caracteres.
La sesión `bb2880ffb7c74c37abcece9c5275ffc2` sigue en `needs_clarification`,
cero reserva de simulaciones y sin bloqueo activo. No se reutilizó ni encadenó
la reformulación `2d0040bbd7184c1d9cbde9a8eef3ce3b`.

Consumo nuevo de proveedores del proyecto: cero llamadas, cero tokens y 0 USD
de API. Cero señales y backtests. El consumo heredado de la hija (1289/239) y
del origen anterior (1257/248) permanece registrado, sin volver a consumirlo.
La cuota de Codex es independiente de ese contador del proyecto.

La comprobación bloqueó red, proveedores, señales, simulaciones y datos de
evaluación exterior; conservó 24 archivos locales de origen/sesión. Se
verificaron las 150 copias históricas y sus originales. Once copias nuevas
incluyen auditoría, estado y fuentes: [evidencia](../reports/phase4-structured-brief-2026-10-19.md).

Error menor: `python -m runpy <archivo>` rechazó el nombre relativo antes de
ejecutar la comprobación. Se corrigió con `runpy.run_path`, sin consumo ni
intentos intermedios. No quedan pruebas fallidas.

Limitación: esta ayuda resuelve la lectura mecánica, no la calidad ni coherencia
de la hipótesis del modelo. Siguiente trabajo útil: tratamiento previo y
comprobable de descripciones incompletas en propuestas nuevas, conservando las
decisiones y presupuestos ya consumidos. No simular esta hija pendiente.

FASE 4 continúa abierta. `PROJECT_STATUS.md` no se ha tocado. Sin commits,
pushes, instalaciones, servicios nuevos, API de pago, TradingView o dinero real.

## Continuación programada — 19/10/2026, disparador 16:47 UTC

Lectura inicial de `AGENTS.md`, este registro y Git. Se conserva `main` en
`ed31448` con todos los cambios previos. Cuota: uso ordinario permitido, primaria
77% al inicio y 80% en la comprobación posterior, mismo reinicio `1792437542`.
Secundaria 28%; reinicios observados `1793003653` y `1793003654`. La primaria no
se ha renovado ni se ha informado un límite alcanzado. No se entrega aún el
informe de renovación ni se pausa el seguimiento.

Se añadió `structured_draft`, prototipo sin modelo de un contrato con solo
`entry` y `exit`. No solicita prosa libre; Python describe las reglas completas
con origen explícito. No atribuye título o hipótesis al modelo ni completa los
textos existentes. Conserva entrada exacta, SHA-256, reglas normalizadas,
informe, eventos y código verificable. El origen de un archivo externo queda
sin atribuir; su consumo heredado permanece desconocido.

El borrador no fija contexto de investigación, no consulta duplicados ni puede
adoptarse en una sesión. `eligible_for_session` y `executable` son falsos. Se
rechazan controles, resultados y código libre. No se cambió ningún módulo ya
sellado, propuesta, revisión o presupuesto anterior. El esquema y CLI están
documentados en `STRUCTURED_DRAFTS.md`.

Pruebas: 36 focalizadas aprobadas en 0,55 s; se añadió después una prueba de
identidad numérica. Suite completa: **941 aprobadas en 79,21 s**, con las 37
nuevas incluidas, temporal exclusivo y caché desactivada. Sin errores pendientes.

Demostración artificial sin mercado:
`.local/structured-drafts/cf542656670d4bb4b5b00627bf5dfd55`. Compara una referencia
con un umbral; no calcula señales o rentabilidad. Se bloquearon red, creación
de proveedor, señales, backtests, XML, desarrollo y reservas. Se conservaron 29
archivos de reservas y del linaje pendiente. El intento `2d0040bbd7184c1d9cbde9a8eef3ce3b`
no se reutilizó y su hija no se simuló ni reformuló.

Consumo nuevo: cero consultas de proveedor, cero tokens de proveedor y 0 USD
de API. Cero simulaciones nuevas de investigación. `source_usage` se conserva
desconocido en este contrato de entrada externa; no se confunde con `new_usage`,
que contiene los ceros comprobados. Los consumos reales anteriores registrados
(incluidos 1257/248 del origen y 1289/239 de su hija) no se vuelven a consumir.
Codex sigue usando la cuota de la aplicación, separada de estos contadores.

Se verificaron 161 copias históricas y sus originales. Hay siete copias nuevas
con auditoría y fuentes: [comprobación](../reports/phase4-structured-draft-2026-10-19.md).
No se han encontrado errores en la implementación o en su comprobación.

Limitación: el contrato compacto aún no se conecta al investigador, y no prueba
ahorro de tokens o mejora de la calidad real de generación. Siguiente paso útil:
preparar su contexto de investigación y memoria de reglas compartida, de forma
que un cambio de protocolo no permita repetir intentos o borrar descartes,
antes de habilitar cualquier generación. No actuar sobre la hija pendiente.

FASE 4 continúa abierta; no se modifica `PROJECT_STATUS.md`. Sin commits,
pushes, instalaciones, servicios nuevos, API de pago, TradingView o dinero real.

## Continuación programada — 19/10/2026, disparador 17:02 UTC

Se leyeron instrucciones, registro y Git. `main` continúa en `ed31448` y se
conservan todos los cambios pendientes. Cuota primaria observada: 81% al inicio,
85% en la comprobación posterior; mismo reinicio `1792437542`. Secundaria 28%
y 29%, reinicio `1793003653`. Uso ordinario permitido. No hay renovación de
primaria o límite alcanzado observado; aún no corresponde el informe solicitado.

Se añadió `structured_draft_context`, separado de la vista previa y del motor.
Obtiene del registro congelado objetivo, controles y metadatos de desarrollo;
captura ideas heredadas y motivos, reglas y reservas del registro compartido.
No selecciona por rendimiento. Las reservas sin propuesta terminada también
permanecen consumidas. No crea o modifica reservas, propuestas o decisiones.

Puede contrastar un borrador por identidad normalizada: `duplicate_or_reserved`
impide considerarlo libre por cambiar de contrato. La ausencia en la captura
solo se informa como tal; no prueba novedad o disponibilidad de otros controles.
`generation_ready`, `eligible_for_session` y `executable` permanecen falsos.
El consumo externo desconocido se conserva desconocido.

Pruebas focalizadas finales: **22 aprobadas en 3,15 s**. Suite completa:
**963 aprobadas en 84,23 s**, con temporal exclusivo y caché desactivada según
`AGENTS.md`. Incluye reserva interrumpida, duplicados entre formatos, motivos
heredados, ámbitos, cambios concurrentes, aislamiento y fuentes alteradas.
No quedan pruebas fallidas.

Comprobación real de contexto conocido, vinculada al ejemplo artificial previo:
`.local/structured-draft-contexts/2d35c3461d234499a1c9300470f6f130`. Captura cuatro
ideas heredadas, dos reglas registradas y dos reservas consumidas. La identidad
del ejemplo no aparece en esas dos reservas; no se aprueba ni se simula.
Se bloquearon red, proveedores, señales, backtests y evaluación exterior, y se
conservaron 29 archivos protegidos del linaje y de reservas. La reformulación
`2d0040bbd7184c1d9cbde9a8eef3ce3b` no se repitió ni encadenó; la hija sigue sin
simularse y no se ha reabierto su sesión.

Consumo nuevo: cero consultas o tokens de proveedor, 0 USD de API y cero nuevas
simulaciones de investigación. Los consumos reales previos (1257/248 del origen,
1289/239 de su hija) siguen registrados sin volver a consumirlos. La cuota de
Codex es independiente. El contexto no suma costes anteriores no atribuidos.

Se verificaron 168 copias históricas y sus originales sin cambios. Once copias
nuevas conservan contexto, memorias, reservas y auditoría:
[comprobación](../reports/phase4-structured-draft-context-2026-10-19.md).
No se cambió ningún módulo ya sellado. La CLI de preparación y verificación
está documentada en `STRUCTURED_DRAFTS.md`.

Error exploratorio: se buscó `proposal.json` en el registro congelado; su archivo
es `frozen.json`. Se corrigió la lectura sin alterar nada o consumir intentos.
No hubo errores de implementación o pruebas pendientes.

Limitación: la copia es histórica, no una garantía de memoria vigente para una
generación futura. Todavía no recopila decisiones de revisión estructurada.
Siguiente tarea útil: conservar también sus estados y motivos comprobados en
la preparación del contexto, sin reabrir sesiones, perder decisiones o aprobar
equivalencia de texto automáticamente. No actuar sobre propuestas pendientes.

FASE 4 permanece abierta; `PROJECT_STATUS.md` no se modifica. Sin commits,
pushes, instalaciones, servicios nuevos, APIs de pago, TradingView o dinero real.

## Continuación programada — 19/10/2026, disparador 17:17 UTC

Se leyeron instrucciones, registro y Git. `main` sigue en `ed31448` con todos
los cambios pendientes conservados. Cuota primaria 86% al inicio y 91% en la
comprobación posterior; mismo reinicio `1792437542`. Secundaria 29% y 30%,
reinicio `1793003654`. Uso ordinario permitido. No se ha observado agotamiento
ni renovación de primaria; el informe de renovación todavía no corresponde.

Se añadió `structured_review_memory`, memoria complementaria que verifica
reservas, propuestas y revisiones registradas por las sesiones del mismo
desarrollo. Conserva decisión, motivo, revisor, comprobaciones y consumo de
origen sin reabrir acciones o consultar el cierre financiero de la sesión.
Una aceptación técnica no se interpreta como cierre completo o rentabilidad.
Un cierre consumido sin revisión registrada sigue consumido.

El contexto base debe contener las reservas de las propuestas recopiladas.
Se limita el registro a 128 reservas globales, sin descartar fuentes en silencio.
El alcance no incluye revisiones independientes fuera del registro ni garantiza
sesiones posteriores. Si una sesión cambia de etapa, su captura puede requerir
renovación. No se habilita generación, aprobación o simulación.

Pruebas: primera ejecución focalizada, 19 aprobadas en 7,81 s. Se añadió después
un caso de consumo heredado desconocido. Suite completa: **983 aprobadas en
91,50 s**, incluidas 20 nuevas, con temporal exclusivo y caché desactivada.
Sin errores de implementación o pruebas pendientes.

Captura real de solo lectura:
`.local/structured-review-memory/ad12b5680d6a4cb3aab5fa7d6f0fec7a`. Preserva las
dos revisiones `needs_clarification` y sus cierres consumidos, sin reabrirlas.
El motivo original de la hija dice 160 caracteres; se conserva como texto no
verificado del revisor junto a la longitud calculada 159 y la fe de erratas
existente. No se corrige silenciosamente ni se completa la hipótesis del modelo.

Consumo nuevo: cero consultas y tokens de proveedor, 0 USD de API y cero nuevas
simulaciones de investigación. Heredado de ambas propuestas: dos consultas,
2546 tokens de entrada y 487 de salida (1257/248 del origen y 1289/239 de la
hija), ya consumidos anteriormente. Se copian sus registros sin volver a
generarlos. Los valores desconocidos permanecen desconocidos. La cuota de Codex
es independiente de estos contadores del proyecto.

Se bloquearon proveedores, red, acciones de sesión, señales, backtests,
verificación de resultados de ejecución, evaluación exterior y `outcome.json`.
No se leyeron archivos financieros de las sesiones. Se conservaron 29 archivos
protegidos. La reformulación `2d0040bbd7184c1d9cbde9a8eef3ce3b` no se repitió
o encadenó, y ninguna propuesta pendiente se simuló.

Se verificaron 179 copias históricas y sus originales. Hay 16 copias nuevas de
memoria, revisiones, reservas, auditoría y fe de erratas:
[comprobación](../reports/phase4-structured-review-memory-2026-10-19.md).
No se modificó ningún módulo ya sellado; el uso está documentado en
`STRUCTURED_DRAFTS.md`.

Siguiente tarea útil: preparar una petición compacta inspeccionable, sin
enviarla, usando contexto y motivos heredados como datos no fiables. Mantener
los permisos cerrados y los límites de intentos existentes; no actuar sobre
propuestas pendientes. Aún falta la integración de generación controlada.

FASE 4 permanece abierta; `PROJECT_STATUS.md` no se modifica. Sin commits,
pushes, instalaciones, servicios nuevos, APIs de pago, TradingView o dinero real.

## Continuación programada — 19/10/2026, disparador 17:32 UTC

Se leyeron instrucciones, registro y Git, conservando todos los cambios.
`main` sigue en `ed31448`. Cuota primaria 93% al inicio y 95% en la comprobación
posterior, uso ordinario permitido. Reinicios observados `1792437542` y
`1792437543`: oscilación de un segundo, con la ventana todavía pendiente de
reinicio a las 19:19 UTC. No constituye evidencia de una ventana renovada.
Secundaria 30% y 31%, reinicio `1793003654`. No se observó agotamiento; no
corresponde todavía entregar el informe de renovación o pausar el seguimiento.

Se añadió `structured_draft_request`, preparación inspeccionable sin envío.
Conserva objetivo y controles del registro y todo el historial capturado, con
motivos tratados como datos no fiables. Solo pide el contrato compacto de
reglas; no completa prosa del modelo. El mensaje de sistema es fijo. Si el
JSON supera 12.288 bytes, falla sin omitir entradas o truncar motivos.

Suite completa: **993 pruebas aprobadas en 101,27 s**, incluidas 10 nuevas,
con temporal exclusivo y caché desactivada. Comprueban separación de roles y
datos, cobertura, ausencia de envío o acciones, tamaño, integridad y CLI.
No quedaron errores de implementación o pruebas pendientes.

Petición real preparada, no enviada:
`.local/structured-draft-requests/1646833181eb44c386eb32872f245afa`.
Ocupa 10.970 bytes e incluye cuatro ideas, dos reglas, dos reservas consumidas
y dos revisiones. Los tokens son desconocidos y no se ha verificado el encaje
en el contexto de un proveedor. `submitted`, `provider_configured` y
`generation_ready` permanecen falsos. No se creó una reserva de generación.

Consumo nuevo: cero consultas o tokens de proveedor, 0 USD de API y cero nuevas
simulaciones de investigación. El consumo anterior sigue en sus fuentes
(1257/248 del origen y 1289/239 de la hija), sin volver a consumirlo. La cuota
de Codex es independiente de estos contadores.

Se bloquearon proveedores, red, acciones, señales, backtests, evaluación exterior
y resultados financieros de las sesiones. Se conservaron 29 archivos protegidos.
La reformulación `2d0040bbd7184c1d9cbde9a8eef3ce3b` no se repitió o encadenó,
ni se reformularon o simularon propuestas pendientes. Se verificaron 195 copias
históricas y sus originales; seis copias nuevas conservan petición y auditoría:
[comprobación](../reports/phase4-structured-draft-request-2026-10-19.md).
No se modificaron módulos ya sellados.

Siguiente tarea útil: comprobar vigencia del contexto antes de cualquier futura
reserva o generación. La preparación actual es histórica y no demuestra que
incluya nuevos registros, que quepa en un modelo o que reduzca consumo real.
No enviar esta petición ni actuar sobre propuestas pendientes automáticamente.

FASE 4 permanece abierta; `PROJECT_STATUS.md` no se modifica. Sin commits,
pushes, instalaciones, servicios nuevos, APIs de pago, TradingView o dinero real.

## Continuación programada — 19/10/2026, disparador 17:47 UTC

Leídos instrucciones, registro y Git; `main` sigue en `ed31448`, con todos los
cambios pendientes conservados. Cuota primaria 98% al inicio y 99% después,
reinicio `1792437542`; secundaria 31%, reinicio `1793003654`. Uso ordinario
permitido: no se ha observado límite alcanzado ni renovación. No se afirma
agotamiento y todavía no corresponde el informe de renovación.

Tarea acotada: auditoría de vigencia con verificadores existentes, sin cambios
de producción. La petición sin enviar coincide ahora con memoria de ideas,
reglas, reservas de reglas y reservas de sesiones: cuatro comparaciones
satisfactorias. Se verificaron 201 copias históricas y sus originales. Cuatro
copias nuevas conservan auditoría, sello, eventos y script con hashes:
[evidencia](../reports/phase4-structured-readiness-2026-10-19.md).
Registro `.local/structured-readiness-audits/a0e47a24646b421e9e689d7a28e46f23`.

No se repitió pytest al no cambiar producción o pruebas: último resultado
comprobado **993 aprobadas en 101,27 s**, con temporal exclusivo y sin caché.
La auditoría terminó sin errores. Consumo nuevo de proveedor: cero consultas,
0 USD de API y cero simulaciones nuevas. El consumo heredado permanece en sus
fuentes, sin volver a consumirlo. Codex usa su cuota separada de aplicación.

Esta vigencia es puntual, sin autorización de generación. Pendientes al retomar:
comprobación atómica de vigencia al reservar, límites reales de contexto del
proveedor y reserva explícita con procedencia de la futura consulta. La petición
sigue sin enviar y no se actuará sobre propuestas pendientes o el linaje
consumido `2d0040bbd7184c1d9cbde9a8eef3ce3b`.

FASE 4 sigue abierta; `PROJECT_STATUS.md` intacto. Sin commits, pushes,
instalaciones, servicios nuevos, API de pago, TradingView u operaciones reales.


## Renovación comprobada e informe — 19/10/2026, disparador 19:32 UTC

Uso ordinario permitido, primaria 0% y nuevo reinicio 1792456351 frente a la
referencia 1792437542; secundaria 31%, reinicio 1793003654. Renovación
comprobada. La lectura previa registrada fue 99% con uso permitido; no se
afirma que se observara agotamiento.

Se verificaron Git y el registro: main sigue en ed31448 con los cambios
pendientes conservados. Verificación final de solo lectura: 205 copias y sus
originales intactos; petición de 10.970 bytes sin enviar; ambas sesiones
needs_clarification, sin bloqueos activos ni reserva de simulaciones.
Última suite completa: 993 aprobadas en 101,27 s, sin cambios posteriores
de producción o pruebas. No se repitió pytest ni se llamó a un modelo.

Consumo nuevo de esta verificación: cero consultas, 0 USD de API y cero
backtests. Desde 886 no hubo consultas nuevas. En el desarrollo desde 819
hubo una consulta local nueva (1289/239 tokens), frente a la heredada
(1257/248), ambas de 0 USD de API. Los costes desconocidos se conservan.

Se prepara la entrega del [informe solicitado](../reports/phase4-autonomous-summary-2026-10-19.md)
y la pausa del seguimiento, conservando el resto de su configuración.
FASE 4 continúa abierta; PROJECT_STATUS.md permanece intacto. Sin commits,
pushes, instalaciones, servicios nuevos, API de pago o dinero real.

Pausa confirmada mediante automation_update y lectura ASCII segura de
automation.toml: status=PAUSED. Se conservaron nombre, prompt, frecuencia,
destino, identificador y fecha de creación; solo cambian estado y updated_at.
Durante la verificación se detectó una conversión de consola cp1252 que
alteraba tildes al serializar metadatos. Se restauro el texto original y
se compararon todos los campos; el prompt final no contiene reemplazos.
No se modificó código de Trading AI ni se consumieron consultas de proveedor.
Se entrega el informe solicitado y se deja pausado el seguimiento.

## Nueva continuacion autorizada - 20/10/2026

El usuario pide continuar autonomamente y preparar informe cuando vuelva.
Se mantiene pausada la automatizacion anterior. Git estaba limpio en f9bb417
(commit realizado fuera de esta continuacion); se conserva ese estado.
Cuota inicial: uso ordinario permitido, primaria 8%, reinicio 1792456351.

Primer incremento: structured_freshness y structured_generation, sin alterar
modulos sellados. Vigencia por doble lectura de las cuatro memorias/reservas,
huella ligada a la peticion y reserva exclusiva por datos de desarrollo y par.
Un fallo posterior a reservar conserva el intento; no existe comando de
reserva o envio en la CLI. Transporte y generacion permanecen deshabilitados.
La doble lectura es optimista: no se presenta como transaccion atomica con
los escritores historicos. No se reserva el intento real del proyecto.

Pruebas focalizadas: 14 de vigencia aprobadas en 18,55 s y 15 de reserva
aprobadas en 23,51 s. Suite completa pendiente tras finalizar el incremento.
Se corrigio un nombre de fixture reservado por pytest y dos literales
al renombrarlo; los fallos eran de las pruebas nuevas, sin llamadas o
intentos reales consumidos. Ultima suite global anterior: 993 aprobadas.

Se estudia la proteccion de contexto del proveedor local con documentacion
oficial. No se ha consultado un modelo, iniciado servicio o instalado nada.
FASE 4 abierta; sin cambios en PROJECT_STATUS.md, commits, pushes o dinero real.

### Punto comprobado de esta continuacion

Suite global de vigencia y reserva: 1022 aprobadas en 162,16 s.
CompactOllamaProvider anade 28 pruebas focalizadas aprobadas en 0,24 s;
la suite anterior se habia recogido antes de crear esas pruebas.
Solo se hizo una peticion local GET /api/version: Ollama existente 0.40.6.
Cero generaciones reales, cero backtests de investigacion y 0 USD de API.
No se inicio o actualizo ningun servicio. Las reservas nuevas solo se
ejercitaron con fixtures; el intento compacto real sigue sin consumirse.

El adaptador nuevo solicita truncate=false y shift=false en la version
0.40.6 comprobada, conserva errores y uso desconocido, y rechaza modelos
remotos, digest cambiado, metricas ausentes o respuestas incompletas.
No se modifica ai.py, ningun modulo sellado o el linaje 2d0040bbd7184c1d9cbde9a8eef3ce3b.
Fuentes oficiales: https://docs.ollama.com/api/chat y las etiquetas v0.40.6
de https://github.com/ollama/ollama (api/types.go, server/routes.go).

Siguiente incremento: conectar una unica llamada compacta mediante reserva,
registrando respuesta original y consumo antes de validar. Todavia no hay
envio; las propuestas nuevas exigiran revision y no se simularan por defecto.

### Controlador compacto y separacion de revision - 20/10/2026

Suite global comprobada antes del ultimo incremento: 1073 aprobadas en 191,66 s.
El fallo inicial de una prueba nueva confundia los campos de metadatos de la
descripcion con frases; se corrigio la prueba y esa suite paso completa.

Se anaden compact_candidate, compact_review y compact_plan: una consulta local
con reserva, JSON original antes de interpretar, duplicados compartidos, revision
declarada independiente y plan con controles congelados. Todavia no hay consulta
real ni revision o plan real compacto. El adaptador ahora conserva ademas la
respuesta bruta si el proveedor la declara incompleta; no la acepta ni reintenta.

Pruebas focalizadas tras ese cambio: 72 aprobadas y un fallo de expectativa
en una prueba nueva que anadia un espacio al checksum. El verificador historico
tolera el espacio final por diseno; la prueba se corrigio para modificar el
checksum, sin cambiar verificadores sellados. Se comprueban ahora revision y plan.
Nueva suite global pendiente al finalizar esos incrementos.

Documentacion de uso y limites: docs/COMPACT_CANDIDATES.md. Se conserva el presupuesto
de una generacion por datos y par; el linaje de reformulacion agotado no se toca.
La revision no da resultados y el plan no tiene todavia ejecutor compacto.
La automatizacion sigue pausada; informe de situacion cuando vuelva el usuario.
FASE 4 abierta; PROJECT_STATUS.md intacto. Sin commits, pushes, instalaciones,
servicios nuevos, consultas de pago o dinero real.

Revision y plan: 30 pruebas focalizadas aprobadas en 77,27 s. La nueva suite
global esta en curso. Se comprobaron de solo lectura las 205 copias historicas
de este linaje y sus originales: intactos. Un primer auxiliar de auditoria
intentaba tratar todos los formatos antiguos de snapshot como mapas; fallo
antes de enviar o reservar. Se corrigio para usar los once inventarios ya
documentados de esta continuacion, sin alterar los originales.

.gitattributes conserva ahora tambien los bytes de trading_ai/*.py para evitar
que una conversion automatica de saltos de linea invalide los registros ligados
al codigo. Los modulos existentes no cambian de contenido; git diff --check pasa.
Se mantiene en cero el numero de generaciones reales nuevas hasta este punto.

Suite completa posterior a todos los incrementos anteriores: 1104 aprobadas en
268,20 s, cache desactivada y temporal exclusivo. Se inicia una sola comprobacion
local del contrato compacto nuevo, separada de las revisiones agotadas. El auxiliar
bloquea rutas de senales, backtests y evaluacion exterior; verificara de nuevo
las 205 copias y sus originales. No se reintentara un error o duplicado.

### Consulta compacta real conservada - 20/10/2026

Una consulta local completada: .local/compact-candidates/ffbda220799941128d4bb654cb6f2288.
Estado duplicate_rules; repite entrada EMA20/SMA60 lag=0 y salida cruzada lag=1
del origen 18fdf9274baa4b96973b8c2f67dab92b. No se aprueba o simula. Las frases
completas son derivadas por Python, sin hipotesis inventada o atribuida al modelo.
Consumo nuevo: 2262 tokens de entrada y 176 de salida, 0 USD de API. Seis consultas
de metadatos del controlador mas una comprobacion anterior de version. Sin
reintentos; presupuesto compacto consumido aunque el resultado sea duplicado.

Auditoria 8d6b96edd60e40829a41e49ed7ba0cb5: cero accesos exteriores, senales,
backtests o acciones de sesion. 205 copias historicas y originales intactos;
20 copias nuevas verificadas. Evidencia: reports/phase4-compact-candidate-2026-10-20.md.
El consumo heredado del linaje (1257/248 y 1289/239) se conserva sin repetirlo.
No se toca el intento 2d0040bbd7184c1d9cbde9a8eef3ce3b ni se libera una reserva.

Siguiente incremento: compact_execution conecta un plan aceptado con el motor
existente y la reserva comun de calculos; se prueba unicamente con fixtures.
La candidata real duplicada no admite revision aceptada ni plan. No hay cambios
en PROJECT_STATUS.md ni acciones de Git; la automatizacion sigue pausada.

### Ejecutor y memoria compacta - 20/10/2026

compact_execution pasa 14 pruebas focalizadas en 97,64 s con datos artificiales:
dos cuentas como maximo, reserva comun, concurrencia, lectura sin recalculo,
fallos parciales y rechazo de candidatas sin plan aceptado. No se ejecuta la
candidata real duplicada. Los calculos siguen en rule_execution/backtesting;
el controlador nuevo no implementa una contabilidad alternativa.

compact_history pasa 16 pruebas focalizadas en 58,58 s. Conserva estados,
reglas, motivos de revision y consumos heredados, incluidos desconocidos;
no lee resultados financieros ni concede permisos. Se anaden ocho comprobaciones
ligeras de consumo incompatible antes de iniciar otra suite global, ahora en curso.
La memoria debe renovarse si cambian sus intentos o revisiones; no se presenta
una captura anterior como historial actual. Falta proyectarla en una peticion.

El plan compacto nuevo indica execution_requires_explicit_tool=true. Ese modulo
todavia no tenia artefactos reales sellados; no cambia los modulos o huellas
de la candidata real archivada. Se mantiene el presupuesto compacto consumido,
cero simulaciones nuevas de investigacion y 0 USD nuevo de API tras la unica
consulta local registrada. FASE 4 abierta, sin cambios de PROJECT_STATUS.md.

### Peticion futura comprobada, sin permiso de envio - 20/10/2026

Suite global: 1142 aprobadas en 425,38 s. La extension compact_request, creada
despues de recoger esa suite, pasa 10 pruebas focalizadas en 88,65 s. Se ha
aclarado el indicador de la memoria como compact_execution_results_read=false:
los verificadores de referencia si comprueban registros historicos de desarrollo.
Se esta ejecutando la suite completa posterior a ambos cambios.

Captura real .local/compact-history/a6bb9a6824904602aa0014905adfb31b y peticion
.local/compact-requests/c787e8461793402788239222e3b11552, 11818 bytes, sin envio,
proveedor o permiso nuevo. Auditoria 68f270d321dd4702a1d5bb1e28113ab4: cinco rutas
prohibidas con cero invocaciones; 225 copias previas y sus originales intactos,
11 copias nuevas verificadas. Consumo nuevo de esta comprobacion cero; conserva
el heredado 2262/176 sin repetirlo. Sigue desconocido el recuento de tokens de
la nueva peticion. Evidencia: reports/phase4-compact-memory-request-2026-10-20.md.

Se anade compact_status, consulta de tres lineas sin escrituras o acciones. Su
primer pase dio 10 aprobadas y un fallo: el subtotal de API para el ambito vacio
aparecia desconocido. Se corrigio para indicar cero solo cuando no hay intentos
en ese ambito; los intentos con uso desconocido conservan None. Se repiten sus
11 pruebas focalizadas. No se han consultado mas modelos o simulado propuestas.

compact_status: 11 aprobadas en 39,75 s tras la correccion. El comando normal
muestra tres lineas; separa propuesta/revision de ejecuciones no inspeccionadas.
La suite global en curso se recogio antes de crear este modulo de lectura.
No se presenta la suma de grupos como una suite global ya ejecutada.

Siguiente desarrollo independiente de nuevos presupuestos: preparar diagnosticos
por periodos conocidos para una candidata con revision aceptada, fijando bloques,
controles y limites antes de calcular. No se usara el duplicado real ni se
presentaran estos periodos como evaluacion independiente o walk-forward de
seleccion si no hay una seleccion previa real. Continuan sin autorizarse API
de pago, instalaciones, servicios, commits, pushes o dinero real.

Suite completa posterior a la peticion extendida: 1152 aprobadas en 524,60 s.
La recogida precede a compact_status y compact_periods: estos pasan aparte sus
11 pruebas (39,75 s) y 17 pruebas (65,65 s), respectivamente. No se suma como
si hubiese pasado ya una suite global de 1180 pruebas.

compact_periods prepara dos o tres bloques mecanicos de un plan aceptado, con
las mismas reglas y controles, todas las observaciones y cuentas independientes.
Cero calculos, seleccion o evaluacion exterior. Fija como maximo seis backtests
futuros y una identidad de campana que no cambia al variar el numero de bloques.
No se aplica al duplicado real. Documentacion: docs/PERIOD_DIAGNOSTICS.md.

Consulta real compact_status comprobada con Python -X utf8: duplicado bloqueado,
presupuesto consumido y cero llamadas o simulaciones de la lectura. En la primera
captura de consola sin ese indicador, la tuberia cp1252 mostro tildes mal; los
archivos UTF-8 estaban intactos y la repeticion con -X utf8 se vio correctamente.
Cuota observada: primaria 61%, uso ordinario permitido; no hay agotamiento
observado. La automatizacion sigue pausada. Se continuara con el ejecutor de
periodos, exclusivamente mediante pruebas artificiales mientras no exista
una candidata real revisada y aceptada.

compact_period_execution pasa 14 pruebas focalizadas en 144,17 s. Reserva una
campana y todos los calculos de sus bloques antes del primer backtest; comparte
el registro individual con los otros ejecutores. Conserva resultados parciales,
bloquea concurrencia/repeticion y verifica sin recalcular. Usa el motor existente,
mantiene todos los bloques y no compone rentabilidades o selecciona un ganador.
Pruebas con datos artificiales; ninguna simulacion nueva de investigacion real.
Se actualiza el plan de periodos, aun sin artefactos reales, para exigir una
herramienta explicita de ejecucion. Pendiente suite global con los nuevos modulos
de estado y periodos. Ultima global verificada sigue siendo 1152 aprobadas.

Verificador de integridad evidence: 19 pruebas aprobadas en 0,21 s antes de
anadir el rechazo de rutas de unidad Windows tambien en otros sistemas; la
suite global posterior incorpora esa comprobacion. Verificacion real: 236 copias
y 236 referencias originales correctas, 1876050 bytes leidos, cero consultas y
backtests. Modo copias permite comprobar los archivos de Git sin exigir .local;
no restaura sesiones o verifica semantica, rendimiento o autenticidad criptografica.
Limites y uso en docs/EVIDENCE_CHECKS.md. En curso suite global con todos los
incrementos hasta este verificador. Sin cambios a productor/artefactos compactos
reales, presupuestos, PROJECT_STATUS.md o Git publicado.

### Cobertura estructural sin consultas nuevas - 20/10/2026

Suite completa de estado, periodos y verificador de evidencia: 1213 aprobadas
en 789,22 s. Posteriormente rule_coverage paso 19 pruebas iniciales en 57,53 s y
20 en 63,07 s tras comprobar el limite sobre el JSON almacenado con indentacion.
No es una deteccion de equivalencia semantica: conserva tipos, roles y operadores
en la plantilla, conserva los numeros originales por separado y no aprueba nada.

Cobertura real .local/rule-coverage/048d7ee5c7da4292b09f2e952882626a:
3 registros, 2 identidades sin nombre y 1 plantilla; 1 repeticion exacta dentro
del ambito. Tipos directos EMA/SMA. No se analizan ideas de texto libre ni se
declaran estrategias mejores a partir de los tipos no observados. Auditoria
96bbeeae8f2a427faca1f1e187f2a71b: 236 copias previas y originales intactos,
8 copias nuevas; cero proveedor, senales, backtests y evaluacion exterior.
Evidencia: reports/phase4-rule-coverage-2026-10-20.md. Presupuesto consumido intacto.

Se prueba ahora guided_compact_request: anade esa cobertura mecanica a la
peticion futura sin cambiar controles, eliminar historial o habilitar envio.
No se modifica ningun productor ya sellado. Ultima cuota observada: primaria
77%, uso ordinario permitido. No se ha observado agotamiento. FASE 4 abierta;
sin cambios de PROJECT_STATUS.md, commits, pushes, instalaciones o dinero real.

### Peticion guiada, integracion y perfil - 20/10/2026

guided_compact_request pasa 9 pruebas en 138,03 s. Peticion real preparada sin
envio en .local/guided-compact-requests/1a1d0783778243ac989ca1ab3fc49911:
12142 bytes, frente al limite 12288. Auditoria 277e89e01e34425481f218e4b42ff6c6:
244 copias previas y originales intactos, 8 nuevas; cuatro rutas bloqueadas a
cero. El presupuesto consumido sigue intacto; no se consulto el modelo.

Suite acumulada: 1242 aprobadas en 996,31 s. Una prueba integrada artificial
adicional paso en 42,46 s: generacion una vez, revision aceptada, dos cuentas,
dos periodos, renovacion de contexto y peticion futura sin nueva inferencia.
No se presenta como una suite global de 1243. La candidata real sigue duplicada
y sin simulaciones de investigacion nuevas; la prueba solo uso datos inventados.

Perfil real .local/verification-profiles/3ee2ee3604144fc3aaeaa2db68ceb16d:
85,70 s y 196 llamadas a _development/load_ecb_rates para leer el mismo bloque.
Hubo pytest concurrente: no es una comparativa de rendimiento ni mejora medida.
Cero proveedor, senales, backtests o evaluacion exterior. Se conservaron 252
copias previas y sus originales, con 5 copias nuevas. El motor no se modifica.

Se desarrolla validated_read_cache como opcion exclusiva de lectura: una
validacion completa por bloque y comprobacion de huellas/codigo/politica en
cada reutilizacion, copias independientes, ambito de contexto y restauracion
de enlaces al salir. No esta activada por defecto ni en productores sellados.
Primer pase: 8 aprobadas y un fallo de expectativa; report.md no era entrada de
_development (RESEARCH_FILES incluye results/analysis/analysis_origin/events).
Se corrige la prueba para modificar results.json y se anade regresion de cambio
de huella de codigo. Se ejecutan ahora sus 10 pruebas antes de uso real.
Cuota observada primaria 92%, uso permitido. Sin agotamiento observado.

Cache opcional: 10 pruebas aprobadas en 28,05 s. Lectura real coincidente con el paquete original: {'full_validations': 1, 'guarded_hits': 195, 'uncached_large_or_limit': 0}; 20.265 s observados. No es benchmark controlado. Registro: .local\cached-read-checks\dbfac940f4ff4ea49692d3200b1d3d7a. Cero consultas y backtests; fuentes/codigo/politica revalidados por acceso.

Punto de reanudacion: HEAD esperado f9bb417, cambios sin commit/push. Ultima suite global 1242 aprobadas; despues una integracion artificial adicional y 10 pruebas de cache. No se han repetido intentos, activado servicios o realizado mas llamadas de modelo; nuevo total real de esta continuacion: 1 llamada local (2262/176 tokens), 0 USD API, 0 backtests de investigacion. FASE 4 abierta y PROJECT_STATUS.md intacto. Automatizacion pausada; informe completo cuando vuelva el usuario. Ultima cuota leida 99%, uso permitido; agotamiento no observado. Pendientes: documentar/archivar cache opcional, completar enlace documental de peticion guiada y perfil, verificar Git/inventarios y preparar informe al volver. No iniciar mas inferencias con el intento compacto consumido.


### Consolidación de lectura y documentación - 20/10/2026

A petición del usuario ("Siguiente paso?"), se completa la documentación pendiente
antes de nuevas investigaciones. Git inicial: main, HEAD f9bb417, con todos los
cambios anteriores conservados. Cuota disponible al inicio: uso ordinario
permitido, primaria 3%, resetsAt 1792498481; no se inicia ninguna inferencia.

Se añaden GUIDED_REQUESTS.md y VALIDATED_READ_CACHE.md y los informes narrativos
de petición guiada, perfil y lectura con caché. Se enlazan desde README, plan,
candidatas y cobertura. No se modifica código de producción o pruebas. La caché
sigue opcional, limitada a lecturas y fuera de los productores históricos.

Se archivan cinco copias del registro de caché anterior, su huella, eventos,
código y pruebas en reports/phase4-cached-read-2026-10-20. Antes de copiarlas se
comprueban huella, evento final, código y coincidencia del packet con guided.json.
Las pruebas archivadas se renombran a validated_read_cache_tests.py para evitar
una segunda recolección; 1253 pruebas recolectadas, sin duplicados del archivo.

Verificación de alcance explícito: 17 inventarios, 262 copias y 262 referencias
originales correctas, 2228440 bytes. Son referencias, no archivos físicos únicos.
El primer intento de verificar todos los inventarios compatibles se detuvo ante
un original histórico fuera del proyecto (temporal de una prueba). No se amplió
la raíz permitida: se verificaron los 16 inventarios usados por la continuación
anterior y el nuevo de caché. No se afirma cobertura de todos los informes.

85 enlaces locales de los nueve documentos comprobados: correctos. git diff
--check correcto. PROJECT_STATUS.md intacto (SHA-256
53bcda9b54a6cc70a016da47e99d5023f646aed90c3d6277e4d0abf7cc72417e).
Suite completa iniciada con caché desactivada y temporal nuevo exclusivo según
AGENTS.md; resultado pendiente al escribir esta entrada. No se repiten cálculos
reales de investigación: los backtests de pytest usan sus datos de prueba.

Consumo nuevo de investigación: cero consultas, tokens y coste de API; cero
backtests de investigación. El consumo 2262/176 de la llamada local anterior es
heredado y no se vuelve a gastar. La candidata real sigue siendo un duplicado,
el intento compacto y la reformulación 2d0040bbd7184c1d9cbde9a8eef3ce3b siguen
consumidos. Sin instalaciones, servicios nuevos, dinero real, commits o pushes.
FASE 4 abierta. Siguiente desarrollo pendiente: protocolo de campaña local con
presupuesto explícito, sin habilitar envíos o reiniciar contadores históricos.


Resultado final de la consolidación: 1253 aprobadas en 1062,09 s (17 min 42 s),
exit code 0. La suite incluye juntas las 1242 anteriores, la integración
artificial y las diez pruebas de caché; se sustituye el resultado pendiente de
la entrada anterior. Recolección previa: 1253, sin pruebas duplicadas por el
archivo de evidencias. No se amplía o repite la batería tras este resultado.
El informe de caché incorpora la comprobación conjunta. Un parche documental
intermedio no coincidió con su contexto y no cambió archivos; se añadió después
el párrafo de resultado. Sin errores de pruebas o nuevas consultas de modelo.
FASE 4 sigue abierta, PROJECT_STATUS.md sin actualizar y cambios sin commit/push.


### Plan de campaña local, sin activación - 20/10/2026

Se continúa el desarrollo autorizado del protocolo de campañas dentro de FASE 4.
Git inicial main, HEAD f9bb417; se conservan todos los cambios pendientes. Se añade
campaign_plan.py sin modificar módulos anteriores vinculados a artefactos.
Los límites de preparación son explícitos: entre 1 y 3 propuestas, y 0/2/4/6
backtests, como máximo dos por propuesta. Son techos solicitados, no permisos.

El plan conserva controles, objetivo, datos, petición guiada exacta e historial
completo, con consumo heredado separado. Su identidad de ámbito depende de datos
y par, sin rutas o límites. Las capacidades ejecutables y reservas nuevas son
cero; no se implementa aún el registro compartido de activaciones o el ejecutor.
Se documenta el contrato futuro: revisión aceptada, cálculos con reservas
compartidas, cero reintentos/reformulaciones, conservación de descartes y parada
ante consumo desconocido o contexto incompleto. Históricos conocidos, sin nueva
validación independiente y con evaluación exterior desactivada.

Pruebas focalizadas: primer pase de 35 aprobadas en 26,49 s; después se añaden
cuatro casos de coherencia de presupuesto/límites y pasan 39 en 26,53 s. Incluyen
integración real de módulos con datos artificiales, respuestas falsas del
proveedor y reservas temporales aisladas; no son llamadas de IA de investigación.
Última suite global sigue siendo 1253 aprobadas, anterior a este módulo. No se
presenta la suma como una suite global nueva. Todos los pytest se ejecutaron con
caché desactivada y temporal exclusivo nuevo, según AGENTS.md.

Se añaden LOCAL_CAMPAIGNS.md y enlaces desde README, plan y petición guiada.
En curso auditoría .local/audit-campaign-plan.py: preparación sobre las fuentes
reales conocidas con proveedor, red, cálculos, reserva heredada y evaluación
exterior bloqueados. No activar nuevos intentos ni repetir la reformulación
2d0040bbd7184c1d9cbde9a8eef3ce3b. PROJECT_STATUS.md permanece sin modificar.


Auditoría real completada: plan 37316f24fb92479aa7b9af4ab8134ed0, auditoría
540c9d9be7f846d1b609751d9f6f2d87. Límites propuestos 3 ideas / 6 backtests;
reservas y capacidades ejecutables cero. Presupuesto heredado consumido intacto,
9 archivos de reservas sin cambios, y contadores de red/proveedor/cálculo/reserva
heredada/evaluación exterior todos a cero. Se conservaron las 262 copias previas
y sus referencias; 11 nuevas, 273 copias y referencias entre 18 inventarios
concretos. Evidencia en reports/phase4-campaign-plan-2026-10-20.md.

Consumo nuevo real de investigación: 0 consultas, 0 tokens, 0 USD de API,
0 backtests. Consumo compacto heredado: 2262/176 tokens de una consulta anterior,
0 USD API; no se vuelve a gastar ni se presenta como consumo global de la app.
La candidata real sigue duplicada, sin revisión aceptada ni simulaciones nuevas.

No se implementa aún la activación o el ejecutor de campañas: el siguiente
incremento será el registro compartido de límites y reservas, comprobado primero
con datos artificiales. No habilitar llamadas por crear planes o cambiar sus
carpetas, límites, criterio o capital. FASE 4 sigue abierta. PROJECT_STATUS.md,
módulos anteriores y archivos de evidencia conservados; sin commit/push.

Comprobaciones finales del incremento: git diff --check correcto, HEAD f9bb417,
75 enlaces locales comprobados y PROJECT_STATUS.md conserva su SHA-256.
Recolección global: 1292 pruebas, sin duplicados del archivo de evidencias;
no se ejecutó una nueva suite global. Resultado focalizado vigente: 39 aprobadas.


### Registro contable compartido de campañas - 20/10/2026

Se implementa campaign_ledger.py, separado de propuesta, revisión y motor.
Git inicial HEAD f9bb417 y 61 entradas pendientes conservadas. SQLite 3.50.4
comprobado como parte del Python existente; no se instala o inicia un servicio.
La base compartida por defecto es .local/campaign-ledger/registry.sqlite3.

La inscripción fija los primeros términos por identidad datos/par. Otro plan
conserva el registro y los contadores; límites o controles diferentes se rechazan.
Reservas con transacción BEGIN IMMEDIATE: una plaza por propuesta, dos backtests
por comparación y como máximo una comparación por propuesta. Claves repetidas
devuelven el mismo recibo; no consumen otra plaza. No hay devolución automática,
reinicio, cambio de base por CLI ni permiso de ejecución en estos recibos.
Estado y consultas siguen declarando execution_authorized false y capacidades
ejecutables cero. La vigencia de la memoria viva deberá comprobarse aparte.

Primer pase: 24 pruebas aprobadas en 17,26 s, incluidas concurrencia real entre
hilos y procesos Windows (spawn), rollback e integridad. Se añaden cuatro casos
más de concurrencia, controles y lectura sin escritura; plan y registro pasan
juntos 67 pruebas en 51,73 s. Después se refuerza el rechazo de valores binarios
u objetos no canónicos en SQLite y se añade una regresión; en curso el pase de
68 pruebas de ambos módulos. Última global verificada sigue siendo 1253.
Todos los pytest usan caché desactivada y temporal exclusivo nuevo según AGENTS.

Se añaden CAMPAIGN_LEDGER.md y enlaces desde campañas, README y plan. El registro
es solo contabilidad; todavía faltan permiso de ejecución, registro de respuestas
y consumo y controlador con revisión aceptada, memoria vigente y reserva del
motor. No se modifican módulos anteriores ligados a evidencias. La base de la
aplicación no existía al terminar las primeras pruebas; los ensayos contables
se mantuvieron en bases temporales artificiales.

En curso auditoría .local/audit-campaign-ledger.py para inscribir el plan real
inactivo sin reservar plazas y guardar una instantánea SQLite independiente.
No activar consultas o simulaciones ni repetir intentos/reformulaciones
consumidos. Sin instalaciones, dinero real, commits, pushes o cambios a
PROJECT_STATUS.md. FASE 4 abierta.


Resultado focalizado final: 68 aprobadas en 51,16 s, exit code 0 (39 del plan y
29 del registro). Incluye rechazo de un recibo SQLite binario en vez de texto.
No se repiten más pruebas tras el pase conjunto; queda pendiente la próxima
suite global, cuya referencia verificada sigue siendo 1253.

Auditoría real 261a7f9f850e425f906a78148e04add9 completada. Se inscribe el ámbito
f0e9b3af64f68a6d66642d794bb1df57ee0a5d677f841e1334997e752ae29e38
con límites 3/6 y cero reservas. No se ejecutan las API internas de reserva sobre
el registro de la aplicación. Contadores red/proveedor/cálculo/reserva heredada/
evaluación exterior todos cero; 9 archivos históricos de reservas intactos.
273 copias y referencias previas intactas, 8 nuevas: 281 entre 19 inventarios.
Evidencia: reports/phase4-campaign-ledger-2026-10-20.md. La base viva queda en
.local/campaign-ledger/registry.sqlite3; la copia archivada procede de una
instantánea independiente del diario y no obliga a congelar la base operativa.

Consumo real nuevo: 0 consultas de modelo, 0 tokens de investigación, 0 USD API,
0 backtests de investigación. Consumo heredado compacto 2262/176 tokens y 0 USD,
conservado sin volver a gastarlo y sin considerarlo consumo global. Las pruebas
artificiales y sus proveedores falsos no se suman a consumo real. Sin errores de
pruebas o herramientas en la auditoría. FASE 4 sigue abierta y PROJECT_STATUS.md
no se actualiza. Sin instalaciones, servicios nuevos, dinero real, commit/push.
Siguiente incremento: registrar respuestas, errores y consumo vinculados a cada
reserva antes de conectar el controlador y comprobar permisos de ejecución.

Comprobaciones finales: HEAD f9bb417, git diff --check correcto, 76 enlaces
locales comprobados y PROJECT_STATUS.md conserva su SHA-256. Recolección global
1321 pruebas, sin duplicados del archivo de evidencia; no es una suite global
ejecutada. Se conservan 66 entradas pendientes, sin commit o push.


### Respuestas, errores y consumo por reserva - 20/10/2026

Se añade campaign_attempts.py sin modificar los módulos anteriores vinculados
a evidencias. Git inicial HEAD f9bb417 y 66 entradas pendientes conservadas.
API internas de preparación, marca previa exclusiva y captura de observación;
CLI solo de consulta. Ninguna autoriza o envía llamadas. El registro de cada
captura queda vinculado a una reserva del ledger y a la huella exacta de petición.
Las rutas de salida no son configurables por CLI; cambiar carpeta no libera
la reserva global. Una marca solo se crea una vez, sin reintentos automáticos.

Se guarda observation.raw con los bytes recibidos antes de interpretar JSON o
consumo. El cierre separa declaración del llamador, análisis contable y validez
de propuesta (no realizada). Datos desconocidos permanecen desconocidos y
exigen parar; los subtotales conocidos no sustituyen un total incompleto.
Se conservan errores, textos truncados y JSON malformado sin completarlos.
Escrituras parciales o bloqueos interrumpidos no se reparan simulando un cierre.
Una observación completa idéntica es idempotente; otra diferente se rechaza.

Pruebas: 38 focalizadas aprobadas en 53,23 s. Se refuerzan lectura de estado
dentro del bloqueo, comprobación de eventos y exclusividad entre procesos.
Pase conjunto final: 109 aprobadas en 110,02 s (39 plan, 29 ledger, 41 nuevas).
Datos artificiales, procesos spawn y temporales nuevos exclusivos; caché de
pytest desactivada según AGENTS.md. Última global sigue siendo 1253. Sin fallos
de pruebas; un parche documental inicial no encontró su contexto, no cambió
archivos y se corrigió antes de continuar.

Se añaden CAMPAIGN_ATTEMPTS.md e informe con enlaces desde README, plan y
campañas. Auditoría real bca9a60c2ed845678760442b730aed63: consulta vacía de la
campaña inactiva, sin inventar capturas o propuestas. Contadores de red,
proveedor, cálculo, reserva heredada, evaluación exterior, reserva de campaña
y escritura de captura todos cero. Registro SQLite sin cambios, 9 archivos
históricos de reservas intactos y raíces de captura sin crear o modificar.
281 copias previas y originales intactos, 8 nuevas: 289 copias y referencias
entre 20 inventarios concretos. No se presentan como archivos físicos únicos.
Evidencia: reports/phase4-campaign-attempts-2026-10-20.md.

Consumo real nuevo: 0 consultas del modelo del proyecto, 0 tokens de
investigación, 0 USD API, 0 backtests. El consumo heredado compacto 2262/176,
0 USD API, permanece separado y no se gasta de nuevo. Las cifras artificiales
de las pruebas no se suman al consumo real. No se repiten intentos o la
reformulación 2d0040bbd7184c1d9cbde9a8eef3ce3b. La candidata real sigue duplicada,
sin revisión aceptada ni nuevas simulaciones. No hay instalaciones, servicios
nuevos, dinero real, commits o pushes. FASE 4 abierta y PROJECT_STATUS.md intacto.
Siguiente bloque: controlador con permiso de campaña, memoria vigente, revisión
aceptada y reservas del motor; no activar envíos por la mera presencia de capturas.

Comprobaciones finales: HEAD f9bb417, git diff --check correcto, 81 enlaces
locales comprobados y PROJECT_STATUS.md conserva su SHA-256. Recolección global
1362 pruebas, sin duplicados del archivo de evidencia; no es una nueva suite
global ejecutada. Resultado conjunto del bloque: 109 aprobadas. Se conservan
71 entradas pendientes, sin commit/push.

### Nombre del proyecto: TiresIAs - 20/10/2026

Por petición del usuario se adopta el nombre «TiresIAs - Laboratorio de
investigación de estrategias de trading con IA». Se actualizan el título y la
presentación de README, el arranque y la ayuda del punto de entrada principal,
y las referencias del plan del investigador y de la integración futura con
TradingView. La identidad visible se define en trading_ai/__init__.py.

Se conservan el paquete trading_ai, sus comandos, la carpeta, la configuración
y las evidencias anteriores. No se modifican los módulos sellados, las cabeceras
de sus informes ni los registros históricos para renombrarlos. Se explica esta
compatibilidad en README. La conexión con TradingView sigue pendiente.

Verificación: 64 pruebas de informes y sensibilidad aprobadas en 1,75 s, con
caché desactivada y temporal exclusivo según AGENTS.md. Presentación y ayuda
con el nombre completo comprobadas; importar el paquete y su punto de entrada
sigue sin imprimir mensajes. Se verifican 289 copias y referencias originales
en los 20 inventarios seleccionados, todas intactas. PROJECT_STATUS.md conserva
su SHA-256 y FASE 4 continúa abierta. git diff --check sin errores de espacios.
Esta comprobación focalizada no constituye una nueva suite global ejecutada.

Consumo nuevo del modelo del proyecto: 0 llamadas, 0 tokens y 0 USD API;
sin simulaciones de investigación nuevas. Los datos artificiales de las pruebas
no son resultados de estrategias reales. Cambios pendientes previos conservados;
sin instalaciones, servicios, commits o pushes.
