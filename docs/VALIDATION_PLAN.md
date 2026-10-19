# FASE 4 — Desarrollo y evaluación cronológicos

Inicio: 19 de octubre de 2026. Fase en desarrollo; separación, registro previo
y primera evaluación de una propuesta implementados. Se añade una comprobación
acotada de sensibilidad y selección interna sobre desarrollo; no cierra la fase.

El objetivo es proponer cambios con una parte del histórico y comprobar después
una propuesta fijada con fechas posteriores. No se eligen parámetros mirando el
resultado reservado. La optimización y el recorrido de ventanas se incorporarán
en tareas posteriores, una vez comprobado este procedimiento básico.

## Primera separación

Corte elegido por el usuario: **2020-01-01**, sin buscar una frontera que mejore
los resultados. Desarrollo contiene fechas anteriores; evaluación contiene fechas
iguales o posteriores. Si el corte no es una fecha publicada, evaluación empieza
en la siguiente observación disponible. Ningún bloque puede quedar vacío.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.validation --cutoff 2020-01-01
```

Este comando valida la copia BCE para los cuatro pares y crea una carpeta nueva
en `.local/validation/<identificador>/`, con:

- `development.xml`: referencias originales del bloque de desarrollo.
- `evaluation.xml`: referencias originales del bloque reservado.
- `manifest.json`: fecha de corte, reglas de asignación, cobertura, hashes,
  procedencia y política prevista de simulación.

No se descarga información ni se consulta IA. Tampoco se ejecuta un backtest.
Los archivos se escriben sin sobrescribir preparaciones anteriores; no se
modifica el XML original. Los hashes identifican los bytes exactos de cada
archivo y permiten detectar cambios antes de reutilizarlo. El corte es
obligatorio: no se elige automáticamente ni se ajusta al observar resultados.

## Reglas del primer protocolo

1. Preparar la separación y conservar su manifiesto antes de investigar variantes.
2. Para investigar, suministrar al agente únicamente `development.xml` mediante
   `--data`. El comando de FASE 3 conserva su valor predeterminado de histórico
   completo; no debe utilizarse ese valor para este protocolo. El registro
   posterior comprueba que la investigación usó exactamente el archivo de
   desarrollo vinculado al manifiesto.
3. Guardar la propuesta exacta, el criterio y los controles antes de abrir la
   evaluación. No cambiar la propuesta a partir de sus resultados.
4. Comparar después base y variante fijada dentro de cada bloque con los mismos
   supuestos. Mantener separados los resultados y sus periodos.
5. Registrar también resultados negativos, inconclusos y errores. Cualquier
   investigación adicional deberá indicar si ya se miró el bloque reservado.

El paso 3 se implementa con el registro descrito a continuación. La primera
evaluación y el registro de sus intentos se implementan en el flujo posterior.
La división no concede
permisos de archivos exclusivos al agente ni bloquea que una persona abra
evaluación. Las herramientas del modelo siguen acotadas.

## Registrar la propuesta antes de evaluar

Ejecutar primero una investigación de FASE 3 con `--data` apuntando a
`development.xml`. Conservar la carpeta de investigación que devuelve el
comando, incluso si el resultado no apoya la hipótesis. No buscar una propuesta
que mejore la evaluación reservada. Después registrar la propuesta:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.holdout freeze --split '.local/validation/<id-separacion>' --research-run '.local/research/<id-investigacion>'
.\.venv\Scripts\python.exe -m trading_ai.holdout verify --frozen-run '.local/holdout/<id-registro>'
```

Sustituir los identificadores entre `<...>` por los que muestran los comandos.
`freeze` crea una carpeta nueva en `.local/holdout/`; `verify` comprueba esa
carpeta sin sobrescribirla. Ambos comandos son locales y no consultan IA.

El registro exige una investigación completada correctamente sobre el archivo
de desarrollo de esa separación, con los mismos controles y código actuales.
Recalcula sus resultados con el motor, comprueba el análisis y rechaza una
investigación sobre evaluación o sobre el histórico completo. No selecciona
propuestas por su rentabilidad ni exige que cumplan el criterio.

Se conservan los siguientes archivos:

