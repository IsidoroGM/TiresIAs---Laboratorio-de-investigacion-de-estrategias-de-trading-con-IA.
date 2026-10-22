# Explicaciones contrastadas de resultados del chat

Incremento de FASE 6, 22/10/2026. Con un resultado BCE o BID/ASK adjunto, el modelo
selecciona de uno a tres aspectos: criterio, rentabilidad, caída, costes, posiciones
o alcance. Python redacta el texto con plantillas y las métricas guardadas. El modo
sin evidencia mantiene la conversación y las propuestas revisables anteriores.

## Uso

1. En la conversación que contiene la prueba, elegir **Resultado histórico** como
   evidencia y los mensajes anteriores que se enviarán. Puede elegirse ninguno.
2. Preguntar, por ejemplo, si la variante cumple el criterio o por sus comisiones.
3. La respuesta aceptada aparece como **Agente · explicación contrastada**. Indica
   que Python elaboró el texto y el modelo seleccionó los aspectos. El criterio,
   veredicto, relación de retorno y caída y alcance aparecen siempre; costes y
   posiciones añaden hechos cuando se eligen esos aspectos.
4. En **Respuesta local**, consultar respuesta original, comprobación, tokens y
   contexto. Si el modelo no respeta el contrato, no se añade una explicación al
   historial: el trabajo muestra el error y el resumen de Python de la evidencia.
   Si la evidencia cambia o queda alterada, ese resumen tampoco se publica.
5. Para proponer otra estrategia, elegir **Sin resultado adjunto**. Explicar un
   resultado no abre una propuesta ni una orden.

## Qué se comprueba

El contrato `conversation_evidence_explanation_v1` no tiene campos de texto libre,
preguntas, reglas no soportadas o propuestas. Exige criterio y evaluación exactos,
incluido alcance de muestra histórica. Python vuelve a calcular la evaluación
desde las métricas ya guardadas, sin ejecutar estrategias. Comprueba aspectos
admitidos, únicos y limitados, rechaza campos adicionales y JSON duplicado.

La solicitud conserva esquema, contexto y huella del resultado dentro del payload
firmado por hash. El resultado se verifica antes y después de la inferencia; otra
conversación no puede adjuntarlo. La cota de contexto cuenta el esquema utilizado,
sin truncar mensajes. El proveedor mantiene versión, huella, CPU, contexto y salida.

Errores de formato, contradicciones, fallos y cancelaciones conservan intento y
consumo disponible. No hay repeticiones automáticas ni aumento del presupuesto:
siguen siendo 24 respuestas y cuatro comparaciones globales. Consultar o refrescar
no llama al modelo ni recalcula una estrategia. El original se conserva para
auditoría; no se transforma en un comentario verificado por mostrarlo en su ficha.

## Alcance

Se garantiza la correspondencia del texto compuesto con los campos comprobados,
no la fiabilidad semántica general del modelo. El modelo puede seleccionar aspectos
poco pertinentes o devolver una evaluación incompatible; en ese caso se rechaza.
Las preguntas sobre hechos ausentes del resultado no reciben una explicación libre
inventada. El texto no evalúa estrategias arbitrarias ni autoriza operaciones.

Se conserva el comentario incorrecto del ensayo anterior y se etiqueta como
anterior al contrato. Los históricos, cálculos, motores y evaluaciones anteriores
no cambian. La evidencia de este incremento se guarda en
`reports/phase6-chat-explanations-2026-10-22/`, sin cierre de fase ni commit/push.
