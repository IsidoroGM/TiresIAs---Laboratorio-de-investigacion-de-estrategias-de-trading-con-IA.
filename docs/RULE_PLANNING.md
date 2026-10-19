# Revisión técnica y plan previo de reglas

`trading_ai.rule_planning` separa la traducción propuesta, su revisión y el
registro previo de un experimento. No consulta IA ni ejecuta simulaciones.
No se ofrece como herramienta de autoaprobación al investigador.

## Revisión del significado

Solo una traducción `pending_semantic_review`, con reglas válidas y un origen
completo, puede recibir una revisión técnica. La revisión declara que se han
comprobado entrada, salida, parámetros, suficiencia de datos y ausencia de
ambigüedades. También identifica al revisor y explica su decisión.

La evaluación se proporciona en un JSON con estos campos exactos:

```json
{
  "schema_version": 1,
  "translation_sha256": "<SHA-256 de translation.json>",
  "spec_sha256": "<spec_sha256 del registro de traducción>",
  "reviewer": "<responsable de la revisión técnica>",
  "decision": "needs_clarification",
  "rationale": "<motivo concreto y comprobaciones realizadas>",
  "checks": {
    "entry_matches": false,
    "exit_matches": false,
    "parameters_match": false,
    "data_sufficient": false,
    "no_unresolved_ambiguity": false
  }
}
```

El ejemplo no es una revisión aceptada. Los hashes vinculan la evaluación con
la traducción y las reglas exactas: una evaluación antigua no sirve para otro
archivo. Se pueden obtener con `Get-FileHash` y el campo `spec_sha256` del JSON.
Decisiones permitidas: `accepted`, `needs_clarification` o `rejected`. Aceptar
exige las cinco comprobaciones en `true`; no se infieren de la confianza del
modelo ni de que las reglas compilen. Las reglas nuevas siguen correspondiendo
al agente: el revisor comprueba el significado y no sustituye una salida ambigua
por una estrategia de su elección.

La revisión es una **declaración técnica**, no una prueba automática de
equivalencia. El programa no autentica la identidad escrita del revisor ni
puede demostrar que sus comprobaciones sean ciertas. El responsable de la
revisión debe contrastar el texto, los parámetros y las reglas. El registro
declara expresamente ese alcance y no activa permisos de simulación.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.rule_planning review --translation-run <traduccion> --assessment <revision.json> --frozen-run <registro-previo>
.\.venv\Scripts\python.exe -m trading_ai.rule_planning verify-review --run <revision-registrada> --frozen-run <registro-previo>
```

Si la traducción está en `needs_data`, `needs_clarification` o `unsupported`,
no hay reglas que revisar. Sin `--assessment`, el comando guarda el estado
`blocked_by_translation`. No consulta al modelo y no admite aprobar ese
borrador mediante una evaluación añadida. La idea y la traducción se conservan
intactas. Resolver dudas requerirá una propuesta nueva y explícita.

## Registro previo del experimento

Solo una revisión `accepted` y todavía verificable permite preparar un plan:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.rule_planning prepare --review-run <revision-registrada> --frozen-run <registro-previo>
.\.venv\Scripts\python.exe -m trading_ai.rule_planning verify-plan --run <plan> --frozen-run <registro-previo>
```

El plan fija automáticamente, sin opciones para cambiarlos en esa CLI:

- Una candidata, con sus reglas y hash exactos, y la base SMA/EMA del protocolo.
- El par, capital, costes, tamaño y criterio del registro previo existente.
- Una copia exacta de `development.xml`, con su cobertura y SHA-256.
- Como máximo una simulación de candidata y una de base: dos en total por plan.
- Cero consultas de IA, variaciones de parámetros y reintentos automáticos.
- Solo compras largas, ejecución en la siguiente observación y cuentas sin
  arrastre de posiciones o señales entre particiones.
- Resultado inconcluso si alguna estrategia no tiene cierres o ambas métricas
  empatan, según `experiments.expected_assessment`.

El estado es `registered_not_run`, `executable: false` y resultados `null`.
El [ejecutor de planes](RULE_EXECUTION.md) consume ese presupuesto mediante una
reserva exclusiva antes de calcular, sin alterar el plan original. Repetir la
preparación crea otro registro y no libera otro intento para los mismos cálculos.
Este flujo no establece un presupuesto global de investigación ni limita
ejecuciones manuales del motor.

Toda esta cobertura de desarrollo ya es conocida. Se etiqueta
`known_development_history_only`; no se permite abrir evaluación exterior ni
presentar el ensayo futuro como evidencia inédita. Preparar un plan no prueba
rentabilidad ni sustituye las comprobaciones de robustez.

## Integridad y registros

Cada intento usa una carpeta nueva: `.local/rule-reviews` o `.local/rule-plans`.
`review.json` o `plan.json` tiene un sello SHA-256 y eventos de cierre. Los planes
incluyen revisión, traducción, identidad de la idea, datos, supuestos y código.
La verificación contrasta los archivos y reconstruye el plan esperado: modificar
presupuesto, reglas, base o controles no se acepta solo por recalcular el sello.

Los errores también quedan registrados. Un intento fallido no es un plan
completo; se exige sello y cierre correcto. Las fuentes no se sobrescriben.
Cambios posteriores de código o fuentes requieren registros actualizados.
Los hashes detectan diferencias respecto a las referencias, pero no son firmas
ni una protección contra modificar coherentemente todas las evidencias locales.

El borrador real anterior quedó bloqueado y no produjo un plan. La
[comprobación conservada](../reports/phase4-rule-planning-2026-10-19.md) no
consultó IA, abrió evaluación exterior ni ejecutó backtests. Las ramas de
aceptación y registro se comprueban con ejemplos artificiales en las pruebas.
Suite completa: **669 pruebas aprobadas**, incluidas 46 nuevas, con caché
desactivada y temporal exclusivo nuevo según `AGENTS.md`.

FASE 4 sigue abierta, OpenAI continúa desactivado y TradingView sigue pendiente
según su plan. Sin nuevas dependencias, servicios, commits ni pushes.
