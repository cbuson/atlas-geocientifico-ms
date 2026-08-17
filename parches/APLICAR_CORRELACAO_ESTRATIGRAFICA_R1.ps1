$ErrorActionPreference='Stop'
Write-Host 'ITA ARANDU MS - CORRELACAO ESTRATIGRAFICA MULTIPONTO - R1.1' -ForegroundColor Cyan

function Find-Root {
 $p=[IO.Path]::GetFullPath($PSScriptRoot)
 for($i=0;$i -lt 8;$i++){if(Test-Path (Join-Path $p 'docs\index.html')){return $p};$q=Split-Path $p -Parent;if(!$q -or $q -eq $p){break};$p=$q}
 throw 'Raiz do repositorio nao encontrada.'
}
function Idx([byte[]]$h,[byte[]]$n,[int]$s=0){
 for($i=$s;$i -le $h.Length-$n.Length;$i++){$ok=$true;for($j=0;$j -lt $n.Length;$j++){if($h[$i+$j]-ne $n[$j]){$ok=$false;break}};if($ok){return $i}};return -1
}
function Insert-Before([string]$path,[string]$anchor,[string]$insert){
 [byte[]]$d=[IO.File]::ReadAllBytes($path);$e=[Text.Encoding]::UTF8;[byte[]]$a=$e.GetBytes($anchor);[byte[]]$x=$e.GetBytes($insert)
 if((Idx $d $x 0)-ge 0){return}
 $p=Idx $d $a 0;if($p -lt 0){throw "Ancora nao encontrada em $path"}
 $m=New-Object IO.MemoryStream;$m.Write($d,0,$p);$m.Write($x,0,$x.Length);$m.Write($d,$p,$d.Length-$p);[IO.File]::WriteAllBytes($path,$m.ToArray());$m.Dispose()
}
function Replace-Literal([string]$path,[string]$old,[string]$new){
 [byte[]]$d=[IO.File]::ReadAllBytes($path);$e=[Text.Encoding]::UTF8;[byte[]]$o=$e.GetBytes($old);[byte[]]$n=$e.GetBytes($new)
 if((Idx $d $n 0)-ge 0){return}
 $p=Idx $d $o 0;if($p -lt 0){return}
 $m=New-Object IO.MemoryStream;$m.Write($d,0,$p);$m.Write($n,0,$n.Length);$m.Write($d,$p+$o.Length,$d.Length-$p-$o.Length);[IO.File]::WriteAllBytes($path,$m.ToArray());$m.Dispose()
}
function Append-Refs([string]$path){
 [byte[]]$d=[IO.File]::ReadAllBytes($path);$e=[Text.Encoding]::UTF8
 if((Idx $d ($e.GetBytes('REF-241')) 0)-ge 0){return}
 [byte[]]$end=$e.GetBytes('];');$p=-1
 for($i=$d.Length-$end.Length;$i -ge 0;$i--){$ok=$true;for($j=0;$j -lt $end.Length;$j++){if($d[$i+$j]-ne $end[$j]){$ok=$false;break}};if($ok){$p=$i;break}}
 if($p -lt 0){throw 'Fim do registro de referencias nao encontrado.'}
 [byte[]]$x=$e.GetBytes([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('LHsiaWQiOiJSRUYtMjQxIiwiZ3JvdXAiOiJGZXJyYW1lbnRhcyBnZW9jaWVudMOtZmljYXMgwrcgZXN0cmF0aWdyYWZpYSIsInN0YXR1cyI6ImluY29ycG9yYWRhIiwidHlwZSI6ImVzdHJhdGlncmFmaWEiLCJhcGEiOiJNdXJwaHksIE0uIEEuLCAmIFNhbHZhZG9yLCBBLiAoMTk5OSkuIEludGVybmF0aW9uYWwgU3RyYXRpZ3JhcGhpYyBHdWlkZeKAlEFuIGFicmlkZ2VkIHZlcnNpb24uIEVwaXNvZGVzLCAyMig0KSwgMjU14oCTMjcxLiBodHRwczovL2RvaS5vcmcvMTAuMTg4MTQvZXBpaXVncy8xOTk5L3YyMmk0LzAwMiIsInVybCI6Imh0dHBzOi8vZG9pLm9yZy8xMC4xODgxNC9lcGlpdWdzLzE5OTkvdjIyaTQvMDAyIiwidXNlIjoiUHJpbmPDrXBpb3MgZGUgY2xhc3NpZmljYcOnw6NvLCB0ZXJtaW5vbG9naWEsIGNvcnJlbGHDp8OjbyBlIGNvbXVuaWNhw6fDo28gZXN0cmF0aWdyw6FmaWNhIHVzYWRvcyBuYSBhanVkYSBtZXRvZG9sw7NnaWNhIGRhIENvcnJlbGHDp8OjbyBFc3RyYXRpZ3LDoWZpY2EuIiwiY2l0YXRpb25fc3RhbmRhcmQiOiJBUEEgNyIsImRvaSI6IjEwLjE4ODE0L2VwaWl1Z3MvMTk5OS92MjJpNC8wMDIiLCJxdWFsaXR5X2NsYXNzIjoiYXJ0aWdvIGNpZW50w61maWNvIGUgZ3VpYSBpbnRlcm5hY2lvbmFsIiwidmVyaWZpY2F0aW9uX2xldmVsIjoiZm9udGVfcHJpbWFyaWFfY29uZmVyaWRhIiwidmVyaWZpZWRfb24iOiIyMDI2LTA4LTE3IiwiYXBhX2Z1bGwiOiJNdXJwaHksIE0uIEEuLCAmIFNhbHZhZG9yLCBBLiAoMTk5OSkuIEludGVybmF0aW9uYWwgU3RyYXRpZ3JhcGhpYyBHdWlkZeKAlEFuIGFicmlkZ2VkIHZlcnNpb24uIEVwaXNvZGVzLCAyMig0KSwgMjU14oCTMjcxLiBodHRwczovL2RvaS5vcmcvMTAuMTg4MTQvZXBpaXVncy8xOTk5L3YyMmk0LzAwMiJ9LHsiaWQiOiJSRUYtMjQyIiwiZ3JvdXAiOiJGZXJyYW1lbnRhcyBnZW9jaWVudMOtZmljYXMgwrcgZXN0cmF0aWdyYWZpYSIsInN0YXR1cyI6ImluY29ycG9yYWRhIiwidHlwZSI6ImVzdHJhdGlncmFmaWEiLCJhcGEiOiJTYWx2YWRvciwgQS4gKEVkLikuICgxOTk0KS4gSW50ZXJuYXRpb25hbCBTdHJhdGlncmFwaGljIEd1aWRlOiBBIGd1aWRlIHRvIHN0cmF0aWdyYXBoaWMgY2xhc3NpZmljYXRpb24sIHRlcm1pbm9sb2d5LCBhbmQgcHJvY2VkdXJlICgybmQgZWQuKS4gSW50ZXJuYXRpb25hbCBVbmlvbiBvZiBHZW9sb2dpY2FsIFNjaWVuY2VzICYgR2VvbG9naWNhbCBTb2NpZXR5IG9mIEFtZXJpY2EuIiwidXJsIjoiaHR0cHM6Ly9zdHJhdGlncmFwaHkub3JnL2d1aWRlLyIsInVzZSI6Ikd1aWEgaW50ZXJuYWNpb25hbCBkZSByZWZlcsOqbmNpYSBwYXJhIGNsYXNzaWZpY2HDp8OjbywgdGVybWlub2xvZ2lhIGUgcHJvY2VkaW1lbnRvcyBlc3RyYXRpZ3LDoWZpY29zLiIsImNpdGF0aW9uX3N0YW5kYXJkIjoiQVBBIDciLCJkb2kiOm51bGwsInF1YWxpdHlfY2xhc3MiOiJndWlhIGludGVybmFjaW9uYWwgb2ZpY2lhbCIsInZlcmlmaWNhdGlvbl9sZXZlbCI6ImZvbnRlX3ByaW1hcmlhX2NvbmZlcmlkYSIsInZlcmlmaWVkX29uIjoiMjAyNi0wOC0xNyIsImFwYV9mdWxsIjoiU2FsdmFkb3IsIEEuIChFZC4pLiAoMTk5NCkuIEludGVybmF0aW9uYWwgU3RyYXRpZ3JhcGhpYyBHdWlkZTogQSBndWlkZSB0byBzdHJhdGlncmFwaGljIGNsYXNzaWZpY2F0aW9uLCB0ZXJtaW5vbG9neSwgYW5kIHByb2NlZHVyZSAoMm5kIGVkLikuIEludGVybmF0aW9uYWwgVW5pb24gb2YgR2VvbG9naWNhbCBTY2llbmNlcyAmIEdlb2xvZ2ljYWwgU29jaWV0eSBvZiBBbWVyaWNhLiBodHRwczovL3N0cmF0aWdyYXBoeS5vcmcvZ3VpZGUvIn0seyJpZCI6IlJFRi0yNDMiLCJncm91cCI6IkZlcnJhbWVudGFzIGdlb2NpZW50w61maWNhcyDCtyBlc3RyYXRpZ3JhZmlhIiwic3RhdHVzIjoiaW5jb3Jwb3JhZGEiLCJ0eXBlIjoiZXN0cmF0aWdyYWZpYSIsImFwYSI6Ik5vcnRoIEFtZXJpY2FuIENvbW1pc3Npb24gb24gU3RyYXRpZ3JhcGhpYyBOb21lbmNsYXR1cmUuICgyMDA1KS4gTm9ydGggQW1lcmljYW4gU3RyYXRpZ3JhcGhpYyBDb2RlLiBBQVBHIEJ1bGxldGluLCA4OSgxMSksIDE1NDfigJMxNTkxLiBodHRwczovL2RvaS5vcmcvMTAuMTMwNi8wNzA1MDUwNDEyOSIsInVybCI6Imh0dHBzOi8vZG9pLm9yZy8xMC4xMzA2LzA3MDUwNTA0MTI5IiwidXNlIjoiUmVmZXLDqm5jaWEgY29tcGxlbWVudGFyIHBhcmEgbm9tZW5jbGF0dXJhLCBkZWZpbmnDp8OjbyBlIHJlbGHDp8O1ZXMgZW50cmUgdW5pZGFkZXMgZXN0cmF0aWdyw6FmaWNhcy4iLCJjaXRhdGlvbl9zdGFuZGFyZCI6IkFQQSA3IiwiZG9pIjoiMTAuMTMwNi8wNzA1MDUwNDEyOSIsInF1YWxpdHlfY2xhc3MiOiJjw7NkaWdvIGVzdHJhdGlncsOhZmljbyBjaWVudMOtZmljbyIsInZlcmlmaWNhdGlvbl9sZXZlbCI6ImZvbnRlX3ByaW1hcmlhX2NvbmZlcmlkYSIsInZlcmlmaWVkX29uIjoiMjAyNi0wOC0xNyIsImFwYV9mdWxsIjoiTm9ydGggQW1lcmljYW4gQ29tbWlzc2lvbiBvbiBTdHJhdGlncmFwaGljIE5vbWVuY2xhdHVyZS4gKDIwMDUpLiBOb3J0aCBBbWVyaWNhbiBTdHJhdGlncmFwaGljIENvZGUuIEFBUEcgQnVsbGV0aW4sIDg5KDExKSwgMTU0N+KAkzE1OTEuIGh0dHBzOi8vZG9pLm9yZy8xMC4xMzA2LzA3MDUwNTA0MTI5In0=')))
 $m=New-Object IO.MemoryStream;$m.Write($d,0,$p);$m.Write($x,0,$x.Length);$m.Write($d,$p,$d.Length-$p);[IO.File]::WriteAllBytes($path,$m.ToArray());$m.Dispose()
}

