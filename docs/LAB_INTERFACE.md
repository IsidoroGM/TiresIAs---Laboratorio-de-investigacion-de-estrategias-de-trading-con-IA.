# Consultar el laboratorio TiresIAs

## Arranque y cierre en Windows

Desde la raíz del proyecto, ejecuta:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.lab
```

Abre [TiresIAs local](http://127.0.0.1:8765). El servidor permanece en esa terminal;
**Ctrl+C** lo cierra y libera el puerto. Cerrar la pestaña no detiene el servidor.
Para otro puerto, añade `--port 8766` y usa la dirección que imprime el comando.
No hay servicios permanentes, conexiones externas o arranque automático de Ollama.
La sexta pantalla de [conversación con el agente](CONVERSATION.md) utiliza el
proveedor local al enviar mensajes y ejecuta pruebas solo con aprobación explícita.

Tras actualizar el código, cierra el servidor anterior con Ctrl+C, vuelve a
ejecutar el comando y recarga la página para utilizar la versión nueva.

## Rendimiento y actualización de fuentes — FASE 5.1

El servidor mantiene en memoria un índice de resúmenes, con un límite de 16 MiB
estimados de objetos y una caché de bytes para construir metadatos de hasta 32 MiB.
Las consultas HTTP se atienden con un máximo de cuatro hilos y una actualización
del índice en curso. No hay una base de datos de caché ni archivos de índice
persistentes: el estado se descarta al cerrar el servidor.

Mientras se consultan los listados, las comprobaciones de cambios se programan
cada dos segundos. Las pantallas de Inicio, Experimentos, Resultados, Memoria y
Consumo consultan novedades periódicamente. Una actualización se publica como una
instantánea completa; si falla, se conserva la anterior con su fecha y un aviso.
**Actualizar fuentes** fuerza una lectura nueva y muestra el fallo si no se puede
completar. Los filtros se conservan durante las actualizaciones del listado.

Esta fecha corresponde a los resúmenes leídos, no a una cotización de mercado o
una verificación actual de cada cuenta. Las fichas, cuentas y originales vuelven
a leer y verificar sus fuentes al abrirse; SQLite sigue consultándose en modo
de solo lectura para los registros de campañas. El chat tiene un registro separado
para sus acciones explícitas. Los datos financieros no reciben caché del navegador.

Cambiar de pantalla cancela las peticiones abandonadas; la ficha se dibuja sin
esperar a cargar su primera cuenta. Cancelar una petición no garantiza interrumpir
el trabajo de disco ya comenzado. El servidor limita el trabajo simultáneo y, si
se satura, devuelve un error temporal que permite reintentar. HTML, CSS y JavaScript
usan ETag para revalidarse sin transferirse otra vez cuando no cambian.

Para reproducir las medidas HTTP, con una salida nueva:

```powershell
.\.venv\Scripts\python.exe -B scripts/benchmark_lab.py ruta-nueva.json
```

Compara dos y cuatro hilos, 30 muestras por pantalla, primera carga y comprobaciones
de detalle. `--baseline-phase5` mide por separado el servidor, catálogo y consultas
del commit de cierre de FASE 5, cargados desde Git local sin modificar el checkout.
La primera carga del proceso se distingue de una caché fría del sistema operativo,
que no se controla en estas medidas.

## Recorrido

1. **Inicio**: recuentos de registros y copias, últimos registros, informes Markdown
   originales y avisos de fuentes. Los recuentos son de catálogo, no de estrategias
   únicas, procesos activos o investigaciones nuevas.
2. **Experimentos**: filtros combinables por par, estrategia, fecha registrada,
   estado, procedencia y texto. La fecha del filtro coincide con el día mostrado
   según la zona horaria del navegador; los archivos conservan sus instantes originales.
   La ficha presenta hipótesis, criterio, reglas, controles, parámetros, fuentes
   y resultados. Un dato ausente permanece como no disponible.
3. **Resultados**: abre una ficha y selecciona una cuenta. Hay cuentas separadas por
   estrategia, entrenamiento/comprobación, ventana y moneda. La curva y el drawdown
   representan los puntos guardados; la tabla separa fechas de señal y ejecución,
   cantidades, precios, costes y resultado neto. La posición abierta no se cierra
   para completar la pantalla. Los formatos de resumen no tienen un gráfico inventado.
4. **Memoria del agente**: fichas de propuestas, revisiones, duplicados, descartes,
   errores, intentos incompletos y resultados. Los desplegables distinguen respuestas
   originales del modelo, descripciones mecánicas de Python, conclusiones contrastadas
   y eventos. El registro completo y las capturas se pueden abrir como texto.
5. **Consumo**: consultas, tokens y coste de API guardados por fuente, con heredado
   aparte. No se ofrece un total global: varias memorias pueden describir la misma
   consulta. Las copias del mismo origen no vuelven a aparecer en este apartado.
   Un campo desconocido permanece desconocido aunque existan subtotales conocidos.

El comparador de cada ficha exige par, moneda, huella y fechas de datos, capital,
costes y tamaño conocidos e iguales. Fuera de una misma comparación guardada,
también exige identidad de ejecución conocida e igual. Explica las diferencias
que bloquean la comparación y muestra los parámetros distintos. Nunca suma capitales
ni compone rentabilidades de ventanas o cuentas independientes.

Los identificadores originales de criterio se conservan en la ficha:
`higher_return_without_more_drawdown` exige rentabilidad estrictamente mayor sin
mayor drawdown; `lower_drawdown_without_lower_return` exige drawdown estrictamente
menor sin reducir rentabilidad. `met`, `not_met` e `inconclusive` significan criterio
cumplido, no cumplido e inconcluso dentro del histórico descrito, respectivamente.
Una propuesta pendiente o técnicamente válida no acredita un resultado calculado.

## Procedencia y verificación

| Indicación | Alcance |
| --- | --- |
| Registro local | Archivo presente en un directorio admitido; su estado describe lo que quedó guardado |
| Copia histórica | Archivo localizado por un inventario de `reports`; puede consultarse sin el original local |
| Integridad de copias comprobada | Todos los archivos de ese inventario conservan sus huellas; no certifica significado, autoría externa o rentabilidad |
| Registro cotejado con una huella archivada | Coinciden los bytes del archivo principal local; no comprueba vigencia de toda su cadena de permisos |
| Registro sin verificación completa | No existe una huella archivada contrastable; no se presenta como certificado |
| Registro incompleto | Falta el archivo principal; se conservan los eventos disponibles sin inventar resultados o ejecución activa |
| Archivo diferente, ausente o no verificable | El problema queda visible; no se reemplaza silenciosamente el original por una copia |
| Registro contable vigente | Consulta separada mediante el lector SQLite existente, abierto en modo de solo lectura; no concede permisos de ejecución |

La contabilidad detallada se contrasta con la huella registrada, su resumen, fechas
y controles antes de dibujarla. No se vuelven a ejecutar señales, indicadores,
simulaciones o métricas para verificarla. Todas las fichas conservan acceso a los
originales, inventarios e informes asociados, servidos como texto seguro.

Los protocolos de desarrollo ya usaron estos datos históricos. La interfaz conserva
los resultados negativos y el duplicado del último ciclo. No demuestra validación
inédita, suficiencia estadística, cotizaciones actuales o rentabilidad futura.

## Fuentes admitidas y límites

El catálogo lee únicamente los directorios expresamente admitidos en
`lab_catalog.py`: investigaciones, registros previos, evaluaciones, robustez,
ideas, revisiones, sesiones, intentos y memorias compactas, campañas y walk-forward.
Incluye las comprobaciones históricas identificadas del investigador. El único
descenso adicional de robustez es `plan/attempts/intento`. No recorre modelos,
descargas, binarios, configuración personal ni credenciales.

Los inventarios versión 1 con mapa de archivos utilizan el verificador existente
`evidence.verify_evidence`. Los cinco inventarios históricos con lista `snapshot,
source, sha256` se comprueban por sus huellas sin convertir o modificar sus bytes.
Fuentes no admitidas o ausentes producen avisos. Las referencias declaradas no
permiten leer rutas arbitrarias fuera del catálogo.

Límites: 32 MiB por archivo, 256 MiB de lectura acumulada de la capa de consulta,
4.096 entradas/archivos, 25.000 puntos y 10.000 operaciones por cuenta detallada.
El verificador de evidencias mantiene además sus límites propios. Las fichas y
originales vuelven a leer sus fuentes; los listados usan el índice fechado descrito
arriba. La caché en memoria no acredita integridad actual ni sustituye sus controles.

Las consultas admiten GET/HEAD, enlaces mediante identificadores de catálogo y
origen/Host locales. El contenido del modelo se coloca como texto; no se ejecuta
como JavaScript, HTML o Python. FASE 5.2 añade rutas POST separadas bajo `/api/chat`,
con origen local obligatorio, token de acción, JSON acotado e identidad de petición.
Permiten mensajes, revisiones y pruebas históricas explícitas; no conceden permisos
de campañas ni modifican presupuestos anteriores. No se habilitan órdenes a brókeres.

## Comprobación de solo lectura

La auditoría explícita puede ejecutarse desde la raíz con:

```powershell
.\.venv\Scripts\python.exe scripts/check_lab_readonly.py
```

Revisa los registros y cuentas existentes con red, proveedores, simulador,
creación de diarios y reservas bloqueados. Contrasta las huellas antes y después.
No realiza inferencias o backtests. Las pruebas automatizadas usan fuentes
artificiales y temporales exclusivos según `AGENTS.md`.

TradingView, brókeres, recepción de eventos y dinero real quedan fuera de FASE 5.

## Ampliación local de FASE 6

La opción **Simulación y TradingView** se desarrolla después del cierre de FASE 5.2.
Prepara contratos y paquetes Pine, registra cuentas virtuales revisadas, muestra
pendientes y conflictos, conserva CSV/JSON aportados y permite procesar, valorar
y conciliar mediante acciones explícitas. Sus consultas GET no crean cuentas ni
inician procesamiento; los POST bajo `/api/simulation` utilizan la misma frontera
de origen y token locales que el chat. La aprobación del procesamiento identifica
cuenta e inbox concretos y caduca si cambian.

La [guía de esta ampliación](TRADINGVIEW_LOCAL.md) describe formatos y controles.
Los ensayos de contratos y contabilidad usan datos artificiales locales. Pine y
las exportaciones reales de TradingView siguen pendientes de validación; no hay
conexión de una cuenta ni órdenes a un bróker.

La sección **Históricos EUR/USD y prueba con spread** permite importar CSV
Dukascopy BID/ASK o un archivo anual H1 de EV Trading Labs. Se declaran las fechas
UTC, con fin exclusivo, y el año del archivo anual. Conserva originales, atribución,
procedencia declarada y calidad. La importación admite hasta 2 MiB en total y no
ejecuta una estrategia. La ficha del histórico verifica los originales y ofrece
una acción separada para calcular SMA 20/60 con compras ASK y ventas BID.

Capital, cantidad y comisión son hipótesis de la prueba. El cálculo no modifica
cuentas virtuales; GET no calcula ni descarga. Se muestran resultados guardados
o los datos que faltan. Enero tiene 27 sesiones y no permite evaluar el cruce
diario. El tramo real de 2025 hasta el 24/12 tiene 307 sesiones; su primer cálculo
produce tres ejecuciones hipotéticas. El año completo queda bloqueado por dos
huecos internos del 25/12. La [guía de históricos](MARKET_DATA.md) describe los
formatos, la definición UTC y los costes incluidos y pendientes.

**Comparar períodos independientes** permite guardar una comparación de dos
resultados con la misma configuración y versión del motor, fuente y política de
sesión. Sus períodos no pueden solaparse. Cada uno conserva su capital inicial y
estado propio: no se suman saldos ni se heredan posiciones. La ficha verifica las
copias guardadas y muestra métricas por período sin ejecutar otra estrategia; el
listado solo lee metadatos. Los bloqueos quedan visibles sin métricas inventadas.
La [validación por períodos](PERIOD_VALIDATION.md) conserva el primer contraste
2024/2025 con fechas y parámetros fijados antes de descargar el año adicional.

**Comparar con referencias y comisiones** calcula cuatro escenarios fijos con
SMA 20/60, comprar/mantener tras el calentamiento y efectivo USD sin intereses.
La ficha permite cambiar de comisión sin recalcular, revisar patrimonio, costes,
caída, operaciones y posición abierta. Los escenarios con huecos o menos de 62
sesiones no publican métricas. El [detalle de reglas y resultados](REFERENCE_COSTS.md)
conserva las hipótesis, incluidas las diferencias de exposición y la ausencia de
cierre final forzado. Consultar no inicia estrategias ni procesa cuentas.

El chat permite seleccionar **Históricos BID/ASK · EUR/USD · SMA**, revisar base,
variante, fuente y costes, y aprobar una comparación mediante el trabajador
existente. Su resultado se consulta en esa conversación, con curvas y operaciones,
y puede adjuntarse como evidencia al modelo. Los cuatro intentos se comparten con
BCE. En las explicaciones nuevas, el modelo elige aspectos y Python redacta el
texto con el criterio registrado y las métricas verificadas. Una respuesta
incompatible se conserva como rechazada, con error y consumo; no cambia la
evaluación ni crea una estrategia. Los comentarios antiguos siguen etiquetados
como interpretaciones sin contraste estructurado. La [guía del recorrido](CHAT_PRICES.md) conserva el
ensayo real y sus límites. Pedir una compra actual sigue sin generar una operación.

**Operaciones virtuales manuales**, bajo la ficha de estrategia del chat, permite
crear una cuenta manual independiente, revisar «simula comprar/vender 1 EUR/USD»
con BID/ASK aportado y aprobar después la intención concreta. Se muestran previsión,
confirmación, efectivo, posición, patrimonio y resultado realizado. La
[guía manual](MANUAL_OPERATIONS.md) detalla límites y controles. Los precios no se
verifican como mercado actual y estas operaciones no cambian los backtests anteriores.

En **Valoración de cada cuenta manual** se consultan BID, fecha, antigüedad,
resultado no realizado y pausa de riesgo. **Actualizar valoración** requiere
revisión explícita del precio y estado concretos; no compra, vende o cobra otra
comisión. El resumen avisa de precios ausentes, futuros o desactualizados, y la
antigüedad avanza sin borrar el formulario. [Detalle](MANUAL_VALUATION.md).

**Contrastar informes de operaciones** compara un CSV con una prueba BID/ASK
guardada. También se accede desde sus operaciones mediante **Contrastar estas
ejecuciones con un informe aportado**. Se revisan mapa, unidades, origen,
configuración y tolerancias antes de mostrar una vista previa sin guardado.
Después se archivan original y copias de referencia con una aprobación separada.
Las filas sin pareja, ambigüedades, diferencias y costes desconocidos quedan
visibles. La coincidencia de campos no verifica el motor externo. El
[lector genérico y el siguiente adaptador de JForex](EXECUTION_COMPARISON.md)
se distinguen de la importación contable del inbox; aquí ninguna cuenta cambia.

**Conciliar costes y valoración de JForex** añade el recorrido del paquete nativo
TEST: referencia guardada, ZIP con HTML y exportaciones, vista previa y guardado
de la conciliación concreta. Muestra el corte común, resultado bruto, swaps
anteriores/posteriores y discrepancias de comisiones. Las reconstrucciones se
distinguen de las capturas informativas de la API, con su instante real y posible
retraso. La ficha de la primera prueba ya está guardada, con estado parcial.
El ensayo v3 también está guardado. La ficha muestra el patrimonio API y la fecha
real, sus 450 s de retraso respecto al corte y la valoración de cada captura con
cotización y costes hasta ese instante. Conserva las diferencias frente a las
reconstrucciones y la coincidencia del patrimonio final con el HTML, sin certificar
sincronización ni equivalencia completa. El [detalle](JFOREX_RECONCILIATION.md)
explica archivos, controles y precisión. Consultar no ejecuta estrategias ni altera
cuentas o consumo.
