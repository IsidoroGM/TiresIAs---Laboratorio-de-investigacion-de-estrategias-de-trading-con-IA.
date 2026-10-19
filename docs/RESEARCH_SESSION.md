# Sesiones de investigación con presupuesto global

`trading_ai.research_session` conecta las herramientas existentes sin cambiar
el motor, los contratos de reglas o las restricciones por origen. El presupuesto
es global **dentro de una sesión**, no entre todas las sesiones del proyecto.

## Límites fijados antes de consultar

| Recurso | Máximo por sesión |
|---|---:|
| Ideas iniciales | 1 |
| Reformulaciones | 1 |
| Consultas de generación | 5 |
| Simulaciones | 2: base y candidata |
| Tokens de salida por consulta | 384 |
| Tokens de contexto por consulta | 4096 |
| Reintentos automáticos | 0 |

El camino largo usa idea, traducción, reformulación, nueva traducción y lectura
del resultado: cinco consultas. Sin reformulación usa como máximo tres. Una
conclusión inconclusa de Python evita la última consulta. Una traducción bloqueada
detiene el ciclo; el modelo no recibe intentos extra para conseguir una aceptada.

Con la configuración predeterminada se reservan como máximo 1920 tokens de salida
en total. La reserva no equivale al consumo medido. Se agregan por separado los
tokens informados y el coste de API; si falta información, se conserva desconocida.
Las consultas de generación se cuentan aparte de las comprobaciones de metadatos
del proveedor local.

La sesión solo admite Ollama local, con los límites anteriores. OpenAI permanece
reservado. La CLI no lee credenciales, inicia servicios, instala dependencias ni
descarga modelos. La API local no cobra por consulta, pero usa recursos del equipo.

## Crear y proponer

```powershell
.\.venv\Scripts\python.exe -m trading_ai.research_session create --frozen-run <registro-previo>
.\.venv\Scripts\python.exe -m trading_ai.research_session propose --session <sesion>
```

Crear no contacta al proveedor. Guarda `session.json`, su sello y un evento de
preparación con fuente, pregunta, configuración, presupuesto y hashes del código.
El protocolo `bounded_research_session_v2` también guarda `memory.json` y fija
su hash en el manifiesto. La memoria se captura al crear, no cambia entre etapas.
Admite `--config`, `--question` y `--output-dir` solo en la creación. Después se
usan los valores sellados, sin opciones para ampliar el presupuesto.

`propose` pide una idea y su traducción. Si requiere aclaración, solicita como
máximo una reformulación y otra traducción, conservando el linaje. No envía al
modelo la evaluación exterior. Las comprobaciones de datos y código se repiten
entre etapas. No se ejecutan simulaciones durante esta acción.

Antes de traducir se compara la idea con la memoria. Si repite las reglas,
parámetros y datos de una idea conocida, termina en `duplicate_idea`: una sola
consulta, sin traducción ni reformulación. Después de reformular se aplica el
mismo filtro frente a la memoria y a la idea inicial. Cambiar solo el título o
la hipótesis tampoco permite gastar otra traducción.

Se detiene en `awaiting_review` si hay reglas propuestas o en el estado de bloqueo
correspondiente: `needs_data`, `unsupported` o `needs_clarification`. El intento
imprime su carpeta; `proposal.json` contiene `latest_translation`, el resto de
archivos vinculados, los hashes y el consumo. Que el JSON compile no demuestra
equivalencia con el texto, novedad ni rentabilidad.

La [entrada estructurada nueva](STRUCTURED_IDEAS.md) evita la traducción de
texto a reglas y dispone de su [flujo propio de revisión, plan y sesión](STRUCTURED_WORKFLOW.md).
Este controlador v2 conserva su flujo y presupuesto; no se transforman sus
registros para aparentar respuestas o aprobaciones del protocolo anterior.

## Memoria de ideas y dudas anteriores

`trading_ai.idea_memory` incorpora propuestas y traducciones verificadas del
mismo registro de desarrollo. Busca las bandejas normales de `.local/discovery`,
`.local/idea-revisions`, `.local/formalization` y las rutas compactas de las
sesiones. Las salidas guardadas en otras ubicaciones no se incorporan por sí solas.

La memoria conserva identidades, propuesta, estado, motivos de traducción y
hashes de sus fuentes. Los motivos siguen siendo texto del modelo sin verificar,
no órdenes ni conclusiones de rendimiento. No se incorpora la evaluación
exterior ni se seleccionan ideas por resultados. La procedencia de desarrollo
se comprueba con los verificadores existentes.

Hay un máximo de 128 fuentes; superarlo detiene la preparación, sin borrar o
descartar silenciosamente el historial. Todas las huellas se usan para detectar
duplicados y como máximo cuatro ideas distintas se envían al modelo, con hasta
dos motivos cada una, para limitar el contexto. La solicitud exacta queda
registrada antes de consultar. También precisa datos disponibles, ejecución
posterior, ventanas y ausencia de cierre automático al final del periodo.

La huella ignora título, hipótesis, mayúsculas, espacios, orden de parámetros y
diferencias numéricas como `20` y `20.0`. Conserva condiciones, valores y tipos de
datos requeridos. **No demuestra equivalencia matemática**: una paráfrasis puede
escapar al filtro y una idea distinta puede seguir siendo ambigua o no mejorar.
La traducción y la revisión técnica continúan siendo necesarias.

