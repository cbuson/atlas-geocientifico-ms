$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$Docs = Join-Path $Root "docs"
if (!(Test-Path $Docs)) { throw "No se encontró la carpeta docs. Ejecute desde la raíz del repositorio." }
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Backup = Join-Path $Docs ("_backup_R9_" + $Stamp)
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
Copy-Item (Join-Path $Docs "index.html") $Backup -Force
if (Test-Path (Join-Path $Docs "service-worker.js")) { Copy-Item (Join-Path $Docs "service-worker.js") $Backup -Force }

Copy-Item (Join-Path $Here "files\assets\css\bancada-normalizacao-r9.css") (Join-Path $Docs "assets\css\bancada-normalizacao-r9.css") -Force
Copy-Item (Join-Path $Here "files\assets\js\bancada-normalizacao-r9.js") (Join-Path $Docs "assets\js\bancada-normalizacao-r9.js") -Force

$IndexPath = Join-Path $Docs "index.html"
$Index = Get-Content $IndexPath -Raw -Encoding UTF8
$CssTag = '<link rel="stylesheet" href="./assets/css/bancada-normalizacao-r9.css?v=9.0">'
$JsTag = '<script src="./assets/js/bancada-normalizacao-r9.js?v=9.0" defer></script>'
if ($Index -notmatch 'bancada-normalizacao-r9\.css') { $Index = $Index -replace '</head>', ($CssTag + "`r`n</head>") }
if ($Index -notmatch 'bancada-normalizacao-r9\.js') { $Index = $Index -replace '</body>', ($JsTag + "`r`n</body>") }
Set-Content $IndexPath $Index -Encoding UTF8

$SwPath = Join-Path $Docs "service-worker.js"
if (Test-Path $SwPath) {
  $Sw = Get-Content $SwPath -Raw -Encoding UTF8
  $Sw = [regex]::Replace($Sw, "ita-arandu-[A-Za-z0-9_.-]+", "ita-arandu-bancada-r9", 1)
  if ($Sw -notmatch 'bancada-normalizacao-r9\.css') {
    $Sw = $Sw -replace '(?s)(const\s+ITA_CORE\s*=\s*\[)', '$1`r`n  "./assets/css/bancada-normalizacao-r9.css?v=9.0",`r`n  "./assets/js/bancada-normalizacao-r9.js?v=9.0",'
  }
  Set-Content $SwPath $Sw -Encoding UTF8
}

Write-Host ""
Write-Host "PATCH BANCADA R9 aplicado corretamente" -ForegroundColor Green
Write-Host "Scroll móvil corregido en Bússola, Nível y GPS" -ForegroundColor Green
Write-Host "Catálogo normalizado a una única acción Abrir" -ForegroundColor Green
Write-Host "Ajuda e Ciência normalizado dentro de las herramientas" -ForegroundColor Green
Write-Host "Coluna Estratigráfica y Correlação Estratigráfica no fueron modificadas" -ForegroundColor Cyan
Write-Host "Backup: $Backup" -ForegroundColor Yellow
