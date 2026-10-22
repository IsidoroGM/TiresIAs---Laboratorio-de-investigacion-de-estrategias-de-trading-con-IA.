# FASE 5.1 — Rendimiento y fluidez de la interfaz local

Diagnóstico del 20/10/2026, Europe/Madrid; implementación y cierre el 21/10/2026.
**FASE 5.1 completada**, antes de TradingView. Referencia de
software: cierre de FASE 5, commit `47d2fc5`. No cambia sus resultados históricos.

## Diagnóstico medido

Conjunto actual: 92 registros y 805 archivos catalogados. Tres solicitudes HTTP
secuenciales por ruta, conexiones nuevas a un servidor temporal en loopback:

| Consulta | Mediana | Mínimo–máximo |
| --- | --- | --- |
| Inicio | 3,333 s | 3,215–3,388 s |
| Experimentos | 3,294 s | 3,152–3,365 s |
| Consumo | 2,447 s | 2,428–2,514 s |

[Muestras, método y perfil](../reports/phase5-1-diagnosis-2026-10-20/baseline.json).
Son tiempos HTTP del servidor en esta sesión; no incluyen dibujado del navegador.
La caché del sistema operativo no se controló: no son medidas de arranque en frío
del disco. Tres muestras describen el problema, pero no permiten establecer un
p95 fiable. La medición de aceptación requerirá más repeticiones.

El código muestra las causas:

- `lab.py` crea un `LabQuery` para cada petición de datos o archivo. Su constructor
  vuelve a recorrer directorios e inventarios. Incluso una ruta desconocida pasa
  por ese trabajo antes de devolver el error.
- `Catalog.safe` recorre repetidamente los componentes de cada ruta, comprobando
  enlaces, junctions y resolución. Un perfil de Inicio registra 2096 llamadas;
  el tiempo total exacto de este nuevo perfil se conserva en la evidencia. El
  catálogo consume aproximadamente la mitad de la consulta instrumentada.
- Inicio llama a `experiments()`: lee los registros y eventos del conjunto completo
  para ofrecer recuentos y cinco entradas recientes. Inicio y Experimentos leen
  unos 1,5 MB por consulta, repartidos entre numerosos archivos pequeños.
- `account()` vuelve a construir el detalle; `compare()` lo repite para las dos
  cuentas. La ficha solicita después su primera cuenta por otra ruta HTTP.
- `HTTPServer` atiende de forma secuencial. El navegador descarta respuestas
  antiguas mediante un contador, pero no cancela las peticiones abandonadas.
- Todas las respuestas usan `no-store`, incluidos HTML, CSS y JavaScript.

Los filtros de la tabla ya trabajan en el navegador después de cargar el listado.
No hay evidencia de que sean la causa principal. El coste del dibujado, los gráficos
y los desplegables se medirá antes de atribuirles un problema de rendimiento.

## Solución recomendada

Conservar Python y su biblioteca estándar. Separar un índice de consulta compartido
de los lectores y verificaciones de cada petición. Entregar por incrementos:

| Incremento | Medida | Resultado buscado |
| --- | --- | --- |
| 5.1.1 | Medición reproducible por etapa y ruta | Comparación antes/después con el mismo conjunto y pruebas de frescura |
| 5.1.2 | Índice y resúmenes en memoria, con generaciones y actualización | Evitar reconstruir el catálogo y releer todos los eventos en cada navegación |
| 5.1.3 | Lecturas compartidas dentro de la petición y escaneo más eficiente | Evitar duplicar detalle, archivos, parseo y comprobaciones equivalentes |
| 5.1.4 | Cancelación y presentación progresiva en el navegador | Navegación rápida sin resultados antiguos ni espera innecesaria por la cuenta |
| 5.1.5 | Atención concurrente limitada, con estado compartido protegido | Una lectura lenta no bloquea toda la interfaz |
| 5.1.6 | Caché condicional de estáticos y comprobación final | Menos transferencias repetidas; cierre con medidas y regresión funcional |

### Índice en memoria y frescura

Crear instantáneas coherentes del catálogo y de los resúmenes ligeros. Cada una
tendrá generación, fecha de indexación y procedencia. Cambiar de pantalla podrá
reutilizar la misma generación sin volver a recorrer el proyecto completo.

