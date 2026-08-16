param(
  [string]$Repo="C:\Users\cbuso\Documents\GitHub\atlas-geocientifico-ms"
)

$ErrorActionPreference="Stop"
$Root=(Resolve-Path $Repo).Path
$Expected="V38.4.37-ESTEREOGRAMA-CALCULADORA-1.0-20260815"

Write-Host ""
Write-Host "ITA ARANDU MS  RECAPTURA V38.4.37 PARA GEOCAMERA + MACROGEO" -ForegroundColor Cyan
Write-Host "Repositorio  $Root"

$VersionPath=Join-Path $Root "VERSION"
if(!(Test-Path $VersionPath)){throw "VERSION nao encontrado"}
$Current=(Get-Content $VersionPath -Raw).Trim()

Write-Host "Versao       $Current"
if($Current -ne $Expected){
  throw "Base inesperada. Esperada $Expected"
}

$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Work=Join-Path $env:TEMP ("ITA_ARANDU_RECAPTURA_V38437_"+$Stamp)
$Payload=Join-Path $Work "payload"
New-Item -ItemType Directory -Path $Payload -Force | Out-Null

$Files=@(
  "VERSION",
  "docs\index.html",
  "docs\service-worker.js",
  "docs\manifest.webmanifest",
  "docs\referencias\index.html",
  "docs\camadas\catalogo-local.json",
  "docs\camadas\snapshots-manifest.json",
  "docs\assets\js\campo-master-v38431.js",
  "docs\assets\js\campo-ux-v38432.js",
  "docs\assets\js\clinometro-visual-v38433.js",
  "docs\assets\js\geoetica-care-v38434.js",
  "docs\assets\js\ferramentas-hub-v38435.js",
  "docs\assets\js\bussola-nivel-v38436.js",
  "docs\assets\js\estereograma-calculadora-v38437.js",
  "docs\assets\css\clinometro-visual-v38433.css",
  "docs\assets\css\geoetica-care-v38434.css",
  "docs\assets\css\ferramentas-hub-v38435.css",
  "docs\assets\css\bussola-nivel-v38436.css",
  "docs\assets\css\estereograma-calculadora-v38437.css",
  "docs\documentos\metodologia-ferramentas-geocientificas.html",
  "docs\documentos\metodologia-clinometro-visual-arandu.html",
  "docs\documentos\metodologia-bussola-geologica.html",
  "docs\documentos\metodologia-nivel-digital.html",
  "docs\documentos\metodologia-estereograma-arandu.html",
  "docs\documentos\metodologia-calculadora-estrutural.html",
  "docs\documentos\protocolo-geoetica.html",
  "docs\documentos\protocolo-care-camada-ancestral.html",
  "docs\documentos\politica-geoetica-care.json",
  "CHANGELOG.md"
)

$Copied=@()
$Missing=@()

foreach($rel in $Files){
  $src=Join-Path $Root $rel
  if(Test-Path $src){
    $dst=Join-Path $Payload $rel
    New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
    Copy-Item $src $dst -Force
    $Copied += $rel
  }else{
    $Missing += $rel
  }
}

# Inventario estrutural sem copiar dados pesados
$Inventory=@()
Get-ChildItem (Join-Path $Root "docs") -Recurse -File | ForEach-Object {
  $rel=$_.FullName.Substring($Root.Length+1)
  $Inventory += [pscustomobject]@{
    path=$rel
    bytes=$_.Length
    modified=$_.LastWriteTime.ToString("s")
    extension=$_.Extension
  }
}
$Inventory | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Work "INVENTARIO_DOCS.json") -Encoding UTF8

# IDs importantes do index para auditoria de arquitetura
$IndexPath=Join-Path $Root "docs\index.html"
$Ids=@()
if(Test-Path $IndexPath){
  $raw=Get-Content $IndexPath -Raw
  [regex]::Matches($raw,'\bid=["'']([^"'']+)["'']') | ForEach-Object {
    $Ids += $_.Groups[1].Value
  }
}
$Ids | Sort-Object -Unique | Set-Content (Join-Path $Work "IDS_INDEX.txt") -Encoding UTF8

# Lista de scripts e estilos carregados pelo index
$Resources=@()
if(Test-Path $IndexPath){
  $raw=Get-Content $IndexPath -Raw
  [regex]::Matches($raw,'(?:src|href)=["'']([^"'']+\.(?:js|css)(?:\?[^"'']*)?)["'']') | ForEach-Object {
    $Resources += $_.Groups[1].Value
  }
}
$Resources | Sort-Object -Unique | Set-Content (Join-Path $Work "RECURSOS_INDEX.txt") -Encoding UTF8

# SHA256 dos arquivos copiados
$Hashes=@()
foreach($rel in $Copied){
  $p=Join-Path $Root $rel
  $h=(Get-FileHash -Algorithm SHA256 $p).Hash.ToLower()
  $Hashes += [pscustomobject]@{path=$rel;sha256=$h}
}
$Hashes | ConvertTo-Json -Depth 3 | Set-Content (Join-Path $Work "SHA256_ESTRUTURA.json") -Encoding UTF8

$Summary=[ordered]@{
  produto="ITA ARANDU MS recaptura estrutural V38.4.37 para GeoCamera + MacroGeo"
  executado_em=(Get-Date).ToString("o")
  repositorio=$Root
  versao=$Current
  arquivos_copiados=$Copied.Count
  arquivos_ausentes=$Missing.Count
  ausentes=$Missing
  regra="Somente estrutura da aplicacao. Nao copia GeoJSON das camadas nem snapshots pesados."
  objetivo="Permitir construir V38.4.38 GeoCamera ARANDU + MacroGeo sobre a instalacao real."
}
$Summary | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Work "RESUMO_RECAPTURA_V38437.json") -Encoding UTF8

$Zip=Join-Path $Root ("parches\ITA_ARANDU_MS_RECAPTURA_V38_4_37_GEOCAMERA_"+$Stamp+".zip")
if(Test-Path $Zip){Remove-Item $Zip -Force}
Compress-Archive -Path (Join-Path $Work "*") -DestinationPath $Zip -CompressionLevel Optimal

Write-Host ""
Write-Host "RECAPTURA CONCLUIDA" -ForegroundColor Green
Write-Host "Arquivos copiados  $($Copied.Count)" -ForegroundColor Green
Write-Host "Arquivos ausentes  $($Missing.Count)" -ForegroundColor $(if($Missing.Count -eq 0){"Green"}else{"Yellow"})
Write-Host ""
Write-Host "ZIP GERADO" -ForegroundColor Cyan
Write-Host $Zip
Write-Host ""
Write-Host "Envie esse ZIP ao ChatGPT." -ForegroundColor Yellow
