# FASE 4 — Descripción mecánica de reglas verificadas

Fecha: 19 de octubre de 2026. Desarrollo acotado, sin cierre de fase.

`structured_brief` describe entrada y salida desde campos declarados y
verificados: serie, ventana, retardo y operador exacto. Se identifica como texto
derivado de Python. Conserva título e hipótesis del modelo como texto literal;
no completa frases por inferencia ni demuestra que coincidan con las reglas.

La comprobación sobre la hija `a1bacf3e52c743c2b4088cad0c82ee45` produjo:

- Entrar largo cuando la EMA actual de 20 observaciones cruza por encima de la
  SMA actual de 60 observaciones.
- Salir de la posición larga cuando la EMA actual de 20 observaciones cruza por
  debajo de la SMA actual de 60 observaciones.

El motor ejecuta las señales en la observación siguiente, si existe. Describir
estas condiciones no demuestra que ocurran señales, operaciones o mejoras.
La hipótesis original sigue teniendo 159 caracteres y acaba en «por debajo de
la». Su sesión conserva `needs_clarification`, sin reserva de simulaciones.

## Comprobaciones y consumo

18 pruebas nuevas: operadores estrictos e inclusivos, cruces, cuatro indicadores,
ventanas y retardos, singular, conservación de texto, aislamiento y rechazo de
artefactos alterados. Suite completa: **904 aprobadas en 78,61 s**, con caché
desactivada y un temporal exclusivo. Las 886 anteriores siguen aprobadas.

Esta tarea consumió cero consultas al modelo, cero tokens de proveedores del
proyecto, cero simulaciones y 0 USD de API. No se reutilizó el intento de
reformulación consumido ni se inició una cadena. El consumo heredado de la hija
sigue siendo 1289/239 tokens; su origen anterior añade 1257/248, registrados
previamente y sin consumir de nuevo. El trabajo de Codex usa la cuota de la
aplicación; estos ceros no representan todo su consumo computacional.

La demostración bloqueó red, creación de proveedores, señales, backtests y
lecturas de `evaluation.xml` o `comparison.json`. Conservó 24 archivos locales
de origen/sesión/reformulación. Se verificaron 150 copias históricas y sus
originales, sin cambios. No se han cambiado módulos ya sellados.

Una primera invocación del script de comprobación usó incorrectamente
`python -m runpy <archivo>` y salió antes de ejecutarlo. Se corrigió usando
`runpy.run_path`; no hubo consultas, simulaciones ni intentos consumidos.

## Evidencia

Registro: `.local/structured-briefs/b496a0e422944772964c2a948124156c`.
Se guardan once copias con SHA-256 y referencias originales:

- [Informe derivado y texto original](phase4-structured-brief-2026-10-19/report.md).
- [Registro verificable](phase4-structured-brief-2026-10-19/brief.json).
- [Contexto y estado de la sesión](phase4-structured-brief-2026-10-19/check-context.json).
- [Auditoría de lecturas y bloqueos](phase4-structured-brief-2026-10-19/io-audit.json).
- [Inventario de archivos](phase4-structured-brief-2026-10-19/snapshot.json).

La legibilidad de las reglas queda resuelta para este contrato. La calidad y
coherencia de la prosa generada siguen pendientes; la ayuda no concede una
aprobación, no reabre la sesión y no cierra FASE 4. Sin commits, pushes,
dependencias, servicios, APIs de pago ni operaciones reales.
