# Próximas fases de TiresIAs

21/10/2026. Punto de partida: FASES 0 a 5, 5.1 y 5.2 completadas. La interfaz
cerró FASE 5 con 1598 pruebas aprobadas; FASE 5.1 añade 29 casos y comprueba 128
pruebas específicas de interfaz, evidencias y registro. Este documento define el
trabajo pendiente; FASE 6 está en desarrollo y las fases 7 y 8 no se han iniciado. FASE 5.2 comprueba 267
pruebas de los componentes afectados, con 46 nuevas; no se ejecutó toda la colección de 1673.

La **FASE 5.1 — Rendimiento y fluidez de la interfaz** queda completada antes de
FASE 6: índice en memoria con frescura visible, lecturas por petición, cancelación,
concurrencia limitada y caché condicional de estáticos. El
[informe de cierre](../reports/phase5-1-completion-2026-10-21.md) conserva medidas y
límites; la primera carga sigue preparando el índice y las fichas verifican bytes.

La secuencia mantiene el [plan acordado de TradingView](TRADINGVIEW_PLAN.md).
Completar software de integración no equivale a validar la rentabilidad de una
estrategia. Los datos ya explorados siguen siendo históricos conocidos.

## FASE 5.2 — Conversación con el agente

**Objetivo:** conversar dentro de TiresIAs para concretar una estrategia, revisar
una propuesta estructurada, solicitar una prueba histórica controlada y discutir
sus resultados con referencias a las evidencias. Se incorpora antes de FASE 6.

El [plan de FASE 5.2](PHASE5_2_PLAN.md) define seis incrementos: contratos y
persistencia; conversación local; propuestas de estrategia; ejecución histórica
explícita; explicación y memoria; verificación y cierre. Se añade la pantalla de
conversación, conservando las cinco pantallas de consulta y su fluidez.

El proveedor es el local ya configurado. Mensajes y trabajos tienen límites y
consumo visibles. La conversación no puede reabrir presupuestos o permisos del
motor, ni convertir una respuesta del modelo en una ejecución automática.

**Cierre de FASE 5.2:** recorrido comprobado desde una conversación hasta una
propuesta revisada, una prueba histórica permitida y su explicación verificable;
historial y estados recuperables, sin duplicados. Las compras y ventas concretas
en el simulador se incorporarán mediante el puente previsto en FASE 6.
El [informe de cierre](../reports/phase5-2-completion-2026-10-21.md) conserva el
ensayo real y sus fallos; la fiabilidad semántica general del modelo no se da por demostrada.

## FASE 6 — TradingView y simulador virtual conectado

**Objetivo:** probar estrategias versionadas en TradingView, consultar sus
resultados e incorporar operaciones simuladas a una cuenta virtual trazable de
TiresIAs. No incluye órdenes a un bróker o dinero real.

**Avance local 21/10/2026:** contratos, generador Pine, referencia OHLC, lector CSV
con mapa explícito, inbox duradero, receptor autenticado loopback y contabilidad
virtual con consulta y acciones revisadas en la interfaz. La [guía local](TRADINGVIEW_LOCAL.md)
describe comandos y límites. No se ha compilado Pine, comprobado equivalencia con
un gráfico ni validado una exportación real; tampoco se ha conectado TradingView
o implementado el puente de operaciones desde el chat. Estos incrementos no
constituyen el cierre de FASE 6.

**Avance de datos y validación 22/10/2026:** importación de precios H1 BID/ASK,
archivos anuales de 2024 y 2025 preservados y cálculo retrospectivo con spread
sobre períodos explícitos hasta el 24/12. Se repite SMA 20/60 con parámetros fijos
y se añade comparación de períodos independientes en la interfaz. Los años
completos quedan bloqueados por huecos internos del 25/12. La
[guía de validación](PERIOD_VALIDATION.md) documenta los resultados negativos y
sus límites; no sustituye el contraste externo de Pine ni completa FASE 6.
Se añade una [comparación con referencias y comisiones](REFERENCE_COSTS.md):
efectivo sin intereses y comprar/mantener con cantidad fija tras el calentamiento,
bajo cuatro tasas supuestas predeterminadas. SMA queda por debajo del efectivo
en ambos períodos incluso sin comisión. El [chat con precios](CHAT_PRICES.md) ya
conecta propuestas SMA con los nuevos históricos mediante revisión y aprobación
explícitas, manteniendo el presupuesto compartido con BCE. El contraste externo
de FASE 6 sigue pendiente. El modo manual posterior se describe abajo.

