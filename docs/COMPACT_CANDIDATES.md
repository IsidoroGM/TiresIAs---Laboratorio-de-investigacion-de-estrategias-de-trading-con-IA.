# Candidatas compactas locales

Este flujo pide únicamente dos reglas declarativas: entrada y salida. Python
valida sus campos y genera frases completas a partir de ellos. Estas frases
tienen origen Python; no se completan títulos o hipótesis supuestamente escritos
por el modelo. El objetivo de investigación procede del registro congelado.

La candidata permanece pendiente de revisión técnica, sin señales, backtests,
resultados, aprobación o adopción automática en sesiones. Las propuestas antiguas
y sus revisiones no se reescriben ni se convierten al contrato compacto.

## Vigencia y presupuesto

`structured_freshness` compara la petición preparada con cuatro capturas actuales:
ideas, reglas, reservas de reglas y reservas/revisiones de sesiones. Hace una doble
lectura para detectar cambios; es una comprobación optimista, no una transacción
con los escritores históricos. Se repite al reservar, antes del envío y después
de recibir la respuesta. Un cambio detectado detiene la aceptación y conserva el
consumo que se haya producido.

`structured_generation` reserva exclusivamente **un intento compacto por archivo
de desarrollo y par**, con cero reintentos automáticos y cero backtests. Una
reserva creada no se libera si falla después. Cambiar carpeta, criterio o capital
no concede otro intento. Este contador no reinicia los intentos de propuestas o
reformulaciones anteriores. La reserva por sí misma no envía nada: sus indicadores
`submitted=false` y `transport_enabled=false` describen esa etapa histórica.

Las consultas de estado no reservan ni envían:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.structured_freshness capture --request-run <peticion>
.\.venv\Scripts\python.exe -m trading_ai.structured_generation status --request-run <peticion>
```

## Proveedor local controlado

`CompactOllamaProvider` utiliza el servicio local existente, CPU, hasta 4.096 tokens
de contexto y 384 de salida. Comprueba Ollama **0.40.6** y un digest de modelo antes
y después de inferir; otra versión exige revisar expresamente el adaptador. No
inicia servicios, descarga modelos o cambia el proveedor histórico `ai.py`.

El cuerpo solicita `truncate=false` y `shift=false`. En esa versión, estas opciones
piden rechazar un desbordamiento en lugar de recortar mensajes o desplazar contexto.
Fuentes: [API oficial](https://docs.ollama.com/api/chat),
[tipos v0.40.6](https://github.com/ollama/ollama/blob/v0.40.6/api/types.go),
[rutas v0.40.6](https://github.com/ollama/ollama/blob/v0.40.6/server/routes.go) y
[preparación del contexto](https://github.com/ollama/ollama/blob/v0.40.6/server/prompt.go).

El tamaño máximo de la petición sigue siendo 12.288 bytes. **Bytes no son tokens**:
no se afirma conocer el recuento antes de enviar ni que la petición vaya a caber.
Se conservan errores sin reintentar. La versión y el digest declarados confían en
el servicio local; no constituyen una certificación criptográfica del servidor.

## Generación y evidencia

El controlador `compact_candidate` comprueba el proveedor, reserva, fija un trabajo
con fuentes y código por SHA-256, y crea una marca exclusiva de envío. Registra la
respuesta original y el consumo antes de interpretar el JSON. No repara JSON,
claves repetidas o campos inválidos. Un fallo conserva el intento y sus registros.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.compact_candidate generate --request-run <peticion>
.\.venv\Scripts\python.exe -m trading_ai.compact_candidate verify --run <candidata>
```

El primer comando consume el intento aunque no produzca una candidata aceptable.
No se debe ejecutar para reformular una propuesta pendiente ni continuar un linaje
agotado. El segundo solo verifica archivos y no contacta con el modelo.

Una respuesta válida queda `pending_technical_review`. Las reglas exactas se
reservan en el registro compartido de reglas tipadas. Si ya estaban reservadas,
queda `duplicate_rules` y se conserva el propietario original. No se inventa un
`proposal.json` antiguo con prosa artificial para sortear su contrato; por ello
los lectores antiguos ven consumida la reserva, pero no una propuesta antigua
registrada. La revisión y el plan específicos se describen a continuación.

Se guardan `events.jsonl`, `job.json`, su huella, `candidate.json`, su sello y
`report.md`. El verificador contrasta fuentes, respuesta, reglas, consumo, marcas
de reserva/envío, código, ubicación y descripción. El registro de uso separa
inferencias de consultas de metadatos. Los tokens ausentes permanecen desconocidos;
el coste de esta API local es cero, con consumo de tiempo y recursos del equipo.

