$ErrorActionPreference="Stop"
Write-Host "ITA ARANDU MS - MICRO PATCH VINCULO POS-DOUTORADO - R1" -ForegroundColor Cyan

function B64([string]$s){ return [Convert]::FromBase64String($s) }
function Find-RepoRoot{
  $starts=@($PSScriptRoot,(Get-Location).Path)
  foreach($s in $starts){
    $p=[System.IO.Path]::GetFullPath($s)
    for($i=0;$i -lt 8;$i++){
      if(Test-Path (Join-Path $p "docs\index.html")){ return $p }
      $parent=Split-Path $p -Parent
      if(!$parent -or $parent -eq $p){ break }
      $p=$parent
    }
  }
  throw "Nao foi possivel localizar docs\index.html."
}
function IndexOf-Bytes([byte[]]$hay,[byte[]]$needle,[int]$start=0){
  for($i=$start;$i -le $hay.Length-$needle.Length;$i++){
    $ok=$true
    for($j=0;$j -lt $needle.Length;$j++){ if($hay[$i+$j] -ne $needle[$j]){ $ok=$false; break } }
    if($ok){ return $i }
  }
  return -1
}
function Replace-Exact([string]$path,[byte[]]$old,[byte[]]$new){
  [byte[]]$data=[System.IO.File]::ReadAllBytes($path)
  $p=IndexOf-Bytes $data $old 0
  if($p -lt 0){ return $false }
  $out=New-Object System.IO.MemoryStream
  $out.Write($data,0,$p);$out.Write($new,0,$new.Length);$out.Write($data,$p+$old.Length,$data.Length-$p-$old.Length)
  [System.IO.File]::WriteAllBytes($path,$out.ToArray());$out.Dispose()
  return $true
}
function Insert-Before([string]$path,[byte[]]$anchor,[byte[]]$insert){
  [byte[]]$data=[System.IO.File]::ReadAllBytes($path)
  if((IndexOf-Bytes $data $insert 0) -ge 0){ return }
  $p=IndexOf-Bytes $data $anchor 0
  if($p -lt 0){ throw "Ancora da ficha Carlos nao encontrada." }
  $out=New-Object System.IO.MemoryStream
  $out.Write($data,0,$p);$out.Write($insert,0,$insert.Length);$out.Write($data,$p,$data.Length-$p)
  [System.IO.File]::WriteAllBytes($path,$out.ToArray());$out.Dispose()
}

$root=Find-RepoRoot
$docs=Join-Path $root "docs"
$index=Join-Path $docs "index.html"
$css=Join-Path $docs "assets\css\atlas.css"
Write-Host "Raiz detectada: $root" -ForegroundColor Green

$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$backup=Join-Path $root ("backup_VINCULO_POSDOC_"+$stamp)
New-Item -ItemType Directory -Path (Join-Path $backup "assets\css") -Force | Out-Null
Copy-Item $index (Join-Path $backup "index.html") -Force
Copy-Item $css (Join-Path $backup "assets\css\atlas.css") -Force
Write-Host "Backup criado: $backup"

