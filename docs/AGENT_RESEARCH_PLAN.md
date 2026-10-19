# Desarrollo del investigador de estrategias

Decisión del usuario: 19 de octubre de 2026. El agente se encargará de proponer
nuevas estrategias; el desarrollo de Trading AI se centra en darle herramientas
de cálculo, registros y controles para contrastarlas. No se elegirá una
estrategia por preferencia del desarrollador ni se asumirá mejor por proponerla.

## Primer paso: bandeja de ideas

El nuevo módulo `trading_ai.discovery` solicita una sola idea al proveedor
configurado y la guarda como pendiente. Puede describir reglas distintas de los
cruces SMA/EMA. El contrato actual de experimentos ejecutables conserva sus
herramientas SMA/EMA; esta bandeja amplía la ideación sin cambiar ese contrato ni
los módulos vinculados a los registros anteriores.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.discovery --frozen-run '.local/holdout/<id-registro>'
```

Sustituir el identificador por el registro de desarrollo existente. Ollama debe
estar preparado según [LOCAL_AI.md](LOCAL_AI.md). El comando no inicia servicios,
instala paquetes, descarga datos ni cambia automáticamente de proveedor.

La petición usa contexto de desarrollo verificado: par, fuente, fechas,
cobertura, hash, controles y tipos de entrada disponibles. No envía precios ni
resultados calculados al modelo en este paso. La idea se genera desde su
conocimiento y ese contexto; no constituye un análisis empírico ni una búsqueda
web. El flujo no abre datos o resultados de evaluación exterior.

El modelo devuelve:

- Nombre e hipótesis breves.
- Reglas declarativas de entrada y salida, solicitadas para compra y cierre.
- Hasta seis parámetros numéricos, finitos y acotados; se solicitan como máximo
  tres para limitar la respuesta. Se rechazan nombres reservados a controles.
- Tipos de datos necesarios: referencias, OHLC, volumen, intradía u otros,
  indicados con campos booleanos explícitos (`true`/`false`).

Python comprueba campos, tipos, tamaños, valores y parámetros duplicados. No prueba la
coherencia de las reglas, su novedad conceptual ni sus afirmaciones de utilidad.
El texto se conserva como entrada no confiable; incluso si contiene código, no
se interpreta ni ejecuta. Las reglas solo se podrán calcular cuando tengan una
traducción explícita a herramientas conocidas y verificadas.

## Estado de las propuestas y datos

Cada llamada crea `.local/discovery/<id-intento>/`, con:

- `events.jsonl`: solicitud, contexto, respuesta original, consumo, cierre o
  error. El consumo se registra antes de interpretar y validar el JSON.
- `idea.json`: especificación, estado pendiente, procedencia, proveedor,
  consumo, hash de identidad y resultados calculados ausentes.

El estado es `pending_tool_mapping` cuando los datos declarados se limitan a
referencias. Si necesita datos adicionales, es `needs_data_and_tool_mapping` y
se registran los tipos faltantes, sin descargarlos. Declarar referencias como
entrada no garantiza que las reglas sean calculables o apropiadas para el BCE.

`executable` siempre es `false` y `calculated_results` siempre es `null`,
asignados por Python. Ni un nombre de estrategia conocido ni un campo del modelo
conceden permisos de ejecución. No se realiza ningún backtest ni se produce una
conclusión sobre rentabilidad. El capital, los costes y el tamaño siguen bajo
control del simulador, separados de los parámetros propuestos.

El identificador depende del JSON canónico de la idea exacta. Se conservan los
intentos repetidos; no se afirma detectar ideas equivalentes redactadas de otra
forma. Errores de formato o respuestas truncadas se registran sin reintentos
automáticos y sin generar una propuesta aceptada.

La primera prueba real del contrato inicial, que usaba una lista de datos,
repitió tipos de entrada. La aplicación la rechazó y conservó respuesta y
consumo. El contrato versión 2 utiliza campos booleanos explícitos para evitar
esa repetición; la prueba que reproduce la lista rechazada sigue en la suite.
Los intentos anteriores no se reescriben al cambiar el contrato.

La verificación real del contrato versión 2 generó un borrador válido en formato,
pero todavía basado en cruces de medias y con una salida ambigua. Queda
pendiente; esta prueba no demuestra que el agente haya encontrado una estrategia
novedosa, coherente o mejor. La [evidencia de ambos intentos](../reports/phase4-discovery-2026-10-19.md)
conserva las respuestas y el consumo. La suite completa contiene **520 pruebas
aprobadas**, incluidas 35 de la bandeja.

## Consumo y controles

Una solicitud de generación por ejecución, con los límites del proveedor local
(384 tokens de salida por defecto). No hay bucle continuo ni búsqueda masiva.
Ollama no cobra por consultas a una API; consume tiempo y recursos del equipo.
Los tokens medidos se registran; un consumo desconocido no se inventa como cero.
OpenAI permanece reservado y desactivado. Una integración de pago requerirá
acordar credenciales, presupuesto y controles antes de activarla.

## Próximas herramientas de desarrollo

El [formato de reglas versión 1](RULE_SPEC.md) ya define condiciones acotadas,
comparaciones, cruces, referencias, medias y extremos de ventanas pasadas. Se
compila a señales deterministas y se prueba su causalidad. Conserva posiciones,
ejecución, riesgo y contabilidad en el motor existente. El ejemplo técnico
reproduce SMA20/60; no propone una estrategia nueva por parte del desarrollador.

Comprobación del formato: **587 pruebas aprobadas**, incluidas 67 nuevas.
La [auditoría técnica](../reports/phase4-rules-2026-10-19.md) confirma igualdad de
señales y contabilidad completa para SMA/EMA20/60 sobre desarrollo, sin consultar
IA ni evaluación exterior. Los borradores ambiguos siguen pendientes: este paso
no elige por el modelo qué debe significar una salida con alternativas.

La [herramienta de traducción](FORMALIZATION.md) ya vincula una idea con reglas
propuestas o con una duda registrada. Si faltan datos declarados, no consulta al
modelo. Una especificación que compila queda pendiente de revisión de significado,
sin generar señales, ejecutar experimentos ni alterar el borrador original.
La comprobación de integración suma **623 pruebas aprobadas**, incluidas 36
nuevas. La [verificación local](../reports/phase4-formalization-2026-10-19.md)
conservó una duda del modelo, sin traducir la salida ambigua ni calcular resultados.

La [revisión técnica y el plan previo](RULE_PLANNING.md) ya conservan una
evaluación explícita ligada a la traducción exacta y fijan un experimento de
desarrollo con una candidata y una base. No generan resultados ni permiten
aprobar borradores sin reglas. Una aceptación es una declaración de revisión,
no una prueba automática de equivalencia entre lenguaje natural y condiciones.
Comprobación: **669 pruebas aprobadas**, incluidas 46 nuevas. El
[ensayo con el borrador real](../reports/phase4-rule-planning-2026-10-19.md)
registró el bloqueo y rechazó el plan sin consultar IA ni simular.

El [ejecutor de planes](RULE_EXECUTION.md) ya usa el motor existente para una
base y una candidata, con reserva compartida antes de calcular. Conserva errores
y resultados parciales; impide repetir los mismos cálculos mediante copias o
renombrados y ofrece lectura verificada sin recalcular. **699 pruebas aprobadas**,
incluidas 30 nuevas. La [evidencia](../reports/phase4-rule-execution-2026-10-19.md)
separa un ejemplo artificial del borrador real, que sigue sin plan ejecutable.

Las [tareas de reformulación y lectura](AGENT_FEEDBACK.md) cuentan con **731
pruebas aprobadas**, incluidas 32 nuevas. La
[comprobación local](../reports/phase4-agent-feedback-2026-10-19.md) conservó una
propuesta nueva pendiente; no resolvió todas las dudas ni produjo una estrategia
simulada. La lectura exige coincidencia exacta con las conclusiones de Python.

Quedan pendientes:

1. Integrar las [reformulaciones y lecturas contrastadas](AGENT_FEEDBACK.md) en
   un ciclo de investigación con presupuesto global por sesión. Estas tareas
   conservan antecedentes y límites por origen, sin bucles automáticos.
2. Ampliar las capacidades solo con comprobaciones de causalidad, calentamiento
   y ejecución posterior. Nunca ejecutar código libre generado.
3. Extender la investigación de desarrollo conservando descartes y errores.
   La lectura actual solo admite una conclusión coincidente con Python y no
   concede permisos para cambiar controles o ejecutar propuestas nuevas.
4. Aplicar el [protocolo de FASE 4](VALIDATION_PLAN.md) para selección, registro
   previo y comprobaciones, sin reutilizar evaluación conocida como inédita.

La evaluación exterior 2020–2026 ya se consultó y la comprobación interna
1999–2019 también es información conocida. Nuevas ideas no cambian ese hecho.
Una comprobación prospectiva necesitará un protocolo y datos no consultados al
fijar la propuesta. No se ejecutan operaciones reales ni se conecta TradingView.

Esta tarea no cierra FASE 4 ni modifica `PROJECT_STATUS.md`. Commits, pushes,
dependencias y servicios adicionales requieren su autorización correspondiente.
