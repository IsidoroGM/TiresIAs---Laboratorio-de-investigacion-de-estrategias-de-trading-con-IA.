# Estado de Trading AI

Última actualización: **19 de octubre de 2026** (Europe/Madrid), cierre de FASE 3.

## Fase activa

**FASES 0, 1, 2 y 3 completadas.** La FASE 2 cerró el motor educativo ampliado:
estrategias SMA/EMA configurables, costes, capital, tamaño de posición,
drawdown, comparaciones y sensibilidad local. La FASE 3 incorpora un investigador
local con Ollama y Qwen3.5:4b, propuestas acotadas, herramientas Python,
conclusiones verificadas y registros de resultados, errores y consumo.
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
- `ai.py`: contrato de proveedores y adaptador Ollama local; OpenAI reservado y desactivado.
- `experiments.py`: validación de propuestas, comparación base/variante y criterios verificables.
- `research.py`: CLI independiente, máximo dos consultas, registro duradero y conclusiones contrastadas.
- `scripts/`: instalación portátil, arranque y parada explícitos de la instancia local.
- `tests/`: **399 pruebas aprobadas**. Temporales de Codex separados según `AGENTS.md`.

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

## Cierre de FASE 3 — Primer investigador local

El usuario eligió un agente local y autorizó la instalación y las comprobaciones
de Ollama con Qwen3.5:4b. La integración usa la biblioteca estándar de Python;
no se añadieron dependencias Python de ejecución. Ollama portátil v0.40.6 se
descarga desde su distribución oficial con SHA-256 fijado. Binarios, modelos,
configuración personal y registros de trabajo quedan excluidos de Git.

| Objetivo | Implementación y comprobación |
|---|---|
| Proponer hipótesis y experimentos | JSON validado; variante SMA/EMA y ventanas limitadas, distinta de la base |
| Usar herramientas controladas | Solo `run_experiment`; el modelo no elige rutas, capital, costes, tamaño ni código |
| Separar IA y cálculos | El motor existente calcula ambas estrategias sobre los mismos datos y supuestos |
| Contrastar conclusiones | Comparaciones y veredicto deben coincidir con el criterio y las cifras calculadas |
| Tratar casos insuficientes | Cero cierres en cualquiera de las estrategias: conclusión inconclusa de Python, sin consulta de análisis |
| Registrar actividad y consumo | JSONL con propuestas, parámetros, respuestas, resultados, errores, tokens, tiempos y hashes |
| Prever futuras APIs | Contrato `ResearchProvider`; opción OpenAI desactivada antes de leer credenciales o abrir conexiones |

Configuración comprobada: CPU, contexto 4096, salida máxima 384 tokens,
temperatura 0, sin razonamiento emitido y sin reintentos automáticos. El servidor
escucha en `127.0.0.1:11435`, con funciones cloud desactivadas; el adaptador bloquea
proxies, redirecciones y destinos remotos. No se inicia ni descarga nada al
ejecutar el investigador. La GPU se descartó por incompatibilidad CUDA/PTX con
el controlador actual; no se modificaron controladores.

Validación de cierre: **399 passed**, caché desactivada y temporal nuevo exclusivo.
Comprobados el arranque del laboratorio, la ayuda del investigador y `--check`
contra el modelo instalado. Las pruebas verifican también que OpenAI se detiene
antes de crear una investigación o abrir la red. No hubo llamadas de pago.

Evidencia conservada:

- [Investigaciones sobre los cuatro pares](../reports/local-agent-check-2026-10-19.md):
  propuestas, cálculos y conclusiones contrastados; una mejora relativa puede seguir teniendo pérdidas.
- [Evaluación aislada del modelo](../reports/local-agent-consistency-2026-10-19.md):
  **4/6 respuestas correctas**. Las dos interpretaciones de historia insuficiente
  fueron incorrectas y se rechazaron; no se borraron ni se reintentaron.
- [Control previo posterior](../reports/local-agent-sufficiency-2026-10-19.md):
  **3/3 flujos correctos**, con una consulta de propuesta y conclusión de Python
  en el caso sin cierres, y dos consultas en los dos casos normales. Tres
  regresiones fallaban antes del cambio y pasan después. Esta comprobación de la
  aplicación no cambia el resultado aislado 4/6 del modelo.

Los informes anteriores conservan su fecha y estado histórico; este documento
registra el cierre posterior autorizado. Los registros identifican la versión
del código y del modelo usada en cada ejecución. El último ajuste de la ayuda
CLI elimina la indicación de fase en desarrollo; no cambia los cálculos.
Se verificaron los enlaces locales y los hashes de las evidencias;
`.gitattributes` conserva sus bytes al clonar, sin convertir finales de línea.

