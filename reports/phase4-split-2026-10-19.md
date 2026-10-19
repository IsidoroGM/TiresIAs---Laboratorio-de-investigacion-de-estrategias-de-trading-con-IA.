# FASE 4 — Primera separación cronológica

Fecha: 19 de octubre de 2026. Preparación comprobada; fase abierta.
El usuario eligió **2020-01-01** como corte antes de preparar los bloques.
No se han calculado rentabilidades, drawdowns ni veredictos de evaluación.

| Bloque | Primera observación | Última observación | Observaciones por par |
|---|---|---|---:|
| Desarrollo | 1999-01-04 | 2019-12-31 | 5375 |
| Evaluación reservada | 2020-01-02 | 2026-10-16 | 1741 |

La evaluación comienza el 2 de enero porque no hay observación publicada en la
copia para el día del corte. La regla sigue siendo desarrollo < 2020-01-01 y
evaluación >= 2020-01-01, sin ajustes basados en resultados.

## Procedencia e integridad

Fuente: `data/raw/ecb-eurofxref-hist-2026-10-18.xml`, 7116 observaciones por par.
SHA-256 original:
`3cb610894f5098c82e39c476e1593033565565eb66570051c9304fbf708978e9`.

Preparación local: `.local/validation/fa8106cf47ab475a973a2f84cfd1ee97/`.
El manifiesto y ambos XML se conservan allí, excluidos de Git.

- `development.xml`: `9b703b20333ef2d962d372fdfb9bf6c700f44ad2dace3d63e4d7ecf4edae58a5`.
- `evaluation.xml`: `d4de382e518ac7b85598ee08011fd9de91e00248611423bfc726ef306d4e7f26`.

Se verificaron los bytes del original y de ambos archivos contra estos hashes.
Para EUR/USD, GBP/USD, USD/JPY y USD/CHF, concatenar las referencias leídas de
desarrollo y evaluación reproduce exactamente las referencias del original,
incluidas fechas y valores. No hay solapamientos, referencias perdidas ni
modificación del original. La generación es determinista para la misma entrada
y corte; cada preparación utiliza una carpeta distinta.

## Pruebas

**423 pruebas aprobadas**, incluidas 24 nuevas, con caché pytest desactivada y
una carpeta temporal nueva y exclusiva según `AGENTS.md`.

Se comprobaron frontera inclusiva en evaluación, huecos de calendario, los
cuatro pares, entradas inválidas, bloques vacíos, cambios de fuente durante
la preparación, hashes y conservación de preparaciones anteriores. Una prueba
modifica únicamente precios futuros y confirma que los datos y mensajes de una
investigación sobre desarrollo no cambian, salvo su identificador único.

Las pruebas del comando comprueban que no consulta IA ni ejecuta backtests.
La comprobación real solo lee los bloques para verificar conservación; no
calcula métricas ni usa evaluación para elegir una variante.

## Alcance pendiente

Este paso prepara datos y documenta cuentas independientes, sin señales ni
posiciones heredadas y con calentamiento dentro de cada bloque. Todavía no
implementa la congelación de propuestas ni un flujo de evaluación que la exija.
El agente de FASE 3 conserva su configuración predeterminada; usar explícitamente
`--data` con `development.xml` para investigar solo desarrollo.

El histórico completo ya se exploró en fases anteriores. Esta separación es
una comprobación del procedimiento, no evidencia totalmente inédita ni
demostración de rentabilidad. No se han instalado dependencias, usado APIs de
pago, iniciado conexiones externas ni realizado operaciones con dinero real.
`PROJECT_STATUS.md` conserva el cierre de FASE 3. Sin commits ni pushes.

Siguiente tarea: guardar una propuesta, criterio y controles fijos antes de
permitir su evaluación sobre el bloque reservado, siguiendo el
[protocolo de FASE 4](../docs/VALIDATION_PLAN.md).
