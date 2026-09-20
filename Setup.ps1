param([string]$SourcePdf = 'D:\Creative_5\MSS Reference Architecture Version 2.0_FINAL_090226.pdf')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$appPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $appPython)) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $bundledPython) {
        & $bundledPython -m venv .venv
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        throw 'Install Python 3.12 or later, then run Setup.cmd again.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& $appPython -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12 or later is required"'
if ($LASTEXITCODE -ne 0) { throw 'Python version check failed.' }
& $appPython -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency download failed. Check your internet connection and try again.' }
New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot 'data') | Out-Null
$destinationPdf = Join-Path $PSScriptRoot 'data\mss-reference-v2.pdf'
if (-not (Test-Path -LiteralPath $destinationPdf)) {
    if (-not (Test-Path -LiteralPath $SourcePdf)) { throw 'Source PDF not found. Run Setup.ps1 -SourcePdf with the path to your reference PDF.' }
    Copy-Item -LiteralPath $SourcePdf -Destination $destinationPdf
}
& $appPython -m satellite.ingest
if ($LASTEXITCODE -ne 0) { throw 'Document indexing failed.' }
Write-Host 'Setup complete. Open Start.cmd to launch the website.'
Write-Host 'Optional: configure .env, then run Enable-AI.cmd for semantic search and AI explanations.'
