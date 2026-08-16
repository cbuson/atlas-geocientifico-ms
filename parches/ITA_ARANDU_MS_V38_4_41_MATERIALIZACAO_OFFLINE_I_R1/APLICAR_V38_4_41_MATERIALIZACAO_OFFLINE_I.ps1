param(
  [string]$Repo="C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms"
)
$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.40B-CAMADAS-UX-CLEAN-1.0-20260816"
$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if($Current -ne $Expected){ throw "Base incorreta  $Current  Esperada  $Expected" }

function Invoke-Py {
 param([string]$Script,[string[]]$ArgsList)
 if(Get-Command py -ErrorAction SilentlyContinue){ & py -3 $Script @ArgsList }
 elseif(Get-Command python -ErrorAction SilentlyContinue){ & python $Script @ArgsList }
 else{ throw "Python nao encontrado" }
 if($LASTEXITCODE -ne 0){ throw "Materializador terminou com codigo $LASTEXITCODE" }
}

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_41_MATERIALIZACAO_OFFLINE_I_"+$Stamp)
New-Item -ItemType Directory -Force -Path $Backup | Out-Null

$Touched=@(
 "VERSION",
 "CHANGELOG.md",
 "docs\assets\js\app.js",
 "docs\camadas\catalogo-local.js",
 "docs\camadas\proveniencia-snapshots.js",
 "docs\camadas\arquivos\estradas_vicinais_ms.geojson",
 "docs\camadas\arquivos\hidrografia_referencia_ms.geojson",
 "docs\camadas\arquivos\rios_principais_ms.geojson",
 "docs\camadas\arquivos\aeroportos_aerodromos_ms.geojson",
 "docs\dados\snapshots\materializacao_offline_20260816.json"
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
 Write-Host "ITA ARANDU MS · V38.4.41 · MATERIALIZACAO OFFLINE I" -ForegroundColor Cyan
 Write-Host "Estradas · Hidrografia · Rios nomeados · Aerodromos" -ForegroundColor Cyan
 Write-Host ""
 Write-Host "As fontes serao baixadas agora. Nao use VPN nem interrompa a conexao." -ForegroundColor Yellow
 Invoke-Py "$PSScriptRoot\tools\materializar_v38441.py" @("--repo",$Root)

 Write-Host ""
 Write-Host "Verificando sintaxe do motor principal..." -ForegroundColor Cyan
 if(Get-Command node -ErrorAction SilentlyContinue){
   & node --check (Join-Path $Root "docs\assets\js\app.js")
   if($LASTEXITCODE -ne 0){ throw "app.js falhou no node --check" }
 } else {
   Write-Host "Node nao encontrado · teste sintatico omitido" -ForegroundColor Yellow
 }

 $audit=Join-Path $Root "AUDITORIA_V38_4_41_MATERIALIZACAO_OFFLINE_I.json"
 if(!(Test-Path $audit)){ throw "Auditoria final nao foi criada" }

 Write-Host ""
 Write-Host "V38.4.41 APLICADA COM SUCESSO" -ForegroundColor Green
 Write-Host "Os quatro produtos agora possuem snapshots locais verificaveis." -ForegroundColor Green
 Write-Host "Backup  $Backup" -ForegroundColor DarkGray

}catch{
 Write-Host ""
 Write-Host "FALHA · restaurando V38.4.40B" -ForegroundColor Red

 foreach($rel in $Touched){
   $dst=Join-Path $Root $rel
   $bak=Join-Path $Backup $rel
   if(Test-Path $bak){
     New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
     Copy-Item $bak $dst -Force
   } elseif(Test-Path $dst) {
     Remove-Item $dst -Force
   }
 }
 throw
}
