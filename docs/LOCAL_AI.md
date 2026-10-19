# Investigador local — FASE 3 completada

La primera integración utiliza Ollama y `qwen3.5:4b` en el ordenador del usuario.
No requiere claves ni pagos por consultas a una API. Consume memoria, tiempo de
cálculo y electricidad. La calidad y la velocidad deben comprobarse con tareas
representativas; la capacidad de proponer una variante no demuestra su utilidad.

## Preparación y arranque en Windows

Desde la raíz del proyecto, en la sesión habitual de PowerShell:

```powershell
.\scripts\Install-LocalAI.ps1
.\scripts\Start-LocalAI.ps1 -PullModel
.\.venv\Scripts\python.exe -m trading_ai.research --check
```

El instalador prepara la distribución portátil oficial de Ollama **v0.40.6**,
con SHA-256 fijado y verificado. El archivo comprimido ocupa aproximadamente
1,47 GB; el modelo descarga aproximadamente 3,3 GB adicionales. Los binarios
extraídos requieren más espacio. No se modifica PATH ni el inicio de Windows.
No se añaden dependencias Python: la integración utiliza la biblioteca estándar.

Los ejecutables, el archivo de instalación, los modelos y los registros del
proyecto se guardan en `.local/`, excluido de Git. El servidor escucha en
`127.0.0.1:11435`, con `OLLAMA_NO_CLOUD=1`, una petición simultánea y contexto
de 4096 tokens. No se expone a la red local. El adaptador omite proxies y bloquea
redirecciones; únicamente admite direcciones IP de loopback.

La configuración inicial utiliza **CPU** (`gpu_layers: 0`). En la primera prueba,
Ollama detectó la GTX 1050 Ti pero falló al cargar el modelo por una incompatibilidad
de PTX/CUDA con el controlador 560.94. No se han actualizado controladores. La opción
se registra en cada ejecución; la aceleración GPU deberá volver a comprobarse antes
de cambiarla. La inferencia en CPU puede tardar más.

`-PullModel` se utiliza para descargar o verificar el modelo expresamente. En
los siguientes arranques basta con:

```powershell
.\scripts\Start-LocalAI.ps1
```

El script reutiliza una instancia identificada como propia. Si el puerto está
ocupado por otra instancia, se detiene con un error. El investigador nunca inicia
un servidor ni descarga modelos por su cuenta.

## Primera investigación

```powershell
.\.venv\Scripts\python.exe -m trading_ai.research --pair EUR/USD
```

Cada ejecución realiza como máximo dos peticiones al modelo:

1. Solicita una propuesta JSON que identifica hipótesis, criterio y herramienta
   `run_experiment`, con estrategia SMA/EMA y ventanas acotadas. Python valida
   todos los campos antes de invocar la herramienta. No se ejecuta código del modelo.
2. Python comprueba primero si ambas estrategias registran operaciones cerradas.
   Si alguna tiene cero cierres, genera una conclusión inconclusa con su motivo
   y omite la petición de análisis al modelo. Si ambas tienen cierres, devuelve
   al modelo el resumen calculado y solicita una valoración estructurada. La
   aplicación comprueba cada comparación y el veredicto contra los números;
   una valoración incorrecta se rechaza y queda registrada.

Los supuestos iniciales son explícitos: base SMA20/60, capital virtual de 1000
en moneda cotizada, coste de 0,1 % por ejecución y asignación del 10 % del efectivo.
La variante usa los mismos datos, capital, costes y tamaño. El modelo no puede
modificarlos ni elegir rutas de archivos, código, herramientas adicionales u órdenes.
Las ventanas rápida y lenta deben ser enteras positivas, rápida < lenta,
rápida <= 120 y lenta <= 252 observaciones. La variante debe diferir de la base.

Los dos criterios admitidos son:

- Rentabilidad acumulada estrictamente mayor sin aumentar el drawdown máximo.
- Drawdown máximo estrictamente menor sin reducir la rentabilidad acumulada.

Si alguna estrategia no tiene cierres o ambas métricas empatan, el resultado se
considera inconcluso. Cumplir un criterio significa únicamente que se cumple en
esa muestra histórica. No se valida fuera de muestra, no se seleccionan ganadores
automáticamente y no se generan órdenes de dinero real. TradingView sigue pendiente
según [su plan](TRADINGVIEW_PLAN.md).

El control de cero cierres identifica si falta información en la base, en la
variante o en ambas. Conserva todas las métricas, incluidas las posiciones
abiertas: cero cierres no significa ausencia de exposición. Esta regla forma
parte del alcance actual y no establece cuántas operaciones demostrarían
robustez. Los empates de métricas cuando ambas estrategias tienen cierres
siguen pasando por el análisis de IA y su comprobación.

Una ejecución inconclusa por cero cierres utiliza una petición de IA para la
propuesta y ninguna para el análisis. El informe indica expresamente que la
conclusión procede de Python. Esto evita una decisión de IA sobre suficiencia;
no implica que el modelo haya mejorado su interpretación de datos insuficientes.

