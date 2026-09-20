$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $projectRoot 'apps\api'
$webRoot = Join-Path $projectRoot 'apps\web'
$venvRoot = Join-Path $apiRoot '.venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host 'Creating Python virtual environment...'
    python -m venv $venvRoot
}

Write-Host 'Installing API dependencies...'
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e "$apiRoot[dev]"

Write-Host 'Installing web dependencies from package-lock/package.json...'
Push-Location $webRoot
try {
    npm.cmd install
}
finally {
    Pop-Location
}

Write-Host 'Bootstrap completed.'

