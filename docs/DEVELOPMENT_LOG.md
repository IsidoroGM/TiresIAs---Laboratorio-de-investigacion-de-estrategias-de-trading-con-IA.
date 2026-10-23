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

### Primer control de campañas de TiresIAs - 20/10/2026

Git inicial limpio en main, HEAD 3d0fa83; los cambios anteriores ya estaban
incorporados en ese commit al iniciar esta petición. Se añade
trading_ai/campaign_controller.py sin modificar módulos históricos sellados.
La CLI solo consulta un ámbito registrado: verifica plan y memoria guiada
vigentes, controles, límites, reservas y consumo de todas sus capturas.

Cada petición debe conservar exactamente los bytes del plan registrado y el
contrato compacto. Las reglas se validan con el compilador existente y sus
descripciones las deriva Python; no se atribuye prosa o hipótesis al modelo.
Se separan error del proveedor, reglas inválidas, duplicado histórico y candidata
pendiente de revisión. Errores e intentos consumidos se conservan, sin completar
JSON o textos. El origen de las observaciones sigue siendo declaración del
llamador; no se acredita transporte o identidad del proveedor.

El consumo desconocido, una captura interrumpida, una petición ajena o una reserva
de comparación sin revisión controlada exigen parar. Se releen fuentes, huellas,
registro y capturas para detectar cambios durante la consulta. Es un control
optimista, sin bloqueo global. Se declara que todavía no hay una petición futura
con toda la memoria de campaña, permiso de ejecución, envío controlado o enlace
de revisión aceptada, plan y reserva del motor. Capacidad ejecutable siempre cero.

Pruebas: primer pase de 31 aprobadas en 94,31 s; tras ampliar contratos, pase
conjunto de 144 aprobadas en 230,06 s: 39 plan, 29 ledger, 41 capturas y 35 nuevas.
Incluye fuentes guiadas completas, cambios durante la consulta y transporte falso.
Temporales exclusivos y caché desactivada según AGENTS.md. Recolección global:
1397 pruebas en 0,76 s; no equivale a una suite global ejecutada. La última global
comprobada sigue siendo 1253. Sin errores de pruebas o de la auditoría.

Auditoría real 389adb9a10f1408ea0fb17609bbd4f6b: campaña inactiva, sin reservas,
capturas o propuestas nuevas. Siete contadores de red/proveedor/cálculo/reserva
heredada/evaluación exterior/reserva de campaña/escritura de capturas todos cero.
SQLite conserva sus bytes, los 9 archivos históricos de reservas están intactos
y las raíces de capturas siguen sin crear. 289 copias y referencias previas
intactas, 8 nuevas: 297 entre 21 inventarios concretos, no archivos físicos únicos.
Evidencia: reports/phase4-campaign-controller-2026-10-20.md. Se añade documentación
de uso y enlaces desde README, el plan del investigador y el plan de campañas.

Consumo nuevo real del investigador: 0 llamadas, 0 tokens, 0 USD API, 0 backtests.
El consumo heredado compacto 2262/176 y 0 USD API permanece separado; no es el
total de la aplicación. Las observaciones de pruebas son artificiales. No se
repite la reformulación 2d0040bbd7184c1d9cbde9a8eef3ce3b, no se simulan propuestas
pendientes y no se reutiliza evaluación conocida como inédita. Sin instalaciones,
servicios nuevos, dinero real, commits o pushes. PROJECT_STATUS.md conserva su
SHA-256 y FASE 4 continúa abierta. Siguiente incremento: registrar la revisión
técnica de las capturas válidas y vincular su plan antes del ejecutor con permiso
de campaña, memoria completa y reserva compartida del motor.

Comprobaciones finales: HEAD 3d0fa83, 10 entradas pendientes, git diff --check
correcto y 85 enlaces locales comprobados. Las 297 copias y referencias de los
21 inventarios conservan sus bytes. No se ha realizado commit o push.

### Revisión técnica y plan de experimento de campaña - 20/10/2026

Inicio: main, HEAD 3d0fa83, 10 entradas pendientes conservadas. Se añaden
campaign_review.py y campaign_experiment.py sin modificar los módulos sellados.
La revisión usa una captura válida y su reserva exacta, con memoria guiada vigente,
consumo verificable y controles fijados. La declaración identifica campaña,
petición, recibo, observación y reglas; no permite introducir cambios de riesgo
o resultados. Aceptar exige las seis comprobaciones booleanas. Motivo y revisor
permanecen como declaraciones no verificadas, sin prueba de rentabilidad o autoría.

Una reserva global exclusiva por captura impide sustituir o repetir la decisión
cambiando la carpeta. Un fallo después de reservar conserva el intento; una
declaración inválida anterior queda registrada sin consumir la revisión. Se
conservan decisiones accepted/rejected/needs_clarification sin reintentos o
reformulaciones automáticas. No se aprueban duplicados o revisiones retroactivas
después de reservar comparaciones. La consulta de estado solo lee el registro.

Una revisión aceptada permite preparar un plan con las reglas exactas, datos de
desarrollo, controles y objetivo congelados. Prevé dos backtests, base y candidata,
con cuentas independientes y ejecución posterior, sin variaciones o consultas
al modelo. Comprueba dos huecos contables y ausencia de comparación o cálculo
consumido. Conserva la identidad de cálculo compartida con los ejecutores previos.
Preparar o verificar no reserva cálculos, ejecuta herramientas o devuelve huecos;
una reserva posterior no borra los artefactos históricos. Se guardan errores y
archivos parciales. Los contratos nuevos no activan los ejecutores anteriores.

Pruebas nuevas: 30 de revisión aprobadas en 88,16 s; 17 de planificación e
integración en 270,89 s; una adicional de rechazo por ejecutores anteriores en
7,59 s. Son 48 distintas verificadas en tres pases, no un pase conjunto o global.
Temporales exclusivos y caché de pytest desactivada según AGENTS.md. Recolección
global: 1445 en 0,72 s; no equivale a ejecución. Última global comprobada: 1253.
Sin errores de pruebas o auditoría. La integración usa fuentes completas,
transporte falso, reglas artificiales y caché de lectura validada explícita;
no activa esa caché por defecto. El recorrido de verificaciones sigue siendo
costoso; estos tiempos no miden rendimiento real de producción.

Auditoría real fee3b2c854f94fe0901844061da9424c: consulta vacía del registro de
revisiones, campaña inactiva, sin crear capturas, revisiones o planes ficticios.
Ocho contadores de red/proveedor/cálculo/reserva heredada/evaluación exterior/
reserva de campaña/escritura de capturas/escritura de revisión o plan todos cero.
SQLite conserva sus bytes, 9 archivos históricos de reservas intactos y cinco
raíces locales sin cambios. Se comprueban 297 copias y referencias previas, se
añaden 10: 307 entre 22 inventarios concretos, no archivos físicos únicos.
Evidencia: reports/phase4-campaign-review-2026-10-20.md. Se documentan comandos,
declaración y límites en CAMPAIGN_REVIEW.md y se enlazan desde los planes y README.

Consumo nuevo real del investigador: 0 llamadas, 0 tokens, 0 USD API, 0 backtests.
El consumo heredado compacto 2262/176 y 0 USD API sigue separado; no es el total
de la aplicación. Las cifras de las pruebas son artificiales. No se repiten los
intentos consumidos, incluida la reformulación 2d0040bbd7184c1d9cbde9a8eef3ce3b.
No se simulan propuestas pendientes ni se reutiliza evaluación conocida como
inédita. Sin instalaciones, servicios nuevos, dinero real, commits o pushes.
PROJECT_STATUS.md conserva su SHA-256 y FASE 4 permanece abierta. Próximo bloque:
permiso de campaña y ejecutor que vincule memoria completa, origen verificado,
revisión, plan y reservas contables con la reserva compartida del motor.

Comprobaciones finales: HEAD 3d0fa83, 17 entradas pendientes conservando las 10
iniciales, git diff --check correcto y 91 enlaces locales comprobados. Las 307
copias y referencias de 22 inventarios conservan sus bytes. Sin commit o push.

### Permiso y ejecutor de comparación virtual - 20/10/2026

Inicio: main, HEAD 3d0fa83, 17 entradas pendientes conservadas. Se añaden
campaign_permission.py y campaign_execution.py sin modificar módulos sellados.
El permiso explícito fija un plan y una comparación de dos backtests, cero
consultas al modelo y cero USD de API. No permite cambios de parámetros,
operaciones de bróker o evaluación exterior. Se comprueban las huellas de todas
las capturas, consumo y revisiones del ámbito antes y durante el cálculo.

La ruta nueva se identifica como offline_virtual_evaluation_of_declared_source.
Se comprueba la cadena local de la captura sin dar por acreditados transporte
o autoría del modelo. El llamador debe reconocer expresamente ese origen
declarado; se conserva transport_verified: false. Es un permiso de cálculo
offline distinto del futuro ciclo de generación con proveedor verificado.
No se declara cumplido el transporte pendiente ni se habilitan consultas nuevas.

El ejecutor ocupa primero la reserva compartida del motor y luego los dos huecos
contables juntos. Calcula base y candidata con el motor y controles congelados,
guarda contabilidad y análisis de Python y no adopta la propuesta automáticamente.
Errores del registro o del motor conservan las reservas y los cálculos parciales;
cambiar la carpeta no libera un intento. La memoria debe permanecer idéntica y
este primer contrato no admite otras comparaciones con resultados sin incorporar.

Pruebas: 25 de permisos aprobadas en 130,17 s y 17 del ejecutor, concurrencia,
fallos e integración aprobadas en 741,11 s. Son 42 distintas en dos pases, no
un pase conjunto o global. Se usa el motor real con referencias artificiales;
la integración conserva los validadores completos y bloquea red, modelos,
presupuestos heredados y evaluación exterior. Los 12 min 21 s corresponden al
pase de 17 pruebas completo, no solo al backtest o a una medida de producción.
El recorrido repetido de verificaciones es costoso; queda pendiente optimizarlo
sin perder comprobaciones. La integración usa caché de lectura validada explícita,
sin activarla por defecto en producción. Sin errores de pruebas o auditoría.
Recolección global: 1487 en 0,88 s, sin ejecución global. Última global comprobada:
1253. Temporales exclusivos y caché de pytest desactivada según AGENTS.md.

Se añaden CAMPAIGN_EXECUTION.md y enlaces desde README y los planes. No se ha
concedido permiso a la campaña de la aplicación, creado propuestas, consultado
modelos o simulado sus candidatas pendientes. Consumo nuevo de investigación
en la aplicación: cero llamadas, tokens, USD API y backtests. Los cálculos del
motor sobre datos artificiales pertenecen a las pruebas y se mantienen separados.
Auditoría real 0dd9454d25784c9d936cc397cc84c4c1: consulta vacía de permisos, campaña
inactiva, sin permisos o ejecuciones nuevos. Nueve contadores de acciones bloqueadas
en cero. SQLite conserva sus bytes, 9 archivos históricos de reservas intactos y
tres raíces de permiso/ejecución sin crear. Se verifican 307 copias y referencias
previas; se añaden 10: 317 entre 23 inventarios concretos, no archivos físicos únicos.
Evidencia: reports/phase4-campaign-execution-2026-10-20.md. Consumo heredado compacto
2262/176 y 0 USD API conservado aparte, sin presentarlo como total de la aplicación.
No se repite la reformulación 2d0040bbd7184c1d9cbde9a8eef3ce3b ni se reutiliza
evaluación conocida como inédita. PROJECT_STATUS.md conserva su SHA-256 y FASE 4
sigue abierta. Sin instalaciones, servicios nuevos, dinero real, commits o pushes.
Siguiente bloque: incorporar resultados a la memoria para nuevos ensayos y
preparar el envío local controlado con procedencia verificada. La reducción de
validaciones repetidas queda como limitación de rendimiento pendiente.