La revisión de cambios se propone cada dos segundos mientras haya consultas,
con una sola actualización en curso. Se compararán inventarios de directorios y
firmas de archivos —identidad, tamaño y tiempos de modificación/cambio— para
reconstruir únicamente lo afectado. Estas firmas sirven para invalidar metadatos;
**no sustituyen una huella criptográfica ni demuestran integridad actual**.

Si se muestra una generación anterior durante una actualización, la interfaz debe
indicar su fecha y que se está actualizando. El objetivo es reflejar altas,
modificaciones y bajas en cinco segundos con el conjunto de referencia. Una
acción de refresco forzado esperará una lectura nueva o mostrará su error.

Las fichas verificadas, cuentas y originales revalidarán sus fuentes al abrirse;
no heredarán una etiqueta de integridad actual de la caché del listado. Cualquier
resultado de verificación reutilizado se identificará por fecha y huellas de la
instantánea comprobada. La contabilidad SQLite vigente seguirá leyéndose mediante
una conexión propia en modo de solo lectura, sin caché de estado financiero actual.

No compartir directamente el objeto `Catalog` actual entre peticiones: contiene
presupuesto acumulado de lectura, avisos y estructuras mutables. Separar la
instantánea compartida del contexto y los límites particulares de cada consulta.
Acotar la caché por entradas y peso, y medir memoria; fijar el límite definitivo
con datos, incluyendo el peso de objetos Python y las generaciones simultáneas.

### Lecturas y escaneo

Reutilizar en una petición los bytes, JSON y detalle ya leídos. Dos cuentas de un
mismo experimento podrán compartir detalle e inventario comprobado en ese contexto.
El presupuesto de lectura seguirá aplicándose al conjunto de la consulta y no se
reiniciará por cada cuenta. Detectar cambios durante la lectura; ante discrepancias,
mostrar un estado incompleto o reintentar de forma acotada.

