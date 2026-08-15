param(
  [string]$Repo = "C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms"
)

$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.28-SNAPSHOT-FIRST-DUAL-SOURCE-R8-20260815"

if(!(Test-Path (Join-Path $Root "VERSION"))){throw "VERSION nao encontrado"}

$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if($Current -ne $Expected){throw "Base incorreta  $Current  Esperada  $Expected"}

function Invoke-Py {
  param(
    [Parameter(Mandatory=$true,Position=0)]
    [string]$Script,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$PyArgs
  )
  if(Get-Command py -ErrorAction SilentlyContinue){& py -3 $Script @PyArgs}
  elseif(Get-Command python -ErrorAction SilentlyContinue){& python $Script @PyArgs}
  else{throw "Python nao encontrado"}
  if($LASTEXITCODE -ne 0){throw "Python terminou com codigo $LASTEXITCODE"}
}

$CatalogJson=Join-Path $Root "docs\camadas\catalogo-local.json"
$SnapshotManifest=Join-Path $Root "docs\camadas\snapshots-manifest.json"
$CatalogHash=""
$ManifestHash=""

if(Test-Path $CatalogJson){$CatalogHash=(Get-FileHash -Algorithm SHA256 $CatalogJson).Hash.ToLower()}
if(Test-Path $SnapshotManifest){$ManifestHash=(Get-FileHash -Algorithm SHA256 $SnapshotManifest).Hash.ToLower()}

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_29_MOBILE_TOOLBAR_"+$Stamp)
New-Item -ItemType Directory -Path $Backup -Force|Out-Null

$Touched=@("VERSION","docs\index.html","docs\assets\js\app.js","docs\service-worker.js","CHANGELOG.md")
foreach($rel in $Touched){
  $src=Join-Path $Root $rel
  if(Test-Path $src){
    $dst=Join-Path $Backup $rel
    New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null
    Copy-Item $src $dst -Force
  }
}

$NewCss=Join-Path $Root "docs\assets\css\mobile-map-toolbar-v38429.css"

try{
  Write-Host ""
  Write-Host "ITA ARANDU MS  V38.4.29  MOBILE MAP TOOLBAR" -ForegroundColor Cyan
  Write-Host "Repositorio  $Root"
  Write-Host "Base detectada  V38.4.28 R8" -ForegroundColor Green
  Write-Host "Camadas, snapshots e indices nao serao alterados" -ForegroundColor Green
  Write-Host ""

  Write-Host "Integrando Base e Legenda na barra superior esquerda" -ForegroundColor Yellow
  Invoke-Py "$PSScriptRoot\payload\tools\apply_mobile_toolbar_v38429.py" --repo "$Root" --payload "$PSScriptRoot\payload"

  Write-Host "Executando auditoria" -ForegroundColor Yellow
  $AuditArgs=@("--repo",$Root)
  if($CatalogHash){$AuditArgs+=@("--catalog-json-sha",$CatalogHash)}
  if($ManifestHash){$AuditArgs+=@("--manifest-sha",$ManifestHash)}

  if(Get-Command py -ErrorAction SilentlyContinue){
    & py -3 "$PSScriptRoot\payload\tools\audit_mobile_toolbar_v38429.py" @AuditArgs
  } elseif(Get-Command python -ErrorAction SilentlyContinue){
    & python "$PSScriptRoot\payload\tools\audit_mobile_toolbar_v38429.py" @AuditArgs
  } else {throw "Python nao encontrado"}

  if($LASTEXITCODE -ne 0){throw "Auditoria terminou com codigo $LASTEXITCODE"}

  Write-Host ""
  Write-Host "V38.4.29 APLICADA COM SUCESSO" -ForegroundColor Green
  Write-Host "Base e Legenda integradas na barra do mapa" -ForegroundColor Green
  Write-Host "Botoes flutuantes da direita removidos" -ForegroundColor Green
  Write-Host "0 camadas alteradas" -ForegroundColor Green
  Write-Host "0 indices recalculados" -ForegroundColor Green
  Write-Host "Backup  $Backup" -ForegroundColor DarkGray
  Write-Host ""
}
catch{
  Write-Host ""
  Write-Host "Falha. Restaurando interface anterior." -ForegroundColor Red
  foreach($rel in $Touched){
    $src=Join-Path $Backup $rel
    $dst=Join-Path $Root $rel
    if(Test-Path $src){
      New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null
      Copy-Item $src $dst -Force
    }
  }
  if(Test-Path $NewCss){Remove-Item $NewCss -Force}
  throw
}
