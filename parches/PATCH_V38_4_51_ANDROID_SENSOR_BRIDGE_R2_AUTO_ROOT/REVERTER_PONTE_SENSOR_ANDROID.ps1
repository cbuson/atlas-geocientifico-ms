$ErrorActionPreference='Stop'
$patchDir=Split-Path -Parent $MyInvocation.MyCommand.Path
$stateFile=Join-Path $patchDir 'ULTIMA_INSTALACAO.json'
if(-not (Test-Path $stateFile)){throw 'Nao existe registro de instalacao deste patch.'}
$s=Get-Content $stateFile -Raw | ConvertFrom-Json
$docs=$s.docs;$backup=$s.backup
if(-not (Test-Path $backup)){throw "Backup nao encontrado · $backup"}
Copy-Item (Join-Path $backup 'assets\js\magnetometro-amostras-v38450.js') (Join-Path $docs 'assets\js\magnetometro-amostras-v38450.js') -Force
if($s.map_modified -and (Test-Path (Join-Path $backup 'assets\js\magnetometro-mapa-v38451.js'))){Copy-Item (Join-Path $backup 'assets\js\magnetometro-mapa-v38451.js') (Join-Path $docs 'assets\js\magnetometro-mapa-v38451.js') -Force}
Copy-Item (Join-Path $backup 'index.html') (Join-Path $docs 'index.html') -Force
if(Test-Path (Join-Path $backup 'service-worker.js')){Copy-Item (Join-Path $backup 'service-worker.js') (Join-Path $docs 'service-worker.js') -Force}
Write-Host 'OK · Ponte nativa revertida para o backup anterior.' -ForegroundColor Green
