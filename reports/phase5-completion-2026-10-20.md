# TiresIAs — interfaz local de FASE 5

20/10/2026. **FASE 5 completada y comprobada: 1598 pruebas aprobadas** y revisión
visual en Windows. Inicio limpio en `main`, commit
`f5e654435f42efcb76c53a82f812a541bf78d521`. El usuario autoriza después de las
comprobaciones publicar este cierre con commit y push.

## Alcance entregado

| Necesidad | Comportamiento comprobado |
| --- | --- |
| Consultar el laboratorio | Cinco apartados: Inicio, Experimentos, Resultados, Memoria del agente y Consumo |
| Encontrar un experimento | Filtros combinables de par, estrategia, fecha local registrada, estado y procedencia |
| Entender lo guardado | Ficha de hipótesis, reglas, parámetros, controles, criterio, cuentas, respuestas, revisiones y errores |
| Revisar capital virtual | Resúmenes y contabilidad guardados; curva, drawdown, operaciones y posición abierta sin recalcular |
| Comparar con límites | Compatibilidad de datos, fechas, moneda y controles; diferencias visibles y cuentas independientes |
| Llegar al original | Archivos de la ejecución, informes e inventarios enlazados como texto |
| Distinguir fuentes | Originales locales, copias históricas y consulta vigente de SQLite separados; integridad acotada sin afirmar certificación de rentabilidad |
| Consultar sin ejecutar | HTTP de solo lectura en 127.0.0.1; sin modelo, nuevas reservas, simulaciones, instalación o servicios permanentes |

