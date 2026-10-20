# Integración futura con TradingView

Decisión del usuario: **19 de octubre de 2026**. Estado: requisitos acordados;
la conexión, las consultas y el registro de operaciones externas están pendientes
de implementación. Este plan complementa el cierre histórico de FASE 2.

## Objetivos acordados

1. Ejecutar estrategias Pine Script sobre gráficos de TradingView, simular sus
   operaciones y consultar información actualizada de señales, operaciones y resultados.
2. Usar esa información para que TiresIAs registre compras, ventas, posiciones,
   costes y capital virtual en su propio simulador.

Los dos objetivos forman una integración conjunta. El emulador de estrategias
de TradingView y la cuenta virtual de nuestra aplicación tendrán registros
identificables y conciliables; no se presupone que compartan una cuenta.

## Flujo previsto

```text
Estrategia y parámetros versionados en TiresIAs
    → Pine Script instalado en un gráfico de TradingView
    → operaciones del emulador y resultados de la estrategia
    → alertas por webhook para novedades / exportaciones para históricos
    → recepción y validación de eventos en TiresIAs
    → registro de compras, ventas y capital virtual
    → consultas del estado actualizado y conciliación entre ambos sistemas
```

### Probar y consultar dentro de TradingView

- Generar inicialmente las estrategias SMA/EMA en Pine Script v6, con parámetros
  explícitos, identificador y versión. Probarlas en el gráfico y Strategy Report.
- Asociar cada ejecución a símbolo y proveedor del gráfico, temporalidad, zona
  horaria, periodo de prueba, código y parámetros, capital, tamaño y costes.
- Contrastar Python y Pine sobre los mismos datos y reglas: semilla EMA,
  calentamiento, confirmación de velas, momento de ejecución y posiciones abiertas.
  No exigir coincidencia con el BCE cuando cambien precios, proveedor o calendario.
- Consultar señales recientes, entradas/salidas simuladas y métricas disponibles.
  Cada consulta indicará fuente, última actualización, fecha de mercado y posibles
  retrasos. La información almacenada no se presentará como una cotización actual.
- Recibir novedades mediante alertas. Incorporar operaciones y métricas históricas
  mediante las exportaciones disponibles de Strategy Report, conservando el archivo
  original y su procedencia. Validar el formato real antes de crear el importador.
- Verificar qué consultas y automatizaciones ofrecen las herramientas oficiales
  en el momento de integrar. No asumir una API pública para subir scripts, modificar
  alertas, descargar cualquier gráfico o consultar continuamente toda la cuenta.
  Cuando sea necesario, el usuario instalará el script, creará las alertas y exportará
  los informes; la aplicación distinguirá estas tareas de las automatizadas.
- Al cambiar código, entradas o gráfico, verificar y recrear las alertas necesarias;
  registrar la versión de configuración que origina cada evento.

### Registrar la simulación en TiresIAs

- Añadir un modo específico de simulación alimentado por TradingView y separado
  del backtest BCE. Mantener cuentas virtuales independientes por experimento y moneda.
- Recibir webhooks HTTPS y normalizar sus mensajes. La recepción registrará primero
  el evento de forma duradera y procesará después la contabilidad.
- Registrar un identificador único, tipo de evento, experimento, versión de estrategia,
  símbolo/proveedor, temporalidad, instante de la señal y de la ejecución simulada,
  recepción, acción, precio, cantidad y moneda cuando estén disponibles.
- Distinguir una **señal** de una **ejecución del emulador**. Para reflejar operaciones
  de TradingView, usar sus eventos de ejecución simulada. No volver a aplicar el
  retraso de una observación a una operación ya ejecutada. Las señales que se ejecuten
  con nuestro propio modelo tendrán una política y un registro separados.
- El simulador local conservará sus límites de saldo, tamaño y costes. Registrar
  rechazos o diferencias frente a TradingView y mostrarlos en la conciliación;
  no sustituir su capital por una cifra recibida ni duplicar costes incluidos.
- Actualizar efectivo, posición, capital valorado, resultados realizados/latentes y
  drawdown. Registrar la antigüedad del último precio: un evento de compra aislado
  no permite valorar continuamente una posición sin recibir más referencias.
- Evitar operaciones duplicadas entre webhooks repetidos e importaciones históricas.
  Identificar duplicados por experimento y evento/orden; conservar el original.
- Detectar eventos atrasados, fuera de orden o de configuraciones desconocidas.
  Conservar los casos pendientes para conciliación, sin inventar ejecuciones perdidas.
- Permitir consultar historial, saldo y posiciones, actualización de datos,
  estado de recepción y discrepancias respecto a los informes de TradingView.

## Entrega progresiva

| Etapa | Resultado esperado |
|---|---|
| FASE 3 — Agente investigador | Preparar propuestas y experimentos trazables; prever consultas con procedencia y fecha |
| FASE 4 — Validación | Verificar reglas, causalidad y equivalencia con datos comparables; conservar separación de desarrollo/prueba |
| FASE 5 — Interfaz | Mostrar resultados, procedencia, fecha de actualización y cuentas virtuales |
| FASE 6 — TradingView | Pine, pruebas en gráfico, consultas/importaciones, alertas y receptor de webhooks |
| Continuación de FASE 6 | Procesar eventos en el simulador interno y conciliar compras, ventas y capital virtual |
| FASE 7 — Cuenta demo externa | Añadir después un adaptador de bróker si procede; no es requisito para el simulador interno |

## Condiciones de aceptación

- Una estrategia versionada genera operaciones simuladas observables en un gráfico
  y un informe de TradingView, con sus parámetros y fuente identificados.
- Una operación comunicada produce un único asiento local; repetirla o importarla
  después no duplica compras, ventas ni costes.
- Compras y ventas conocidas producen saldos y capital verificables; las posiciones
  abiertas se valoran con referencias fechadas y los rechazos quedan explicados.
- Una consulta diferencia la hora de consulta de la última información recibida;
  si faltan datos o eventos se indica expresamente y se permite conciliar.
- Se comprueba recuperación ante duplicados, pérdidas, retrasos, cambios de versión
  y reinicios antes de considerar completa la integración.

## Capacidades verificadas y pendientes

TradingView permite simular con estrategias Pine sobre datos históricos y en
tiempo real mediante su emulador. Las estrategias Pine no colocan órdenes en la
cuenta Paper Trading integrada; utilizaremos el emulador y nuestra propia cuenta
virtual. [Documentación oficial de estrategias](https://www.tradingview.com/pine-script-docs/faq/strategies/).

Los webhooks notifican alertas a una aplicación externa mediante POST. Requieren
2FA y pueden fallar; el receptor debe responder dentro del plazo documentado.
Antes de desplegar se verificarán el plan de TradingView, los permisos y la
disponibilidad de datos necesarios. Se usará un receptor autenticado, con validación
de mensajes y sin credenciales del bróker en el contenido.
[Webhooks oficiales](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/).

Las alertas de estrategia pueden representar ejecuciones del emulador. Una alerta
usa una copia de su script/configuración; modificar el gráfico no actualiza por
sí solo una alerta ya creada. [Alertas Pine](https://www.tradingview.com/pine-script-docs/concepts/alerts/).

Las pestañas de operaciones y métricas de Strategy Report se exportan por separado.
Una exportación no proporciona por sí sola actualizaciones continuas.
[Exportación oficial de estrategias](https://www.tradingview.com/support/solutions/43000613680-how-to-export-strategy-data/).

Revisar estas capacidades al implementar. Este acuerdo incorpora simulación y
conexiones de información; la ejecución con dinero real sigue fuera de este alcance.
