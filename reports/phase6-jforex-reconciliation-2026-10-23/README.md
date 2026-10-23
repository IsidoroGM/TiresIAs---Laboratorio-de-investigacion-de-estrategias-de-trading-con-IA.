# FASE 6: conciliación al corte e integración de JForex

Se incorpora un lector acotado de ZIP con HTML y exportaciones TEST H1/4-OHLC BID,
con límites, nombres exactos, coherencia de parámetros/posiciones/fechas y archivo
de originales. No ejecuta HTML ni extrae rutas del ZIP. Admite v2 y v3 de nuestra
estrategia; no declara un lector universal de informes de JForex.

La app muestra vista previa, guardado ligado a la huella revisada, catálogo de
metadatos y ficha verificada. Conserva el primer ensayo real v2 como conciliación
e09d030c7635c6542cd53b030874afb51ad162b8305853a2d13b55e42ff96681.
El ZIP original con posibles datos privados permanece en `.local/`; aquí se guarda
el resultado sin identificadores de cuenta ni los archivos nativos originales.

Al 25/12/2025 00:00 UTC: bruto -7,79 USD; swaps derivados previos -3,01376 USD,
posteriores -0,12354 USD. HTML/eventos publican comisión 0,06 USD y los agregados de
órdenes suman 0,05 USD. Los escenarios reconstruidos resultan -10,86376 USD y
-10,85376 USD; no se presentan como observaciones nativas ni límites certificados.
El patrimonio exacto del tester a ese corte y el detalle por fill siguen pendientes.
Se conserva estado parcial y no se importa contabilidad a cuentas.

La revisión Java v3 captura cuenta y órdenes al primer tick desde el corte y al
detener el tester, con instante real, objetivo, cotización, campos informativos
de la API y exposición neta de historiales. No se mueve una captura posterior al
instante objetivo ni se llama efectivo al balance EOD previo. Se separa el importe
original API de la exposición; una orden cerrada puede conservar 0,001 y tener
exposición cero. El ZIP de entrega contiene fuente/guía/ajustes, sin API/JAR/JFX.

248 pruebas seleccionadas aprobadas sin omisiones: 42 de conciliación, 37 Java,
44 de comparación y 125 de servicio/simulador/interfaz. Se compila contra la API
instalada; los dobles no ejecutan el tester. JavaScript pasa comprobación sintáctica.
La ficha y sus importes/avisos se verifican en el navegador, con capturas conservadas.
El guardado mantiene once huellas de almacenes existentes; presupuesto global
4 solicitudes de modelo y 1 experimento, sin llamadas propias ni cuentas cambiadas.

Los manifiestos anteriores, fuentes de motores, referencia congelada y
PROJECT_STATUS se verifican intactos. Se registran por separado los cambios
autorizados del servicio y la interfaz. No hay backtest Python nuevo, operación
real/demo, commit, push o cierre de fase. FASE 6 sigue abierta.

Siguiente comprobación: reimportar la fuente v3 en JCloud, compilar con F5 y repetir
los mismos ajustes y parámetros para obtener las capturas nativas que faltan.
Esa ejecución aún no está verificada; las comisiones por fill desconocidas, posibles
retrasos de la API y diferencias de ejecución mantienen sus límites explícitos.