OpenAI permanece reservado y desactivado. Este flujo solo usa desarrollo ya
conocido; no abre evaluación exterior ni acredita una mejora de estrategia.
FASE 4 sigue abierta. No implementa TradingView o ejecución con bróker.

## Revisión y plan independientes

`compact_review` exige una declaración ligada al SHA-256 de la candidata y de sus
reglas, con revisor, motivo, decisión y seis comprobaciones booleanas: reglas,
ventanas/retardos, suficiencia de referencias, ejecución posterior, objetivo de
desarrollo y ausencia de ambigüedades pendientes. Aceptar exige las seis; un
duplicado no se puede aprobar. El motivo se conserva como declaración no
verificada del revisor. No se considera una hipótesis escrita por el modelo ni
una prueba de novedad o beneficio.

La revisión tiene su propia reserva única por reglas y referencia. Una decisión
cerrada o un fallo posterior a reservar no se reabre cambiando carpeta. Un error
de validación anterior a la reserva no consume la revisión. La candidata original
permanece intacta y su estado histórico sigue pendiente.

El archivo de declaración tiene esta estructura; las dos huellas deben tomarse
de la candidata verificada. Las marcas se rellenan tras revisar las reglas,
sin sustituirlas por la confianza expresada por un modelo:

```json
{
  "schema_version": 1,
  "candidate_sha256": "SHA-256 de candidate.json",
  "spec_sha256": "spec_sha256 de la candidata",
  "reviewer": "Identificación del revisor",
  "decision": "needs_clarification",
  "rationale": "Duda concreta pendiente de resolver.",
  "checks": {
    "rules_understood": false,
    "windows_and_lags_understood": false,
    "reference_data_sufficient": false,
    "next_observation_execution_understood": false,
    "development_objective_understood": false,
    "no_unresolved_ambiguity": false
  }
}
```

```powershell
.\.venv\Scripts\python.exe -m trading_ai.compact_review review --candidate-run <candidata> --assessment <revision.json>
.\.venv\Scripts\python.exe -m trading_ai.compact_review verify --run <revision>
.\.venv\Scripts\python.exe -m trading_ai.compact_plan prepare --review-run <revision-aceptada>
.\.venv\Scripts\python.exe -m trading_ai.compact_plan verify --run <plan>
```

`compact_plan` copia las reglas exactas y los datos de desarrollo. Toma el criterio,
base, capital, costes, tamaño y política de ejecución del registro congelado;
no recibe ajustes propuestos por la IA o por la revisión. Registra como máximo una
simulación de base y una de candidata para un futuro ejecutor, con cero variaciones
y reintentos. Preparar el plan no reserva o ejecuta esas simulaciones.

La identidad del cálculo es compartida con los ejecutores anteriores: cambiar
protocolo, nombre técnico o criterio no libera un cálculo consumido. Se rechaza un
plan nuevo si ya existe esa reserva. El plan histórico continúa verificable si
posteriormente se reserva el cálculo. No se crea una traducción ficticia al
protocolo anterior para usar su ejecutor.

Consumo nuevo de revisar o preparar: cero consultas de modelo, tokens, backtests y
coste de API. El consumo de la candidata se conserva por separado como heredado.
Las memorias antiguas aún no proyectan estas revisiones compactas en peticiones
nuevas; no deben presentarse como historial completo de este contrato.

## Ejecución explícita con el mismo motor

```powershell
.\.venv\Scripts\python.exe -m trading_ai.compact_execution execute --plan-run <plan>
.\.venv\Scripts\python.exe -m trading_ai.compact_execution verify --run <ejecucion>
```

`compact_execution` exige un plan compacto verificable y su revisión aceptada.
Reserva la identidad compartida antes de calcular y llama al motor existente:
una cuenta base y una candidata, con los mismos datos y controles, sin ajustes
de parámetros. Cambiar de carpeta o ejecutar simultáneamente no concede otro
intento. Un fallo conserva la reserva, los contadores y los resultados parciales.

Guarda señales por huella, contabilidad completa, resúmenes e informe. La
comparación usa el criterio calculado por Python; cero cierres o métricas iguales
pueden dejarla inconclusa. No utiliza un juicio del modelo para decidir si mejora.
La lectura verificada comprueba archivos y conclusiones sin recalcular.

Generar, revisar y preparar continúan sin ejecutar estas simulaciones. La llamada
al ejecutor es una acción separada; una candidata pendiente o duplicada no puede
saltarse revisión y plan. El plan registra `execution_requires_explicit_tool=true`.
Los ejemplos artificiales de las pruebas no acreditan una estrategia útil.

