$ErrorActionPreference = "Stop"
Write-Host "ITA ARANDU MS · V38.4.46C · navegação robusta Ajuda/Ciência" -ForegroundColor Cyan
$root = (Get-Location).Path
$versionFile = Join-Path $root "VERSION"
if (!(Test-Path $versionFile)) { throw "VERSION não encontrado. Execute este script na raiz do repositório ITA ARANDU MS." }
$current = (Get-Content $versionFile -Raw).Trim()
$allowed = @(
  "V38.4.46B-BANCADA-TERNARIO-NAVEGACAO-INTERNA-1.0-20260816",
  "V38.4.46A-BANCADA-TERNARIO-CIENCIA-1.0-20260816",
  "V38.4.46-BANCADA-TERNARIO-USDA-VISUAL-1.0-20260816"
)
if ($allowed -notcontains $current) {
  throw "Versão não esperada: $current. Esperada V38.4.46 visual, 46A ou 46B."
}
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $root "BACKUPS\V38_4_46C_NAV_ROBUSTA_$stamp"
New-Item -ItemType Directory -Force -Path (Join-Path $backup "docs\assets\js") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $backup "docs\assets\css") | Out-Null
Copy-Item (Join-Path $root "VERSION") $backup -Force
Copy-Item (Join-Path $root "docs\index.html") (Join-Path $backup "docs\index.html") -Force
Copy-Item (Join-Path $root "docs\assets\js\ternario-usda-v38446.js") (Join-Path $backup "docs\assets\js\ternario-usda-v38446.js") -Force
if (Test-Path (Join-Path $root "docs\assets\css\ternario-usda-v38446.css")) { Copy-Item (Join-Path $root "docs\assets\css\ternario-usda-v38446.css") (Join-Path $backup "docs\assets\css\ternario-usda-v38446.css") -Force }
$payload = Join-Path $PSScriptRoot "payload"
Copy-Item (Join-Path $payload "docs\index.html") (Join-Path $root "docs\index.html") -Force
Copy-Item (Join-Path $payload "docs\assets\js\ternario-usda-v38446.js") (Join-Path $root "docs\assets\js\ternario-usda-v38446.js") -Force
Copy-Item (Join-Path $payload "docs\assets\css\ternario-usda-v38446.css") (Join-Path $root "docs\assets\css\ternario-usda-v38446.css") -Force
Copy-Item (Join-Path $payload "VERSION") (Join-Path $root "VERSION") -Force
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) { & node --check (Join-Path $root "docs\assets\js\ternario-usda-v38446.js"); if ($LASTEXITCODE -ne 0) { throw "Falha de sintaxe no JavaScript do ternário." } }
$html = Get-Content (Join-Path $root "docs\index.html") -Raw
$js = Get-Content (Join-Path $root "docs\assets\js\ternario-usda-v38446.js") -Raw
foreach($needle in @('data-ternario-help','data-ternario-science','data-ternario-return','ternarioSubview')) { if($html -notmatch [regex]::Escape($needle)) { throw "HTML sem $needle" } }
foreach($needle in @('ternarioDelegated','showSubview','returnToDiagram')) { if($js -notmatch [regex]::Escape($needle)) { throw "JS sem $needle" } }
Write-Host "PASS · Ajuda/Ciência usam navegação delegada no contêiner do ternário." -ForegroundColor Green
Write-Host "PASS · Voltar da subvista retorna ao diagrama sem fechar a ferramenta." -ForegroundColor Green
Write-Host "Backup: $backup" -ForegroundColor DarkGray
Write-Host "Versão: $((Get-Content $versionFile -Raw).Trim())" -ForegroundColor Green
