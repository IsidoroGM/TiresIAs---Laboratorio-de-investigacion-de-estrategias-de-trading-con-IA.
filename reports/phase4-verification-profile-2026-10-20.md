# Perfil de una verificación de lectura — 20/10/2026

Se perfiló la verificación de la petición guiada
`1a1d0783778243ac989ca1ab3fc49911`. El registro identificó 196 llamadas a
`robustness._development` y a `load_ecb_rates` para el mismo desarrollo.

- Tiempo de pared observado: 85,696711 segundos.
- Llamadas totales registradas por el perfilador: 88.451.788.
- Registro: `.local/verification-profiles/3ee2ee3604144fc3aaeaa2db68ceb16d`.
- Consumo nuevo: cero consultas de modelo, coste de API y backtests.

Había una ejecución de pytest concurrente. El perfilador añade además su propio
coste. Este registro localiza trabajo repetido; no es una medición controlada
de velocidad ni una comparación con la caché posterior.

Se conservaron 252 copias previas y sus referencias originales. El
[inventario nuevo](phase4-verification-profile-2026-10-20/snapshot.json) contiene
cinco copias: perfil JSON, huella, eventos, script y datos de cProfile.
La verificación de integridad no necesita abrir los datos binarios del perfilador.

La [lectura opcional con caché](../docs/VALIDATED_READ_CACHE.md) aborda esta
repetición sin modificar los módulos históricos en disco ni activarse en sus
productores. Su [registro separado](phase4-cached-read-2026-10-20.md) conserva
el resultado y sus límites de interpretación.
