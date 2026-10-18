# Histórico educativo del BCE

Proveedor aprobado: Banco Central Europeo. Copia descargada el 18 de octubre
de 2026 para el primer ejercicio de la FASE 1.

## Procedencia

- [Página oficial y significado de las referencias](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html).
- [Descarga del histórico XML completo](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml).
- Copia original sin transformar: [ecb-eurofxref-hist-2026-10-18.xml](raw/ecb-eurofxref-hist-2026-10-18.xml).
- Tamaño: 8.202.267 bytes. Contiene varias monedas; nuestra inspección seleccionó USD, GBP, JPY y CHF.
- SHA-256: `3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

La dirección de descarga cambia de contenido al publicarse nuevas observaciones.
La copia fechada y su hash identifican los bytes concretos de este ejercicio.
El hash permite detectar cambios en la copia; no sustituye la verificación de
la procedencia. La descarga se realizó por HTTPS desde el dominio oficial.

## Estructura y muestra

XML representa datos mediante etiquetas y atributos anidados. Cada bloque
`Cube` con atributo `time` contiene las referencias de una fecha; dentro, el
atributo `currency` identifica la moneda y `rate` su valor por un euro.

Extracto de la observación más reciente, presentado con saltos de línea:

```xml
<Cube time="2026-10-16">
  <Cube currency="USD" rate="1.1253"/>
</Cube>
```

Esto significa **1 EUR = 1,1253 USD**. La fecha es una fecha de referencia,
no una marca de tiempo de ejecución. El XML incluye un espacio de nombres
(`http://www.ecb.int/vocabulary/2002-08-01/eurofxref`) que habrá que tener
en cuenta al buscar sus etiquetas desde Python.

| Fecha | Referencia USD por EUR |
|---|---:|
| 2026-10-16 | 1.1253 |
| 2026-10-15 | 1.1208 |
| 2026-10-14 | 1.1195 |
| 2026-10-13 | 1.1188 |
| 2026-10-12 | 1.1181 |

## Pares del laboratorio

Además de EUR/USD, el alcance incluye GBP/USD, USD/JPY y USD/CHF. Son pares
de negociación importante recogidos en la
[encuesta trienal del BIS de 2025](https://www.bis.org/publications/202509-commentary-otc-derivatives).
Esta selección no pretende reproducir exactamente los cuatro primeros puestos
por volumen mundial.

El XML ya contiene las monedas necesarias; no hace falta otra descarga. El BCE
publica unidades de cada moneda por un euro. Para obtener un par A/B queremos
unidades de B por una unidad de A: dividimos la referencia de B entre la de A,
siempre de la misma fecha. Para EUR, la referencia es 1.

| Par | Significado | Cálculo con atributos `rate` del XML |
|---|---|---|
| EUR/USD | Dólares por euro | USD |
| GBP/USD | Dólares por libra esterlina | USD / GBP |
| USD/JPY | Yenes por dólar | JPY / USD |
| USD/CHF | Francos suizos por dólar | CHF / USD |

Las tres referencias cruzadas son valores derivados, no cotizaciones directas
de esos pares publicadas en el XML. Como muestra, el 2026-10-16 se obtienen
GBP/USD = 1.333531, USD/JPY = 158.020084 y USD/CHF = 0.823958, redondeados a
seis decimales solo para mostrarlos. Se comprobó el cálculo sobre todo el
histórico durante la inspección. El lector `trading_ai.data.load_ecb_rates`
calcula ahora estos pares en memoria; no guarda series derivadas.

## Inspección realizada

La inspección inicial utilizó la biblioteca estándar de Python. Posteriormente
se repitió con el lector de la aplicación para los cuatro pares:

- XML legible mediante `xml.etree.ElementTree`.
- 7.116 bloques diarios, cada uno con exactamente una referencia de cada moneda:
  USD, GBP, JPY y CHF. Los cuatro pares comparten esas mismas fechas.
- Fechas válidas mediante `datetime.date.fromisoformat`, sin duplicados.
- Todas las referencias de esas cuatro monedas y los tres cocientes derivados
  son números finitos y positivos, comprobados con `decimal.Decimal`.
- Periodo observado: 1999-01-04 a 2026-10-16.
- Orden estrictamente descendente por fecha.

Esta inspección no demuestra que estén todos los días de publicación esperados.
Falta contrastar el calendario de publicación. El BCE no publica referencias
los fines de semana ni los días de cierre de TARGET; no debemos rellenar
automáticamente esas fechas ni tratarlas como errores.

Son referencias informativas, no precios ejecutables ni velas OHLC. No incluyen
spread bid/ask, comisiones ni datos intradiarios. Servirán para aprender a leer,
validar y transformar series; no para acreditar la viabilidad de operaciones reales.

## Comprobar la copia

Desde la raíz del proyecto, en PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\data\raw\ecb-eurofxref-hist-2026-10-18.xml'
```

El resultado debe coincidir con el hash anterior (sin importar mayúsculas).
El lector para los cuatro pares y las instrucciones para probarlo están descritos
en el [README del proyecto](../README.md#leer-el-histórico-y-ejecutar-las-pruebas).
Ordena las observaciones cronológicamente y rechaza monedas necesarias ausentes
sin mezclar referencias de días diferentes.