- `frozen.json`: propuesta exacta, criterio, controles, resultados de desarrollo,
  fecha UTC del registro, política de arranque independiente y hashes del código,
  del manifiesto y de los archivos de investigación.
- `frozen.sha256`: hash de los bytes exactos de `frozen.json`.
- `events.jsonl`: inicio, cierre del registro o motivo del fallo; se sincroniza
  a disco. Cada intento utiliza otra carpeta.

Los archivos de ambas particiones se leen para comprobar sus hashes. Solo se
interpretan las referencias y se recalculan métricas de desarrollo. Ninguno de
estos comandos ejecuta un backtest sobre evaluación. `verify` rechaza cambios
en propuesta, controles, manifiesto, datos, archivos de investigación o código.
La evaluación exige esta verificación y usa los parámetros registrados, sin
aceptar otros parámetros para evaluar.

Los hashes y el registro local permiten detectar cambios ordinarios. No son una
firma digital ni un registro externo inmutable: alguien con acceso completo
puede reescribir archivos y hashes. Tampoco demuestran que nunca se consultó
evaluación fuera de este flujo. Fijar otra propuesta no vuelve inéditos unos
resultados de evaluación que ya se hayan visto. El flujo siguiente registra el
acceso y bloquea repeticiones sobre el mismo archivo reservado.

## Evaluar la propuesta registrada

```powershell
.\.venv\Scripts\python.exe -m trading_ai.evaluation --frozen-run '.local/holdout/<id-registro>'
```

Solo se admiten el registro y una carpeta de salida opcional. No hay opciones
para cambiar par, estrategia, ventanas, costes, tamaño o capital. El comando
verifica propuesta, controles, investigación, datos y código antes del cálculo;
no cambia ni vuelve a registrar la propuesta. El módulo de evaluación es nuevo
y conserva intactos los archivos de código vinculados al registro anterior.

Se comprueban las fechas reales del bloque reservado y se ejecutan base y
variante con los mismos supuestos. Las métricas y la valoración del criterio
proceden de Python, sin consultar IA. Los resultados de desarrollo se conservan
y muestran por separado. Se distinguen criterio cumplido, no cumplido e
inconcluso dentro de cada bloque; no se declara un ganador global.

La salida nueva se guarda en `.local/evaluations/<id-intento>/`:

- `events.jsonl`: inicio, comprobaciones, acceso, cálculo, cierre o error, con
  tiempos, hashes del código y consumo de API cero.
- `evaluation_raw.json`: resultado calculado, conservado incluso si después se
  detecta una discrepancia. Por sí solo no acredita una evaluación completada.
- `comparison.json`: resultados separados, propuesta, controles, valoraciones
  y referencias, tras superar las comprobaciones posteriores al cálculo.
- `report.md`: informe de ambos bloques, sus supuestos y límites.

El evento final `evaluation_completed` identifica un cierre correcto. Un error
queda registrado como `evaluation_failed`; no se generan conclusiones válidas
a partir de un resultado rechazado.

### Marcar el acceso al bloque reservado

Antes de interpretar referencias o calcular métricas de evaluación, la
aplicación crea exclusivamente `.local/evaluation-access/<sha256-xml>.json`,
con la fecha UTC, el registro previo y el intento de evaluación. El directorio
es compartido y no cambia al elegir otra carpeta de resultados o registrar otra
propuesta. Dos intentos simultáneos no pueden adquirir el mismo archivo.

Una marca existente bloquea una segunda evaluación de esos mismos bytes. Un
fallo posterior al acceso conserva la marca y no permite reintentar
automáticamente. El registro de cada intento explica el rechazo; el primer
resultado se conserva. No hay opción `--force`. Si hiciera falta recuperar un
fallo, se acordaría un procedimiento que preserve la evidencia de acceso.

Este primer flujo permite una evaluación por archivo reservado completo,
compartido por los cuatro pares, no una por variante o par. Evaluaciones de más
pares o propuestas requerirán un protocolo previo de conjunto, sin abrir una
búsqueda adaptada a resultados ya consultados. No se han implementado aún.