$root=Find-Root;$docs=Join-Path $root 'docs';$index=Join-Path $docs 'index.html';$refs=Join-Path $docs 'referencias\referencias.js';$refpage=Join-Path $docs 'referencias\index.html'
if(!(Test-Path (Join-Path $docs 'assets\js\coluna-estratigrafica-v38457.js'))){throw 'A base da Coluna Estratigrafica nao foi encontrada.'}

$stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$backup=Join-Path $root ('backup_CORRELACAO_R1_'+$stamp)
New-Item -ItemType Directory -Path (Join-Path $backup 'referencias') -Force|Out-Null
Copy-Item $index (Join-Path $backup 'index.html') -Force
Copy-Item $refs (Join-Path $backup 'referencias\referencias.js') -Force
Copy-Item $refpage (Join-Path $backup 'referencias\index.html') -Force
Write-Host "Backup criado: $backup" -ForegroundColor Cyan

New-Item -ItemType Directory -Path (Join-Path $docs 'assets\js') -Force|Out-Null
New-Item -ItemType Directory -Path (Join-Path $docs 'assets\css') -Force|Out-Null
New-Item -ItemType Directory -Path (Join-Path $docs 'documentos') -Force|Out-Null
Copy-Item (Join-Path $PSScriptRoot 'payload\assets\js\correlacao-estratigrafica-v1.js') (Join-Path $docs 'assets\js\correlacao-estratigrafica-v1.js') -Force
Copy-Item (Join-Path $PSScriptRoot 'payload\assets\css\correlacao-estratigrafica-v1.css') (Join-Path $docs 'assets\css\correlacao-estratigrafica-v1.css') -Force
Copy-Item (Join-Path $PSScriptRoot 'payload\documentos\metodologia-correlacao-estratigrafica.html') (Join-Path $docs 'documentos\metodologia-correlacao-estratigrafica.html') -Force

