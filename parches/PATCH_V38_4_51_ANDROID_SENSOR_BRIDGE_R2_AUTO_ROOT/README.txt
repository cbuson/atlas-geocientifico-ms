ITA ARANDU MS - PONTE NATIVA ANDROID - R2

Correcao do instalador para Windows PowerShell 5.1.
O R1 podia falhar na validacao por causa de caracteres acentuados interpretados com codificacao diferente.
O R2 usa identificadores ASCII estaveis, detecta automaticamente a pasta docs, cria backup antes da alteracao e verifica ItaSensors depois da copia.

Instalacao
1. Extraia esta pasta dentro de atlas-geocientifico-ms\parches
2. Abra PowerShell nesta pasta
3. Execute
   Set-ExecutionPolicy -Scope Process Bypass
   .\APLICAR_PONTE_SENSOR_ANDROID.ps1

Nao e necessario informar a pasta docs.