Arranque desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.lab
```

Abrir [TiresIAs local](http://127.0.0.1:8765). Cerrar con **Ctrl+C en la terminal**.
No requiere Ollama. [Guía de uso](../docs/LAB_INTERFACE.md) y
[contratos de lectura](../docs/PHASE5_PLAN.md).

## Pruebas y conservación

Las **51 pruebas nuevas** pasaron en 11,89 s antes del ajuste de presentación de
fecha local. La colección final incluye esas pruebas y las 1547 anteriores.
Siempre se desactiva la caché pytest y se elige un temporal GUID nuevo y exclusivo
por proceso, según AGENTS.md. No se cambian permisos generales de Windows.

La primera colección completa se detuvo antes de modificar fuentes para corregir
el filtro de fecha: comparaba el día UTC del archivo con una fecha mostrada en
hora local. Se comprobaron los procesos detenidos y después se reinició toda la
colección con fuentes estables. Los logs parciales de la raíz de esta carpeta
son de esa ejecución interrumpida; **no se cuentan como pruebas aprobadas**.
La ejecución final queda en `suite-final` y su cotejo exige la colección exacta,
sin duplicados, omisiones, fallos o saltos, y huellas de fuentes sin cambios.

Resultado final: **1598 aprobadas**, cero fallos, errores o saltos. Particiones de
510, 575 y 513 casos, con tiempos JUnit de 1235,329 s, 1399,702 s y 1285,328 s.
Los procesos se ejecutaron en paralelo; no se suman esos tiempos como duración
transcurrida. La colección coincide exactamente y los 139 archivos de fuentes
mantienen sus huellas durante toda la comprobación.

- [Resultado completo](phase5-completion-2026-10-20/suite-final/suite-result.json).
- [Colección y huellas](phase5-completion-2026-10-20/suite-final/suite-manifest.json).
- JUnit: [510 casos](phase5-completion-2026-10-20/suite-final/suite-1.xml),
  [575 casos](phase5-completion-2026-10-20/suite-final/suite-2.xml) y
  [513 casos](phase5-completion-2026-10-20/suite-final/suite-3.xml).

- [Auditoría de consulta](phase5-completion-2026-10-20/read-only-check.json):
  92 registros, 190 cuentas contando originales y copias (40 con detalle guardado,
  150 con resumen), 47 fuentes de consumo. Cero llamadas prohibidas, inferencias,
  backtests o reservas nuevas; 837 archivos controlados conservan sus huellas.
- [Conservación de FASE 4](phase5-completion-2026-10-20/preservation-check.json):
  los 131 archivos anteriores de código y pruebas conservan sus bytes. Tampoco
  cambia ningún informe o evidencia anterior seguido por Git.
- [Comprobación visual](phase5-completion-2026-10-20/visual-check.json): navegador
  Windows, cinco apartados, filtros, fechas próximas al cambio de día, fichas,
  gráficos, comparación admitida/bloqueada, errores y acceso al inventario original.
  Una fuente artificial separada comprueba que script e imagen con manejador se
  muestran literalmente: cero elementos script o img en el contenido de la ficha.
- [Cierre de servidores](phase5-completion-2026-10-20/shutdown-check.json): puertos
  8765 y 8766 cerrados; cero servicios permanentes creados.

La auditoría conserva los estados existentes: 52 copias con integridad comprobada,
23 originales cotejados, ocho registros sin verificación completa y nueve
incompletos. No se corrigen evidencias para cambiar esas etiquetas. El consumo del
ciclo permanece en 2898/180 tokens nuevos y 2262/176 heredados, por separado;
**durante esta fase no se hacen inferencias reales**.

La raíz y rama Git están comprobadas. La primera consulta remota quedó bloqueada
por la red aislada (salida 128). Al preparar la publicación autorizada, una consulta
`git ls-remote` con acceso a red confirma que `origin/main` coincide con HEAD
`f5e654435f42efcb76c53a82f812a541bf78d521`. El resultado del push y el nuevo
identificador se comunican al terminar la publicación.

El [cotejo de publicación](phase5-completion-2026-10-20/git-publication-check.json)
confirma las ocho fuentes nuevas y las evidencias con sus bytes exactos en Git.
Las 139 fuentes de disco coinciden con las utilizadas en las pruebas. Tres fuentes
anteriores ya tenían CRLF en disco y LF en sus blobs de Git: backtesting.py,
metrics.py y test_structured_freshness.py, con el mismo contenido al normalizar
saltos de línea. Se conservan intactos los originales y sus blobs anteriores;
la carpeta [tested-source-bytes](phase5-completion-2026-10-20/tested-source-bytes)
guarda copias de sus bytes probados, con huellas y rutas en el cotejo. Esta
diferencia previa no se presenta como igualdad de bytes entre disco y clon.

## Evidencia visual

- [Inicio](phase5-completion-2026-10-20/home.png).
- [Explorador y fecha local](phase5-completion-2026-10-20/experiments.png).
- [Curva de capital histórica](phase5-completion-2026-10-20/equity.png).
- [Comparación admitida](phase5-completion-2026-10-20/comparison.png) y
  [tramos incompatibles bloqueados](phase5-completion-2026-10-20/incompatible-accounts.png).
- [Memoria y revisión separadas](phase5-completion-2026-10-20/memory.png),
  [consumo heredado](phase5-completion-2026-10-20/inherited-usage.png) y
  [apartado Consumo](phase5-completion-2026-10-20/consumption.png).
- Fuente artificial: [texto seguro](phase5-completion-2026-10-20/artificial-text-safety.png),
  [respuesta literal](phase5-completion-2026-10-20/artificial-model-text.png) y
  [registro ausente](phase5-completion-2026-10-20/artificial-missing-record.png).

## Límites conservados

Los registros históricos sin contabilidad detallada siguen sin curva u operaciones
reconstruidas. Las copias verificadas acreditan integridad de archivos, sin firma
externa, revisión semántica completa o validación independiente de una estrategia.
No se infiere que un proceso siga activo a partir de su último evento.

Los datos del BCE ya se habían explorado. Se conservan el duplicado del modelo,
las reformulaciones consumidas y los resultados temporales negativos. Las cuentas
por ventana y moneda no forman una cuenta continua. El coste desconocido no se
convierte en cero y no se agregan memorias que puedan solaparse.

La comprobación visual utiliza el resultado negativo ya guardado de la primera
ventana: base 0,425809 % de rentabilidad y 1,746293 % de drawdown; EMA19/60,
1,189731 % y 1,914928 %. La candidata aumenta ambas métricas y no cumple el
criterio de mejorar rentabilidad sin mayor drawdown. Las otras ventanas conservan
su selección vacía, sin forzar ganadores. Estas cifras no proceden de una nueva
simulación realizada para la interfaz.

Sin nuevas dependencias, llamadas de pago, lectura de credenciales, modelos nuevos,
operaciones reales o reinicio de presupuestos. TradingView, recepción de eventos y
brókeres corresponden a fases posteriores. **FASE 6 no se inicia**.