# Card and count. Incremental only.
Insert-Before $index ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PGFydGljbGUgY2xhc3M9Iml0YS10b29sLWNhcmQiIGRhdGEtc2VhcmNoPSJjb2x1bmEgZXN0cmF0aWdyYWZpYSBmb3JtYWNhbyBpZGFkZSI+'))) ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PGFydGljbGUgY2xhc3M9Iml0YS10b29sLWNhcmQgaXRhLXRvb2wtZmVhdHVyZWQiIGRhdGEtc2VhcmNoPSJjb3JyZWxhY2FvIGVzdHJhdGlncmFmaWNhIGNvbHVuYXMgcGVyZmlsIGdwcyBsaXRvbG9naWEgYmlvZXN0cmF0aWdyYWZpYSBjcm9ub2VzdHJhdGlncmFmaWEiPjxkaXYgY2xhc3M9Iml0YS10b29sLXRvcCI+PHNwYW4gY2xhc3M9Iml0YS10b29sLWljb24iPuKHhDwvc3Bhbj48c3BhbiBjbGFzcz0iaXRhLXRvb2wtc3RhdHVzIG9wZXJhY2lvbmFsIj5OT1ZPIMK3IE9QRVJBQ0lPTkFMPC9zcGFuPjwvZGl2PjxoND5Db3JyZWxhw6fDo28gRXN0cmF0aWdyw6FmaWNhIMK3IE11bHRpcG9udG88L2g0PjxwPkNvbXBhcmUgZHVhcyBvdSBtYWlzIGNvbHVuYXMsIGRvY3VtZW50ZSBjcml0w6lyaW9zIGUgY29uZmlhbsOnYSwgdmlzdWFsaXplIG9zIHBvbnRvcyBHUFMgbm8gbWFwYSBlIGV4cG9ydGUgbyBwYWluZWwgZGUgY29ycmVsYcOnw6NvLjwvcD48ZGl2IGNsYXNzPSJpdGEtdG9vbC1hY3Rpb25zIj48YnV0dG9uIHR5cGU9ImJ1dHRvbiIgY2xhc3M9ImFjdGlvbi1idG4gcHJpbWFyeSIgZGF0YS10b29sLWFjdGlvbj0iY29ycmVsYWNhb0VzdHJhdGlncmFmaWNhIj5BYnJpcjwvYnV0dG9uPjxidXR0b24gdHlwZT0iYnV0dG9uIiBjbGFzcz0iYWN0aW9uLWJ0biIgZGF0YS10b29sLWFjdGlvbj0iY29ycmVsYWNhb0FqdWRhIj5BanVkYTwvYnV0dG9uPjwvZGl2PjwvYXJ0aWNsZT4K')))
Replace-Literal $index '<span class="ita-tools-count">3</span></summary><div class="ita-tools-grid">' '<span class="ita-tools-count">4</span></summary><div class="ita-tools-grid">'
Insert-Before $index '</head>' ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PGxpbmsgcmVsPSJzdHlsZXNoZWV0IiBocmVmPSIuL2Fzc2V0cy9jc3MvY29ycmVsYWNhby1lc3RyYXRpZ3JhZmljYS12MS5jc3M/dj0xLjAuMCI+')))
Insert-Before $index '</body>' ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PHNjcmlwdCBzcmM9Ii4vYXNzZXRzL2pzL2NvcnJlbGFjYW8tZXN0cmF0aWdyYWZpY2EtdjEuanM/dj0xLjAuMCI+PC9zY3JpcHQ+')))

