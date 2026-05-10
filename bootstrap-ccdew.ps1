# Bootstrap CCDEW pe Windows (PowerShell)
# Usage:  .\bootstrap-ccdew.ps1 [target-folder]
# Default target: CCDEW

$ErrorActionPreference = 'Stop'

Write-Host "=== CCDEW bootstrap ===" -ForegroundColor Cyan

# 1. Prereq check
$missing = @()
foreach ($cmd in @('node','npm','git','python','claude')) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { $missing += $cmd }
}
if ($missing.Count -gt 0) {
    Write-Host "MISSING: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Install: Node>=18, Python 3, Git, Claude Code CLI (https://docs.claude.com/claude-code)"
    exit 1
}

$nodeVer = (node -v) -replace '^v',''
if ([version]$nodeVer -lt [version]'18.0.0') {
    Write-Host "Node prea vechi: $nodeVer (necesita >=18)" -ForegroundColor Red
    exit 1
}
Write-Host "Prereqs OK (Node $nodeVer)" -ForegroundColor Green

# 2. Clone
$target = if ($args.Count -gt 0) { $args[0] } else { 'CCDEW' }
if (Test-Path $target) {
    Write-Host "Folder '$target' exista deja, sar peste clone." -ForegroundColor Yellow
} else {
    git clone https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace.git $target
}
Set-Location $target

# 3. Optional: codeburn global
$installCb = Read-Host "Instalez codeburn global pentru cost tracking? (y/N)"
if ($installCb -eq 'y') {
    npm install -g codeburn
}

# 4. Tests + audit
Write-Host "`n=== npm test ===" -ForegroundColor Cyan
npm test
if ($LASTEXITCODE -ne 0) { Write-Host "Tests FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`n=== npm run audit ===" -ForegroundColor Cyan
npm run audit
if ($LASTEXITCODE -ne 0) { Write-Host "Audit FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`n=== READY ===" -ForegroundColor Green
Write-Host "Folder: $(Get-Location)"
Write-Host "Pornire: claude"
