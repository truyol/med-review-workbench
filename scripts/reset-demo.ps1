# reset-demo.ps1
# 重置演示环境：删除演示持久卷（含历史脏数据），重建并写入干净的演示种子。
# 只影响演示栈（compose 项目 med-review-workbench / 卷 medreview_data）。
# 不影响 P8 完整门禁使用的隔离栈（项目 medreview-p8-gate）。

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectRoot 'deploy\docker-compose.yml'
$apiPython = Join-Path $projectRoot 'apps\api\.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $apiPython)) {
    throw "API virtualenv not found. Run scripts\bootstrap.ps1 first."
}

Write-Host 'Stopping demo stack and removing demo volume (medreview_data)...'
docker compose -f $composeFile down -v
if ($LASTEXITCODE -ne 0) { throw 'Failed to tear down the demo stack.' }

Write-Host 'Starting a clean demo stack (rebuilding images)...'
docker compose -f $composeFile up -d --build --wait
if ($LASTEXITCODE -ne 0) { throw 'Failed to start the demo stack.' }

Write-Host 'Seeding a clean demo project...'
docker compose -f $composeFile exec -T api python -m app.ops.seed_demo --sample-root /sample-data
if ($LASTEXITCODE -ne 0) { throw 'Failed to seed the demo project.' }

Write-Host ''
Write-Host 'Demo reset complete. Open http://localhost:8080' -ForegroundColor Green
