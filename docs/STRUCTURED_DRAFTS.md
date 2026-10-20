# Borradores compactos — vista previa sin modelo

El contrato experimental `structured_draft_preview_v1` contiene solamente
`entry` y `exit`, una condición explícita por lado. Usa los mismos operandos,
operadores, ventanas y retardos acotados del lenguaje de reglas existente.
No admite título, hipótesis, código, resultados o controles del simulador.

Su objetivo es reducir la salida que un modelo necesitaría redactar en una
integración futura. Python describe todos los campos de las reglas con frases
completas y marca ese origen. No rellena texto de un modelo ni inventa una
hipótesis de investigación. La integración con el investigador está pendiente.

Ejemplo artificial de archivo `borrador.json`:

```json
{
  "entry": {
    "left": {"kind": "reference", "lag": 0},
    "operator": "gt",
    "right": {"kind": "constant", "value": "1"}
  },
  "exit": {
    "left": {"kind": "reference", "lag": 0},
    "operator": "lte",
    "right": {"kind": "constant", "value": "1"}
  }
}
```

```powershell
.\.venv\Scripts\python.exe -m trading_ai.structured_draft preview --input borrador.json
.\.venv\Scripts\python.exe -m trading_ai.structured_draft verify --run <vista-previa>
```

La entrada JSON tiene un límite de 4096 bytes. Se rechazan campos repetidos,
JSON incompleto, números no finitos y condiciones fuera del lenguaje. El
registro conserva los bytes exactos de la entrada y su SHA-256, reglas
normalizadas, descripción, informe, eventos y hashes de código. La verificación
usa esa copia: cambiar el archivo externo después no reescribe el registro.

Un archivo externo no demuestra autoría de IA ni consumo anterior. El origen
queda sin atribuir y su consumo como desconocido. La vista previa registra por
separado cero consultas nuevas, cero tokens de proveedor y 0 USD nuevo de API.
No equivale a que generar cualquier archivo de origen no haya costado nada.

La vista previa no accede a datos de mercado, modelos, red o reservas de intentos.
No comprueba duplicados del histórico ni fija pregunta o contexto de investigación.
La identidad normalizada de las reglas coincide con la del protocolo existente:
escribir `1.00` en lugar de `1` no proporciona una identidad distinta.

`eligible_for_session=false` y `executable=false` permanecen fijos. El flujo
actual exige una propuesta registrada y no puede adoptar este borrador.
Antes de conectar un investigador harán falta origen verificable, contexto,
memoria compartida de reglas e intentos y revisión técnica independiente. No
se reinician presupuestos ni se reabren propuestas o reformulaciones consumidas.

El prototipo no promete que el modelo vaya a generar reglas válidas, que vaya a
usar menos tokens en una consulta real o que una estrategia mejore resultados.
Esas afirmaciones necesitan sus comprobaciones separadas. FASE 4 sigue abierta.

## Contexto de investigación sin generación

