$ErrorActionPreference = "Stop"
Write-Host "ITA ARANDU MS - REDE ESTEREOGRAFICA V38.4.55" -ForegroundColor Cyan
$PatchDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Resolve-Path (Join-Path $PatchDir "..\..")
$Docs = Join-Path $Repo "docs"
if (!(Test-Path (Join-Path $Docs "index.html"))) { throw "Pasta docs nao encontrada." }
function SHA($p) { (Get-FileHash -Algorithm SHA256 $p).Hash.ToLower() }
if ((SHA (Join-Path $Docs "index.html")) -ne "c05d400a061a904252f48720c6318b9d072ef98e5947bc9bbdfd95686580293d" -or (SHA (Join-Path $Docs "referencias\referencias.js")) -ne "d99b77ca6cd0b268ef565b6bc9cfe8c552ef91d5179d57775d057d0d08c04d76") { throw "Base diferente do docs(3) V38.4.54 recebido. Nenhum arquivo foi alterado." }
$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$backup=Join-Path $Repo ("backup_REDE_ESTEREOGRAFICA_"+$stamp)
Copy-Item $Docs $backup -Recurse
Write-Host "Backup criado em $backup" -ForegroundColor Green
$payload=Join-Path $PatchDir "payload"
Get-ChildItem $payload -Recurse -File | ForEach-Object { $rel=$_.FullName.Substring($payload.Length).TrimStart('\'); $dest=Join-Path $Docs $rel; New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null; [System.IO.File]::WriteAllBytes($dest,[System.IO.File]::ReadAllBytes($_.FullName)) }
Write-Host "OK - Rede Estereografica V38.4.55 instalada sem recodificar HTML." -ForegroundColor Green
