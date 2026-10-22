# Estado de TiresIAs

Última actualización: **21 de octubre de 2026** (Europe/Madrid), cierre de FASE 5.2.

## Fase activa

**FASES 0, 1, 2, 3, 4, 5, 5.1 y 5.2 completadas.** La FASE 2 cerró el motor educativo ampliado:
estrategias SMA/EMA configurables, costes, capital, tamaño de posición,
drawdown, comparaciones y sensibilidad local. La FASE 3 incorpora un investigador
local con Ollama y Qwen3.5:4b, propuestas acotadas, herramientas Python,
conclusiones verificadas y registros de resultados, errores y consumo.
La FASE 4 incorpora separación cronológica, registro previo, evaluación histórica,
sensibilidad, selección interna, walk-forward descriptivo y un ciclo local acotado
con memoria y controles. La FASE 5 incorpora la interfaz local de consulta de
experimentos, resultados, memoria, consumo y capital virtual. La FASE 5.1 mejora
su rendimiento mediante un índice en memoria con actualización y lectores por
petición, conservando los controles de integridad. La FASE 5.2 añade conversación
local persistente, propuestas revisables y pruebas históricas explícitas, con
presupuesto compartido y evidencias enlazadas. Las fases 6 a 8
siguen pendientes; la fase 8 de ejecución
real supervisada es opcional. El nombre actual es **TiresIAs - Laboratorio de
investigación de estrategias de trading con IA**; el paquete `trading_ai` y la
carpeta original se conservan por compatibilidad.

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
- `lab_catalog.py` y `lab_query.py`: catálogo acotado y contratos de lectura, procedencia,
  copias históricas, integridad de archivos y cuentas guardadas sin recalcular.
- `lab.py` y `lab_static/`: interfaz local en español con seis apartados, filtros,
  fichas, gráficos, operaciones, comparación compatible y fuentes originales;
  servidor explícito en `127.0.0.1`; cinco pantallas de consulta y acciones
  autenticadas de conversación, revisión y prueba histórica en la sexta.
- `conversation.py`: sesiones, mensajes, revisiones y trabajos persistentes,
  reserva compartida, cola acotada, recuperación e integración con el backtest.
- `conversation_provider.py`: contrato conversacional local independiente del
  ciclo de campañas, sin recortes de contexto, descargas o reintentos automáticos.
- `lab_service.py`: índice de consulta en memoria, actualizaciones por generación,
  frescura visible, caché de metadatos acotada y contextos de lectura independientes.
- `scripts/`: instalación portátil, arranque y parada explícitos de la instancia local.
- `scripts/check_lab_readonly.py`: auditoría explícita con proveedores, red,
  simulaciones, diarios y reservas bloqueados durante la consulta.
- `scripts/benchmark_lab.py`: medidas HTTP reproducibles y referencia de FASE 5
  desde Git local, sin modificar el checkout.
- `tests/`: **1598 aprobadas** en la colección completa del cierre de FASE 5;
  **128 específicas aprobadas** en FASE 5.1 (80 de interfaz y 48 de evidencias/registro).
  FASE 5.2 comprueba **267 pruebas de los componentes afectados**, con 46 nuevas.
  Colección actual: **1673 nodos**, incluidos los 1598 anteriores, 29 de FASE 5.1
  y 46 de FASE 5.2. No se ejecutó completa en estas mejoras. `pytest.ini` delimita
  `tests` para excluir copias archivadas en informes. Temporales según `AGENTS.md`.

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

## Cierre de FASE 4 — Validación y ciclo de investigación acotado

Se cierra el alcance de desarrollo educativo, sin afirmar rentabilidad, suficiencia
estadística o validación independiente. La división de datos ya explorados permite
comprobar el procedimiento; no los convierte en inéditos.

| Objetivo | Implementación y comprobación |
|---|---|
| Separar desarrollo y evaluación | Frontera 2020-01-01 elegida por el usuario, datos y manifiestos con huellas |
| Registrar antes de evaluar | Propuesta, criterio y controles congelados; acceso exclusivo y sin reintento |
| Comparar con controles constantes | Motor existente, cuentas y calentamiento independientes, ejecución posterior |
| Sensibilidad y selección interna | Ventanas/costes predefinidos, selección anterior a comprobación y descartes conservados |
| Ampliar reglas | Vocabulario tipado causal con retardos y revisión separada; nunca código libre del modelo |
| Incorporar memoria | Historial completo, errores, consumo y resultados; diccionario reversible sin recortes |
| Ciclo local acotado | Transporte local identificado, presupuesto compartido, revisión mecánica, cálculos y memoria separados |
| Walk-forward | Tres ventanas expansivas, selección solo en entrenamiento y sin ganador forzado |
| Verificar y preservar | Colección completa aprobada, fuentes estables y evidencias anteriores intactas |

