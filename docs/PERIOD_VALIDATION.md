# Validación retrospectiva por períodos

22/10/2026. Siguiente incremento de FASE 6: ampliar los datos y contrastar la misma
estrategia en otro año. No inicia FASE 7 ni cierra la integración de TradingView.

## Protocolo fijado

Antes de descargar 2024 se conserva
[`protocol.json`](../reports/phase6-period-validation-2026-10-22/protocol.json):
SMA 20/60, largos, capital hipotético de 1.000 USD por período, cantidad fija de
1 EUR y comisión proporcional supuesta de 0,001 por ejecución. Se mantienen las
reglas anteriores de sesiones UTC, compra ASK, venta y valoración BID, ejecución
en la siguiente apertura observada y ausencia de cierre final forzado.

El período adicional es **01/01/2024–24/12/2024**, con fin exclusivo 25/12, usando
los mismos límites del calendario que el período ya calculado de 2025. Cada año
empieza sin posición y sin medias heredadas. No se concatenan saldos ni se eligen
parámetros o fechas según el resultado. Si falla la calidad, se conserva el bloqueo.

2024 es anterior a la prueba conocida de 2025. Esta repetición es retrospectiva:
no constituye una comprobación prospectiva ni acredita una muestra futura intacta.

## Resultado comprobado

Se obtiene el archivo anual EUR/USD H1 de 2024 del
[catálogo de EV Trading Labs](https://evtradelabs.com/data), con atribución conservada.
Su SHA-256 es `66fa719d8e7d75c11e1c691b232471fe3c9323e91ed998e8b82fe943f85d38b2`.
Contiene 6.247 velas y 314 fechas UTC observadas. El período fijado contiene 6.144
velas y 308 sesiones, sin huecos internos o de cobertura según la política vigente;
103 velas quedan fuera del período y se conservan en el original.

El archivo anual completo presenta dos huecos internos el 25/12: 04:00–05:00 y
08:00–22:00 UTC. Su prueba se bloquea sin métricas. No se cambia esta política para
publicar un resultado anual ni se certifica un calendario de mercado.

| Período, hasta el 24/12 | Sesiones | Ejecuciones | Operaciones cerradas | Posición final EUR | Patrimonio final USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2024 | 308 | 6 | 3 | 0 | 999,96832951 |
| 2025 | 307 | 3 | 1 | 1 | 999,98870447 |

Las cifras parten de 1.000 USD y una exposición fija de solo 1 EUR. Ambos resultados
son negativos bajo la comisión supuesta. Hay muy pocas operaciones para concluir
que la estrategia es robusta. Una reconstrucción independiente desde los gzip,
sin importar módulos del proyecto, reproduce medias, señales, ejecuciones, caja,
posiciones, comisiones, spread y cada punto de patrimonio y drawdown de ambos años.

## Comparación desde TiresIAs

En **Simulación y TradingView → Comparar períodos independientes**, seleccionar
dos resultados guardados y pulsar **Guardar comparación de períodos**.

Se exige la misma configuración completa, procedencia declarada, mercado, política
de sesiones y versión del motor. Los períodos deben ser distintos y no solaparse.
Se guardan copias exactas de ambos resultados y de sus entradas diarias e inventarios.
La ficha comprueba esas copias y reconstruye la tabla desde los resultados, sin
volver a ejecutar la estrategia. Si un período está bloqueado o es insuficiente,
la comparación queda incompleta y conserva su estado sin inventar métricas.

El listado solo consulta metadatos acotados; abrir la ficha verifica sus entradas.
Las huellas detectan cambios, pero no certifican la autenticidad del proveedor ni
demuestran por sí solas la corrección económica de un cálculo. La comprobación
aritmética independiente se conserva como evidencia separada.

Los originales completos de 2024 y 2025 ya están disponibles localmente. Esto no
significa que dos años completos hayan superado los controles de calidad. No se
han cambiado el motor de señales, Pine, contratos ni cuentas virtuales.

## Verificación y trabajo pendiente

363 pruebas seleccionadas aprobadas: 24 de comparación y las 339 seleccionadas
anteriores. Se comprueban origen/token HTTP, configuraciones distintas,
solapamientos, versiones del motor, calidad bloqueada, copias modificadas y ausencia
de ejecuciones o procesamiento contable durante las consultas. No se ejecuta toda
la colección. Se comprueba también sintaxis JavaScript y el recorrido del botón
de comparación en navegador con los dos períodos reales.

El incremento posterior ya incorpora una [referencia simple y sensibilidad a
comisiones](REFERENCE_COSTS.md), manteniendo períodos y parámetros. El
[chat ya utiliza los nuevos históricos](CHAT_PRICES.md) para pruebas revisadas. El contraste externo de
Pine y el puente del chat a operaciones virtuales siguen pendientes de FASE 6.
No se habilita una demo externa ni se realiza commit o push.

Evidencia: [informe y archivos](../reports/phase6-period-validation-2026-10-22/README.md).
