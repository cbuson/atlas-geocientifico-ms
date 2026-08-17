$ErrorActionPreference = "Stop"
Write-Host "ITA ARANDU MS - AUTORIA CIENTIFICA COMPLETA - R3" -ForegroundColor Cyan

function B64([string]$s) { return [Convert]::FromBase64String($s) }
function Find-RepoRoot {
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
  throw "Nao foi possivel localizar a raiz do repositorio."
}
function IndexOf-Bytes([byte[]]$hay,[byte[]]$needle,[int]$start=0){
  if($needle.Length -eq 0){ return 0 }
  for($i=$start;$i -le $hay.Length-$needle.Length;$i++){
    $ok=$true
    for($j=0;$j -lt $needle.Length;$j++){ if($hay[$i+$j] -ne $needle[$j]){ $ok=$false; break } }
    if($ok){ return $i }
  }
  return -1
}
function Replace-Range([string]$path,[byte[]]$startNeedle,[byte[]]$endNeedle,[byte[]]$replacement){
  [byte[]]$data=[System.IO.File]::ReadAllBytes($path)
  $s=IndexOf-Bytes $data $startNeedle 0
  if($s -lt 0){ return $false }
  $e=IndexOf-Bytes $data $endNeedle $s
  if($e -lt 0){ throw "Fim do bloco Autoria nao encontrado." }
  $out=New-Object System.IO.MemoryStream
  $out.Write($data,0,$s)
  $out.Write($replacement,0,$replacement.Length)
  $out.Write($data,$e,$data.Length-$e)
  [System.IO.File]::WriteAllBytes($path,$out.ToArray())
  $out.Dispose()
  return $true
}
function Insert-Before([string]$path,[byte[]]$anchor,[byte[]]$insert){
  [byte[]]$data=[System.IO.File]::ReadAllBytes($path)
  if((IndexOf-Bytes $data $insert 0) -ge 0){ return }
  $pos=IndexOf-Bytes $data $anchor 0
  if($pos -lt 0){ throw "Ancora nao encontrada." }
  $out=New-Object System.IO.MemoryStream
  $out.Write($data,0,$pos); $out.Write($insert,0,$insert.Length); $out.Write($data,$pos,$data.Length-$pos)
  [System.IO.File]::WriteAllBytes($path,$out.ToArray()); $out.Dispose()
}
function Insert-After([string]$path,[byte[]]$anchor,[byte[]]$insert){
  [byte[]]$data=[System.IO.File]::ReadAllBytes($path)
  if((IndexOf-Bytes $data $insert 0) -ge 0){ return }
  $pos=IndexOf-Bytes $data $anchor 0
  if($pos -lt 0){ throw "Botao Ajuda nao encontrado." }
  $cut=$pos+$anchor.Length
  $out=New-Object System.IO.MemoryStream
  $out.Write($data,0,$cut); $out.Write($insert,0,$insert.Length); $out.Write($data,$cut,$data.Length-$cut)
  [System.IO.File]::WriteAllBytes($path,$out.ToArray()); $out.Dispose()
}
function Replace-Exact([string]$path,[byte[]]$old,[byte[]]$new){
  [byte[]]$data=[System.IO.File]::ReadAllBytes($path)
  $p=IndexOf-Bytes $data $old 0
  if($p -lt 0){ return }
  $out=New-Object System.IO.MemoryStream
  $out.Write($data,0,$p); $out.Write($new,0,$new.Length); $out.Write($data,$p+$old.Length,$data.Length-$p-$old.Length)
  [System.IO.File]::WriteAllBytes($path,$out.ToArray()); $out.Dispose()
}

$root=Find-RepoRoot
$docs=Join-Path $root "docs"
$index=Join-Path $docs "index.html"
$css=Join-Path $docs "assets\css\atlas.css"
Write-Host "Raiz detectada: $root" -ForegroundColor Green
if(!(Test-Path $css)){ throw "atlas.css nao encontrado." }

$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$backup=Join-Path $root ("backup_AUTORIA_COMPLETA_"+$stamp)
New-Item -ItemType Directory -Path (Join-Path $backup "assets\css") -Force | Out-Null
Copy-Item $index (Join-Path $backup "index.html") -Force
Copy-Item $css (Join-Path $backup "assets\css\atlas.css") -Force
Write-Host "Backup criado: $backup"