La ruta nueva `campaign_cycle` es un contrato de **experimentos virtuales sobre
reglas tipadas cerradas**. Su revisión mecánica no acredita comprensión semántica
humana y no adopta estrategias. Los permisos y revisiones manuales v1 conservan
su alcance; no se simulan sus propuestas pendientes. El modelo no decide datos,
capital, coste, tamaño, permisos o código ejecutable. Duplicados, errores, contexto
insuficiente o consumo desconocido detienen el ciclo, sin reintentos automáticos.

El registro admite tres propuestas y seis backtests. La habilitación nueva exige
un permiso y opciones explícitas; el registro contable por sí solo permanece
inactivo y no concede ejecución. La reserva de ciclo es exclusiva por ámbito y
no se libera cambiando carpeta. Se usa Ollama 0.40.6, Qwen3.5:4b en CPU, contexto
4096 y salida 384, sin recortes, proxies o destinos remotos. El esquema fijo se
guarda por huella y se transmite íntegro. Los presupuestos heredados no se reinician.

Comprobación local real: una consulta nueva, 2898 tokens de entrada y 180 de salida,
seis consultas de metadatos y **0 USD API**. La respuesta repitió una identidad
conocida: `duplicate_rules`, rechazada antes de simular. No hubo reintento ni
estrategia nueva aceptada. Quedan dos huecos de propuestas y seis de backtests en
el registro, sin reabrir automáticamente el ciclo. El ámbito compacto heredado
2262/176 tokens y 0 USD se conserva aparte; no se presenta como consumo total.

El walk-forward parte de la EMA20/60 previamente congelada y sus variaciones
mecánicas ±1, con un máximo independiente de 24 backtests y cero consultas IA.
Se ejecutaron **20 backtests**: EMA19/60 fue elegida en el primer entrenamiento,
pero incumplió el criterio en comprobación al aumentar también el drawdown.
Las otras dos ventanas quedaron sin elegible y no forzaron una comparación.
La selección se sincroniza antes del cálculo de comprobación; no se reelige al
ver sus resultados. Las cuentas son independientes y no se compone una curva
ficticia. El protocolo usa desarrollo conocido, sin afirmar prueba inédita.

Verificación de cierre: **1547 aprobadas**, distribuidas en 459, 575 y 513 casos
sin omisiones o duplicados frente a la colección prevista. Tiempos por proceso:
998,22 s, 1194,79 s y 1075,35 s; se ejecutaron en paralelo, no se suman como duración
transcurrida. Caché pytest desactivada, temporales nuevos exclusivos y 131 archivos
de código/pruebas sin cambios durante la revisión. Las 31 pruebas nuevas incluyen
integración completa sobre fuentes artificiales, motor real y transporte simulado.

La auditoría final `3f5f81a4fbf04bbcb7b0894c14a899aa` verifica las 332 copias y
referencias anteriores y añade 98: **430 entre 25 inventarios concretos**, no
archivos físicos únicos. El sellado no consulta modelos o recalcula backtests.
La comprobación real no accede a evaluación exterior, no realiza conexiones fuera
del servidor local y conserva límites, controles e intentos históricos.

- [Informe de cierre y evidencias](../reports/phase4-completion-2026-10-20.md).
- [Guía del ciclo y walk-forward](PHASE4_COMPLETION.md).
- [Protocolo cronológico y sus límites](VALIDATION_PLAN.md).

No se instalaron dependencias, descargaron modelos o iniciaron servicios nuevos.
Se reutilizó el servidor local existente. OpenAI, TradingView y el bróker siguen
sin habilitarse. No hubo operaciones reales, commits o pushes. HEAD se conserva
en `3d0fa83` con todos los cambios previos y nuevos pendientes en el directorio.

## Cierre de FASE 5 — Interfaz local de consulta

Interfaz completada y comprobada visualmente en Windows: Inicio, Experimentos,
Resultados, Memoria del agente y Consumo. Permite encontrar un experimento,
entender sus controles, revisar cuentas virtuales y llegar a los archivos,
informes e inventarios originales. Conserva por separado respuestas del modelo,
descripciones y conclusiones de Python, errores, descartes y pendientes.