## Memoria compacta de solo lectura

```powershell
.\.venv\Scripts\python.exe -m trading_ai.compact_history capture --request-run <peticion>
.\.venv\Scripts\python.exe -m trading_ai.compact_history verify --run <memoria>
```

Captura las reservas compactas de los mismos datos y par, incluidos intentos
interrumpidos, fallidos y duplicados. Los consumos de origen se conservan aparte;
si no se pueden comprobar, quedan desconocidos. La memoria no consulta modelos,
libera reservas, inventa reglas o aprueba candidatas. Incluye las revisiones
compactas como declaraciones no verificadas del revisor. No lee resultados de
ejecuciones compactas ni proyecta métricas financieras. La comprobación de fuentes
sigue verificando los registros históricos de desarrollo y sus controles.

La verificación exige que los estados y la pertenencia sigan coincidiendo con la
captura: si aparece un intento o avanza una revisión, exige renovar la memoria.
La doble lectura detecta cambios durante la preparación; no es una transacción
con todos los escritores. Archivar el JSON conserva lo observado, sin presentarlo
como estado actual indefinidamente. Capturar esta memoria no autoriza otra generación.

## Petición futura con historial compacto

```powershell
.\.venv\Scripts\python.exe -m trading_ai.compact_request prepare --history-run <memoria> --base-request-run <peticion-base>
.\.venv\Scripts\python.exe -m trading_ai.compact_request verify --run <peticion-extendida>
```

La extensión conserva el objetivo, datos, controles e historial anterior. Añade
una entrada por intento compacto: estado, reglas exactas cuando existen, revisión
y motivo literal no verificado. No rellena reglas ausentes o completa frases del
modelo. Añade sus huellas al conjunto de reglas consumidas sin duplicarlas.

Requiere una petición base vigente para las memorias antiguas y la misma referencia
congelada. Si las nuevas reglas cambiaron las reservas, primero se debe renovar ese
contexto base. Los motivos permanecen codificados como datos del mensaje de usuario;
no se convierten en instrucciones de sistema. No se afirma que un modelo vaya a
respetarlos por sí solo: los controles siguen en Python.

El máximo permanece en 12.288 bytes. Se incluyen todas las entradas y los motivos
completos; si no caben, se detiene sin omitirlos o recortarlos. No se estima el
recuento de tokens ni se garantiza encajar en el proveedor. El consumo de origen
se vincula por separado y el consumo nuevo es cero.

`prepared.json` usa un protocolo distinto y mantiene envío, proveedor y permiso de
generación deshabilitados. Incluye el presupuesto observado, también si ya está
consumido. Los controladores antiguos no aceptan este archivo como permiso nuevo;
no se habilita una ruta de envío ni se modifica el contador existente.

La [prueba local](../reports/phase4-compact-candidate-2026-10-20.md) produjo reglas
completas pero duplicadas: se conservaron sin aprobar o simular. La
[comprobación de memoria y petición](../reports/phase4-compact-memory-request-2026-10-20.md)
incorpora ese descarte sin otra consulta al modelo.

La [petición guiada](GUIDED_REQUESTS.md) añade la cobertura estructural sin
recortar historial o habilitar envío. La [lectura con caché](VALIDATED_READ_CACHE.md)
permite verificarla con reutilizaciones acotadas y fuentes contrastadas.

## Consulta breve de estado

```powershell
.\.venv\Scripts\python.exe -m trading_ai.compact_status --request-run <peticion-base>
```

Muestra tres líneas sobre propuesta/revisión y presupuesto, sin crear registros,
reservar intentos o ejecutar acciones. `--json` muestra también el uso de origen,
separado del consumo nuevo nulo. Solo suma intentos compactos: no presenta ese
subtotal como consumo de toda la aplicación. Un consumo desconocido permanece
desconocido; sin intentos registrados el subtotal de ese ámbito es cero.

Esta lectura no inspecciona ejecuciones o sus resultados y no afirma que no
existan. Una revisión aceptada se informa como elegible para preparar un plan,
sin iniciar cálculos. Si el estado cambia durante la doble lectura, se detiene
sin publicar un estado mezclado. La consulta no concede permisos nuevos.

Los [diagnósticos por periodos](PERIOD_DIAGNOSTICS.md) ya pueden prepararse por
separado para un plan aceptado. Conservan las reglas y todos los bloques de
desarrollo conocidos, sin seleccionar una estrategia o simular durante la
preparación. El duplicado real sigue fuera de ese flujo.