Comprobaciones finales: HEAD 3d0fa83, 24 entradas pendientes conservando las 17
iniciales; git diff --check correcto, 91 enlaces locales comprobados y 317 copias
y referencias intactas entre 23 inventarios. Raíces reales de permisos y ejecución
sin crear. Sin commit o push.

### Memoria de resultados y verificación reutilizable - 20/10/2026

Inicio: main, HEAD 3d0fa83, 24 entradas pendientes conservadas. Se añaden
campaign_memory.py y verification_session.py y sus pruebas sin modificar módulos
o pruebas históricos sellados. La memoria reúne reservas, propuestas, capturas y
consumo, revisiones, permisos y resultados completos verificados por el motor.
Conserva conclusiones negativas e inconclusas, sin adopción automática. Los
intentos fallidos conservan error, contabilidad parcial y contadores observados;
no se convierten en un resultado completo ni liberan reservas.

Se detectan también la reserva compartida anterior a un fallo de SQLite, un
recibo sin ejecución y el protocolo desconocido de una reserva vinculada a un
permiso, aunque todavía no haya recibo contable. Una reserva que no sea objeto
JSON se rechaza expresamente. Las consultas comparan dos lecturas y las memorias
guardadas se sellan y vuelven a contrastarse con el estado actual. No se recortan
datos: el límite de documento es 120.000 bytes. Los desconocidos y el consumo
compacto heredado permanecen separados del consumo nuevo de la consulta.

La sesión opcional de verificación reutiliza solo la lectura guiada dentro de
una operación explícita. Cada acierto comprueba bytes, rutas, presencia, listados
y código/configuración. No se guardan SQLite, permisos, cálculos o resultados en
caché. Se devuelven copias independientes, se restauran lectores incluso por
error y otros hilos sin sesión mantienen la ruta original. No hay caché persistente
ni reintento automático al cambiar una fuente.

Pruebas: 29 distintas verificadas en pases focalizados; no es una nueva suite
global verde. Primer pase: 24 aprobadas en 206,23 s. La primera integración
detectó el uso de argumentos de glob desde rglob en Python 3.14; corregido en
el módulo nuevo, pasó en 177,17 s. La captura inicial de tiempos emitió un aviso
JUnit no fatal; los XML posteriores usan junit_family=legacy. Las 12 pruebas de
sesión pasaron después en 7,22 s. Tras ampliar controles, un pase conjunto tuvo
27 aprobadas y una fallida en 481,69 s: se editó el nuevo módulo durante la prueba
de guardar/verificar memoria y cambió code_sha256. No se presenta ese pase como
verde. Se repitió esa prueba con fuentes estables junto con la de JSON no objeto:
dos aprobadas en 58,39 s. Esta última también pasó separadamente en 18,04 s.
La unión de casos aprobados en los tres XML finales verifica 29 distintas, con
solapamiento. No quedan fallos de prueba sin comprobar tras su corrección.

La integración conserva validadores y cálculos reales de Python sobre referencias
artificiales, con red/modelos, presupuesto heredado y evaluación exterior bloqueados.
Una validación guiada inicial con seguimiento tardó 6,43 s; reutilizar esa misma
entrada con guardas, 1,22 s. Una validación completa y 84 reutilizaciones en la
integración; no se compara ese tiempo con el de un backtest. La recolección global
actual es 1516 en 1,07 s, sin ejecución global. La última global ejecutada sigue
en 1253. Pytest sin caché y con temporales exclusivos conforme a AGENTS.md.

Auditoría final d4c89640027443bf8debb71d948f0afd: memoria real vacía guardada en
.local/campaign-memory/00b3e4e65fde4f59aae5f18c3ec81880. Las consultas sin caché,
inicial con caché y repetida devuelven el mismo documento. Tiempos observados
149,39 s, 80,50 s y 4,81 s, respectivamente; una verificación guiada completa y
siete reutilizaciones durante consultas y guardado/verificación. Son lecturas de
una campaña vacía, sin inferencia o simulaciones. Nueve contadores de acciones
bloqueadas en cero, SQLite intacto, nueve archivos históricos de reservas intactos
y raíces reales de permisos/ejecuciones sin crear. Se conservan 317 copias y
referencias previas y se añaden 15: 332 entre 24 inventarios, no archivos físicos
únicos. La auditoría preliminar 36b4c2155e434dd5a64dc0aa4c8541f2 queda como borrador
local tras ampliar el control de reservas; su memoria anterior está obsoleta por
el cambio de código y no se reutiliza como contexto. La consulta auxiliar de
Win32_Process no estuvo disponible por permisos; no afectó a estas comprobaciones.

Consumo nuevo de investigación de la aplicación: cero consultas, tokens, USD API
y backtests. Los cálculos de prueba sobre datos artificiales van aparte. El ámbito
compacto heredado conserva 2262/176 tokens y 0 USD, sin presentarse como consumo
total de la aplicación. No se activa la campaña, conceden permisos nuevos o
simulan candidatas reales pendientes. La procedencia continúa declarada, con
transporte y autoría no acreditados. No se repite la reformulación
2d0040bbd7184c1d9cbde9a8eef3ce3b ni se considera inédita evaluación conocida.

La petición inicial permanece congelada y la memoria no se envía al modelo.
El ciclo automático local y la incorporación de esta memoria a nuevas peticiones
continúan pendientes. El primer permiso conserva su límite de una comparación.
Siguiente paso: contexto renovado con resultados y control de tamaño; después
transporte local verificado y controlador separado de revisión, cálculos y permisos.
FASE 4 sigue abierta y PROJECT_STATUS.md conserva su SHA-256. Sin instalaciones,
servicios nuevos, operaciones reales, commits o pushes.

Detalle y evidencias: [memoria de resultados](../reports/phase4-campaign-memory-2026-10-20.md).

Comprobaciones finales: HEAD 3d0fa83, 32 entradas pendientes conservando las 24
iniciales; git diff --check correcto, 106 enlaces locales comprobados y 332 copias
y referencias originales verificadas entre 24 inventarios. PROJECT_STATUS.md
sin cambios. Sin commit o push.

### Integración para cierre de FASE 4 - 20/10/2026

Autorización nueva: continuar hasta terminar FASE 4, sin commits o pushes.
Inicio: main, HEAD 3d0fa83, 32 entradas pendientes conservadas. Se añaden
campaign_context.py, campaign_cycle.py y walk_forward.py sin modificar módulos
o pruebas históricos sellados. PROJECT_STATUS.md aún no se actualiza: el cierre
queda pendiente de la suite completa y la auditoría final.

El contexto incorpora el historial íntegro y resultados nuevos mediante un
diccionario reversible de claves y cadenas repetidas. La captura fija el esquema
por SHA-256 y el transporte lo envía íntegro. Contrato nuevo: 12 KiB para captura,
24 KiB para mensajes más esquema, contexto 4096 y salida 384 tokens, CPU y rechazo
de desbordamiento sin recortes. No se amplían contadores históricos o capacidades
del modelo. Los primeros dos pases detectaron el exceso de bytes al duplicar el
esquema en la captura; se corrigió separando su huella y la envoltura del transporte,
sin recortar el historial. El adaptador compacto histórico permanece intacto.

El ciclo separa generación, revisión mecánica de reglas tipadas cerradas, plan,
cálculos del motor y memoria. La revisión no inventa aceptación semántica humana:
semantic_acceptance y automatic_adoption permanecen en false. Es un contrato de
experimentos virtuales distinto de las revisiones/permisos manuales v1; no procesa
sus pendientes. Las habilitaciones de generación local y cálculo virtual son
explícitas. Máximo registrado: tres propuestas y seis backtests. El intento de
ciclo es exclusivo por ámbito; fallos y duplicados consumen intentos sin reintento.
No se considera una propuesta automáticamente mejor ni se reabre la reformulación
2d0040bbd7184c1d9cbde9a8eef3ce3b. Los controles y datos permanecen congelados.

El walk-forward fija tres ventanas expansivas y cinco variantes mecánicas de la
SMA/EMA congelada: original y ventanas ±1. Selecciona exclusivamente en entrenamiento,
sin cambiar costes, y sincroniza la selección antes de cargar el tramo en el
cálculo de comprobación. La verificación de procedencia puede leer previamente
el desarrollo completo, sin aportar métricas de comprobación al selector.
Si no hay elegibles, no fuerza ganador o comprobación. Cuentas y calentamiento
independientes, máximo 24 backtests en su protocolo separado, cero peticiones IA
y sin agregación ficticia de capitales. Todos los datos son desarrollo conocido;
no se acredita validación independiente o prospectiva.

Pruebas focalizadas finales: 31 aprobadas en 134,42 s, con transporte y datos
artificiales, motor real y validadores completos en la integración. Cubren memoria
para la siguiente petición, límites, duplicados, identidad del modelo, concurrencia,
carreras de reserva, errores parciales, consumo desconocido, alteraciones,
selección vacía y selección duradera antes de cargar la comprobación. Temporales
exclusivos y caché pytest desactivada según AGENTS.md. Recolección completa:
1547 pruebas, distribuidas sin solapamiento en tres procesos de 459, 575 y 513;
su ejecución está en curso, sin presentarla todavía como aprobada.

Comprobación real bdd6a55c937f4f2abc272a9ad2d64625 sobre el servidor ya instalado
y en ejecución, Ollama 0.40.6; no se arranca o instala ningún servicio. Ciclo
.local/campaign-cycles/eaba7b8479034eb69e52838fa1919715: una consulta local,
2898 tokens de entrada, 180 de salida, seis consultas de metadatos y 0 USD API.
El modelo repite una identidad consumida: duplicate_rules. Se rechaza antes de
simular, sin reintento. Quedan dos huecos de propuestas y seis de backtests en el
registro; no se liberan intentos ni se reabre el ciclo. El ámbito compacto heredado
2262/176 tokens y 0 USD permanece separado; no es el total de la aplicación.

Walk-forward real .local/walk-forward-runs/c4efcbf170af4d23a1d961c05546ef12:
20 backtests de los 24 máximos. La primera ventana tiene selección, pero no cumple
el criterio en comprobación: rentabilidad y drawdown mayores frente a la base.
Las otras dos no tienen elegibles y no ejecutan comprobación. No se sustituye
la selección ni se fuerza ganador. Ningún acceso a evaluación exterior o red
fuera del servidor local. Controles y límites registrados sin cambios, nueve
archivos históricos de intentos intactos y 332 copias/referencias anteriores
intactas. La evaluación exterior anterior no se repite ni se considera inédita.

Guía del contrato: [integración de FASE 4](PHASE4_COMPLETION.md). Sin llamadas
de pago, operaciones reales, instalaciones, servicios nuevos, commits o pushes.