Alterar la memoria o sus fuentes bloquea el uso de la sesión. Las ideas añadidas
después de crearla se incorporarán al preparar otra sesión, sin cambiar el
contexto ya fijado. Una sesión de protocolo anterior se conserva como historial;
se crea una nueva con memoria, sin reiniciar sus acciones ni borrar reservas.

## Revisar y completar

La [revisión técnica](RULE_PLANNING.md) sigue siendo explícita y separada del
modelo investigador. Debe identificar la traducción más reciente y confirmar
entrada, salida, parámetros, datos y ausencia de ambigüedad. No es una prueba
automática del significado ni una autenticación de quien figura como revisor.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.research_session finish --session <sesion> --assessment <revision.json>
```

El archivo de revisión se valida antes de consumir esta acción. Un formato o
hash incorrecto puede corregirse sin regenerar la propuesta. Una revisión válida
con decisión `rejected` o `needs_clarification` se registra y termina sin simular.
No se sustituye la propuesta ni se convierte un rechazo en permiso de ejecución.

Una revisión aceptada permite registrar el plan, reservar las dos simulaciones,
invocar al [ejecutor](RULE_EXECUTION.md), verificar sus resultados y solicitar
una [lectura contrastada](AGENT_FEEDBACK.md). La conclusión debe coincidir con
Python. No hay selección posterior de otro candidato ni cambio de criterio,
capital, costes o tamaño para obtener un resultado favorable.

El estado `completed` significa que el procedimiento terminó; el criterio puede
no cumplirse o ser inconcluso. No demuestra una estrategia mejor. Si falla la
lectura del modelo después de calcular, se conservan los resultados del motor
y el presupuesto reservado, y la acción se registra como fallida.

## Persistencia, concurrencia y fallos

Cada consulta tiene una reserva exclusiva en `budget/model-N.json` antes de
enviarse. Se guarda consumo conocido incluso si la respuesta es inválida o el
proveedor falla. Una reserva sin respuesta sigue consumida y su uso es desconocido.
Las simulaciones se reservan en `budget/backtests.json` antes de invocar el
ejecutor: una reserva fallida no se devuelve automáticamente.

Cada acción tiene un único intento registrado en `actions/`, con eventos y
resultados en `attempts/`. Los artefactos de herramientas usan rutas compactas
en `a/` para evitar anidamientos excesivos en Windows. Las letras de esas rutas
no definen permisos; cada origen queda identificado en los registros.

Un bloqueo exclusivo `active.lock` impide ejecutar dos acciones simultáneas.
Se retira al salir normalmente, incluidos errores gestionados. Una terminación
abrupta puede dejarlo puesto: no se recupera ni se borra automáticamente.
Los intentos reclamados tampoco se repiten tras un error. Los registros de
duplicados del ejecutor y del feedback siguen vigentes entre sesiones.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.research_session status --session <sesion>
```

La consulta de estado es de solo lectura y no contacta al modelo. Verifica el
manifiesto y los archivos registrados de las etapas y muestra reservas y consumo.
La verificación específica del ejecutor sigue disponible para consultar sus
resultados. Cambiar fuentes o código puede invalidar una sesión pendiente.

La ubicación forma parte del manifiesto: copiar o mover la sesión no crea un
presupuesto nuevo válido. Los archivos y hashes son controles locales, no firmas
contra manipulación conjunta. Borrarlos o alterarlos deliberadamente queda fuera
de esa garantía. Las llamadas manuales a herramientas separadas no se imputan a
esta sesión; tampoco hay un límite global entre sesiones distintas.

## Estado de desarrollo

**761 pruebas aprobadas**, incluidas 30 nuevas. El
[registro de comprobación](../reports/phase4-research-session-2026-10-19.md)
conserva un ciclo artificial de cinco consultas simuladas y una sesión real
preparada con cero consultas y cero simulaciones. No se inició una nueva búsqueda
real ni se ejecutó el borrador que seguía ambiguo.

Posteriormente, el [primer inicio operativo](../reports/phase4-session-proposal-2026-10-19.md)
repitió la idea anterior y se detuvo por el límite compartido de reformulación.
Quedaron registradas dos consultas, 0 USD de API y cero simulaciones, sin
reintentar o ampliar el presupuesto. La sesión preparada de la evidencia anterior
es una instantánea histórica, no su estado operativo actual.

La [corrección de memoria y duplicados](../reports/phase4-idea-memory-2026-10-19.md)
cuenta con **782 pruebas aprobadas**, incluidas 21 nuevas. Su comprobación local
recibió dos ideas anteriores y cinco fuentes verificadas. Terminó correctamente
en `needs_clarification` tras cuatro consultas, 0 USD de API y cero simulaciones:
el modelo aún no concretó sus reglas. La memoria reduce repeticiones y gasto
innecesario, pero no garantiza precisión, novedad o una propuesta aceptable.

El alcance es `known_development_history_only`. Continúan pendientes las
comprobaciones de robustez para propuestas nuevas y la validación prospectiva
con datos no consultados. TradingView sigue sin conexión y no hay operaciones
reales. FASE 4 permanece abierta y `PROJECT_STATUS.md` no se modifica.
