param(
 [string]$Repo="C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms"
)
$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.44-ISGT-UI-FIX-1.0-20260816"
$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if($Current -ne $Expected){throw "Base incorreta  $Current  Esperada  $Expected"}

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_45_ISGT_SNAPSHOT_"+$Stamp)
New-Item -ItemType Directory -Force -Path $Backup | Out-Null

$Touched=@(
 "VERSION",
 "CHANGELOG.md",
 "docs\index.html",
 "docs\service-worker.js",
 "docs\assets\js\app.js",
 "docs\camadas\catalogo-local.js",
 "docs\camadas\proveniencia-snapshots.js",
 "docs\camadas\arquivos\isgt_v01_250km2.geojson",
 "docs\camadas\arquivos\terras_indigenas_funai_ms.geojson",
 "docs\camadas\arquivos\territorios_quilombolas_incra_ms.geojson",
 "docs\camadas\arquivos\unidades_conservacao_cnuc_ms.geojson",
 "docs\camadas\arquivos\zonas_amortecimento_ms.geojson",
 "docs\camadas\arquivos\corredores_ecologicos_ms.geojson",
 "docs\camadas\arquivos\areas_uso_restrito_ms.geojson",
 "docs\camadas\arquivos\aur_pantanal_ms.geojson",
 "docs\dados\snapshots\isgt_v01_250km2_20260816.json",
 "AUDITORIA_V38_4_45_ISGT_SNAPSHOT.json"
)

foreach($rel in $Touched){
 $src=Join-Path $Root $rel
 if(Test-Path $src){
  $dst=Join-Path $Backup $rel
  New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent)|Out-Null
  Copy-Item $src $dst -Force
 }
}

try{
 Write-Host ""
 Write-Host "ITA ARANDU MS · V38.4.45 · ISGT V0.1 SNAPSHOT · R2" -ForegroundColor Cyan
 Write-Host "Materializacao fisica dos 1.554 hexagonos" -ForegroundColor Cyan
 Write-Host "FUNAI · INCRA · IBGE · CNUC/MMA · IMASUL/PIN MS" -ForegroundColor Yellow
 Write-Host ""

 if(Get-Command py -ErrorAction SilentlyContinue){
   & py -3 "$PSScriptRoot\tools\materializar_isgt_v01_v38445.py" --repo $Root
 } elseif(Get-Command python -ErrorAction SilentlyContinue){
   & python "$PSScriptRoot\tools\materializar_isgt_v01_v38445.py" --repo $Root
 } else {throw "Python nao encontrado"}

 if($LASTEXITCODE -ne 0){throw "Materializador terminou com codigo $LASTEXITCODE"}

 if(Get-Command node -ErrorAction SilentlyContinue){
   & node --check (Join-Path $Root "docs\assets\js\app.js")
   if($LASTEXITCODE -ne 0){throw "app.js falhou no node --check"}
 }

 $Audit=Join-Path $Root "AUDITORIA_V38_4_45_ISGT_SNAPSHOT.json"
 if(!(Test-Path $Audit)){throw "Auditoria final nao foi criada"}

 Write-Host ""
 Write-Host "V38.4.45 APLICADA COM SUCESSO" -ForegroundColor Green
 Write-Host "ISGT agora e snapshot local de 1.554 hexagonos." -ForegroundColor Green
 Write-Host "Use Ctrl + F5 na primeira abertura." -ForegroundColor Yellow
 Write-Host "Backup  $Backup" -ForegroundColor DarkGray
}
catch{
 Write-Host ""
 Write-Host "FALHA · restaurando V38.4.44" -ForegroundColor Red

 foreach($rel in $Touched){
  $dst=Join-Path $Root $rel
  $bak=Join-Path $Backup $rel
  if(Test-Path $bak){
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent)|Out-Null
    Copy-Item $bak $dst -Force
  } elseif(Test-Path $dst){
    Remove-Item $dst -Force
  }
 }
 throw
}
