$ErrorActionPreference = "Stop"
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Location).Path

Write-Host "ITA ARANDU MS · V38.4.46 · Bancada Digital + Ternario USDA" -ForegroundColor Cyan
Write-Host "Base esperada · V38.4.45-ISGT-V01-SNAPSHOT-MATERIALIZADO-1.0-20260816"

$versionFile = Join-Path $ProjectRoot "VERSION"
if (!(Test-Path $versionFile)) { throw "VERSION nao encontrado. Execute este script na raiz do repositorio ITA ARANDU MS." }
$current = (Get-Content $versionFile -Raw).Trim()
if ($current -ne "V38.4.45-ISGT-V01-SNAPSHOT-MATERIALIZADO-1.0-20260816") {
  throw "Base recusada. Encontrado '$current'. Este patch foi construido especificamente sobre a V38.4.45 enviada." 
}
if (!(Test-Path (Join-Path $ProjectRoot "docs/index.html"))) { throw "docs/index.html nao encontrado." }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $ProjectRoot "backup_V38_4_46_$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

$files = @(
  "VERSION",
  "docs/index.html",
  "docs/service-worker.js",
  "docs/assets/css/ferramentas-hub-v38435.css",
  "docs/assets/css/ternario-usda-v38446.css",
  "docs/assets/js/ferramentas-hub-v38435.js",
  "docs/assets/js/ternario-usda-v38446.js",
  "docs/documentos/metodologia-ternario-usda.html",
  "docs/referencias/referencias.js",
  "docs/referencias/index.html",
  "AUDITORIA_V38_4_46_BANCADA_TERNARIO_USDA.json"
)

foreach ($rel in $files) {
  $srcExisting = Join-Path $ProjectRoot $rel
  if (Test-Path $srcExisting) {
    $bk = Join-Path $backup $rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $bk) | Out-Null
    Copy-Item $srcExisting $bk -Force
  }
}

foreach ($rel in $files) {
  $src = Join-Path (Join-Path $PatchRoot "payload") $rel
  if (!(Test-Path $src)) { throw "Arquivo ausente no patch · $rel" }
  $dst = Join-Path $ProjectRoot $rel
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
  Copy-Item $src $dst -Force
}

$newVersion = (Get-Content $versionFile -Raw).Trim()
if ($newVersion -ne "V38.4.46-BANCADA-TERNARIO-USDA-VISUAL-1.0-20260816") { throw "Falha na atualizacao de VERSION." }

Write-Host "" 
Write-Host "PASS · Patch aplicado" -ForegroundColor Green
Write-Host "PASS · Backup criado em $backup" -ForegroundColor Green
Write-Host "PASS · Bancada agrupada e responsiva" -ForegroundColor Green
Write-Host "PASS · Ternario USDA visual e interativo instalado" -ForegroundColor Green
Write-Host "PASS · Ajuda, metodologia e referencias REF-206 a REF-208 instaladas" -ForegroundColor Green
Write-Host "Caderneta permanece sem alteracoes funcionais." -ForegroundColor Yellow
Write-Host "Publique no GitHub e force a atualizacao da PWA se o navegador conservar cache antigo." -ForegroundColor Cyan
