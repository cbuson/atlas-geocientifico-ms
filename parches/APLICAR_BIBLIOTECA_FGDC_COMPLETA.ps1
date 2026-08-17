$ErrorActionPreference = 'Stop'

function Find-DocsRoot {
    param([string]$Start)
    $candidates = @(
        (Join-Path $Start 'docs'),
        (Join-Path (Split-Path $Start -Parent) 'docs'),
        (Join-Path (Split-Path (Split-Path $Start -Parent) -Parent) 'docs'),
        (Join-Path (Split-Path (Split-Path (Split-Path $Start -Parent) -Parent) -Parent) 'docs')
    )
    foreach($c in $candidates){
        if((Test-Path (Join-Path $c 'index.html')) -and (Test-Path (Join-Path $c 'service-worker.js'))){ return (Resolve-Path $c).Path }
    }
    throw 'Nao foi possivel localizar automaticamente a pasta docs.'
}

function Assert-Hash {
    param([string]$Path,[string]$Expected)
    if(-not (Test-Path $Path)){ throw "Arquivo base ausente: $Path" }
    $got=(Get-FileHash -Algorithm SHA256 $Path).Hash.ToLowerInvariant()
    if($got -ne $Expected.ToLowerInvariant()){ throw "BASE NAO COINCIDE COM V38.4.56: $Path`nEsperado $Expected`nObtido   $got`nNenhum arquivo foi alterado." }
}

$docs = Find-DocsRoot -Start $PSScriptRoot
Write-Host "Raiz detectada: $docs"

Assert-Hash (Join-Path $docs 'index.html') '47807b2e29e821985647dbae8800adb8eb14bddd211d30b2e8c2b005a395d5e0'
Assert-Hash (Join-Path $docs 'service-worker.js') '6da114117d2a884f9c1e12e2538d20f91431c893c7bf5430c6c01ce91b651c2a'
Assert-Hash (Join-Path $docs 'assets\js\coluna-estratigrafica-v38456.js') 'b1b4e7aaa20ce3701f40f50a21d87ab1de5098881abb227714ac17f25b73af63'
Assert-Hash (Join-Path $docs 'assets\css\coluna-estratigrafica-v38456.css') 'ab9b2faa8581dea52a895f90573f9714c93e25a0fdf85f8d1fdbb64ce6f94d97'
Assert-Hash (Join-Path $docs 'documentos\metodologia-coluna-estratigrafica.html') 'f84baa8bffa88543e3b0fa26dee13ccee3fa95720312a4782c647a4d90ce8883'
Write-Host 'OK - base V38.4.56 validada.'

$stage=Join-Path $PSScriptRoot '_stage_fgdc_v38457'
if(Test-Path $stage){Remove-Item $stage -Recurse -Force}
New-Item $stage -ItemType Directory | Out-Null
$stagePatterns=Join-Path $stage 'patterns'
New-Item $stagePatterns -ItemType Directory | Out-Null

# Reutiliza os vetores já incorporados na V38.4.56
$existing=Join-Path $docs 'assets\padroes\fgdc'
if(Test-Path $existing){Get-ChildItem $existing -Filter '*.svg' | Copy-Item -Destination $stagePatterns}

$codes=Get-Content (Join-Path $PSScriptRoot 'CODIGOS_FGDC.txt')
$toDownload=Get-Content (Join-Path $PSScriptRoot 'CODIGOS_FGDC_BAIXAR.txt')
$baseUrl='https://raw.githubusercontent.com/davenquinn/geologic-patterns/master/assets/svg'
Write-Host "Preparando biblioteca FGDC completa. Downloads pendentes: $($toDownload.Count)"
$i=0
foreach($code in $toDownload){
    $i++
    $out=Join-Path $stagePatterns ($code+'.svg')
    $url=$baseUrl+'/'+$code+'.svg'
    $ok=$false
    for($attempt=1;$attempt -le 3 -and -not $ok;$attempt++){
        try{
            Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $out -TimeoutSec 45
            if((Get-Item $out).Length -lt 100){throw 'SVG muito pequeno'}
            $bytes=[System.IO.File]::ReadAllBytes($out)
            $txt=[System.Text.Encoding]::UTF8.GetString($bytes)
            if($txt -notmatch '<svg'){throw 'Conteudo nao parece SVG'}
            $ok=$true
        }catch{
            if(Test-Path $out){Remove-Item $out -Force}
            if($attempt -eq 3){throw "Falha ao obter FGDC $code apos 3 tentativas. Nenhum arquivo do site foi alterado. URL $url"}
            Start-Sleep -Seconds 2
        }
    }
    if(($i % 10) -eq 0 -or $i -eq $toDownload.Count){Write-Host "  $i / $($toDownload.Count) padrões adicionais preparados"}
}

