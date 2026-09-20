$ErrorActionPreference = 'Stop'

function Show-CommandVersion {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    try {
        $value = & $Command 2>&1 | Select-Object -First 1
        Write-Host "[OK] ${Name}: $value"
    }
    catch {
        Write-Host "[MISSING] ${Name}: $($_.Exception.Message)"
    }
}

Show-CommandVersion 'Node' { node --version }
Show-CommandVersion 'npm' { npm.cmd --version }
Show-CommandVersion 'Python' { python --version }
Show-CommandVersion 'pip' { python -m pip --version }
Show-CommandVersion 'Git' { git --version }
Show-CommandVersion 'Docker' { docker --version }

$codeCli = 'D:\app\Microsoft VS Code\bin\code.cmd'
if (Test-Path -LiteralPath $codeCli) {
    $version = & $codeCli --version | Select-Object -First 1
    Write-Host "[OK] VS Code: $version ($codeCli)"
}
else {
    Write-Host "[MISSING] VS Code CLI at $codeCli"
}

Write-Host ''
Write-Host 'Docker/WSL2 are deployment-stage dependencies and may be intentionally absent.'