Evaluar `os.scandir()` o `Path.info`, disponible en Python 3.14, para aprovechar
metadatos obtenidos durante la enumeración y reducir llamadas redundantes. El
recorrido actual ya usa `Path.iterdir()`: la mejora exige aprovechar esos datos,
no simplemente cambiar el nombre de la función. Conservar las comprobaciones
actuales de rutas, enlaces y junctions antes de abrir archivos. Los objetos
`DirEntry` y `Path.info` almacenan información que puede envejecer; no son una
autorización permanente para seguir una ruta. Fuentes:
[PEP 471](https://peps.python.org/pep-0471/) y
[Path.info en Python 3.14](https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.info).

Validar las rutas HTTP antes de construir lectores: un 404 no necesita indexar
los experimentos. Mantener identificadores opacos y ubicaciones admitidas.

### Navegador y servidor

Cancelar con `AbortController` las peticiones de la pantalla o cuenta abandonada,
conservando el contador que evita pintar resultados antiguos. Dibujar primero
la ficha y cargar la contabilidad de forma independiente. Preparar los textos
extensos al abrir su desplegable si el perfil de navegador justifica esa mejora.
Cancelar `fetch` no garantiza interrumpir un cálculo que el servidor ya comenzó;
se necesita además limitar trabajo y tratar desconexiones sin bloquear la cola.
[Documentación de AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController).

Después de separar el estado mutable, evaluar un servidor con hilos y límites
explícitos: empezar comparando dos y cuatro tareas de lectura, cola acotada y
tiempos de espera. Una única reconstrucción por generación, publicación atómica
de la instantánea y contextos de lectura independientes. No mantener un bloqueo
global durante todo el trabajo de disco. Comprobar apagado y conexiones lentas.
[ThreadingHTTPServer](https://docs.python.org/3.14/library/http.server.html#http.server.ThreadingHTTPServer)
resuelve la atención de conexiones en paralelo, pero no elimina el trabajo duplicado.

Una simple decoración `lru_cache` tampoco proporciona invalidación por cambios o
una única ejecución de trabajo concurrente: Python documenta que dos llamadas
pueden calcular el mismo valor antes de que se almacene.
[Documentación de functools](https://docs.python.org/3.14/library/functools.html#functools.lru_cache).

Para HTML/CSS/JavaScript, proponer ETag y revalidación condicional con `no-cache`,
o recursos versionados cuando convenga. Mantener `no-store` para los datos y los
originales de consulta; la caché de metadatos descrita aquí vive en el servidor.
Esta mejora de estáticos tiene prioridad menor que eliminar el escaneo repetido.
[Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)
y [ETag](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/ETag).

## Alternativas consideradas

| Alternativa | Valoración para el conjunto actual |
| --- | --- |
| Índice en memoria con invalidación y verificaciones de detalle | Recomendado: aborda el coste medido, es descartable al cerrar y conserva archivos como fuentes |
| Guardar respuestas durante un tiempo sin revisar fuentes | Insuficiente: puede ocultar cambios y presentar verificaciones antiguas como vigentes |
| Añadir únicamente hilos | Parcial: reduce esperas entre conexiones pero conserva el coste y puede multiplicar las lecturas |
| Índice persistente SQLite o monitor de archivos externo | Reservar para crecimiento medido o arranque todavía lento; añade reconstrucción, invalidación y dependencias operativas |
| Reescribir con otro framework, Redis o más hardware | Beneficio no demostrado por este perfil; primero resolver las lecturas redundantes |

## Criterios propuestos de aceptación

Objetivos de ingeniería por comprobar; no son resultados ya obtenidos:

- Con los mismos 92 registros/805 archivos y el índice preparado: mediana de
  Inicio, Experimentos y Consumo de 200 ms o menos; p95 de 500 ms o menos.
  Medir al menos 30 peticiones por ruta, sin perfilador, incluyendo ciclos de
  actualización del índice, y publicar todos los valores. Separar la carga inicial
  de un proceso nuevo del acceso con el índice preparado; no llamar arranque en
  frío del disco a una prueba sin controlar la caché del sistema operativo.
- Medir también ficha local, ficha archivada, cuenta y comparación. Publicar por
  separado el coste de verificar los bytes actuales; optimizarlo no autoriza a
  saltarse la verificación para cumplir un objetivo de latencia.
- Altas, modificaciones y bajas aparecen en cinco segundos en el conjunto de
  referencia. Refresco forzado confirma una generación nueva o informa del fallo.
- Una alteración, incluso conservando tamaño y fecha de modificación, se detecta
  al verificar el detalle o abrir el original. Nunca se reutiliza como comprobación
  actual un resultado basado solo en esos metadatos.
- Pruebas de navegación rápida, cambio de cuenta, dos pestañas, peticiones
  simultáneas, actualización fallida, archivo cambiado durante lectura, rutas
  convertidas en enlaces/junctions y cierre del servidor. No mezclar generaciones
  de forma silenciosa; no duplicar reconstrucciones ni exceder límites de memoria.
- Medir el navegador además del HTTP: tiempo hasta ver contenido y poder actuar,
  renderizado y tamaño de respuestas. Conservar filtros y contenido del modelo
  como texto; la velocidad no cambia los controles de acceso o las cuentas.
- Pruebas funcionales y auditoría de lectura con cero inferencias, backtests,
  reservas o escrituras en fuentes desde la interfaz. Temporales exclusivos y
  caché pytest desactivada según AGENTS.md; conservar evidencias previas y comparar
  el nuevo código contra el commit de cierre, sin reescribir sus manifiestos.

## Resultado de la implementación

Los incrementos anteriores quedan entregados. Con cuatro hilos y el índice
preparado, las medianas HTTP de Inicio, Experimentos y Consumo son 1,98, 2,33 y
2,18 ms; p95 de 19,38, 22,66 y 15,29 ms, con 30 muestras por pantalla. Primera
consulta de una instancia nueva: 2,402 s. Una adición se refleja por HTTP en
2,170 s con el intervalo predeterminado. Se mantienen las verificaciones actuales.

Pasan 80 pruebas de interfaz y 48 de evidencias/registro contable. La colección
comprueba 1627 nodos sin errores: 1598 anteriores y 29 nuevos. No se presenta
como una nueva ejecución completa de esos 1627 casos. Se verifican las cinco
pantallas, cuentas, filtros, actualización y errores en el navegador.

El detalle de métodos, límites, memoria, diagnósticos y evidencias está en el
[informe de cierre](../reports/phase5-1-completion-2026-10-21.md). Los servidores
temporales están cerrados. PROJECT_STATUS se actualiza al cerrar esta fase.
La FASE 6 queda pendiente. No se realiza commit o push sin una nueva petición.
