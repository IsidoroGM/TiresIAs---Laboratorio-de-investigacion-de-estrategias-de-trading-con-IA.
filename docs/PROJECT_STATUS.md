# Estado de Trading AI

Última actualización: **19 de octubre de 2026** (Europe/Madrid), cierre de FASE 2.

## Fase activa

**FASES 0, 1 y 2 completadas.** La FASE 2 cierra el motor educativo ampliado:
estrategias SMA/EMA configurables, costes, capital, tamaño de posición,
drawdown, comparaciones y sensibilidad local. La FASE 3 (primer agente de IA)
está pendiente de seleccionar proveedor/modelo y acordar la primera integración.
Las fases 4 a 8 siguen pendientes; la fase 8 de ejecución real supervisada es opcional.

Completar esta fase significa cumplir su alcance de desarrollo, no demostrar
que las estrategias sean rentables o aptas para operar con dinero real.

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
- `trading_ai/__main__.py`: CLI con modos excluyentes `--report`, `--compare` y
  `--sensitivity`; ventanas, costes, capital, asignación y archivos configurables.
- `data.py`: lector local del XML BCE para EUR/USD, GBP/USD, USD/JPY y USD/CHF.
- `indicators.py`: SMA y EMA (semilla SMA, alfa 2/(n+1)), sin información futura.
- `strategies.py`: contrato `Strategy`, implementaciones inmutables SMA/EMA y
  selección explícita; cruces alcistas para comprar y bajistas para cerrar.
- `backtesting.py`: ejecución en la referencia siguiente, costes proporcionales,
  cuenta independiente por par, saldo limitado, tamaño fijo o porcentaje del
  efectivo, curva diaria, drawdown y valoración de posiciones abiertas sin cierre forzado.
- `metrics.py`: métricas de cierres, moneda cotizada y valores no disponibles.
- `reporting.py`: informes individuales y comparación SMA/EMA deterministas,
  con hash de datos, supuestos y protección contra sobrescrituras.
- `sensitivity.py`: variaciones fijas de un factor cada vez, omisiones explícitas
  de escenarios inválidos y cambios frente a la base; sin búsqueda de parámetros.
- `tests/`: **343 pruebas aprobadas**. Temporales de Codex separados según `AGENTS.md`.

Comprobaciones de cierre de FASE 1:

- Copia BCE `data/raw/ecb-eurofxref-hist-2026-10-18.xml`, 7.116 fechas compartidas
  por los cuatro pares, de 1999-01-04 a 2026-10-16. Procedencia y SHA-256 en `data/README.md`.
- Fechas y referencias necesarias válidas, sin duplicados; calendario completo
  de publicación todavía no contrastado.
- Pruebas de conversiones, medias, señales, ejecución posterior, métricas,
  errores y estabilidad de resultados pasados frente a datos futuros.
- Se conserva `reports/phase1.md` como informe histórico de cierre de FASE 1.
  El código actual usa por defecto `reports/report.md`; elegir otra salida al
  cambiar formato o supuestos. Contenido idéntico permite repetir el comando;
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

## Cierre de FASE 2 — Motor de estrategias ampliado

| Objetivo del plan | Implementación y comprobación |
|---|---|
| Interfaz común para estrategias | `Strategy`: nombre y generación de señales; SMA/EMA sin estado entre llamadas |
| Nuevos indicadores | EMA con semilla explícita, recurrencia conocida y pruebas de causalidad |
| Configuraciones | Selección SMA/EMA; ventanas positivas rápida < lenta; costes, capital y tamaño validados |
| Comparar estrategias | `--compare` ejecuta ambas con los mismos datos y supuestos por par |
| Mejorar costes y simulación | Costes por compra/venta, cuentas, cantidades fraccionarias, presupuesto, curva y drawdown |
| Introducir pruebas de robustez | `--sensitivity`: ±1 observación y ±0.05 pp de coste, un factor cada vez |

Validación de cierre: **343 passed**, sin caché pytest y con una carpeta temporal
nueva y exclusiva. Los cuatro informes siguientes se recalcularon y coincidieron
íntegramente con su contenido guardado:

- [SMA20/60](../reports/sma20-60-allocation10.md).
- [EMA20/60](../reports/ema20-60-allocation10.md).
- [Comparación](../reports/comparison20-60-allocation10.md).
- [Sensibilidad](../reports/sensitivity20-60-allocation10.md).

