# Explicaciones contrastadas del chat

22/10/2026. Incremento de FASE 6, sin cierre. `protocol.json` se fija antes de la
comprobación real y reutiliza el resultado BID/ASK anterior, sin nuevos backtests.

## Cambio y límites

La explicación libre anterior permitía afirmar cumplimiento de otro criterio y
no enviaba explícitamente el criterio registrado. Ahora los mensajes con evidencia
usan un contrato separado: criterio, evaluación exacta y hasta tres aspectos
admitidos, sin texto libre, preguntas o propuestas. Python recompone cada frase
a partir de las métricas guardadas. El modelo no puede modificar el veredicto.

Se comprueban JSON estricto, campos, relaciones, alcance y criterio; evidencia y
solicitud conservan huellas. Se verifica el resultado antes y después de inferir.
El proveedor cuenta el esquema efectivo dentro de la misma cota de contexto.
Respuestas incompatibles no se convierten en mensajes ni revisiones; conservan
original, consumo, error y reserva. Puede mostrarse un resumen determinista cuando
la evidencia sigue íntegra. No se reenvían trabajos automáticamente.

La interfaz distingue **Agente · explicación contrastada**, con origen Python del
texto y origen modelo de los aspectos, de las interpretaciones antiguas sin ese
contrato. La respuesta incorrecta anterior se conserva byte a byte. Se mantienen
propuestas sin evidencia, motores, límites, contabilidad y resultados anteriores.

La correspondencia de las frases con la evidencia no equivale a razonamiento libre
fiable. El modelo puede omitir aspectos pedidos; las preguntas sobre hechos ausentes
siguen limitadas al contenido que puede explicar este contrato. No se utiliza una
lista de palabras como supuesto detector semántico general.

## Comprobación real

Conversación `0190241d62b543c6b69b4a5db31051d6`; explicación
`c7af5d216275498d8d6e2f1a292ffa1c`; resultado anterior
`3efdcca61aa34110950cfaa6374d43b5`, archivo SHA-256
`221279810c1472bccfc3849440462fa93e933c8246dc81b9abd1b6d0debf6516`.

Desde el navegador se adjunta ese resultado y se elige ningún mensaje anterior.
Se pregunta una vez por criterio, rentabilidad, caída y comisiones. El modelo local
Qwen3.5:4b mantiene el criterio `higher_return_without_more_drawdown` y evaluación
`not_supported_in_sample`, retorno mayor y caída mayor. Selecciona `return`,
`drawdown` y `scope`: omite comisiones pedidas. Se conserva esa limitación y no se
repite la inferencia. La explicación visible incluye criterio, conclusión y ambos
signos, y aclara que una rentabilidad mayor significa perder menos en esta muestra.

El mismo modelo/digest y límites anteriores consumen 291 tokens de entrada y 96 de
salida, duración informada 25,7354833 s, coste API 0 USD. Las reservas pasan de 2 a 3
respuestas y permanecen en una comparación; quedan 21 respuestas y tres comparaciones.
Los trabajos y mensajes anteriores permanecen idénticos. Cuentas e inbox sin cambios.

## Pruebas y evidencia

41 pruebas nuevas cubren ambos criterios, las nueve relaciones posibles por
criterio, falta de cierres, costes/posiciones, campos libres, cambios de evidencia,
preservación de errores/consumo, recuperación y proveedor/contexto. Las 113 pruebas
de conversación pasan en la comprobación inicial.

Selección ampliada: 525 casos, **524 aprobados y uno fallido** en la primera ejecución.
El fallo es WinError 10053 en el rechazo de transporte chunked del receptor HTTP;
la repetición aislada pasa **1/1**, sin modificar el código del receptor. Se conservan
`tests.log/xml` y `transport-recheck.log/xml`. No se afirma una ejecución inicial
completamente verde ni una ejecución de toda la colección. Pytest usa caché
desactivada y un temporal GUID nuevo en cada ejecución, según AGENTS.md.

Se comprueban sintaxis JavaScript, espacios de Git, interfaz real y conservación de
ocho informes anteriores con sus evidencias y originales. El manifiesto incluye
captura, petición preparada, contrato, respuesta y texto visible; no guarda el token
HTTP de acciones. No se reinicia presupuesto, descarga modelo, cambia permisos
generales, procesa una cuenta, modifica PROJECT_STATUS ni hace commit/push.