#### Cierre comprobado de FASE 4

Colección completa aprobada: 1547 pruebas, en tres procesos aislados y sin
solapamientos: 459 en 998,22 s; 575 en 1194,79 s; 513 en 1075,35 s. Se ejecutaron
en paralelo; no se suman como tiempo transcurrido. Ningún error, fallo o salto.
La comparación con los nodos recogidos y la huella de los 131 archivos de código
y pruebas confirma cobertura completa y fuentes estables. El primer cotejo de
JUnit señaló barras de Windows en identificadores parametrizados; se igualó la
normalización a la de la colección, sin colisiones, cambios de aplicación o
nuevas ejecuciones de investigación.

Auditoría final 3f5f81a4fbf04bbcb7b0894c14a899aa: los verificadores comprueban ciclo
y walk-forward con red, nuevas reservas y recálculos bloqueados. Cero acciones
nuevas. Las 332 copias y referencias anteriores permanecen intactas; se añaden
98, con 430 entre 25 inventarios concretos, no archivos físicos únicos. La evidencia
nueva ocupa 46.792.487 bytes e incluye contabilidad, datos, fuentes y resultados
de pruebas. Los informes previos conservan sus fechas y estados históricos.

PROJECT_STATUS.md se actualiza ahora al cerrar la fase por autorización del usuario,
incluyendo el nombre TiresIAs, la arquitectura incorporada, resultados adversos,
consumo nuevo y heredado por separado, pruebas y limitaciones. Se actualizan README
y documentos de uso. El cierre acredita el alcance de software educativo; no
rentabilidad, fiabilidad general del modelo o validación independiente. La consulta
local nueva fue un duplicado rechazado, no una estrategia aceptada. El walk-forward
usó exclusivamente datos de desarrollo ya conocidos; no se reabre evaluación exterior.

Detalle: [cierre de FASE 4](../reports/phase4-completion-2026-10-20.md). El siguiente
paso propuesto es FASE 5, interfaz de consulta, sin empezarla automáticamente.
No hubo servicios nuevos, instalaciones, llamadas de pago, dinero real, commits
o pushes. Se mantienen todos los cambios previos del usuario.

Comprobaciones finales: HEAD 3d0fa83, 43 entradas pendientes conservando las 32
iniciales; raíz Git correcta y git diff --check aprobado. Las 430 copias y sus
referencias originales están verificadas entre 25 inventarios. Los 131 archivos
de código/pruebas conservan su huella; la recolección posterior al archivo de
evidencias sigue en 1547 casos, sin pruebas duplicadas. Se comprobaron 142 enlaces
locales, sin destinos ausentes. PROJECT_STATUS.md recoge el cierre de FASE 4.

#### Publicación autorizada del cierre

El usuario autoriza ahora el commit y push de FASE 4. Antes de preparar la
publicación se consulta GitHub: main y origin/main coinciden en 3d0fa83. Se
conservan las 43 entradas pendientes del cierre, incluidos los informes y sus
evidencias. Los 131 archivos de código/pruebas mantienen las huellas de la
colección aprobada de 1547 casos. Una nueva verificación de los 25 inventarios
confirma 430 copias y 430 referencias originales, sin consultas al modelo,
backtests o coste de API nuevos. No se repiten investigaciones ni se modifica
PROJECT_STATUS.md después del cierre. Los apartados anteriores que indican
ausencia de commits o pushes describen aquellas ejecuciones previas a esta
autorización.

La revisión del índice conserva byte a byte los 156 archivos de código y evidencia
sellada incluidos en el commit. Git detecta un espacio final dentro del diagnóstico
original de pytest en focused-tests.xml; se conserva esa evidencia histórica y se
documenta una excepción de whitespace exclusivamente para ese archivo en
.gitattributes. No se altera su contenido ni se excluyen comprobaciones del código.


### 20/10/2026 — FASE 5, interfaz local por incrementos

Petición: completar la interfaz de consulta del laboratorio, sin iniciar FASE 6,
consultar modelos, repetir simulaciones históricas, reservar intentos o publicar
cambios. Leídos AGENTS, README, estado, avances recientes, cierre de FASE 4 y plan
TradingView antes de modificar archivos. Inicio limpio en main,
f5e654435f42efcb76c53a82f812a541bf78d521, coincidente con la referencia origin/main.
No se modifican fuentes antiguas vinculadas a las evidencias.

Primer incremento: PHASE5_PLAN, catálogo acotado y contratos de lectura. Se
reutiliza evidence.verify_evidence para los inventarios versión 1 y se admiten
sin conversión los cinco inventarios históricos de lista. Los originales locales,
copias archivadas y estado contable vigente se distinguen expresamente. Ausencias,
alteraciones y falta de verificación no se convierten en resultados certificados.

Segundo incremento: servidor explícito de biblioteca estándar en 127.0.0.1 y
cinco pantallas en español: Inicio, Experimentos, Resultados, Memoria del agente
y Consumo. Filtros, ficha, archivos originales e inventarios. Contenido del modelo
como texto, separado de la descripción y las conclusiones de Python. Host/Origin
locales, CSP, GET/HEAD, rutas mediante identificadores de catálogo y sin controles
de ejecución. Sin dependencias, instalaciones o servicios permanentes.

Tercer incremento: resúmenes históricos, contabilidad completa guardada del
walk-forward, operaciones, curva, drawdown y posición abierta. Cuentas separadas
por estrategia, tramo y moneda. Comparación bloqueada ante diferencias o valores
necesarios desconocidos; se conservan los costes particulares de cada escenario
de sensibilidad. No se reconstruyen curvas ni operaciones para formatos antiguos.
Memoria, errores, consumo nuevo/heredado y desconocido separados, sin total global
que duplique memorias. El registro SQLite se consulta con su lector mode=ro.

Pruebas focalizadas: primer pase 42 aprobadas y una omitida por la disponibilidad
de enlaces simbólicos de Windows. La prueba de la guarda se hizo independiente
de privilegios, sin cambiar permisos: 43 aprobadas. Ampliación de casos de formatos,
comparabilidad, capturas y trazabilidad: 51 aprobadas en 11,89 s. Caché desactivada
y un temporal GUID nuevo y exclusivo por ejecución, conforme a AGENTS.md.

Revisión visual en el navegador de Windows: Inicio, explorador con filtros
combinados, ficha y cuenta histórica de comprobación con curva y operaciones.
La revisión detectó que el filtro de fecha comparaba UTC mientras la pantalla
mostraba hora local. Se detuvo la primera colección completa antes de modificar
fuentes y se corrigió el filtro para usar el mismo día local visible. Los procesos
fueron detenidos y se comprobó que solo quedaba el servidor de consulta antes de
editar. Sus manifiesto y logs parciales se conservan como ejecución interrumpida;
no se cuentan como pruebas aprobadas.

Auditoría explícita check_lab_readonly.py: 92 registros, 190 cuentas (40 con
contabilidad detallada y 150 solo con resumen, contando originales y copias),
47 fuentes de consumo. Estados de integridad: 52 copias comprobadas, 23 originales
cotejados, ocho registros sin verificación completa y nueve incompletos. Las 837
fuentes controladas conservan sus huellas; cero llamadas prohibidas, inferencias,
backtests, reservas o escrituras desde la consulta. Incluye consulta vigente del
registro contable y controles de acceso históricos. No se reinterpretan estos
recuentos como cuentas únicas o consumo total. Evidencia en
reports/phase5-completion-2026-10-20/read-only-check.json.

Punto de continuación: colección completa de 1598 pruebas en curso en tres
procesos aislados (510, 575, 513), tras congelar fuentes de código, pruebas y
recursos web. Resultados en reports/phase5-completion-2026-10-20/suite-final.
Falta terminar la revisión visual, cotejar la colección exacta y cerrar documentos.
PROJECT_STATUS permanece en el cierre de FASE 4 hasta completar esas verificaciones.
No hay commits, pushes o inferencias nuevas; la reformulación consumida y el
resultado negativo del walk-forward se conservan sin reabrirlos.


#### Cierre comprobado de FASE 5

La colección final completa termina con 1598 pruebas aprobadas, cero fallos,
errores o saltos. Tres procesos aislados: 510 casos en 1235,329 s; 575 en
1399,702 s; 513 en 1285,328 s (tiempos JUnit). Se ejecutaron en paralelo: no se
suman como duración transcurrida. La unión coincide exactamente con los nodos
recogidos, sin omisiones, duplicados o colisiones tras normalizar las barras de
Windows. Los 139 archivos de código, pruebas, recursos web y auditoría conservan
sus huellas durante toda la ejecución. Python 3.14.8 confirmado.

Revisión visual final: cinco apartados, filtros combinados y fecha local próxima
al cambio de día, ficha de walk-forward y cuenta EMA19/60 de comprobación,
curva, drawdown, operaciones y posición abierta; comparación admitida dentro del
mismo tramo y bloqueada al mezclar entrenamiento/comprobación. El enlace desde
la ficha abre el inventario original como texto. El duplicado permanece descartado
y el consumo nuevo 2898/180 y heredado 2262/176 quedan separados. Una fuente
artificial aparte muestra literalmente script e imagen con manejador, sin crear
elementos ejecutables; un identificador inexistente presenta un error comprensible.
Capturas y registro visual conservados en el informe de cierre.

Los dos servidores temporales de comprobación se cerraron y sus puertos 8765 y
8766 quedaron libres. No se crearon servicios permanentes. Las 837 fuentes de la
auditoría de lectura mantienen sus huellas, con cero inferencias, backtests,
reservas o escrituras desde la consulta. Los 131 archivos anteriores de código y
pruebas y los informes/evidencias anteriores seguidos por Git permanecen intactos.

README, guía y plan describen arranque con python -m trading_ai.lab, cierre con
Ctrl+C, límites de lectura, registros históricos y cuentas independientes.
PROJECT_STATUS se actualiza únicamente ahora, al completar la fase, con el alcance,
las 1598 pruebas y las limitaciones. FASE 6 queda pendiente, sin iniciarse.
Los formatos antiguos sin detalle no reciben curvas reconstruidas; la integridad
no se presenta como validación independiente, fiabilidad del modelo o rentabilidad.
No se reabren reformulaciones, evaluaciones o presupuestos.

Git sigue en main, HEAD f5e654435f42efcb76c53a82f812a541bf78d521, con los cambios
de FASE 5 pendientes de revisión. La referencia local origin/main coincide; el
intento de comprobar el servidor remoto con git ls-remote devuelve 128 y no se
presenta como sincronización remota confirmada. Sin commits o pushes, dependencias
nuevas, llamadas de pago, credenciales leídas u operaciones reales.

Punto de reanudación: FASE 5 cerrada. El siguiente desarrollo, solo si el usuario
lo encarga, corresponde a FASE 6 según TRADINGVIEW_PLAN.md. Informe y evidencias:
[phase5-completion-2026-10-20](../reports/phase5-completion-2026-10-20.md).

#### Publicación autorizada del cierre y fases siguientes

El usuario aclara expresamente que desea publicar el cierre de FASE 5, con commit
y push a main. La FASE 6 permanece pendiente. Se incorpora
[NEXT_PHASES](NEXT_PHASES.md), con objetivos, incrementos y criterios de cierre:
FASE 6, TradingView y simulador virtual conectado; FASE 7, cuenta demo externa;
FASE 8, ejecución real supervisada opcional, sujeta a una autorización específica.
La secuencia conserva TRADINGVIEW_PLAN y no habilita conexiones u operaciones.

