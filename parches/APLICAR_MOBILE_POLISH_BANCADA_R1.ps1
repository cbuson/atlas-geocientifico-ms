$ErrorActionPreference='Stop'
Write-Host 'ITA ARANDU MS - MOBILE POLISH BANCADA - R1' -ForegroundColor Cyan

function Find-Root {
 $p=[IO.Path]::GetFullPath($PSScriptRoot)
 for($i=0;$i -lt 8;$i++){if(Test-Path (Join-Path $p 'docs\index.html')){return $p};$q=Split-Path $p -Parent;if(!$q -or $q -eq $p){break};$p=$q}
 throw 'Raiz do repositorio nao encontrada.'
}

function Insert-Before([string]$path,[string]$anchor,[string]$insert){
 $raw=[IO.File]::ReadAllText($path,[Text.Encoding]::UTF8)
 if($raw.Contains($insert)){return}
 $p=$raw.IndexOf($anchor,[StringComparison]::OrdinalIgnoreCase)
 if($p -lt 0){throw "Ancora $anchor nao encontrada."}
 $fixed=$raw.Insert($p,$insert)
 [IO.File]::WriteAllText($path,$fixed,(New-Object Text.UTF8Encoding($false)))
}

$root=Find-Root
$docs=Join-Path $root 'docs'
$index=Join-Path $docs 'index.html'
$dest=Join-Path (Join-Path (Join-Path $docs 'assets') 'css') 'mobile-polish-bancada-r1.css'
$src=Join-Path (Join-Path (Join-Path $PSScriptRoot 'payload') 'assets\css') 'mobile-polish-bancada-r1.css'

if(!(Test-Path $index)){throw 'index.html nao encontrado.'}
if(!(Test-Path $src)){throw 'CSS do patch nao encontrado.'}

$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
Copy-Item $index ($index+'.antes_mobile_polish_'+$stamp) -Force
Copy-Item $src $dest -Force

$link=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PGxpbmsgcmVsPSJzdHlsZXNoZWV0IiBocmVmPSIuL2Fzc2V0cy9jc3MvbW9iaWxlLXBvbGlzaC1iYW5jYWRhLXIxLmNzcz92PTEuMC4wIj4='))
Insert-Before $index '</head>' $link

$raw=[IO.File]::ReadAllText($index,[Text.Encoding]::UTF8)
if(-not $raw.Contains('mobile-polish-bancada-r1.css')){throw 'Falha ao vincular o CSS no index.'}

Write-Host 'OK - tipografia mobile da Coluna normalizada.' -ForegroundColor Green
Write-Host 'OK - abas, botoes, cards, escala e estatisticas reduzidos para celular.' -ForegroundColor Green
Write-Host 'OK - GeoCamera passa a ocupar integralmente a area visual sem faixa preta.' -ForegroundColor Green
Write-Host 'OK - video e canvas usam object-fit cover com altura mobile controlada.' -ForegroundColor Green
Write-Host 'OK - nenhum conteudo cientifico, GPS, padrao FGDC ou autoria foi alterado.' -ForegroundColor Green
Write-Host 'OK - index.html recebeu somente um link CSS incremental.' -ForegroundColor Green
Write-Host ''
Write-Host 'Depois feche a aba e abra novamente o site. Em GitHub Pages pode ser necessario aguardar a publicacao.' -ForegroundColor Yellow
