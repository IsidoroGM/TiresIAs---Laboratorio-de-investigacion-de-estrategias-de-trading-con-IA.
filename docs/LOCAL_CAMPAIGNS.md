# Campañas locales de investigación

Una campaña agrupa un número limitado de ideas con los mismos datos, objetivo y
controles. Su finalidad es registrar lo probado y lo descartado para poder
compararlo. Completar una campaña no demuestra que una estrategia sea mejor.

## Primer paso implementado: plan sin activación

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_plan prepare --guided-run <peticion-guiada> --max-proposals 3 --max-backtests 6
.\.venv\Scripts\python.exe -m trading_ai.campaign_plan verify --run <plan-campana>
```

Los dos límites son obligatorios. Se admiten entre una y tres propuestas y
0, 2, 4 o 6 backtests, con un máximo de dos por propuesta: base y candidata.
Con cero backtests se puede planificar únicamente investigación de ideas.
Se rechazan valores booleanos, fraccionarios y campos adicionales.

El comando crea `campaign.json`, su huella, `limits.json`, una copia exacta de
`request.json` y `events.jsonl` en una carpeta nueva de `.local/campaign-plans`.
Comprueba fuentes antes y después de prepararlo. La verificación vuelve a
contrastar fuentes, presupuesto heredado, límites, historial y código.

**Es un plan, no un presupuesto activado.** El estado es
`planned_not_activated`; las reservas y capacidades ejecutables son cero.
No hay comandos de activación, generación o ejecución. La herramienta no llama
al modelo, reserva intentos, calcula señales o ejecuta simulaciones.

Preparar varios planes o cambiar sus límites no concede consultas nuevas. La
identidad de ámbito depende de los bytes de desarrollo y del par, sin rutas,
límites, criterio o capital. Ya existe un [registro contable compartido](CAMPAIGN_LEDGER.md)
de ese ámbito, con reservas exclusivas y sin activación. El presupuesto compacto anterior
se conserva tal como estaba, incluido un intento ya consumido.

## Memoria y procedencia

Se copian íntegramente controles, objetivo, datos, historial estructurado,
intentos compactos, identidades consumidas y cobertura de reglas. Los motivos
de revisión permanecen como declaraciones no verificadas del revisor. No se
completa el texto del modelo ni se convierten descartes en candidatas aceptadas.

El consumo heredado corresponde al ámbito compacto capturado; no se presenta
como consumo de toda la aplicación. Un valor desconocido permanece desconocido.
`new_usage` es cero para esta preparación y verificación. Los límites solicitados
no son consumo ni permisos concedidos.

La petición guiada se conserva sin añadir el manifiesto de campaña al mensaje.
Su límite sigue en 12.288 bytes; no hay recuento previo de tokens ni garantía de
encaje. El plan no resuelve la posible falta de espacio para futuras entradas.

## Contrato del ejecutor futuro

Antes de ejecutar faltan un permiso de campaña explícito y el controlador que
utilice el registro compartido sin reiniciar los contadores históricos. Cada consulta
reservada, incluso fallida o duplicada, consumirá un intento. No habrá reintentos
automáticos, reformulaciones de linajes consumidos o diagnósticos adicionales
fuera de los límites registrados.

El flujo previsto separa propuesta, revisión aceptada, plan verificado, cálculo
con el motor y análisis de Python. Cada nueva petición requerirá memoria completa
y vigente. Los resultados negativos e inconclusos se conservarán; no habrá
adopción automática. Consumo desconocido, contexto insuficiente o cambios de
fuentes, controles, código o identidad del proveedor detendrán el flujo.

El proveedor previsto continúa siendo Ollama local en CPU, con la versión ya
comprobada 0.40.6, contexto máximo de 4.096 tokens y salida máxima de 384. Este
plan no configura o consulta un proveedor ni habilita OpenAI. No hay conexión
con TradingView o bróker. El histórico sigue siendo desarrollo conocido, con
evaluación exterior desactivada y sin afirmar validación inédita.

Este paso pertenece a la FASE 4, que permanece abierta. La
[comprobación local](../reports/phase4-campaign-plan-2026-10-20.md) conserva un
plan inactivo y las evidencias de que los presupuestos anteriores no cambiaron.

Las [capturas de intentos](CAMPAIGN_ATTEMPTS.md) conservan ahora respuestas,
errores y consumo por reserva, manteniendo separados registro y ejecución.
