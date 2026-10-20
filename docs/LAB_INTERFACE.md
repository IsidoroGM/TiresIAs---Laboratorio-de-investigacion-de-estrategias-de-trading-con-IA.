# Consultar el laboratorio TiresIAs

## Arranque y cierre en Windows

Desde la raíz del proyecto, ejecuta:

```powershell
.\.venv\Scripts\python.exe -m trading_ai.lab
```

Abre [TiresIAs local](http://127.0.0.1:8765). El servidor permanece en esa terminal;
**Ctrl+C** lo cierra y libera el puerto. Cerrar la pestaña no detiene el servidor.
Para otro puerto, añade `--port 8766` y usa la dirección que imprime el comando.
No hay servicios permanentes, conexiones externas o arranque automático de Ollama.

## Recorrido

1. **Inicio**: recuentos de registros y copias, últimos registros, informes Markdown
   originales y avisos de fuentes. Los recuentos son de catálogo, no de estrategias
   únicas, procesos activos o investigaciones nuevas.
2. **Experimentos**: filtros combinables por par, estrategia, fecha registrada,
   estado, procedencia y texto. La fecha del filtro coincide con el día mostrado
   según la zona horaria del navegador; los archivos conservan sus instantes originales.
   La ficha presenta hipótesis, criterio, reglas, controles, parámetros, fuentes
   y resultados. Un dato ausente permanece como no disponible.
3. **Resultados**: abre una ficha y selecciona una cuenta. Hay cuentas separadas por
   estrategia, entrenamiento/comprobación, ventana y moneda. La curva y el drawdown
   representan los puntos guardados; la tabla separa fechas de señal y ejecución,
   cantidades, precios, costes y resultado neto. La posición abierta no se cierra
   para completar la pantalla. Los formatos de resumen no tienen un gráfico inventado.
4. **Memoria del agente**: fichas de propuestas, revisiones, duplicados, descartes,
   errores, intentos incompletos y resultados. Los desplegables distinguen respuestas
   originales del modelo, descripciones mecánicas de Python, conclusiones contrastadas
   y eventos. El registro completo y las capturas se pueden abrir como texto.
5. **Consumo**: consultas, tokens y coste de API guardados por fuente, con heredado
   aparte. No se ofrece un total global: varias memorias pueden describir la misma
   consulta. Las copias del mismo origen no vuelven a aparecer en este apartado.
   Un campo desconocido permanece desconocido aunque existan subtotales conocidos.

El comparador de cada ficha exige par, moneda, huella y fechas de datos, capital,
costes y tamaño conocidos e iguales. Fuera de una misma comparación guardada,
también exige identidad de ejecución conocida e igual. Explica las diferencias
que bloquean la comparación y muestra los parámetros distintos. Nunca suma capitales
ni compone rentabilidades de ventanas o cuentas independientes.

Los identificadores originales de criterio se conservan en la ficha:
`higher_return_without_more_drawdown` exige rentabilidad estrictamente mayor sin
mayor drawdown; `lower_drawdown_without_lower_return` exige drawdown estrictamente
menor sin reducir rentabilidad. `met`, `not_met` e `inconclusive` significan criterio
cumplido, no cumplido e inconcluso dentro del histórico descrito, respectivamente.
Una propuesta pendiente o técnicamente válida no acredita un resultado calculado.

## Procedencia y verificación

| Indicación | Alcance |
| --- | --- |
| Registro local | Archivo presente en un directorio admitido; su estado describe lo que quedó guardado |
| Copia histórica | Archivo localizado por un inventario de `reports`; puede consultarse sin el original local |
| Integridad de copias comprobada | Todos los archivos de ese inventario conservan sus huellas; no certifica significado, autoría externa o rentabilidad |
| Registro cotejado con una huella archivada | Coinciden los bytes del archivo principal local; no comprueba vigencia de toda su cadena de permisos |
| Registro sin verificación completa | No existe una huella archivada contrastable; no se presenta como certificado |
| Registro incompleto | Falta el archivo principal; se conservan los eventos disponibles sin inventar resultados o ejecución activa |
| Archivo diferente, ausente o no verificable | El problema queda visible; no se reemplaza silenciosamente el original por una copia |
| Registro contable vigente | Consulta separada mediante el lector SQLite existente, abierto en modo de solo lectura; no concede permisos de ejecución |

La contabilidad detallada se contrasta con la huella registrada, su resumen, fechas
y controles antes de dibujarla. No se vuelven a ejecutar señales, indicadores,
simulaciones o métricas para verificarla. Todas las fichas conservan acceso a los
originales, inventarios e informes asociados, servidos como texto seguro.

Los protocolos de desarrollo ya usaron estos datos históricos. La interfaz conserva
los resultados negativos y el duplicado del último ciclo. No demuestra validación
inédita, suficiencia estadística, cotizaciones actuales o rentabilidad futura.

## Fuentes admitidas y límites

El catálogo lee únicamente los directorios expresamente admitidos en
`lab_catalog.py`: investigaciones, registros previos, evaluaciones, robustez,
ideas, revisiones, sesiones, intentos y memorias compactas, campañas y walk-forward.
Incluye las comprobaciones históricas identificadas del investigador. El único
descenso adicional de robustez es `plan/attempts/intento`. No recorre modelos,
descargas, binarios, configuración personal ni credenciales.

Los inventarios versión 1 con mapa de archivos utilizan el verificador existente
`evidence.verify_evidence`. Los cinco inventarios históricos con lista `snapshot,
source, sha256` se comprueban por sus huellas sin convertir o modificar sus bytes.
Fuentes no admitidas o ausentes producen avisos. Las referencias declaradas no
permiten leer rutas arbitrarias fuera del catálogo.

Límites: 32 MiB por archivo, 256 MiB de lectura acumulada de la capa de consulta,
4.096 entradas/archivos, 25.000 puntos y 10.000 operaciones por cuenta detallada.
El verificador de evidencias mantiene además sus límites propios. Una consulta
vuelve a leer sus fuentes; no hay caché persistente que oculte cambios.

El HTTP solo admite GET/HEAD, enlaces mediante identificadores de catálogo y
origen/Host locales. El contenido del modelo se coloca como texto en el documento;
no se ejecuta como JavaScript, HTML o código Python. No se incorporan rutas de envío,
ejecución, adopción, reserva o modificación de presupuestos.

## Comprobación de solo lectura

La auditoría explícita puede ejecutarse desde la raíz con:

```powershell
.\.venv\Scripts\python.exe scripts/check_lab_readonly.py
```

Revisa los registros y cuentas existentes con red, proveedores, simulador,
creación de diarios y reservas bloqueados. Contrasta las huellas antes y después.
No realiza inferencias o backtests. Las pruebas automatizadas usan fuentes
artificiales y temporales exclusivos según `AGENTS.md`.

TradingView, brókeres, recepción de eventos y dinero real quedan fuera de FASE 5.
