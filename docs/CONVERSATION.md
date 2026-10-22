# Conversar con el agente — FASE 5.2

## Abrir y retomar una conversación

Tras actualizar el código, cierra el servidor anterior con Ctrl+C en su terminal,
vuelve a arrancarlo y recarga la página:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.lab
```

En [TiresIAs local](http://127.0.0.1:8765), entra en **Conversar con el agente**.
Crear y consultar conversaciones no genera respuestas. Para enviar mensajes,
arranca la instancia local y el modelo ya instalado:

```powershell
.\scripts\Start-LocalAI.ps1
```

El laboratorio no inicia Ollama ni descarga modelos automáticamente. Usa
`config/ai.local.json` si existe; por defecto, Qwen3.5:4b en `127.0.0.1:11435`, CPU,
contexto 4096 y salida hasta 384 tokens. Comprueba Ollama 0.40.6 y la huella del
modelo. OpenAI sigue desactivado. Una respuesta puede tardar decenas de segundos.

## Recorrido

1. Escribe un título y pulsa **Crear conversación**. El historial queda guardado
   y puedes retomarlo desde la lista.
2. Describe la idea y pulsa **Enviar al agente local**. Por ejemplo: «Quiero
   investigar un cruce EMA15/45, diario, para EUR/USD, con posiciones largas».
   Cada mensaje admite hasta 800 caracteres.
3. Elige qué contexto se envía: ningún mensaje anterior o los últimos dos, cuatro
   u ocho. Si supera la cota conservadora, se rechaza antes de llamar al modelo.
   El historial permanece completo; elige menos mensajes para continuar.
4. Revisa las preguntas y sugerencias. El modelo puede equivocarse: su texto no
   se ejecuta. La aplicación rechaza formatos incompatibles y contradicciones
   explícitas entre una hipótesis que nombra EMA/SMA y el tipo de sus parámetros.
5. En **Estrategia y prueba histórica**, revisa variante, base, ventanas, par,
   capital virtual, costes, tamaño, fechas y criterio. Los valores iniciales son
   ejemplos, no decisiones aceptadas. Puedes preparar la ficha a mano.
6. Confirma las reglas admitidas y pulsa **Guardar propuesta revisada**. Se guarda
   otra revisión y se conserva la anterior. Modificar el formulario exige guardar
   una nueva revisión antes de ejecutar.
7. Pulsa **Aprobar esta revisión y probar en histórico**. Aprueba solo esa revisión
   y reserva una comparación con dos backtests. No genera texto del modelo ni
   ejecuta operaciones en una cuenta conectada.
8. Abre **Prueba histórica → Ver métricas verificadas**. Las cifras vienen de
   Python. El enlace abre el experimento y sus evidencias; este formato conserva
   resúmenes de ambas cuentas, sin inventar curvas u operaciones detalladas.
9. Elige ese resultado como evidencia y envía otra pregunta. El modelo selecciona
   hasta tres aspectos de la explicación y devuelve el criterio y evaluación
   exactos. Python comprueba la respuesta y redacta los hechos a partir del
   resultado guardado. Las contradicciones no se publican como explicación;
   conservan original, error, consumo y reserva. No se reintentan automáticamente.
   Para proponer otra estrategia, selecciona **Sin resultado adjunto**.

La [explicación contrastada](CHAT_EXPLANATIONS.md) funciona con BCE y BID/ASK.
Las respuestas anteriores conservan su texto y su aviso de comentario sin
contraste estructurado. No se revisan retrospectivamente ni se presentan como
salidas del contrato nuevo.

## Reglas y datos admitidos

El recorrido BCE admite cruces SMA/EMA, largos, entrada alcista y salida bajista; ejecución en
la observación siguiente. Pares: EUR/USD, GBP/USD, USD/JPY y USD/CHF diarios,
con referencias educativas del BCE. Se usa la copia local de `data/README.md`,
sin permitir rutas libres. El período puede abarcar hasta diez años y debe tener
suficientes observaciones para las ventanas y la ejecución posterior.

FASE 6 añade la elección **Históricos BID/ASK · EUR/USD · SMA**. Permite revisar
ventanas SMA base/variante, elegir un histórico aportado, cantidad fija EUR y
comisión supuesta, guardar una revisión y aprobar una comparación independiente
del BCE. Los cuatro intentos de comparación se comparten entre ambas fuentes.
La [guía del chat con precios](CHAT_PRICES.md) describe reglas, ejecución y límites,
incluidos los errores observados en la explicación del modelo.

Capital, coste proporcional por ejecución y fracción de efectivo son supuestos
de una cuenta virtual. Dejar vacío el tamaño fraccionario utiliza una unidad base.
Los criterios comparan retorno y drawdown; ausencia de cierres o empate mantienen
el resultado inconcluso. Las fechas efectivas y la huella quedan guardadas.

El [modo manual de operaciones virtuales](MANUAL_OPERATIONS.md) ofrece otra ficha
en la misma conversación: petición limitada, cuenta manual y BID/ASK aportado,
revisión y aprobación separadas. No utiliza el envío al modelo ni el backtest.

Stop-loss, cortos y órdenes actuales quedan fuera del ejecutor histórico. Confirmar el
formulario declara que has revisado las reglas admitidas; no traduce reglas nuevas
en lenguaje libre. Pedir «compra ahora» en el mensaje general no crea una operación.

La exploración del chat tiene presupuesto propio y usa históricos conocidos.
No activa campañas ni acepta sus permisos como entrada; no reabre intentos ni
accede a evaluaciones bloqueadas. No demuestra validación independiente o rentabilidad.

## Consumo, cancelación y recuperación

El presupuesto inicial persistido es **24 intentos de respuesta y cuatro
comparaciones históricas** para todo el proyecto. Cada comparación reserva dos
cálculos. Otra conversación, otra redacción, ceros adicionales en un coste o
cambiar solo el criterio no permiten repetir cálculos ni reiniciar el presupuesto.
No borres el registro para simular un presupuesto nuevo.

Se admiten ocho trabajos activos/en cola, uno activo por conversación y una
inferencia de chat a la vez; hasta 100 conversaciones y 128 revisiones. No se
amplían límites ni se repiten inferencias automáticamente. Los trabajos conservan
el contexto elegido, los errores, la respuesta original y el consumo disponible.

Fallos y cancelaciones conservan su reserva. Tokens desconocidos no equivalen a
cero. Ollama tiene coste de API cero; no se estima electricidad. **Consumo** muestra
el chat separado de las fuentes anteriores.

**Solicitar cancelación** cancela un trabajo que no comenzó. Si ya está calculando
o generando texto, puede terminar antes de cancelarse: se conserva el resultado y
su consumo. Una recarga no vuelve a enviar un trabajo aceptado.

Un cierre abrupto marca trabajos pendientes o en ejecución como interrumpidos,
sin reenvío automático. Otra instancia puede consultar el historial, pero solo
un servidor posee el trabajador. Para actuar, utiliza esa instancia o cierra la
anterior y reinicia el laboratorio.

El historial vive en `.local/conversations/chat.sqlite3`; los resultados, en
`.local/chat-experiments/`. Están excluidos de Git. Guardar mensajes no entrena
el modelo. Solo se envían el contexto elegido y resultados de la misma conversación;
no se envían credenciales ni se leen archivos arbitrarios a petición del modelo.

Las cinco pantallas de consulta mantienen su funcionamiento. Abrirlas, refrescarlas
o filtrar no genera respuestas ni cálculos. Los trabajos largos se procesan fuera
de los manejadores HTTP de consulta.

Para reproducir la selección de pruebas de los componentes afectados:

```powershell
$codexPytestRun = Join-Path ([System.IO.Path]::GetTempPath()) ('trading-ai-codex-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp "$codexPytestRun" tests/test_conversation.py tests/test_conversation_prices.py tests/test_conversation_explanation.py
```

La selección usa un temporal GUID nuevo y caché desactivada, según AGENTS.md.
No inicia Ollama ni representa la ejecución de la colección completa.