Append-Refs $refs
$refSections=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('CjxoMSBpZD0iY29ycmVsYWNhby1lc3RyYXRpZ3JhZmljYS1yZWZlcmVuY2lhcyI+Q29ycmVsYcOnw6NvIEVzdHJhdGlncsOhZmljYTwvaDE+CjxwIGNsYXNzPSJzZWN0aW9uLWxlYWQiPlJlZmVyw6puY2lhcyBtZXRvZG9sw7NnaWNhcyBwYXJhIGNvcnJlbGHDp8OjbyBlIGNsYXNzaWZpY2HDp8OjbyBlc3RyYXRpZ3LDoWZpY2EuPC9wPgo8c2VjdGlvbiBjbGFzcz0iZW50cnkgcmVmZXJlbmNlLWVudHJ5IiBpZD0icmVmLTI0MSI+PGgyPlJFRi0yNDE8L2gyPjxkaXYgY2xhc3M9Im1ldGEiPkZlcnJhbWVudGFzIGdlb2NpZW50w61maWNhcyDCtyBlc3RyYXRpZ3JhZmlhIMK3IEFQQSA3PC9kaXY+PGRpdiBjbGFzcz0ic291cmNlIj5NdXJwaHksIE0uIEEuLCAmYW1wOyBTYWx2YWRvciwgQS4gKDE5OTkpLiBJbnRlcm5hdGlvbmFsIFN0cmF0aWdyYXBoaWMgR3VpZGXigJRBbiBhYnJpZGdlZCB2ZXJzaW9uLiBFcGlzb2RlcywgMjIoNCksIDI1NeKAkzI3MS4gaHR0cHM6Ly9kb2kub3JnLzEwLjE4ODE0L2VwaWl1Z3MvMTk5OS92MjJpNC8wMDIgPGEgaHJlZj0iaHR0cHM6Ly9kb2kub3JnLzEwLjE4ODE0L2VwaWl1Z3MvMTk5OS92MjJpNC8wMDIiIHJlbD0ibm9vcGVuZXIiIHRhcmdldD0iX2JsYW5rIj5mb250ZTwvYT48L2Rpdj48cD5QcmluY8OtcGlvcyBkZSBjbGFzc2lmaWNhw6fDo28sIHRlcm1pbm9sb2dpYSwgY29ycmVsYcOnw6NvIGUgY29tdW5pY2HDp8OjbyBlc3RyYXRpZ3LDoWZpY2EgdXNhZG9zIG5hIGFqdWRhIG1ldG9kb2zDs2dpY2EgZGEgQ29ycmVsYcOnw6NvIEVzdHJhdGlncsOhZmljYS48L3A+PC9zZWN0aW9uPgo8c2VjdGlvbiBjbGFzcz0iZW50cnkgcmVmZXJlbmNlLWVudHJ5IiBpZD0icmVmLTI0MiI+PGgyPlJFRi0yNDI8L2gyPjxkaXYgY2xhc3M9Im1ldGEiPkZlcnJhbWVudGFzIGdlb2NpZW50w61maWNhcyDCtyBlc3RyYXRpZ3JhZmlhIMK3IEFQQSA3PC9kaXY+PGRpdiBjbGFzcz0ic291cmNlIj5TYWx2YWRvciwgQS4gKEVkLikuICgxOTk0KS4gSW50ZXJuYXRpb25hbCBTdHJhdGlncmFwaGljIEd1aWRlOiBBIGd1aWRlIHRvIHN0cmF0aWdyYXBoaWMgY2xhc3NpZmljYXRpb24sIHRlcm1pbm9sb2d5LCBhbmQgcHJvY2VkdXJlICgybmQgZWQuKS4gSW50ZXJuYXRpb25hbCBVbmlvbiBvZiBHZW9sb2dpY2FsIFNjaWVuY2VzICZhbXA7IEdlb2xvZ2ljYWwgU29jaWV0eSBvZiBBbWVyaWNhLiBodHRwczovL3N0cmF0aWdyYXBoeS5vcmcvZ3VpZGUvIDxhIGhyZWY9Imh0dHBzOi8vc3RyYXRpZ3JhcGh5Lm9yZy9ndWlkZS8iIHJlbD0ibm9vcGVuZXIiIHRhcmdldD0iX2JsYW5rIj5mb250ZTwvYT48L2Rpdj48cD5HdWlhIGludGVybmFjaW9uYWwgZGUgcmVmZXLDqm5jaWEgcGFyYSBjbGFzc2lmaWNhw6fDo28sIHRlcm1pbm9sb2dpYSBlIHByb2NlZGltZW50b3MgZXN0cmF0aWdyw6FmaWNvcy48L3A+PC9zZWN0aW9uPgo8c2VjdGlvbiBjbGFzcz0iZW50cnkgcmVmZXJlbmNlLWVudHJ5IiBpZD0icmVmLTI0MyI+PGgyPlJFRi0yNDM8L2gyPjxkaXYgY2xhc3M9Im1ldGEiPkZlcnJhbWVudGFzIGdlb2NpZW50w61maWNhcyDCtyBlc3RyYXRpZ3JhZmlhIMK3IEFQQSA3PC9kaXY+PGRpdiBjbGFzcz0ic291cmNlIj5Ob3J0aCBBbWVyaWNhbiBDb21taXNzaW9uIG9uIFN0cmF0aWdyYXBoaWMgTm9tZW5jbGF0dXJlLiAoMjAwNSkuIE5vcnRoIEFtZXJpY2FuIFN0cmF0aWdyYXBoaWMgQ29kZS4gQUFQRyBCdWxsZXRpbiwgODkoMTEpLCAxNTQ34oCTMTU5MS4gaHR0cHM6Ly9kb2kub3JnLzEwLjEzMDYvMDcwNTA1MDQxMjkgPGEgaHJlZj0iaHR0cHM6Ly9kb2kub3JnLzEwLjEzMDYvMDcwNTA1MDQxMjkiIHJlbD0ibm9vcGVuZXIiIHRhcmdldD0iX2JsYW5rIj5mb250ZTwvYT48L2Rpdj48cD5SZWZlcsOqbmNpYSBjb21wbGVtZW50YXIgcGFyYSBub21lbmNsYXR1cmEsIGRlZmluacOnw6NvIGUgcmVsYcOnw7VlcyBlbnRyZSB1bmlkYWRlcyBlc3RyYXRpZ3LDoWZpY2FzLjwvcD48L3NlY3Rpb24+Cg=='))
$refRaw=Get-Content $refpage -Raw -Encoding UTF8
if($refRaw -notmatch 'REF-241'){
  if($refRaw.Contains('</main>')){ Insert-Before $refpage '</main>' $refSections }
  elseif($refRaw.Contains('</body>')){ Insert-Before $refpage '</body>' $refSections }
  elseif($refRaw.Contains('</html>')){ Insert-Before $refpage '</html>' $refSections }
  else{
    Add-Content -Path $refpage -Value $refSections -Encoding UTF8
  }
}

