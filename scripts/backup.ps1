param(
    [ValidateSet('backup', 'restore', 'verify')]
    [string]$Mode = 'backup',
    [string]$Source,
    [string]$Target
)

$ErrorActionPreference = 'Stop'
$invocationRoot = (Get-Location).Path
$projectRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $projectRoot 'apps\api'
$apiPython = Join-Path $apiRoot '.venv\Scripts\python.exe'
$liveDatabase = Join-Path $apiRoot 'var\medreview.db'

if (-not (Test-Path -LiteralPath $apiPython)) {
    throw 'API virtualenv not found. Run scripts\bootstrap.ps1 first.'
}

if (-not $Source) {
    $Source = $liveDatabase
}

if ($Mode -eq 'backup' -and -not $Target) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $Target = Join-Path $projectRoot "var\backups\medreview-$stamp.db"
}
elseif ($Mode -eq 'restore' -and -not $Target) {
    $Target = $liveDatabase
}

if (-not [System.IO.Path]::IsPathRooted($Source)) {
    $Source = Join-Path $invocationRoot $Source
}
if ($Target -and -not [System.IO.Path]::IsPathRooted($Target)) {
    $Target = Join-Path $invocationRoot $Target
}

Push-Location $apiRoot
try {
    if ($Mode -eq 'verify') {
        & $apiPython -m app.ops.sqlite_backup verify $Source
    }
    else {
        & $apiPython -m app.ops.sqlite_backup $Mode $Source $Target
    }
    if ($LASTEXITCODE -ne 0) {
        throw "SQLite $Mode failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