Coste de API registrado en las comprobaciones locales: **0 USD**; siguen
existiendo consumo de electricidad, memoria y tiempo. Una futura API OpenAI
requerirá acordar modelo, credenciales, presupuesto y controles de gasto.
No hay sustitución automática por un proveedor de pago.

Este cierre acredita el primer flujo investigador acotado, no fiabilidad general
de la IA, suficiencia estadística ni rentabilidad. La comprobación de cero
cierres no garantiza que cualquier número positivo sea suficiente. Continúan
pendientes la validación fuera de muestra y la búsqueda controlada de parámetros
de FASE 4. TradingView sigue planificado y sin conexión implementada según
[su plan](TRADINGVIEW_PLAN.md); no hay operaciones con dinero real.

Uso, configuración, instalación y referencias oficiales en
[LOCAL_AI.md](LOCAL_AI.md).

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
| Ollama portátil v0.40.6 y Qwen3.5:4b | Instalados y comprobados en CPU; archivos locales excluidos de Git |
| API OpenAI | Reserva desactivada; sin credenciales ni llamadas facturables |
| Otros frameworks, bases de datos y APIs externas | Pendientes de evaluación cuando sean necesarios |

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
- El primer agente investigador local queda completado en FASE 3; optimización
  y validación fuera de muestra en FASE 4. Las propuestas se verifican con herramientas.
- Mantener Ollama local como proveedor inicial y permitir una futura integración
  OpenAI sin activar pagos ni leer credenciales hasta acordar presupuesto y acceso.
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
Esa autorización correspondió al cierre de FASE 2.

El cierre de FASE 2 quedó publicado en `main` como `f94b867`. Después quedaron
pendientes cambios en README y el nuevo plan de TradingView, conservados e
incluidos junto al desarrollo de FASE 3. Antes de preparar este cierre se
actualizaron las referencias de `origin` y se comprobó la relación con `main`.
El usuario autorizó expresamente cerrar FASE 3, actualizar este documento y
realizar commit y push. El commit usa el mensaje
`feat: close phase 3 local research agent`; su identificador y el resultado
del push se comunican al finalizar. Futuros commits y pushes requieren nueva autorización.

## Asuntos pendientes y observaciones

- El BCE es la fuente educativa aprobada; faltan datos ejecutables y validación
  del calendario. Los cruces respecto al euro son referencias derivadas.
- Hay costes proporcionales hipotéticos; faltan spreads, slippage, swaps,
  financiación y restricciones de negociación verificadas para un bróker real.
- La sensibilidad reutiliza el histórico completo; faltan separación de datos,
  validación fuera de muestra, walk-forward y análisis de cambios simultáneos.
- El investigador local está disponible; su fiabilidad general sigue sin
  demostrarse. No hay paper trading en tiempo real, interfaz gráfica ni conexión
  con un bróker. No se han elegido parámetros ganadores.
- TradingView: Pine, gráficos, consultas, alertas e importaciones al simulador
  continúan pendientes de implementación; no se activa esa conexión en este cierre.
- En una captura se observó un comando de creación de `.venv` ejecutado desde el
  directorio personal. Puede existir un entorno adicional allí; no se ha
  inspeccionado ni eliminado. El entorno del proyecto sí está comprobado.
- La depuración desde el editor todavía no se ha probado.

## Próximo paso propuesto

Primera tarea de FASE 4: definir y comprobar una separación cronológica entre
datos de desarrollo y de evaluación, con una frontera explícita y sin que el
agente consulte el bloque reservado para proponer cambios. Después, comparar una
propuesta fijada contra la base con los mismos supuestos, registrando resultados
dentro y fuera de muestra. La selección de ventanas no debe reutilizar el bloque
reservado. El histórico completo ya se exploró en fases anteriores: una partición
posterior de esta copia sirve para verificar el procedimiento, no constituye
evidencia totalmente inédita. El primer paso será acordar ese protocolo.

La FASE 4 no se inicia con este cierre. No se añaden dependencias, credenciales
ni conexiones externas; las decisiones adicionales se acordarán cuando proceda.

Por indicación del usuario, actualizar este documento únicamente al terminar
una fase, no después de cada tarea. Registrar resultados comprobados y las
limitaciones que sigan pendientes. Esta regla sustituye la frecuencia anterior.