| Incremento | Entrega | Comprobación de aceptación |
| --- | --- | --- |
| 6.1. Contratos y estrategias | Identidad/versiones de estrategia, parámetros, fuente, símbolo, temporalidad, fechas, costes y cuenta; primeras estrategias SMA/EMA en Pine según el plan acordado | Cada resultado identifica exactamente qué configuración y datos lo originaron |
| 6.2. Contraste con Python | Casos pequeños conocidos y comparación con datos equivalentes: semilla, calentamiento, señales, ejecución y posiciones abiertas | Diferencias explicadas; no se exige igualdad entre precios de proveedores distintos o con las referencias del BCE |
| 6.3. Importación de históricos | Lector de exportaciones reales de operaciones y métricas, con archivo original, huella, validación y errores visibles | Importar dos veces el mismo archivo/evento no duplica operaciones ni costes |
| 6.4. Recepción de novedades | Alertas y receptor de webhooks autenticado, con validación, registro duradero y procesamiento separado | Duplicados, retrasos, orden incorrecto, reinicios y mensajes incompatibles se detectan sin inventar ejecuciones |
| 6.5. Contabilidad y conciliación | Compras, ventas, cantidades, posiciones, costes y capital virtual desde eventos simulados; consulta en la interfaz | La cuenta interna y el informe externo pueden conciliarse, con diferencias y antigüedad de datos explícitas |
| 6.6. Operaciones simuladas desde conversación | Convertir una petición del chat de FASE 5.2 en una intención estructurada para el simulador, con modo, cuenta, instrumento, acción, cantidad y condiciones | Revisión y autorización explícitas, controles de saldo y riesgo independientes del modelo y registro único; pedir o proponer una operación no equivale a ejecutarla |

Las cuentas del emulador y las de TiresIAs se identifican por separado. Un evento
de ejecución ya producido no vuelve a recibir el retraso de una observación del
backtest BCE. Una señal sin ejecución no se convierte automáticamente en compra.
El simulador conserva sus controles de saldo, costes y tamaño; no reemplaza su
capital por una cifra recibida. Las cuentas y monedas independientes no se suman.

Primero se construirán y probarán los contratos y lectores con ejemplos
artificiales. Antes de conectar un servicio externo se comprobarán sus capacidades
oficiales vigentes, el acceso del usuario, sus datos y cualquier coste. El usuario
realizará los pasos manuales de cuenta, instalación de scripts o configuración de
alertas que correspondan. No se presupone una API para automatizar toda la cuenta.

**Cierre de FASE 6:** una estrategia versionada tiene una simulación identificable;
sus históricos y novedades pueden registrarse una sola vez en TiresIAs; compras,
ventas, posición y capital son conciliables; la interfaz muestra origen, fechas,
datos ausentes y errores. Se prueba recuperación tras fallos sin duplicar asientos.
La petición de una operación por conversación pasa por revisión y los controles
del simulador, con su resultado confirmado enlazado a la conversación.
Abrir o refrescar una pantalla sigue siendo una consulta sin ejecuciones nuevas.

## FASE 7 — Cuenta demo externa

**Objetivo:** comprobar un adaptador de bróker en una cuenta demo elegida por el
usuario, contrastando eventos externos con la contabilidad interna. Es posterior
a la simulación interna de FASE 6 y no es necesaria para completarla.

Trabajo previsto:

1. Elegir proveedor, cuenta y datos; confirmar permisos, condiciones y posibles
   costes antes de leer credenciales o habilitar conexiones.
2. Definir el adaptador y probarlo sin cuenta conectada: órdenes, identificadores,
   respuestas, rechazos, ejecuciones parciales y desconexiones.
3. Conectar explícitamente la demo y registrar su estado real, sin considerar una
   petición enviada como una ejecución confirmada.
4. Incorporar límites independientes de la IA: saldo, tamaño, exposición, frecuencia
   y pérdidas permitidas según controles acordados. Incluir pausa y bloqueo ante
   datos obsoletos, estados desconocidos o discrepancias.
5. Conciliar órdenes, operaciones, costes, saldo y posiciones; comprobar reinicios,
   repetición de mensajes y recuperación sin duplicados.
6. Realizar una comprobación prospectiva con reglas fijadas previamente, conservando
   también pérdidas, rechazos y diferencias respecto a la simulación histórica.

**Cierre de FASE 7:** funcionamiento demo trazable y recuperable, controles de riesgo
comprobados, conciliación y errores visibles. Un resultado favorable en demo no
autoriza pasar automáticamente a dinero real ni demuestra rentabilidad futura.

## FASE 8 — Ejecución real supervisada, opcional

**Objetivo:** solo si el usuario decide solicitarlo después de revisar las fases
anteriores, preparar una operativa real con controles humanos y límites explícitos.
No es una continuación automática de la demo.

Antes de cualquier habilitación deberán definirse y comprobarse:

- Autorización nueva y específica, cuenta, alcance, capital y límites establecidos
  por el usuario; credenciales protegidas y separadas de Git y del modelo.
- Revisión de los resultados prospectivos y de las diferencias entre simulación,
  demo y ejecución real: costes, precios, tamaños, liquidez y restricciones del proveedor.
- Motor de riesgo independiente del LLM y aprobación humana de la operativa real;
  el modelo no podrá aumentar límites o concederse permisos.
- Pausa inmediata, cancelación, bloqueo ante estados desconocidos, seguimiento de
  posiciones, conciliación y procedimiento de recuperación y cierre.
- Registro duradero de decisiones, aprobaciones, eventos, costes, errores y consumo.

**Cierre de preparación de FASE 8:** controles y procedimientos revisados y probados,
con una decisión humana explícita sobre cualquier operativa. No se fija aquí una
cantidad a invertir, un objetivo de beneficio ni una fecha para operar.