Los criterios son acotados para poder verificar el primer agente; no son una
evaluación completa de la viabilidad de una estrategia. El texto de la hipótesis
es una propuesta de la IA, no una fuente de resultados comprobados.

## Configuración y proveedores futuros

`config/ai.example.json` documenta los valores predeterminados. Para personalizarlos:

```powershell
Copy-Item config/ai.example.json config/ai.local.json
```

El archivo personal está excluido de Git. También se puede elegir un archivo
con `--config`. El modelo debe estar descargado previamente; no hay descargas ni
reintentos automáticos. Cada respuesta tiene un máximo de 384 tokens por defecto
y se solicita sin salida de razonamiento. Las respuestas truncadas se rechazan.

`ResearchProvider` en `trading_ai/ai.py` define el contrato común: descripción del
proveedor y respuesta con consumo. `OllamaProvider` lo implementa. Un adaptador
para **OpenAI API (los modelos usados también por ChatGPT)** podrá cumplir el mismo
contrato sin introducir dependencias del proveedor en los cálculos del simulador.

La opción `--provider openai` está **reservada y desactivada**: devuelve un error
antes de consultar credenciales o realizar peticiones. No hay todavía adaptador
facturable. Incorporarlo requerirá acordar modelo, credenciales, presupuestos,
estimación/reserva del coste y pruebas del adaptador. No existe cambio automático
de Ollama a una API de pago ante un error.

## Registros y errores

Cada investigación crea `.local/research/<identificador>/`:

- `events.jsonl`: propuestas, solicitudes, parámetros, respuestas, herramientas,
  resultados, errores, tiempos UTC y consumo medido. Guarda el hash del código y
  la identidad/digest del modelo. Cada evento se escribe y sincroniza a disco.
- `results.json`: resultados del motor y SHA-256/fechas de los datos, conservados
  aunque falle después la interpretación de IA. Los `Decimal` se guardan como texto.
- `analysis.json` y `report.md`: conclusión creada por el control de Python o
  análisis de IA que supera la comprobación.
- `analysis_origin.json`: autoría de la conclusión (`python` o `model`),
  verificación y, cuando procede, motivo `no_closed_trades` y estrategias sin cierres.

Los números del informe se insertan desde el motor. La IA devuelve comparaciones
y un veredicto, no redacta los importes mostrados. El registro indica coste de API
cero para Ollama local; no estima electricidad. Si no se conocen los tokens de una
petición fallida, se conserva su ausencia, sin inventar un consumo cero. Cada
ejecución utiliza otra carpeta y no sobrescribe investigaciones anteriores.
El registro incluye el control previo, los cierres de cada estrategia y la
omisión de análisis cuando corresponda. Los tokens y el número de peticiones
reflejan solo las consultas realizadas, sin inventar una segunda respuesta.

Para detener la instancia del proyecto y liberar recursos:

```powershell
.\scripts\Stop-LocalAI.ps1
```

El script verifica el PID y la ruta del ejecutable antes de detenerlo.

## Referencias oficiales

- [Ollama en Windows y distribución portátil](https://docs.ollama.com/windows).
- [Ollama v0.40.6](https://github.com/ollama/ollama/releases/tag/v0.40.6).
- [Modelo Qwen3.5:4b](https://ollama.com/library/qwen3.5:4b).
- [API de conversación](https://docs.ollama.com/api/chat).
- [Respuestas estructuradas](https://docs.ollama.com/capabilities/structured-outputs).
- [Modo exclusivamente local](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features).

La FASE 3 se cierra el 19 de octubre de 2026 con autorización del usuario.
El [estado del proyecto](PROJECT_STATUS.md) recoge el alcance y sus límites.

Comprobación del 19 de octubre de 2026: 396 pruebas sin red y una investigación
real en CPU de 46 segundos, con 1102 tokens de entrada y 170 de salida en total.
La propuesta EMA15/45 para EUR/USD no cumplió el criterio frente a SMA20/60:
rentabilidad acumulada de 0,068919 % frente a 1,500933 %, y drawdown máximo de
4,500939 % frente a 2,508037 %. El agente lo reconoció y la aplicación verificó
su conclusión. Estos datos pertenecen únicamente a esa ejecución y sus supuestos.

La [evaluación aislada de consistencia](../reports/local-agent-consistency-2026-10-19.md)
posterior obtuvo 4/6 respuestas correctas: fallaron las dos preguntas sobre
historia insuficiente. Esa evidencia se conserva. Tras añadir el control previo,
la suite completa contiene 399 pruebas aprobadas; tres regresiones de cero
cierres fallaban antes del cambio y pasan después.

La [verificación del control previo](../reports/local-agent-sufficiency-2026-10-19.md)
completó tres flujos: el insuficiente con una petición para la propuesta y
conclusión de Python; los dos casos normales con propuesta y análisis de IA
verificado. Esta comprobación del flujo no sustituye el resultado aislado 4/6
del modelo. Los informes conservan el estado histórico de cada comprobación;
el cierre posterior se registra en `PROJECT_STATUS.md`.
