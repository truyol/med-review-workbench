$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $projectRoot 'apps\api'
$webRoot = Join-Path $projectRoot 'apps\web'
$apiPython = Join-Path $apiRoot '.venv\Scripts\python.exe'
$composeFile = Join-Path $projectRoot 'deploy\docker-compose.yml'
$reportRoot = Join-Path $projectRoot 'var\test-reports'

# The full gate runs against an ISOLATED compose project, volume and port so that
# automated tests never write into the demo stack (project "med-review-workbench",
# volume medreview_data, port 8080). The gate stack is always torn down with -v.
$gateProject = 'medreview-p8-gate'
$gatePort = '18080'
$gateBaseUrl = "http://127.0.0.1:$gatePort"

function Assert-NativeCommandSucceeded {
    param([Parameter(Mandatory)][string]$Step)

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null

$previousWebPort = $env:WEB_PORT
$previousBaseUrl = $env:PLAYWRIGHT_BASE_URL
$previousLive = $env:PLAYWRIGHT_LIVE
$gateStackUp = $false

try {
    Write-Host 'Fast gate'
    & (Join-Path $PSScriptRoot 'check.ps1')
    Assert-NativeCommandSucceeded 'Fast gate'

    Write-Host "Isolated gate environment (project=$gateProject, port=$gatePort)"
    $env:WEB_PORT = $gatePort
    & docker compose -p $gateProject -f $composeFile up --build -d --wait
    Assert-NativeCommandSucceeded 'Gate Compose startup'
    $gateStackUp = $true

    & docker compose -p $gateProject -f $composeFile exec -T api python -m app.ops.seed_demo --sample-root /sample-data
    Assert-NativeCommandSucceeded 'Gate demo seed'

    Write-Host 'API coverage'
    Push-Location $apiRoot
    try {
        & $apiPython -m pytest --cov=app --cov-report=term --cov-report="json:$reportRoot\api-coverage.json" -q
        Assert-NativeCommandSucceeded 'API coverage'
    }
    finally {
        Pop-Location
    }

    Write-Host 'Web component coverage and real-backend Playwright'
    Push-Location $webRoot
    try {
        npm.cmd run test -- --coverage
        Assert-NativeCommandSucceeded 'Web coverage'
        $env:PLAYWRIGHT_BASE_URL = $gateBaseUrl
        $env:PLAYWRIGHT_LIVE = '1'
        npm.cmd run e2e -- --reporter=line
        Assert-NativeCommandSucceeded 'Playwright E2E'
    }
    finally {
        Pop-Location
    }

    Write-Host 'Runtime privacy log scan'
    & docker compose -p $gateProject -f $composeFile logs --no-color api |
        & $apiPython (Join-Path $projectRoot 'scripts\privacy-scan.py')
    Assert-NativeCommandSucceeded 'Privacy log scan'

    Write-Host 'Python dependency audit'
    Push-Location $apiRoot
    try {
        & $apiPython -m pip_audit --local --progress-spinner off --timeout 60
        Assert-NativeCommandSucceeded 'Python dependency audit'
    }
    finally {
        Pop-Location
    }

    Write-Host 'Node production dependency audit'
    Push-Location $webRoot
    try {
        npm.cmd audit --omit=dev --audit-level=high
        Assert-NativeCommandSucceeded 'Node dependency audit'
    }
    finally {
        Pop-Location
    }

    Write-Host 'Full P8 gate passed.'
}
finally {
    $env:WEB_PORT = $previousWebPort
    $env:PLAYWRIGHT_BASE_URL = $previousBaseUrl
    $env:PLAYWRIGHT_LIVE = $previousLive

    if ($gateStackUp) {
        Write-Host "Tearing down isolated gate stack (project=$gateProject, volumes removed)"
        & docker compose -p $gateProject -f $composeFile down -v | Out-Null
    }
}
