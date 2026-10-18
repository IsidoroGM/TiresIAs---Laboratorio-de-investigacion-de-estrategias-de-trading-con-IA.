# Estado de Trading AI

Última actualización: **18 de octubre de 2026** (Europe/Madrid).

## Fase activa

**FASES 0 y 1 completadas.** La FASE 1 termina con datos, validación básica,
SMA20/SMA60, señales, backtest educativo, métricas e informe reproducible.
La FASE 2 está pendiente de proponer y aprobar su primera tarea. Las fases 3 a 8
siguen pendientes; la fase 8 de ejecución real supervisada es opcional.

El objetivo y el alcance inicial se describen en el [README](../README.md).

## Tareas comprobadas

- Revisión inicial del directorio y de las herramientas disponibles.
- Actualización de Python de 3.14.3 a 3.14.8 de 64 bits mediante el instalador
  oficial, con hash y firma verificados. No fue necesario reiniciar.
- Creación de `.venv` y comprobación del aislamiento respecto a paquetes globales
  y del usuario. El ejecutable y `pip` pertenecen al entorno del proyecto.
- Comprobación por el usuario de Python 3.14.8 y la ruta de `.venv` desde la
  terminal integrada de VS Code, utilizando PowerShell.
- Inicialización del repositorio Git propio del proyecto, con rama inicial `main`.
- Creación y comprobación de `.gitignore`: excluye el entorno, cachés y archivos
  `.env`, y permite una futura plantilla `.env.example` sin secretos.
- Creación y revisión del README y este documento. Se comprobaron los enlaces
  relativos, los comandos de activación y verificación en PowerShell, y la
  ejecución directa del intérprete del proyecto.
- Creación del paquete `trading_ai`, con `__init__.py` y `__main__.py`. Se comprobó
  el arranque mediante `python -m trading_ai`, la importación del paquete y del
  módulo de entrada sin salida, y la carga del código local desde `.venv`.
- El usuario reprodujo desde la terminal integrada de VS Code el arranque con
  las dos líneas previstas y la importación sin mensajes. Ambos comportamientos
  quedaron confirmados en su captura.

## Arquitectura actual

El proyecto contiene la configuración de Git, documentación, un entorno virtual
local y el paquete `trading_ai` en la raíz del repositorio.

- `trading_ai/__init__.py`: descripción del paquete convencional.
- `trading_ai/__main__.py`: CLI con `--report`, `--data` y `--output`.
- `data.py`: lector local del XML BCE para EUR/USD, GBP/USD, USD/JPY y USD/CHF.
- `indicators.py`: SMA con valores iniciales `None`, sin información futura.
- `strategies.py`: señales de cruce alcista para comprar y bajista para cerrar.
- `backtesting.py`: una unidad base por operación, ejecución en la referencia
  siguiente, costes cero y posición abierta conservada al finalizar.
- `metrics.py`: métricas de cierres, moneda cotizada y valores no disponibles.
- `reporting.py`: informe Markdown determinista, con hash de datos y supuestos.
- `tests/`: 165 pruebas aprobadas. Temporales de Codex separados según `AGENTS.md`.

Comprobaciones de cierre de FASE 1:

- Copia BCE `data/raw/ecb-eurofxref-hist-2026-10-18.xml`, 7.116 fechas compartidas
  por los cuatro pares, de 1999-01-04 a 2026-10-16. Procedencia y SHA-256 en `data/README.md`.
- Fechas y referencias necesarias válidas, sin duplicados; calendario completo
  de publicación todavía no contrastado.
- Pruebas de conversiones, medias, señales, ejecución posterior, métricas,
  errores y estabilidad de resultados pasados frente a datos futuros.
- `python -m trading_ai --report` genera `reports/phase1.md`; revisado contra
  los resultados calculados. Contenido idéntico permite repetir el comando;
  un archivo distinto ya existente no se sobrescribe.
- Cierres: EUR/USD 69, GBP/USD 70, USD/JPY 67, USD/CHF 70; queda una posición
  USD/CHF abierta. Resultados educativos sin costes, no operaciones reales.
- Importar el paquete y su entrada sigue sin imprimir ni ejecutar el informe.
- Incidente de permisos pytest resuelto: carpetas creadas por la identidad
  aislada impedían las pruebas del usuario. Permisos reparados y verificados
  con su cuenta; las ejecuciones aisladas usan temporales propios y caché desactivada.

La arquitectura propuesta es un monolito modular. La separación entre datos,
indicadores, señales, gestión de posiciones, simulación y análisis se incorporará
progresivamente, tras aprobar cada tarea.

## Herramientas y dependencias

