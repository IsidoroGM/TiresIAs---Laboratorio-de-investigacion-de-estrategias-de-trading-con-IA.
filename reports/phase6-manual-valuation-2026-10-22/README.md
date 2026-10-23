# Valoración de cuentas manuales sin otra operación

22/10/2026. Desarrollo posterior al commit `0bd90113c5ea47731da52a57d26d9b5f6dfeafdc`,
publicado y verificado en origin/main antes de continuar. Este incremento queda
local. FASE 6 sigue abierta, sin cambio de PROJECT_STATUS.

## Cambio

`manual_valuation` permite aprobar otra referencia BID/ASK para una cuenta manual
existente. No modifica `conversation_operations`, el motor contable ni contratos;
sus huellas previas siguen iguales y la cuenta existente conserva compatibilidad.
Se registra la huella del nuevo componente y se comprueba la versión revisada.
La base conserva su esquema y cadena, sin migración ni reinicio de saldo.

El precio debe ser positivo, no cruzado, reciente, no futuro y compatible con los
instantes anteriores. Estado y código deben coincidir con lo revisado. La aprobación
y valoración se confirman en un asiento atómico, con identidad persistida y límite
de asientos. Repeticiones concurrentes o tras reinicio devuelven el mismo asiento;
cambios de datos o conversación se rechazan. No se crea fill ni comisión nueva.

La valoración usa BID y actualiza patrimonio, máximo, caída y posible pausa de
riesgo. Mantiene efectivo, EUR, coste de adquisición, resultado realizado, costes,
operaciones y secuencia. Un cambio de cadena invalida intenciones pendientes del
estado anterior. La venta para reducir una posición sigue permitida bajo pausa.

La consulta muestra último BID, fecha, antigüedad, resultado no realizado y pausa,
y las últimas 200 valoraciones de la conversación. Estado e historial se leen en
la misma instantánea. La interfaz fecha su estado consultado y actualiza el aviso
de antigüedad durante el sondeo habitual, sin recargar formularios ni pedir una
inferencia o valoración nueva. Un precio reciente sigue siendo aportado y no verificado.

## Demostración y límites

`protocol.json` fija los precios artificiales antes del ensayo. En la interfaz se
crea `manual-valoracion-20261022`, capital 1.000 USD, máximo 1 EUR, comisión 0,001.
La compra a ASK 1,1002 deja efectivo 998,8986998 USD, posición 1 EUR y patrimonio
999,9986998 USD al BID 1,1. Tras aprobar otro BID 1,09 / ASK de referencia 1,0902,
el patrimonio pasa a 999,9886998 USD y el resultado no realizado a −0,0113002 USD.
Efectivo, cantidad, coste de adquisición, resultado realizado, una única compra
y comisiones de 0,0011002 USD permanecen idénticos.

La posición de ejemplo queda abierta en esa cuenta virtual independiente. Los
precios no son observaciones de mercado; se usan para verificar contabilidad y UI.
No se ejecutan backtests ni se llama al modelo durante este ensayo. Antes de la
demostración se observa otra petición del usuario en una conversación de la app:
se preserva, no se reintenta y su consumo no se atribuye al ensayo. No se publican
sus mensajes en esta evidencia. Las cuentas de estrategia e inbox siguen vacíos.

## Verificación

586 pruebas seleccionadas aprobadas, 24 nuevas. Cubren antigüedad y fronteras,
campos/aprobación, secuencia temporal, motor/estado revisados, repetición, concurrencia,
reinicio, fallo de transacción, manipulación, riesgo y reducción de posición,
invalidez de intenciones pendientes y HTTP con presupuestos sin cambios.
No se ejecuta otra colección completa. Pytest usa temporal GUID nuevo y caché
desactivada, según AGENTS.md. Sintaxis JavaScript, espacios, interfaz y conservación
de evidencias anteriores comprobados. Un cálculo independiente stdlib/Decimal
verifica efectivo, coste, patrimonio y resultado no realizado de la demostración.

El manifiesto conserva entradas y salida del ejemplo, asiento y huellas, sin tokens
HTTP ni otros mensajes del usuario. El commit y push previos sí están completados;
este avance adicional no se incluye en ellos ni se publica automáticamente.
