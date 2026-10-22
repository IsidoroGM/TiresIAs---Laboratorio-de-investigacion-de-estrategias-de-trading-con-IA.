# Conversación con históricos BID/ASK y revisión antes de ejecutar

22/10/2026. Incremento de FASE 6, sin cierre ni inicio de demo externa.
`protocol.json` fija la comprobación de integración antes del ensayo real:
SMA 15/45 frente a 20/60, histórico de 2025 hasta el 24/12, 1.000 USD hipotéticos,
cantidad fija de 1 EUR y comisión supuesta 0,001. No se realiza una búsqueda de parámetros.

## Implementación

`conversation_prices` prepara revisiones humanas con fuente y reglas BID/ASK
explícitas y utiliza el motor SMA existente sin modificarlo. Se conservan el
trabajador, SQLite, identidad de peticiones, cancelación y cuatro comparaciones
globales de la conversación. BCE y BID/ASK comparten ese límite; no se amplía
ni reinicia. Guardar una revisión no ejecuta; la aprobación identifica revisión,
huella de código y fuente. Un alias del mismo precio o cambios de texto, criterio
y formato decimal no permiten repetir un intento ya reservado.

Los originales se reconstruyen y verifican al revisar, aprobar y ejecutar.
Los huecos y la historia insuficiente bloquean la revisión. Los dos cálculos usan
la misma copia de sesiones, cantidad y costes, con compra ASK, venta/valoración BID
y siguiente apertura observada. Se guardan entradas, aprobación, resultados y
procedencia. GET comprueba copias y no calcula estrategias ni llama al modelo.
No se modifican Pine, contratos, motor SMA ni contabilidad virtual.

La interfaz añade elección de fuente, ficha BID/ASK, aprobación separada y métricas,
curvas y operaciones en la conversación. El resultado puede adjuntarse como evidencia
para otra pregunta. El criterio calculado por Python se muestra junto al comentario
del modelo y en la tabla, con etiquetas legibles y originales conservados.

## Ensayo real

Se inicia el Ollama ya instalado con la identidad habitual de Windows: la identidad
aislada no podía abrir los manifiestos del modelo. No se cambian permisos generales
ni se descarga otro modelo. Ollama 0.40.6, Qwen3.5:4b, huella
`d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`, CPU y límites de contexto anteriores.

La primera respuesta conserva SMA 15/45 pero introduce dos preguntas y avisos
genéricos de stops/cortos no solicitados. El borrador queda incompleto. Se realiza
una revisión humana explícita, con las ventanas originales y fuente de 2025,
seguida de una aprobación desde el navegador. No se ejecuta directamente el texto
del modelo. Una segunda respuesta recibe ese resultado como evidencia, sin
mensajes anteriores añadidos al contexto.

Base: 999,98870447 USD, caída observada 0,003205379045267818213953294716 %, un cierre.
Variante: 999,99492622 USD, caída 0,006035287026639822136920034699 %, dos cierres.
Ambas conservan 1 EUR abierto. La variante tiene mayor retorno y mayor caída:
`not_supported_in_sample` para el criterio registrado. El resultado negativo
respecto al criterio se conserva; no se elige una estrategia ganadora.

La explicación del modelo afirma un cumplimiento cualitativo de «criterio de cruce
alcista», distinto del criterio registrado. Se conserva ese fallo semántico y la
respuesta original. La conclusión de Python queda visible junto al comentario;
no se presenta el texto del modelo como un veredicto verificado.

Se consumen dos intentos de respuesta y una comparación; quedan 22 respuestas y
tres comparaciones. No se repiten inferencias para obtener una explicación más
favorable. Las cuentas virtuales y el inbox permanecen sin cambios.

## Verificación

463 pruebas seleccionadas aprobadas: 26 nuevas de conversación con precios, 46 de
conversación previa y las 391 seleccionadas del incremento anterior. No se ejecuta
la colección completa. Pytest usa caché desactivada y temporal GUID exclusivo según
AGENTS.md. Se comprueba sintaxis JavaScript y el recorrido real en navegador.

La reconstrucción independiente stdlib/Decimal desde el gzip reproduce medias,
señales, costes, ocho ejecuciones y 614 puntos de patrimonio y drawdown. La base
coincide con el resultado anterior. Se verifican también los originales y las
evidencias previas sin modificarlas. Los gzip permanecen fuera de Git.

`manifest.json` conserva huellas de fuentes, resultados, conversación del ensayo,
auditoría, pruebas y capturas. No contiene el token HTTP de acciones. PROJECT_STATUS
no cambia y no se realiza commit o push.
