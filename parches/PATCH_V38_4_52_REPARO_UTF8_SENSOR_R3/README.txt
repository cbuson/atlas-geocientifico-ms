ITA ARANDU MS - REPARO UTF8 + SENSOR R3

Corrige a codificacao quebrada produzida pelo patch R2 no Windows PowerShell 5.1 e restaura os textos UTF-8 originais.
Tambem preserva a ponte ItaSensors nos dois magnetometros.

Instalacao
1. Coloque esta pasta em atlas-geocientifico-ms\parches
2. Abra PowerShell nesta pasta
3. Execute
   Set-ExecutionPolicy -Scope Process Bypass
   .\APLICAR_REPARO_UTF8_SENSOR.ps1

Depois publique as alteracoes no GitHub Pages.
