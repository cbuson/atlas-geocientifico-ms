# Teste de aceitação · V38.4.59 FIELD ROBUSTNESS

Executar em HTTPS no dispositivo real antes de congelar a release.

1. Instalar/abrir ITA ARANDU MS e entrar em **Campo**.
2. Tocar **Preparar saída offline** e aguardar **Pronto para campo offline ✓**.
3. Verificar o indicador de armazenamento e solicitar persistência quando suportada.
4. Criar uma estação; registrar observação, litologia, uma medida, uma amostra e pelo menos uma fotografia.
5. **Não salvar a estação.** Fechar completamente o navegador/PWA.
6. Reabrir. Confirmar mensagem **Estação não finalizada recuperada** e verificar que texto, medida, amostra e fotografia continuam presentes.
7. Salvar a estação. Fechar e reabrir. Confirmar que a estação está em **Estações locais**.
8. Exportar **JSON, GeoJSON, KML e Pacote completo ZIP**. Abrir o ZIP e confirmar a presença do original fotográfico.
9. Ativar **modo avião**, fechar a PWA e reabrir. Confirmar abertura do shell, Campo, geologia regional, limites/municípios e malhas 250/500/1000 km².
10. Em modo avião, criar uma segunda estação, salvá-la, fechar/reabrir e exportá-la.
11. Confirmar que serviços conectados são identificados como indisponíveis/offline e não simulam dados.
12. Reativar a rede e usar **Verificar pacote** novamente.

### Critério de aceitação
A release só deve ser congelada para o artigo se os passos 1–12 forem concluídos sem perda de dados de campo. Qualquer falha deve ser registrada com dispositivo, SO, navegador, hora e etapa.