Supuestos comunes: copia BCE de 7.116 observaciones, ventanas base 20/60,
capital inicial 1000 en cada moneda cotizada, coste 0.1 % por ejecución y
asignación del 10 % del efectivo, incluyendo costes. La sensibilidad ejecuta
56 escenarios (7 por estrategia y par) y conserva el mismo histórico.

Resultados base de la comparación, con costes y posiciones abiertas incluidos:

| Par | Capital final SMA | Capital final EMA |
|---|---:|---:|
| EUR/USD | 1015.009331 USD | 1013.740017 USD |
| GBP/USD | 977.844806 USD | 998.897874 USD |
| USD/JPY | 1029.441001 JPY | 1026.320534 JPY |
| USD/CHF | 930.922718 CHF | 950.072500 CHF |

GBP/USD con EMA cambia de signo entre escenarios: rentabilidad acumulada
de -0.667648 % a +0.450857 %. No hay un ganador uniforme. Sensibilidad local
no equivale a validación fuera de muestra ni a robustez demostrada.

Se resolvieron los restos de conflictos de Git en código y README durante
el desarrollo y los de este documento al cerrar la fase. No se añadieron
dependencias de ejecución, APIs, credenciales ni conexiones a un bróker.

Repaso general solicitado por el usuario: revisados lectura y validación de datos,
causalidad de indicadores/señales, ejecución posterior, contabilidad, límites de
saldo, costes, tamaño, métricas, CLI, informes y continuidad de la documentación.
Se encontró y corrigió una dependencia del redondeo mostrado respecto al contexto
Decimal externo. Tres regresiones fallaban antes del arreglo y pasan después;
los resultados y los cuatro informes guardados conservan su contenido habitual.

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
- EUR/USD, GBP/USD, USD/JPY y USD/CHF diarios; SMA/EMA educativas, 20/60 por defecto.
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

El identificador y el contenido de los commits se consultan mediante `git log` y
`git show`. Antes del commit de cierre, HEAD era `03ca414`, una integración previa
de `main`; también constan `75de89f` y `d85eebb`. La revisión de `origin/main`
confirmó que no había commits pendientes de integrar al preparar el cierre.
El entorno virtual permanece en disco y está excluido del seguimiento.
El usuario autorizó explícitamente el commit y push de este cierre a GitHub.
El commit de cierre usa el mensaje `feat: close phase 2 strategy research engine`;
su identificador y la confirmación del push se comunican al finalizar la tarea.
Esta autorización corresponde al cierre actual; futuros commits requieren nueva autorización.

## Asuntos pendientes y observaciones

- El BCE es la fuente educativa aprobada; faltan datos ejecutables y validación
  del calendario. Los cruces respecto al euro son referencias derivadas.
- Hay costes proporcionales hipotéticos; faltan spreads, slippage, swaps,
  financiación y restricciones de negociación verificadas para un bróker real.
- La sensibilidad reutiliza el histórico completo; faltan separación de datos,
  validación fuera de muestra, walk-forward y análisis de cambios simultáneos.
- No hay agentes, acceso a modelos, paper trading en tiempo real, interfaz
  gráfica ni conexión con un bróker. No se han elegido parámetros ganadores.
- En una captura se observó un comando de creación de `.venv` ejecutado desde el
  directorio personal. Puede existir un entorno adicional allí; no se ha
  inspeccionado ni eliminado. El entorno del proyecto sí está comprobado.
- La depuración desde el editor todavía no se ha probado.

## Próximo paso propuesto

Primera tarea de FASE 3: acordar proveedor, modelo y presupuesto de uso del
agente investigador. Revisar documentación oficial vigente antes de recomendar
una integración. Después, configurar acceso seguro y herramientas Python
limitadas a los experimentos reproducibles existentes, registrando propuestas,
errores y costes. La decisión del modelo no sustituirá a los cálculos.

Las dependencias, credenciales y llamadas externas se acordarán en esa tarea;
el cierre actual solo prepara la continuidad y no activa un servicio de IA.

Por indicación del usuario, actualizar este documento únicamente al terminar
una fase, no después de cada tarea. Registrar resultados comprobados y las
limitaciones que sigan pendientes. Esta regla sustituye la frecuencia anterior.