Antes de preparar el commit se cotejan de nuevo las 139 fuentes con el manifiesto
de las 1598 pruebas: sin cambios. Las reglas de Git conservan también los bytes de
las nuevas pruebas, recursos web, auditoría y evidencias para mantener esas huellas
al clonar. La hoja de ruta y su enlace desde README son cambios documentales.
La consulta remota, con acceso a red tras el bloqueo de la sesión aislada, confirma
que main del servidor conserva f5e654435f42efcb76c53a82f812a541bf78d521; no hay
historia remota nueva que integrar antes de preparar la publicación.

El cotejo de bytes del índice confirma las ocho fuentes nuevas y las evidencias.
Detecta además tres diferencias previas de finales de línea: en disco CRLF y en
los blobs antiguos LF, con contenido normalizado idéntico. Los 131 originales
anteriores y sus blobs se mantienen intactos. Para conservar exactamente lo que
se probó, se añaden copias de esos tres archivos en tested-source-bytes, junto a
git-publication-check.json. No se reescriben los manifiestos o pruebas anteriores.

#### FASE 5.1 — Diagnóstico y propuesta de rendimiento

20/10/2026. El usuario denomina FASE 5.1 a la mejora de rendimiento y solicita
investigar soluciones y proponer medidas. Se revisan las lecturas del catálogo,
consultas, HTTP y navegador, y documentación oficial de Python 3.14 y MDN.

Medición HTTP local con servidor temporal propio, tres muestras por ruta:
medianas 3,333 s en Inicio, 3,294 s en Experimentos y 2,447 s en Consumo. Conjunto
de 92 registros y 805 archivos catalogados. El perfil separado identifica el
escaneo repetido y las comprobaciones de rutas; no se suman tiempos acumulados
solapados. La caché del sistema operativo no se controló y no se calcula p95
con estas tres muestras. El servidor temporal se cierra al terminar.

Se entrega [PHASE5_1_PLAN](PHASE5_1_PLAN.md) y evidencia en
[baseline.json](../reports/phase5-1-diagnosis-2026-10-20/baseline.json). Se prioriza
índice y resúmenes en memoria con invalidación, lectores por petición, reducción
de trabajo duplicado, cancelación en el navegador, concurrencia limitada y caché
condicional de estáticos. Los objetivos de latencia son propuestas por verificar.
NEXT_PHASES incorpora esta fase antes de TradingView. No se modifica aplicación,
pruebas, evidencias previas o PROJECT_STATUS; no se declara completada FASE 5.1.
La petición de esta fase es de investigación y propuesta, sin publicación Git.

#### FASE 5.1 — Implementación y comprobaciones

21/10/2026. El usuario solicita implementar la propuesta. LabService mantiene
instantáneas independientes del catálogo y resúmenes, con publicación atómica,
comprobación de dependencias cada dos segundos y una única actualización en curso.
Se mantienen separados el índice compartido, el presupuesto de lectura y los
avisos de cada petición. Caché de metadatos acotada a 32 MiB de peso estimado e
índice a 16 MiB. Los originales y las verificaciones de detalle no usan esa caché.

El escaneo reutiliza comprobaciones de los componentes de rutas durante su propia
enumeración; antes de abrir un archivo se vuelven a validar enlaces y junctions.
Se detectan cambios durante la lectura y se reutilizan bytes y detalle dentro de
una consulta, sin permitir continuar desde la caché después de agotar su presupuesto.
Las respuestas HTTP se atienden con cuatro hilos como máximo, cola TCP acotada,
tiempo de espera de conexión y error 503 reintentable si todos están ocupados.
Las rutas desconocidas se rechazan antes de construir el catálogo.

El navegador cancela consultas abandonadas, conserva filtros al actualizar y
presenta la ficha sin esperar a la primera cuenta. Los listados muestran la fecha
de los resúmenes y los fallos de actualización; el refresco forzado relee fuentes.
HTML/CSS/JS incorporan ETag; datos y originales conservan no-store. La medición
de navegación queda en atributos del DOM, sin añadir detalles técnicos al flujo.

Las pruebas detectaron un cierre TCP con RST al devolver 503 en Windows: se consumen
cabeceras acotadas antes de responder. También se observó que lstat/fstat difieren
en la semántica de ctime en este entorno; se cotejan identidad, tamaño y mtime
entre ambas APIs, y ctime entre las lecturas fstat. Se conserva el XML del pase
fallido como diagnóstico, sin sumarlo a pruebas aprobadas.

Resultado focalizado final: 80 pruebas de interfaz aprobadas (51 anteriores y 29
nuevas) en 18,18 s. Evidencias/registro contable: otras 48 aprobadas en 22,65 s.
Son 128 casos distintos; no se presentan como una nueva ejecución de toda la
colección histórica de 1598 casos. Caché pytest desactivada y temporal exclusivo
por ejecución. La navegación, gráficos, comparación y filtros se revisan en IAB
sin modificar la pestaña o servidor 8765 que el usuario mantiene abiertos.

Se añade scripts/benchmark_lab.py para medidas HTTP repetibles. En la versión
final, 30 muestras por ruta y configuración de dos/cuatro hilos, incluyendo
comprobaciones periódicas del índice. Con cuatro hilos: medianas de 1,98, 2,33
y 2,18 ms en Inicio, Experimentos y Consumo; p95 de 19,38, 22,66 y 15,29 ms.
Primera consulta en servidor nuevo: 2,402 s, sin controlar la caché del sistema.
La referencia histórica se carga desde Git sin alterar el checkout. Los ensayos
preliminares se distinguen de las series finales y conservan sus resultados.

Una fuente artificial añadida aparece por HTTP en 2,170 s con el intervalo de
actualización por defecto. Auditoría real: mismos 92 registros, 40 cuentas con
detalle y 150 con resumen, sin inferencias, backtests o reservas. Los 131 archivos
anteriores del motor y pruebas conservan sus huellas. Se registra el cierre tras
terminar el cotejo final de medidas, fuentes, documentos y servidores temporales.

La colección general detecta una copia de test_structured_freshness.py archivada
en la evidencia de publicación de FASE 5; pytest intentaba importarla como prueba.
Se conserva la copia y se añade pytest.ini con testpaths=tests para delimitar el
directorio de pruebas del proyecto. La colección errónea se conserva como
diagnóstico; el cotejo posterior debe recoger exactamente los 1598 nodos anteriores
y los 29 nuevos, sin ejecutar las copias históricas de informes.

#### Cierre comprobado de FASE 5.1

La colección final recoge exactamente 1627 nodos, sin errores: 1598 anteriores y
29 nuevos. Las series definitivas de 30 muestras mantienen sus fuentes estables.
Referencia FASE 5: medianas 3155,18/3196,91/2426,35 ms; versión final de cuatro
hilos: 1,98/2,33/2,18 ms y p95 19,38/22,66/15,29 ms. Auditoría final: 838 archivos
sin cambios, mismos registros y cuentas, cero acciones prohibidas. Se conservan
separados los ensayos preliminares y diagnósticos fallidos, sin contarlos como éxito.

Revisión visual terminada: cinco pantallas, filtros conservados al sondear y al
forzar refresco, navegación rápida, cambio de cuenta, dos gráficos y comparaciones
admitidas/bloqueadas; sin errores de consola. Las observaciones de navegación
incluyen petición y construcción del DOM, no pintado físico. Servidor y pestaña
temporales cerrados; el servidor 8765 y Chrome del usuario permanecen abiertos.

README, guía, plan, siguiente fase e informe quedan actualizados. PROJECT_STATUS
se actualiza únicamente al cerrar esta fase. El desarrollo permanece local sobre
47d2fc5, sin commit o push nuevos. FASE 6 pendiente. Informe:
[phase5-1-completion-2026-10-21](../reports/phase5-1-completion-2026-10-21.md).

### 21/10/2026 — Definición de FASE 5.2: conversación con el agente

Por petición del usuario se crea el [plan de FASE 5.2](PHASE5_2_PLAN.md), después
de FASE 5.1 y antes de TradingView. Define conversación local persistente,
propuestas estructuradas y versionadas, revisión explícita, pruebas históricas
mediante los controles existentes y explicación de resultados con sus evidencias.
Se divide en seis incrementos; el primero será contratos y persistencia.

Se actualizan la hoja de ruta y los enlaces del README. El puente del chat hacia
operaciones concretas del simulador queda descrito como incremento 6.6; las cuentas
demo y la posible ejecución real mantienen sus fases y autorizaciones propias.
Se conservan límites, presupuestos y evidencias anteriores y la fluidez de FASE 5.1
como requisitos de implementación.

La FASE 5.2 queda definida, sin implementación ni cierre. Este cambio es documental:
no se ejecutan inferencias ni experimentos, no se modifica PROJECT_STATUS y no se
realizan commit o push.

### 21/10/2026 — Implementación y cierre de FASE 5.2

Se entregan los seis incrementos del plan: almacenamiento SQLite de conversaciones,
mensajes, revisiones y trabajos; pantalla Conversar con el agente; contrato Ollama
independiente; propuestas con revisión humana; comparación histórica explícita;
discusión de resultados y recuperación. Las consultas permanecen separadas de las
acciones POST con origen y token locales, JSON acotado e identidades idempotentes.

Un trabajador y una cola acotados mantienen disponibles las consultas. El bloqueo
del sistema operativo evita dos escritores; los reinicios no reenvían trabajos.
Los presupuestos iniciales compartidos del chat son 24 intentos de respuesta y
cuatro comparaciones de dos backtests. Fallos, cancelaciones y duplicados no
reabren capacidad. No se modifican campañas, permisos o presupuestos anteriores.

Se verifican revisiones, fuente y código antes de calcular; se rechazan historia
insuficiente y contradicciones EMA/SMA. Comparaciones equivalentes tampoco se
repiten cambiando hipótesis, criterio o representación decimal. Las propuestas
solo admiten los cruces largos D1 existentes. Se conservan aprobación, copia BCE,
resultados de Python, conclusión y enlaces a la ficha y evidencias.

La selección final aprueba 267 casos, incluidos 46 nuevos. Colección completa:
1673 nodos, los 1598 anteriores más 29 de FASE 5.1 y 46 de FASE 5.2. No se ejecutó
toda la colección: se interrumpió una ejecución amplia y se completó la selección
documentada. Un lanzamiento inicial apuntaba a un archivo de pruebas inexistente;
no ejecutó casos y se conserva como diagnóstico. La repetición final comprueba
también la procedencia duradera del proveedor. Fuentes finales estables, caché
desactivada y temporales GUID exclusivos según AGENTS.md.

Ensayo real en raíz aislada: cuatro peticiones, 1800/680 tokens, API 0 USD, una
comparación y dos backtests. Se conservan confusión inicial SMA/EMA, explicación
rechazada por el control de cifras y sus correcciones. Sin reintentos automáticos;
la revisión humana sigue siendo necesaria. La interpretación del modelo se
distingue de las comparaciones comprobadas por Python.

