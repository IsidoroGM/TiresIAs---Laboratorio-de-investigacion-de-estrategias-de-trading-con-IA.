# Preparar la primera prueba histórica en JForex

Preparación de FASE 6, 22/10/2026. El comparador CSV de TiresIAs está implementado;
la estrategia Java equivalente, el lector del informe nativo y el contraste externo
siguen pendientes. Esta guía no acredita una prueba ejecutada en JForex.

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

Se deja **propuesto y sin calcular** otro caso de comparación: capital hipotético
de 1.000.000 USD y cantidad de 1.000 EUR, manteniendo la relación cantidad/capital.
Será una referencia nueva e identificable, con cantidad nativa y metadatos propios;
no sustituirá la anterior ni dividirá artificialmente fills o comisiones externos.
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

## Estado de esta entrega

Instalador preparado y firma comprobada; referencia Python archivada y propuesta
de escala explícita. Sin instalación, alta, inicio de sesión, compilación Java,
backtest nuevo, operación, llamada al modelo, commit o push. Se conserva el estado
anterior de FASE 6 y no se actualiza PROJECT_STATUS.
