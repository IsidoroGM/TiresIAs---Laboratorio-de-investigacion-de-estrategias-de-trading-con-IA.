# CSV de precios Dukascopy: avance de FASE 6

22/10/2026. Se incorpora un lector local de los archivos de precios descargados
desde el [exportador oficial](https://widgets.dukascopy.com/en/historical-data-export).
El descargador por meses y la agrupación diaria UTC están implementados por CLI.
La ampliación del histórico está limitada por el acceso del proveedor. Ya se puede
consultar y calcular una prueba con spread sobre históricos preparados desde
Simulación y TradingView. La pantalla también permite importar nuevos CSV BID/ASK
o un archivo anual H1 de EV Trading Labs. La [guía de históricos](MARKET_DATA.md)
describe esta alternativa, los períodos explícitos y la primera prueba real de 2025.

## Primera descarga

Seleccionar EUR/USD, Export, período **1 Hour**, fechas **1–31 enero 2025**,
zona **UTC** y **Bid**. Descargar. Repetir con **Ask** y exactamente los mismos
ajustes. Al reabrir Export, el formulario observado vuelve a Minute y la fecha
actual: revisar todos los campos en cada descarga.

La versión del formulario revisada permite Tick, Second, Minute y Hour, sin una
opción diaria directa. Este lector conserva el intervalo original. La futura
comparación con velas de otro proveedor debe respetar las diferencias de sesión
y días parciales. La preparación diaria implementada usa fechas UTC observadas,
incluidos domingos y días parciales, sin rellenar precios. Un mes no permite
evaluar la SMA 20/60 diaria con su calentamiento completo.

## Formato comprobado

```csv
Etc/UTC,Open,High,Low,Close,Volume
2025-01-01T22:00:00+00:00,1.03503,1.03577,1.03483,1.0355,1443220000
```

La cabecera identifica la zona y las columnas, pero no incluye par, proveedor,
lado BID/ASK ni duración. Se declaran explícitamente, sin convertir el nombre del
archivo en una garantía de autenticidad. Se comprueban UTC, alineación temporal,
orden, duplicados, OHLC, volumen no negativo y límites de tamaño/filas.

Los intervalos ausentes y los días UTC con menos de 24 horas se informan sin
rellenar precios ni deducir un calendario de mercado. El volumen se conserva sin
atribuirle unidades no verificadas. No se certifica que la última vela esté cerrada.

## Inspección local

Desde el entorno virtual, usando una ruta de salida que todavía no exista:

```powershell
python -m trading_ai.dukascopy --pair EUR/USD `
  --bid "RUTA_DEL_BID.csv" --bid-interval 1Hour `
  --ask "RUTA_DEL_ASK.csv" --ask-interval 1Hour `
  --output .local/dukascopy/revision-nueva
```

Admite `1Hour` y `1Minute`. Para conservar e inspeccionar solamente el BID, omitir
los dos argumentos ASK. Cada original se guarda byte a byte junto a una inspección
JSON. `report.json` resume el emparejado. Un resultado incompleto o incompatible
devuelve código 2 y conserva el diagnóstico; un par alineado devuelve 0. Una
salida existente no se reemplaza. La igualdad usa fechas de apertura y cierre,
sin emparejar filas por posición, remuestrear ni rellenar huecos.

Si el par coincide, se muestran diferencias ASK-BID en aperturas y cierres. Los
extremos de velas independientes no se interpretan como spread intravela. Un ASK
inferior al BID en esos puntos impide declarar el par listo.

Estos CSV contienen **precios**, no ejecuciones. No cargarlos en el importador de
operaciones de la pantalla Simulación y TradingView. La herramienta nueva no
crea cuentas, genera fills, procesa contabilidad ni abre conexiones de red.

## Archivos aportados el 22/10/2026

El BID aporta 528 velas H1 entre 01/01/2025 22:00 UTC y 31/01/2025 22:00 UTC
(el último instante es el cierre inferido de su última vela horaria). Se observan
27 fechas UTC, 17 con 24 horas, y cuatro intervalos sin observaciones.

El primer ASK aportado corresponde a 660 velas M1 del 22/10/2026 entre 00:00 y 11:00 UTC.
No hay ninguna apertura/cierre común con el BID. Se conservan ambos originales y
se rechaza su emparejado en la inspección inicial.

La segunda entrega aporta el ASK H1 de enero de 2025: 528 velas que coinciden con
las 528 del BID, sin velas exclusivas de un lado ni diferencias negativas ASK-BID
en apertura/cierre. Sus diferencias observadas oscilan entre 0,00001 y 0,00088 USD
por unidad EUR; no describen el spread máximo o mínimo intravela. Se conserva la
pareja original y su informe en un directorio exclusivo de `.local/dukascopy/`.

Una comprobación independiente con CSV, fechas y Decimal confirma el número de
filas, orden, ausencia de duplicados, coherencia OHLC, alineación y diferencias
de precios. El [informe de la muestra emparejada](../reports/phase6-dukascopy-paired-2026-10-22/README.md)
conserva el resultado y sus huellas. Esto completa la comprobación de esta muestra;
la simulación diaria continúa pendiente.

## Descarga por meses y sesiones diarias UTC

Se añade `python -m trading_ai.dukascopy_history`, inicialmente limitado a EUR/USD
y meses completos cerrados, con un máximo de 36 meses por ejecución. Es una acción
explícita: arrancar o consultar el laboratorio no inicia descargas. No requiere
instalar paquetes, registrar cuentas ni aportar credenciales.

```powershell
python -m trading_ai.dukascopy_history `
  --start-month 2024-01 --end-month 2025-12 `
  --output .local/dukascopy/historico-nuevo
```

El archivo público H1 se solicita desde `www.dukascopy.com/datafeed/`, con mes
indexado desde cero. Se comprueba cada redirección: solo se admiten los dos hosts
de Dukascopy previstos y la misma ruta. El servidor redirige algunos archivos a
HTTP. El manifiesto guarda la URL final y `final_transport_https`; no atribuye
autenticación del proveedor a esos datos. No se desactiva la validación TLS ni se
usan cookies, claves, resolución de retos o servicios de pago.

Las peticiones son secuenciales y espaciadas. HTTP 202, 429, errores, HTML o un
cuerpo vacío no cuentan como cotizaciones. Un error interrumpe la ejecución y
genera `failure.json`, con estado HTTP y `Retry-After` cuando están disponibles.
Los intentos anteriores no se reemplazan. Los archivos ya válidos permanecen en
caché para que una nueva ejecución explícita pueda continuar.

Cada BI5 original se conserva junto a URL, fecha y SHA-256. Se validan LZMA,
límites de memoria/tamaño, orden temporal, precios, volúmenes y todas las horas
del mes. El precio usa la escala EUR/USD verificada contra los CSV aportados.
Los registros planos de volumen cero se excluyen con una política explícita:
el número excluido queda registrado y el original binario permanece intacto.
Un cuerpo corrupto o un mes sin todas sus horas no entra en caché.

`daily.json` agrupa por fecha UTC y conserva las fechas observadas, incluidos
domingos y días parciales. Distingue el límite de sesión de la primera/última
hora realmente observada. No inventa cotizaciones para las horas o días ausentes.
Los huecos internos quedan visibles e impiden preparar señales. Esta definición
no declara equivalencia con las velas diarias de OANDA o TradingView.

`signal-preview.json` contiene solo medias y señales SMA 20/60 sobre cierres BID,
sin órdenes, fills, contabilidad ni métricas de rentabilidad. Se requieren al
menos 61 sesiones para disponer del primer cruce tras el calentamiento.

Para reproducir una descarga ya conservada sin ninguna petición de red:

```powershell
python -m trading_ai.dukascopy_history `
  --start-month 2025-01 --end-month 2025-01 --offline `
  --output .local/dukascopy/reproduccion-nueva
```

El ensayo real de enero descargó BID y ASK automáticamente: las 528 velas de cada
lado coinciden exactamente en fechas y OHLC con los CSV del usuario. Produce 27
sesiones UTC observadas. La reproducción offline tiene el mismo contenido diario,
sin nuevas peticiones. No hay histórico suficiente para la SMA diaria 20/60.

La ampliación a 2024–2025 no se completó: el servidor mantiene HTTP 429, también
tras una nueva comprobación más de tres minutos después. No se deduce que se hayan
obtenido esos dos años. Se conserva el [informe de este avance](../reports/phase6-dukascopy-history-2026-10-22/README.md).

Fuentes técnicas consultadas:

- [Históricos gratuitos de Dukascopy](https://www.dukascopy.com/swiss/english/marketwatch/historical/).
- [Formación de los períodos diarios UTC](https://www.dukascopy.com/swiss/english/about/faq/?mob=0).
- [Generación de las rutas en dukascopy-node](https://github.com/Leo4815162342/dukascopy-node/blob/master/src/url-generator/index.ts),
  contrastada con el formato binario y las respuestas reales. No se instala ni
  utiliza ese paquete; su versión actual emplea otra API.
- [Incidencia pública de disponibilidad del datafeed](https://github.com/Leo4815162342/dukascopy-node/issues/254).

## Prueba histórica con BID/ASK

Desde **Simulación y TradingView → Precios Dukascopy y prueba con spread**, elegir
un histórico preparado, capital y cantidad hipotéticos y una comisión proporcional
supuesta. Cero permite un ensayo sin comisión; no certifica una tarifa del proveedor.
**Verificar datos y calcular** comprueba primero los binarios originales, sus huellas
y la reconstrucción de las sesiones. Consultar la pantalla no inicia descargas ni
cálculos. Los resultados nuevos se guardan en `.local/dukascopy-research/`.

La estrategia fija de la pantalla es SMA 20/60 sobre cierres BID de sesiones UTC
observadas. Se mantienen domingos y días parciales. Una señal se conoce al límite
de cierre de esa sesión y se ejecuta en la primera apertura H1 observada de la
siguiente, comprando a ASK y vendiendo a BID. No se inventa una apertura a las
00:00 ni se vuelve a restar el spread ya incluido en los precios. La comisión
supuesta se carga una vez por ejecución. Se requiere efectivo suficiente, sin
apalancamiento. El patrimonio usa el cierre BID observado y su fecha real.

No se simulan swaps, deslizamiento, liquidez, movimientos intravela o restricciones
de bróker. La señal final puede quedar pendiente; la posición abierta no se fuerza
a cerrar. Este cálculo independiente no produce eventos de TradingView, no modifica
el libro de cuentas y no declara equivalencia con Pine u OANDA.

También está disponible desde el entorno virtual, con una salida nueva:

```powershell
python -m trading_ai.dukascopy_backtest `
  --history .local/dukascopy/auto-pilot-2025-01-2026-10-22 `
  --output .local/dukascopy/prueba-nueva `
  --capital 1000 --quantity 1 --commission-rate 0
```

Con enero devuelve código 2 y guarda `insufficient_history`: 27 sesiones disponibles,
61 requeridas y 34 pendientes. No calcula rentabilidad ni inventa operaciones.
Una prueba calculada devuelve 0. Una entrada alterada o inválida devuelve 2 y no
crea la salida. Cada resultado conserva las copias de entrada, las reglas y huellas
de las fuentes ejecutables; una salida previa no se reemplaza.

La nueva comprobación de descarga 2024–2025 sigue recibiendo HTTP 429 en la primera
petición y se detiene. La interfaz está preparada para histórico suficiente, pero
los resultados reales completos todavía no existen. Véase el [informe de este
avance](../reports/phase6-dukascopy-spread-2026-10-22/README.md).
