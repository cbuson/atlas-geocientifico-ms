# Auditoria V38.4.59 · FIELD ROBUSTNESS

## Escopo
Release de robustez de campo construída sobre V38.4.58D. Nenhuma camada científica, regra analítica, índice ou resultado territorial foi alterado.

## Mudanças funcionais
- Campo Master 2.1 é a única caderneta ativa no runtime. O banco legado `ita_arandu_campo_v01` é lido apenas para migração conservadora e não é apagado.
- Rascunho completo persistido no IndexedDB do Campo Master, incluindo fotografias como Blob, amostras, medidas, estruturas, croquis, GPS e orientação.
- Recuperação automática de estação não finalizada após recarga/fechamento.
- Monitor de armazenamento com `navigator.storage.estimate()` e solicitação opcional de persistência com `navigator.storage.persist()`.
- Modo Expedição com pacote Essencial de Campo explicitamente baixável e verificável antes da saída.
- O pacote obrigatório contém 10 recursos locais (6.48 MB); os 5 recursos Leaflet externos são cache opcional e não bloqueiam o estado “pronto para campo offline”.
- Cache de expedição preservado na ativação do service worker V38.4.59.
- A lógica UX-CAMPO-02 foi removida do runtime de `app.js`, eliminando listeners e bancos concorrentes.

## Verificação estática
- Arquivos científicos comparados: **132**
- Arquivos científicos alterados: **0**
- JavaScript ativo verificado por `node --check`: **52**, falhas: **0**
- JSON analisados: **179**, falhas: **0**
- IDs HTML duplicados: **0**
- Referências locais ausentes em `index.html`: **0**
- Entradas do núcleo PWA: **233**, ausentes: **0**, tamanho local aproximado: **9.54 MB**

## Limite da auditoria automatizada
O Chromium headless do ambiente de execução bloqueou navegação para localhost por política administrativa. Portanto, a prova interativa final deve ser executada após publicação em navegador real. O checklist de aceitação está em `TESTE_CAMPO_V38_4_59.md`.

## Fronteiras declaradas
- Serviços `CONECTADA` continuam dependentes de rede se não houver snapshot local.
- Tiles de mapa-base externos não fazem parte do pacote offline obrigatório.
- Quota e persistência são decisões do navegador/SO; o sistema as mede e avisa, mas não pode garantir uma quota fixa.
- Não há sincronização obrigatória com servidor central; a arquitetura permanece local-first e usa exportação explícita/ZIP como cópia transferível.