$help=B64("PGJ1dHRvbiB0eXBlPSJidXR0b24iIGNsYXNzPSJuYXYtYnRuIGhlbHAiIGRhdGEtbW9kYWw9ImFqdWRhTW9kYWwiIGRhdGEtc2VjdGlvbj0iYWp1ZGEiPj8gQWp1ZGE8L2J1dHRvbj4=")
$diag=B64("PGRpdiBjbGFzcz0ibW9kYWwiIGlkPSJkaWFnbm9zdGljb01vZGFsIg==")
$icon=B64("PGJ1dHRvbiB0eXBlPSJidXR0b24iIGNsYXNzPSJuYXYtYnRuIGF1dG9yaWEtc2hvcnQiIGRhdGEtbW9kYWw9ImF1dG9yaWFNb2RhbCIgYXJpYS1sYWJlbD0iQXV0b3JpYSBkbyBwcm9qZXRvIiB0aXRsZT0iQXV0b3JpYSBkbyBwcm9qZXRvIj48c3BhbiBhcmlhLWhpZGRlbj0idHJ1ZSI+aTwvc3Bhbj48L2J1dHRvbj4=")
$modal=B64("PGRpdiBjbGFzcz0ibW9kYWwgYXV0b3JpYS1wcm9qZWN0LW1vZGFsIiBpZD0iYXV0b3JpYU1vZGFsIiByb2xlPSJkaWFsb2ciIGFyaWEtbW9kYWw9InRydWUiIGFyaWEtbGFiZWxsZWRieT0iYXV0b3JpYVRpdGxlIj48ZGl2IGNsYXNzPSJtb2RhbC1ib3ggYXV0b3JpYS1wcm9qZWN0LWJveCI+PGRpdiBjbGFzcz0ibW9kYWwtaGVhZCI+PGRpdj48ZGl2IGNsYXNzPSJraWNrZXIiPkF1dG9yaWE8L2Rpdj48aDIgaWQ9ImF1dG9yaWFUaXRsZSI+RXF1aXBlIGNpZW50w61maWNhPC9oMj48L2Rpdj48YnV0dG9uIHR5cGU9ImJ1dHRvbiIgY2xhc3M9ImNsb3NlLW1vZGFsIiBkYXRhLWNsb3NlPSJhdXRvcmlhTW9kYWwiIGFyaWEtbGFiZWw9IkZlY2hhciBhdXRvcmlhIj7DlzwvYnV0dG9uPjwvZGl2PjxkaXYgY2xhc3M9Im1vZGFsLWJvZHkiPgo8ZGl2IGNsYXNzPSJhdXRvcmlhLWludHJvIj48Yj5JVEEgQVJBTkRVIE1TPC9iPjxzcGFuPkF0bGFzIGdlb2NpZW50w61maWNvIGVkdWNhdGl2byBlIGNpZW50w61maWNvIGRlIE1hdG8gR3Jvc3NvIGRvIFN1bDwvc3Bhbj48L2Rpdj4KCjxkaXYgY2xhc3M9ImF1dG9yaWEtZnVsbC1jYXJkIj4KPGRpdiBjbGFzcz0iYXV0b3JpYS1wZXJzb24taGVhZCI+PGRpdiBjbGFzcz0iYXV0b3JpYS1wZXJzb24tbWFyayIgYXJpYS1oaWRkZW49InRydWUiPkNCPC9kaXY+PGRpdj48aDM+Q2FybG9zIEJ1c8OzbiBCdWVzYTwvaDM+PGRpdiBjbGFzcz0iYXV0aG9yLXJvbGUiPkNvbmNlcMOnw6NvIGRvIHByb2pldG8sIGFycXVpdGV0dXJhIGNpZW50w61maWNhIGUgZGlnaXRhbCwgaW50ZWdyYcOnw6NvIHRlcnJpdG9yaWFsLCBkZXNlbmhvIGRvIHNpc3RlbWEgbXVsdGllc2NhbGFyLCBkb2N1bWVudGHDp8OjbyBlIGRlc2Vudm9sdmltZW50byBtZXRvZG9sw7NnaWNvLjwvZGl2PjwvZGl2PjwvZGl2Pgo8ZGl2IGNsYXNzPSJhdXRob3ItbWV0YSBhdXRvcmlhLW1ldGEtZ3JpZCI+CjxkaXY+PHNwYW4gY2xhc3M9ImF1dG9yaWEtbGFiZWwiPkluc3RpdHVpw6fDo288L3NwYW4+PHN0cm9uZz5Vbml2ZXJzaWRhZGUgRmVkZXJhbCBkZSBNYXRvIEdyb3NzbyBkbyBTdWwgwrcgVUZNUzwvc3Ryb25nPjwvZGl2Pgo8ZGl2PjxzcGFuIGNsYXNzPSJhdXRvcmlhLWxhYmVsIj5Qcm9ncmFtYTwvc3Bhbj48c3Ryb25nPlByb2dyYW1hIGRlIFDDs3MtR3JhZHVhw6fDo28gZW0gVGVjbm9sb2dpYXMgQW1iaWVudGFpcyDCtyBQUEdUQTwvc3Ryb25nPjwvZGl2Pgo8ZGl2PjxzcGFuIGNsYXNzPSJhdXRvcmlhLWxhYmVsIj5VbmlkYWRlPC9zcGFuPjxzdHJvbmc+RmFjdWxkYWRlIGRlIEVuZ2VuaGFyaWFzLCBBcnF1aXRldHVyYSBlIFVyYmFuaXNtbyBlIEdlb2dyYWZpYSDCtyBGQUVORzwvc3Ryb25nPjwvZGl2Pgo8ZGl2PjxzcGFuIGNsYXNzPSJhdXRvcmlhLWxhYmVsIj5FLW1haWw8L3NwYW4+PGEgaHJlZj0ibWFpbHRvOmNhcmxvcy5idXNvbkB1Zm1zLmJyIj5jYXJsb3MuYnVzb25AdWZtcy5icjwvYT48L2Rpdj4KPGRpdj48c3BhbiBjbGFzcz0iYXV0b3JpYS1sYWJlbCI+T1JDSUQ8L3NwYW4+PGEgaHJlZj0iaHR0cHM6Ly9vcmNpZC5vcmcvMDAwMC0wMDAyLTE0NDYtMjI1MiIgdGFyZ2V0PSJfYmxhbmsiIHJlbD0ibm9vcGVuZXIgbm9yZWZlcnJlciI+MDAwMC0wMDAyLTE0NDYtMjI1MjwvYT48L2Rpdj4KPGRpdj48c3BhbiBjbGFzcz0iYXV0b3JpYS1sYWJlbCI+Q3VycsOtY3VsbyBMYXR0ZXM8L3NwYW4+PGEgaHJlZj0iaHR0cDovL2xhdHRlcy5jbnBxLmJyLzk3MDMxNzk1NTE3MjQxNzgiIHRhcmdldD0iX2JsYW5rIiByZWw9Im5vb3BlbmVyIG5vcmVmZXJyZXIiPjk3MDMxNzk1NTE3MjQxNzg8L2E+PC9kaXY+CjwvZGl2Pgo8ZGl2IGNsYXNzPSJhdXRvcmlhLWNvbnRyaWIiPjxiPkNvbnRyaWJ1acOnw6NvIG5vIHByb2pldG88L2I+PHNwYW4+Q29uY2Vww6fDo28gZ2VyYWwsIGFycXVpdGV0dXJhIGNpZW50w61maWNhIGUgZGlnaXRhbCwgaW50ZWdyYcOnw6NvIGRlIGRhZG9zLCBkZXNlbmhvIG1ldG9kb2zDs2dpY28sIGRvY3VtZW50YcOnw6NvLCBvcmdhbml6YcOnw6NvIG11bHRpZXNjYWxhciBlIGRlc2Vudm9sdmltZW50byBkYSBpbmZyYWVzdHJ1dHVyYSBlZHVjYWNpb25hbCBlIGdlb2NpZW50w61maWNhLjwvc3Bhbj48L2Rpdj4KPGRpdiBjbGFzcz0iYXV0b3JpYS1wZXJzb24tYWN0aW9ucyI+PGEgaHJlZj0ibWFpbHRvOmNhcmxvcy5idXNvbkB1Zm1zLmJyIj5FLW1haWw8L2E+PGEgaHJlZj0iaHR0cHM6Ly9vcmNpZC5vcmcvMDAwMC0wMDAyLTE0NDYtMjI1MiIgdGFyZ2V0PSJfYmxhbmsiIHJlbD0ibm9vcGVuZXIgbm9yZWZlcnJlciI+T1JDSUQ8L2E+PGEgaHJlZj0iaHR0cDovL2xhdHRlcy5jbnBxLmJyLzk3MDMxNzk1NTE3MjQxNzgiIHRhcmdldD0iX2JsYW5rIiByZWw9Im5vb3BlbmVyIG5vcmVmZXJyZXIiPkN1cnLDrWN1bG8gTGF0dGVzPC9hPjwvZGl2Pgo8L2Rpdj4KCjxkaXYgY2xhc3M9ImF1dG9yaWEtZnVsbC1jYXJkIj4KPGRpdiBjbGFzcz0iYXV0b3JpYS1wZXJzb24taGVhZCI+PGRpdiBjbGFzcz0iYXV0b3JpYS1wZXJzb24tbWFyayIgYXJpYS1oaWRkZW49InRydWUiPlNHPC9kaXY+PGRpdj48aDM+U2FuZHJhIEdhcmNpYSBHYWJhczwvaDM+PGRpdiBjbGFzcz0iYXV0aG9yLXJvbGUiPkNvYXV0b3JpYSBjaWVudMOtZmljYSwgZ2VvbG9naWEsIGhpZHJvZ2VvbG9naWEsIGdlb3RlY25pYSBhbWJpZW50YWwsIGdlb3F1w61taWNhLCBnZW9sb2dpYSBhbWJpZW50YWwgZSByZXZpc8OjbyBkYSBpbnRlZ3Jhw6fDo28gZ2VvY2llbnTDrWZpY2EuPC9kaXY+PC9kaXY+PC9kaXY+CjxkaXYgY2xhc3M9ImF1dGhvci1tZXRhIGF1dG9yaWEtbWV0YS1ncmlkIj4KPGRpdj48c3BhbiBjbGFzcz0iYXV0b3JpYS1sYWJlbCI+SW5zdGl0dWnDp8Ojbzwvc3Bhbj48c3Ryb25nPlVuaXZlcnNpZGFkZSBGZWRlcmFsIGRlIE1hdG8gR3Jvc3NvIGRvIFN1bCDCtyBVRk1TPC9zdHJvbmc+PC9kaXY+CjxkaXY+PHNwYW4gY2xhc3M9ImF1dG9yaWEtbGFiZWwiPlByb2dyYW1hPC9zcGFuPjxzdHJvbmc+UHJvZ3JhbWEgZGUgUMOzcy1HcmFkdWHDp8OjbyBlbSBUZWNub2xvZ2lhcyBBbWJpZW50YWlzIMK3IFBQR1RBPC9zdHJvbmc+PC9kaXY+CjxkaXY+PHNwYW4gY2xhc3M9ImF1dG9yaWEtbGFiZWwiPlVuaWRhZGU8L3NwYW4+PHN0cm9uZz5GYWN1bGRhZGUgZGUgRW5nZW5oYXJpYXMsIEFycXVpdGV0dXJhIGUgVXJiYW5pc21vIGUgR2VvZ3JhZmlhIMK3IEZBRU5HPC9zdHJvbmc+PC9kaXY+CjxkaXY+PHNwYW4gY2xhc3M9ImF1dG9yaWEtbGFiZWwiPkUtbWFpbDwvc3Bhbj48YSBocmVmPSJtYWlsdG86c2FuZHJhLmdhYmFzQHVmbXMuYnIiPnNhbmRyYS5nYWJhc0B1Zm1zLmJyPC9hPjwvZGl2Pgo8ZGl2PjxzcGFuIGNsYXNzPSJhdXRvcmlhLWxhYmVsIj5PUkNJRDwvc3Bhbj48YSBocmVmPSJodHRwczovL29yY2lkLm9yZy8wMDAwLTAwMDItMTAyNy0wMjg4IiB0YXJnZXQ9Il9ibGFuayIgcmVsPSJub29wZW5lciBub3JlZmVycmVyIj4wMDAwLTAwMDItMTAyNy0wMjg4PC9hPjwvZGl2Pgo8ZGl2PjxzcGFuIGNsYXNzPSJhdXRvcmlhLWxhYmVsIj5DdXJyw61jdWxvIExhdHRlczwvc3Bhbj48YSBocmVmPSJodHRwOi8vbGF0dGVzLmNucHEuYnIvOTc5MTYwNTY1NzU2NjU5NiIgdGFyZ2V0PSJfYmxhbmsiIHJlbD0ibm9vcGVuZXIgbm9yZWZlcnJlciI+OTc5MTYwNTY1NzU2NjU5NjwvYT48L2Rpdj4KPC9kaXY+CjxkaXYgY2xhc3M9ImF1dG9yaWEtY29udHJpYiI+PGI+Q29udHJpYnVpw6fDo28gbm8gcHJvamV0bzwvYj48c3Bhbj5Db2F1dG9yaWEgY2llbnTDrWZpY2EgZSByZXZpc8OjbyBnZW9jaWVudMOtZmljYSwgY29tIGNvbnRyaWJ1acOnw7VlcyBlbSBnZW9sb2dpYSwgaGlkcm9nZW9sb2dpYSwgZ2VvdGVjbmlhIGFtYmllbnRhbCwgZ2VvcXXDrW1pY2EsIGdlb2xvZ2lhIGFtYmllbnRhbCBlIGludGVncmHDp8OjbyBkb3MgY29udGXDumRvcyBjaWVudMOtZmljb3MuPC9zcGFuPjwvZGl2Pgo8ZGl2IGNsYXNzPSJhdXRvcmlhLXBlcnNvbi1hY3Rpb25zIj48YSBocmVmPSJtYWlsdG86c2FuZHJhLmdhYmFzQHVmbXMuYnIiPkUtbWFpbDwvYT48YSBocmVmPSJodHRwczovL29yY2lkLm9yZy8wMDAwLTAwMDItMTAyNy0wMjg4IiB0YXJnZXQ9Il9ibGFuayIgcmVsPSJub29wZW5lciBub3JlZmVycmVyIj5PUkNJRDwvYT48YSBocmVmPSJodHRwOi8vbGF0dGVzLmNucHEuYnIvOTc5MTYwNTY1NzU2NjU5NiIgdGFyZ2V0PSJfYmxhbmsiIHJlbD0ibm9vcGVuZXIgbm9yZWZlcnJlciI+Q3VycsOtY3VsbyBMYXR0ZXM8L2E+PC9kaXY+CjwvZGl2PgoKPGRpdiBjbGFzcz0iYXV0b3JpYS1wcm9qZWN0LWlkIj4KPGRpdj48c3BhbiBjbGFzcz0iYXV0b3JpYS1sYWJlbCI+SWRlbnRpZmljYcOnw6NvIHBlcnNpc3RlbnRlIGRvIHByb2pldG88L3NwYW4+PHN0cm9uZz5ET0kgwrcgMTAuNTI4MS96ZW5vZG8uMjE5MjMxMDE8L3N0cm9uZz48c21hbGw+UmVnaXN0cm8gZG8gSVRBIEFSQU5EVSBNUyBubyBaZW5vZG88L3NtYWxsPjwvZGl2Pgo8ZGl2IGNsYXNzPSJhdXRvcmlhLWFjdGlvbnMiPjxhIGNsYXNzPSJhdXRvcmlhLWxpbmsgcHJpbWFyeSIgaHJlZj0iaHR0cHM6Ly96ZW5vZG8ub3JnL3JlY29yZHMvMjE5MjMxMDEiIHRhcmdldD0iX2JsYW5rIiByZWw9Im5vb3BlbmVyIG5vcmVmZXJyZXIiPkFicmlyIFplbm9kbzwvYT48YSBjbGFzcz0iYXV0b3JpYS1saW5rIiBocmVmPSJodHRwczovL2RvaS5vcmcvMTAuNTI4MS96ZW5vZG8uMjE5MjMxMDEiIHRhcmdldD0iX2JsYW5rIiByZWw9Im5vb3BlbmVyIG5vcmVmZXJyZXIiPkFicmlyIERPSTwvYT48L2Rpdj4KPC9kaXY+Cgo8aDM+Q29tbyBjaXRhciBJVEEgQVJBTkRVIE1TPC9oMz4KPGRpdiBjbGFzcz0iYXV0b3JpYS1jaXRhdGlvbiI+QnVzw7NuIEJ1ZXNhLCBDLiwgJmFtcDsgR2FiYXMsIFMuIEcuICgyMDI2KS4gPGk+SVRBIEFSQU5EVSBNUyDCtyBBdGxhcyBnZW9jaWVudMOtZmljbyBlZHVjYXRpdm8gZSBjaWVudMOtZmljbyBkZSBNYXRvIEdyb3NzbyBkbyBTdWw8L2k+IFtTb2Z0d2FyZSBlIGF0bGFzIGdlb2NpZW50w61maWNvXS4gWmVub2RvLiBodHRwczovL2RvaS5vcmcvMTAuNTI4MS96ZW5vZG8uMjE5MjMxMDE8L2Rpdj4KCjxkaXYgY2xhc3M9ImF1dG9yaWEtbm90ZSI+PGI+QXV0b3JpYSBlIHJhc3RyZWFiaWxpZGFkZTwvYj48c3Bhbj5PcyB2w61uY3Vsb3MsIGlkZW50aWZpY2Fkb3JlcyBlIGNvbnRhdG9zIGFjaW1hIHBlcm1pdGVtIHZlcmlmaWNhciBhIGF1dG9yaWEgY2llbnTDrWZpY2EgZG8gcHJvamV0by4gTyBET0kgZm9ybmVjZSB1bSBpZGVudGlmaWNhZG9yIHBlcnNpc3RlbnRlIHBhcmEgbyByZWdpc3RybyBubyBaZW5vZG8uIE9zIGxpbmtzIGV4dGVybm9zIHNvbWVudGUgc8OjbyBhYmVydG9zIHF1YW5kbyBvIHVzdcOhcmlvIG9zIGVzY29saGUuPC9zcGFuPjwvZGl2Pgo8L2Rpdj48L2Rpdj48L2Rpdj4=")
$cssBlock=B64("LyogSVRBIEFSQU5EVSBNUyDCtyBhdXRvcmlhIGNpZW50w61maWNhIGNvbXBsZXRhICovCi5uYXYtYnRuLmF1dG9yaWEtc2hvcnR7d2lkdGg6MzRweDtoZWlnaHQ6MzRweDttaW4td2lkdGg6MzRweDtwYWRkaW5nOjAhaW1wb3J0YW50O2JvcmRlci1yYWRpdXM6NTAlO2Rpc3BsYXk6aW5saW5lLWZsZXg7YWxpZ24taXRlbXM6Y2VudGVyO2p1c3RpZnktY29udGVudDpjZW50ZXI7Zm9udC1zaXplOjB9Ci5uYXYtYnRuLmF1dG9yaWEtc2hvcnQgc3BhbntkaXNwbGF5OmlubGluZS1mbGV4O2FsaWduLWl0ZW1zOmNlbnRlcjtqdXN0aWZ5LWNvbnRlbnQ6Y2VudGVyO3dpZHRoOjE4cHg7aGVpZ2h0OjE4cHg7Ym9yZGVyOjEuNXB4IHNvbGlkIGN1cnJlbnRDb2xvcjtib3JkZXItcmFkaXVzOjUwJTtmb250OjkwMCAxMnB4LzEgR2VvcmdpYSxzZXJpZn0KLmF1dG9yaWEtcHJvamVjdC1ib3h7d2lkdGg6bWluKDkwMHB4LDk1dncpO21heC1oZWlnaHQ6bWluKDg4dmgsOTIwcHgpfQouYXV0b3JpYS1wcm9qZWN0LW1vZGFsIC5tb2RhbC1ib2R5e2JhY2tncm91bmQ6I2ZmZn0KLmF1dG9yaWEtaW50cm97ZGlzcGxheTpmbGV4O2ZsZXgtZGlyZWN0aW9uOmNvbHVtbjtnYXA6M3B4O3BhZGRpbmc6MnB4IDAgMTJweH0KLmF1dG9yaWEtaW50cm8gYntmb250LXNpemU6MTlweDtjb2xvcjojMTIzZjVkfQouYXV0b3JpYS1pbnRybyBzcGFue2NvbG9yOiM2MDc2ODR9Ci5hdXRvcmlhLWZ1bGwtY2FyZHtib3JkZXI6MXB4IHNvbGlkICNkNWUyZTk7Ym9yZGVyLXJhZGl1czoxNHB4O3BhZGRpbmc6MTRweDttYXJnaW46MCAwIDEycHg7YmFja2dyb3VuZDojZmZmfQouYXV0b3JpYS1wZXJzb24taGVhZHtkaXNwbGF5OmZsZXg7YWxpZ24taXRlbXM6ZmxleC1zdGFydDtnYXA6MTJweH0KLmF1dG9yaWEtcGVyc29uLWhlYWQgaDN7bWFyZ2luOjAgMCA0cHg7Y29sb3I6IzE0M2Y1Yn0KLmF1dG9yaWEtcGVyc29uLW1hcmt7d2lkdGg6NDZweDtoZWlnaHQ6NDZweDttaW4td2lkdGg6NDZweDtib3JkZXItcmFkaXVzOjUwJTtkaXNwbGF5OmZsZXg7YWxpZ24taXRlbXM6Y2VudGVyO2p1c3RpZnktY29udGVudDpjZW50ZXI7YmFja2dyb3VuZDojZTlmM2Y5O2JvcmRlcjoxcHggc29saWQgI2M2ZGFlNjtjb2xvcjojMGI1Njg2O2ZvbnQtd2VpZ2h0Ojk1MH0KLmF1dG9yaWEtbWV0YS1ncmlke2Rpc3BsYXk6Z3JpZDtncmlkLXRlbXBsYXRlLWNvbHVtbnM6cmVwZWF0KDIsbWlubWF4KDAsMWZyKSk7Z2FwOjlweCAxNHB4O21hcmdpbi10b3A6MTJweH0KLmF1dG9yaWEtbWV0YS1ncmlkPmRpdntkaXNwbGF5OmZsZXg7ZmxleC1kaXJlY3Rpb246Y29sdW1uO2dhcDoycHg7cGFkZGluZzo4cHggOXB4O2JvcmRlci1yYWRpdXM6OXB4O2JhY2tncm91bmQ6I2Y4ZmJmZDtib3JkZXI6MXB4IHNvbGlkICNlMWViZjB9Ci5hdXRvcmlhLW1ldGEtZ3JpZCBzdHJvbmcsLmF1dG9yaWEtbWV0YS1ncmlkIGF7Zm9udC1zaXplOjEycHg7bGluZS1oZWlnaHQ6MS4zNX0KLmF1dG9yaWEtbWV0YS1ncmlkIGF7Y29sb3I6IzBiNTY4Njtmb250LXdlaWdodDo4MDA7dGV4dC1kZWNvcmF0aW9uOm5vbmU7d29yZC1icmVhazpicmVhay13b3JkfQouYXV0b3JpYS1sYWJlbHtmb250LXNpemU6OHB4O2xldHRlci1zcGFjaW5nOi4wOWVtO3RleHQtdHJhbnNmb3JtOnVwcGVyY2FzZTtmb250LXdlaWdodDo5NTA7Y29sb3I6IzY0N2U4Y30KLmF1dG9yaWEtY29udHJpYnttYXJnaW4tdG9wOjEwcHg7ZGlzcGxheTpmbGV4O2ZsZXgtZGlyZWN0aW9uOmNvbHVtbjtnYXA6M3B4O2NvbG9yOiM1MzZlN2Q7bGluZS1oZWlnaHQ6MS40NX0KLmF1dG9yaWEtY29udHJpYiBie2NvbG9yOiMyMzRiNjR9Ci5hdXRvcmlhLXBlcnNvbi1hY3Rpb25ze2Rpc3BsYXk6ZmxleDtnYXA6N3B4O2ZsZXgtd3JhcDp3cmFwO21hcmdpbi10b3A6MTBweH0KLmF1dG9yaWEtcGVyc29uLWFjdGlvbnMgYXtkaXNwbGF5OmlubGluZS1mbGV4O2FsaWduLWl0ZW1zOmNlbnRlcjtqdXN0aWZ5LWNvbnRlbnQ6Y2VudGVyO3BhZGRpbmc6N3B4IDEwcHg7Ym9yZGVyOjFweCBzb2xpZCAjYmNkMGRjO2JvcmRlci1yYWRpdXM6OXB4O3RleHQtZGVjb3JhdGlvbjpub25lO2NvbG9yOiMwYjU2ODY7YmFja2dyb3VuZDojZmZmO2ZvbnQtd2VpZ2h0Ojg1MH0KLmF1dG9yaWEtcHJvamVjdC1pZHttYXJnaW46MTRweCAwO3BhZGRpbmc6MTNweDtib3JkZXI6MXB4IHNvbGlkICNjOWRjZTc7YmFja2dyb3VuZDojZjdmYmZkO2JvcmRlci1yYWRpdXM6MTJweDtkaXNwbGF5OmZsZXg7anVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47Z2FwOjE0cHg7YWxpZ24taXRlbXM6Y2VudGVyfQouYXV0b3JpYS1wcm9qZWN0LWlkPmRpdjpmaXJzdC1jaGlsZHtkaXNwbGF5OmZsZXg7ZmxleC1kaXJlY3Rpb246Y29sdW1uO2dhcDozcHh9Ci5hdXRvcmlhLXByb2plY3QtaWQgc3Ryb25ne2ZvbnQtc2l6ZToxN3B4O2NvbG9yOiMwNzNiNjM7d29yZC1icmVhazpicmVhay1hbGx9Ci5hdXRvcmlhLXByb2plY3QtaWQgc21hbGx7Y29sb3I6IzYxNzk4Nn0KLmF1dG9yaWEtYWN0aW9uc3tkaXNwbGF5OmZsZXg7Z2FwOjdweDtmbGV4LXdyYXA6d3JhcDtqdXN0aWZ5LWNvbnRlbnQ6ZmxleC1lbmR9Ci5hdXRvcmlhLWxpbmt7ZGlzcGxheTppbmxpbmUtZmxleDthbGlnbi1pdGVtczpjZW50ZXI7anVzdGlmeS1jb250ZW50OmNlbnRlcjtib3JkZXI6MXB4IHNvbGlkICNiOGNlZGE7YmFja2dyb3VuZDojZmZmO2NvbG9yOiMwYjU2ODY7Ym9yZGVyLXJhZGl1czo5cHg7cGFkZGluZzo4cHggMTBweDtmb250LXdlaWdodDo4NTA7dGV4dC1kZWNvcmF0aW9uOm5vbmU7d2hpdGUtc3BhY2U6bm93cmFwfQouYXV0b3JpYS1saW5rLnByaW1hcnl7YmFja2dyb3VuZDojMGI1Njg2O2NvbG9yOiNmZmY7Ym9yZGVyLWNvbG9yOiMwYjU2ODZ9Ci5hdXRvcmlhLWNpdGF0aW9ue2JvcmRlci1sZWZ0OjNweCBzb2xpZCAjMGI1Njg2O2JhY2tncm91bmQ6I2Y1ZjlmYjtib3JkZXItcmFkaXVzOjhweDtwYWRkaW5nOjExcHggMTNweDtsaW5lLWhlaWdodDoxLjU1O2NvbG9yOiMzODU0NjZ9Ci5hdXRvcmlhLW5vdGV7bWFyZ2luLXRvcDoxMnB4O2JvcmRlcjoxcHggc29saWQgI2Q4ZTRlYTtib3JkZXItcmFkaXVzOjEwcHg7cGFkZGluZzoxMHB4IDEycHg7ZGlzcGxheTpmbGV4O2ZsZXgtZGlyZWN0aW9uOmNvbHVtbjtnYXA6M3B4O2JhY2tncm91bmQ6I2ZmZn0KLmF1dG9yaWEtbm90ZSBie2NvbG9yOiMxNzQ2NjR9Ci5hdXRvcmlhLW5vdGUgc3Bhbntjb2xvcjojNjA3Njg0O2xpbmUtaGVpZ2h0OjEuNDV9CkBtZWRpYShtYXgtd2lkdGg6NzYwcHgpey5hdXRvcmlhLW1ldGEtZ3JpZHtncmlkLXRlbXBsYXRlLWNvbHVtbnM6MWZyfS5hdXRvcmlhLXByb2plY3QtaWR7YWxpZ24taXRlbXM6c3RyZXRjaDtmbGV4LWRpcmVjdGlvbjpjb2x1bW59LmF1dG9yaWEtYWN0aW9uc3tqdXN0aWZ5LWNvbnRlbnQ6ZmxleC1zdGFydH0uYXV0b3JpYS1saW5re2ZsZXg6MSAxIGF1dG99fQ==")
$oldCard=B64("PGJ1dHRvbiB0eXBlPSJidXR0b24iIGNsYXNzPSJkb2MtY2FyZCIgZGF0YS1tb2RhbD0iYXV0b3JpYU1vZGFsIj48Yj5BdXRvcmlhPC9iPjxzcGFuPkVxdWlwZSwgdsOtbmN1bG9zLCBPUkNJRCwgY29udHJpYnVpw6fDtWVzIGUgY2l0YcOnw6NvIHByb3Zpc8OzcmlhLjwvc3Bhbj48L2J1dHRvbj4=")
$newCard=B64("PGJ1dHRvbiB0eXBlPSJidXR0b24iIGNsYXNzPSJkb2MtY2FyZCIgZGF0YS1tb2RhbD0iYXV0b3JpYU1vZGFsIj48Yj5BdXRvcmlhPC9iPjxzcGFuPkVxdWlwZSBjaWVudMOtZmljYSwgdsOtbmN1bG9zIGluc3RpdHVjaW9uYWlzLCBlLW1haWwsIE9SQ0lELCBDdXJyw61jdWxvIExhdHRlcywgY29udHJpYnVpw6fDtWVzLCBET0kgZSBjaXRhw6fDo28gZG8gcHJvamV0by48L3NwYW4+PC9idXR0b24+")

