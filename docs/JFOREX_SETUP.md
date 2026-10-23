# Preparar la primera prueba histórica en JForex

Preparación de FASE 6, 22/10/2026. El comparador CSV de TiresIAs está implementado.
Después de esta preparación el usuario confirma JForex y acceso demo. Ya existe
una [estrategia para el tester](../integrations/jforex/README.md), compilada contra
la API local y comprobada sin conexión. Su compilación/ejecución en la plataforma,
el lector del HTML nativo y el contraste externo siguen pendientes. La guía
conserva la preparación inicial; no acredita una prueba ejecutada en JForex.

## Descarga y acceso

La comprobación del registro de Windows y de las carpetas habituales del usuario
no encontró JForex. Esto no descarta instalaciones portables en otra ubicación.
Java y Maven están disponibles, pero el instalador oficial de JForex incluye su
propio entorno Java: no hace falta cambiarlos para instalar la plataforma.
[Instalación oficial](https://www.dukascopy.com/wiki/en/manuals/jforex4-desktop/installation/).

Se ha descargado, sin ejecutar, este instalador en el proyecto:

```text
.local/jforex/downloads/JForex4_windows-x64.exe
```

Versión observada: **4.23**, 70.667.784 bytes. SHA-256:

```text
de97aa5ca691a8f027a07da466a146022c8a05a7d327f0a887d626d2f81667e4
```

Windows devuelve firma Authenticode **Valid**, firmante **SWFX SA**. La URL procede
del manual oficial, utiliza HTTPS y la descarga no cambia de servidor. El ejecutable
permanece en `.local/`, excluido de Git; el informe guarda metadatos y huellas.

Pasos del usuario:

1. Abrir el instalador, revisar sus condiciones y completar la instalación.
2. Si no dispone de acceso, abrir la página oficial de
   [registro de demo JForex](https://www.dukascopy.com/swiss/english/forex/demo-fx-account/),
   seleccionar JForex y completar personalmente sus datos y condiciones. Esa página
   incluye CAPTCHA y consentimiento para contacto y comunicación de los datos a
   representantes del grupo. No se ha enviado ningún formulario.
3. Acceder a la aplicación con las credenciales recibidas. No copiarlas al proyecto,
   al chat o a la configuración del modelo. Basta confirmar versión y acceso al tester.
4. Abrir **View → Strategy Tester**. Detener aquí la preparación hasta disponer de
   la estrategia Java específica y haber revisado las reglas siguientes.

La demo permite acceder a la plataforma; este trabajo de FASE 6 se limita al
probador histórico. No habilita operativa prospectiva de la demo de FASE 7.

## Referencia Python conservada

| Propiedad | Valor de la referencia existente |
| --- | --- |
| Identificador | `72061a4aa7a0455cb400edcc580cb964` |
| Instrumento | EUR/USD |
| Estrategia | SMA 20/60, solo compra y cierre de la posición larga |
| Período UTC | 2025-01-01 incluido → 2025-12-25 excluido |
| Capital hipotético inicial | 1.000 USD |
| Cantidad fija | 1 EUR |
| Comisión supuesta por ejecución | 0,001 del importe, equivalente al 0,1 % |
| Sesiones | Días UTC observados, incluidos domingos y días parciales |
| Señal | Cruce de SMA sobre cierres BID; exige medias actual y anterior válidas |
| Ejecución | Primera apertura H1 observada de la siguiente sesión |
| Compra / venta / valoración | ASK / BID / BID |
| Final del período | No fuerza una venta final ni inventa una ejecución pendiente |

El exportado de preparación copia el resultado y sus entradas guardadas; no calcula
otra estrategia. Los fills de referencia están identificados como resultados Python,
no como ejecuciones del proveedor. No se modifican cuentas ni presupuestos del chat.

## Diferencia de cantidad que hay que resolver

La [API de JForex](https://www.dukascopy.com/wiki/en/development/strategy-api/orders-and-positions/order-amounts/)
expresa cantidades en millones y documenta un mínimo de 1.000 unidades para EUR/USD.
Por tanto, la referencia de 1 EUR no se puede enviar directamente como una orden
admitida. En la API, `0.001` representa 1.000 EUR; `1` representa 1.000.000 EUR.
La unidad que muestre un formulario de la plataforma debe comprobarse por separado.

En la preparación inicial se dejó propuesto otro caso de comparación: capital hipotético
de 1.000.000 USD y cantidad de 1.000 EUR, manteniendo la relación cantidad/capital.
Tras la confirmación del usuario se calcula como una referencia nueva e identificable,
con cantidad nativa y metadatos propios. No sustituye la anterior ni divide
artificialmente fills o comisiones externos.
El depósito de la cuenta demo no tiene que confundirse con el capital del tester.

Antes de calcular ese caso se verificará que el motor del tester admite los ajustes
necesarios de saldo, comisiones y tamaño. La tarifa real de JForex puede diferir
de la comisión proporcional supuesta: una tarifa agregada o redondeada no se
presentará como si fuera exactamente el 0,1 % por fill.

## Equivalencia pendiente

El [manual del Strategy Tester](https://www.dukascopy.com/wiki/en/manuals/jforex4-desktop/strategy-tester/)
explica selección de instrumento, intervalo, ticks o velas interpoladas y guardado
de mensajes e informes. Estos controles no garantizan que una vela diaria nativa
reproduzca nuestra agrupación UTC de H1 BID/ASK.

La estrategia específica debe usar únicamente `IEngine.Type.TEST`, rechazar otros
modos y comprobarse antes de cargarla. Debe reconstruir y exportar las sesiones y
señales necesarias para identificar diferencias de calendario, datos o ejecución.
El ejemplo genérico SMA de Dukascopy no se considera nuestra estrategia equivalente.

Orden de comprobación: precios H1 BID/ASK → sesiones UTC → calentamiento y señales
→ cantidades admitidas → confirmaciones de ejecución → comisiones y estado final.
Se fijarán los parámetros antes de mirar resultados y no se optimizarán en este paso.

Al ejecutar la prueba revisada se conservarán versión de plataforma, código y
parámetros, método de ticks/interpolación, zona y período, moneda y capital del
tester, informe HTML nativo, mensajes y cualquier exportación adicional necesaria.
El HTML por sí solo podría no incluir las comisiones o señales de cada fill;
eso se verificará con el archivo original. El adaptador no interpretará sus scripts
o enlaces como instrucciones.

## Estado de la preparación inicial

Instalador preparado y firma comprobada; referencia Python archivada y propuesta
de escala explícita. Sin instalación, alta, inicio de sesión, compilación Java,
backtest nuevo, operación, llamada al modelo, commit o push. Se conserva el estado
anterior de FASE 6 y no se actualiza PROJECT_STATUS.

## Avance posterior a la confirmación del usuario

Se localiza JForex 4.23 y API demo 4.9.8. `TiresiasSmaUtcTester.java` implementa
el recorrido exclusivo TEST y exportaciones para revisar datos y ejecuciones.
La referencia escalada ya se calcula una vez como resultado nuevo
`4e59e20a16b74fc7bd16ea7dad80d02d`, conservando el anterior intacto. Las pruebas
offline no son un backtest nativo. Usa las
[instrucciones actuales de la estrategia](../integrations/jforex/README.md) para
el siguiente paso; no necesitas volver a instalar ni registrar una demo.

## Primeros informes nativos: 23/10/2026

El usuario compila el fuente en JForex y aporta informes HTML y mensajes originales.
Los dos primeros intentos se detienen en `onStart` por método de datos vacío y
cuenta EUR, respectivamente. El siguiente usa USD, capital 1.000.000 y método
`candles_h1_4ohlc_bid`, pero se detiene el sábado 30/08/2025 a las 00:07:30 UTC
tras una solicitud rechazada como `System offline`. No hay fills y no se concluye
rentabilidad ni equivalencia con Python.

La estrategia v2 consulta el calendario histórico nativo antes de incorporar ticks
de interpolación: los de mercado cerrado no generan sesiones ni órdenes. Conserva
sus intervalos y contadores, los H1 originales y el detalle textual de los rechazos.
35 pruebas locales aprobadas contra la API instalada. Falta reimportar el fuente
actualizado en JCloud, compilarlo y ejecutar otra prueba histórica. Los informes
previos se conservan en `.local/jforex/prueba-historica-01/`; esta corrección no
modifica la referencia Python ni cierra FASE 6.

## Ensayo v2 completado: 23/10/2026

Tras reimportar la corrección, el informe `TiresiasSmaUtcTester_23102026_120254.html`
completa la prueba sin errores: dos compras, una venta y posición final de 1.000 EUR.
El patrimonio final informado es 999.988,68 USD, pérdida de 11,32 USD frente al
capital inicial. Las 307 sesiones, OHLC diarios, SMA y señales coinciden con la
referencia congelada. Hay cinco diferencias horarias de precio en tres velas H1;
los tres fills coinciden en precio/cantidad/señal y difieren 450 segundos en fecha
de ejecución. No se oculta esa diferencia con tolerancias temporales.

Los costes y la valoración requieren conciliación: el HTML presenta comisiones
0,06 USD frente a 0,05 USD sumando los agregados de órdenes, y conserva swaps hasta
dos días después del corte de estrategia. No se atribuye esa discrepancia a un
concepto concreto sin evidencia adicional. El detalle por fill sigue desconocido.
La exposición abierta se calcula con el saldo de fills y estado de órdenes, no
sumando `IOrder.getAmount` de órdenes cerradas. Originales privados conservados;
revisión en `reports/phase6-jforex-native-review-2026-10-23/`. Siguiente paso:
conciliar costes y valoración a igual fecha e integrar el flujo de contraste.

El [flujo de conciliación](JFOREX_RECONCILIATION.md) ya está integrado y conserva
el primer paquete v2. El ensayo v3 `TiresiasSmaUtcTester_23102026_125636.html` también
está completado: se han conservado las capturas reales de cuenta/órdenes cerca del
corte y al final. Sus parámetros y tres fills coinciden con v2. No necesitas
repetir este mismo ensayo; las diferencias y límites restantes están descritos en
la guía de conciliación. Esta prueba histórica no optimiza la estrategia ni
autoriza operativa demo o real.
