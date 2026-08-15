param([string]$Repo="C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms")
$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.32-CAMPO-UX-FECHO-20260815"
$Current=(Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
if($Current -ne $Expected){throw "Base incorreta  $Current  Esperada  $Expected"}
function Invoke-Py{param([Parameter(Mandatory=$true,Position=0)][string]$Script,[Parameter(ValueFromRemainingArguments=$true)][string[]]$PyArgs);if(Get-Command py -ErrorAction SilentlyContinue){& py -3 $Script @PyArgs}elseif(Get-Command python -ErrorAction SilentlyContinue){& python $Script @PyArgs}else{throw "Python nao encontrado"};if($LASTEXITCODE -ne 0){throw "Python terminou com codigo $LASTEXITCODE"}}
$Catalog=Join-Path $Root "docs\camadas\catalogo-local.json";$Manifest=Join-Path $Root "docs\camadas\snapshots-manifest.json";$Master=Join-Path $Root "docs\assets\js\campo-master-v38431.js"
$CH=(Get-FileHash -Algorithm SHA256 $Catalog).Hash.ToLower();$MH=(Get-FileHash -Algorithm SHA256 $Manifest).Hash.ToLower();$MasterH=(Get-FileHash -Algorithm SHA256 $Master).Hash.ToLower()
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss";$Backup=Join-Path $env:TEMP ("ITA_ARANDU_BACKUPS\V38_4_33_CLINOMETRO_"+$Stamp);New-Item -ItemType Directory -Path $Backup -Force|Out-Null
$Touched=@("VERSION","docs\index.html","docs\service-worker.js","docs\referencias\index.html","CHANGELOG.md")
foreach($rel in $Touched){$src=Join-Path $Root $rel;if(Test-Path $src){$dst=Join-Path $Backup $rel;New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null;Copy-Item $src $dst -Force}}
$New=@("docs\assets\css\clinometro-visual-v38433.css","docs\assets\js\clinometro-visual-v38433.js","docs\documentos\metodologia-clinometro-visual-arandu.html")
try{
 Write-Host "";Write-Host "ITA ARANDU MS  V38.4.33  CLINOMETRO VISUAL ARANDU" -ForegroundColor Cyan
 Write-Host "Metodologia e bibliografia APA 7 integradas" -ForegroundColor Green
 Write-Host "Campo Master, camadas, snapshots e indices serao preservados" -ForegroundColor Green
 Invoke-Py "$PSScriptRoot\payload\tools\apply_clinometro_v38433.py" --repo "$Root" --payload "$PSScriptRoot\payload"
 if(Get-Command py -ErrorAction SilentlyContinue){& py -3 "$PSScriptRoot\payload\tools\audit_clinometro_v38433.py" --repo "$Root" --catalog-sha "$CH" --manifest-sha "$MH" --master-sha "$MasterH"}else{& python "$PSScriptRoot\payload\tools\audit_clinometro_v38433.py" --repo "$Root" --catalog-sha "$CH" --manifest-sha "$MH" --master-sha "$MasterH"}
 if($LASTEXITCODE -ne 0){throw "Auditoria terminou com codigo $LASTEXITCODE"}
 Write-Host "";Write-Host "V38.4.33 CLINOMETRO VISUAL ARANDU APLICADO COM SUCESSO" -ForegroundColor Green
 Write-Host "Contato assistido + visual assistido" -ForegroundColor Green
 Write-Host "Repeticoes + estatistica + validacao" -ForegroundColor Green
 Write-Host "Metodologia + formulas + limitacoes + APA 7" -ForegroundColor Green
 Write-Host "REF-174 a REF-178 adicionadas" -ForegroundColor Green
 Write-Host "0 camadas alteradas | 0 indices recalculados" -ForegroundColor Green
 Write-Host "Backup  $Backup" -ForegroundColor DarkGray
}catch{
 Write-Host "Falha. Restaurando estado anterior." -ForegroundColor Red
 foreach($rel in $Touched){$src=Join-Path $Backup $rel;$dst=Join-Path $Root $rel;if(Test-Path $src){New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null;Copy-Item $src $dst -Force}}
 foreach($rel in $New){$p=Join-Path $Root $rel;if(Test-Path $p){Remove-Item $p -Force}}
 throw
}
