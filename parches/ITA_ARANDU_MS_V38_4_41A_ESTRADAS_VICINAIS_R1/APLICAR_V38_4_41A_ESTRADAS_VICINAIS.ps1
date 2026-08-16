param(
  [string]$Repo="C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms"
)
$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.40B-CAMADAS-UX-CLEAN-1.0-20260816"
$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if($Current -ne $Expected){ throw "Base incorreta  $Current  Esperada  $Expected" }

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_41A_ESTRADAS_"+$Stamp)
New-Item -ItemType Directory -Force -Path $Backup | Out-Null

$Touched=@(
 "VERSION",
 "CHANGELOG.md",
 "docs\assets\js\app.js",
 "docs\camadas\catalogo-local.js",
 "docs\camadas\proveniencia-snapshots.js",
 "docs\camadas\arquivos\estradas_vicinais_ms.geojson",
 "docs\dados\snapshots\estradas_vicinais_20260816.json"
)

foreach($rel in $Touched){
 $src=Join-Path $Root $rel
 if(Test-Path $src){
  $dst=Join-Path $Backup $rel
  New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
  Copy-Item $src $dst -Force
 }
}

try{
 Write-Host ""
 Write-Host "ITA ARANDU MS · V38.4.41A · ESTRADAS VICINAIS OFFLINE" -ForegroundColor Cyan
 Write-Host "Download em blocos pequenos + retries automaticos" -ForegroundColor Cyan
 Write-Host ""

 if(Get-Command py -ErrorAction SilentlyContinue){
   & py -3 "$PSScriptRoot\tools\materializar_estradas_v38441a.py" --repo $Root
 } elseif(Get-Command python -ErrorAction SilentlyContinue){
   & python "$PSScriptRoot\tools\materializar_estradas_v38441a.py" --repo $Root
 } else {
   throw "Python nao encontrado"
 }
 if($LASTEXITCODE -ne 0){ throw "Materializador terminou com codigo $LASTEXITCODE" }

 if(Get-Command node -ErrorAction SilentlyContinue){
   & node --check (Join-Path $Root "docs\assets\js\app.js")
   if($LASTEXITCODE -ne 0){ throw "app.js falhou no node --check" }
 }

 Write-Host ""
 Write-Host "V38.4.41A APLICADA COM SUCESSO" -ForegroundColor Green
 Write-Host "Somente Estradas Vicinais foi materializada." -ForegroundColor Green
 Write-Host "Hidrografia nao foi tocada." -ForegroundColor Yellow
 Write-Host "Backup  $Backup" -ForegroundColor DarkGray
}
catch{
 Write-Host ""
 Write-Host "FALHA · restaurando V38.4.40B" -ForegroundColor Red
 foreach($rel in $Touched){
   $dst=Join-Path $Root $rel
   $bak=Join-Path $Backup $rel
   if(Test-Path $bak){
     New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
     Copy-Item $bak $dst -Force
   } elseif(Test-Path $dst){
     Remove-Item $dst -Force
   }
 }
 throw
}
