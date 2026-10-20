# Petición guiada preparada, sin envío — 20/10/2026

Se preparó una petición que conserva el historial compacto e incorpora la
cobertura estructural de las reglas. No se consultó el modelo ni se simuló.

- Registro: `.local/guided-compact-requests/1a1d0783778243ac989ca1ab3fc49911`.
- Estado: `prepared_not_submitted`; presupuesto compacto consumido.
- Tamaño: 12.142 bytes de un máximo de 12.288; tokens y encaje en contexto sin verificar.
- Historial: cero entradas omitidas y ningún texto recortado.
- Consumo nuevo: cero consultas, tokens, coste de API y backtests.

El consumo vinculado de la candidata anterior es una consulta local de 2.262
tokens de entrada y 176 de salida, con 0 USD de API. Es consumo heredado de esta
petición, no una consulta repetida. Esa candidata fue un duplicado y permanece
fuera del flujo de revisión aceptada y simulación.

La auditoría `277e89e01e34425481f218e4b42ff6c6` conservó 244 copias previas y sus
referencias originales, y añadió ocho copias. No hubo llamadas al proveedor,
señales, backtests o lectura de evaluación exterior. Sus registros y el script
están en el [inventario](phase4-guided-request-2026-10-20/snapshot.json).

La herramienta pasó nueve pruebas focalizadas; quedó incluida en la suite de
1.242 pruebas aprobadas. La prueba integrada posterior utilizó datos artificiales.
Estos controles verifican preparación e integridad, sin demostrar mejora de una
estrategia ni conceder permiso para nuevos intentos.

Uso y límites: [peticiones guiadas](../docs/GUIDED_REQUESTS.md).
