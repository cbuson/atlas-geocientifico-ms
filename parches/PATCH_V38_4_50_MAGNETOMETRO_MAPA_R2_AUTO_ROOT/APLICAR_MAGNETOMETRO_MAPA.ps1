$ErrorActionPreference = 'Stop'

Write-Host 'ITA ARANDU MS · PATCH Magnetometro Mapa R2' -ForegroundColor Cyan
Write-Host 'Localizando automaticamente a pasta docs...' -ForegroundColor DarkCyan

function Find-ItaDocsRoot {
    param([string]$StartPath)

    $current = (Resolve-Path $StartPath).Path
    for($i = 0; $i -lt 8; $i++) {
        $directIndex = Join-Path $current 'index.html'
        if(Test-Path $directIndex) {
            $txt = Get-Content $directIndex -Raw -ErrorAction SilentlyContinue
            if($txt -match 'magnetometro-amostras-v38450') {
                return $current
            }
        }

        $docs = Join-Path $current 'docs'
        $docsIndex = Join-Path $docs 'index.html'
        if(Test-Path $docsIndex) {
            $txt = Get-Content $docsIndex -Raw -ErrorAction SilentlyContinue
            if($txt -match 'magnetometro-amostras-v38450') {
                return $docs
            }
        }

        $parent = Split-Path $current -Parent
        if([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) { break }
        $current = $parent
    }
    return $null
}

$root = Find-ItaDocsRoot -StartPath $PSScriptRoot
if(-not $root) {
    throw 'Nao foi encontrada uma pasta docs com a base V38.4.50 Magnetometro Amostras. Nada foi alterado.'
}

Write-Host ('Raiz detectada · ' + $root) -ForegroundColor Green
$index = Join-Path $root 'index.html'
$txt = Get-Content $index -Raw
if($txt -notmatch 'magnetometro-amostras-v38450') {
    throw 'Base V38.4.50 Magnetometro Amostras nao detectada. Nada foi alterado.'
}

$src = Join-Path $PSScriptRoot 'files'
if(!(Test-Path (Join-Path $src 'index.html'))) {
    throw 'Arquivo do patch ausente · files\index.html'
}
if(!(Test-Path (Join-Path $src 'service-worker.js'))) {
    throw 'Arquivo do patch ausente · files\service-worker.js'
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = Join-Path $root ('.backup_mag_mapa_' + $stamp)
New-Item -ItemType Directory -Path $backup | Out-Null
Copy-Item $index (Join-Path $backup 'index.html') -Force
$sw = Join-Path $root 'service-worker.js'
if(Test-Path $sw) {
    Copy-Item $sw (Join-Path $backup 'service-worker.js') -Force
}

# Copia apenas componentes que realmente existam no patch.
foreach($folderName in @('assets','documentos','referencias')) {
    $folder = Join-Path $src $folderName
    if(Test-Path $folder) {
        Copy-Item $folder $root -Recurse -Force
    }
}

Copy-Item (Join-Path $src 'index.html') $index -Force
Copy-Item (Join-Path $src 'service-worker.js') $sw -Force

$installed = Get-Content $index -Raw
if($installed -notmatch 'magnetometro-mapa-v38451') {
    Write-Warning 'Os arquivos foram copiados, mas o marcador final nao foi localizado. Verifique a instalacao.'
} else {
    Write-Host 'OK · Magnetometro Mapa instalado · V38.4.51' -ForegroundColor Green
}
Write-Host ('Backup · ' + $backup) -ForegroundColor DarkGray
Write-Host 'Pode fechar esta janela e testar a Bancada Digital.' -ForegroundColor Cyan
