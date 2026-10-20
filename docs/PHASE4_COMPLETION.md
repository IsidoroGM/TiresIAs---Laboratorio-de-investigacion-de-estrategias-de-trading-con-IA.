# FASE 4 completada — TiresIAs

Cierre de desarrollo educativo: **20/10/2026**, **1547 pruebas aprobadas**.
[Informe y evidencia del cierre](../reports/phase4-completion-2026-10-20.md).

Este documento reúne el alcance de cierre: validación educativa reproducible y
un ciclo local acotado. No equivale a demostrar rentabilidad, robustez estadística
o capacidad para operar con dinero real. El histórico utilizado ya es conocido.

## Ciclo de investigación local

`campaign_context.py` incorpora el historial original completo y las entradas del
ciclo, incluidos resultados negativos, errores, revisión y consumo. Un diccionario
reversible de claves y cadenas repetidas reduce metadatos sin resumir textos. Las
pruebas reconstruyen el historial original y comprueban que la segunda petición
contiene los resultados de la primera. Si no cabe, el ciclo se detiene sin recortes.

La captura conserva mensajes y la huella del esquema fijo. El esquema se transmite
íntegro a Ollama. Límites del contrato nuevo: captura 12 KiB, mensajes más esquema
24 KiB, modelo 4096 tokens, salida 384 tokens, CPU y timeout de 180 s. El número de
bytes no garantiza el encaje en tokens. Se conservan las opciones que rechazan
desbordamientos sin truncar o desplazar contexto, la comprobación de versión
0.40.6 y la vinculación del digest del modelo. No se modifica el adaptador compacto
histórico ni se usa su intento heredado como permiso nuevo.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.campaign_cycle prepare --scope <ambito-registrado>
.\.venv\Scripts\python.exe -m trading_ai.campaign_cycle run --permit <permiso> --allow-local-generation --allow-virtual-calculations
.\.venv\Scripts\python.exe -m trading_ai.campaign_cycle inspect --run <ciclo-completado>
.\.venv\Scripts\python.exe -m trading_ai.campaign_cycle status --run <intento>
```

Solo se utiliza el servidor local ya instalado; el programa no arranca servicios,
descarga modelos, instala dependencias o utiliza OpenAI. No hay sustitución por un
servicio de pago. Cada petición se reserva antes del envío en SQLite y se conserva
su captura original. La identidad de ámbito sigue siendo datos y par: cambiar la
carpeta no reinicia límites. El máximo registrado sigue siendo tres propuestas y
seis backtests; cada comparación consume dos juntos. Un intento de ciclo exclusivo
por ámbito impide repetir automáticamente una campaña interrumpida o completada.

El contrato comienza sin reservas de campaña anteriores; no migra pendientes ni
reinterpreta capturas de otros protocolos. Los nueve intentos históricos y la
reformulación consumida permanecen intactos. La fila contable conserva su estado
histórico inactivo: por sí sola no concede ejecución. La habilitación procede del
permiso nuevo y de las dos opciones explícitas del ejecutor.

## Revisión y cálculos separados

El contrato nuevo admite únicamente **experimentos virtuales de reglas tipadas
cerradas**, con una entrada y salida precisas. Python valida el vocabulario,
normaliza constantes, comprueba identidades consumidas y disponibilidad para
calentamiento y ejecución posterior. Esa revisión mecánica queda guardada antes
del plan y el cálculo. No interpreta prosa ni afirma que el significado de una
idea ambigua haya sido revisado por una persona. `semantic_acceptance` permanece
en `false`; ninguna candidata se adopta automáticamente.

Es una ruta distinta de los permisos/revisiones manuales v1, que conservan sus
contratos y sus bytes. No se simulan sus propuestas pendientes. Los lectores v1
no son el inspector de este ciclo; para sus capturas, resultados y consumo se
utiliza `campaign_cycle inspect/status`.

Los datos, capital, costes, tamaño y criterio proceden del registro congelado.
El modelo no los controla. Antes de cada cálculo se comprueban permiso, fuentes,
reservas y archivos anteriores. Se usa el motor existente con cuentas independientes,
ejecución posterior y sin cierre forzado. El criterio se calcula con Python.
La reserva compartida del motor bloquea repetir un cálculo aunque cambie su nombre
o la carpeta. Los cálculos parciales y los fallos conservan sus intentos; no se
liberan reservas ni se reconstruyen resultados que falten.

Duplicados, reglas inválidas, falta de datos, errores del proveedor, cambios de
identidad/fuentes, consumo desconocido o contexto insuficiente detienen el ciclo.
El estado de una ejecución fallida se consulta sin modelos ni nuevos cálculos.
La procedencia registrada vincula mensajes y JSON del transporte controlado con
el modelo identificado; es evidencia local, sin firma externa o prueba criptográfica
de autoría. No se atribuye al modelo la descripción mecánica escrita por Python.

## Walk-forward sobre desarrollo conocido

`walk_forward.py` toma la variante SMA/EMA previamente congelada, sin elegir una
estrategia nueva por preferencia del desarrollador. Fija antes de calcular cinco
variantes mecánicas de ventanas: original, rápida ±1 y lenta ±1; omite las inválidas
o idénticas a la base. Los costes y restantes controles permanecen congelados.

Se divide desarrollo en cuatro bloques contiguos por número de observaciones:
entrenamiento expansivo en el primer bloque, primeros dos y primeros tres;
comprobación en el bloque inmediatamente posterior de cada ventana. El primer
tramo debe permitir calentamiento y una observación posterior.

En cada ventana se calculan la base y todas las variantes solo con entrenamiento.
Se exige cumplir el criterio frente a la base y tener cierres. Los desempates son
rentabilidad descendente, drawdown ascendente, ventanas ascendentes e identidad.
La selección se escribe y sincroniza a disco **antes** de cargar el tramo en el
cálculo de comprobación. La validación de procedencia puede leer el XML completo
de desarrollo antes: comprueba datos y referencias, sin calcular métricas de los
tramos de comprobación para el selector. Solo después de fijar la selección se
comparan la base y la seleccionada. Si no hay
elegibles, se conserva la selección vacía y no se fuerza un ganador o comprobación.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.walk_forward prepare --frozen-run <registro-desarrollo>
.\.venv\Scripts\python.exe -m trading_ai.walk_forward run --plan <plan>
.\.venv\Scripts\python.exe -m trading_ai.walk_forward verify --run <resultado>
```

