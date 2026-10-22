# Históricos aportados y primera prueba con precios reales

22/10/2026. Avance de FASE 6; sin cierre, commit o push.

## Fuente y contraste

La descarga binaria directa de Dukascopy conserva sus diagnósticos anteriores.
El exportador web revisado admite H1 con un rango aproximado de un mes: con inicio
01/01/2025, el calendario deshabilita los días posteriores al 01/02. Ofrece
multiplicadores 1–4 de Hour, sin una exportación D1 directa en ese formulario.
Las dos rutas públicas de FXCM comprobadas responden HTTP 403, error 1010. No se
resuelven retos ni se utilizan credenciales o servicios de pago.

Se obtiene desde el [catálogo de EV Trading Labs](https://evtradelabs.com/data)
el archivo `EURUSD/H1/2025.json.gz`: 199.128 bytes y 6.223 velas H1 BID/ASK. El
catálogo declara agregación de Dukascopy, aperturas UTC, años cerrados sin cuenta
y uso gratuito con atribución. Se conserva esa atribución. No es una descarga
autenticada directamente del bróker ni una garantía de equivalencia con OANDA.

Una auditoría independiente JSON/Decimal/CSV confirma que las 528 velas de enero
coinciden exactamente en fechas y OHLC con ambos CSV originales del usuario.
El volumen se conserva en los originales y no se le atribuyen unidades verificadas.

## Calidad y período fijado antes del cálculo

El archivo anual forma 313 fechas UTC observadas. El 25/12 presenta dos huecos
internos: 03:00–06:00 y 08:00–22:00 UTC. El original anual completo se conserva.
Su prueba queda `blocked_internal_gaps`, sin operaciones ni rentabilidad.

Antes de mirar métricas se fija el período **01/01/2025–24/12/2025**, con fin
exclusivo 25/12. Incluye 6.122 velas H1 y 307 sesiones; excluye explícitamente las
101 velas posteriores al corte. El corte obedece al primer día con huecos internos,
no al resultado de la estrategia. No se rellenan precios ni se eliminan velas del
original. No se certifica un calendario de mercado ni se declara ausencia de todos
los errores posibles del proveedor.

Se mantienen SMA 20/60, largos, capital hipotético 1.000 USD, cantidad fija 1 EUR y
comisión proporcional supuesta 0,001 por ejecución. Hay tres operaciones hipotéticas,
un cierre y una posición abierta. El patrimonio final calculado es 999,98870447 USD;
no se fuerza una venta al terminar el histórico. Es un ensayo retrospectivo con
hipótesis de costes, sin swaps, deslizamiento, liquidez o equivalencia Pine verificados.
Las cuentas virtuales y el inbox no cambian.

## Implementación

`market_history` prepara CSV Dukascopy BID/ASK o JSON gzip anual H1 de EV Trading
Labs. Guarda los originales byte a byte, procedencia declarada, período explícito,
huellas y datos de calidad. Al cargar reconstruye desde los originales y contrasta
el diario y el inventario. El perfil previo BI5 permanece admitido.

La nueva importación de la interfaz recibe solo archivos elegidos y limita el
total a 2 MiB. Permite consultar el histórico, comprobar originales y ejecutar el
cálculo mediante una acción posterior. No inicia red ni backtests al consultar.
Los POST mantienen el origen y token locales existentes. No se cambian contratos,
Pine, el motor contable, PROJECT_STATUS ni evidencias anteriores.

Se bloquean huecos internos y tramos sin observaciones superiores a 96 horas,
incluidos los extremos solicitados. Ese umbral es una comprobación explícita de
cobertura, no un calendario de negociación verificado. Se conserva el motivo del
bloqueo en lugar de publicar métricas sobre un período incompleto.

La evidencia incluye los diagnósticos externos, contraste independiente, resultados,
pruebas seleccionadas y capturas de navegador. Los precios originales permanecen
en `.local/`, fuera de Git. El histórico 2024–2025 completo todavía no está adquirido;
esta entrega obtiene el archivo de 2025 y calcula únicamente el período indicado.

## Verificación y límites de la comprobación

339 pruebas seleccionadas aprobadas: 40 del nuevo importador y las 299 seleccionadas
de la entrega anterior. `tests.log` y `tests.xml` conservan el resultado; no se ha
ejecutado la colección completa. Se desactiva la caché de pytest y se utiliza una
ruta temporal nueva y exclusiva según AGENTS.md. Se comprueba sintaxis JavaScript.

Las importaciones reales del archivo anual y los CSV se completan mediante la API
HTTP local. La interfaz presenta los campos por formato y permite calcular desde
la ficha importada; se comprueban el botón y el resultado en navegador. La
automatización del selector nativo de archivos no llegó a completarse. Por ello,
no se declara validada la selección manual de archivos en el navegador. No se
interpreta esa limitación de la automatización como un fallo confirmado de la aplicación.

Un segundo cálculo independiente, sin importar módulos del proyecto, reconstruye
las 307 sesiones desde los precios originales y confirma todas las medias, señales,
tres ejecuciones, caja, posición, patrimonio y drawdown. Los resultados de la API
y del navegador coinciden en entradas, reglas y cálculos; sus rutas de procedencia
son distintas, por lo que no se exige igualdad byte a byte entre ambos resultados.
Las capturas muestran el período y el resultado real de esta prueba.

`manifest.json` inventaría las evidencias y las fuentes probadas. Las copias de
auditoría y resultados no incluyen los archivos brutos anuales. Las huellas se
comprueban también frente a los originales locales y las evidencias anteriores,
que permanecen sin cambios. El resultado conservado no acredita autenticidad
del proveedor, equivalencia con TradingView ni una estrategia validada fuera de muestra.
