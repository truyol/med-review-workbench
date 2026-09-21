$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $projectRoot 'apps\api'
$webRoot = Join-Path $projectRoot 'apps\web'
$apiPython = Join-Path $apiRoot '.venv\Scripts\python.exe'

function Assert-NativeCommandSucceeded {
    param([Parameter(Mandatory)][string]$Step)

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

if (-not (Test-Path -LiteralPath $apiPython)) {
    throw "API virtualenv not found. Run scripts\bootstrap.ps1 first."
}

Write-Host 'Project scripts: ruff check'
& $apiPython -m ruff check (Join-Path $projectRoot 'scripts\prepare-dicom-samples.py') (Join-Path $projectRoot 'scripts\seed-demo.py') (Join-Path $projectRoot 'scripts\privacy-scan.py')
Assert-NativeCommandSucceeded 'Project scripts ruff check'

Write-Host 'Operations: Docker Compose config'
docker compose -f (Join-Path $projectRoot 'deploy\docker-compose.yml') config --quiet
Assert-NativeCommandSucceeded 'Docker Compose config'

Write-Host 'API: ruff check'
Push-Location $apiRoot
try {
    & $apiPython -m ruff check .
    Assert-NativeCommandSucceeded 'API ruff check'
    Write-Host 'API: mypy'
    & $apiPython -m mypy app tests
    Assert-NativeCommandSucceeded 'API mypy'
    Write-Host 'API: pytest'
    & $apiPython -m pytest -q
    Assert-NativeCommandSucceeded 'API pytest'
    Write-Host 'API: isolated alembic upgrade/downgrade smoke'
    $migrationDatabase = Join-Path $env:TEMP "medreview-migration-$([guid]::NewGuid()).db"
    $previousDatabaseUrl = $env:APP_DATABASE_URL
    $migrationDatabaseUrl = $migrationDatabase.Replace('\', '/')
    $env:APP_DATABASE_URL = "sqlite:///$migrationDatabaseUrl"
    try {
        & $apiPython -m alembic upgrade head
        Assert-NativeCommandSucceeded 'API alembic upgrade'
        & $apiPython -m alembic downgrade base
        Assert-NativeCommandSucceeded 'API alembic downgrade'
    }
    finally {
        $env:APP_DATABASE_URL = $previousDatabaseUrl
        Remove-Item -LiteralPath $migrationDatabase -Force -ErrorAction SilentlyContinue
    }
}
finally {
    Pop-Location
}

Write-Host 'Web: lint'
Push-Location $webRoot
try {
    npm.cmd run lint
    Assert-NativeCommandSucceeded 'Web lint'
    Write-Host 'Web: test'
    npm.cmd run test
    Assert-NativeCommandSucceeded 'Web test'
    Write-Host 'Web: build'
    npm.cmd run build
    Assert-NativeCommandSucceeded 'Web build'
}
finally {
    Pop-Location
}

Write-Host 'All checks passed.'