Revisión en navegador: propuesta, aprobación, métricas, enlace a experimento y
fuentes, historial tras reinicio y consumo, sin errores de consola. Durante una
inferencia real, p95 HTTP de 23,70/3,40/20,26 ms, 30 muestras por ruta. Auditoría
de consulta sin acciones prohibidas y 838 evidencias anteriores idénticas. Se
cierran servidores y pestaña temporales, conservando el servidor 8765 del usuario.

Se actualizan guía, plan, hoja de ruta, README y PROJECT_STATUS únicamente al
cierre de la fase. Desarrollo local sin commit ni push; FASE 6 pendiente.
[Informe de cierre](../reports/phase5-2-completion-2026-10-21.md).

### 21/10/2026 — Avance local de FASE 6, sin cierre

Por autorización del usuario para continuar el desarrollo se implementan contratos
SMA/EMA de intercambio, generación Pine v6 con huellas, referencia OHLC con
aperturas siguientes y lector CSV genérico de mapa explícito. Se conservan
originales, vistas previas, aprobaciones y progreso de importación; el bloqueo de
escritor impide cargas simultáneas. No se presume un esquema real de Strategy Report.

Se añade inbox SQLite duradero, receptor autenticado exclusivamente loopback y
contabilidad virtual independiente del modelo. Recibir no contabiliza; secuencias,
saldo, cantidad, costes y riesgo se comprueban al procesar. Duplicados, conflictos,
huecos, retrasos y cambios de motor quedan visibles. Nuevas entradas se pausan ante
rechazos o drawdown. No se inventan fills ni se reemplaza capital por cifras externas.

La pantalla Simulación y TradingView ofrece paquetes, cuentas, historial, CSV,
inbox, revisión de pendientes, valoración manual y conciliación. Los POST requieren
origen y token locales. La aprobación identifica la cuenta y el inbox revisados;
un evento o conflicto nuevo la invalida. Las consultas no crean cuentas, ejecutan
operaciones ni llaman a proveedores.

396 pruebas seleccionadas aprobadas, 129 nuevas; colección completa 1802,
conservando los 1673 nodos anteriores. No se ejecutó toda la colección: se conserva
el intento amplio interrumpido. Caché desactivada y temporales GUID exclusivos.
Se verifican concurrencia, recuperación, alteraciones y límites, sintaxis JS y
consulta sin efectos: 92 registros, 190 cuentas, 47 fuentes y 840 archivos idénticos.
Los 839 archivos de la auditoría anterior permanecen iguales.

Ensayo artificial: compra a apertura 9, venta a apertura 11, capital 100, coste
1 % por lado, efectivo 101,8 y costes 0,2; recepción fuera de orden, reinicio,
deduplicación entre mensaje Pine y evento canónico y conciliación alineada.
Navegador: preparación, cuenta revisada, JSON sin procesamiento automático,
aprobación, CSV con original exacto y duplicados sin nuevo efecto; consola limpia.
p95 HTTP aislado de simulación 29,90 ms, treinta muestras. Se conservan también
la constante equivocada del primer comprobador y los diagnósticos de profundidad
JSON y cierre HTTP de Windows, con sus correcciones verificadas.

Contraste adicional entre referencia OHLC y libro: 48 casos artificiales de
SMA/EMA, dos pares de ventanas, doce semillas y cuatro pares, con 3360 estados
al cierre coincidentes en efectivo, cantidad y patrimonio y coincidencia final
de costes/PnL realizado. Usa límite de drawdown 100 % solo para aislar aritmética;
las pausas por riesgo se prueban aparte, sin cambiar el predeterminado del 20 %.
Se conservan resultados, semillas y huellas; no ejecuta Pine ni usa datos externos.

La compilación Pine, equivalencia externa, CSV real, relay HTTPS y puente de
intenciones desde chat siguen pendientes. Se documenta que ese puente exige un
modo manual separado de las identidades de ejecución de estrategia. Sin nuevas
inferencias reales, conexión de cuenta, commit o push. Se conservan los cambios de
FASES 5.1/5.2. PROJECT_STATUS no se actualiza porque FASE 6 permanece abierta.
[Informe de avance](../reports/phase6-progress-2026-10-21.md) y
[guía local](TRADINGVIEW_LOCAL.md).

### 21/10/2026 — Diagnóstico del primer gráfico TradingView

El usuario aporta RE10142: el control del Pine detiene la ejecución en la primera
vela por configuración incompatible. La cabecera comunicada por el usuario es
«Euro/Dólar estadounidense - 1 - OANDA»: el intervalo seleccionado es un minuto,
mientras que el contrato exige 1D. Se indica cambiar a 1 día y comprobar de nuevo;
el resto de propiedades del gráfico no queda validado por esa cabecera.

El mensaje v1 era genérico. Se incorpora el generador Pine v2, con valores
recibidos y requeridos en cada discrepancia. Conserva los cinco controles, sin
normalizar silenciosamente proveedores/modificadores ni relajar unidades. Los
contratos v1 siguen admitidos y su script original se reproduce byte a byte; v2
tiene una identidad propia. Se prepara un paquete diagnóstico sin registrar cuenta.
Las cuentas previas mantienen la protección existente ante cambios de motor.

131 pruebas afectadas aprobadas, incluidas dos de compatibilidad de versiones y
diagnóstico. La nueva versión del Pine aún requiere compilación en TradingView;
no se declara resuelta la validación completa del gráfico. Evidencia en
`reports/phase6-chart-guard-2026-10-21/`. Sin cierre de fase, cambio de PROJECT_STATUS,
commit, push o conexión de cuenta.

### 22/10/2026 — Primera inspección de precios Dukascopy

Se reciben dos CSV originales. El BID contiene 528 velas H1 de enero de 2025; el
ASK contiene 660 velas M1 del 22/10/2026. No comparten ninguna apertura/cierre.
Se incorpora `python -m trading_ai.dukascopy`: conserva originales y huellas,
valida formato UTC, precios, volumen, duplicados y alineación, y bloquea el
emparejado con fechas o intervalos distintos. La identidad de proveedor/par/lado
es declarada por el usuario porque el cuerpo del CSV no contiene esos campos.

Se informan huecos y días parciales sin rellenarlos ni clasificarlos como sesiones
verificadas. El BID contiene 27 fechas UTC, 17 completas de 24 horas y cuatro
intervalos sin observaciones. No se agregan días, generan señales/fills ni procesan
cuentas. Los contratos, el generador Pine y el motor contable mantienen sus bytes.
Los originales aportados permanecen en `.local/dukascopy/`, fuera de Git.

La primera comprobación sigue pendiente del ASK horario del mismo enero. Se añade
la [guía de Dukascopy](DUKASCOPY.md), indicando el reinicio del formulario observado
al abrir Export, el alcance del lector y las tareas pendientes. FASE 6 permanece
abierta; no se cambia PROJECT_STATUS ni se realiza commit o push.

152 pruebas seleccionadas aprobadas, incluidas 21 del nuevo lector. Se guardan
diagnóstico, resultados y huellas en `reports/phase6-dukascopy-2026-10-22/`.
El navegador no entrega el archivo tras el intento automático de descargar el
ASK corregido; se deja el formulario configurado para su descarga manual.

### 22/10/2026 — Muestra BID/ASK de Dukascopy emparejada

El usuario aporta el ASK H1 de enero de 2025. Se inspecciona junto al BID anterior
en un directorio nuevo, conservando ambas inspecciones y originales. Coinciden las
528 aperturas/cierres, sin intervalos exclusivos de un lado, duplicados, errores
OHLC ni diferencias negativas ASK-BID de apertura/cierre. La comprobación
independiente usa CSV, datetime y Decimal, sin importar el lector del proyecto.

Se conservan la inspección inicial incompatible y sus evidencias. La muestra
correcta tiene su propio informe en `reports/phase6-dukascopy-paired-2026-10-22/`.
No cambian fuentes ejecutables ni se repiten pruebas unitarias sin cambios:
se comprueban sus huellas frente a la ejecución anterior de 152 pruebas aprobadas.
No se ejecuta una estrategia diaria con un mes de datos, ni se procesan cuentas.
La agregación con sesión explícita, simulación con spread y descarga automática
continúan pendientes. No hay cierre de fase, modificación de PROJECT_STATUS,
commit o push.

### 22/10/2026 — Descargador Dukascopy y agrupación diaria UTC

Se implementa `python -m trading_ai.dukascopy_history`, independiente de contratos
Pine y cuentas. Descarga archivos públicos H1 por mes cerrado para EUR/USD, con
peticiones en serie, límites, originales preservados, huellas y caché verificable.
Los errores se conservan como ejecuciones incompletas. No se considera una
respuesta vacía, HTML o HTTP 202/429 como datos ni se reintenta indefinidamente.

La API más reciente devuelve un reto de acceso; no se utiliza para descargar.
La ruta pública de archivos redirige entre hosts de Dukascopy y algunos destinos
son HTTP. Se registra esa limitación de transporte sin atribuir autenticación.
El primer intento amplio detectó una segunda redirección legítima no prevista por
la comprobación inicial; se corrige admitiendo los dos hosts y la misma ruta.

Ensayo real de enero de 2025: dos archivos descargados; los 528 registros con
actividad de cada lado coinciden exactamente en fechas y OHLC con los CSV del
usuario mediante un comprobador independiente. Los registros planos de volumen
cero se excluyen de forma identificada. Los originales binarios se conservan.

Se forman 27 sesiones UTC observadas, manteniendo domingos y días parciales,
primera/última observación e intervalos ausentes. No se rellenan precios ni se
declara equivalencia con otro proveedor. La preparación de señales SMA 20/60
requiere 61 sesiones y se bloquea con huecos internos. No genera operaciones.
La reproducción offline conserva el mismo contenido diario con cero peticiones.

La ampliación 2024–2025 permanece incompleta por HTTP 429, también tras comprobar
de nuevo el acceso más de tres minutos después. No se inventa histórico ni se
presenta la descarga o la estrategia como completadas. Se conserva evidencia de
los intentos, contraste, caché, reproducción y 185 pruebas seleccionadas aprobadas
(33 del descargador, 21 del lector CSV y 131 relacionadas) en
`reports/phase6-dukascopy-history-2026-10-22/`. FASE 6 sigue abierta, sin cambio de
PROJECT_STATUS, commit, push ni conexión de cuenta.

### 22/10/2026 — Prueba Dukascopy con spread y consulta desde la interfaz

Se añade `dukascopy_backtest`: reconstruye el histórico desde BI5, contrasta huellas
y sesiones, calcula SMA sobre cierres BID y ejecuta en la primera apertura realmente
observada de la siguiente sesión. Compra a ASK, vende y valora a BID; el spread no
se carga dos veces. Capital y cantidad son hipotéticos y la comisión es una tasa
supuesta explícita. No se modelan swaps, deslizamiento, liquidez o intravela; no se
fuerza el cierre final ni se inventa una ejecución tras el último dato.

El cálculo es independiente de Pine y del libro contable. Conserva entradas, reglas,
resultados y huellas de sus fuentes. La interfaz añade selección de históricos
preparados, acción de verificar/calcular y consulta de resultados. GET no descarga
ni calcula; los POST mantienen el origen y token locales. No se crean cuentas.

La muestra real de enero conserva 27 sesiones; se guarda `insufficient_history`
con 34 sesiones pendientes para SMA 20/60, sin operaciones ni rentabilidad. Se
comprueba el recorrido en el navegador. Los ensayos con longitud suficiente son
artificiales y se identifican como tales. La nueva reanudación 2024–2025 recibe
HTTP 429 en la primera petición y se detiene; el histórico amplio sigue pendiente.

