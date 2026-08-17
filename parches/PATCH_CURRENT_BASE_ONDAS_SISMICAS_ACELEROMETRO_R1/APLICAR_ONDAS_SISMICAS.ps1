$ErrorActionPreference = 'Stop'
Write-Host 'ITA ARANDU MS - PATCH ONDAS SISMICAS - R1' -ForegroundColor Cyan
$patchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Resolve-Path (Join-Path $patchRoot '..\..')
$docs = Join-Path $repo 'docs'
if (!(Test-Path $docs)) { throw 'Pasta docs nao encontrada.' }
Write-Host ('Raiz detectada: ' + $docs) -ForegroundColor Green
$expected = @{
  'index.html'='ae44addaa69746bfbd93800a691cd5547a71fd3c333fa0c6c25e07360a33699a'
  'service-worker.js'='694eb237ee51f4fad14f9ad659193dc8ab6375d236f979127914120aabdd6ada'
  'referencias/referencias.js'='2a7e691e3250c4a54b99988d46274bf797a19bc3c833cc01b5dae68a6d3840ba'
}
foreach($rel in $expected.Keys){
  $target=Join-Path $docs $rel
  if(!(Test-Path $target)){ throw ('Arquivo base ausente: '+$rel) }
  $hash=(Get-FileHash -Algorithm SHA256 $target).Hash.ToLower()
  if($hash -ne $expected[$rel]){
    Write-Host ('NAO COINCIDE: '+$rel) -ForegroundColor Red
    Write-Host ('atual: '+$hash) -ForegroundColor DarkGray
    throw 'Base diferente do ZIP atual fornecido. Nenhum arquivo foi alterado.'
  }
}
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$backup=Join-Path $repo ('backup_ondas_sismicas_'+$stamp)
New-Item -ItemType Directory -Path $backup -Force | Out-Null
foreach($rel in $expected.Keys){
  $src=Join-Path $docs $rel
  $dst=Join-Path $backup $rel
  New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Force
}
$files=Join-Path $patchRoot 'files'
Get-ChildItem -Path $files -File -Recurse | ForEach-Object {
  $rel=$_.FullName.Substring($files.Length).TrimStart('\','/')
  $dst=Join-Path $docs $rel
  New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
  [System.IO.File]::WriteAllBytes($dst,[System.IO.File]::ReadAllBytes($_.FullName))
}
# UTF-8 strict validation, read only
$utf8 = New-Object System.Text.UTF8Encoding($false,$true)
foreach($rel in @('index.html','referencias/referencias.js','documentos/metodologia-ondas-sismicas-acelerometro.html')){
  $bytes=[System.IO.File]::ReadAllBytes((Join-Path $docs $rel))
  [void]$utf8.GetString($bytes)
}
Write-Host 'OK - Ondas sismicas instaladas sem recodificar HTML.' -ForegroundColor Green
Write-Host ('Backup: '+$backup) -ForegroundColor Green
Write-Host 'Nova ferramenta: Bancada Digital > Geofisica experimental > Ondas sismicas - Acelerometro' -ForegroundColor Cyan
