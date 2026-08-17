$ErrorActionPreference = "Stop"
Write-Host "ITA ARANDU MS · V38.4.46B · navegação interna do ternário" -ForegroundColor Cyan
$root = (Get-Location).Path
$versionFile = Join-Path $root "VERSION"
if (!(Test-Path $versionFile)) { throw "VERSION não encontrado. Execute este script na raiz do repositório ITA ARANDU MS." }
$current = (Get-Content $versionFile -Raw).Trim()
$allowed = @(
  "V38.4.46A-BANCADA-TERNARIO-CIENCIA-LINK-1.0-20260816",
  "V38.4.46-BANCADA-TERNARIO-USDA-VISUAL-1.0-20260816"
)
if ($allowed -notcontains $current) { throw "Versão de base não reconhecida: $current`nEsperada V38.4.46A ou V38.4.46 visual." }
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$payload = Join-Path $scriptDir "payload"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $root "backups\V38_4_46B_NAV_$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$targets = @(
  "VERSION",
  "docs\index.html",
  "docs\assets\js\ternario-usda-v38446.js",
  "docs\assets\css\ternario-usda-v38446.css"
)
foreach ($rel in $targets) {
  $src = Join-Path $root $rel
  if (Test-Path $src) {
    $dst = Join-Path $backup $rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item $src $dst -Force
  }
}
foreach ($rel in $targets) {
  $src = Join-Path $payload $rel
  $dst = Join-Path $root $rel
  if (!(Test-Path $src)) { throw "Payload ausente: $rel" }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
  Copy-Item $src $dst -Force
}
$js = Join-Path $root "docs\assets\js\ternario-usda-v38446.js"
if (Get-Command node -ErrorAction SilentlyContinue) { node --check $js; if ($LASTEXITCODE -ne 0) { throw "Falha de sintaxe JavaScript" } }
$idx = Get-Content (Join-Path $root "docs\index.html") -Raw
if ($idx -notmatch 'id="ternarioSubview"' -or $idx -notmatch 'data-ternario-return') { throw "Validação da navegação interna falhou." }
Write-Host "PASS · navegação corrigida" -ForegroundColor Green
Write-Host "Bancada > Ternário > Ajuda/Ciência > Ternário > Bancada" -ForegroundColor Green
Write-Host "Backup: $backup" -ForegroundColor DarkGray