299 pruebas seleccionadas aprobadas, incluida la integración y las comprobaciones
de laboratorio/rendimiento; no se ejecuta la colección completa. Se revisa la
sintaxis JavaScript y la interfaz con datos reales insuficientes y un caso
artificial aislado. Pruebas y evidencia en
`reports/phase6-dukascopy-spread-2026-10-22/`. No se cierra
FASE 6, modifica PROJECT_STATUS ni realiza commit o push.

### 22/10/2026 — Importación de históricos y primera prueba con precios reales

Se incorpora `market_history` para CSV Dukascopy BID/ASK y archivos anuales H1
JSON gzip de EV Trading Labs. Preserva originales, atribución, fechas UTC explícitas
con fin exclusivo, huellas, horas seleccionadas/excluidas y controles de calidad.
La lectura reconstruye desde los originales y contrasta todo el inventario y diario.
Se mantienen los históricos BI5 anteriores y las fronteras de origen/token locales.
La interfaz permite importar, consultar la calidad y calcular mediante acciones
separadas. Las consultas no descargan ni ejecutan estrategias.

El exportador Dukascopy observado limita H1 a aproximadamente un mes. Dos rutas
públicas FXCM responden 403, error 1010. Se descarga sin cuenta el archivo anual
EUR/USD H1 de 2025 desde el catálogo de EV Trading Labs: 199.128 bytes, 6.223 velas,
313 fechas UTC. El catálogo declara agregación de Dukascopy y uso gratuito con
atribución. No se certifica descarga directa del bróker ni transporte final que
el navegador no expuso. Un contraste independiente reproduce exactamente fechas
y OHLC de las 528 velas de enero frente a ambos CSV originales.

El 25/12 presenta dos huecos internos: la simulación del año completo queda
bloqueada sin métricas. Antes de calcular resultados se fija el tramo hasta el
24/12, con fin exclusivo 25/12: 6.122 velas y 307 sesiones; las 101 velas restantes
se conservan en el original y se identifican como fuera del período. El corte
responde a calidad, no a rentabilidad. Se bloquean también tramos sin observaciones
superiores a 96 horas, incluidos extremos, sin declarar un calendario verificado.

SMA 20/60, 1.000 USD hipotéticos, cantidad 1 EUR y comisión supuesta 0,001 producen
tres ejecuciones, una operación cerrada y una posición de 1 EUR abierta. Patrimonio
final 999,98870447 USD. Una reconstrucción independiente con Decimal reproduce
las 307 sesiones, medias, señales, ejecuciones, caja, posiciones, capital y drawdown.
La importación real anual y CSV se comprueba mediante la API HTTP local; el botón
de cálculo y el resultado se comprueban en navegador. La automatización del selector
nativo no se completó: no se declara validada la selección manual de archivos.
Las cuentas virtuales y el inbox no cambian.

339 pruebas seleccionadas aprobadas (40 nuevas y las 299 seleccionadas anteriores),
sin ejecutar la colección completa. Se comprueba sintaxis JavaScript y se conserva
evidencia, fuentes probadas y capturas en
`reports/phase6-market-history-import-2026-10-22/`. El histórico 2024–2025 completo
sigue pendiente; FASE 6 permanece abierta, sin cambio de PROJECT_STATUS, commit o push.

### 22/10/2026 — Repetición fija en 2024 y comparación de períodos

Antes de descargar el año adicional se fija un protocolo: mismos SMA 20/60, largos,
1.000 USD hipotéticos, cantidad 1 EUR, comisión supuesta 0,001 y límites del
calendario que en la prueba de 2025, hasta el 24/12. Cada período empieza sin
posición ni medias previas. No se buscan parámetros o cortes por rentabilidad.

Se obtiene públicamente de EV Trading Labs el archivo anual EUR/USD H1 de 2024,
195.309 bytes, 6.247 velas y 314 fechas UTC. El período fijo conserva 6.144 velas,
308 sesiones y 103 velas fuera del período en el original. El año completo presenta
dos huecos el 25/12 y queda bloqueado sin métricas. Los originales anuales de ambos
años están disponibles; no se declara cobertura completa ni se relaja la política.

2024 produce seis ejecuciones, tres operaciones cerradas y patrimonio final
999,96832951 USD, sin posición abierta. 2025 conserva tres ejecuciones, un cierre,
1 EUR abierto y 999,98870447 USD. Ambos resultados son negativos con la comisión
supuesta. Un programa independiente con Decimal reproduce medias, señales,
ejecuciones, comisiones, spread y cada punto de capital y drawdown de ambos períodos.
Son datos retrospectivos; no se declara validación prospectiva ni robustez estadística.

Se añade `market_comparison`, acción HTTP explícita y ficha en la interfaz.
Requiere misma configuración, procedencia, política de sesión y motor, con períodos
sin solaparse. Guarda copias verificables; las consultas no calculan estrategias
ni procesan cuentas. El listado usa metadatos acotados y la ficha contrasta sus
entradas. Las cuentas virtuales y el inbox permanecen sin cambios.

363 pruebas seleccionadas aprobadas, 24 nuevas de comparación y las 339 anteriores;
no se ejecuta la colección completa. Se comprueban sintaxis JavaScript y formulario
de comparación en navegador con los resultados reales. Evidencia en
`reports/phase6-period-validation-2026-10-22/`. FASE 6 sigue abierta; no se modifica
PROJECT_STATUS ni se realiza commit o push.

### 22/10/2026 — Referencias y sensibilidad a comisiones

Antes de calcular se fija el protocolo de SMA 20/60 frente a efectivo USD sin
intereses y comprar/mantener 1 EUR tras 61 sesiones completas. Se mantienen los
períodos hasta el 24/12 de 2024 y 2025 y capital hipotético de 1.000 USD. Tasas
supuestas por ejecución 0; 0,0005; 0,001; 0,002, sin seleccionar una ganadora.
La referencia compra ASK y termina valorada a BID; no hay cierre forzado ni una
comisión de salida inexistente. Se conservan diferencias de tiempo en mercado.

Se añade `market_benchmark`, persistencia con entradas exactas, resumen acotado,
acción HTTP explícita y ficha de escenarios. El cálculo verifica originales; las
consultas no ejecutan estrategias ni procesan cuentas. No se modifica el motor
SMA, los contratos, Pine ni el libro contable. Los años completos siguen bloqueados.

SMA queda por debajo del efectivo en los ocho escenarios incluso con comisión
cero. Supera a comprar/mantener en 2024 y queda por debajo en 2025. Bajo la tasa
base 0,001, SMA conserva 999,96832951 y 999,98870447 USD; la referencia conserva
999,94493691 y 1000,08745140 USD. No se concluye robustez o rentabilidad general.

391 pruebas seleccionadas aprobadas, 28 nuevas y las 363 seleccionadas anteriores,
sin ejecutar toda la colección. Un cálculo independiente stdlib/Decimal desde los
gzip reproduce los ocho escenarios, 44 ejecuciones y 4.920 puntos de patrimonio.
La tasa base coincide con las pruebas anteriores. Se comprueban sintaxis JavaScript,
formulario real y selector de comisión en navegador. Evidencia en
`reports/phase6-reference-costs-2026-10-22/`. FASE 6 sigue abierta; PROJECT_STATUS
no cambia y no se realiza commit o push.

### 22/10/2026 — Conversación y comparación con históricos BID/ASK

Se incorpora `conversation_prices`: revisión humana de cruces SMA base/variante,
histórico aportado con período explícito, cantidad EUR y costes supuestos. Reutiliza
trabajador, revisiones, aprobación concreta y presupuesto global de cuatro
comparaciones de BCE; no lo amplía ni reinicia. Guardar no ejecuta. Los originales
se verifican al revisar, aprobar y ejecutar; cambios de datos o motor bloquean.
Los resultados conservan entradas y aprobación, y se consultan sin recalcular.

La interfaz permite elegir la fuente, ver métricas, curvas y ejecuciones dentro
de la conversación y adjuntar la evidencia a una pregunta. EMA sigue disponible
en BCE; no se traduce silenciosamente a SMA. No se modifica el motor de precios,
Pine, contratos ni cuentas virtuales. Las peticiones de operaciones actuales siguen
fuera de este recorrido de investigación histórica.

Ensayo real con Qwen3.5:4b local: conserva SMA 15/45, aunque añade preguntas y avisos
no pedidos, que quedan en el borrador incompleto. Se revisa explícitamente frente
a SMA 20/60 sobre 307 sesiones de 2025, capital hipotético 1.000 USD, 1 EUR y
comisión 0,001. La base conserva 999,98870447 USD y la variante 999,99492622 USD.
La variante pierde menos pero tiene mayor caída; el criterio no queda respaldado.
Una reconstrucción independiente reproduce ocho ejecuciones y 614 puntos de capital.

La explicación real del modelo afirma cumplimiento cualitativo de otro criterio.
Se conserva el error y el original, y se antepone el veredicto de Python en la
interfaz junto a la interpretación sin verificación semántica. No se repite la
inferencia para conseguir una respuesta favorable. Consumo: dos respuestas y una
comparación del presupuesto existente; cuentas e inbox sin cambios.

463 pruebas seleccionadas aprobadas, 26 nuevas, 46 de conversación previa y las
391 seleccionadas anteriores; no se ejecuta la colección completa. Se comprueban
sintaxis JavaScript y recorrido real en navegador. El servicio del modelo se
arranca con la identidad habitual de Windows para leer sus archivos existentes,
sin cambiar permisos generales ni volver a descargarlo. Evidencia en
`reports/phase6-chat-prices-2026-10-22/`. FASE 6 sigue abierta, sin cambio de
PROJECT_STATUS, commit o push.

### 22/10/2026 — FASE 6: explicaciones contrastadas del chat

Se añade `conversation_evidence_explanation_v1` para mensajes con un resultado
BCE o BID/ASK adjunto. La petición incorpora explícitamente el criterio registrado,
la evaluación recalculada desde las métricas y una huella del resultado. El modelo
solo selecciona hasta tres aspectos; el texto visible se compone en Python.
Se rechazan campos libres, propuestas y evaluaciones incompatibles, conservando
original, error, tokens y reserva sin reintento. Las huellas se comprueban antes
y después de inferir. El esquema efectivo cuenta en la cota de contexto.

Se mantiene el modo de propuestas sin evidencia, los límites 24/4, las cuentas y
los motores anteriores. La interfaz identifica texto compuesto por Python y
conserva las interpretaciones anteriores con aviso. Los fallos muestran un resumen
de Python solo cuando la evidencia sigue íntegra. No se modifica PROJECT_STATUS.

41 pruebas nuevas y 113 pruebas de conversación aprobadas. La selección ampliada
de 525 obtiene inicialmente 524 aprobadas y un fallo WinError 10053 al probar el
rechazo de transporte chunked del receptor HTTP. Esa prueba pasa al repetirla
aisladamente (1/1), sin cambiar el receptor ni ocultar el fallo original.
No se ejecuta la colección completa. Temporales exclusivos y caché desactivada.

