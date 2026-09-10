# Auditoria V38.4.58D · Catálogo evolutivo

Data: 2026-09-10

## Objetivo

Separar explicitamente os recursos operacionais da versão atual das fontes identificadas para expansão futura, sem adicionar camadas, ferramentas ou resultados científicos.

## Resultado

- Catálogo preservado: **190 itens**.
- Disponíveis nesta versão: **126** (`incorporada`, `conectada` ou `derivada em sessão`).
- Expansão futura documentada: **64**.
- Arquivos científicos comparados com V38.4.58C: **120**.
- Arquivos científicos alterados: **0**.
- JavaScript verificado por `node --check`: **44 arquivos + service-worker**.
- Erros de sintaxe JavaScript: **0**.
- JSON verificados: **176**.
- Erros JSON: **0**.
- IDs HTML duplicados: **0**.
- Referências estáticas locais ausentes no `index.html`: **0**.

## Mudanças de interface

1. Cada grupo mostra `X disponíveis · Y em desenvolvimento`.
2. Camadas operacionais aparecem em **Disponível nesta versão** com controle de ativação.
3. Fontes futuras aparecem em **Expansão futura**, em bloco recolhível, sem checkbox de ativação.
4. `CAPTURA` passa a ser exibido como **FONTE IDENTIFICADA**.
5. `EM AVALIAÇÃO` e `PLANEJADA` permanecem explicitamente não operacionais.
6. Produtos com estado `derivada` calculáveis em sessão passam a ser reconhecidos como operacionais e identificados como **DERIVADA EM SESSÃO**.
7. O painel **Dados** usa a mesma semântica e separa recurso atual de expansão futura.
8. A cabeceira identifica o Atlas como **versão operacional em evolução**.

## Preservação científica

O objeto `CATALOG` de V38.4.58C e V38.4.58D é idêntico. Nenhum item foi adicionado, removido ou teve status científico alterado. Os arquivos GeoJSON, JSON e CSV científicos auditados permanecem byte a byte idênticos.

## Limite da auditoria

O ambiente de execução bloqueia navegação headless para `localhost`. A verificação visual final deve ser realizada após publicação no navegador real.
