param(
  [Parameter(Mandatory=$true)][string]$Destino
)
$ErrorActionPreference = 'Stop'
$Esperada = 'V38.4.16-GATE-ICG-20260815'
$Final = 'V38.4.17-ICG-CONHECIMENTO-GEOCIENTIFICO-20260815'
$RaizPatch = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $RaizPatch 'payload'
$Destino = (Resolve-Path $Destino).Path
$VersionFile = Join-Path $Destino 'VERSION'
if (!(Test-Path $VersionFile)) { throw "VERSION nao encontrado em $Destino" }
$Atual = (Get-Content $VersionFile -Raw -Encoding UTF8).Trim()
if ($Atual -ne $Esperada) { throw "Base incorreta. Esperada $Esperada e encontrada $Atual" }
if (!(Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python launcher py nao encontrado.' }
if (!(Test-Path (Join-Path $Destino 'docs\indices\politica-icg-v38416.json'))) { throw 'Politica ICG V38.4.16 nao encontrada.' }
if (!(Test-Path (Join-Path $Destino 'AUDITORIA_V38_4_16_GATE_ICG_FINAL.json'))) { throw 'Auditoria final do gate ICG V38.4.16 nao encontrada.' }

Write-Host 'ITA ARANDU MS - PATCH V38.4.17 - ICG - CONHECIMENTO GEOCIENTIFICO' -ForegroundColor Cyan
Write-Host "Origem confirmada - $Atual"
Write-Host 'Escopo - materializacao ICG 250 / 500 / 1000 km2. Bases e IDE nao serao recalculados.'
Write-Host 'Regra - minimo 2 dimensoes observadas. null permanece null. IDE fica fora da formula.'

$Protegidos = @(
 'docs\indices\imc-v32.js','docs\indices\imc_v32_snapshot.json',
 'docs\indices\iod-v3848.js','docs\indices\iod_v3848_snapshot.json',
 'docs\indices\icp-v3849.js','docs\indices\icp_v3849_snapshot.json',
 'docs\indices\igc-v38410.js','docs\indices\igc_v38410_snapshot.json',
 'docs\indices\igq-v38411.js','docs\indices\igq_v38411_snapshot.json',
 'docs\indices\igf-v38412.js','docs\indices\igf_v38412_snapshot.json',
 'docs\indices\ics-v38413.js','docs\indices\ics_v38413_snapshot.json',
 'docs\indices\ide-v38415.js','docs\indices\ide_v38415_snapshot.json',
 'docs\indices\politica-icg-v38416.json',
 'docs\camadas\arquivos\malha_r5_250km2.geojson','docs\camadas\arquivos\malha_500km2.geojson','docs\camadas\arquivos\malha_1000km2.geojson'
)
foreach($rel in $Protegidos){ if(!(Test-Path (Join-Path $Destino $rel))){ throw "Arquivo protegido ausente - $rel" } }

$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Backup=Join-Path $env:TEMP "ITA_ARANDU_BACKUPS\V38_4_16_ANTES_ICG_$Stamp"
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
$Tocados = @(
 'VERSION','CHANGELOG.md','docs\assets\js\app.js','docs\assets\js\bootstrap.js','docs\index.html','docs\service-worker.js',
 'docs\camadas\catalogo-local.json','docs\camadas\catalogo-local.js','docs\referencias\bibliografia-camadas-indices.json','docs\referencias\index.html','docs\documentos\index.html',
 'docs\indices\icg_v38417_snapshot.json','docs\indices\icg-v38417.js','docs\documentos\metodologia-icg.html',
 'AUDITORIA_V38_4_17_ICG_RUNTIME.json','AUDITORIA_V38_4_17_ICG_FINAL.json','tools\materializar_icg_v38417.py','tools\auditar_icg_v38417.py'
)
$BackupRel = @($Tocados + $Protegidos | Select-Object -Unique)
foreach($rel in $BackupRel){
 $src=Join-Path $Destino $rel
 if(Test-Path $src){$dst=Join-Path $Backup $rel;New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent)|Out-Null;Copy-Item $src $dst -Force}
}

try {
 Write-Host '1 de 4 - Instalando motor reprodutivel do ICG...' -ForegroundColor Cyan
 New-Item -ItemType Directory -Force -Path (Join-Path $Destino 'tools') | Out-Null
 Copy-Item (Join-Path $Payload 'tools\materializar_icg_v38417.py') (Join-Path $Destino 'tools\materializar_icg_v38417.py') -Force
 Copy-Item (Join-Path $Payload 'tools\auditar_icg_v38417.py') (Join-Path $Destino 'tools\auditar_icg_v38417.py') -Force
 & py (Join-Path $Destino 'tools\materializar_icg_v38417.py') --self-test
 if($LASTEXITCODE -ne 0){throw "Self-test ICG terminou com codigo $LASTEXITCODE"}

 Write-Host '2 de 4 - Materializando ICG 250, 500 e 1000 km2...' -ForegroundColor Cyan
 & py (Join-Path $Destino 'tools\materializar_icg_v38417.py') --repo $Destino
 if($LASTEXITCODE -ne 0){throw "Materializador ICG terminou com codigo $LASTEXITCODE"}

 Write-Host '3 de 4 - Executando auditoria cientifica e de integracao...' -ForegroundColor Cyan
 if(Get-Command node -ErrorAction SilentlyContinue){
   & node --check (Join-Path $Destino 'docs\assets\js\app.js')
   if($LASTEXITCODE -ne 0){throw "node --check app.js terminou com codigo $LASTEXITCODE"}
 }
 & py (Join-Path $Destino 'tools\auditar_icg_v38417.py') --repo $Destino
 if($LASTEXITCODE -ne 0){throw "Auditoria ICG terminou com codigo $LASTEXITCODE"}

 Write-Host '4 de 4 - Confirmando versao e imutabilidade das bases...' -ForegroundColor Cyan
 $Depois=(Get-Content $VersionFile -Raw -Encoding UTF8).Trim()
 if($Depois -ne $Final){throw "Versao final inesperada - $Depois"}
 Write-Host ''
 Write-Host 'PATCH APLICADO COM SUCESSO' -ForegroundColor Green
 Write-Host "Versao final - $Final" -ForegroundColor Green
 Write-Host 'ICG 250 / 500 / 1000 km2 - MATERIALIZADO E AUDITADO' -ForegroundColor Green
 Write-Host 'Sete dimensoes base, IDE e tres malhas - INALTERADOS por SHA256' -ForegroundColor Green
 Write-Host 'null - preservado. n_obs menor que 2 permanece ICG null.' -ForegroundColor Green
 Write-Host 'Sensibilidade - alpha 0.5 / 1 / 2 - auditada' -ForegroundColor Green
 Write-Host 'IDE - preservado como indicador companheiro e fora da formula ICG' -ForegroundColor Green
 Write-Host 'VCG e PIG - continuam bloqueados ate regras proprias' -ForegroundColor Yellow
 Write-Host "Auditoria final - $(Join-Path $Destino 'AUDITORIA_V38_4_17_ICG_FINAL.json')"
 Write-Host "Metodologia - $(Join-Path $Destino 'docs\documentos\metodologia-icg.html')"
 Write-Host "Backup - $Backup"
 Write-Host ''
 Write-Host 'Proximo passo - gate proprio para VCG - Vazios de Conhecimento Geocientifico' -ForegroundColor Cyan
} catch {
 Write-Host ''
 Write-Host 'Falha detectada. Restaurando a V38.4.16...' -ForegroundColor Yellow
 foreach($rel in $BackupRel){
   $src=Join-Path $Backup $rel;$dst=Join-Path $Destino $rel
   if(Test-Path $src){New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent)|Out-Null;Copy-Item $src $dst -Force}
   elseif($Tocados -contains $rel){if(Test-Path $dst){Remove-Item $dst -Force}}
 }
 Write-Host "Restauracao concluida - $Backup" -ForegroundColor Yellow
 throw
}
