# TiresIAs — cierre de FASE 4

20/10/2026. Inicio en `main`, HEAD `3d0fa83`, conservando las 32 entradas
pendientes. **FASE 4 completada en su alcance de desarrollo educativo**, con
comprobación local, colección completa aprobada y evidencia sellada.

## Alcance entregado

| Requisito | Implementación y evidencia |
| --- | --- |
| Separación cronológica | Corte elegido 2020-01-01, cuatro pares, manifiesto, datos sin solapamiento. [Separación histórica](phase4-split-2026-10-19.md). |
| Registro previo y evaluación | Propuesta/control congelados, cuentas independientes y acceso exclusivo. [Registro](phase4-freeze-2026-10-19.md), [evaluación histórica](phase4-evaluation-2026-10-19.md). |
| Sensibilidad y selección interna | Ventanas y costes registrados, selección antes de comprobar, resultados negativos conservados. [Robustez interna](phase4-robustness-2026-10-19.md). |
| Reglas adicionales acotadas | Vocabulario tipado para referencia, SMA/EMA, mínimos/máximos móviles y retardos; sin código libre de IA. |
| Memoria de resultados | Historial completo, descartes, errores, consumo y resultados de Python para la siguiente petición; codificación reversible sin recortes. |
| Ciclo local | Nueva ruta `campaign_cycle` con permiso, dos habilitaciones explícitas, transporte local identificado y revisión mecánica separada de cálculos. |
| Varios tramos temporales | Tres ventanas expansivas predefinidas sobre desarrollo conocido, sin reelección después de la comprobación. |
| Presupuestos y conservación | Tres propuestas/seis backtests de campaña; protocolo de robustez con máximo 24 backtests aparte. Reservas exclusivas y sin reintentos. |

Guía: [integración y comandos](../docs/PHASE4_COMPLETION.md). Los contratos v1 y
sus evidencias conservan sus bytes. La revisión automática nueva permite solo
experimentos virtuales con reglas cerradas; `semantic_acceptance: false` evita
atribuir una aceptación humana o resolver prosa ambigua. No se simulan los
borradores pendientes de otros protocolos ni se reabre la reformulación consumida.

## Comprobación real del modelo local

Servidor del proyecto ya en ejecución: Ollama 0.40.6 y Qwen3.5:4b, CPU,
contexto 4096, salida máxima 384, sin recortes o desplazamientos de contexto.
No se instalaron paquetes, descargaron modelos o iniciaron servicios nuevos.

Ciclo `eaba7b8479034eb69e52838fa1919715`: **una consulta nueva**, 2898 tokens de
entrada, 180 de salida, seis consultas de metadatos y **0 USD API**. La respuesta
repitió una identidad conocida y terminó en `duplicate_rules`: **cero backtests
de esa candidata**, sin reintento o adopción. No se presenta como estrategia nueva
o como demostración de búsqueda fiable del modelo.

El registro conserva dos huecos de propuestas y seis de backtests; la reserva
exclusiva de ciclo impide reabrirlo automáticamente. Los nueve archivos de intentos
históricos conservan sus huellas. Consumo compacto heredado separado: 2262 tokens
de entrada y 176 de salida, 0 USD API. Ninguna de esas cifras representa el total
histórico de la aplicación.

## Walk-forward real: resultado negativo conservado

Protocolo sobre el desarrollo anterior a 2020, ya explorado. La familia parte de
la EMA20/60 previamente congelada; sus cinco variantes ±1 se registran antes de
los cálculos. El modelo no modifica capital, coste, tamaño, fechas o criterio.
Se calculan **20 backtests de un máximo de 24**, sin consultas al modelo.

| Ventana | Entrenamiento | Comprobación | Selección y resultado |
| --- | --- | --- | --- |
| 1 | 1999-01-04 a 2004-04-01 | 2004-04-02 a 2009-07-02 | EMA19/60; criterio no cumplido. |
| 2 | 1999-01-04 a 2009-07-02 | 2009-07-03 a 2014-09-26 | Sin elegible; no se fuerza una comprobación. |
| 3 | 1999-01-04 a 2014-09-26 | 2014-09-29 a 2019-12-31 | Sin elegible; no se fuerza una comprobación. |

