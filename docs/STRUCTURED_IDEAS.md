# Propuestas con reglas explícitas desde su origen

`trading_ai.structured_ideas` pide al investigador reglas en el lenguaje que
Python ya entiende. Evita tener que adivinar después qué significa «la media
rápida» o a qué indicador corresponde cada ventana. No cambia el motor.

## Contrato inicial

El modelo devuelve solamente `title`, `hypothesis`, `entry` y `exit`. La
hipótesis es texto sin verificar. Entrada y salida tienen una condición cada
una, con `left`, `operator` y `right`:

- Serie `reference`: referencia BCE y `lag` explícito.
- Indicador `sma`, `ema`, `rolling_min` o `rolling_max`: `window` y `lag` explícitos.
- Constante: `value` decimal como texto.
- Operador: `gt`, `gte`, `lt`, `lte`, `eq`, `crosses_above` o `crosses_below`.

Ventanas 1–252 y retardos 0–252. No hay referencias futuras, código libre, datos
externos o campos para capital, costes, tamaño y permisos. Python comprueba
tipos, campos y límites; no basta con que el proveedor devuelva JSON.

Una regla como `reference(lag=0) gt ema(window=20, lag=1)` identifica ambos
operandos sin inventar una correspondencia entre nombres y parámetros. Es un
ejemplo del formato, no una estrategia elegida ni un resultado calculado.

Python envuelve cada condición en un grupo `all` del `RuleSpec` existente y
asigna un nombre técnico fijo. No genera señales ni ejecuta el simulador.
Calentamiento, prioridad de salida y ejecución en la observación siguiente
siguen perteneciendo al motor. La compilación demuestra estructura válida,
no que la hipótesis tenga sentido, produzca operaciones o mejore resultados.

## Uso acotado

```powershell
.\.venv\Scripts\python.exe -m trading_ai.structured_ideas propose --frozen-run <registro-previo>
.\.venv\Scripts\python.exe -m trading_ai.structured_ideas verify --run <propuesta> --frozen-run <registro-previo>
```

`propose` admite `--config`, `--question` y `--output-dir`. Solo Ollama local:
**una consulta**, salida máxima 384 tokens, contexto máximo 4096, cero
traducciones, cero simulaciones y cero reintentos automáticos. No inicia
servicios, instala paquetes, descarga modelos o consulta APIs de pago.
La configuración se comprueba antes de contactar al proveedor.

La llamada, respuesta cruda y consumo se registran antes de validar. Una salida
inválida o truncada conserva su error y consumo conocido; el desconocido no se
convierte en cero. Se crea una carpeta nueva por invocación, sin reanudar ni
reintentar una generación dentro de ella.

El presupuesto anterior corresponde a **esta herramienta**. Es una entrada
nueva separada del [controlador de sesiones v2](RESEARCH_SESSION.md): todavía
no se incorpora a su ciclo ni se imputa a su presupuesto. Una invocación manual
no amplía ni reinicia ninguna sesión anterior. No hay bucle automático de
generaciones hasta encontrar una propuesta aceptable.

## Memoria, duplicados y procedencia

Se conserva una copia de la memoria anterior de ideas y dudas, sin evaluación
exterior ni selección por resultados. También se consultan las propuestas
estructuradas anteriores con reserva y cierre verificables del mismo desarrollo.
Se envían como máximo cuatro ideas/reglas de contexto; como máximo dos son
reglas estructuradas. Los historiales completos mantienen sus huellas y fuentes.

Las propuestas estructuradas usan una reserva exclusiva compartida en
`.local/structured-idea-access`. La identidad depende del desarrollo y las
reglas normalizadas. Título, hipótesis y formas decimales como `1`/`1.0` no crean
una candidata nueva. Si dos generaciones coinciden, una queda en
`pending_semantic_review` y la otra en `duplicate_rules`, vinculada al origen.
La reserva no se elimina por un fallo posterior ni cambia al elegir otra carpeta.

Se limita el historial estructurado a 128 reservas; superarlo requiere revisión
explícita, sin descartar entradas silenciosamente. Una reserva interrumpida sin
propuesta no se presenta como terminada y sigue impidiendo reutilizar sus reglas.
Una propuesta presente sin cierre verificable bloquea su incorporación.

Las reglas pueden ser equivalentes de otras maneras que la huella no detecta.
Las ideas antiguas en texto solo aportan contexto: no se presume equivalencia
automática entre ese texto y las nuevas reglas.

## Registros y siguiente integración

Cada carpeta conserva `proposal.json`, `report.md`, `events.jsonl`, `memory.json`
y `rules-memory.json`. `verify` comprueba respuesta original, compilación,
fuentes, hashes, ubicación, código, reserva, informe y consumo, sin consultar IA
o recalcular resultados. Cambios de fuentes o código pueden invalidar un registro;
los archivos y hashes son controles locales, no firmas contra manipulación conjunta.

Una propuesta válida continúa con `executable: false`, sin resultados ni
equivalencia semántica verificada. No se fabrica una traducción antigua ni una
aprobación para introducirla en los planes existentes.

El [flujo estructurado](STRUCTURED_WORKFLOW.md) ya conecta este origen con la
revisión técnica, el plan y una sesión de ejecución. Atribuye su consumo sin
regenerar la propuesta y conserva la trazabilidad y el presupuesto.
FASE 4 sigue abierta; `PROJECT_STATUS.md` no se actualiza en esta entrega.

## Comprobación de esta entrega

**819 pruebas aprobadas**, incluidas 37 nuevas. La
[primera comprobación local](../reports/phase4-structured-ideas-2026-10-19.md)
produjo una propuesta estructuralmente válida con una consulta, 0 USD de API y
cero traducciones o simulaciones. Su salida incluye `lag=1`: el retardo está
identificado y permanece pendiente de revisión frente a la hipótesis.
