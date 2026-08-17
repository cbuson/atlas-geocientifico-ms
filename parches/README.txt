ITA ARANDU MS · PATCH V38.4.56 → V38.4.57
Biblioteca completa FGDC Section 37 para Coluna Estratigráfica

Este instalador valida a base V38.4.56, prepara os 117 padrões litológicos das séries 600 e 700 e só altera docs depois de completar a biblioteca em área de staging.

Os 15 padrões já presentes na V38.4.56 são reutilizados. Os demais SVG são obtidos do repositório aberto davenquinn/geologic-patterns, que documenta a extração da biblioteca FGDC para web.

Executar no PowerShell 5.1 ou superior
Set-ExecutionPolicy -Scope Process Bypass
.\APLICAR_BIBLIOTECA_FGDC_COMPLETA.ps1

O script detecta automaticamente a pasta docs quando está dentro de atlas-geocientifico-ms\parches.
