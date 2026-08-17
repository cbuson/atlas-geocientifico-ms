ITA ARANDU MS - PATCH V38.4.53 -> V38.4.54
DIAGRAMA DE ROSAS - DIRECOES

1. Descompacte esta pasta dentro de atlas-geocientifico-ms\parches
2. Abra PowerShell nesta pasta
3. Execute
   Set-ExecutionPolicy -Scope Process Bypass
   .\APLICAR_DIAGRAMA_ROSAS.ps1

O instalador valida SHA256 da base antes de alterar qualquer arquivo.
Nao usa Get-Content ou Set-Content sobre index.html.
Cria backup automatico antes de copiar os arquivos.
