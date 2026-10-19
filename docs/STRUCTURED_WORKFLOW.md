# Sesiones con propuestas estructuradas

Este flujo conecta la propuesta explícita con revisión técnica, plan previo y
dos simulaciones del motor. Conserva los protocolos anteriores y sus archivos.
No hay operaciones reales, llamadas de pago o cambios del simulador.

## Pasos y presupuesto

1. `structured_ideas propose` genera una propuesta con una consulta local.
2. `structured_session create` incorpora ese origen verificado, sin consultarlo
   de nuevo. Atribuye sus tokens y coste, y los separa del consumo nuevo: cero.
3. `structured_session finish` registra una revisión técnica explícita. Si se
   acepta, fija el plan y reserva exactamente dos simulaciones: base y candidata.
   La conclusión se calcula en Python, sin otra llamada al modelo.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.structured_session create --proposal-run <propuesta> --frozen-run <registro-previo>
.\.venv\Scripts\python.exe -m trading_ai.structured_session finish --session <sesion> --assessment <revision.json>
.\.venv\Scripts\python.exe -m trading_ai.structured_session status --session <sesion>
```

Una propuesta solo puede originar una sesión registrada. Copiar carpetas o
elegir otra salida no renueva su presupuesto. Los intentos fallidos no se borran
ni reintentan automáticamente. Un bloqueo de proceso interrumpido requiere
revisión; no se recupera por suposición.

La generación original queda fuera temporalmente de esta sesión, pero su
consumo aparece como `source_*`. `new_model_requests` y `new_api_cost_usd` son
cero. No se presenta ese consumo heredado como una llamada nueva ni se omite.

## Revisión sin aprobación del propio investigador

El archivo de revisión identifica los hashes de propuesta y reglas, revisor,
motivo, decisión y seis comprobaciones booleanas:

- Entrada y salida coinciden con la hipótesis.
- Ventanas y retardos se han entendido explícitamente.
- Hay datos suficientes y no quedan ambigüedades.

Aceptar exige todas las comprobaciones. Las decisiones `rejected` y
`needs_clarification` cierran la sesión sin plan ni simulaciones. Un archivo
mal formado puede corregirse antes de consumir `finish`; una decisión válida
ya registrada no se sustituye para forzar otra ejecución.

La revisión es una declaración técnica, no una prueba automática de equivalencia
o identidad del revisor. La compilación no concede aprobación. Una revisión
separada puede realizarla Codex en el desarrollo autorizado; el modelo local
investigador no aprueba su propia propuesta.

## Plan y ejecución

`structured_planning` fija la candidata exacta, base, criterio, fechas, datos,
capital, tamaño y costes del registro de desarrollo. No hay argumentos para
cambiarlos al ejecutar. La copia de datos solo contiene desarrollo.

`structured_execution` reutiliza cálculo, métricas e interpretación del criterio
del ejecutor anterior. Usa su mismo registro compartido de identidad de
cálculos; cambiar de protocolo o carpeta no libera otro intento de la misma
identidad. El nombre técnico y el criterio no alteran esa identidad.

Las cuentas son independientes, con ejecución posterior y posiciones abiertas
sin cierre final forzado. Se conservan contabilidad, resúmenes, hashes de señales,
reservas y errores. Verificar no recalcula ni consulta IA. Un resultado puede ser
negativo o inconcluso; `completed` significa que terminó el procedimiento.

La conclusión relativa puede cumplir el criterio con ambas rentabilidades
negativas. Cumplirlo no implica ganar dinero ni demostrar superioridad general.
Todo el histórico usado es conocido, sin nueva evaluación exterior.

## Una reformulación acotada

`structured_revision` admite una revisión `needs_clarification` y una consulta
local para generar otra propuesta estructurada, sin modificar la anterior.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.structured_revision revise --run <revision-tecnica> --frozen-run <registro-previo>
.\.venv\Scripts\python.exe -m trading_ai.structured_revision verify --run <reformulacion> --frozen-run <registro-previo>
```

Registra origen, pregunta real, extracto del motivo, respuesta y consumo. El
extracto está limitado y su truncamiento se declara en el contexto. El motivo
no se trata como una orden para cambiar controles o como un hecho financiero.
Una reserva compartida permite un intento por propuesta y desarrollo, aunque
cambien motivo o carpeta. Las propuestas hijas no pueden originar otra
reformulación. El historial se limita a 128 reservas y no se borra para continuar.

Se separan consumo nuevo e heredado; el coste de linaje conserva ambos y no
convierte valores desconocidos en cero. Si falla el hijo, su registro de error
y consumo sigue vinculado. Si repite reglas, conserva `duplicate_rules`. Una
reformulación distinta tampoco se presume equivalente, aceptada o mejor.

Este es un paso explícito separado de la sesión ya cerrada por aclaraciones.
Su propuesta hija exige otra revisión técnica; no reabre la decisión anterior
ni aumenta los límites de aquella sesión. No hay un bucle hasta conseguir éxito.

## Ayudas estáticas para el revisor

`structured_diagnostics diagnose --run <propuesta> --frozen-run <registro>`
conserva propiedades verificables sin señales, simulaciones o modelo. `verify`
comprueba su origen y resultados estáticos sin consultar IA.

Indica longitudes exactas, retardos y primer índice en que las series y cruces
pueden estar disponibles. El calentamiento es global entre entrada y salida.
El índice de ejecución es una cota y requiere una observación siguiente; no
promete una operación. `entry_ruled_out` solo descarta la señal por estructura
o calentamiento, sin afirmar que en los demás casos vaya a producirse.

Las advertencias de texto son indicios para revisar. Un título en el límite o
una frase sin punto no demuestran por sí solos truncamiento o incoherencia.
La herramienta no interpreta la hipótesis ni cambia la decisión técnica.

## Descripción completa de los campos declarados

`structured_brief` redacta entrada y salida a partir de las reglas verificadas:
operador exacto, serie, ventana y retardo. Aclara la ejecución posterior del
motor sin calcular señales o resultados. Es texto mecánico de Python, con
origen explícito; no se atribuye al modelo ni demuestra la hipótesis.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.structured_brief create --run <propuesta> --frozen-run <registro>
.\.venv\Scripts\python.exe -m trading_ai.structured_brief verify --run <descripcion> --frozen-run <registro>
```

El informe conserva título e hipótesis originales como texto literal, aunque
estén incompletos. No completa sus frases, no sustituye la revisión y no libera
intentos consumidos. Conserva hashes de fuentes, código y registro verificable.
Cero consultas de modelo o API; no cambia el estado de la propuesta.

Existe también una [vista previa experimental de borradores compactos](STRUCTURED_DRAFTS.md),
sin título ni hipótesis libres. Solo valida y describe reglas externas; todavía
no se conecta al investigador o a este flujo y no sustituye propuestas pendientes.

FASE 4 sigue abierta. No se actualiza `PROJECT_STATUS.md` en estos desarrollos.