Arranque desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.lab
```

Abrir `http://127.0.0.1:8765` y cerrar con Ctrl+C en la terminal. No necesita
Ollama, dependencias nuevas o servicios permanentes. Los servidores utilizados
para comprobar la interfaz quedaron cerrados y sus puertos libres.

Los gráficos y operaciones usan exclusivamente la contabilidad guardada. Los
formatos antiguos sin detalle permanecen como resúmenes, sin reconstruir curvas.
Se mantienen separadas cuentas, tramos y monedas; no se suman capitales ni se
componen rentabilidades. El comparador explica las diferencias que bloquean una
comparación. La fecha del filtro coincide con el día local mostrado en pantalla.

La procedencia distingue registros locales, copias archivadas y consulta vigente
del registro contable SQLite, abierto en modo de solo lectura. Comprobar una huella
acredita integridad de archivos, no rentabilidad, autoría externa o revisión
semántica completa. Los registros incompletos y sin verificación conservan ese
estado; no se presentan como resultados certificados o procesos activos.

Auditoría de consulta: 92 registros y 190 cuentas contando originales y copias
(40 con detalle guardado y 150 con resumen), 47 fuentes de consumo; 837 archivos
controlados conservan sus huellas. Cero llamadas prohibidas, inferencias,
simulaciones o reservas nuevas. El ciclo conserva `duplicate_rules`, 2898/180 tokens
nuevos y 2262/176 heredados, por separado. No se reabre la reformulación consumida
ni se cambian presupuestos. Los resultados temporales negativos permanecen intactos.

Colección completa: **1598 aprobadas**, sin fallos, errores o saltos, en tres
procesos aislados de 510, 575 y 513 casos. Tiempos JUnit: 1235,329 s, 1399,702 s
y 1285,328 s; ejecución paralela, sin sumar esos tiempos como duración transcurrida.
El cotejo confirma coincidencia exacta de la colección y 139 archivos de código,
pruebas y recursos web estables durante la revisión. Caché pytest desactivada y
temporal GUID nuevo y exclusivo por proceso, según AGENTS.md.

La primera colección se detuvo antes de corregir el filtro UTC/local; sus logs
parciales no se cuentan como aprobados. Después se repitió toda la colección
sobre la versión final. Las 51 pruebas nuevas cubren comportamiento e integración,
alteraciones, formatos guardados, cuentas, consumo desconocido, rutas y HTTP.
La revisión visual añade filtros combinados, gráficos, comparaciones, trazabilidad,
errores y contenido artificial con etiquetas mostrado como texto inerte.

Los 131 archivos anteriores de código y pruebas conservan sus bytes. No cambia
ningún informe o evidencia anterior seguido por Git. Inicio limpio en `main`,
HEAD `f5e654435f42efcb76c53a82f812a541bf78d521`. Tras las comprobaciones, el usuario
autoriza expresamente publicar este cierre con commit y push. La consulta remota
de publicación mediante `git ls-remote` confirma ese mismo punto de partida en
`origin/main`; el nuevo identificador y el resultado del push se comunican al terminar.

- [Informe, pruebas y capturas](../reports/phase5-completion-2026-10-20.md).
- [Guía de arranque, cierre y pantallas](LAB_INTERFACE.md).
- [Plan y contratos de lectura](PHASE5_PLAN.md).
- [Objetivos y criterios de cierre de FASES 6, 7 y 8](NEXT_PHASES.md).

Este cierre cumple el alcance de software de consulta; no convierte los datos
conocidos en una validación inédita ni demuestra rentabilidad. No se instalan
dependencias, leen credenciales o activan APIs de pago. TradingView y brókeres
siguen pendientes. **FASE 6 no se inicia**.

## Cierre de FASE 5.1 — Rendimiento y fluidez

Índice de resúmenes en memoria, actualizado por cambios cada dos segundos mientras
hay consultas; una actualización en curso y publicación atómica. Los listados
conservan filtros, fecha de lectura y avisos de error. Actualizar fuentes fuerza
una lectura nueva. Las fichas, cuentas y originales siguen leyendo sus bytes
actuales; la consulta vigente de SQLite mantiene una conexión propia de solo lectura.

Cada petición conserva su presupuesto y avisos, reutilizando bytes y detalle
dentro de la consulta. Escaneo con menos validaciones repetidas y controles actuales
antes de abrir archivos. Servidor con cuatro hilos y cola acotada, cancelación en
el navegador, carga independiente de cuentas y ETag en HTML/CSS/JavaScript. Datos
y originales conservan no-store. Sin dependencias o servicios externos nuevos.

