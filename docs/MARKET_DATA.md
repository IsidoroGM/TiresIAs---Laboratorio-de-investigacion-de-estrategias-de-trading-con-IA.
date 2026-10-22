# Importar históricos EUR/USD y calcular una prueba

Avance de FASE 6, 22/10/2026. Los precios alimentan una investigación histórica
independiente de las cuentas virtuales y las importaciones de operaciones TradingView.

## Fuentes y formatos

- **CSV Dukascopy BID/ASK H1**: los archivos del exportador oficial con cabecera
  `Etc/UTC,Open,High,Low,Close,Volume`. Hace falta el mismo período en ambos lados.
  Par, proveedor, lado e intervalo son declaraciones explícitas: no vienen
  certificados en la cabecera. Se aceptan hasta doce pares de archivos.
- **EV Trading Labs H1 anual**: un `.json.gz` EUR/USD, con columnas
  `ts,o,h,l,c,ao,ah,al,ac,v`. El catálogo declara precios agregados de Dukascopy,
  timestamps de apertura UTC y años cerrados H1 gratuitos sin cuenta. El uso exige
  atribución a EV Trading Labs, conservada en los resultados. Descargar únicamente
  el instrumento, intervalo y año elegidos desde su [catálogo](https://evtradelabs.com/data).
  No se admite un archivo M1 cambiando su nombre.

El archivo anual obtenido se conserva en `C:/Users/34656/Downloads/2025.json.gz`.
Su huella SHA-256 es
`75424fa8293615a3e98d7463c90c8e1ef446bff0f29388c894298249791c995c`.
Los originales importados se copian en `.local/dukascopy/`, fuera de Git. Las huellas
permiten detectar cambios posteriores; no autentican al proveedor ni certifican
equivalencia con OANDA. No se atribuyen unidades verificadas al volumen.

## Desde la interfaz

1. Abrir **Simulación y TradingView → Históricos EUR/USD y prueba con spread →
   Importar precios históricos**.
2. Elegir el formato. Para CSV, seleccionar los archivos BID y ASK correspondientes.
   Cada lista se ordena por nombre: usar nombres con fecha ISO para varios meses.
   Los archivos deben formar períodos crecientes, sin solapamientos ni duplicados.
   Para el formato anual, seleccionar un solo `.json.gz` y declarar su año cerrado.
3. Indicar inicio UTC incluido y fin UTC **excluido**. Para incluir el 24/12/2025,
   usar `2025-12-25` como fin. El período debe estar cerrado y no superar 1.098 días.
4. Importar. El límite conjunto de archivos en la interfaz es 2 MiB. Se guardan
   los originales completos; las horas fuera del período se cuentan como excluidas.
5. Revisar la ficha y la calidad. Elegir capital hipotético en USD, cantidad fija
   en EUR y tasa proporcional de comisión supuesta. Pulsar la acción de calcular.

La importación y el cálculo son acciones distintas. Consultar una ficha no
descarga ni ejecuta una estrategia. No se crean cuentas, movimientos o eventos de inbox.

La recepción de archivos por la API local se ha comprobado con los CSV reales y
el archivo anual. El cálculo posterior se ha comprobado en el navegador. La
automatización del selector nativo de archivos no llegó a completarse; esa parte
de la selección manual en navegador no queda validada en esta entrega.

## Calidad, sesiones y reglas de cálculo

Se validan orden, duplicados, horas UTC, OHLC, precios positivos y coherencia
BID/ASK. El archivo anual conserva incluso las velas planas de volumen cero.
Cada sesión corresponde a una fecha UTC observada: se mantienen domingos y días
parciales. No se rellenan huecos ni se certifica un calendario de mercado.

La prueba se bloquea ante huecos internos de una sesión y ante tramos sin
observaciones superiores a 96 horas, incluidos los extremos solicitados. El
umbral de 96 horas es una política explícita de cobertura, no una validación del
calendario de negociación. También se bloquea si faltan las 61 sesiones mínimas
para el calentamiento y la primera comparación SMA 20/60.

Las señales usan cierres BID; se ejecutan en la primera apertura H1 observada de
la sesión siguiente. Las compras usan ASK; las ventas y la valoración usan BID.
El spread ya está en esos precios y no se cobra de nuevo. No se fuerza el cierre
de una posición al terminar el período. Swaps, deslizamiento, liquidez e intravela
no están verificados. La comisión introducida es una hipótesis, no una tarifa del proveedor.

## Primera prueba real de 2025

El archivo contiene 6.223 velas H1, que forman 313 fechas UTC. Un contraste
independiente confirma que las 528 velas de enero coinciden exactamente en fechas
y OHLC con ambos CSV originales del usuario.

El 25/12 contiene dos huecos internos. El año completo se conserva, pero su
simulación queda bloqueada sin métricas. Antes de calcular la estrategia se fija
el tramo **01/01/2025–24/12/2025**, con fin exclusivo 25/12: 6.122 velas, 307
sesiones y 101 velas fuera del período. El corte se elige por calidad, sin mirar
el resultado. Una [entrega posterior](PERIOD_VALIDATION.md) incorpora el archivo
anual de 2024 y repite las mismas reglas en otro período. Los originales de ambos
años están disponibles; no se certifica cobertura completa ni se ignoran sus huecos.

Con SMA 20/60, capital hipotético 1.000 USD, cantidad 1 EUR y comisión supuesta
0,001 por ejecución, hay tres ejecuciones hipotéticas, una operación cerrada y
1 EUR abierto. El patrimonio final es **999,98870447 USD**. Un segundo cálculo
independiente reproduce todas las medias, señales, ejecuciones y puntos de capital.
No hay una validación equivalente en Pine ni una conclusión de rentabilidad.

## CLI sin descargas

Los directorios de salida deben ser nuevos. Este ejemplo usa un nombre distinto
en cada ejecución:

```powershell
$historyOutput = Join-Path '.local/dukascopy' ('prices-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -m trading_ai.market_history `
  --format evtradelabs_h1_json_gzip `
  --annual 'C:/Users/34656/Downloads/2025.json.gz' --year 2025 `
  --start-date 2025-01-01 --end-date 2025-12-25 --output "$historyOutput"
```

Para los CSV, usar `--format dukascopy_csv --bid RUTA_BID --ask RUTA_ASK`, las
mismas fechas y una salida nueva; omitir `--annual` y `--year`. Con varios archivos,
pasar cada lista en orden cronológico. Después puede calcularse con
`python -m trading_ai.dukascopy_backtest --help`, o seleccionarse el histórico en
la interfaz. La carga reconstruye desde los originales y contrasta el diario y
el inventario antes de usar precios.

Pruebas, auditorías y capturas en
[`reports/phase6-market-history-import-2026-10-22/`](../reports/phase6-market-history-import-2026-10-22/README.md).
