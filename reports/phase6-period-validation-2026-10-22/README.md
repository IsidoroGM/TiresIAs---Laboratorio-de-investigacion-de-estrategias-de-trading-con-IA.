# Repetición fija de SMA 20/60 en 2024 y comparación con 2025

22/10/2026. Incremento de FASE 6, sin cierre de fase ni inicio de demo externa.

`protocol.json` se escribe antes de descargar 2024 y calcular sus resultados.
Fija 01/01–24/12 de cada año, fin exclusivo 25/12, con SMA 20/60, 1.000 USD
hipotéticos por período, cantidad fija 1 EUR y comisión supuesta 0,001. No se
buscan parámetros ni se ajustan fechas según beneficio. Los controles de calidad
existentes permanecen iguales; un período bloqueado no se reemplaza por otro corte.

## Fuente y calidad

Descarga pública del [catálogo de EV Trading Labs](https://evtradelabs.com/data),
EURUSD/H1/2024.json.gz, con atribución conservada. Original de 195.309 bytes;
SHA-256 `66fa719d8e7d75c11e1c691b232471fe3c9323e91ed998e8b82fe943f85d38b2`.
No se crea cuenta ni se contrata un plan. El origen es declarado por el catálogo;
no se certifica descarga directa de Dukascopy, volumen ni transporte final que
la automatización del navegador no expuso.

El original anual tiene 6.247 velas H1 y 314 fechas UTC observadas. El período fijo
contiene 6.144 velas y 308 sesiones; conserva 103 velas fuera del período en el
archivo original. El diario preparado coincide en conteos con una inspección
independiente de timestamps. El año completo contiene dos huecos del 25/12,
04:00–05:00 y 08:00–22:00 UTC: queda `blocked_internal_gaps`, sin operaciones ni métricas.

## Resultados y límites

| Período fijo | Sesiones | Ejecuciones | Cierres | EUR abiertos | Patrimonio final USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2024 | 308 | 6 | 3 | 0 | 999,96832951 |
| 2025 | 307 | 3 | 1 | 1 | 999,98870447 |

Cada período arranca con su propio capital y sin posición ni medias previas.
No se suman saldos de cuentas o períodos. 2025 ya era conocido y 2024 es anterior:
esta comprobación retrospectiva no es validación prospectiva ni una muestra futura
intacta. No permite concluir robustez estadística con cuatro operaciones cerradas.
No se cambian parámetros a partir de estos resultados negativos.

Un programa independiente con stdlib y Decimal reconstruye desde ambos gzip las
medias, señales, nueve ejecuciones, posición, caja, comisiones, spread, patrimonio
y drawdown de las 615 sesiones. No importa módulos del proyecto. Las cuentas
virtuales y el inbox permanecen sin cambios.

## Implementación y verificación

`market_comparison` compara dos resultados guardados con la misma configuración,
procedencia, sesión y motor, sin solapamiento. Preserva sus entradas exactas;
al consultar verifica huellas y reconstruye la tabla desde esas copias sin calcular
señales. Conserva resultados bloqueados como comparación incompleta. No autentica
al proveedor ni confunde la integridad de un archivo con la corrección de sus métricas.

La interfaz añade el formulario y la ficha de comparación con métricas en columnas
por período, enlaces a cada prueba y descarga JSON. El listado usa metadatos
acotados sin verificar todas las copias en cada visita. Los POST mantienen origen,
token y bloqueo de escritura existentes. GET no crea comparaciones ni ejecuta estrategias.

363 pruebas seleccionadas aprobadas (24 nuevas y 339 anteriores), con caché de
pytest desactivada y temporal exclusivo según AGENTS.md. No se ejecuta la colección
completa. Se comprueba sintaxis JavaScript y el botón de comparación real en navegador.
Las capturas y la comparación conservada muestran ambos períodos sin combinar saldos.

`manifest.json` inventaría fuentes, resultados, auditoría independiente, protocolo,
capturas y pruebas. Los gzip brutos permanecen en `.local/`, fuera de Git. Se
comprueban las huellas de las evidencias anteriores sin modificar sus archivos.
PROJECT_STATUS no cambia en este incremento; no se realizan commits ni pushes.
