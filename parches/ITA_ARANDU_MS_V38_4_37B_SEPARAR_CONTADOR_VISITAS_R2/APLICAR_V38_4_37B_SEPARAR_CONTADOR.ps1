param(
[string]$Repo="C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms"
)

$ErrorActionPreference="Stop"

$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.37A-CONTADOR-VISITAS-1.0-20260815"
$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()

if($Current -ne $Expected){
 throw "Base incorreta  $Current  Esperada  $Expected"
}

function Invoke-Py{
 param(
 [Parameter(Mandatory=$true,Position=0)][string]$Script,
 [Parameter(ValueFromRemainingArguments=$true)][string[]]$PyArgs
 )
 if(Get-Command py -ErrorAction SilentlyContinue){
  & py -3 $Script @PyArgs
 }elseif(Get-Command python -ErrorAction SilentlyContinue){
  & python $Script @PyArgs
 }else{
  throw "Python nao encontrado"
 }
 if($LASTEXITCODE -ne 0){
  throw "Python terminou com codigo $LASTEXITCODE"
 }
}

$Catalog=Join-Path $Root "docs\camadas\catalogo-local.json"
$Manifest=Join-Path $Root "docs\camadas\snapshots-manifest.json"

$CH=(Get-FileHash -Algorithm SHA256 $Catalog).Hash.ToLower()
$MH=(Get-FileHash -Algorithm SHA256 $Manifest).Hash.ToLower()

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_37B_CONTADOR_SEPARADO_"+$Stamp)

New-Item -ItemType Directory -Path $Backup -Force | Out-Null

$Touched=@(
"VERSION",
"docs\index.html",
"docs\service-worker.js",
"CHANGELOG.md"
)

foreach($rel in $Touched){
 $src=Join-Path $Root $rel
 if(Test-Path $src){
  $dst=Join-Path $Backup $rel
  New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
  Copy-Item $src $dst -Force
 }
}

try{
 Write-Host ""
 Write-Host "ITA ARANDU MS  V38.4.37B  CONTADOR SEPARADO" -ForegroundColor Cyan
 Write-Host "Tracker GoatCounter sera preservado" -ForegroundColor Green
 Write-Host "Leitor do painel Dados sera removido" -ForegroundColor Green
 Write-Host "Pagina independente Visitas sera criada" -ForegroundColor Green

 Invoke-Py "$PSScriptRoot\payload\tools\apply_v38437b.py" --repo "$Root" --payload "$PSScriptRoot\payload"

 if(Get-Command py -ErrorAction SilentlyContinue){
  & py -3 "$PSScriptRoot\payload\tools\audit_v38437b.py" --repo "$Root" --catalog-sha "$CH" --manifest-sha "$MH"
 }else{
  & python "$PSScriptRoot\payload\tools\audit_v38437b.py" --repo "$Root" --catalog-sha "$CH" --manifest-sha "$MH"
 }

 if($LASTEXITCODE -ne 0){
  throw "Auditoria terminou com codigo $LASTEXITCODE"
 }

 Write-Host ""
 Write-Host "V38.4.37B APLICADA COM SUCESSO" -ForegroundColor Green
 Write-Host "Dados estatisticos desacoplados do GoatCounter" -ForegroundColor Green
 Write-Host "Tracker de visitas continua ativo" -ForegroundColor Green
 Write-Host "Nova pagina  docs\visitas\index.html" -ForegroundColor Green
 Write-Host "0 camadas alteradas | 0 indices recalculados" -ForegroundColor Green
 Write-Host "Backup  $Backup" -ForegroundColor DarkGray

}catch{
 Write-Host "Falha. Restaurando estado anterior." -ForegroundColor Red

 foreach($rel in $Touched){
  $src=Join-Path $Backup $rel
  $dst=Join-Path $Root $rel
  if(Test-Path $src){
   New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
   Copy-Item $src $dst -Force
  }
 }

 $new=Join-Path $Root "docs\visitas\index.html"
 if(Test-Path $new){
  Remove-Item $new -Force
 }

 throw
}
