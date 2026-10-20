# FASE 5 — Interfaz local de consulta

20/10/2026. Punto de partida: `main`, `f5e654435f42efcb76c53a82f812a541bf78d521`,
directorio limpio; HEAD y la referencia local `origin/main` coinciden.

## Pantallas y contratos

| Pantalla | Fuentes admitidas | Presentación |
| --- | --- | --- |
| Inicio | Catálogo de registros y Markdown de reports | Recuentos del catálogo, avisos, informes originales y límites educativos |
| Experimentos | JSON y eventos JSONL de investigaciones, propuestas, revisiones, sesiones, ejecuciones, ciclos y walk-forward | Filtros de par, estrategia, fecha registrada, estado y procedencia; ficha con controles, hipótesis, reglas, criterio, comparación y fuentes |
| Resultados | Resúmenes guardados y contabilidad `summary/backtest` del motor | Cuenta independiente por estrategia, tramo y moneda; curva y drawdown completos solo si están guardados; operaciones y posición abierta |
| Memoria del agente | Propuestas, revisiones, eventos y capturas originales de esos registros; memorias archivadas | Texto original del modelo separado de descripciones y conclusiones de Python; duplicados, descartes, errores y pendientes |
| Consumo | Consumo guardado de cada registro/ciclo y eventos de respuesta | Nuevo y heredado separados; desconocido como no disponible; sin total global que duplique memorias o copias |

Arquitectura: navegador → servidor HTTP de biblioteca estándar → catálogo/capa
de consulta → lectores y verificador de integridad existentes. Módulos nuevos;
sin modificar fuentes del motor vinculadas a evidencias previas. Sin dependencias.

## Ubicaciones y límites de lectura

Solo los subdirectorios expresamente admitidos de `.local` y `reports`.
No se recorren modelos, binarios, descargas, configuración personal o credenciales.
Catálogo con profundidad acotada; enlaces mediante identificadores opacos,
nunca una ruta arbitraria de la petición HTTP. Se rechazan escapes, enlaces
simbólicos y junctions; tamaños y número de archivos acotados. Una referencia
guardada fuera de esas ubicaciones se muestra como texto sin seguirla.

Los inventarios `reports/*/snapshot.json` de versión 1 permiten localizar copias
archivadas. Se reutiliza `evidence.verify_evidence` para comprobar sus bytes,
con prevalidación de rutas. Su alcance es **integridad de copias**, no certificación
semántica, autoría externa ni validación independiente. Las copias se identifican
como históricas aunque existan originales locales. Los JSON sin inventario o
sin una huella contrastable permanecen como registros sin verificación completa.
Los originales locales se cotejan con las copias disponibles, sin usar las copias
para reemplazar silenciosamente un original ausente o alterado.

La implementación admite además los cinco inventarios históricos con lista de
copias `snapshot/source/sha256`. Se comprueban por huellas sin transformar los
originales ni presentarlos como el contrato versión 1. La robustez interna admite
su ubicación fija `plan/attempts/intento` y conserva los controles de cada escenario.

Se distinguen estado registrado, integridad, procedencia, instante de consulta,
fecha registrada y fechas históricas de mercado. El último evento no demuestra
que siga habiendo un proceso activo. Archivos ausentes, inválidos, incompletos,
alterados y formatos no admitidos producen avisos y no resultados certificados.

## Resultados y comparabilidad

No se calculan señales, indicadores, simulaciones o métricas nuevas del motor.
Los resúmenes antiguos sin curva u operaciones detalladas lo indican. Los gráficos
usan exclusivamente puntos guardados, con fechas y moneda. No se agregan cuentas,
ni se encadenan ventanas. La comparación exige par, moneda, huella y periodo de
datos, capital, costes y tamaño conocidos e iguales; muestra las diferencias de
estrategia y parámetros. Datos conocidos no se convierten en validación inédita.

## Servidor y comprobación

Arranque explícito: `python -m trading_ai.lab`, solo `127.0.0.1`, parada Ctrl+C.
Sin servicios permanentes, apertura automática de navegador o rutas de ejecución.
Solo GET/HEAD; validación de Host/Origin y política de contenido local. Todo texto
del modelo se presenta como texto, sin HTML, evaluación o ejecución de código.

Incrementos: catálogo y ficha; navegación/filtros; cuentas/gráficos/comparación;
memoria/consumo; integración, revisión visual en navegador Windows y suite completa
con fuentes estables. Pruebas con temporales nuevos y caché desactivada según
AGENTS.md. Se registran fallos y comprobaciones en DEVELOPMENT_LOG. PROJECT_STATUS
se actualiza únicamente tras completar la fase. Sin inferencias reales, nuevas
simulaciones históricas, reservas, commits, pushes o trabajo de FASE 6.