Máximo: 24 backtests y cero consultas al modelo. Es un protocolo de robustez
separado del presupuesto de seis backtests de la campaña de nuevas ideas. Ambos
tienen identidad global, reservas exclusivas y ausencia de reintentos. Los
resultados de cada cuenta se mantienen separados, sin sumar capitales o componer
rentabilidades de cuentas independientes. El verificador no repite backtests.

La separación y este protocolo se han diseñado con datos ya consultados: se
comprueba el procedimiento, **no se acredita validación independiente**. La
sensibilidad de costes anterior y la primera evaluación histórica se conservan.
La validación prospectiva sigue necesitando datos posteriores no observados al
fijar las reglas. TradingView y los adaptadores de bróker pertenecen a fases futuras.

## Comprobación del cierre

Las primeras 31 pruebas de esta integración pasan sobre fuentes artificiales con
el motor real, sin red real. Incluyen el ciclo completo con verificadores originales,
memoria de resultados, concurrencia, identidad del modelo, carreras del registro,
consumo desconocido, fallos parciales, selección vacía y selección duradera antes
de cargar el tramo en el cálculo de comprobación. La colección completa pasó en
tres procesos aislados de 459, 575 y 513 pruebas, con temporales exclusivos y
caché desactivada. Se verifican 430 copias y referencias entre 25 inventarios,
conservando los 131 archivos de código/pruebas de la revisión.

La comprobación local ya realizada consumió una consulta nueva: 2898 tokens de
entrada y 180 de salida, 0 USD API. El modelo devolvió una identidad conocida y
se detuvo en `duplicate_rules`, sin simularla o reintentar. Es un descarte real,
no una nueva estrategia válida. Las pruebas artificiales comprueban por separado
el recorrido con candidatas nuevas y memoria para la siguiente petición.

El walk-forward real calculó 20 backtests de los 24 máximos. La primera ventana
seleccionó una variante que no cumplió el criterio al comprobarla: mayor
rentabilidad, pero también mayor drawdown. Las otras dos no seleccionaron
candidata. No se modificó la selección a partir de esos resultados.
