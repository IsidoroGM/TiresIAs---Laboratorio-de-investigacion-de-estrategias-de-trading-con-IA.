# Prueba local con spread e interfaz: avance de FASE 6

22/10/2026. La fase continúa abierta. Sin commit ni push.

Se añade un cálculo histórico independiente de Pine y de las cuentas virtuales.
Reconstruye las sesiones desde los BI5 originales, comprueba sus huellas y las
contrasta con `daily.json` antes de calcular. Conserva las entradas, resultado,
configuración y huellas de las fuentes ejecutables en un directorio nuevo.

La estrategia calcula SMA 20/60 sobre cierres BID de sesiones UTC observadas.
Compra a ASK y vende a BID en la primera apertura H1 observada de la siguiente
sesión. No inventa una ejecución a las 00:00 si el mercado observado abre después.
El spread está incorporado al precio y no vuelve a cargarse como comisión. Se
informa un diagnóstico respecto al punto medio, sin restarlo de nuevo al saldo.
La posición se valora a BID; no se fuerza la liquidación final ni se inventan
precios para una señal que queda pendiente al terminar el histórico.

El capital y la cantidad son hipotéticos, sin apalancamiento. La comisión
proporcional se declara como hipótesis, incluso si es cero. No se modelan swaps,
deslizamiento, liquidez, restricciones de bróker o movimientos intravela.
No hay equivalencia verificada con Pine/OANDA ni conexión a una cuenta.

## Interfaz y comprobación real

En **Simulación y TradingView** se incorpora **Precios Dukascopy y prueba con
spread**, con selección del histórico preparado, capital/cantidad hipotéticos,
comisión supuesta y una acción explícita para verificar y calcular. Conserva los
resultados y muestra operaciones, curva o el motivo por el que no puede calcular.
GET solo consulta resúmenes y resultados; no descarga ni inicia un backtest.
Se mantienen el origen y el token locales requeridos por los POST existentes.

Con los originales reales de enero de 2025 se verifican 27 sesiones. Faltan 34
para las 61 requeridas por el primer cruce SMA 20/60. El resultado queda en
`insufficient_history`, sin operaciones ni resumen de rentabilidad. Una comisión
de cero se usa solo como parámetro del diagnóstico; no se atribuye al proveedor.

La reanudación explícita 2024–2025 vuelve a recibir HTTP 429 y se detiene en la
primera petición. No se repite en bucle. Los dos años no están descargados.
La ruta original de enero termina en HTTP; se conserva esa limitación sin
atribuir autenticación del origen. La incidencia de acceso de la API actual
también aparece en el [informe público de dukascopy-node](https://github.com/Leo4815162342/dukascopy-node/issues/261).

## Verificación

Las pruebas artificiales comprueban la aritmética BID/ASK y de las comisiones,
ausencia de doble cargo del spread, valoración BID, rechazo por efectivo, señales
pendientes, causalidad, contexto Decimal, originales alterados y reproducción.
Se comprueban también acciones y consultas HTTP, rutas de catálogo, alteración de
resultados y copias de entrada, sin crear cuentas ni recepciones.

299 pruebas seleccionadas aprobadas: 34 nuevas de cálculo e integración, las 185
de la selección previa y 80 de laboratorio/rendimiento. No se ejecuta la colección
completa. Se comprueba además la sintaxis JavaScript y la interfaz en el navegador.
El caso artificial de 181 sesiones genera dos operaciones y un cierre; su curva
se muestra sin sustituir la muestra real ni incorporarse a su catálogo.

`tests.log` y `tests.xml` conservan la selección final. `manifest.json` conserva
huellas de código y evidencia. Las pruebas artificiales no demuestran resultados
de mercado. Las capturas de enero muestran únicamente el diagnóstico real de
histórico insuficiente; cualquier captura de un caso completo artificial se
identifica por separado.

No se modifican contratos, Pine, el motor contable, PROJECT_STATUS ni evidencias
anteriores. La adquisición de histórico suficiente continúa pendiente.
