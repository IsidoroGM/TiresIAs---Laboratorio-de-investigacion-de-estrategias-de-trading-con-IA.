# Lectura guiada con caché opcional — 20/10/2026

La lectura del registro guiado `1a1d0783778243ac989ca1ab3fc49911` devolvió un
`packet` idéntico al documento guiado original. Se guardó en
`.local/cached-read-checks/dbfac940f4ff4ea49692d3200b1d3d7a`.

- Una validación completa y 195 reutilizaciones con fuentes contrastadas.
- Ninguna lectura excedió los límites de contenido o cantidad de bloques.
- Tiempo de pared observado: 20,264602 segundos.
- Consumo nuevo: cero consultas, tokens, coste de API y backtests.
- Permiso nuevo de generación y ejecución: ambos desactivados.

El documento interior conserva el consumo heredado y el presupuesto consumido.
Esta lectura no generó una propuesta ni convirtió el duplicado real en una
candidata aceptada. No leyó evaluación exterior ni alteró registros de origen.

Se comprobaron la huella del registro, el evento de finalización, la igualdad con
el documento guiado y la huella del código de caché antes de archivar. El
[inventario](phase4-cached-read-2026-10-20/snapshot.json) conserva cinco copias:
registro, huella, eventos, código de caché y sus pruebas. Verificarlas no reconstruye
la sesión ni reproduce la lectura: comprueba los bytes declarados.

La consolidación verificó 17 inventarios concretos, incluidos los anteriores:
262 copias y sus 262 referencias originales, con 2.228.440 bytes leídos. No se
incluyeron inventarios antiguos de otros formatos o con originales fuera del
proyecto. Las pruebas copiadas usan un nombre que pytest no recolecta; no se
añaden por segunda vez a la suite desde el archivo de evidencias.

Las diez pruebas focalizadas comprobaron copias independientes, cambios de datos
con fecha de modificación restaurada, cambios de política o huellas de código,
limpieza ante excepciones, ámbitos anidados, otro hilo sin contexto, límite de
entradas y lectura integrada sin proveedor o motor.

El tiempo anterior de 85,70 segundos incluía perfilador y pytest concurrente.
Las condiciones difieren y no se afirma una aceleración medida. La caché continúa
opcional y fuera de los productores sellados. Uso y límites:
[documentación](../docs/VALIDATED_READ_CACHE.md).


Comprobación conjunta posterior: **1.253 pruebas aprobadas en 1.062,09 segundos
(17 min 42 s)**. Incluye la integración artificial y las diez pruebas de caché
que se habían ejecutado por separado tras la suite anterior de 1.242.
Ejecución de Codex con caché de pytest desactivada y temporal exclusivo según
AGENTS.md. No hubo cambios de código en esta consolidación.
