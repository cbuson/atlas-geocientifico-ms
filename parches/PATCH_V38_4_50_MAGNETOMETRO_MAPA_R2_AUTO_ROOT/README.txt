ITA ARANDU MS · PATCH V38.4.50 → V38.4.51
MAGNETOMETRO · MAPA · R2 AUTO ROOT

Este instalador foi corrigido para uso dentro da pasta parches do repositorio.
Ele procura automaticamente a pasta docs da aplicacao.

INSTALACAO
1. Extraia esta pasta dentro de atlas-geocientifico-ms\parches\
2. Abra PowerShell DENTRO desta pasta do patch.
3. Execute

   Set-ExecutionPolicy -Scope Process Bypass
   .\APLICAR_MAGNETOMETRO_MAPA.ps1

NAO escreva novamente o nome da pasta PATCH antes do script se o PowerShell ja estiver dentro dela.

O instalador
- localiza docs automaticamente
- confirma a base V38.4.50 Magnetometro Amostras
- cria backup de index.html e service-worker.js
- aplica apenas os arquivos existentes no patch
- valida o marcador da V38.4.51

Se a base correta nao for encontrada, o instalador para sem alterar a aplicacao.
