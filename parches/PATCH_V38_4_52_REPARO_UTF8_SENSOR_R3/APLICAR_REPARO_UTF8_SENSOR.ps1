$ErrorActionPreference = 'Stop'
Write-Host 'ITA ARANDU MS - REPARO UTF8 + PONTE SENSOR - R3' -ForegroundColor Cyan

$patchDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$candidates = @(
  (Join-Path $patchDir '..\..\docs'),
  (Join-Path $patchDir '..\docs'),
  (Join-Path (Get-Location) 'docs'),
  (Get-Location).Path
)

$docs = $null
foreach($c in $candidates){
  try {
    $r = (Resolve-Path $c -ErrorAction Stop).Path
    if((Test-Path (Join-Path $r 'index.html')) -and (Test-Path (Join-Path $r 'assets\js\magnetometro-amostras-v38450.js'))){
      $docs = $r
      break
    }
  } catch {}
}
if(-not $docs){
  throw 'Nao foi encontrada a pasta docs do ITA ARANDU MS. Mantenha este patch dentro de atlas-geocientifico-ms\parches.'
}
Write-Host "Raiz detectada: $docs" -ForegroundColor Green

$payloadIndex = Join-Path $patchDir 'payload\index.html'
$payloadSW = Join-Path $patchDir 'payload\service-worker.js'
$payloadSample = Join-Path $patchDir 'payload\assets\js\magnetometro-amostras-v38450.js'
$payloadMap = Join-Path $patchDir 'payload\assets\js\magnetometro-mapa-v38451.js'
foreach($p in @($payloadIndex,$payloadSW,$payloadSample,$payloadMap)){
  if(-not (Test-Path $p)){throw "Patch incompleto: $p"}
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$repoRoot = Split-Path $docs -Parent
$backup = Join-Path $repoRoot "parches\_backups\REPARO_UTF8_SENSOR_R3_$stamp"
New-Item -ItemType Directory -Force -Path (Join-Path $backup 'assets\js') | Out-Null
Copy-Item (Join-Path $docs 'index.html') (Join-Path $backup 'index.html') -Force
if(Test-Path (Join-Path $docs 'service-worker.js')){Copy-Item (Join-Path $docs 'service-worker.js') (Join-Path $backup 'service-worker.js') -Force}
Copy-Item (Join-Path $docs 'assets\js\magnetometro-amostras-v38450.js') (Join-Path $backup 'assets\js\magnetometro-amostras-v38450.js') -Force
if(Test-Path (Join-Path $docs 'assets\js\magnetometro-mapa-v38451.js')){Copy-Item (Join-Path $docs 'assets\js\magnetometro-mapa-v38451.js') (Join-Path $backup 'assets\js\magnetometro-mapa-v38451.js') -Force}

# Importante: copia binaria directa. No usa Get-Content/Set-Content y por eso no recodifica UTF-8.
Copy-Item $payloadIndex (Join-Path $docs 'index.html') -Force
Copy-Item $payloadSW (Join-Path $docs 'service-worker.js') -Force
Copy-Item $payloadSample (Join-Path $docs 'assets\js\magnetometro-amostras-v38450.js') -Force
Copy-Item $payloadMap (Join-Path $docs 'assets\js\magnetometro-mapa-v38451.js') -Force

if(-not (Select-String -Path (Join-Path $docs 'assets\js\magnetometro-amostras-v38450.js') -Pattern 'ItaSensors' -SimpleMatch -Quiet)){
  throw 'Falha: ItaSensors nao foi encontrado no Magnetometro Amostras.'
}
if(-not (Select-String -Path (Join-Path $docs 'assets\js\magnetometro-mapa-v38451.js') -Pattern 'ItaSensors' -SimpleMatch -Quiet)){
  throw 'Falha: ItaSensors nao foi encontrado no Magnetometro Mapa.'
}
Write-Host 'OK - UTF-8 restaurado sem recodificacao.' -ForegroundColor Green
Write-Host 'OK - Ponte ItaSensors preservada em Amostras e Mapa.' -ForegroundColor Green
Write-Host "Backup: $backup" -ForegroundColor DarkGray
Write-Host 'Depois de publicar no GitHub Pages, feche todas as abas antigas e limpe/recarregue a PWA se o cache mantiver a versao anterior.' -ForegroundColor Yellow
Write-Host 'Observacao: Chrome continua sem acesso nativo ao magnetometro. X/Y/Z em uT via ItaSensors exigem o app Android nativo.' -ForegroundColor Yellow
