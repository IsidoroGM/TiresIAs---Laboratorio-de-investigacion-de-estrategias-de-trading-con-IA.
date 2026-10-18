# Comprobaciones desde Codex en Windows

El usuario ejecuta normalmente `python -m pytest -q` desde su entorno virtual.
La sesión aislada de Codex utiliza otra identidad de Windows. No ejecutar pytest
con sus rutas predeterminadas desde esa sesión: puede crear temporales y cachés
que el usuario habitual no pueda abrir (incidente comprobado el 18/10/2026).

Para pruebas desde la sesión aislada, desactivar su caché y usar una ruta temporal
nueva, exclusiva de esa ejecución:

```powershell
$codexPytestRun = Join-Path ([System.IO.Path]::GetTempPath()) ('trading-ai-codex-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp "$codexPytestRun"
```

`--basetemp` puede limpiar la ruta indicada: usar siempre ese nombre nuevo y
exclusivo. Nunca apuntarlo a una carpeta existente del usuario, la raíz del
proyecto ni la raíz temporal. No cambiar permisos generales de Windows.

Actualizar `docs/PROJECT_STATUS.md` solo al cerrar una fase, según lo acordado
con el usuario. No realizar commits ni pushes sin su autorización.
