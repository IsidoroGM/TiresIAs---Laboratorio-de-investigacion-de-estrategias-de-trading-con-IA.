param([switch]$PullModel)
$ErrorActionPreference = 'Stop'
$tradingAiRoot = Split-Path -Parent $PSScriptRoot
$tradingAiLocal = Join-Path $tradingAiRoot '.local'
$tradingAiExe = Join-Path $tradingAiLocal 'ollama/ollama.exe'
if (-not (Test-Path -LiteralPath $tradingAiExe)) { throw 'Ejecuta primero scripts/Install-LocalAI.ps1.' }
$tradingAiLogs = Join-Path $tradingAiLocal 'logs'
New-Item -ItemType Directory -Path $tradingAiLogs -Force | Out-Null
$env:OLLAMA_HOST = '127.0.0.1:11435'
$env:OLLAMA_MODELS = Join-Path $tradingAiLocal 'models'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_CONTEXT_LENGTH = '4096'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$tradingAiServer = $null
try { $tradingAiServer = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/version' -TimeoutSec 2 } catch { }
if (-not $tradingAiServer) {
    $tradingAiStamp = [guid]::NewGuid().ToString('N')
    $tradingAiProcess = Start-Process -FilePath $tradingAiExe -ArgumentList 'serve' -WorkingDirectory $tradingAiRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $tradingAiLogs ($tradingAiStamp + '.stdout.log')) -RedirectStandardError (Join-Path $tradingAiLogs ($tradingAiStamp + '.stderr.log'))
    $tradingAiProcess.Id | Set-Content -LiteralPath (Join-Path $tradingAiLocal 'ollama.pid')
    for ($tradingAiAttempt = 0; $tradingAiAttempt -lt 30; $tradingAiAttempt++) {
        Start-Sleep -Milliseconds 500
        try { $tradingAiServer = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/version' -TimeoutSec 1; break } catch { }
        if ($tradingAiProcess.HasExited) { throw 'Ollama terminó al arrancar. Consulta .local/logs.' }
    }
    if (-not $tradingAiServer) { throw 'Ollama no respondió en el puerto local 11435.' }
} else {
    $tradingAiPidFile = Join-Path $tradingAiLocal 'ollama.pid'
    if (-not (Test-Path -LiteralPath $tradingAiPidFile)) { throw 'Puerto 11435 ocupado por una instancia no identificada del proyecto.' }
    $tradingAiExistingId = [int](Get-Content -LiteralPath $tradingAiPidFile)
    $tradingAiExisting = Get-Process -Id $tradingAiExistingId -ErrorAction Stop
    if ($tradingAiExisting.Path -ne $tradingAiExe) { throw 'El proceso registrado no coincide con Ollama del proyecto.' }
}
Write-Output ('Ollama local listo. Versión: ' + $tradingAiServer.version)
if ($PullModel) {
    Write-Output 'Descargando/verificando qwen3.5:4b. El progreso queda en .local/logs/pull-model.log.'
    & $tradingAiExe pull 'qwen3.5:4b' *> (Join-Path $tradingAiLogs 'pull-model.log')
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo descargar qwen3.5:4b.' }
    Write-Output 'Modelo local preparado y verificado por Ollama.'
}