`structured_draft_context` prepara por separado objetivo, controles y metadatos
de datos copiados del registro congelado de desarrollo. Verifica ese origen;
no elige parámetros por rentabilidad ni vuelve a consultar evaluación exterior.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.structured_draft_context prepare --frozen-run <registro> --draft-run <vista-previa>
.\.venv\Scripts\python.exe -m trading_ai.structured_draft_context verify --run <contexto>
```

`--draft-run` es opcional. Guarda ideas anteriores y motivos de aclaración,
reglas registradas y reservas del mismo desarrollo en el registro compartido
`structured-idea-access`. Incluye reservas sin propuesta terminada; no borra,
reescribe o crea reservas. Rechaza identidades incompatibles y límites de
historial superados en vez de descartar fuentes silenciosamente.

Si se vincula un borrador, compara su identidad normalizada con las reservas
capturadas. `duplicate_or_reserved` indica una identidad ya consumida.
`not_found_in_captured_claims` solo indica ausencia en esa copia, sin demostrar
novedad semántica, aprobación o disponibilidad de intentos en otros controles.

Es una captura histórica: su verificación comprueba integridad de las fuentes
guardadas, sin afirmar que contiene entradas posteriores. Antes de cualquier
generación habrá que obtener contexto vigente y hacer su reserva controlada.
El contexto base no recopila por sí solo decisiones de revisión estructurada;
sus motivos heredados proceden de la memoria de ideas anterior. La memoria
complementaria descrita a continuación conserva esas decisiones por separado.

`generation_ready=false` permanece fijo. Este paso no envía solicitudes, no
aprueba propuestas y no conecta borradores al simulador. El consumo anterior
no se vuelve a producir ni se convierte en cero. Un borrador externo conserva
su `source_usage` desconocido y el contexto registra su consumo nuevo por separado.

## Memoria complementaria de revisiones estructuradas

```powershell
.\.venv\Scripts\python.exe -m trading_ai.structured_review_memory capture --context-run <contexto>
.\.venv\Scripts\python.exe -m trading_ai.structured_review_memory verify --run <memoria>
```

Lee reservas de sesiones del mismo desarrollo, verifica su propuesta y recupera
la revisión registrada por su controlador. No consulta `outcome.json` ni los
resultados financieros de la sesión. Una revisión aceptada no demuestra que la
sesión terminara o que la estrategia cumpla un criterio financiero.

Conserva decisiones, motivos, revisor y comprobaciones. Un cierre reservado sin
revisión registrada sigue consumido; no se convierte en permiso para repetirlo.
Una sesión sin cierre reservado se indica como pendiente de revisión, sin
aprobarla. Si el contexto base no incluye la reserva de una propuesta, exige
preparar un contexto actualizado antes de capturarla.

Los motivos son declaraciones del revisor sin verificar su exactitud. Se
conservan literalmente y se muestran junto a longitudes de texto calculadas,
sin corregir a escondidas discrepancias o cambiar decisiones. El consumo de
origen se copia por separado, incluidos valores desconocidos; el nuevo es cero.

El alcance son las sesiones registradas capturadas, con un máximo de 128
reservas globales. No incluye revisiones independientes fuera de ese registro
ni garantiza cubrir sesiones posteriores. Si una sesión cambia de etapa, una
captura anterior puede requerir renovación para ser verificable. No se reabren
acciones ni se conceden permisos de generación o simulación.

## Petición inspeccionable, sin envío

```powershell
.\.venv\Scripts\python.exe -m trading_ai.structured_draft_request prepare --memory-run <memoria-revisiones>
.\.venv\Scripts\python.exe -m trading_ai.structured_draft_request verify --run <peticion>
```

Prepara `request.json` con dos mensajes y el esquema compacto. El mensaje de
sistema es fijo. El objetivo, controles y datos proceden del registro congelado;
las ideas, reglas y motivos se codifican en `untrusted_history`, como datos sin
autoridad para cambiar instrucciones. Las declaraciones del revisor no pasan
a ser hechos comprobados por aparecer en una petición.

Incluye todas las entradas de las capturas, proyectando los campos necesarios
de ideas y reglas; los archivos completos siguen vinculados por hash. No
trunca motivos ni omite entradas para encajar: si el JSON completo supera
12.288 bytes, se detiene y registra el error antes de producir una petición.

El recuento es de bytes, no de tokens. `token_count` sigue desconocido y
`fits_provider_context_verified=false`: no garantiza caber en una ventana de
4.096 tokens ni demuestra ahorro de consumo. No se elige modelo o proveedor,
no se envía la petición ni se crea una reserva de generación.

`submitted=false` y `generation_ready=false` permanecen fijos. La integración
futura deberá comprobar vigencia del contexto, límites reales del proveedor y
reserva explícita antes de consultar un modelo. Esta preparación no reformula
propuestas pendientes, no continúa linajes y no habilita simulaciones.

La preparación anterior permanece sin envío. El [flujo compacto separado](COMPACT_CANDIDATES.md)
ya añade vigencia, reserva exclusiva, una consulta local, revisión y plan. Su
ejecutor exige una acción explícita posterior y no acepta propuestas duplicadas
o pendientes. No cambia los permisos de esta vista previa ni de una petición
preparada.
