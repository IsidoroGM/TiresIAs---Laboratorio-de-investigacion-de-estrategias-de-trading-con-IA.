# Reformulación de ideas y lectura de resultados

`trading_ai.agent_feedback` añade dos tareas independientes para el investigador:
reformular una idea con dudas y contrastar su lectura de resultados verificados.
No ejecuta estrategias, crea planes ni aprueba sus propias reglas.

## Una reformulación explícita

```powershell
.\.venv\Scripts\python.exe -m trading_ai.agent_feedback revise --translation-run <traduccion-con-dudas> --frozen-run <registro-previo>
.\.venv\Scripts\python.exe -m trading_ai.agent_feedback verify-revision --run <reformulacion> --frozen-run <registro-previo>
```

Solo admite traducciones `needs_clarification` completas y verificables. Envía
la idea original, la razón previa identificada como declaración no verificada
del modelo y metadatos de desarrollo. No envía precios ni resultados de
estrategias. Los hechos sobre datos disponibles y ejecución los fija Python;
la explicación anterior del modelo no puede redefinir el simulador.

El agente puede escoger una interpretación nueva para resolver una alternativa.
Se registra como **propuesta nueva**, sin afirmar que sea equivalente a la
anterior. Python comprueba formato y límites y rechaza una copia exacta del
original; no demuestra que la nueva redacción sea clara, novedosa o mejor.
Si sigue ambigua, continúa pendiente y no se repite la consulta automáticamente.

La carpeta `.local/idea-revisions/<id>` contiene `idea.json` y `events.jsonl`.
La idea usa el contrato versión 2 de la bandeja y añade `lineage`, con identidad
de origen, profundidad, propuesta anterior y hashes de sus archivos y traducción.
El padre no se sobrescribe. `verify-revision` contrasta esa relación, el cierre,
el código y la reserva, sin consultar al proveedor.

El nuevo borrador sigue en `pending_tool_mapping` o
`needs_data_and_tool_mapping`, con `executable: false` y resultados `null`.
Es compatible con el traductor existente. La verificación de linaje es explícita;
el traductor valida el contrato de la nueva idea y no sustituye esa comprobación.
Después siguen haciendo falta traducción, revisión técnica y plan antes de
calcular. Esta tarea no elige una estrategia por cuenta del desarrollador.

## Una lectura contrastada de resultados

```powershell
.\.venv\Scripts\python.exe -m trading_ai.agent_feedback analyze --execution-run <ejecucion-completa> --frozen-run <registro-previo>
```

Primero utiliza el [verificador del ejecutor](RULE_EXECUTION.md), incluido cierre,
fuentes, código y reserva del experimento. Solo después ofrece al modelo los
resúmenes calculados de base y candidata, criterio, controles y cobertura. No
recalcula ni envía curvas completas, reglas en texto libre o evaluación exterior.

La respuesta tiene exactamente cuatro campos: `criterion_status`,
`return_comparison`, `drawdown_comparison` y `scope`. Python exige coincidencia
exacta con su conclusión. No admite métricas añadidas, promesas ni explicaciones
libres que atribuyan causas no demostradas. Se comprueba también que los
resultados y sus fuentes no hayan cambiado durante la consulta.

Si Python ya determina `inconclusive`, conserva esa conclusión sin contactar
al proveedor. Se registra `python_inconclusive_precheck`, cero solicitudes y
cero coste de API. En los otros casos, una coincidencia se registra como
`model_cross_checked_by_python`. Esto comprueba lectura del criterio, no un
razonamiento financiero general ni superioridad de la propuesta.

Cada intento usa `.local/agent-analyses/<id>`, con solicitud, respuesta, consumo
y cierre o error en eventos. Solo un intento con `analysis_completed` y su
hash correcto tiene una lectura aceptada. Un JSON parcial o un error no la
acreditan. `analysis.json` conserva la fuente y su hash, conclusión contrastada,
respuesta del modelo, proveedor y consumo, sin habilitar nuevos experimentos.

## Presupuestos y fallos

Cada tarea reserva su intento antes de consultar en
`.local/agent-feedback-access`, con creación exclusiva de archivo:

- Reformulación: una consulta como máximo por idea de origen y hash de desarrollo.
  Copiar la traducción o cambiar el texto de la duda no libera otra consulta.
  Profundidad máxima uno; una idea ya reformulada no inicia una cadena automática.
- Lectura: una consulta como máximo por identidad del cálculo. Un caso inconcluso
  no usa esa consulta, pero conserva igualmente su intento de lectura.
- Cero reintentos automáticos. Un fallo posterior a la reserva consume el intento;
  se conservan la respuesta original y el uso conocido. Uso desconocido no se
  convierte en un coste inventado de cero.

El límite es por origen o cálculo, no un presupuesto global entre todas las
ideas distintas. Borrar o manipular coherentemente archivos locales puede
invalidar estos controles; los hashes no son firmas ni autentican autores.
Las marcas no se borran automáticamente. El registro de simulaciones permanece
separado: analizar no libera ni consume nuevos backtests.

Se admiten `--config`, `--provider` y `--output-dir` en las tareas con modelo.
Ollama local es el predeterminado; OpenAI permanece reservado y falla antes de
crear el intento. No se instalan dependencias, arrancan servicios ni descargan
datos. Una consulta local no cobra por API, pero usa recursos del equipo.

El [controlador de sesiones](RESEARCH_SESSION.md) ya conecta estas tareas con
presupuesto global por sesión y una pausa para revisión técnica antes de simular.
La ampliación de capacidades y validación prospectiva sigue pendiente. El histórico ya explorado
continúa etiquetado como conocido. FASE 4 permanece abierta; no se modifica
`PROJECT_STATUS.md`, no hay commits o pushes ni operaciones reales.

Comprobación: **731 pruebas aprobadas**, incluidas 32 nuevas. La
[prueba local y las evidencias](../reports/phase4-agent-feedback-2026-10-19.md)
conservan una reformulación válida solo en formato: todavía contiene dudas y
una salida al final del periodo no contemplada por el contrato actual. No se
tradujo ni simuló. La lectura de resultados se verificó con ejemplos artificiales
y proveedores en memoria, sin otra consulta real al modelo.
