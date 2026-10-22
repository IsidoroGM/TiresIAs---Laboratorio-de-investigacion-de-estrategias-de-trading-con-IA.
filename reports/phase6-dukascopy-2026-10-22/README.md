# Comprobación inicial de CSV Dukascopy

22/10/2026. Avance local de FASE 6, que permanece abierta.

Se revisan los dos archivos aportados por el usuario mediante el lector nuevo.
Los originales se conservan en un directorio exclusivo de `.local/dukascopy/`;
este informe incluye sus huellas y diagnósticos, sin redistribuir las cotizaciones.

| Archivo declarado | Velas | Apertura inicial UTC | Cierre final inferido UTC |
| --- | --- | --- | --- |
| EUR/USD BID H1 | 528 | 01/01/2025 22:00 | 31/01/2025 22:00 |
| EUR/USD ASK M1 | 660 | 22/10/2026 00:00 | 22/10/2026 11:00 |

No comparten ninguna apertura/cierre. El lector rechaza el emparejado por
intervalo y fechas distintos; no calcula spread ni genera ejecuciones. El BID
contiene 27 fechas UTC, 17 con 24 horas, y cuatro intervalos sin observaciones.
No se deduce si un hueco corresponde a un cierre de mercado o a datos ausentes.

La cabecera no contiene par, proveedor ni lado: esos metadatos son declarados,
sin autenticación del proveedor. No hay agregación diaria, comprobación de
equivalencia Pine ni simulación con spread. Tampoco se verifica que la última
vela comunicada por un archivo esté definitivamente cerrada.

Se prepara en el navegador el ASK de 1–31 enero 2025, 1 Hour, UTC. El intento de
descarga automática no entrega una ruta de archivo: la espera agota su plazo y
no se encuentra el archivo esperado en Downloads. Se deja el formulario correcto
abierto para la descarga manual, sin declarar obtenido el ASK pendiente.

**Pruebas seleccionadas: 152 aprobadas**, 21 del lector nuevo y 131 de los
componentes relacionados. Temporales GUID exclusivos y caché de pytest desactivada.
No se ha ejecutado la colección completa. `tests.log` y `tests.xml` conservan la
ejecución; `input-diagnosis.json` y `manifest.json` registran el diagnóstico y las
huellas de las fuentes probadas. No hay cuentas, órdenes, inferencias IA,
procesamiento contable, commit, push ni cierre de fase en este recorrido.
