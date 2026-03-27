# Install genlang globally from source
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CliDir = Join-Path $ScriptDir "scaffold-cli"

Write-Host "🔨 Building genlang..." -ForegroundColor Cyan
Set-Location $CliDir

# Build and install globally
cargo install --path . --force

Write-Host "✅ genlang installed globally!" -ForegroundColor Green
Write-Host "Run 'genlang --help' to get started." -ForegroundColor Yellow