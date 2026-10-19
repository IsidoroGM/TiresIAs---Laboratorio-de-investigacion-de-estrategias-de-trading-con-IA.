# Propuestas de traducción de ideas a reglas

`trading_ai.formalization` vincula una idea de la bandeja versión 2 con una
propuesta en el [lenguaje de reglas](RULE_SPEC.md). Una consulta local como
máximo por ejecución, sin reintentos automáticos, búsqueda ni simulación:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.formalization --idea-run <carpeta-idea> --frozen-run <carpeta-registro-previo>
```

Se admiten `--config` y `--output-dir`. El proveedor predeterminado sigue siendo
Ollama local; OpenAI está reservado y falla antes de consultar una API de pago.
El comando no instala dependencias, inicia servicios ni descarga datos.

## Flujo y estados

Python verifica la idea original, su identificador, respuesta registrada, cierre
y referencia de desarrollo. Solo acepta ideas pendientes y sin resultados. Se
verifica el mismo desarrollo registrado, sin abrir la partición exterior ni sus
comparaciones. Al modelo se envía el texto exacto de la propuesta y las
capacidades del lenguaje, sin precios ni métricas históricas.

Si faltan datos declarados, se registra `needs_data` con cero consultas. En los
demás casos, el modelo devuelve un objeto con `status`, `reason` y `spec`:

| Respuesta del modelo | Registro de Python | Reglas guardadas |
|---|---|---|
| `needs_clarification` | `needs_clarification` | Ninguna |
| `unsupported` | `unsupported` | Ninguna |
| `proposed` con reglas válidas | `pending_semantic_review` | Especificación canónica y SHA-256 |
| JSON, campos o reglas inválidos | Error conservado en eventos | Ningún registro aceptado |

El modelo recibe instrucciones de no elegir alternativas ambiguas ni inventar
condiciones, parámetros o significados de ventanas. Si la idea no cabe fielmente
en el lenguaje, debe indicar la limitación. Las dudas y las incompatibilidades
requieren `spec: null`; no se acepta una traducción parcial junto a ellas.

La compilación comprueba estructura y límites. **No demuestra que la traducción
signifique lo mismo que el texto original.** La detección de ambigüedad por el
modelo puede fallar. Por eso incluso una especificación compilable conserva
`semantic_equivalence_verified: false`, `executable: false` y
`calculated_results: null`. No se generan señales ni se llama al simulador.
El capital, los costes, el tamaño y la ejecución posterior siguen separados.
La explicación del modelo también puede contener errores: se conserva como
declaración del modelo, sin utilizarla para redefinir los controles del motor.

## Evidencias y consumo

Cada intento crea una carpeta nueva en `.local/formalization`. `events.jsonl`
conserva solicitud, contrato, respuesta original, errores, consumo y hashes del
código. Una traducción registrada añade `translation.json`, con el texto
original, identidad de la idea y hashes de sus archivos de origen. El origen se
vuelve a verificar antes de guardar; un cambio durante la consulta detiene el
intento. Los hashes permiten comprobar coincidencias de archivos locales; no
son una firma ni impiden modificar archivos y hashes conjuntamente.

Se conserva el consumo conocido incluso si el JSON falla o la respuesta se
trunca. Si una llamada falla sin informar uso o coste, se registra desconocido,
sin convertirlo en cero. Un bloqueo previo por datos declarados registra cero
solicitudes y cero coste de API. El servicio local usa recursos del equipo.
Repetir manualmente el comando crea otro intento y otra posible consulta.

La [revisión técnica y el registro previo](RULE_PLANNING.md) permiten declarar
la revisión del significado y fijar los límites antes de habilitar cálculos.
Una traducción no selecciona una estrategia por rentabilidad ni modifica una
idea anterior. FASE 4 sigue abierta; no se actualiza `PROJECT_STATUS.md`.

Comprobación de esta integración: **623 pruebas aprobadas**, incluidas 36 nuevas.
La [prueba local conservada](../reports/phase4-formalization-2026-10-19.md)
registró `needs_clarification`, sin reglas ni resultados simulados.