$present=@(Get-ChildItem $stagePatterns -Filter '*.svg' | ForEach-Object {$_.BaseName} | Sort-Object -Unique)
$missing=@($codes | Where-Object {$_ -notin $present})
if($missing.Count -gt 0){throw "Biblioteca incompleta no staging. Faltam: $($missing -join ', ')"}
if($present.Count -ne 117){throw "Contagem inesperada no staging: $($present.Count), esperado 117."}
Write-Host 'OK - 117 SVG preparados e validados antes de alterar docs.'

$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$backup=Join-Path (Split-Path $docs -Parent) ("backup_V38_4_56_antes_FGDC_COMPLETA_"+$stamp)
New-Item $backup -ItemType Directory | Out-Null
Copy-Item (Join-Path $docs 'index.html') $backup
Copy-Item (Join-Path $docs 'service-worker.js') $backup
Copy-Item (Join-Path $docs 'assets\js\coluna-estratigrafica-v38456.js') $backup
Copy-Item (Join-Path $docs 'assets\css\coluna-estratigrafica-v38456.css') $backup
Copy-Item (Join-Path $docs 'documentos\metodologia-coluna-estratigrafica.html') $backup
if(Test-Path $existing){Copy-Item $existing (Join-Path $backup 'fgdc') -Recurse}
Write-Host "Backup criado: $backup"

$payload=Join-Path $PSScriptRoot 'payload'
Copy-Item (Join-Path $payload 'index.html') (Join-Path $docs 'index.html') -Force
Copy-Item (Join-Path $payload 'service-worker.js') (Join-Path $docs 'service-worker.js') -Force
Copy-Item (Join-Path $payload 'assets\js\coluna-estratigrafica-v38457.js') (Join-Path $docs 'assets\js\coluna-estratigrafica-v38457.js') -Force
Copy-Item (Join-Path $payload 'assets\css\coluna-estratigrafica-v38457.css') (Join-Path $docs 'assets\css\coluna-estratigrafica-v38457.css') -Force
Copy-Item (Join-Path $payload 'documentos\metodologia-coluna-estratigrafica.html') (Join-Path $docs 'documentos\metodologia-coluna-estratigrafica.html') -Force
Copy-Item (Join-Path $payload 'documentos\CHANGELOG_V38_4_57.md') (Join-Path $docs 'documentos\CHANGELOG_V38_4_57.md') -Force
New-Item (Join-Path $docs 'assets\padroes\fgdc') -ItemType Directory -Force | Out-Null
Copy-Item (Join-Path $stagePatterns '*.svg') (Join-Path $docs 'assets\padroes\fgdc') -Force
Copy-Item (Join-Path $payload 'assets\padroes\fgdc\manifest-section37.json') (Join-Path $docs 'assets\padroes\fgdc\manifest-section37.json') -Force

$final=@(Get-ChildItem (Join-Path $docs 'assets\padroes\fgdc') -Filter '*.svg' | Where-Object {$_.BaseName -in $codes})
if($final.Count -ne 117){throw "Instalacao terminou com contagem incorreta de padrões: $($final.Count)"}

# UTF-8 estrito, somente leitura
$utf8 = New-Object System.Text.UTF8Encoding($false,$true)
foreach($f in @('index.html','service-worker.js','assets\js\coluna-estratigrafica-v38457.js','assets\css\coluna-estratigrafica-v38457.css','documentos\metodologia-coluna-estratigrafica.html')){
    [void]$utf8.GetString([System.IO.File]::ReadAllBytes((Join-Path $docs $f)))
}
Remove-Item $stage -Recurse -Force
Write-Host ''
Write-Host 'OK - ITA ARANDU MS V38.4.57 instalado.'
Write-Host 'OK - 117 padrões FGDC Section 37 armazenados localmente.'
Write-Host 'OK - PWA preparada para precache integral da biblioteca litológica.'
Write-Host 'OK - UTF-8 validado sem reescrever arquivos de texto.'