Con 92 registros y 805 archivos catalogados, 30 muestras HTTP por pantalla y el
índice preparado: medianas de 1,98 ms en Inicio, 2,33 ms en Experimentos y 2,18 ms
en Consumo; p95 de 19,38, 22,66 y 15,29 ms. Referencia previa: 3155,18, 3196,91
y 2426,35 ms de mediana. Primera consulta nueva: 2,402 s, sin controlar la caché
del sistema operativo. El navegador registra observaciones de 8,9–37,6 ms en
listados; esos tiempos incluyen petición y construcción del DOM, no pintado físico.
Las comprobaciones completas de copias archivadas conservan su coste explícito.

128 pruebas aprobadas y colección exacta de 1627 nodos sin errores. Auditoría de
838 fuentes sin cambios, 92 registros, 40 cuentas detalladas y 150 con resumen;
cero inferencias, simulaciones, reservas o escrituras desde la consulta. Estados
históricos conservados. Adición artificial visible por HTTP en 2,170 s con el
intervalo predeterminado. Los 131 archivos previos del motor y sus pruebas siguen
intactos, al igual que las evidencias anteriores seguidas por Git.

Se conservan los pases fallidos como diagnósticos. Se corrigieron las diferencias
de ctime de Windows y el cierre TCP ante saturación. El descubrimiento de pytest
se limita a tests para no importar copias históricas de pruebas; no se eliminan
esas evidencias. La revisión visual cubre cinco pantallas, gráficos, cambios de
cuenta, comparación, navegación rápida y filtros tras actualización.

Los servidores y pestañas de comprobación quedaron cerrados. El servidor del
usuario en 8765 conserva su proceso anterior: cerrar con Ctrl+C, arrancar otra
vez y recargar el navegador para aplicar la nueva versión.

- [Informe y evidencias](../reports/phase5-1-completion-2026-10-21.md).
- [Plan y criterios](PHASE5_1_PLAN.md).
- [Guía de uso y actualización](LAB_INTERFACE.md).

La implementación permanece local sobre `47d2fc5`, sin commits o pushes nuevos.
La FASE 6 sigue pendiente; no se reabren investigaciones o presupuestos.

## Cierre de FASE 5.2 — Conversación con el agente

Se entregan los seis incrementos: contratos y persistencia; conversación local;
propuestas estructuradas; revisión y aprobación de una prueba histórica concreta;
explicación y memoria; verificación. La pantalla Conversar con el agente permite
retomar una sesión, elegir mensajes de contexto y un resultado como evidencia,
consultar consumo y solicitar cancelación. Las cinco pantallas anteriores mantienen
su función de consulta, sin inferencias o cálculos al abrirlas.

El registro del chat es independiente de campañas y no modifica sus presupuestos,
permisos o evaluaciones. Límites persistidos por proyecto: 24 intentos de respuesta,
cuatro comparaciones de dos backtests, ocho trabajos activos/en cola y uno activo
por conversación. Los fallos y cancelaciones conservan la reserva; un reinicio no
reenvía trabajos. No se admiten rutas libres, texto ejecutable u órdenes a un bróker.

Las propuestas SMA/EMA largas, D1, requieren revisión de hipótesis, ventanas,
controles y período BCE; hasta diez años con historia suficiente. Fuente, código
y revisión se verifican antes del cálculo. Cambiar redacción, criterio o ceros
decimales no permite repetir la misma comparación. Las revisiones y la aprobación
quedan vinculadas por huellas a sus trabajos y resultados.

**267 pruebas aprobadas**, cero fallos, errores o saltos; 46 casos nuevos. Colección
completa de 1673 nodos sin errores, con los 1598 de FASE 5 conservados exactamente.
No se presenta como ejecución de toda la colección: la ejecución amplia inicial
se interrumpió y se completó la selección de componentes afectados. Caché de pytest
desactivada y temporal GUID nuevo por proceso. Las fuentes finales permanecieron
idénticas durante la comprobación.

Ensayo real aislado: cuatro peticiones Ollama, una comparación y dos backtests,
1800 tokens de entrada, 680 de salida y coste API cero. Se conservan una confusión
SMA/EMA y el rechazo de una explicación por un control numérico demasiado estricto,
junto con sus correcciones y consumo. La propuesta final sigue requiriendo revisión
humana. La comparación de Python y la interpretación libre del modelo aparecen
separadas; no se da por demostrada fiabilidad semántica general ni rentabilidad.

