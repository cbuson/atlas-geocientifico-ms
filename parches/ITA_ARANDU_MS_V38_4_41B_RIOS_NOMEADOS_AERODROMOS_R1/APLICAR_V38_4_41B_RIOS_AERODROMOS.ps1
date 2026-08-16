param(
 [string]$Repo="C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms"
)
$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.41A-ESTRADAS-VICINAIS-OFFLINE-1.0-20260816"
$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if($Current -ne $Expected){ throw "Base incorreta  $Current  Esperada  $Expected" }

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_41B_RIOS_AERODROMOS_"+$Stamp)
New-Item -ItemType Directory -Force -Path $Backup | Out-Null

$Touched=@(
 "VERSION",
 "CHANGELOG.md",
 "docs\assets\js\app.js",
 "docs\camadas\catalogo-local.js",
 "docs\camadas\proveniencia-snapshots.js",
 "docs\camadas\arquivos\rios_principais_ms.geojson",
 "docs\camadas\arquivos\aeroportos_aerodromos_ms.geojson",
 "docs\dados\snapshots\rios_nomeados_aerodromos_20260816.json"
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
 Write-Host "ITA ARANDU MS · V38.4.41B" -ForegroundColor Cyan
 Write-Host "RIOS NOMEADOS + AEROPORTOS E AERODROMOS" -ForegroundColor Cyan
 Write-Host "Hidrografia completa NAO sera baixada." -ForegroundColor Yellow
 Write-Host "Estradas vicinais NAO serao modificadas." -ForegroundColor Yellow
 Write-Host ""

 if(Get-Command py -ErrorAction SilentlyContinue){
   & py -3 "$PSScriptRoot\tools\materializar_rios_aerodromos_v38441b.py" --repo $Root
 } elseif(Get-Command python -ErrorAction SilentlyContinue){
   & python "$PSScriptRoot\tools\materializar_rios_aerodromos_v38441b.py" --repo $Root
 } else { throw "Python nao encontrado" }

 if($LASTEXITCODE -ne 0){ throw "Materializador terminou com codigo $LASTEXITCODE" }

 if(Get-Command node -ErrorAction SilentlyContinue){
   & node --check (Join-Path $Root "docs\assets\js\app.js")
   if($LASTEXITCODE -ne 0){ throw "app.js falhou no node --check" }
 }

 Write-Host ""
 Write-Host "V38.4.41B APLICADA COM SUCESSO" -ForegroundColor Green
 Write-Host "Rios nomeados e aerodromos agora possuem snapshot local." -ForegroundColor Green
 Write-Host "Backup  $Backup" -ForegroundColor DarkGray
}
catch{
 Write-Host ""
 Write-Host "FALHA · restaurando V38.4.41A" -ForegroundColor Red
 foreach($rel in $Touched){
   $dst=Join-Path $Root $rel
   $bak=Join-Path $Backup $rel
   if(Test-Path $bak){
     New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
     Copy-Item $bak $dst -Force
   } elseif(Test-Path $dst){ Remove-Item $dst -Force }
 }
 throw
}
