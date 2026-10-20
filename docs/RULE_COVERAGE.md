# Cobertura estructural de reglas

La herramienta describe las reglas tipadas de las capturas indicadas. Cuenta
identidades de reglas sin nombre técnico y agrupa plantillas de forma mecánica.
No propone una estrategia o decide que una candidata sea distinta o mejor.

```powershell
.\.venv\Scripts\python.exe -m trading_ai.rule_coverage capture --context-run <contexto> --history-run <memoria-compacta>
.\.venv\Scripts\python.exe -m trading_ai.rule_coverage verify --run <cobertura>
```

Una plantilla conserva entrada/salida, tipos de operandos, operadores, grupos y
orden de condiciones. Omite el nombre, valores, ventanas y retardos. El registro
completo conserva esos parámetros por separado: cambiarlos puede alterar señales
y resultados. Compartir plantilla no demuestra equivalencia semántica.

La lista de tipos no observados se refiere solo a los campos de operandos
directos de las reglas capturadas. Por ejemplo, que no aparezca `reference` como
operando directo no implica que una EMA no utilice referencias. No se analiza
texto libre ni se cubre todo el historial de la aplicación o todas las ideas
posibles. Un tipo no observado no es una recomendación ni una oportunidad mejor.

La [comprobación local](../reports/phase4-rule-coverage-2026-10-20.md) encontró tres
registros, dos identidades sin nombre y una plantilla. El último registro era un
duplicado. Se conservaron las diferencias de retardo sin corregir o aprobarlas.
No hubo consultas, señales, simulaciones o cambios de presupuesto.

Los límites son 256 especificaciones y 120.000 bytes de JSON almacenado, incluida
su indentación. Si se exceden, se detiene sin recortar perfiles o fuentes.

La [petición guiada](GUIDED_REQUESTS.md) incorpora esta cobertura como contexto
de una petición futura, conservando historial y controles. Prepararla no concede
otro intento cuando el presupuesto ya está consumido.
