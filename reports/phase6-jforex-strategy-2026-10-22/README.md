# FASE 6 — Estrategia JForex exclusiva TEST

El usuario confirma plataforma y acceso demo. Se localizan JForex 4.23 y API 4.9.8.
La estrategia Java compila contra ese JAR con `javac --release 21`. No se inicia
JForex, se leen credenciales o se opera una cuenta desde este trabajo. La compilación
y ejecución dentro de la plataforma siguen pendientes del usuario.

El protocolo se fija antes de un único backtest local nuevo: 1.000.000 USD y
1.000 EUR, con las reglas y precios preservados y comisión supuesta 0,001. Su
identificador y huella están en `reference-link.json`. Mantiene las mismas sesiones,
señales, fechas y precios; capital/cantidad/costes se escalan por 1.000. La referencia
anterior no se reemplaza. El presupuesto del chat no se utiliza ni se reabre.

El harness usa dobles de las interfaces API, sin cliente ni engine nativo. El replay
offline aporta dos cotizaciones por sesión: apertura y cierre de los H1 originales,
con la fecha del cierre desplazada un milisegundo dentro de su sesión. Añade un
marcador artificial al límite final; no es una cotización externa observada.
Comprueba SMA, señales y peticiones sobre esos mismos datos. Sus confirmaciones,
IDs y comisiones son artificiales. No reproduce ticks/interpolación o contabilidad
de JForex y no demuestra equivalencia de motores.

`offline-replay/` conserva esa salida identificada como artificial. `python-reference/`
conserva el nuevo resultado y sus entradas. El código no genera comisiones por fill
a partir de totales ni atribuye a un cierre nativo una señal futura. Los cierres
y valoraciones posteriores al intervalo exigen conciliación con el HTML nativo.

660 pruebas seleccionadas aprobadas, incluidas 30 de JForex y ninguna omitida.
`tests-final.*` conserva la comprobación final; `tests.*` conserva las 659 anteriores
a añadir el caso de cierre nativo anterior a nuestra señal. No se ejecuta la colección
completa. La auditoría verifica los 15 manifiestos de los 14 informes anteriores,
sus evidencias, fuentes del núcleo, originales y cálculos decimales de escala.

El paquete para el usuario contiene la fuente Java, guía, mapa y referencia de la
prueba. No contiene el JAR del proveedor ni presenta archivos `.class` como `.jfx`.
El lector nativo HTML y la validación externa siguen pendientes de los originales.
Sin órdenes externas, operaciones manuales, llamadas al modelo, commit o push.
PROJECT_STATUS permanece intacto; FASE 6 no se cierra.

Tras la auditoría se intenta inspeccionar la ventana de JForex mediante Windows
Computer Use. La herramienta devuelve «Computer Use app approval timed out».
No se obtiene captura ni se envía ninguna entrada a la aplicación. El nombre
de la ventana no se copia a este informe. Se solicita al usuario elegir entre
reintentar el permiso de acceso o seguir las instrucciones manualmente.
Esto no es una compilación nativa fallida ni un rechazo de la estrategia.