# Ensure the small header icon exists.
Insert-After $index $help $icon

# Replace any existing autoria modal, whether R2 or an older version.
[byte[]]$data=[System.IO.File]::ReadAllBytes($index)
$autoriaId=[Text.Encoding]::UTF8.GetBytes('id="autoriaModal"')
$autoriaPos=IndexOf-Bytes $data $autoriaId 0
if($autoriaPos -ge 0){
  # Find opening div that starts the modal by scanning backwards for "<div class="
  $divStart=[Text.Encoding]::UTF8.GetBytes('<div class=')
  $start=-1
  for($i=$autoriaPos; $i -ge 0; $i--){
    if($i -le $data.Length-$divStart.Length){
      $ok=$true
      for($j=0;$j -lt $divStart.Length;$j++){ if($data[$i+$j] -ne $divStart[$j]){ $ok=$false; break } }
      if($ok){ $start=$i; break }
    }
  }
  if($start -lt 0){ throw "Inicio do modal Autoria nao encontrado." }
  [byte[]]$sliceStart=New-Object byte[] ($data.Length-$start)
  [Array]::Copy($data,$start,$sliceStart,0,$sliceStart.Length)
  # Use diagnostic modal as immutable end anchor
  $diagPos=IndexOf-Bytes $data $diag $start
  if($diagPos -lt 0){ throw "Modal Diagnostico nao encontrado para delimitar Autoria." }
  $out=New-Object System.IO.MemoryStream
  $out.Write($data,0,$start); $out.Write($modal,0,$modal.Length); $out.Write($data,$diagPos,$data.Length-$diagPos)
  [System.IO.File]::WriteAllBytes($index,$out.ToArray()); $out.Dispose()
} else {
  Insert-Before $index $diag $modal
}

