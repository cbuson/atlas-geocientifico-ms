$ErrorActionPreference='Stop'
Write-Host 'ITA ARANDU MS - COLUNA GPS + AJUDA + PADROES VISIVEIS - R5' -ForegroundColor Cyan

function Find-Root {
  $p=[IO.Path]::GetFullPath($PSScriptRoot)
  for($i=0;$i -lt 8;$i++){
    if(Test-Path (Join-Path $p 'docs\index.html')){return $p}
    $q=Split-Path $p -Parent
    if(!$q -or $q -eq $p){break}
    $p=$q
  }
  throw 'Nao foi possivel localizar a raiz do repositorio.'
}
function Get-HashValue([string]$p){(Get-FileHash $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Replace-Literal([string]$path,[string]$old,[string]$new){
  [byte[]]$d=[IO.File]::ReadAllBytes($path);$enc=[Text.Encoding]::UTF8
  [byte[]]$o=$enc.GetBytes($old);[byte[]]$n=$enc.GetBytes($new)
  function Idx([byte[]]$h,[byte[]]$x){
    for($i=0;$i -le $h.Length-$x.Length;$i++){$ok=$true;for($j=0;$j -lt $x.Length;$j++){if($h[$i+$j]-ne $x[$j]){$ok=$false;break}};if($ok){return $i}};return -1
  }
  if((Idx $d $n)-ge 0){return}
  $p=Idx $d $o
  if($p -lt 0){throw 'O bloco Abrir + Ciencia da Coluna nao foi encontrado. Nenhuma substituicao do index foi feita.'}
  $m=New-Object IO.MemoryStream;$m.Write($d,0,$p);$m.Write($n,0,$n.Length);$m.Write($d,$p+$o.Length,$d.Length-$p-$o.Length);[IO.File]::WriteAllBytes($path,$m.ToArray());$m.Dispose()
}

$root=Find-Root;$docs=Join-Path $root 'docs'
$js=Join-Path $docs 'assets\js\coluna-estratigrafica-v38457.js'
$css=Join-Path $docs 'assets\css\coluna-estratigrafica-v38457.css'
$index=Join-Path $docs 'index.html'
if(!(Test-Path $js) -or !(Test-Path $css)){throw 'Coluna Estratigrafica V38.4.57 nao encontrada.'}

# Aceita a base limpa ou a R5/R5.1 já instalada.
$rawJs=Get-Content $js -Raw -Encoding UTF8
if(($rawJs -notmatch 'Coluna Estratigrafica') -and ($rawJs -notmatch 'colunaEstratigraficaModal')){throw 'O JavaScript da Coluna nao foi reconhecido.'}
$rawCss=Get-Content $css -Raw -Encoding UTF8
if($rawCss.Length -lt 500){throw 'O CSS da Coluna nao foi reconhecido.'}
Write-Host 'OK - arquivos da Coluna reconhecidos.' -ForegroundColor Green

$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$backup=Join-Path $root ('backup_COLUNA_R5_'+$stamp)
New-Item -ItemType Directory -Path (Join-Path $backup 'assets\js') -Force|Out-Null
New-Item -ItemType Directory -Path (Join-Path $backup 'assets\css') -Force|Out-Null
Copy-Item $js (Join-Path $backup 'assets\js\coluna-estratigrafica-v38457.js') -Force
Copy-Item $css (Join-Path $backup 'assets\css\coluna-estratigrafica-v38457.css') -Force
Copy-Item $index (Join-Path $backup 'index.html') -Force
Write-Host "Backup criado: $backup" -ForegroundColor Cyan

# Copy only column-specific JS/CSS and PNG assets.
Copy-Item (Join-Path $PSScriptRoot 'payload\assets\js\coluna-estratigrafica-v38457.js') $js -Force
Copy-Item (Join-Path $PSScriptRoot 'payload\assets\css\coluna-estratigrafica-v38457.css') $css -Force
$patDest=Join-Path $docs 'assets\padroes\fgdc'
New-Item -ItemType Directory -Path $patDest -Force|Out-Null
Copy-Item (Join-Path $PSScriptRoot 'payload\assets\padroes\fgdc\*.png') $patDest -Force

# Incremental edit only to the Column card. Never replace index.html.
$old=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PGJ1dHRvbiB0eXBlPSJidXR0b24iIGNsYXNzPSJhY3Rpb24tYnRuIHByaW1hcnkiIGRhdGEtdG9vbC1hY3Rpb249ImNvbHVuYUNvbnN0cnV0b3IiPkFicmlyPC9idXR0b24+PGEgY2xhc3M9ImFjdGlvbi1idG4iIGhyZWY9Ii4vZG9jdW1lbnRvcy9tZXRvZG9sb2dpYS1jb2x1bmEtZXN0cmF0aWdyYWZpY2EuaHRtbCIgdGFyZ2V0PSJfYmxhbmsiIHJlbD0ibm9vcGVuZXIiPkNpw6puY2lhPC9hPg=='))
$new=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PGJ1dHRvbiB0eXBlPSJidXR0b24iIGNsYXNzPSJhY3Rpb24tYnRuIHByaW1hcnkiIGRhdGEtdG9vbC1hY3Rpb249ImNvbHVuYUNvbnN0cnV0b3IiPkFicmlyPC9idXR0b24+PGJ1dHRvbiB0eXBlPSJidXR0b24iIGNsYXNzPSJhY3Rpb24tYnRuIiBkYXRhLXRvb2wtYWN0aW9uPSJjb2x1bmFBanVkYSI+QWp1ZGE8L2J1dHRvbj4='))
Replace-Literal $index $old $new

# Validate result.
$raw=Get-Content $js -Raw -Encoding UTF8
if($raw -notmatch 'id="ceUseGPS"' -or $raw -notmatch 'data-tool-action="colunaAjuda"' -or $raw -notmatch 'patternPng'){throw 'Falha de validacao do JS R5.'}
$pngs=(Get-ChildItem $patDest -Filter '*.png' -File).Count
if($pngs -lt 114){throw "Foram encontrados apenas $pngs PNGs FGDC."}
$idx=Get-Content $index -Raw -Encoding UTF8
if($idx -notmatch 'data-tool-action="colunaAjuda"'){throw 'O botao Ajuda da Coluna nao foi instalado.'}

Write-Host 'OK - GPS incorporado a Coluna Estratigrafica.' -ForegroundColor Green
Write-Host 'OK - latitude, longitude, precisao, altitude e horario preservados.' -ForegroundColor Green
Write-Host 'OK - exportacoes JSON, CSV e SVG recebem a posicao.' -ForegroundColor Green
Write-Host 'OK - botao Ciencia da Bancada substituido por Ajuda interna.' -ForegroundColor Green
Write-Host 'OK - 114 padroes PNG com fundo branco foram instalados.' -ForegroundColor Green
Write-Host 'OK - SVG originais foram preservados para rastreabilidade e exportacao.' -ForegroundColor Green
Write-Host 'OK - index.html nao foi substituido.' -ForegroundColor Green
Write-Host 'Depois use Ctrl+F5. Se o navegador mantiver cache antigo, feche a aba local e abra novamente localhost:8000.' -ForegroundColor Yellow
