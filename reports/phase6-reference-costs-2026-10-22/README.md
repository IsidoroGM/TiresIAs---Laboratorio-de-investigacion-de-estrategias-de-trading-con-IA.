# Referencias y comisiones fijas para SMA 20/60

22/10/2026. Incremento de FASE 6. `protocol.json` se guarda antes de calcular los
nuevos resultados. Períodos, parámetros y datos conservan la validación anterior.
No se cierra FASE 6, modifica PROJECT_STATUS ni realiza commit o push.

## Diseño y resultado

1.000 USD hipotéticos, cantidad fija de 1 EUR, SMA 20/60 y cuatro comisiones
supuestas por ejecución: 0 %, 0,05 %, 0,1 % y 0,2 %. Referencias: efectivo USD
sin intereses y comprar/mantener la cantidad fija tras 61 sesiones completas.
La apertura de referencia coincide con la primera posible ejecución de una
decisión SMA tras el calentamiento, no con una fecha elegida por rentabilidad.
Se conservan domingos y días parciales; se necesitan 62 sesiones observadas.

Se compra a ASK, se vende y valora a BID. El spread no desaparece con comisión
cero. No hay reinversión, apalancamiento, salida final forzada ni una comisión de
salida inventada. Comprar/mantener conserva 1 EUR abierto. No se ajustan diferencias
por exposición ni se verifican swaps, deslizamiento o liquidez.

| Año | Comisión por ejecución | SMA, USD | Comprar y mantener, USD |
| --- | ---: | ---: | ---: |
| 2024 | 0 % | 999,97485000 | 999,94603000 |
| 2024 | 0,05 % | 999,971589755 | 999,945483455 |
| 2024 | 0,1 % | 999,96832951 | 999,94493691 |
| 2024 | 0,2 % | 999,96180902 | 999,94384382 |
| 2025 | 0 % | 999,99221000 | 1000,08854000 |
| 2025 | 0,05 % | 999,990457235 | 1000,087995700 |
| 2025 | 0,1 % | 999,98870447 | 1000,08745140 |
| 2025 | 0,2 % | 999,98519894 | 1000,08636280 |

El efectivo conserva 1.000 USD. SMA queda por debajo en los ocho escenarios,
incluido cero comisión. Supera a comprar/mantener en 2024 y queda por debajo en
2025. No se elige un ganador ni se concluye robustez a partir de pocas operaciones.
Los años completos de 2024 y 2025 siguen bloqueados por huecos, sin métricas.

## Implementación y comprobación

`market_benchmark` verifica el histórico, utiliza el motor SMA existente y calcula
las referencias. Guarda entradas, escenarios completos, reglas, versiones y un
resumen acotado. El listado solo lee resúmenes; la ficha contrasta sus copias sin
calcular señales. El POST explícito conserva origen, token y bloqueo de escritura.
Las cuentas virtuales y el inbox no cambian.

391 pruebas seleccionadas aprobadas, 28 nuevas de aritmética, causalidad, calidad,
saldo, integridad y HTTP; no se ejecuta la colección completa. Pytest usa caché
desactivada y temporal exclusivo según AGENTS.md. Se comprueba sintaxis JavaScript.

Una reconstrucción independiente desde ambos gzip, sin módulos del proyecto,
reproduce todas las medias, señales, costes, 44 ejecuciones y 4.920 puntos de
patrimonio/drawdown de SMA y referencia en los ocho escenarios. La tasa 0,001
coincide con los resultados SMA anteriores. Se prueba el botón real en navegador
y el selector de comisión, incluido cero. Las capturas muestran resultados reales.

`manifest.json` inventaría fuentes probadas, copias de resultados, protocolo,
auditoría, pruebas y capturas. Se verifican sin modificación las evidencias
anteriores. Los originales permanecen en `.local/`, con atribución a EV Trading
Labs conservada; sus huellas detectan cambios y no autentican al proveedor.
