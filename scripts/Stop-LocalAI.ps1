$ErrorActionPreference = 'Stop'
$tradingAiRoot = Split-Path -Parent $PSScriptRoot
$tradingAiExe = Join-Path $tradingAiRoot '.local/ollama/ollama.exe'
$tradingAiPidFile = Join-Path $tradingAiRoot '.local/ollama.pid'
if (-not (Test-Path -LiteralPath $tradingAiPidFile)) { Write-Output 'No hay una instancia registrada.'; return }
$tradingAiProcessId = [int](Get-Content -LiteralPath $tradingAiPidFile)
$tradingAiProcess = Get-Process -Id $tradingAiProcessId -ErrorAction SilentlyContinue
if (-not $tradingAiProcess) { Write-Output 'La instancia registrada ya terminó.'; return }
if ($tradingAiProcess.Path -ne $tradingAiExe) { throw 'El PID corresponde a otro programa. No se detendrá.' }
$env:OLLAMA_HOST = '127.0.0.1:11435'
& $tradingAiExe stop 'qwen3.5:4b' *> (Join-Path $tradingAiRoot '.local/logs/stop-model.log')
if ($LASTEXITCODE -ne 0) { throw 'No se pudo descargar el modelo de memoria. La instancia sigue activa.' }
Stop-Process -Id $tradingAiProcessId
Write-Output 'Ollama del proyecto detenido.'
