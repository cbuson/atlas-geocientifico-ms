param(
  [string]$Repo = "C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms"
)

$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path

$Allowed=@(
 "V38.4.28-SNAPSHOT-FIRST-DUAL-SOURCE-R8-20260815",
 "V38.4.29-MOBILE-MAP-TOOLS-INTEGRADOS-20260815"
)

if(!(Test-Path (Join-Path $Root "VERSION"))){throw "VERSION nao encontrado"}
$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if($Allowed -notcontains $Current){throw "Base nao reconhecida  $Current"}

function Invoke-Py {
  param(
    [Parameter(Mandatory=$true,Position=0)][string]$Script,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$PyArgs
  )
  if(Get-Command py -ErrorAction SilentlyContinue){& py -3 $Script @PyArgs}
  elseif(Get-Command python -ErrorAction SilentlyContinue){& python $Script @PyArgs}
  else{throw "Python nao encontrado"}
  if($LASTEXITCODE -ne 0){throw "Python terminou com codigo $LASTEXITCODE"}
}

$Catalog=Join-Path $Root "docs\camadas\catalogo-local.json"
$Manifest=Join-Path $Root "docs\camadas\snapshots-manifest.json"
$CatalogHash=""
$ManifestHash=""
if(Test-Path $Catalog){$CatalogHash=(Get-FileHash -Algorithm SHA256 $Catalog).Hash.ToLower()}
if(Test-Path $Manifest){$ManifestHash=(Get-FileHash -Algorithm SHA256 $Manifest).Hash.ToLower()}

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_30_CAMPO_GEOFOTO_"+$Stamp)
New-Item -ItemType Directory -Path $Backup -Force|Out-Null

$Touched=@("VERSION","docs\index.html","docs\service-worker.js","CHANGELOG.md")
foreach($rel in $Touched){
  $src=Join-Path $Root $rel
  if(Test-Path $src){
    $dst=Join-Path $Backup $rel
    New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null
    Copy-Item $src $dst -Force
  }
}

$New=@(
 "docs\assets\js\campo-geofoto-v38430.js",
 "docs\assets\css\campo-geofoto-v38430.css",
 "docs\documentos\protocolo-campo-geofoto.html"
)

try{
  Write-Host ""
  Write-Host "ITA ARANDU MS  V38.4.30  CAMPO GEOFOTO 1.0" -ForegroundColor Cyan
  Write-Host "Repositorio  $Root"
  Write-Host "Base  $Current"
  Write-Host "Camadas, snapshots e indices permanecerao intactos" -ForegroundColor Green
  Write-Host ""

  Write-Host "Instalando Caderno de Campo Geocientifico Digital" -ForegroundColor Yellow
  Invoke-Py "$PSScriptRoot\payload\tools\apply_campo_geofoto_v38430.py" --repo "$Root" --payload "$PSScriptRoot\payload"

  Write-Host "Executando auditoria" -ForegroundColor Yellow
  $Args=@("--repo",$Root)
  if($CatalogHash){$Args+=@("--catalog-sha",$CatalogHash)}
  if($ManifestHash){$Args+=@("--manifest-sha",$ManifestHash)}

  if(Get-Command py -ErrorAction SilentlyContinue){
    & py -3 "$PSScriptRoot\payload\tools\audit_campo_geofoto_v38430.py" @Args
  } elseif(Get-Command python -ErrorAction SilentlyContinue){
    & python "$PSScriptRoot\payload\tools\audit_campo_geofoto_v38430.py" @Args
  } else {throw "Python nao encontrado"}

  if($LASTEXITCODE -ne 0){throw "Auditoria terminou com codigo $LASTEXITCODE"}

  Write-Host ""
  Write-Host "V38.4.30 CAMPO GEOFOTO 1.0 APLICADA COM SUCESSO" -ForegroundColor Green
  Write-Host "Camera geocientifica integrada ao Campo" -ForegroundColor Green
  Write-Host "GPS + UTM + orientacao + SHA256 + EXIF de importacao" -ForegroundColor Green
  Write-Host "JSON + GeoJSON + KML" -ForegroundColor Green
  Write-Host "0 camadas alteradas" -ForegroundColor Green
  Write-Host "0 indices recalculados" -ForegroundColor Green
  Write-Host "Backup  $Backup" -ForegroundColor DarkGray
  Write-Host ""
}
catch{
  Write-Host ""
  Write-Host "Falha. Restaurando estado anterior." -ForegroundColor Red
  foreach($rel in $Touched){
    $src=Join-Path $Backup $rel
    $dst=Join-Path $Root $rel
    if(Test-Path $src){
      New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null
      Copy-Item $src $dst -Force
    }
  }
  foreach($rel in $New){
    $p=Join-Path $Root $rel
    if(Test-Path $p){Remove-Item $p -Force}
  }
  throw
}
