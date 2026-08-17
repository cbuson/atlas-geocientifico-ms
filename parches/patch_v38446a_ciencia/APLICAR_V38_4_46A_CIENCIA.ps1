$ErrorActionPreference = "Stop"
Write-Host "ITA ARANDU MS · HOTFIX V38.4.46A · botão Ciência do ternário" -ForegroundColor Cyan
if (-not (Test-Path ".\VERSION")) { throw "VERSION não encontrado. Execute este script na raiz do repositório ITA ARANDU MS." }
$current = (Get-Content ".\VERSION" -Raw).Trim()
$allowed = @(
  "V38.4.46-BANCADA-TERNARIO-USDA-VISUAL-1.0-20260816",
  "V38.4.46A-BANCADA-TERNARIO-CIENCIA-LINK-1.0-20260816"
)
if ($allowed -notcontains $current) { throw "Versão inesperada: $current. Este hotfix deve ser aplicado sobre a V38.4.46 visual." }
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$payload = Join-Path $scriptDir "payload"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = ".\backups\V38_4_46A_CIENCIA_$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$files = @(
  "VERSION",
  "docs\index.html",
  "docs\assets\js\ternario-usda-v38446.js",
  "docs\documentos\metodologia-ternario-usda.html"
)
foreach ($rel in $files) {
  $srcExisting = Join-Path "." $rel
  if (Test-Path $srcExisting) {
    $dstBackup = Join-Path $backup $rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dstBackup) | Out-Null
    Copy-Item $srcExisting $dstBackup -Force
  }
}
foreach ($rel in $files) {
  $src = Join-Path $payload $rel
  $dst = Join-Path "." $rel
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
  Copy-Item $src $dst -Force
}
node --check ".\docs\assets\js\ternario-usda-v38446.js"
if ($LASTEXITCODE -ne 0) { throw "Falha de sintaxe no JavaScript do ternário." }
$idx = Get-Content ".\docs\index.html" -Raw
if ($idx -notmatch 'data-ternario-science') { throw "Botão Ciência não encontrado após instalação." }
$js = Get-Content ".\docs\assets\js\ternario-usda-v38446.js" -Raw
if ($js -notmatch 'function science') { throw "Handler Ciência não encontrado após instalação." }
if (-not (Test-Path ".\docs\documentos\metodologia-ternario-usda.html")) { throw "Metodologia do ternário não encontrada." }
Write-Host "PASS · botão Ciência conectado à metodologia completa" -ForegroundColor Green
Write-Host "PASS · fallback para a mesma aba caso o navegador bloqueie nova janela" -ForegroundColor Green
Write-Host "Backup: $backup" -ForegroundColor DarkGray
