param(
    [switch]$IncludeCodex,
    [switch]$IncludePylance
)

$ErrorActionPreference = 'Stop'

$codeCli = 'D:\app\Microsoft VS Code\bin\code.cmd'
if (-not (Test-Path -LiteralPath $codeCli)) {
    throw "VS Code CLI not found at $codeCli"
}

$extensions = @(
    'dbaeumer.vscode-eslint',
    'esbenp.prettier-vscode',
    'ms-playwright.playwright',
    'ms-azuretools.vscode-docker',
    'qwtel.sqlite-viewer'
)

if ($IncludeCodex) {
    $extensions = @('openai.chatgpt') + $extensions
}

if ($IncludePylance) {
    $extensions = @('ms-python.vscode-pylance') + $extensions
}

foreach ($extension in $extensions) {
    Write-Host "Installing VS Code extension: $extension"
    & $codeCli --install-extension $extension --force
}

Write-Host 'VS Code extensions installed.'
