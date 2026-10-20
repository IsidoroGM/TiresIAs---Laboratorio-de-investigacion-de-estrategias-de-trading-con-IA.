# Verificar las copias de evidencia

Los informes archivados incluyen inventarios `snapshot.json` con rutas de origen
y SHA-256. `evidence` comprueba el formato de mapa versión 1 usado por los informes
estructurados y compactos. Otros formatos se rechazan expresamente; no se omiten
para presentar una verificación completa.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m trading_ai.evidence --snapshot reports/phase4-compact-memory-request-2026-10-20/snapshot.json
```

Por defecto verifica solo las copias del directorio del inventario. Puede
utilizarse después de clonar Git aunque falten los originales de `.local`, que no
se incluyen en el repositorio. El resultado indica que los originales no se
inspeccionaron; no los cuenta como comprobados ni reconstruye sesiones.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m trading_ai.evidence --snapshot reports/phase4-compact-memory-request-2026-10-20/snapshot.json --with-originals
```

Esta modalidad exige también los originales y sus huellas, dentro de la raíz de
fuentes permitida. Por defecto es el proyecto; `--source-root` permite indicar
explícitamente otra raíz. Las rutas absolutas antiguas no se remapean ni se
reescriben para hacerlas parecer verificadas en otra carpeta.

Puede repetirse `--snapshot` para un lote y usar `--json` para obtener detalles.
Se rechazan inventarios duplicados, rutas de copia que salgan de su directorio,
archivos modificados o ausentes y límites excedidos. Los límites son 1.024
entradas, 32 MiB por archivo y 512 MiB de lectura total. No escribe archivos,
consulta modelos, abre servicios o repite cálculos. Un fallo no publica un éxito
parcial. Las referencias originales contadas pueden apuntar al mismo archivo
desde distintos inventarios; no se presentan como archivos físicos únicos.

La comprobación inicial de esta herramienta verificó 236 copias y sus 236 referencias originales
(1.876.050 bytes leídos en total), sin llamadas de modelo o backtests. Una huella
que coincide prueba integridad de esos bytes respecto al inventario; no sustituye
la revisión técnica, reproduce una simulación o acredita rentabilidad.

La consolidación posterior de [petición guiada](GUIDED_REQUESTS.md), perfil y
[caché opcional](VALIDATED_READ_CACHE.md) verificó 17 inventarios concretos:
262 copias y 262 referencias originales, con 2.228.440 bytes leídos. El ámbito
son esos inventarios de formatos compatibles; no incluye todos los informes
históricos ni convierte sus referencias repetidas en archivos únicos.
