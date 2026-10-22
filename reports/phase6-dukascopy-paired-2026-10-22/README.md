# Muestra BID/ASK de Dukascopy emparejada

22/10/2026. Se recibe el ASK horario correcto de enero y se comprueba contra el
BID anterior. La inspección inicial incompatible permanece conservada en
`../phase6-dukascopy-2026-10-22/`.

- BID: 528 velas de una hora; SHA-256
  `7efe20d392e9bf9506e7db31ad0c31673bb0e63e953eaeefdeaf9a1bc7396910`.
- ASK: 528 velas de una hora; SHA-256
  `b7e7904e871ebe7d042be5ecac2187d28cdb0317ca3a29e1233f7457478a2905`.
- Primera apertura: 01/01/2025 22:00 UTC. Último cierre inferido de la duración:
  31/01/2025 22:00 UTC.
- 528 intervalos comunes; cero intervalos exclusivos de un lado. Sin diferencias
  negativas ASK-BID en aperturas/cierres. Rango observado: 0,00001–0,00088 USD por
  unidad EUR, sin interpretación de spread intravela.

Los originales e inspecciones se guardan en un directorio exclusivo de
`.local/dukascopy/`. Los CSV de Downloads permanecen intactos. El cuerpo no
autentica proveedor, par ni lado: se mantienen como metadatos declarados.

`paired-input-diagnosis.json` contiene el diagnóstico del lector. Una segunda
comprobación sin importarlo confirma filas, fechas, orden, duplicados, coherencia
OHLC, emparejado, diferencias de precio y huellas de los originales preservados.
Su resultado se guarda en `independent-audit.json`; el código se conserva en
`independent-audit.py`. No se incluye el histórico bruto en estos informes.

Se verifican las huellas de las fuentes ejecutables contra la ejecución anterior
de 152 pruebas seleccionadas aprobadas. No hay cambios de código que justifiquen
repetirlas. No se ejecuta la colección completa.

La muestra está disponible para el trabajo posterior de integración. Este
recorrido no agrega velas diarias, ejecuta una estrategia, genera operaciones,
registra cuentas ni procesa contabilidad. Un mes no cubre el calentamiento SMA
20/60 diario. FASE 6 permanece abierta; más histórico, sesión diaria explícita,
simulación con spread e incorporación a la interfaz siguen pendientes.
