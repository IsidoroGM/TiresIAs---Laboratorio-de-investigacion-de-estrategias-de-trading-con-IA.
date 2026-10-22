# FASE 5.2 — Conversación con el agente

21/10/2026. **Estado: implementada y comprobada localmente.** Los seis incrementos
quedan entregados después de FASE 5.1 y antes de FASE 6. El
[informe de cierre](../reports/phase5-2-completion-2026-10-21.md) conserva pruebas,
ensayo real, límites y errores observados. Consulta la [guía de uso](CONVERSATION.md).

## Objetivo y experiencia prevista

Poder hablar con el agente dentro de TiresIAs para convertir una idea en una
estrategia concreta, revisar sus reglas, solicitar una prueba histórica controlada
y discutir sus resultados con referencias a las evidencias guardadas.

Se añadirá una pantalla **Conversar con el agente**, conservando las cinco
pantallas actuales de consulta. Permitirá crear, retomar y consultar conversaciones;
ver los mensajes, la propuesta de estrategia, los datos pendientes, el estado del
trabajo y su consumo. Cada experimento quedará enlazado a la conversación y a la
revisión exacta de la propuesta que lo originó.

Ejemplo de recorrido:

1. El usuario escribe: «Quiero estudiar una estrategia de cruces de medias para
   EUR/USD con pocas operaciones».
2. El agente concreta las cuestiones pendientes: reglas de entrada y salida,
   temporalidad, datos disponibles, período, tamaño y costes. Distingue requisitos
   del usuario de sugerencias propias; no inventa las decisiones que faltan.
3. TiresIAs muestra una propuesta estructurada y versionada, junto con los límites
   del motor que la ejecutaría. Si una regla no está soportada, lo indica.
4. El usuario revisa y solicita **Probar en histórico** sobre esa revisión, con los
   datos y el presupuesto visibles. Cambiar las reglas exige una revisión nueva.
5. El sistema ejecuta el trabajo permitido y conserva sus evidencias. El agente
   explica las métricas disponibles y permite abrir el experimento correspondiente.

Enviar un mensaje permite una respuesta del modelo dentro del presupuesto de la
conversación. La ejecución histórica requiere su propia acción explícita: un
mensaje o una propuesta del modelo no desencadena por sí solo un backtest.

## Alcance y límites

- Conversación de investigación con el proveedor local ya configurado. Sin nuevas
  instalaciones, proveedores de pago ni descargas automáticas.
- Estrategias que puedan representarse con los contratos y cálculos existentes.
  El primer recorrido verificable usará SMA/EMA y posiciones largas. Reglas como
  posiciones cortas, stop-loss u órdenes no soportadas se mostrarán como pendientes
  de desarrollo; nunca se sustituirán silenciosamente por otra estrategia.
- Pruebas sobre datos históricos identificados, con sus limitaciones visibles.
  Consultar históricos conocidos no se presentará como validación prospectiva.
- Memoria conversacional guardada en el proyecto, con referencias a propuestas y
  experimentos. Guardar mensajes no entrena ni modifica el modelo.
- Los mensajes, resúmenes y respuestas del modelo no serán código ejecutable,
  permisos ni acreditación de que una estrategia es válida o rentable.

La petición «compra ahora» no ejecutará una operación en esta fase. La conversación
podrá explicar qué falta para tramitarla; no mostrará una compra como realizada.
El puente entre una intención revisada y una operación del simulador se desarrollará
en FASE 6. La cuenta demo corresponde a FASE 7 y la ejecución real supervisada,
opcional y con autorización específica, a FASE 8.

## Entregas por incremento

| Incremento | Entrega | Condición de aceptación |
| --- | --- | --- |
| **5.2.1. Contratos y persistencia** | Conversaciones, mensajes, revisiones de propuesta y trabajos con identificadores estables; almacenamiento local y referencias verificables | Una sesión se guarda y recupera tras reiniciar, conservando orden, revisiones, consumo y errores; pruebas con proveedor artificial |
| **5.2.2. Conversación local** | Pantalla nueva, envío explícito, historial, estado del trabajo y adaptador conversacional del proveedor local | Cada envío aceptado tiene identidad propia; duplicados o recargas no repiten inferencias; las pantallas de consulta siguen respondiendo mientras el modelo trabaja |
| **5.2.3. Propuestas de estrategia** | Preguntas para resolver ambigüedades y ficha estructurada con reglas, parámetros, datos y condiciones de ejecución | Una propuesta incompleta o incompatible no puede ejecutarse; las sugerencias del modelo se distinguen de los requisitos confirmados |
| **5.2.4. Prueba histórica controlada** | Preparación y ejecución explícita de una revisión mediante los controles del motor existente | La solicitud identifica revisión, datos, alcance y presupuesto; no permite reabrir intentos, permisos o reformulaciones consumidos |
| **5.2.5. Explicación y memoria** | Discusión de resultados con enlaces a sus evidencias; recuperación del contexto de la sesión | Cada cifra citada puede contrastarse con su resultado original; datos ausentes o inconclusos siguen visibles como tales |
| **5.2.6. Verificación y cierre** | Pruebas de integración, revisión de interfaz, medidas de respuesta y guía de uso | Recorrido completo comprobado, incluidos fallos y reinicios, sin duplicar trabajos ni degradar la consulta de FASE 5.1 |

La secuencia comienza por contratos y pruebas artificiales. El primer hito usable
será conversar y recuperar el historial; la ejecución de experimentos llegará en
5.2.4, después de comprobar propuestas y permisos.

## Propuesta y estados del trabajo

La ficha de estrategia recogerá al menos:

- Identidad y revisión, origen de cada decisión y mensajes que la justifican.
- Instrumento, fuente, temporalidad, período y particiones aplicables.
- Tipo de estrategia, parámetros y reglas explícitas de entrada y salida.
- Dirección permitida, tamaño, capital, moneda, costes y política de ejecución.
- Campos pendientes, incompatibilidades y límites de interpretación.
- Alcance de la prueba, consumo previsto, permisos aplicables y resultados enlazados.

Las revisiones se conservan como registros inmutables: incompleta, sugerencia del
modelo pendiente de revisión o lista para revisión. La aprobación para una prueba
queda en el trabajo asociado a su huella; la existencia de otra revisión determina
cuál fue sustituida. Una aprobación no se extiende a futuras variantes u operaciones.

Los trabajos distinguirán **en cola**, **en ejecución**, **completado**, **fallido**,
**cancelado** y **estado por resolver**. Un reinicio o una respuesta perdida no
autoriza a reenviar automáticamente una petición al modelo o al motor. Cancelar
no borra consumo ya producido ni recupera intentos consumidos; la interfaz
distinguirá solicitud de cancelación y cancelación efectiva.

## Integración con el motor y control del consumo

El investigador actual admite una pregunta inicial por CLI, pero invocarlo inicia
investigación y cálculos. No se usará como sustituto de una conversación inocua.
El ciclo de campañas tiene además un esquema y límites propios: se conservarán
sus contratos y evidencias, sin ampliar su esquema sellado para aceptar mensajes
libres ni eludir sus permisos desde la web.

Se creará un adaptador conversacional con contrato versionado. Antes de cada
inferencia comprobará disponibilidad del proveedor y capacidad del contexto;
antes de cada prueba verificará compatibilidad y los controles del ejecutor
correspondiente. La conversación no concede acceso a evaluaciones o herramientas
que ese ejecutor tenga bloqueadas.

Los límites de mensajes, tokens, contexto, tiempo y trabajos se fijarán antes de
habilitar el recorrido y serán visibles. Las reservas se harán antes de ejecutar;
el consumo conocido, errores y consumo desconocido se conservarán. Abrir otra
conversación o copiar una propuesta no reiniciará los límites de una campaña.
No habrá reintentos, truncados ni aumentos de presupuesto silenciosos.

El historial completo se conservará, pero el modelo recibirá únicamente el contexto
seleccionado y permitido. Esta entrega utiliza selección explícita de mensajes y
rechaza el exceso de contexto; no genera resúmenes automáticos para ampliar capacidad.
Se indica qué contexto se ha incluido y qué falta. Los resultados elegidos aportan datos verificables; el
texto guardado no podrá convertirse en instrucciones para saltarse controles.

Las credenciales y los archivos ajenos a las fuentes permitidas no se enviarán al
modelo. Las referencias se resolverán mediante identificadores y rutas controladas,
sin permitir lecturas arbitrarias solicitadas por el usuario o por una respuesta.

## Interfaz, concurrencia y recuperación

- Separar consultas de acciones: abrir, refrescar o sondear una pantalla no crea
  inferencias, experimentos ni reservas.
- Ejecutar trabajos largos fuera de los manejadores de consulta HTTP, mediante
  una cola limitada y un trabajador del proveedor. Inicialmente, una inferencia
  local activa a la vez y un trabajo activo por conversación.
- Persistir identidad y estado antes de entregar un trabajo al ejecutor. Repetir
  la misma solicitud devolverá su estado, sin duplicar efectos.
- Conservar acceso local, validación de Host/Origin y las protecciones existentes;
  añadir autenticación de las acciones de la sesión, protección frente a peticiones
  cruzadas y límites de tamaño antes de habilitar rutas que escriban o ejecuten.
- Mostrar esperas, errores, cancelaciones y capacidad agotada. El tiempo de respuesta
  del modelo dependerá del equipo; no se prometerá la latencia de una consulta web.
- Mantener las lecturas y cachés de FASE 5.1. Verificar con el modelo ocupado que
  las consultas calientes de Inicio, catálogo y Consumo mantienen un p95 inferior
  a 500 ms en el entorno de referencia, documentando muestra y condiciones.

## Comprobaciones y condiciones de cierre

Las pruebas utilizarán primero un proveedor artificial y datos pequeños conocidos.
Cubrirán persistencia, propuestas ambiguas o incompatibles, límites de contexto,
rechazos, doble envío, recarga, cancelación, reinicio y resultados incompletos.
También comprobarán que consultas HTTP no llaman al modelo, que cambiar de sesión
no reabre presupuestos y que mensajes o rutas manipulados no eluden validaciones.

La revisión de interfaz comprobará el recorrido completo y la respuesta de las
cinco pantallas actuales durante trabajos largos. Una prueba local con el modelo
real será acotada, con presupuesto registrado y evidencias separadas de las pruebas
artificiales. Las comprobaciones desde Codex respetarán los temporales exclusivos
y la caché desactivada de AGENTS.md.

La fase se cerrará cuando se pueda **conversar → revisar una propuesta → solicitar
una prueba histórica permitida → consultar y explicar su resultado → retomar la
conversación tras reiniciar**, con consumo y procedencia trazables. No bastará con
mostrar una interfaz de chat o generar texto sin un vínculo verificable al motor.

El registro de desarrollo y la guía recogen la entrega; PROJECT_STATUS se actualiza
al cerrar la fase. La creación inicial del plan fue documental. El desarrollo
posterior conserva las evidencias anteriores y permanece sin commit ni push nuevos.

Referencias: [proveedor local](LOCAL_AI.md), [interfaz actual](LAB_INTERFACE.md),
[siguientes fases](NEXT_PHASES.md) y [plan de TradingView](TRADINGVIEW_PLAN.md).