La marca es local y se basa en los bytes del XML. No impide consultas por otras
herramientas ni detecta todas las representaciones equivalentes de los mismos
datos. Alguien con acceso completo podría borrar registros o alterar archivos.
Es un control del flujo de la aplicación, no una garantía de datos inéditos.

## Contabilidad y calentamiento

Cada bloque y par tiene una cuenta virtual independiente, con el mismo capital
inicial, costes y tamaño acordados. No se trasladan posiciones, capital,
señales pendientes ni valores de indicadores desde desarrollo a evaluación.
Las medias se calculan desde el inicio de cada bloque y no hay operaciones
durante su calentamiento. Una señal al final de desarrollo no se ejecuta en
evaluación. Las posiciones abiertas permanecen valoradas al final de su
bloque, sin cierre forzado, como en el motor actual.

Esta elección facilita comprobar la separación y supone un arranque desde cero
en evaluación. No representa continuar operando una cuenta que ya tuviera una
posición. No se comparará el capital de ambos bloques como si fuera una curva
continua. Si se introduce calentamiento previo en otra tarea, se especificarán
sus reglas y pruebas antes de utilizarlo.

## Robustez interna exclusivamente en desarrollo

Después de consultar la primera evaluación exterior se incorpora este análisis
descriptivo. El flujo lee la propuesta registrada y el bloque de desarrollo;
no abre `evaluation.xml`, los resultados de evaluación exterior ni su registro
de acceso. El registro original y los módulos vinculados a él se conservan.
No se cambia la propuesta ya evaluada ni se vuelve a evaluar en 2020–2026.

Se fija este protocolo antes de sus cálculos:

| Elemento | Regla |
|---|---|
| Selección interna | Desarrollo anterior a 2010-01-01: 1999–2009 |
| Comprobación interna | Desarrollo desde 2010-01-01: 2010–2019 |
| Ventanas de la variante | EMA20/60, EMA19/60, EMA21/60, EMA20/59 y EMA20/61 |
| Costes por ejecución | 0,05 %, 0,10 % y 0,15 % para cada configuración |
| Base | SMA20/60 con el mismo coste que la variante en cada comparación |
| Capital y tamaño | 1000 USD y 10 % del efectivo, costes incluidos |
| Total | 15 escenarios por tramo; 30 comparaciones, cada una con base y variante |

Las ventanas son cambios mecánicos de una observación respecto a EMA20/60,
la propuesta registrada. No son nuevas propuestas de IA. Los costes cambian
en ±0,05 puntos porcentuales respecto al original. Si otra configuración de
partida produjera ventanas o costes inválidos, el plan registraría las omisiones
antes de calcular; no se ajustan silenciosamente al límite.

La selección considera **solo el primer tramo y el coste original de 0,10 %**.
Exige cierres en ambas estrategias y cumplir el criterio registrado frente a
la base: mayor rentabilidad sin aumentar el drawdown. Entre las elegibles ordena
por rentabilidad de la variante descendente, después drawdown ascendente y,
en caso de empate, ventanas rápida/lenta ascendentes e identificador. Cumplir
un criterio relativo puede seguir dando pérdidas; no acredita viabilidad.
Si no hay elegibles, se guarda una selección vacía y no se fuerza un ganador.