En la primera comprobación, SMA20/60 obtiene 0,425809 % de rentabilidad acumulada
y 1,746293 % de drawdown; EMA19/60, 1,189731 % y 1,914928 %. La candidata aumenta
ambas métricas: incumple el criterio de mayor rentabilidad sin más drawdown.
No se elige otra configuración después de verlo.

Cada cuenta y calentamiento son independientes; no se suman capitales de ventanas
ni se presenta su producto como una curva continua. La selección se sincroniza a
disco antes de cargar el tramo en el cálculo de comprobación. La validación de
procedencia puede leer el desarrollo completo antes, sin suministrar métricas de
comprobación al selector.

Comprobación real: `bdd6a55c937f4f2abc272a9ad2d64625`. Cero intentos de acceso al
bloque exterior o red fuera del servidor local. Controles y límites de SQLite
intactos; 332 copias y referencias anteriores verificadas antes y después.

## Verificación y limitaciones

Las 31 pruebas focalizadas nuevas pasan en 134,42 s, con motor real y fuentes
artificiales, sin red real. Incluyen integración con los validadores originales,
memoria íntegra para la siguiente petición, duplicados, consumo desconocido,
cambios de modelo, carreras de reserva, concurrencia, errores parciales, alteraciones
y selección fijada antes de la comprobación. Los primeros pases detectaron el
exceso de bytes por duplicar el esquema en la captura; se corrigió fijándolo por
huella y transmitiéndolo íntegro, sin recortar el historial.

La colección global contiene **1547 pruebas aprobadas** en tres procesos aislados:
459 en 998,22 s; 575 en 1194,79 s; 513 en 1075,35 s. Se ejecutaron en paralelo;
los tiempos no se suman como duración transcurrida. La unión coincide con la
colección prevista sin omisiones, duplicados, errores o saltos. Se mantuvieron
intactos los 131 archivos de código y pruebas. Caché pytest desactivada y un
temporal nuevo exclusivo por proceso; sin cambios de permisos generales de Windows.

El primer cotejo de identificadores JUnit detectó diferencias de barras en nombres
parametrizados de Windows. Se aplicó al cotejo la misma normalización de la
colección, rechazando colisiones. No cambió el código de la aplicación ni se
repitieron los backtests o las consultas locales.

Este cierre acredita herramientas y controles del laboratorio educativo. La
evaluación exterior 2020–2026 y el desarrollo 1999–2019 ya eran conocidos: no se
reutilizan como validación independiente o inédita. No se demuestra suficiencia
estadística, rentabilidad general o selección fiable del modelo. La evaluación
prospectiva requiere datos futuros no observados al fijar el protocolo.

TradingView, la interfaz, paper trading externo y bróker siguen en fases futuras.
OpenAI permanece reservado y desactivado. No hay operaciones reales, commits o pushes.

## Evidencia final

Auditoría `3f5f81a4fbf04bbcb7b0894c14a899aa`. El sellado verifica el ciclo, los
resultados del walk-forward y las fuentes actuales con red, reservas y recálculos
bloqueados: cero acciones nuevas durante esa verificación. Se conservan las 332
copias y referencias anteriores y se añaden 98: **430 entre 25 inventarios
concretos**, sin presentarlas como archivos físicos únicos.

- [Inventario y huellas](phase4-completion-2026-10-20/snapshot.json).
- [Registro de cierre y pruebas](phase4-completion-2026-10-20/closure/closure.json).
- [Ciclo local y consumo original](phase4-completion-2026-10-20/cycle/cycle.json).
- [Resultados por ventana](phase4-completion-2026-10-20/walk-run/results.json).

El registro de aplicación se escribió antes de la suite y conserva aquel estado;
el registro de cierre contiene el resultado posterior completo. `PROJECT_STATUS.md`
se actualiza únicamente ahora, al cerrar la fase. El siguiente desarrollo es
FASE 5: interfaz de consulta del laboratorio; no se inicia con este cierre.
