# Diagnósticos por periodos conocidos

`compact_periods` prepara dos o tres bloques cronológicos de un plan compacto
con revisión aceptada. Divide por número de observaciones, conserva todas las
fechas y referencias, sin solapamientos, rellenos o exclusión del peor periodo.
Las reglas, base, criterio, costes, capital y tamaño se copian sin ajustes.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.compact_periods prepare --plan-run <plan> --periods 3
.\.venv\Scripts\python.exe -m trading_ai.compact_periods verify --run <diagnostico>
```

Cada periodo tendrá dos cuentas virtuales independientes. El calentamiento se
hará dentro del bloque, sin posiciones o señales heredadas y sin cierre forzado
al final. Los bloques cortos pueden quedar sin operaciones; deben conservarse y
explicarse como inconclusos. No se elegirá el bloque ganador ni se compondrán sus
rentabilidades como si fueran una sola cuenta.

La preparación fija los XML y sus huellas, fechas, límites y máximo de seis
backtests futuros. No calcula ni reserva simulaciones. La campaña tendrá un solo
intento por cálculo de origen: cambiar de dos a tres periodos o de carpeta no
libera otra campaña. Comparte además las identidades individuales con los otros
ejecutores de reglas. La ejecución requiere una acción explícita separada.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.compact_period_execution execute --plan-run <diagnostico>
.\.venv\Scripts\python.exe -m trading_ai.compact_period_execution verify --run <ejecucion>
```

El ejecutor reserva la campaña y todos los cálculos de bloques antes del primer
backtest. Una colisión posterior conserva las reservas ya creadas y no calcula
otros bloques. Si falla el motor, conserva los resultados parciales y el intento;
no cambia de dos a tres periodos para continuar. Usa las mismas herramientas de
cálculo del motor, sin consultas a IA o una contabilidad alternativa.

Conserva datos, contabilidad, resúmenes y criterio de todos los bloques, con un
informe por campaña. Los recuentos de estados no se interpretan como una tasa de
éxito operativa, ni como rentabilidad de una cartera. La lectura verificada
contrasta las fuentes, reservas, artefactos y criterios sin repetir los backtests.

La herramienta no selecciona estrategias, entrena parámetros o ejecuta una
selección walk-forward. Sirve para preparar diagnósticos de una regla fija sobre
desarrollo ya conocido. No abre evaluación exterior ni convierte los bloques
en evidencia inédita. Las comprobaciones actuales usan datos artificiales;
la candidata real duplicada no tiene un plan aceptado y no se utiliza aquí.
