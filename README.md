# Trading AI

Proyecto educativo de investigación y trading algorítmico asistido por agentes de
IA. Se construye paso a paso para aprender Python, arquitectura modular, pruebas
automatizadas y evaluación de estrategias.

## Objetivo y alcance inicial

El primer objetivo es obtener datos históricos, validarlos y desarrollar un
backtest educativo reproducible.

- Mercado: Forex, comenzando por EUR/USD.
- Temporalidad: D1 (diaria), con enfoque de swing trading.
- Estrategia didáctica prevista: cruce de medias móviles simples SMA20/SMA60.
- Evaluación: resultados, costes, riesgo y limitaciones de cada simulación.

La fuente de datos todavía está pendiente de selección. Los tipos de referencia
del BCE son una opción educativa: no son cotizaciones negociables ni equivalen
necesariamente al cierre diario del mercado.

## Estado actual

La fase activa es la **FASE 0: preparación y fundamentos**. Están comprobados
Python 3.14.8 de 64 bits, el entorno virtual `.venv`, su uso desde la terminal de
VS Code y el repositorio Git local.

El paquete `trading_ai` dispone de un punto de entrada ejecutable que muestra la
presentación del laboratorio. Su arranque y su importación están comprobados.

Todavía no hay código de estrategias, descarga de datos, backtesting, API,
dashboard, agentes ni conexión con un bróker. No hay simulaciones ni resultados
de rendimiento que presentar.

## Trabajar con el entorno preparado

Abre en VS Code la carpeta raíz del proyecto, que contiene este README y
`.gitignore`, y abre una terminal de PowerShell. Los siguientes comandos utilizan
el entorno `.venv` que ya está creado; ejecútalos uno por uno:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
python -c "import sys; print(sys.executable); print(sys.prefix != sys.base_prefix)"
python -m pip --version
```

Resultados esperados:

- Python muestra `3.14.8`.
- La ruta del ejecutable termina en `.venv\Scripts\python.exe` dentro del proyecto.
- La comparación de los prefijos muestra `True`: se está usando un entorno virtual.
- La ruta de `pip` pertenece a `.venv\Lib\site-packages`.

Para salir del entorno en esa terminal, ejecuta `deactivate`. También puedes
ejecutar el Python del proyecto sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe --version
```

`.venv` es local y está excluido de Git. En otra copia del repositorio será
necesario preparar su propio entorno; estas instrucciones describen el entorno
actual. `pip` 26.2.1 es el único paquete instalado en él. Pandas, NumPy y pytest
están previstos y se incorporarán en tareas posteriores aprobadas.

## Ejecutar el laboratorio

Desde la raíz del proyecto, con el entorno virtual activo:

```powershell
python -m trading_ai
```

La salida esperada es:

```text
Trading AI - laboratorio educativo
Estado: FASE 0 - entorno de desarrollo.
```

`-m` busca el paquete y ejecuta su archivo `__main__.py`. También puedes ejecutar
el laboratorio sin activar previamente el entorno:

```powershell
.\.venv\Scripts\python.exe -m trading_ai
```

Para comprobar que importar el paquete no inicia el programa:

```powershell
python -c "import trading_ai; import trading_ai.__main__"
```

Este último comando debe terminar sin imprimir mensajes. La llamada a `main()`
está protegida por `if __name__ == "__main__"`, que distingue la ejecución como
programa de la importación del módulo.

## Organización

```text
.gitignore
README.md
docs/
    PROJECT_STATUS.md
trading_ai/
    __init__.py
    __main__.py
```

El paquete está directamente en la raíz del repositorio. `__init__.py` contiene
su descripción y lo identifica como un paquete convencional. `__main__.py`
define la función de arranque `main()`, sin parámetros y con retorno `None`.

La arquitectura prevista es un monolito modular, con responsabilidades separadas
para datos, indicadores, señales, simulación e informes. Esos módulos todavía no
están implementados. La carpeta `tests/` y pytest se incorporarán con la primera
lógica que necesite pruebas automatizadas. Por ahora se han comprobado el arranque,
la importación sin salida y la carga del paquete local desde el entorno virtual.

## Evolución y controles

La aplicación deberá distinguir entre backtesting histórico, paper trading y una
posible ejecución real en una fase avanzada. Esta última requerirá una nueva
autorización explícita y estará deshabilitada por defecto cuando se implemente.

Los agentes accederán a herramientas controladas. Las órdenes deberán pasar por
validaciones y un motor de riesgo cuyos límites no podrá modificar el LLM.
La confianza expresada por un agente no sustituye la validación de una estrategia.

Se registrarán las fuentes, los costes y las hipótesis de los experimentos. No se
utilizará información futura para generar señales. Los resultados simulados no
garantizan rentabilidad futura. Las credenciales nunca deben incluirse en Git.

## Continuidad

Consulta [el estado del proyecto](docs/PROJECT_STATUS.md) para conocer las tareas
completadas, las decisiones, los asuntos pendientes y el próximo paso propuesto.
