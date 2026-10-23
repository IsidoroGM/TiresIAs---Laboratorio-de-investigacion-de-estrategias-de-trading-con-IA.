# FASE 6: primer ensayo nativo completo de JForex

El usuario aporta el HTML y los archivos de la revisión v2 del tester. La prueba
completa la ventana prevista sin fallos de estrategia. Se omiten 9.880 ticks de
mercado cerrado y se procesan 24.488. Hay dos compras y una venta de 1.000 EUR,
con una posición final abierta de 1.000 EUR. El HTML informa de 999.988,68 USD
frente a 1.000.000 USD iniciales: pérdida global de 11,32 USD. La posición cerrada
muestra -13,24 USD y la abierta +1,98 USD. Son cifras del informe y su corte final.

El calendario nativo permite seleccionar 6.122 H1 entre las 8.592 exportadas, con
las mismas aperturas horarias que la referencia. Se observan cinco diferencias de
precio en tres velas (archivo separado). No cambian los OHLC diarios: las 307
sesiones reconstruidas independientemente producen exactamente el SHA-256 de la
referencia. Coinciden las SMA y las señales de todas las sesiones.

Las tres ejecuciones coinciden en dirección, cantidad, precio y fecha de señal.
Cada ejecución nativa ocurre 450 segundos después de la apertura asumida por
Python. El contraste conserva esa diferencia con tolerancia temporal cero; una
ventana de una vela H1 se usa únicamente para emparejar candidatos únicos.
Las comisiones por fill siguen desconocidas y no se asignan las agregadas.

La comisión mostrada por el HTML (0,06 USD) y la suma de agregados de órdenes
(0,05 USD) difieren al nivel de presentación disponible. Los swaps ajustan los
precios mostrados de las posiciones; el historial de fills mantiene los precios
originales. Además, el tester llega al 27/12 y registra dos swaps después del corte
de estrategia del 25/12. No se compara su patrimonio final directamente con el
de Python al 25/12 ni se declara contabilidad final reconciliada.

El campo v2 `remaining_amount_millions` reproduce IOrder.getAmount: una orden
CLOSED conserva 0,001. La exposición abierta se verifica mediante saldo de fills
y estado nativo, sin sumar ese campo de órdenes cerradas como posición restante.

Los HTML, mensajes y CSV originales se conservan byte a byte en `.local/`, con
huellas aquí y sin publicar identificadores de cuenta. Este documento registra
una revisión de resultados; no implementa ni valida un importador HTML genérico.
No crea cuentas, operaciones, backtests Python, solicitudes al modelo ni registros
en el comparador de la app. No repite las 35 pruebas de código ya aprobadas: no
cambia el adaptador. Las verificaciones de datos/ejecuciones se ejecutan mediante
el script conservado. Todas las evidencias anteriores, el código de motores y
PROJECT_STATUS permanecen intactos. Sin commit/push ni cierre de FASE 6.

Siguiente paso: conciliar comisiones, swaps y valoración al mismo corte temporal,
y después incorporar esta evidencia nativa al flujo de contraste de la aplicación.
La equivalencia completa de motores o resultados permanece sin verificar.