Revisión visual de propuesta, aprobación, resultado, evidencias, historial tras
reiniciar y Consumo, sin errores de consola. Durante una inferencia real, 30 muestras
por ruta mantuvieron p95 de 23,70/3,40/20,26 ms en Inicio/Experimentos/Consumo.
Es tiempo HTTP en el equipo de referencia, no latencia del modelo o pintado físico.

La auditoría conserva 92 registros, 40 cuentas detalladas y 150 con resumen, con
cero acciones prohibidas. Las 838 fuentes del inventario anterior siguen idénticas;
los módulos anteriores del motor y las pruebas se conservan. El ensayo se hizo
fuera de la base de conversaciones de uso habitual. Servidores y pestaña temporales
cerrados; no se intervino en el servidor del usuario. Al final, 8765 no estaba
escuchando: arrancar el laboratorio para usar la versión nueva. Sin dependencias
nuevas, commit o push. FASE 6 pendiente.

- [Informe y evidencias](../reports/phase5-2-completion-2026-10-21.md).
- [Guía de conversación](CONVERSATION.md).
- [Plan y alcance entregado](PHASE5_2_PLAN.md).

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
| SQLite local y servidor HTTP | Biblioteca estándar; registro de campañas existente e interfaz de consulta comprobados |
| Otros frameworks y APIs externas | Pendientes de evaluación cuando sean necesarios |

El código de aplicación solo usa la biblioteca estándar. pytest funciona con
Python 3.14.8. Pandas y NumPy siguen pendientes de aprobación si llegan a necesitarse.

## Decisiones acordadas

- Aprendizaje práctico y tareas pequeñas comprobables, con avance autónomo dentro
  del alcance autorizado. No pedir validaciones rutinarias; detenerse al completar
  la fase o tarea encargada.
- Consultar cambios de alcance, dependencias, proveedores o gastos fuera de la
  autorización existente. Mantener los controles del simulador separados de la IA.
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

El cierre de FASE 4 quedó publicado en `main` como `f5e6544`. El usuario autoriza
ahora publicar el cierre comprobado de FASE 5; el mensaje previsto es
`feat: close phase 5 local research interface`. Se comprueba que el servidor remoto
conserva el punto de partida antes de publicar, sin sobrescribir historia. La hoja
de ruta de las fases siguientes forma parte de esta entrega; no inicia FASE 6.
El identificador final y la confirmación del push se comunican al terminar.

## Asuntos pendientes y observaciones

- El BCE es la fuente educativa aprobada; faltan datos ejecutables y validación
  del calendario. Los cruces respecto al euro son referencias derivadas.
- Hay costes proporcionales hipotéticos; faltan spreads, slippage, swaps,
  financiación y restricciones de negociación verificadas para un bróker real.
- La separación y el walk-forward están implementados sobre datos ya conocidos;
  faltan datos futuros no consultados para validación prospectiva independiente
  y análisis ampliado de cambios simultáneos.
- El investigador local está disponible; su fiabilidad general sigue sin
  demostrarse. La interfaz local de consulta está disponible; no hay paper trading
  en tiempo real ni conexión con un bróker. No se han elegido parámetros ganadores.
- TradingView: Pine, gráficos, consultas, alertas e importaciones al simulador
  continúan pendientes de implementación; no se activa esa conexión en este cierre.
- En una captura se observó un comando de creación de `.venv` ejecutado desde el
  directorio personal. Puede existir un entorno adicional allí; no se ha
  inspeccionado ni eliminado. El entorno del proyecto sí está comprobado.
- La depuración desde el editor todavía no se ha probado.

## Próximo paso propuesto

**FASE 6.1 — Contratos y primeras estrategias Pine**, pendiente según el plan acordado.
La FASE 5.2 queda completada como conversación y pruebas históricas controladas.
El puente del chat a operaciones del simulador está previsto en FASE 6.6. La cuenta demo y la
posible ejecución real supervisada permanecen en fases posteriores.

No se inicia FASE 6 automáticamente con este cierre. No se añaden dependencias,
credenciales o conexiones externas sin la autorización correspondiente. Futuros
commits o pushes requieren una petición nueva.

Por indicación del usuario, actualizar este documento únicamente al terminar
una fase, no después de cada tarea. Registrar resultados comprobados y las
limitaciones que sigan pendientes. Esta regla sustituye la frecuencia anterior.
