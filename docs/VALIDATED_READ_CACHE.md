# Lectura con caché de desarrollo validado

La verificación de una petición guiada recorre varias veces sus fuentes. La caché
opcional evita interpretar repetidamente el mismo XML durante una sola consulta,
manteniendo las comprobaciones de sus archivos y del código en cada reutilización.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.validated_read_cache --run <peticion-guiada>
```

Devuelve el mismo documento verificado que `guided_compact_request verify`,
dentro de `packet`, junto con contadores de validaciones completas y reutilizaciones.
No escribe registros, consulta modelos o ejecuta backtests. El consumo que pueda
aparecer dentro de `packet` procede de intentos anteriores; `new_usage` es cero.

La primera lectura de cada bloque hace la validación completa. Las siguientes
contrastan las huellas de datos de desarrollo, manifiesto, investigación de origen,
registro congelado y eventos. También contrastan código, política y referencias
a las funciones de las que depende la validación. Un cambio detectado detiene la
lectura. No se confía solo en fechas de modificación o tamaños de archivos.

Se admiten hasta ocho bloques, con contenido de desarrollo de hasta 16 MiB por
bloque. Al superar esos límites se vuelve a validar completamente, sin omitir
controles. Se entregan copias independientes de los metadatos; al salir se vacían
las entradas y se restauran los enlaces temporales, también ante excepciones.

El ámbito utiliza un contexto de ejecución y enlaces temporales en los módulos
Python cargados. Otro hilo sin ese contexto conserva la validación completa.
No modifica archivos de módulos históricos ni está activado por defecto en
productores, ejecutores o sesiones. Debe mantenerse como opción explícita de
lectura; no sustituye comprobaciones de vigencia, reservas o permisos.

Las comprobaciones son optimistas: no bloquean todos los escritores de archivos
ni constituyen una transacción atómica. La caché no conserva permisos de revisión
o ejecución, no reabre intentos y no acredita equivalencia semántica o rendimiento.

El [perfil previo](../reports/phase4-verification-profile-2026-10-20.md) detectó 196
validaciones repetidas. La [lectura comprobada](../reports/phase4-cached-read-2026-10-20.md)
obtuvo el documento idéntico con una validación completa y 195 reutilizaciones.
Los tiempos registrados se tomaron en condiciones diferentes: no son una
comparativa controlada ni permiten afirmar un factor de aceleración.
