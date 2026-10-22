# Diagnóstico de gráfico — 21/10/2026

RE10142 aportado por el usuario: comprobación de compatibilidad del Pine, no error
de sintaxis. La cabecera comunicada es «Euro/Dólar estadounidense - 1 - OANDA».
`1` es un minuto; el contrato exige `1D`. Se solicita seleccionar un día y volver
a comprobar. No se han verificado todavía moneda, tipo de gráfico y unidades.

El mensaje v1 no identificaba la discrepancia. El generador v2 muestra valores
recibidos y requeridos, manteniendo los cinco requisitos. v1 sigue generando sus
bytes originales; v2 utiliza otra identidad. Las reglas de estrategia no cambian.
La nueva compilación Pine y la resolución completa del gráfico quedan pendientes.

131 pruebas de contratos, importación, libro, receptor, servicio e interfaz API y
CLI aprobadas. No se ejecuta la colección completa. Caché desactivada y temporal
GUID nuevo, conforme a AGENTS.md. Se preservan las evidencias anteriores.

Se conservan captura aportada, fuentes comprobadas, scripts v1/v2, manifiesto y
JUnit. El paquete nuevo está preparado, sin alta de cuenta, conexión o ejecución.
No se modifica PROJECT_STATUS ni se realizan commit o push.

Referencia: [formato de temporalidades](https://www.tradingview.com/pine-script-docs/concepts/timeframes/).
