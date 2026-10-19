# Ejecutor de planes de reglas

`trading_ai.rule_execution` ejecuta un [plan registrado y revisado](RULE_PLANNING.md).
Verifica toda su procedencia, datos, código y controles antes de reservar el
intento. Usa el motor existente: una cuenta para la base y otra para la candidata,
con el mismo capital, costes y tamaño. No consulta IA ni modifica las reglas.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.rule_execution --plan-run <plan> --frozen-run <registro-previo>
```

Se puede elegir `--output-dir`; no se pueden cambiar estrategia, parámetros,
capital, costes, datos o presupuesto mediante esta CLI. Como máximo calcula
una base y una candidata, sin barridos de parámetros ni reintentos automáticos.
El plan sigue siendo el registro original `registered_not_run`: no se modifica
al ejecutarlo. El resultado y la reserva compartida registran lo sucedido.

## Reserva antes de calcular

La identidad del cálculo incluye reglas, datos, base, controles y supuestos de
ejecución. Excluye el nombre técnico de la candidata y el criterio de análisis,
porque cambiarlos no cambia esos cálculos. No demuestra equivalencia matemática
entre reglas escritas de otras formas.

Se crea una marca exclusiva en `.local/rule-execution-access` antes de generar
señales o simular. El registro es compartido e independiente de la carpeta de
salida. Copiar el plan, prepararlo otra vez, crear otra revisión con las mismas
reglas o renombrar la candidata no permite repetir el cálculo. Dos procesos
concurrentes no pueden reservar la misma identidad.

Una reserva consume el intento completo, aunque falle después antes de terminar
las dos simulaciones. No se libera automáticamente. Una interrupción abrupta
puede dejar solo los últimos eventos y la marca; tampoco libera el intento.
Un plan inválido rechazado antes de reservar no consume ese acceso.

Las marcas son archivos locales, no una protección contra borrado o manipulación
deliberados. Conservarlas forma parte del historial del laboratorio. Cambiar
código no libera automáticamente una identidad ya reservada. Esto tampoco es
un presupuesto global para estrategias diferentes ni limita usos manuales del
motor fuera de este flujo.

## Datos y resultados

Se copia el desarrollo fijado a la carpeta del intento y se verifica su hash y
cobertura. Ambos cálculos usan las mismas observaciones inmutables. Se verifica
de nuevo el plan, sus fuentes, el código, la copia de datos y la marca antes de
cada cálculo y antes de publicar resultados completos.

El motor conserva la ejecución en la referencia siguiente, el calentamiento
dentro del periodo, las posiciones largas y la contabilidad independiente.
Las posiciones abiertas se valoran sin cierre forzado. No hay arrastre desde
otras simulaciones ni acceso a evaluación exterior.

Cada intento se registra en `.local/rule-executions/<id>`:

- `events.jsonl`: reserva, presupuesto usado por papel, cálculos, errores y cierre.
- `development.xml`: copia exacta de los datos utilizados.
- `baseline.json` y `candidate.json`: resumen, hash de señales y contabilidad
  completa del motor, con operaciones, posiciones y curva de capital.
- `results.json`: comparación, criterio, conclusión de Python, hashes y consumo.
- `report.md`: lectura de la comparación y sus límites.

El criterio es el fijado en el plan. Con cero cierres en cualquiera de las dos
estrategias o con ambas métricas iguales, el resultado es inconcluso. Cumplirlo
no demuestra que una propuesta sea mejor en general. El alcance es
`known_development_history_only`: este histórico ya es conocido y no se
presenta como una prueba inédita. La revisión técnica sigue siendo una declaración
de comprobaciones; el ejecutor no demuestra equivalencia con el lenguaje natural.

## Lectura verificada y fallos

```powershell
.\.venv\Scripts\python.exe -m trading_ai.rule_execution --verify-run <ejecucion> --frozen-run <registro-previo>
```

Verificar es de solo lectura y no recalcula. Exige el evento final
`execution_completed`, los hashes de resultados, informe y archivos calculados,
la marca original y coincidencia con el plan y sus fuentes actuales. Una copia
de evidencias para archivo se compara mediante hashes; no se presenta como una
nueva ejecución con otra reserva.

Si falla un cálculo, se conservan los anteriores y el error. Si falla la escritura
del informe, puede existir `results.json` sin cierre correcto: **ese archivo por
sí solo no acredita una ejecución completa**. El verificador lo rechaza.
Cambios posteriores en código, datos o fuentes también pueden invalidar la
verificación; los archivos históricos permanecen conservados.

Comprobación: **699 pruebas aprobadas**, incluidas 30 nuevas del ejecutor.
La [evidencia de desarrollo](../reports/phase4-rule-execution-2026-10-19.md)
distingue un ejemplo artificial calculado en pytest del borrador real bloqueado.
Cero consultas de IA y cero coste de API. Sin dependencias nuevas ni operaciones
reales. OpenAI sigue desactivado y TradingView no está conectado.

Las [reformulaciones y lecturas contrastadas](AGENT_FEEDBACK.md) permiten proponer
una revisión explícita de una idea con dudas y contrastar una conclusión sobre
estos resultados. No ejecutan otros experimentos. FASE 4 permanece abierta; no se actualiza
`PROJECT_STATUS.md` ni se autorizan commits o pushes con este paso.
