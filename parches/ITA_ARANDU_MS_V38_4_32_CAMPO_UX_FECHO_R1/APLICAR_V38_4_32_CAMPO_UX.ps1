param(
  [string]$Repo = "C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms"
)

$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.31-CAMPO-MASTER-2.0-20260815"

if(!(Test-Path (Join-Path $Root "VERSION"))){throw "VERSION nao encontrado"}
$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if($Current -ne $Expected){throw "Base incorreta  $Current  Esperada  $Expected"}

function Invoke-Py {
  param([Parameter(Mandatory=$true,Position=0)][string]$Script,[Parameter(ValueFromRemainingArguments=$true)][string[]]$PyArgs)
  if(Get-Command py -ErrorAction SilentlyContinue){& py -3 $Script @PyArgs}
  elseif(Get-Command python -ErrorAction SilentlyContinue){& python $Script @PyArgs}
  else{throw "Python nao encontrado"}
  if($LASTEXITCODE -ne 0){throw "Python terminou com codigo $LASTEXITCODE"}
}

$Catalog=Join-Path $Root "docs\camadas\catalogo-local.json"
$Manifest=Join-Path $Root "docs\camadas\snapshots-manifest.json"
$MasterJs=Join-Path $Root "docs\assets\js\campo-master-v38431.js"

$CatalogHash="";$ManifestHash="";$MasterJsHash=""
if(Test-Path $Catalog){$CatalogHash=(Get-FileHash -Algorithm SHA256 $Catalog).Hash.ToLower()}
if(Test-Path $Manifest){$ManifestHash=(Get-FileHash -Algorithm SHA256 $Manifest).Hash.ToLower()}
if(Test-Path $MasterJs){$MasterJsHash=(Get-FileHash -Algorithm SHA256 $MasterJs).Hash.ToLower()}

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_32_CAMPO_UX_"+$Stamp)
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
$New=@("docs\assets\css\campo-ux-v38432.css","docs\assets\js\campo-ux-v38432.js")

try{
  Write-Host ""
  Write-Host "ITA ARANDU MS  V38.4.32  FECHAMENTO UX DO CAMPO" -ForegroundColor Cyan
  Write-Host "Base  $Current"
  Write-Host "Motor cientifico Campo Master 2.0 sera mantido intacto" -ForegroundColor Green
  Write-Host "Camadas, snapshots e indices permanecerao intactos" -ForegroundColor Green
  Write-Host ""

  Invoke-Py "$PSScriptRoot\payload\tools\apply_campo_ux_v38432.py" --repo "$Root" --payload "$PSScriptRoot\payload"

  $Args=@("--repo",$Root)
  if($CatalogHash){$Args+=@("--catalog-sha",$CatalogHash)}
  if($ManifestHash){$Args+=@("--manifest-sha",$ManifestHash)}
  if($MasterJsHash){$Args+=@("--master-js-sha",$MasterJsHash)}

  if(Get-Command py -ErrorAction SilentlyContinue){
    & py -3 "$PSScriptRoot\payload\tools\audit_campo_ux_v38432.py" @Args
  } else {
    & python "$PSScriptRoot\payload\tools\audit_campo_ux_v38432.py" @Args
  }
  if($LASTEXITCODE -ne 0){throw "Auditoria terminou com codigo $LASTEXITCODE"}

  Write-Host ""
  Write-Host "V38.4.32 CAMPO UX APLICADA COM SUCESSO" -ForegroundColor Green
  Write-Host "Acordeoes inteligentes no celular" -ForegroundColor Green
  Write-Host "Estudante Essencial + Especialista Avancado" -ForegroundColor Green
  Write-Host "Anterior + Proximo + salto de secao" -ForegroundColor Green
  Write-Host "Completude com pendencia visivel" -ForegroundColor Green
  Write-Host "Meu caderno atualizado para funcional" -ForegroundColor Green
  Write-Host "Campo Master 2.0 intacto" -ForegroundColor Green
  Write-Host "0 camadas alteradas" -ForegroundColor Green
  Write-Host "0 indices recalculados" -ForegroundColor Green
  Write-Host "Backup  $Backup" -ForegroundColor DarkGray
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
  foreach($rel in $New){
    $p=Join-Path $Root $rel
    if(Test-Path $p){Remove-Item $p -Force}
  }
  throw
}