Replace-Exact $index $oldCard $newCard

[byte[]]$cssData=[System.IO.File]::ReadAllBytes($css)
$marker=[Text.Encoding]::UTF8.GetBytes('/* ITA ARANDU MS · autoria científica completa */')
if((IndexOf-Bytes $cssData $marker 0) -lt 0){
  $nl=[Text.Encoding]::UTF8.GetBytes("`r`n")
  $out=New-Object System.IO.MemoryStream
  $out.Write($cssData,0,$cssData.Length); $out.Write($nl,0,$nl.Length); $out.Write($cssBlock,0,$cssBlock.Length)
  [System.IO.File]::WriteAllBytes($css,$out.ToArray()); $out.Dispose()
}

[byte[]]$verify=[System.IO.File]::ReadAllBytes($index)
$checks=@(
 [Text.Encoding]::UTF8.GetBytes('carlos.buson@ufms.br'),
 [Text.Encoding]::UTF8.GetBytes('sandra.gabas@ufms.br'),
 [Text.Encoding]::UTF8.GetBytes('9703179551724178'),
 [Text.Encoding]::UTF8.GetBytes('9791605657566596'),
 [Text.Encoding]::UTF8.GetBytes('0000-0002-1446-2252'),
 [Text.Encoding]::UTF8.GetBytes('0000-0002-1027-0288'),
 [Text.Encoding]::UTF8.GetBytes('10.5281/zenodo.21923101')
)
foreach($c in $checks){ if((IndexOf-Bytes $verify $c 0) -lt 0){ throw "Verificacao final da ficha de autoria falhou." } }

Write-Host "OK - Ficha completa de autoria restaurada e ampliada." -ForegroundColor Green
Write-Host "OK - E-mails institucionais incorporados." -ForegroundColor Green
Write-Host "OK - ORCID de ambos incorporados." -ForegroundColor Green
Write-Host "OK - Curriculos Lattes de ambos incorporados." -ForegroundColor Green
Write-Host "OK - Contribuicoes cientificas incorporadas." -ForegroundColor Green
Write-Host "OK - DOI e Zenodo incorporados." -ForegroundColor Green
Write-Host "OK - Icone de autoria junto a Ajuda mantido." -ForegroundColor Green
Write-Host "OK - Modificacao por bytes, sem recodificacao global do HTML." -ForegroundColor Green