$raw=Get-Content $index -Raw -Encoding UTF8
if($raw -notmatch 'correlacaoEstratigrafica' -or $raw -notmatch 'correlacao-estratigrafica-v1.js'){throw 'Falha de validacao no index.'}
$r=Get-Content $refs -Raw -Encoding UTF8
if($r -notmatch 'REF-241' -or $r -notmatch 'REF-243'){throw 'Falha de validacao das referencias.'}

Write-Host 'OK - Correlação Estratigráfica adicionada à Bancada Digital.' -ForegroundColor Green
Write-Host 'OK - interface responsiva para desktop, tablet e celular vertical.' -ForegroundColor Green
Write-Host 'OK - importação de colunas JSON e coluna atual habilitada.' -ForegroundColor Green
Write-Host 'OK - correlação manual documentada com critério e confiança.' -ForegroundColor Green
Write-Host 'OK - mapa com pontos GPS e ordem espacial do perfil.' -ForegroundColor Green
Write-Host 'OK - exportação JSON, CSV e SVG.' -ForegroundColor Green
Write-Host 'OK - Ajuda e Ciência e metodologia APA 7 incorporadas.' -ForegroundColor Green
Write-Host 'OK - REF-241 a REF-243 adicionadas sem substituir o registro mestre.' -ForegroundColor Green
Write-Host 'OK - bibliografia estatica usa ancora tolerante main/body/html.' -ForegroundColor Green
Write-Host 'OK - index.html alterado somente por inserções incrementais.' -ForegroundColor Green
Write-Host 'Depois use Ctrl+F5.' -ForegroundColor Yellow