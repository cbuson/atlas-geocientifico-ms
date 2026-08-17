$ErrorActionPreference = 'Stop'
Write-Host 'ITA ARANDU MS - PATCH PONTE NATIVA ANDROID - R2' -ForegroundColor Cyan

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
    $sampleCandidate = Join-Path $r 'assets\js\magnetometro-amostras-v38450.js'
    if((Test-Path (Join-Path $r 'index.html')) -and (Test-Path $sampleCandidate)){
      $docs = $r
      break
    }
  } catch {}
}

if(-not $docs){
  throw 'Nao foi encontrada a pasta docs do ITA ARANDU MS. Mantenha este patch dentro de atlas-geocientifico-ms\parches.'
}
Write-Host "Raiz detectada: $docs" -ForegroundColor Green

$sample = Join-Path $docs 'assets\js\magnetometro-amostras-v38450.js'
$map = Join-Path $docs 'assets\js\magnetometro-mapa-v38451.js'
$index = Join-Path $docs 'index.html'
$sw = Join-Path $docs 'service-worker.js'

# Validacao propositalmente sem acentos para funcionar de forma confiavel no Windows PowerShell 5.1.
if(-not (Select-String -Path $sample -Pattern 'magAmostrasModal' -SimpleMatch -Quiet)){
  throw 'Base incompatível: arquivo do Magnetometro Amostras existe, mas nao contem o identificador esperado magAmostrasModal.'
}

$hasMap = $false
if(Test-Path $map){
  if(Select-String -Path $map -Pattern 'magMapaModal' -SimpleMatch -Quiet){
    $hasMap = $true
  } else {
    Write-Host 'Aviso: Magnetometro Mapa encontrado, mas nao reconhecido. Ele nao sera alterado.' -ForegroundColor Yellow
  }
}

$payloadSample = Join-Path $patchDir 'payload\assets\js\magnetometro-amostras-v38450.js'
$payloadMap = Join-Path $patchDir 'payload\assets\js\magnetometro-mapa-v38451.js'
$payloadChangelog = Join-Path $patchDir 'payload\documentos\CHANGELOG_V38_4_52.md'
foreach($required in @($payloadSample,$payloadChangelog)){
  if(-not (Test-Path $required)){throw "Patch incompleto: arquivo ausente $required"}
}
if($hasMap -and -not (Test-Path $payloadMap)){throw 'Patch incompleto: payload do Magnetometro Mapa ausente.'}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$repoRoot = Split-Path $docs -Parent
$backup = Join-Path $repoRoot "parches\_backups\ANDROID_SENSOR_BRIDGE_$stamp"
New-Item -ItemType Directory -Force -Path (Join-Path $backup 'assets\js') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $backup 'documentos') | Out-Null
Copy-Item $sample (Join-Path $backup 'assets\js\magnetometro-amostras-v38450.js')
if($hasMap){Copy-Item $map (Join-Path $backup 'assets\js\magnetometro-mapa-v38451.js')}
Copy-Item $index (Join-Path $backup 'index.html')
if(Test-Path $sw){Copy-Item $sw (Join-Path $backup 'service-worker.js')}

Copy-Item $payloadSample $sample -Force
if($hasMap){Copy-Item $payloadMap $map -Force}
Copy-Item $payloadChangelog (Join-Path $docs 'documentos\CHANGELOG_V38_4_52.md') -Force

$txt = Get-Content $index -Raw
$txt = $txt -replace 'magnetometro-amostras-v38450\.js\?v=38\.4\.(49|50|51)', 'magnetometro-amostras-v38450.js?v=38.4.52'
$txt = $txt -replace 'magnetometro-mapa-v38451\.js\?v=38\.4\.51', 'magnetometro-mapa-v38451.js?v=38.4.52'
Set-Content -Path $index -Value $txt -Encoding UTF8

if(Test-Path $sw){
  $swtxt = Get-Content $sw -Raw
  $swtxt = $swtxt -replace "ita-arandu-v38-4-[^']+", 'ita-arandu-v38-4-52-android-native-sensors'
  $swtxt = $swtxt -replace 'magnetometro-amostras-v38450\.js\?v=38\.4\.(49|50|51)', 'magnetometro-amostras-v38450.js?v=38.4.52'
  $swtxt = $swtxt -replace 'magnetometro-mapa-v38451\.js\?v=38\.4\.51', 'magnetometro-mapa-v38451.js?v=38.4.52'
  Set-Content -Path $sw -Value $swtxt -Encoding UTF8
}

# Verificacao pos-instalacao.
if(-not (Select-String -Path $sample -Pattern 'ItaSensors' -SimpleMatch -Quiet)){
  throw 'Falha de verificacao: a ponte ItaSensors nao apareceu no Magnetometro Amostras.'
}
if($hasMap -and -not (Select-String -Path $map -Pattern 'ItaSensors' -SimpleMatch -Quiet)){
  throw 'Falha de verificacao: a ponte ItaSensors nao apareceu no Magnetometro Mapa.'
}

$state = @{
  docs=$docs
  backup=$backup
  installed=(Get-Date).ToString('o')
  map_modified=$hasMap
  patch='R2'
} | ConvertTo-Json
Set-Content -Path (Join-Path $patchDir 'ULTIMA_INSTALACAO.json') -Value $state -Encoding UTF8

Write-Host 'OK - Ponte web para sensor nativo Android instalada - V38.4.52' -ForegroundColor Green
Write-Host 'OK - Magnetometro Amostras preparado para ItaSensors.' -ForegroundColor Green
if($hasMap){Write-Host 'OK - Magnetometro Mapa preparado para ItaSensors.' -ForegroundColor Green}
else{Write-Host 'Magnetometro Mapa nao reconhecido ou nao presente. Nenhuma alteracao feita nele.' -ForegroundColor Yellow}
Write-Host "Backup: $backup" -ForegroundColor DarkGray
Write-Host 'No Chrome comum, a API Web continua sendo usada quando disponivel. O acesso nativo em uT exige o aplicativo Android ITA ARANDU.' -ForegroundColor Yellow
