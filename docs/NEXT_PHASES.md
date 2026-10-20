# Próximas fases de TiresIAs

20/10/2026. Punto de partida: FASES 0 a 5 completadas. La interfaz local está
comprobada con 1598 pruebas aprobadas. Este documento define el trabajo pendiente;
no declara iniciada o completada ninguna fase posterior.

La secuencia mantiene el [plan acordado de TradingView](TRADINGVIEW_PLAN.md).
Completar software de integración no equivale a validar la rentabilidad de una
estrategia. Los datos ya explorados siguen siendo históricos conocidos.

## FASE 6 — TradingView y simulador virtual conectado

**Objetivo:** probar estrategias versionadas en TradingView, consultar sus
resultados e incorporar operaciones simuladas a una cuenta virtual trazable de
TiresIAs. No incluye órdenes a un bróker o dinero real.

| Incremento | Entrega | Comprobación de aceptación |
| --- | --- | --- |
| 6.1. Contratos y estrategias | Identidad/versiones de estrategia, parámetros, fuente, símbolo, temporalidad, fechas, costes y cuenta; primeras estrategias SMA/EMA en Pine según el plan acordado | Cada resultado identifica exactamente qué configuración y datos lo originaron |
| 6.2. Contraste con Python | Casos pequeños conocidos y comparación con datos equivalentes: semilla, calentamiento, señales, ejecución y posiciones abiertas | Diferencias explicadas; no se exige igualdad entre precios de proveedores distintos o con las referencias del BCE |
| 6.3. Importación de históricos | Lector de exportaciones reales de operaciones y métricas, con archivo original, huella, validación y errores visibles | Importar dos veces el mismo archivo/evento no duplica operaciones ni costes |
| 6.4. Recepción de novedades | Alertas y receptor de webhooks autenticado, con validación, registro duradero y procesamiento separado | Duplicados, retrasos, orden incorrecto, reinicios y mensajes incompatibles se detectan sin inventar ejecuciones |
| 6.5. Contabilidad y conciliación | Compras, ventas, cantidades, posiciones, costes y capital virtual desde eventos simulados; consulta en la interfaz | La cuenta interna y el informe externo pueden conciliarse, con diferencias y antigüedad de datos explícitas |

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

El siguiente trabajo de desarrollo, cuando se encargue, será **6.1: contratos de
intercambio y primeras estrategias Pine versionadas**. La FASE 6 sigue pendiente.