Una única respuesta real de Qwen3.5:4b sobre el resultado ya guardado conserva el
criterio y veredicto correctos. Elige rentabilidad, caída y alcance; omite comisiones
solicitadas. Se registra esa limitación de cobertura, sin repetir para mejorar la
respuesta. El texto explica que perder menos con mayor caída no respalda el criterio.
291 tokens de entrada, 96 de salida, unos 25,7 segundos; quedan 21 respuestas y tres
comparaciones. No se ejecutan backtests nuevos ni se reescribe el comentario erróneo
anterior. Evidencia en `reports/phase6-chat-explanations-2026-10-22/`. FASE 6 abierta,
sin commit o push.


### 22/10/2026 — FASE 6.6: operaciones virtuales manuales desde conversación

Nuevo registro manual independiente de backtests y fills de estrategia. Una
petición limitada «simula comprar/vender cantidad EUR/USD» se conserva con cuenta,
cotización BID/ASK aportada, estado y versión revisados. Guardar no mueve saldo;
una segunda aprobación aplica los controles de la transición contable existente
y confirma aprobación y asiento en una única transacción. Duplicados, concurrencia,
reinicio y fallo de persistencia no duplican ejecución. Se conservan rechazos,
cancelaciones y huellas; cambios de cuenta/motor o precio caducado exigen revisión.

El modelo no interpreta ni ejecuta este modo; no se consumen respuestas o comparaciones.
No se obtiene cotización de mercado. Compra ASK, venta/valoración BID, sin apalancamiento
ni acumulación. La interfaz muestra previsión y confirmación, saldo, posición, patrimonio,
resultado realizado y comisiones. Cuentas y almacenamiento anteriores permanecen iguales.

562 pruebas seleccionadas aprobadas, 37 nuevas; no toda la colección. Caché desactivada
y temporal GUID exclusivo. Demostración en navegador con cuenta manual de ejemplo,
1.000 USD, 1 EUR y comisión 0,001: compra ASK 1,1002 y venta BID 1,101 artificiales.
Cierra sin posición con 999,9985988 USD y resultado realizado −0,0014012 USD. La
subida de precio no compensa costes del ejemplo. Se verifica de forma independiente
con Decimal; no se presenta como rendimiento de una estrategia o cotización real.

Reservas del chat sin cambios (3 respuestas, 1 comparación). Evidencia en
`reports/phase6-chat-operations-2026-10-22/`. FASE 6 sigue abierta, sin modificación
de PROJECT_STATUS, commit o push.


### 22/10/2026 — Publicación autorizada del trabajo acumulado

El usuario solicita commit y push a GitHub y continuar después. Se preparan los
avances locales de FASE 5.1, FASE 5.2 y los incrementos de FASE 6; esta sigue abierta.
Fetch confirma HEAD/origin/main en 47d2fc5. Los modelos, ejecutables, bases locales
y configuración privada siguen ignorados; no se encuentran patrones de credenciales
en los archivos candidatos. Diez manifiestos previos conservan sus 190 evidencias.
Se comprueban los bytes del índice y se amplían las reglas de preservación de Git.

Se conserva la selección de 562 pruebas aprobadas con fuentes idénticas. Una
comprobación completa adicional se interrumpe por el coste de las campañas antiguas,
con salida parcial conservada y sin declararla completa o aprobada. No se modifica
PROJECT_STATUS en esta publicación. Detalle en `reports/publication-2026-10-22/`.
El identificador del commit y la confirmación del push se comunicarán tras publicarlo.


### 22/10/2026 — Publicación confirmada y valoración manual sin operación

El commit 0bd90113c5ea47731da52a57d26d9b5f6dfeafdc queda publicado en origin/main.
Push y consulta posterior de refs/heads/main confirman el mismo SHA, sin diferencias
local/remoto y con árbol limpio antes de continuar. Incluye los avances acumulados
hasta las operaciones manuales; FASE 6 permanece abierta.

Después del push se implementa manual_valuation, un avance local adicional. Reutiliza
la base y transición de riesgo manual existentes sin cambiar sus huellas ni migrar
la base. Otra aprobación de BID/ASK y fecha UTC, vinculada al estado y código,
actualiza patrimonio, caída y pausa sin cambiar saldo, EUR, comisiones, resultado
realizado o número de operaciones. Un asiento atómico conserva origen y aprobación;
repeticiones, cambios de cuenta/motor e instantes incompatibles se comprueban.
Las intenciones pendientes con otra cadena quedan bloqueadas hasta revisarlas.

586 pruebas seleccionadas aprobadas, 24 nuevas; caché desactivada y temporal GUID
exclusivo. No se ejecuta otra colección completa. La interfaz muestra antigüedad
que avanza, avisos de datos ausentes/futuros/caducados, resultado no realizado y
últimas valoraciones. La lectura usa una instantánea y no opera ni llama al modelo.

En navegador se abre una cuenta de ejemplo con 1.000 USD y se compra 1 EUR a ASK
artificial 1,1002; después se valora a BID artificial 1,09, sin otro fill o comisión.
Patrimonio 999,9886998 USD y resultado no realizado −0,0113002 USD, con la posición
virtual aún abierta. No es evidencia de rendimiento de una estrategia. Una petición
adicional del usuario en la aplicación se conserva sin atribuirla al ensayo.

Evidencia en `reports/phase6-manual-valuation-2026-10-22/`. Este avance posterior
queda local, sin segundo commit/push. PROJECT_STATUS no cambia; FASE 6 sigue abierta.

### 22/10/2026 — Contraste de ejecuciones y elección de JForex

Se implementa execution_comparison: CSV UTF-8 con mapa, unidades, zona, metadatos
y tolerancias explícitos frente a una prueba BID/ASK guardada. Alinea por acción
y fecha únicas, conserva ausencias y ambigüedades, compara con aritmética decimal
y no convierte costes desconocidos en cero. Una fila inválida impide comparar un
subconjunto silencioso. Coincidir no autentica origen, formato o motor externo.

La interfaz ofrece una vista previa sin escritura y un guardado revisado aparte,
vinculado a su huella. Archiva CSV, resultado, resumen y copias de la simulación y
precios; lecturas verifican huellas sin recalcular o tocar cuentas. El catálogo
consulta metadatos acotados. Cambiar controles invalida también respuestas de
vista previa pendientes. No cambian los motores de cuenta manual o de backtest.

630 pruebas seleccionadas aprobadas en 56,20 s, incluidas 44 del nuevo comparador;
temporal GUID exclusivo y caché desactivada. No se ejecuta la colección completa.
En navegador se carga un CSV artificial derivado de las tres ejecuciones guardadas
del tramo 2025: precio +0,0001, otra ejecución +60 segundos y una comisión vacía.
Se alinean tres parejas, se detectan dos filas con diferencias y el coste desconocido.
Se revisa y archiva el resultado sin nuevos backtests, peticiones al modelo o asientos.

El usuario elige JForex/Dukascopy. Su documentación del SDK describe informes HTML;
el lector CSV no se presenta como adaptador de ese formato. Queda pendiente obtener
un original con su configuración para implementar y probar la conversión y realizar
el contraste externo real. Evidencias en `reports/phase6-execution-comparison-2026-10-22/`.
Este incremento permanece local, sin commit/push; PROJECT_STATUS no cambia y FASE 6
sigue abierta.

### 22/10/2026 — Preparación de JForex y comprobación de requisitos

Se revisan las fuentes oficiales de instalación, probador histórico, unidades de
órdenes y modo TEST. No se encuentra JForex en registro o directorios habituales
del entorno normal del usuario; se evita concluir que no existe una instalación
portable. Java y Maven están disponibles. Se descarga el instalador oficial Windows
4.23 en `.local/jforex/downloads/`, sin ejecutarlo. Authenticode devuelve Valid y
firmante SWFX SA; se guardan URL HTTPS, tamaño y SHA-256.

Se identifica un requisito nuevo: la referencia de 1 EUR no respeta el mínimo API
de 1.000 unidades EUR/USD. Se archiva su configuración intacta y se propone un
caso nuevo con 1.000 EUR y 1.000.000 USD hipotéticos, sin calcularlo. No se convierte
el caso antiguo ni se afirma equivalencia de velas, costes o motores. La guía
JFOREX_SETUP separa instalación/acceso de la preparación de estrategia, comprobación
de datos y obtención del informe HTML nativo. La estrategia Java aún no se genera
ni se declara compilada o probada.

Este paso prepara documentos y archivos de referencia; no cambia código de la
aplicación y no repite pruebas del motor. Se verifican 14 manifiestos de 13 informes
anteriores (incluido un manifiesto de archivo interno) y las fuentes conservadas,
sin nuevos backtests, llamadas al modelo,
cuentas o asientos. Evidencias en `reports/phase6-jforex-preparation-2026-10-22/`.
Sin instalación, formularios, credenciales o aceptación de condiciones. Los avances
siguen locales, sin commit/push, y PROJECT_STATUS permanece intacto.

### 22/10/2026 — Estrategia de JForex exclusiva del probador histórico

El usuario confirma JForex y acceso demo. Se localizan JForex 4.23 y su API demo
4.9.8, sin consultar credenciales ni iniciar un cliente. Se implementa
`integrations/jforex/TiresiasSmaUtcTester.java`, compilada con JDK 25 y destino
Java 21 contra el JAR instalado. La compilación dentro de JForex sigue pendiente.

El código rechaza motores DEMO/LIVE antes de archivos, suscripciones u órdenes y
repite la guarda en callbacks y envíos. Exige un tester USD nuevo con capital
indicado y apalancamiento 1:1. Congela parámetros, agrupa ticks por sesión UTC,
calcula cruces SMA causales con Decimal de 28 dígitos y solicita compra/cierre
largo al primer tick de la siguiente sesión observada. No sustituye fills nativos
por aperturas previstas ni cierra posiciones desde onStop. Las diferencias entre
ticks/interpolación y nuestros H1 siguen pendientes de comprobación.

Exporta sesiones, H1 BID/ASK, peticiones, mensajes, partes de ejecuciones y costes
agregados. Los costes por fill e identificadores ausentes no se inventan. Un cierre
nativo anterior no recibe una señal posterior; se explicita que la señal procede
de nuestra petición y no prueba causalidad nativa. Fallos, final no observado,
rechazos o datos incompatibles quedan visibles y no provocan un reenvío automático.

Se fija protocolo antes de una sola referencia Python nueva: capital hipotético
1.000.000 USD, cantidad 1.000 EUR y comisión supuesta 0,001. Resultado
`4e59e20a16b74fc7bd16ea7dad80d02d`, 307 sesiones y tres ejecuciones. Se conserva
intacto el caso anterior de 1 EUR y no se cambia el presupuesto del chat.

660 pruebas seleccionadas aprobadas, 30 nuevas de JForex, sin omisiones y con
temporal GUID/caché desactivada. Los dobles offline implementan las interfaces del
JAR real; no ejecutan el tester. También se reproduce la secuencia de aperturas y
cierres de la referencia preservada para contrastar SMA y peticiones. Sus fills y
comisiones son artificiales: no constituyen validación externa ni rendimiento JForex.

