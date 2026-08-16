param(
 [string]$Repo="C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms",
 [string]$GoatCode=""
)
$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.37-ESTEREOGRAMA-CALCULADORA-1.0-20260815"
$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if($Current -ne $Expected){throw "Base incorreta  $Current  Esperada  $Expected"}

if([string]::IsNullOrWhiteSpace($GoatCode)){
 Write-Host ""
 Write-Host "Digite somente o codigo do seu sitio GoatCounter." -ForegroundColor Yellow
 Write-Host "Exemplo  se o endereco for https://ita-arandu.goatcounter.com use ita-arandu" -ForegroundColor DarkGray
 $GoatCode=Read-Host "Codigo GoatCounter"
}
$GoatCode=$GoatCode.Trim().ToLower()
if($GoatCode -notmatch '^[a-z0-9][a-z0-9-]{1,62}$'){throw "Codigo GoatCounter invalido"}

function Invoke-Py{param([Parameter(Mandatory=$true,Position=0)][string]$Script,[Parameter(ValueFromRemainingArguments=$true)][string[]]$PyArgs);if(Get-Command py -ErrorAction SilentlyContinue){& py -3 $Script @PyArgs}elseif(Get-Command python -ErrorAction SilentlyContinue){& python $Script @PyArgs}else{throw "Python nao encontrado"};if($LASTEXITCODE -ne 0){throw "Python terminou com codigo $LASTEXITCODE"}}

$Catalog=Join-Path $Root "docs\camadas\catalogo-local.json";$Manifest=Join-Path $Root "docs\camadas\snapshots-manifest.json";$Master=Join-Path $Root "docs\assets\js\campo-master-v38431.js";$Struct=Join-Path $Root "docs\assets\js\estereograma-calculadora-v38437.js"
$CH=(Get-FileHash -Algorithm SHA256 $Catalog).Hash.ToLower();$MH=(Get-FileHash -Algorithm SHA256 $Manifest).Hash.ToLower();$MasterH=(Get-FileHash -Algorithm SHA256 $Master).Hash.ToLower();$StructH=(Get-FileHash -Algorithm SHA256 $Struct).Hash.ToLower()

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss";$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_37A_CONTADOR_VISITAS_"+$Stamp);New-Item -ItemType Directory -Path $Backup -Force|Out-Null
$Touched=@("VERSION","docs\index.html","docs\service-worker.js","docs\referencias\index.html","CHANGELOG.md")
foreach($rel in $Touched){$src=Join-Path $Root $rel;if(Test-Path $src){$dst=Join-Path $Backup $rel;New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null;Copy-Item $src $dst -Force}}
$New=@("docs\assets\js\contador-visitas-v38437a.js","docs\documentos\metodologia-contador-visitas.html","docs\documentos\contador-visitas-referencias.json")

try{
 Write-Host ""
 Write-Host "ITA ARANDU MS  V38.4.37A  CONTADOR AGREGADO DE VISITAS" -ForegroundColor Cyan
 Write-Host "Provedor  GoatCounter" -ForegroundColor Green
 Write-Host "Codigo    $GoatCode"
 Write-Host "Sem token privado no repositorio" -ForegroundColor Green
 Invoke-Py "$PSScriptRoot\payload\tools\apply_contador_visitas_v38437a.py" --repo "$Root" --payload "$PSScriptRoot\payload" --code "$GoatCode"
 if(Get-Command py -ErrorAction SilentlyContinue){& py -3 "$PSScriptRoot\payload\tools\audit_contador_visitas_v38437a.py" --repo "$Root" --catalog-sha "$CH" --manifest-sha "$MH" --master-sha "$MasterH" --struct-sha "$StructH"}else{& python "$PSScriptRoot\payload\tools\audit_contador_visitas_v38437a.py" --repo "$Root" --catalog-sha "$CH" --manifest-sha "$MH" --master-sha "$MasterH" --struct-sha "$StructH"}
 if($LASTEXITCODE -ne 0){throw "Auditoria terminou com codigo $LASTEXITCODE"}
 Write-Host ""
 Write-Host "V38.4.37A CONTADOR DE VISITAS APLICADO COM SUCESSO" -ForegroundColor Green
 Write-Host "Visitas acumuladas + hoje + 7 dias + mes atual" -ForegroundColor Green
 Write-Host "0 tokens privados expostos" -ForegroundColor Green
 Write-Host "0 camadas alteradas | 0 indices recalculados" -ForegroundColor Green
 Write-Host ""
 Write-Host "IMPORTANTE" -ForegroundColor Yellow
 Write-Host "No GoatCounter ative  Settings > Allow adding visitor counts on your website." -ForegroundColor Yellow
 Write-Host "Depois publique no GitHub Pages e teste no endereco publico." -ForegroundColor Yellow
 Write-Host "Backup  $Backup" -ForegroundColor DarkGray
}catch{
 Write-Host "Falha. Restaurando estado anterior." -ForegroundColor Red
 foreach($rel in $Touched){$src=Join-Path $Backup $rel;$dst=Join-Path $Root $rel;if(Test-Path $src){New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null;Copy-Item $src $dst -Force}}
 foreach($rel in $New){$p=Join-Path $Root $rel;if(Test-Path $p){Remove-Item $p -Force}}
 throw
}