Los costes alternativos solo describen sensibilidad, no se selecciona el coste
más favorable. La selección se escribe y sincroniza a disco antes del primer
cálculo de comprobación interna. Después se calculan **todos** los escenarios
en el segundo tramo, incluidos los negativos e inconclusos; no se vuelve a
elegir una variante a partir de sus resultados. Cada escenario y periodo
mantiene cuenta, posiciones y calentamiento independientes.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.robustness prepare --frozen-run '.local/holdout/<id-registro>' --inner-cutoff 2010-01-01
.\.venv\Scripts\python.exe -m trading_ai.robustness run --plan-dir '.local/robustness/<id-plan>'
```

`prepare` crea una carpeta nueva con `plan.json`, `plan.sha256`, `selection.xml`,
`check.xml` y el registro de preparación, sin calcular métricas. El plan incluye
escenarios, omisiones, fechas, hashes, criterio, desempates y controles. El corte
interno es obligatorio y debe dejar datos a ambos lados dentro de desarrollo.

`run` no admite ventanas, costes ni otros parámetros nuevos. Verifica el plan,
sus referencias y código; registra un intento exclusivo y calcula en el orden
fijado. Los intentos se guardan en `attempts/<id>/`, con:

- Un JSON por escenario y periodo, con parámetros, resultados y valoración.
- `selection.json`, creado antes de la comprobación interna.
- `results.json` y `report.md`, con todos los escenarios y sus límites.
- `events.jsonl`, con solicitudes, resultados, selección, cierre o error.

Un fallo detiene el intento, conserva los escenarios ya calculados y no publica
un informe completado. El mismo plan no se repite ni sobrescribe. Preparar otro
plan no convierte en inéditos los datos ni autoriza nuevas consultas a la
evaluación exterior. No se consultan modelos ni se añaden dependencias.

Este procedimiento comprueba sensibilidad local y una separación cronológica
interna. El histórico completo ya se exploró y el análisis se diseñó después
de ver la evaluación exterior: no es confirmación independiente. Ver todos los
resultados del segundo tramo los convierte también en información conocida;
no se deben reutilizar para presentar una nueva elección como inédita.

La [primera ejecución de robustez interna](../reports/phase4-robustness-2026-10-19.md)
calculó las 30 comparaciones previstas (15 en cada tramo).
Ninguna ventana fue elegible al coste original en selección: la selección quedó
vacía y no se sustituyó tras calcular el segundo tramo. La suite contiene
**485 pruebas aprobadas**, incluidas 18 nuevas de este flujo. La ejecución real
utilizó además una comprobación de aperturas de archivos que rechazaba datos,
resultados y marcas de acceso de evaluación exterior.

## Comprobaciones del primer paso

Las pruebas utilizan datos pequeños sin red y verifican conservación de
referencias y conversiones, orden, frontera incluida en evaluación, huecos de
calendario, ausencia de solapamientos y pérdida de fechas, hashes, errores de
entrada y conservación de preparaciones anteriores.

Otra prueba cambia únicamente precios de evaluación y repite una investigación
con un proveedor simulado sobre desarrollo. Los datos y los mensajes enviados
al proveedor son idénticos, salvo el identificador único de ejecución. Esto
comprueba el uso explícito de `development.xml`; no demuestra un bloqueo del
acceso a archivos fuera del flujo de la aplicación.

La primera evaluación sobre el archivo reservado completó el flujo de la
propuesta registrada. Las [evidencias de evaluación](../reports/phase4-evaluation-2026-10-19.md)
conservan resultados, informe, acceso y eventos. La suite contiene **467 pruebas
aprobadas**, incluidas 18 nuevas sobre evaluación, cuentas independientes,
integridad, repeticiones, concurrencia, errores y casos inconclusos.

## Límites

El usuario ha encargado al agente la búsqueda de nuevas ideas de estrategia.
El desarrollo continúa con la [bandeja de ideas y futuras herramientas](AGENT_RESEARCH_PLAN.md),
sin elegir manualmente una estrategia supuestamente mejor. Las ideas nuevas
quedan pendientes de traducirse a reglas calculables; no alteran los resultados
ni los registros de las comprobaciones anteriores.

El histórico completo ya se exploró en las fases anteriores. Dividir esta copia
ahora permite comprobar el procedimiento, pero no convierte el bloque reservado
en evidencia totalmente inédita. El modelo también puede tener conocimiento
previo general del mercado. Una evaluación prospectiva requerirá datos que no
se hayan observado al fijar la propuesta.

Una frontera y resultados favorables no demuestran robustez. Este flujo añade
una selección interna y sensibilidad acotadas, no una búsqueda general.
Siguen pendientes más periodos y walk-forward con un protocolo previo, así como
evaluaciones prospectivas cuando haya datos no consultados. Continúan las limitaciones del BCE y
del simulador educativo. TradingView sigue sin conectar según
[su plan](TRADINGVIEW_PLAN.md), OpenAI sigue desactivado y no hay operaciones
con dinero real.

`PROJECT_STATUS.md` conserva el cierre de FASE 3 y solo se actualizará al cerrar
esta fase con autorización del usuario. Este inicio no autoriza commits ni pushes.
