param([switch]$DownloadOnly)
$ErrorActionPreference = 'Stop'
$tradingAiRoot = Split-Path -Parent $PSScriptRoot
$tradingAiLocal = Join-Path $tradingAiRoot '.local'
$tradingAiRuntime = Join-Path $tradingAiLocal 'ollama'
$tradingAiDownload = Join-Path $tradingAiLocal 'downloads'
$tradingAiArchive = Join-Path $tradingAiDownload 'ollama-windows-amd64-v0.40.6.zip'
$tradingAiDigest = 'e359637575302f288d76c0007c408a4be9c7376d59c4f28684d63b232a44b427'
New-Item -ItemType Directory -Path $tradingAiDownload -Force | Out-Null
if (-not (Test-Path -LiteralPath $tradingAiArchive)) {
    Write-Output 'Descargando Ollama v0.40.6 (archivo oficial de 1,47 GB)...'
    $tradingAiProgress = $ProgressPreference
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri 'https://github.com/ollama/ollama/releases/download/v0.40.6/ollama-windows-amd64.zip' -OutFile ($tradingAiArchive + '.partial')
        $tradingAiActualDigest = (Get-FileHash -LiteralPath ($tradingAiArchive + '.partial') -Algorithm SHA256).Hash
        if ($tradingAiActualDigest -ne $tradingAiDigest) { throw 'El SHA-256 de Ollama no coincide con el publicado por GitHub.' }
        Move-Item -LiteralPath ($tradingAiArchive + '.partial') -Destination $tradingAiArchive
    } finally { $ProgressPreference = $tradingAiProgress }
}
if ((Get-FileHash -LiteralPath $tradingAiArchive -Algorithm SHA256).Hash -ne $tradingAiDigest) {
    throw 'Archivo local de Ollama con SHA-256 distinto al esperado.'
}
if ($DownloadOnly) { Write-Output 'Descarga y SHA-256 comprobados.'; return }
if (-not (Test-Path -LiteralPath (Join-Path $tradingAiRuntime 'ollama.exe'))) {
    Write-Output 'Extrayendo Ollama portátil...'
    Expand-Archive -LiteralPath $tradingAiArchive -DestinationPath $tradingAiRuntime
}
Write-Output 'Ollama preparado en .local/ollama. Sin cambios en PATH ni inicio de Windows.'
