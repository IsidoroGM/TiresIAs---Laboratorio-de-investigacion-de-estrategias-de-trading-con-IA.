# Conversación y pruebas con históricos BID/ASK

22/10/2026. Incremento de FASE 6. La conversación ya puede revisar una propuesta
SMA y compararla con otra SMA sobre un histórico de precios aportado. Se conserva
el recorrido BCE para SMA/EMA y su presupuesto; no se crean cuentas ni órdenes.

## Recorrido en TiresIAs

1. En **Conversar con el agente**, crear o retomar una conversación. Por ejemplo:
   «Propón SMA 15/45 para EUR/USD con precios BID/ASK, posiciones largas».
2. Revisar la respuesta. Su texto y sus parámetros son una sugerencia sin autoridad
   para ejecutar. Puede contener errores o preguntas innecesarias.
3. En **Estrategia y prueba histórica → Fuente para la prueba**, elegir
   **Históricos BID/ASK · EUR/USD · SMA**. Una sugerencia no elige automáticamente
   la fuente, los costes o el capital.
4. Seleccionar un histórico preparado. La ficha verifica sus originales y muestra
   período UTC con fin exclusivo, sesiones y huella. Se utiliza todo ese período;
   para cambiarlo, preparar antes otro histórico con fechas explícitas.
5. Revisar SMA base y variante, ventanas, capital USD, cantidad fija EUR, tasa de
   comisión supuesta, criterio e hipótesis. Confirmar las reglas y pulsar
   **Guardar propuesta BID/ASK revisada**. Guardar no calcula.
6. Pulsar **Aprobar esta revisión y probar con BID/ASK**. Aprueba una revisión
   concreta y reserva una comparación con dos cálculos. Cambiar campos exige una
   nueva revisión; cambiar datos o código invalida la aprobación anterior.
7. Abrir **Prueba histórica → Ver métricas verificadas**. Muestra base y variante,
   veredicto del criterio, curvas, ejecuciones, rechazos y procedencia, dentro de
   la conversación. El enlace al histórico vuelve a verificar sus originales.
8. Elegir ese resultado como evidencia y preguntar sobre él. Con **Sin mensajes
   anteriores** se reduce el contexto sin perder el historial guardado. La
   explicación utiliza el criterio registrado y texto compuesto por Python;
   el modelo solo selecciona aspectos admitidos. Una respuesta contradictoria
   queda rechazada con su original y consumo conservados.

También puede prepararse la ficha manualmente sin enviar un mensaje al modelo.
La explicación con texto generado sí requiere el Ollama y modelo locales ya
configurados. El laboratorio no los descarga automáticamente.

## Reglas y límites

- BID/ASK admite solo cruces SMA largos en EUR/USD, con rápida hasta 120 y lenta
  hasta 252, rápida menor que lenta y variante distinta de base. EMA sigue en BCE;
  no se sustituye por SMA silenciosamente. RSI, stops, cortos y órdenes actuales
  no se ejecutan a partir de un texto libre.
- Se conservan sesiones UTC observadas, domingos y días parciales. La señal usa
  cierre BID, compra ASK y vende/valora BID en la siguiente apertura observada.
  El spread está en los precios; la comisión supuesta se cobra aparte. No se
  modelan swaps o deslizamiento ni se fuerza una venta final.
- La revisión exige suficientes sesiones para ambos cruces y una apertura
  posterior. Los huecos bloquean antes de reservar una comparación. Los originales
  se verifican al revisar, aprobar y ejecutar.
- El presupuesto sigue siendo **24 respuestas y cuatro comparaciones globales**,
  compartido entre BCE y BID/ASK. No aumenta al cambiar conversación o fuente.
  Un alias del mismo histórico, otros ceros decimales, hipótesis o criterio no
  permiten repetir el mismo cálculo. Fallos y cancelaciones conservan la reserva.
- Una consulta GET no calcula ni llama al modelo. La ejecución copia las entradas
  y aprobación; la consulta contrasta sus huellas. Un trabajo interrumpido requiere
  revisión y no se reenvía automáticamente. No se procesan cuentas virtuales.

Los resultados BID/ASK de este recorrido se consultan en su conversación y se
conservan en `.local/chat-price-experiments/`. No se publican como experimentos
BCE en el catálogo anterior. El [modo manual de operaciones](MANUAL_OPERATIONS.md)
utiliza cuentas independientes y otro recorrido de revisión/aprobación dentro del chat.

## Comprobación real y límites del modelo

Se solicita una sola propuesta SMA 15/45 al Qwen3.5:4b local y se conservan esas
ventanas. El borrador añade preguntas sobre EMA y avisos de stops/cortos no pedidos;
queda incompleto. Se guarda una revisión humana explícita con las reglas admitidas
y después se aprueba la comparación con SMA 20/60 sobre 307 sesiones de 2025,
1.000 USD hipotéticos, 1 EUR y comisión supuesta 0,001.

| Resultado | Base 20/60 | Variante 15/45 |
| --- | ---: | ---: |
| Patrimonio final USD | 999,98870447 | 999,99492622 |
| Máxima caída observada % | 0,00320538 | 0,00603529 |
| Operaciones cerradas | 1 | 2 |

La variante pierde menos, pero tiene mayor caída: **no respalda el criterio de
mayor retorno sin mayor caída**. Un cálculo independiente reproduce las dos
estrategias, 614 puntos de patrimonio y ocho ejecuciones. La base coincide con
la prueba anterior. No se selecciona una nueva estrategia ganadora.

La explicación real del modelo afirma cumplimiento cualitativo de un «criterio
de cruce alcista», que no es el criterio registrado. Ese error se conserva. La
interfaz antepone la conclusión calculada por Python y etiqueta el comentario
como interpretación que requiere revisión. No se declara fiabilidad semántica
general del modelo ni se permite que cambie el veredicto o autorice operaciones.

La comprobación utiliza dos respuestas y una comparación del presupuesto existente.
463 pruebas seleccionadas aprobadas, incluidas 26 nuevas de conversación BID/ASK
y 46 previas de conversación. No se ejecuta toda la colección. Evidencia en el
[informe](../reports/phase6-chat-prices-2026-10-22/README.md). FASE 6 sigue abierta,
sin cambio de PROJECT_STATUS, commit o push.

Después de ese ensayo se incorpora el [contrato de explicaciones contrastadas](CHAT_EXPLANATIONS.md).
El comentario incorrecto anterior sigue conservado y etiquetado; no se reescribe.
Las preguntas nuevas con evidencia ya no publican conclusiones libres del modelo.
