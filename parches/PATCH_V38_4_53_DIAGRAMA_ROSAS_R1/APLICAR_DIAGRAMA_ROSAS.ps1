$ErrorActionPreference = "Stop"
Write-Host "ITA ARANDU MS - PATCH DIAGRAMA DE ROSAS - R1" -ForegroundColor Cyan
Write-Host "Instalador seguro. Nao regrava HTML como texto. Copia arquivos validados byte a byte." -ForegroundColor Cyan
$patchDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $patchDir "..\.." )).Path
$docs = Join-Path $repoRoot "docs"
if (!(Test-Path (Join-Path $docs "index.html"))) { throw "Raiz docs nao encontrada em $docs" }
Write-Host "Raiz detectada: $docs" -ForegroundColor Green
$expected = @{
  "index.html" = "b6a5df2a9b973aea29db1d431ba17fdc86e844e37b14fb07a9c83f648e2a44ec"
  "referencias/referencias.js" = "cae246fe3d074eccd6c5f8e84c38e731385c9618a1f5e53502fb7db4d5d132eb"
  "service-worker.js" = "5f27e25ced7dbe9b65f2a734ae3af85b1f79abe121a7d1d1b1fe6a804c93a3bf"
}
foreach($rel in $expected.Keys){
  $target = Join-Path $docs $rel
  if(!(Test-Path $target)){ throw "Arquivo base ausente: $rel" }
  $actual = (Get-FileHash -Algorithm SHA256 $target).Hash.ToLower()
  if($actual -ne $expected[$rel]){
    Write-Host "BASE NAO COINCIDE. NENHUM ARQUIVO FOI ALTERADO." -ForegroundColor Red
    Write-Host "$rel atual: $actual" -ForegroundColor Yellow
    Write-Host "$rel esperado: $($expected[$rel])" -ForegroundColor Yellow
    throw "Interrompido por seguranca. Este patch exige a base V38.4.53 resultante do patch Ondas Sismicas." 
  }
}
Write-Host "Base V38.4.53 validada." -ForegroundColor Green
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $repoRoot ("backup_PATCH_ROSAS_"+$stamp)
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$files = @(
  "index.html",
  "referencias/referencias.js",
  "service-worker.js",
  "assets/css/diagrama-rosas-v38454.css",
  "assets/js/diagrama-rosas-v38454.js",
  "documentos/metodologia-diagrama-rosas.html",
  "documentos/CHANGELOG_V38_4_54.md"
)
foreach($rel in $files){
  $target = Join-Path $docs $rel
  if(Test-Path $target){
    $b = Join-Path $backup $rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $b) | Out-Null
    [System.IO.File]::Copy($target,$b,$true)
  }
}
foreach($rel in $files){
  $src = Join-Path (Join-Path $patchDir "payload") $rel
  if(!(Test-Path $src)){ throw "Payload ausente: $rel" }
  $dst = Join-Path $docs $rel
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
  [System.IO.File]::Copy($src,$dst,$true)
}
$payloadExpected = @{
  "index.html" = "c05d400a061a904252f48720c6318b9d072ef98e5947bc9bbdfd95686580293d"
  "referencias/referencias.js" = "d99b77ca6cd0b268ef565b6bc9cfe8c552ef91d5179d57775d057d0d08c04d76"
  "service-worker.js" = "5ca7993a9feb4bb0b0b7f795daf90d7b4450d2e73984de4f5450ab0334384963"
  "assets/css/diagrama-rosas-v38454.css" = "df59649d860946326a8969f5b8b158b8c1b297f256cefa392004214350694d0c"
  "assets/js/diagrama-rosas-v38454.js" = "7332c3c79429ccd983e16dc53c481e957a0f0038d13176939985188683fa0b56"
  "documentos/metodologia-diagrama-rosas.html" = "53f2aec944a691da89fd5eaacea7328283d6086d481e679ebd202860df5bd480"
  "documentos/CHANGELOG_V38_4_54.md" = "167b727cdcbde1ebc16bf8c653219120296e447867515915f6b08703c85ee301"
}
foreach($rel in $payloadExpected.Keys){
  $target = Join-Path $docs $rel
  $actual = (Get-FileHash -Algorithm SHA256 $target).Hash.ToLower()
  if($actual -ne $payloadExpected[$rel]){ throw "Falha de verificacao pos-instalacao: $rel" }
}
Write-Host "OK - Diagrama de Rosas instalado - V38.4.54" -ForegroundColor Green
Write-Host "OK - Ajuda, metodologia, limitacoes e referencias APA 7 integradas." -ForegroundColor Green
Write-Host "OK - REF-226 a REF-230 incorporadas na biblioteca geral." -ForegroundColor Green
Write-Host "OK - Tema claro permanece padrao. Modo escuro nao e ativado automaticamente." -ForegroundColor Green
Write-Host "Backup: $backup" -ForegroundColor Yellow
