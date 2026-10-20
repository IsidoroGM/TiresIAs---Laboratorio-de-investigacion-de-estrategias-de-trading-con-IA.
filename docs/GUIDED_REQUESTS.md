# Petición guiada por las reglas ya capturadas

La petición guiada añade un resumen mecánico de la cobertura de reglas a una
petición compacta preparada. Ayuda a mostrar al investigador qué formas de reglas
aparecen en el historial. No demuestra novedad ni recomienda una estrategia.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.guided_compact_request prepare --prepared-run <peticion-extendida> --coverage-run <cobertura>
.\.venv\Scripts\python.exe -m trading_ai.guided_compact_request verify --run <peticion-guiada>
```

Las fuentes deben compartir el mismo registro congelado. Todas las identidades
de la cobertura deben figurar entre las reglas consumidas de la petición base.
Se conserva el historial completo, incluidos motivos literales de revisiones,
reglas, objetivo, datos y controles. Si la extensión ya existe o faltan
identidades, se detiene para renovar las fuentes; no las corrige automáticamente.

El máximo sigue siendo 12.288 bytes del JSON preparado. Si no cabe, se rechaza sin
recortar motivos o entradas. El tamaño en bytes no equivale al número de tokens:
el recuento previo y el encaje en el contexto del proveedor siguen sin verificar.

El protocolo `guided_compact_request_preview_v1` produce `guided.json`, su huella,
`request.json` y eventos. No configura proveedor, envía mensajes o concede un
intento nuevo. Conserva el presupuesto observado, incluso cuando está consumido;
los controladores anteriores no aceptan esta previsualización como autorización.

La [comprobación local](../reports/phase4-guided-request-2026-10-20.md) dejó una
petición de 12.142 bytes preparada y sin enviar. El intento compacto real anterior
sigue consumido y su candidata duplicada sigue sin aprobarse o simularse.

La verificación reconstruye el documento desde sus fuentes y compara sus bytes,
huellas y código. Puede usarse la [lectura con caché opcional](VALIDATED_READ_CACHE.md)
para evitar interpretar repetidamente el mismo histórico durante esa consulta.
Ambas modalidades verifican el documento; ninguna ejecuta la investigación.

El [plan de campaña local](LOCAL_CAMPAIGNS.md) registra límites explícitos y
conserva este documento y todo su historial. Continúa sin presupuesto activado.