Se entrega fuente Java, guía y mapa CSV. Falta compilar/ejecutar dentro de JForex,
recibir HTML/exportaciones originales y conciliar datos, ejecuciones y costes.
No se implementa a ciegas el lector HTML. Evidencias en
`reports/phase6-jforex-strategy-2026-10-22/`. Núcleo Python, cuentas, modelos y
evidencias anteriores permanecen intactos. Avance local, sin commit/push y sin
actualizar PROJECT_STATUS; FASE 6 permanece abierta.

Después se intenta consultar la ventana abierta de JForex con Windows Computer Use.
La solicitud de acceso a la aplicación caduca antes de concederse; no se obtiene
captura ni se envían acciones a su interfaz. Se deja registrada la limitación y
se pregunta si reintentar el acceso o realizar la prueba manualmente con el paquete.
No es un fallo de compilación nativa observado: esa comprobación sigue pendiente.

### 23/10/2026 — Primer ensayo nativo de JForex y calendario de mercado

El usuario compila la estrategia en el editor de JForex y facilita tres informes
originales. Los dos primeros fallan al iniciar por configuración incompleta (método
vacío, capital inicial insuficiente) y moneda EUR. El tercero confirma USD, capital
1.000.000 y el método horario previsto. Procesa 23.137 ticks y 5.784 barras H1,
pero solicita una compra el sábado 30/08/2025 a las 00:07:30 UTC. El tester responde
`System offline` y `ORDER_SUBMIT_REJECTED`; no confirma operaciones y no completa
la ventana. Las interpolaciones incluían días y horas de mercado cerrado.

Se corrige el adaptador Java usando `IDataService.isOfflineTime(time, instrument)`
de la API instalada. Los ticks cerrados no entran en sesiones/SMA ni provocan
peticiones. El viernes se completa al primer tick admitido tras la reapertura,
manteniendo la fecha de la señal; no se reenvían órdenes rechazadas. El calendario
ausente/fallido detiene la prueba. El protocolo v2 añade intervalos/contador de ticks
omitidos y contenido/motivos de mensajes nativos; conserva los H1 sin filtrar.

35 pruebas locales aprobadas (5 adicionales) contra la API real con dobles offline,
sin omisiones. Comprueban el hueco de cierre, precio constante durante mercado
abierto, señal/ejecución tras reapertura, final de ventana en cierre, indisponibilidad
de calendario y conservación del motivo del rechazo. No representan un nuevo
ensayo nativo. Los originales privados se archivan con SHA-256 bajo `.local/` y se
conservan las evidencias anteriores. Falta reimportar y compilar el fuente v2 en
JCloud y repetir el ensayo. Sin cambios de motores Python, backtests/modelos nuevos,
commit/push o PROJECT_STATUS; FASE 6 sigue abierta.

### 23/10/2026 — Ensayo JForex v2 completo y primer contraste nativo

El usuario reimporta y ejecuta la revisión corregida. El HTML
`TiresiasSmaUtcTester_23102026_120254.html` y sus exportaciones completan la ventana
sin fallos. Se procesan 24.488 ticks, se omiten 9.880 de períodos cerrados y se
confirman tres ejecuciones de 1.000 EUR (compra, venta, compra), dejando 1.000 EUR
abiertos. El HTML informa de patrimonio final 999.988,68 USD: -11,32 USD respecto
al millón inicial. Esta cifra corresponde al corte del informe nativo.

Una revisión independiente reconstruye 6.122 H1 a partir de 8.592 barras y los
52 intervalos de calendario. Las aperturas coinciden con la fuente de referencia;
se detectan cinco diferencias OHLC en tres velas. Los agregados de las 307 sesiones
mantienen exactamente la huella canónica de Python y coinciden con daily.csv, SMA
y señales. No se sustituyen datos ni se vuelve a calcular un backtest Python.

Las funciones puras del comparador emparejan las tres ejecuciones con ventana H1
de 3.600 segundos y tolerancia temporal cero: mismo precio, cantidad y señal, pero
fecha nativa 450 segundos posterior. Las comisiones por fill quedan desconocidas;
estado `differences`, sin guardar registros en la app ni modificar cuentas/modelos.

El HTML muestra 0,06 USD de comisiones y los agregados de órdenes suman 0,05 USD.
El informe incorpora dos swaps posteriores al corte de estrategia del 25/12 y su
valoración no coincide en fecha con la de Python. La columna v2 denominada
remaining_amount_millions refleja IOrder.getAmount, que en la orden cerrada sigue
mostrando 0,001: la posición se revisa mediante fills netos y estado, sin tratar ese
valor como cantidad abierta. Se conservan explícitas estas limitaciones y no se
declara contabilidad final reconciliada ni equivalencia completa.

Originales archivados y verificados byte a byte bajo `.local/`; revisión pública
sin identificadores de cuenta en `reports/phase6-jforex-native-review-2026-10-23/`.
Se verifican 17 manifiestos anteriores y fuentes de motores, referencia y
PROJECT_STATUS intactos. No cambia el adaptador: se conservan sus 35 pruebas ya
aprobadas y no se repiten. Siguiente paso: conciliar costes/valoración al mismo
corte e incorporar la evidencia al flujo de contraste. Sin commit/push ni cierre
de fase.

### 23/10/2026 — Conciliación al corte e integración del paquete nativo

Se implementa `jforex_reconciliation.py`: lector acotado del ZIP de HTML y archivos
de la estrategia TEST H1/4-OHLC BID, perfiles v2/v3, con límites, nombres exactos,
sin extracción de rutas ni ejecución de HTML/scripts. Verifica coherencia de
capital, moneda, SMA, fechas, posiciones/horas y cantidades de swaps contra fills;
reconstruye sesiones independientemente de la huella de referencia. La app añade
vista previa, aprobación ligada a su huella, archivo idempotente con referencia
congelada y consulta/catalogación sin recalcular estrategias.

Se conserva el paquete real v2 como conciliación
`e09d030c7635c6542cd53b030874afb51ad162b8305853a2d13b55e42ff96681`.
Al 25/12/2025 00:00 UTC: bruto -7,79 USD; swaps derivados previos -3,01376 USD y
posteriores -0,12354 USD. HTML/eventos publican comisión 0,06 USD y las órdenes
suman 0,05 USD. Las reconstrucciones resultan -10,86376 y -10,85376 USD, frente a
-11,29553 USD de Python con sus costes supuestos. Se identifican como escenarios
diagnósticos, no observaciones nativas ni intervalo certificado. Quedan parcial,
sin reparto de comisión por fill ni equivalencia completa.

La estrategia v3 captura cuenta/órdenes al primer tick desde el corte y al final.
Conserva fecha real, objetivo, cotización, equity/base equity informativos,
balance EOD anterior, precios ajustados, P/L, comisión agregada y exposición por
historial. No cierra posiciones ni crea operaciones para obtener las capturas.
Renombra el importe bruto API como native_amount_millions y expone aparte la
cantidad abierta de entradas menos cierres. Una captura posterior no se retrodata;
el posible retraso de IAccount queda explícito. Su ejecución nativa está pendiente.

248 pruebas seleccionadas aprobadas, sin omisiones: 42 del lector/conciliación,
37 de Java contra la API instalada y los componentes de comparador, servicio,
simulador e interfaz afectados. Sintaxis JavaScript comprobada. Se verifica la
ficha real en el navegador y se conserva captura visual. El guardado del análisis
mantiene intactas once huellas de almacenes existentes, incluidos cuentas y chat.
Sin backtests Python nuevos, solicitudes al modelo, operaciones reales,
commit/push ni cambio de PROJECT_STATUS. FASE 6 continúa abierta.

### 23/10/2026 — Capturas nativas v3 y valoración por instante real

Se recibe `TiresiasSmaUtcTester_23102026_125636.html`, sin errores, junto con sus
exportaciones v3. Se archivan y verifican trece archivos originales/revisados bajo
`.local/jforex/prueba-historica-01/revision-v3-ec1a8c6c1dce/`, sin sobreescribir
los ensayos previos. Las 307 sesiones/señales y los tres fills coinciden con v2;
queda exposición larga de 1.000 EUR. No se vuelve a ejecutar un backtest Python.

La API publica patrimonio 999.989,14 USD al 25/12/2025 00:07:30 UTC, 450 s después
del corte objetivo, y 999.988,68 USD al 26/12 23:52:30 UTC. Esta última lectura
coincide con el HTML final (-11,32 USD). La lectura inicial no se retrodata al corte
ni certifica sincronización con la cotización; el balance EOD no se usa como caja.

El adaptador añade reconstrucciones por captura con su BID, posición de fills,
swaps y eventos de comisión hasta la fecha real, frente al agregado de órdenes
de esa misma captura como escenario independiente. Guarda la diferencia respecto
a la API sin asignarle una causa. No descuenta swaps del P/L ajustado de órdenes.
Al primer tick quedan diferencias +0,06376/+0,05376 USD; al final +0,0073/-0,0027.
Los totales publicados 0,06/0,05 USD y el coste por fill desconocido siguen visibles.
La ficha presenta valores/fechas, retraso y tablas de cada observación.

Conciliación guardada con referencia congelada:
`3594870d86b9d25e902b5b22ccf9774fdd1b3eee3e5f9fec317b1db8c6d15d8a`.
Guardado ligado a la vista previa, verificado por GET e idempotencia; dieciocho
huellas de almacenes/registro v2/PROJECT_STATUS intactas y presupuesto global
sin cambios (4 solicitudes de modelo, 1 experimento). 117 pruebas seleccionadas
aprobadas, incluidas 46 de conciliación; sintaxis JavaScript y ficha en navegador
verificadas. No cambian la estrategia Java ni los motores Python. Las 248 pruebas
del incremento anterior permanecen como evidencia histórica, sin atribuirlas a
otra ejecución. Evidencia nueva en
`reports/phase6-jforex-cutoff-validation-2026-10-23/`.

Siguiente trabajo: diferencias temporales de ejecución y alcance de costes antes
de ampliar el contraste. No se pide repetir el mismo ensayo para capturas que ya
se conservan. FASE 6 sigue abierta, sin commit/push ni cambio de PROJECT_STATUS.

### 23/10/2026 — Preparación del commit y push autorizados

El usuario solicita publicar los avances pendientes. Se comprueba que el remoto
main conserva el commit base `0bd90113c5ea47731da52a57d26d9b5f6dfeafdc`.
La entrega reúne valoración manual sin operación, comparación de ejecuciones,
estrategia exclusiva TEST y conciliación de JForex con capturas nativas v3.
Se corrige en README la referencia obsoleta a la ejecución v3 aún pendiente.

La revisión verifica veinte manifiestos de evidencias y las fuentes vigentes
comprobadas en los incrementos anteriores. Se conservan sus bytes y resultados,
incluidos los indicadores de publicación pendientes que describen aquel momento;
no se reescriben retrospectivamente. Las 117 pruebas seleccionadas del último
incremento permanecen acreditadas; no se repite la colección completa. Sintaxis
JavaScript comprobada. Los originales nativos privados y almacenes de `.local/`
permanecen fuera de Git. Se comprobarán también los bytes protegidos del índice
antes de crear el commit.

La publicación no cierra FASE 6 ni modifica PROJECT_STATUS. El siguiente incremento
debe explicar y modelar expresamente el desfase temporal Python/JForex y delimitar
los costes comparables antes de ampliar la prueba a otros períodos. No se solicita
otra ejecución idéntica para capturas ya recibidas. La confirmación del commit y
del push se comunica después de comprobar la rama remota.