$old1=B64("Q29uY2Vww6fDo28gZG8gcHJvamV0bywgYXJxdWl0ZXR1cmEgY2llbnTDrWZpY2EgZSBkaWdpdGFsLCBpbnRlZ3Jhw6fDo28gdGVycml0b3JpYWwsIGRlc2VuaG8gZG8gc2lzdGVtYSBtdWx0aWVzY2FsYXIsIGRvY3VtZW50YcOnw6NvIGUgZGVzZW52b2x2aW1lbnRvIG1ldG9kb2zDs2dpY28u")
$new1=B64("UGVzcXVpc2Fkb3IgZGUgcMOzcy1kb3V0b3JhZG8gdm9sdW50w6FyaW8gbmEgVW5pdmVyc2lkYWRlIEZlZGVyYWwgZGUgTWF0byBHcm9zc28gZG8gU3VsLiBDb25jZXDDp8OjbyBkbyBwcm9qZXRvLCBhcnF1aXRldHVyYSBjaWVudMOtZmljYSBlIGRpZ2l0YWwsIGludGVncmHDp8OjbyB0ZXJyaXRvcmlhbCwgZGVzZW5obyBkbyBzaXN0ZW1hIG11bHRpZXNjYWxhciwgZG9jdW1lbnRhw6fDo28gZSBkZXNlbnZvbHZpbWVudG8gbWV0b2RvbMOzZ2ljby4=")
$old2=B64("Q29uY2Vww6fDo28gZ2VyYWwsIGFycXVpdGV0dXJhIGNpZW50w61maWNhIGUgZGlnaXRhbCwgaW50ZWdyYcOnw6NvIGRlIGRhZG9zLCBkZXNlbmhvIG1ldG9kb2zDs2dpY28sIGRvY3VtZW50YcOnw6NvLCBvcmdhbml6YcOnw6NvIG11bHRpZXNjYWxhciBlIGRlc2Vudm9sdmltZW50byBkYSBpbmZyYWVzdHJ1dHVyYSBlZHVjYWNpb25hbCBlIGdlb2NpZW50w61maWNhLg==")
$new2=B64("RGVzZW52b2x2aW1lbnRvIGRvIElUQSBBUkFORFUgTVMgbm8gw6JtYml0byBkYSBwZXNxdWlzYSBkZSBww7NzLWRvdXRvcmFkbyB2b2x1bnTDoXJpbyBuYSBVbml2ZXJzaWRhZGUgRmVkZXJhbCBkZSBNYXRvIEdyb3NzbyBkbyBTdWwsIGNvbSByZXNwb25zYWJpbGlkYWRlIHBlbGEgY29uY2Vww6fDo28gZ2VyYWwsIGFycXVpdGV0dXJhIGNpZW50w61maWNhIGUgZGlnaXRhbCwgaW50ZWdyYcOnw6NvIGRlIGRhZG9zLCBkZXNlbmhvIG1ldG9kb2zDs2dpY28sIGRvY3VtZW50YcOnw6NvLCBvcmdhbml6YcOnw6NvIG11bHRpZXNjYWxhciBlIGRlc2Vudm9sdmltZW50byBkYSBpbmZyYWVzdHJ1dHVyYSBlZHVjYWNpb25hbCBlIGdlb2NpZW50w61maWNhLg==")
$anchor=B64("PGRpdiBjbGFzcz0iYXV0b3JpYS1wZXJzb24tYWN0aW9ucyI+PGEgaHJlZj0ibWFpbHRvOmNhcmxvcy5idXNvbkB1Zm1zLmJyIj5FLW1haWw8L2E+")
$block=B64("PGRpdiBjbGFzcz0iYXV0b3JpYS12aW5jdWxvLXBlc3F1aXNhIj48Yj5Ww61uY3VsbyBkYSBwZXNxdWlzYTwvYj48c3Bhbj5PIElUQSBBUkFORFUgTVMgaW50ZWdyYSBhIHBlc3F1aXNhIGRlc2Vudm9sdmlkYSBubyDDom1iaXRvIGRvIHDDs3MtZG91dG9yYWRvIHZvbHVudMOhcmlvIG5hIFVuaXZlcnNpZGFkZSBGZWRlcmFsIGRlIE1hdG8gR3Jvc3NvIGRvIFN1bC4gRXN0ZSB2w61uY3VsbyBuw6NvIGNvcnJlc3BvbmRlIGEgY2FyZ28gZG9jZW50ZSBvdSBwb3Npw6fDo28gcGVybWFuZW50ZSBubyBxdWFkcm8gaW5zdGl0dWNpb25hbC48L3NwYW4+PC9kaXY+")
$cssBlock=B64("LyogSVRBIEFSQU5EVSBNUyDCtyB2w61uY3VsbyBww7NzLWRvdXRvcmFkbyB2b2x1bnTDoXJpbyAqLwouYXV0b3JpYS12aW5jdWxvLXBlc3F1aXNhe21hcmdpbi10b3A6MTBweDtwYWRkaW5nOjEwcHggMTJweDtib3JkZXI6MXB4IHNvbGlkICNkNWUyZTk7Ym9yZGVyLXJhZGl1czoxMHB4O2JhY2tncm91bmQ6I2Y4ZmJmZDtkaXNwbGF5OmZsZXg7ZmxleC1kaXJlY3Rpb246Y29sdW1uO2dhcDozcHh9Ci5hdXRvcmlhLXZpbmN1bG8tcGVzcXVpc2EgYntjb2xvcjojMjM0YjY0fQouYXV0b3JpYS12aW5jdWxvLXBlc3F1aXNhIHNwYW57Y29sb3I6IzUzNmU3ZDtsaW5lLWhlaWdodDoxLjQ1fQ==")

$ok1=Replace-Exact $index $old1 $new1
$ok2=Replace-Exact $index $old2 $new2
Insert-Before $index $anchor $block

[byte[]]$cssData=[System.IO.File]::ReadAllBytes($css)
if((IndexOf-Bytes $cssData $cssBlock 0) -lt 0){
  $nl=[Text.Encoding]::UTF8.GetBytes("`r`n")
  $out=New-Object System.IO.MemoryStream
  $out.Write($cssData,0,$cssData.Length);$out.Write($nl,0,$nl.Length);$out.Write($cssBlock,0,$cssBlock.Length)
  [System.IO.File]::WriteAllBytes($css,$out.ToArray());$out.Dispose()
}

[byte[]]$verify=[System.IO.File]::ReadAllBytes($index)
$checks=@(
 [Text.Encoding]::UTF8.GetBytes('Pesquisador de pós-doutorado voluntário'),
 [Text.Encoding]::UTF8.GetBytes('O ITA ARANDU MS integra a pesquisa desenvolvida no âmbito do pós-doutorado voluntário'),
 [Text.Encoding]::UTF8.GetBytes('Este vínculo não corresponde a cargo docente ou posição permanente no quadro institucional.')
)
foreach($c in $checks){ if((IndexOf-Bytes $verify $c 0) -lt 0){ throw "Verificacao final falhou." } }

Write-Host "OK - Vinculo corrigido para pesquisador de pos-doutorado voluntario." -ForegroundColor Green
Write-Host "OK - ITA ARANDU MS identificado como parte da pesquisa de pos-doutorado voluntario." -ForegroundColor Green
Write-Host "OK - Sem sugestao de cargo docente ou posicao permanente na UFMS." -ForegroundColor Green
Write-Host "OK - Micro patch aplicado por bytes, sem recodificacao global." -ForegroundColor Green
