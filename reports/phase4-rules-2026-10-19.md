# FASE 4 — Condiciones declarativas calculables

Fecha: 19 de octubre de 2026. Desarrollo de herramientas; fase abierta.
**587 pruebas aprobadas**, incluidas 67 nuevas sobre el formato de reglas.

Se añadió `trading_ai.rules`: un validador y generador de señales para reglas
JSON con significado preciso. Las ideas seguirán correspondiendo al agente;
este paso construye el vocabulario que podrá utilizar, sin elegir una estrategia
nueva ni interpretar por él una descripción ambigua.

## Capacidades y separación

- Referencias, SMA, EMA y mínimos/máximos de ventanas, con retraso explícito.
- Comparaciones numéricas y cruces; grupos planos de «todas» o «alguna».
- Hasta cuatro condiciones por grupo, ventanas de 1–252 y retrasos de 0–252.
- Constantes decimales finitas y acotadas, sin expresiones libres.
- Calentamiento obligatorio de entrada y salida; prioridad fija de salida
  cuando coinciden señales, sin abrir cortos.

El compilador rechaza campos de capital, costes, tamaño, fuentes y código libre.
Genera una señal por observación, sin mantener posiciones ni modificar entradas.
El motor existente conserva la ejecución en la siguiente referencia y toda la
contabilidad. Las reglas son inmutables y su JSON canónico tiene un SHA-256.

La CLI `python -m trading_ai.rules --spec config/rules.example.json` valida el
archivo sin consultar precios, modelos ni backtests. El ejemplo representa la
base SMA20/60 ya existente; no constituye una propuesta de mejora.

## Comprobación real de compatibilidad

Se usaron exclusivamente 5375 observaciones de desarrollo EUR/USD, entre
1999-01-04 y 2019-12-31, SHA-256
`9b703b20333ef2d962d372fdfb9bf6c700f44ad2dace3d63e4d7ecf4edae58a5`.

| Implementación existente | Formato declarativo | Señales | Backtest completo | Cierres |
|---|---|---|---|---:|
| SMA20/SMA60 | Ejemplo SMA20/60 | Idénticas | Idéntico | 50 |
| EMA20/EMA60 | Equivalente técnico EMA20/60 | Idénticas | Idéntico | 47 |

La comparación abarca el resultado completo del motor: operaciones, posiciones,
costes, capital, curva diaria, drawdown derivado y rechazos. Las posiciones
abiertas finales permanecen abiertas en ambas implementaciones. Se comprobó
que las fechas de ejecución de los cierres son posteriores a sus señales.

Supuestos de compatibilidad: capital inicial 1000 USD, coste del 0,1 % por
ejecución y tamaño del 10 % del efectivo, costes incluidos. Los indicadores y
el motor originales no se modificaron. La comparación verifica el compilador;
no selecciona estrategias ni reevalúa una hipótesis sobre datos exteriores.

La ejecución técnica bloqueó aperturas de `evaluation.xml`, comparaciones,
resultados y registro de acceso de evaluación exterior, con comprobaciones
sobre `builtins.open` e `io.open`. Terminó correctamente. Esta comprobación
cubre el código ejecutado, no sustituye un aislamiento de permisos del sistema.

## Pruebas y evidencia

Las 67 pruebas nuevas incluyen resultados numéricos conocidos, igualdad en los
cruces, calentamiento, retrasos, extremos de ventanas, combinaciones y prioridad.
Verifican que añadir o alterar datos futuros no cambie señales pasadas, y que
SMA/EMA y su contabilidad coincidan con las implementaciones originales.

También cubren especificaciones inmutables, hashes estables ante cambios en el
orden de claves, contexto Decimal exterior, rechazo de entradas inválidas,
controles añadidos, código, operaciones desconocidas, datos futuros, límites,
claves JSON repetidas y archivos sobredimensionados. La CLI se prueba sin IA ni
backtests. Suite completa: **587 passed**, caché desactivada y temporal nuevo
exclusivo según `AGENTS.md`.

Auditoría local: `.local/rules-checks/7b49145cd35f4e52b1ff8ea1e8a99ec0/`.
Copias exactas, con bytes conservados por `.gitattributes`:

- [Auditoría, hashes y rutas leídas](phase4-rules-2026-10-19/audit.json).
- [Eventos de comprobación](phase4-rules-2026-10-19/events.jsonl).
- [Especificación SMA](phase4-rules-2026-10-19/sma-spec.json).
- [Especificación EMA](phase4-rules-2026-10-19/ema-spec.json).
- [Correspondencia de copias y hashes](phase4-rules-2026-10-19/snapshot.json).

No hubo consultas de IA, descargas ni dependencias nuevas. Coste de API: **0 USD**.
No se abrieron datos ni resultados de evaluación exterior.

## Alcance pendiente

El formato define reglas computables, no garantiza utilidad, novedad, robustez
o rentabilidad. OHLC, volumen, RSI y condiciones no implementadas siguen fuera
del vocabulario inicial. No se sustituye una condición ausente por otra.

La bandeja de ideas conserva `executable: false`. Su borrador anterior, que
mezclaba alternativas de salida, no se tradujo ni se modificó. Falta vincular
una especificación formal a la idea, contrastar su significado y habilitar una
herramienta de experimento controlada. El contrato histórico SMA/EMA y los
registros anteriores se conservan.

Todo el histórico ya se había explorado: esta comprobación técnica no crea
datos inéditos ni una evaluación prospectiva. No hay dinero real, nuevas
conexiones de TradingView ni APIs de pago. FASE 4 continúa abierta;
`PROJECT_STATUS.md` conserva el cierre de FASE 3. Sin commits ni pushes.

El [formato de reglas](../docs/RULE_SPEC.md) documenta los campos, la semántica
y la API. El [plan del investigador](../docs/AGENT_RESEARCH_PLAN.md) recoge la
integración pendiente.