| Elemento | Estado |
|---|---|
| Python 3.14.8 de 64 bits | Instalado y comprobado |
| `venv` | Módulo de la biblioteca estándar; entorno `.venv` creado |
| `pip` 26.2.1 | Disponible en `.venv` |
| VS Code y extensiones Python | Disponibles; terminal del proyecto comprobada |
| Git | Repositorio local inicializado |
| Pandas y NumPy | Previstos para datos y cálculos; no instalados |
| pytest 9.1.1 | Instalado con dependencias auxiliares; declarado en `requirements-dev.txt` |
| Frameworks, bases de datos y APIs externas | Pendientes de evaluación cuando sean necesarios |

El código de aplicación solo usa la biblioteca estándar. pytest funciona con
Python 3.14.8. Pandas y NumPy siguen pendientes de aprobación si llegan a necesitarse.

## Decisiones acordadas

- Aprendizaje práctico y tareas pequeñas: explicación, propuesta, aprobación,
  implementación, pruebas y revisión. Detenerse al terminar cada tarea.
- Consultar cambios de arquitectura, dependencias, proveedores y alcance.
- Usar inicialmente el paquete `trading_ai` en la raíz (estructura plana) para
  ejecutarlo desde el proyecto sin configurar su instalación como paquete.
- Mantener el arranque en `__main__.py` sin efectos al importar; pruebas con pytest.
- EUR/USD, GBP/USD, USD/JPY y USD/CHF diarios; SMA20/SMA60 educativa.
- El agente investigador está previsto en FASE 3; optimización y validación
  fuera de muestra en FASE 4. Las propuestas se verificarán con herramientas.
- Comunicación concisa, menos actualizaciones informativas y lecturas repetidas,
  según preferencia del usuario para reducir consumo de tokens.
- Mantener cálculos y reglas reproducibles, separados de las propuestas del LLM.
- Permitir en el futuro seleccionar entre backtesting, paper trading y ejecución
  real supervisada. La ejecución real requiere validación y nueva autorización.
- Mantener el motor de riesgo independiente de la IA y sus límites bajo control
  humano. La confianza del agente no demuestra la viabilidad de una estrategia.
- Conservar el trabajo existente y consultar antes de eliminar archivos,
  realizar commits o hacer pushes.

## Situación de Git

El repositorio propio está en la raíz de Trading AI. Existe otro repositorio en la
carpeta superior que incluye otros proyectos. Antes de operar con Git, comprobar
que `git rev-parse --show-toplevel` apunta a Trading AI.

Al inicializar el repositorio propio se comprobó que el índice, HEAD y la
configuración del repositorio superior no cambiaron. No modificar ni reorganizar
ese repositorio como parte de este proyecto.

La ruta exacta de Trading AI se registró en `safe.directory` de la configuración
global de Git del usuario habitual de Windows. Esta excepción permite utilizar
el repositorio cuyo directorio `.git` fue creado por el usuario de la sesión aislada.

El primer commit local aprobado, `12c2da4`, reúne estos cinco archivos:
`.gitignore`, `README.md`, `docs/PROJECT_STATUS.md`, `trading_ai/__init__.py` y
`trading_ai/__main__.py`. Su mensaje es:

```text
chore: preparar base inicial de Trading AI
```

El identificador y el contenido del commit se consultan mediante `git log` y
`git show`. No hay remotos configurados. El entorno virtual permanece en disco
y está excluido del seguimiento. Los futuros commits requieren nueva aprobación.
Al cierre también consta el commit `638028f` (`feat: implement backtesting
framework with educational focus`). Los cambios del informe y la documentación
de cierre siguen sin commit. Esta tarea no ha realizado commits ni pushes.

## Asuntos pendientes y observaciones

- El BCE es la fuente educativa aprobada; faltan datos ejecutables y validación
  del calendario. Los cruces respecto al euro son referencias derivadas.
- Faltan costes, cuenta de capital, curva de capital, drawdown, valoración de
  posiciones abiertas y validación fuera de muestra. No hay agentes ni bróker.
- En una captura se observó un comando de creación de `.venv` ejecutado desde el
  directorio personal. Puede existir un entorno adicional allí; no se ha
  inspeccionado ni eliminado. El entorno del proyecto sí está comprobado.
- La depuración desde el editor todavía no se ha probado.

## Próximo paso propuesto

Proponer la primera tarea de FASE 2: configuración explícita de ventanas y
supuestos para comparar estrategias, seguida de costes y mayor realismo de
simulación. Acordar el alcance de esa tarea antes de implementarla.

Por indicación del usuario, actualizar este documento únicamente al terminar
una fase, no después de cada tarea. Registrar resultados comprobados y las
limitaciones que sigan pendientes. Esta regla sustituye la frecuencia anterior.