## Reglas comunes de entrega

- Avanzar por incrementos pequeños y verificables, conservando las evidencias y
  versiones anteriores. No reabrir presupuestos o reformulaciones consumidas.
- Mantener separados investigación, cálculos, permisos, contabilidad y consulta.
  Un texto del modelo no será código ejecutable ni una aprobación de operaciones.
- Mostrar fuente, fecha, moneda, cuenta y límites de cada resultado. Datos ausentes,
  consumo desconocido y discrepancias no se sustituyen por valores inventados.
- Verificar con datos artificiales y pruebas de integración antes de conectar
  servicios. En Windows, respetar los temporales exclusivos y la caché desactivada
  de AGENTS.md para pruebas desde la sesión aislada.
- Registrar avances en DEVELOPMENT_LOG y actualizar PROJECT_STATUS únicamente al
  completar una fase. Las dependencias, gastos y conexiones nuevas requieren el
  alcance autorizado correspondiente.

Las explicaciones nuevas con resultados adjuntos ya usan un contrato estructurado:
el modelo selecciona aspectos y Python compone el texto con criterio y evaluación
comprobados. Se conserva el comentario incorrecto anterior y no se recalculan sus
estrategias. La elección de aspectos por el modelo sigue pudiendo ser incompleta;
este incremento no acredita razonamiento libre fiable.

El primer recorrido de 6.6 ya admite peticiones manuales limitadas a comprar/vender
EUR/USD, cuentas independientes y precios BID/ASK aportados, con revisión, aprobación
concreta, controles del simulador y asiento atómico. No interpreta operaciones libres
mediante el LLM ni obtiene precios automáticamente. Se conserva separado de los fills
de estrategia y del inbox externo; no completa el contraste externo pendiente.

Las cuentas manuales también permiten revisar y registrar otra valoración BID/ASK
sin comprar ni vender, con antigüedad, resultado no realizado y riesgo visibles.
Los cambios invalidan intenciones revisadas con un estado anterior. Las cotizaciones
siguen aportadas por el usuario y sin comprobación automática de mercado.

El siguiente desarrollo de FASE 6 debe completar el contraste externo de Pine y
datos equivalentes, adaptar una exportación real conservando sus originales y
ampliar el modo manual del chat si se acuerdan otras reglas o una fuente de cotizaciones.
La conexión HTTPS de alertas se habilitará únicamente tras revisar capacidades,
cuenta y configuración. FASE 5.2 está completada localmente; FASE 6 permanece abierta.

Ya existe un comparador genérico de CSV de ejecuciones frente a resultados BID/ASK
guardados: mapa y origen explícitos, vista previa, diferencias y archivo de
originales sin efectos contables. El ensayo de interfaz usa un ejemplo artificial;
no acredita equivalencia externa. El usuario elige JForex/Dukascopy como siguiente
fuente. El próximo paso es obtener un informe HTML original del tester con sus
ajustes, adaptar su detalle real y contrastar reglas y ejecuciones. La
[guía del comparador](EXECUTION_COMPARISON.md) describe el contrato y lo pendiente.

La [preparación de JForex](JFOREX_SETUP.md) identifica una incompatibilidad de
tamaño: la referencia Python usa 1 EUR y la API documenta un mínimo de 1.000.
Se calcula un caso escalado independiente, conservando el anterior. Tras preparar
la descarga oficial firmada, el usuario confirma instalación y demo. La estrategia
Java exclusiva TEST está implementada y compila contra su API 4.9.8;
30 casos offline comprueban guardas,
señales, unidades y exportaciones. Una referencia Python nueva usa las cantidades
escaladas con los mismos datos. Quedan pendientes compilar/ejecutar en el tester,
recibir su HTML y exportaciones, comprobar los precios y conciliar los resultados.
La [guía de la estrategia](../integrations/jforex/README.md) fija la primera prueba.

**Avance del 23/10/2026:** el ensayo nativo v2 ya completa la ventana con tres
ejecuciones; sesiones y señales coinciden, con diferencias temporales de +450 s.
La [conciliación nativa](JFOREX_RECONCILIATION.md) incorpora los originales al flujo
de la app, conserva su referencia y muestra cortes, swaps y comisiones discordantes.
La revisión v3 actual añade capturas de cuenta/órdenes al corte y corrige la
semántica del importe nativo frente a exposición abierta. El ensayo v3 posterior
ya está verificado y guardado: la API publica 999.989,14 USD al 25/12/2025 00:07:30
UTC y 999.988,68 USD al final, coincidente con el HTML. La primera captura llega
450 s después del corte, sin prueba de sincronización exacta. La app reconstruye
ambos instantes conservando diferencias y comisiones discordantes. No es necesario
repetir este ensayo para obtener las capturas que ya tenemos.

Siguiente incremento: tratar explícitamente las diferencias de ejecución respecto
a las aperturas Python y fijar el alcance de costes comparables, sin alterar los
resultados congelados ni repartir comisiones desconocidas. Después se podrá ampliar
el contraste a otro período y estrategia. La equivalencia completa y el cierre
de FASE 6 siguen pendientes.
