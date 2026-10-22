# Descarga Dukascopy y sesiones diarias UTC: avance

22/10/2026. FASE 6 continúa abierta.

## Resultado comprobado

El descargador nuevo solicita y conserva los archivos públicos H1 mensuales de
EUR/USD, con caché y límites. El ensayo de enero de 2025 obtuvo BID y ASK. Sus
528 velas con actividad por lado coinciden exactamente en apertura, máximo,
mínimo, cierre y fechas con los dos CSV aportados por el usuario. La comprobación
independiente lee LZMA/struct/CSV sin importar el descodificador del proyecto.

Se producen 27 sesiones UTC observadas, sin crear precios en intervalos ausentes.
Se mantienen domingos y días parciales, con límites de sesión y horas observadas
separados. La reproducción offline tiene el mismo SHA-256 de las sesiones y los
mismos bytes de `daily.json`, sin peticiones nuevas.

El perfil diario es explícito y distinto de una garantía de equivalencia con las
velas de OANDA/TradingView. Con enero no se alcanza el calentamiento SMA 20/60.
`signal-preview.json` contiene cálculos, sin operaciones, rentabilidad ni cuentas.

## Acceso externo y limitaciones

La API más reciente responde HTTP 202 con un reto de acceso, no con cotizaciones.
El servidor HTTPS antiguo no responde dentro del plazo del sondeo. Se comprueba
la ruta pública desde el sitio oficial: enero está disponible mediante una
redirección a HTTP. Se guardan URLs, SHA-256, fechas y la limitación de transporte;
el origen no se presenta como autenticado. No se usan credenciales ni servicios
de pago, ni se desactiva la validación de certificados.

La ampliación a 2024–2025 se detuvo inicialmente por una segunda redirección que
la primera comprobación rechazaba. Se ajusta la validación para admitir los dos
hosts de Dukascopy y conservar la ruta. Los siguientes intentos reciben HTTP 429,
también más de tres minutos después. La última respuesta no aporta Retry-After.
Los dos años **no están descargados**. No se reintenta en bucle ni se presenta un
resultado vacío como una descarga terminada.

## Verificación y evidencia

Se prueban meses cerrados y límites, LZMA corrupto/truncado/excesivo, precios y
volúmenes inválidos, duplicados, meses incompletos, exclusión identificada de
registros planos sin volumen, días parciales y domingos, huecos internos,
integridad de caché, transporte, reproducción offline y reanudación tras fallos.
HTTP 202/429/HTML no promueve un conjunto de datos vacío.

185 pruebas seleccionadas aprobadas: 33 del descargador nuevo, 21 del lector CSV
y 131 relacionadas con contratos, importación y simulación. `tests.log` y
`tests.xml` conservan los resultados. No se ha ejecutado la colección completa.
`manifest.json` registra huellas de fuentes y evidencia.
Los originales y resultados de cálculo permanecen en `.local/dukascopy/`.

`tested-source/` conserva las dos fuentes nuevas y el comprobador independiente
como instantáneas. El comprobador conserva sus rutas de la ejecución original;
su copia es evidencia, no un nuevo punto de entrada. `pilot-summary.json`,
`offline-summary.json` y `csv-comparison.json` reproducen los informes originales;
`probes/` y `failures/` conservan los diagnósticos de acceso.

Los informes de enero y de los errores externos conservan sus estados originales.
No se modifican contratos, políticas de ejecución, capital, cuentas, PROJECT_STATUS
ni cierres de fases. No se realizan commits o pushes.
