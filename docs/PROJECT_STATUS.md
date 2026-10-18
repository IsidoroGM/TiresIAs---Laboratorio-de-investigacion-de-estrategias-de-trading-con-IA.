# Estado de Trading AI

Última actualización: **18 de octubre de 2026** (Europe/Madrid).

## Fase activa

**FASE 0 — Preparación y fundamentos.** Ninguna fase completa se ha dado por
terminada. Las fases 1 a 8 siguen pendientes; la fase 8, dedicada a evaluar una
posible ejecución real supervisada, es opcional.

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
- `trading_ai/__main__.py`: función `main() -> None` que muestra la presentación
  del laboratorio; su llamada está protegida por la condición de ejecución directa.

Todavía no hay lógica de mercado, tests automatizados persistentes ni carpeta
`tests/`. No se han generado datos de mercado, resultados de backtesting ni
operaciones.

La arquitectura propuesta es un monolito modular. La separación entre datos,
indicadores, señales, gestión de posiciones, simulación y análisis se incorporará
progresivamente, tras aprobar cada tarea.

## Herramientas y dependencias

| Elemento | Estado |
|---|---|
| Python 3.14.8 de 64 bits | Instalado y comprobado |
| `venv` | Módulo de la biblioteca estándar; entorno `.venv` creado |
| `pip` 26.2.1 | Único paquete instalado en `.venv` al verificar esta tarea |
| VS Code y extensiones Python | Disponibles; terminal del proyecto comprobada |
| Git | Repositorio local inicializado |
| Pandas y NumPy | Previstos para datos y cálculos; no instalados |
| pytest | Previsto para pruebas; no instalado |
| Frameworks, bases de datos y APIs externas | Pendientes de evaluación cuando sean necesarios |

La compatibilidad documentada de Pandas, NumPy y pytest con Python 3.14 fue
revisada antes de elegir la versión. Sus versiones concretas y su funcionamiento
conjunto se comprobarán cuando se apruebe instalarlos.

## Decisiones acordadas

- Aprendizaje práctico y tareas pequeñas: explicación, propuesta, aprobación,
  implementación, pruebas y revisión. Detenerse al terminar cada tarea.
- Consultar cambios de arquitectura, dependencias, proveedores y alcance.
- Usar inicialmente el paquete `trading_ai` en la raíz (estructura plana) para
  ejecutarlo desde el proyecto sin configurar su instalación como paquete.
- Mantener el arranque en `__main__.py` y evitar que importar el paquete ejecute
  la función de inicio. Incorporar `tests/` y pytest con la primera lógica que
  necesite pruebas automatizadas, en una tarea aprobada aparte.
- Empezar por EUR/USD D1, swing trading y una estrategia didáctica SMA20/SMA60.
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

El primer punto de control local aprobado reúne estos cinco archivos:
`.gitignore`, `README.md`, `docs/PROJECT_STATUS.md`, `trading_ai/__init__.py` y
`trading_ai/__main__.py`. El mensaje acordado es:

```text
chore: preparar base inicial de Trading AI
```

El identificador y el contenido del commit se consultan mediante `git log` y
`git show`. No hay remotos configurados. El entorno virtual permanece en disco
y está excluido del seguimiento. Los futuros commits requieren nueva aprobación.

## Asuntos pendientes y observaciones

- Elegir la fuente de datos. El BCE es una posibilidad educativa, no un proveedor
  de precios ejecutables para validar una estrategia real.
- En una captura se observó un comando de creación de `.venv` ejecutado desde el
  directorio personal. Puede existir un entorno adicional allí; no se ha
  inspeccionado ni eliminado. El entorno del proyecto sí está comprobado.
- La depuración desde el editor todavía no se ha probado.

## Próximo paso propuesto

Revisar el cierre de la FASE 0 y presentar la primera tarea de la FASE 1:
seleccionar una fuente de datos educativos EUR/USD D1, explicando su significado
y limitaciones. La selección del proveedor y cualquier implementación posterior
requieren aprobación antes de comenzar.

Actualizar este documento al finalizar tareas aprobadas, reflejando únicamente
resultados comprobados y señalando las limitaciones que sigan pendientes.
