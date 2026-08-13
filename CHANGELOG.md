# V35 Beta · repositório modular e camadas separadas · 2026-08-13

- 26 camadas válidas convertidas em arquivos GeoJSON independentes
- `index.html` reduzido a ponto de entrada
- removido o grande `ATLAS_DATA` do HTML e do carregamento direto
- cobertura cartográfica do IMC separada do código
- carregamento local sob demanda
- catálogo público de arquivos
- 2 snapshots compactados herdados detectados com falha de integridade e retirados do estado incorporado
- blobs problemáticos preservados para auditoria e futura reconstrução
- PWA adaptada à arquitetura modular

# V34 Beta · repositório modular · 2026-08-13

- `docs/index.html` convertido em ponto de entrada leve
- CSS extraído para `docs/assets/css`
- lógica da aplicação extraída para `docs/assets/js`
- dados do atlas extraídos para `docs/dados`
- referências extraídas para `docs/referencias`
- IMC e snapshot expostos em `docs/indices`
- camadas compactadas e cobertura cartográfica expostas em `docs/camadas`
- documentos públicos expostos em `docs/documentos`
- PWA atualizada para a nova estrutura

# Changelog

## V33 Beta PWA · 2026-08-13

- preserva o IMC V32 por interseção areal exata
- adiciona PWA instalável
- adiciona botão de instalação em Ajuda
- adiciona manifest, service worker e ícones
- prepara o fluxo Android Trusted Web Activity sem inventar package id, certificado ou Digital Asset Links
- adiciona instruções de primeira publicação no GitHub Desktop

# CHANGELOG V32

- IMC 250, 500 e 1000 km² materializados localmente
- removida a dependência do cálculo dinâmico 7 × 7 para o IMC operacional
- substituída a aproximação por interseção areal exata em projeção Lambert Azimutal Equal-Area
- base geológica estadual 1:1.000.000 preservada como nível mínimo de conhecimento cartográfico
- incorporadas quatro folhas PLGB 1:250.000 com código cartográfico verificado
- incorporadas nove folhas 1:100.000 com código cartográfico verificado
- escala mais detalhada prevalece nas áreas de sobreposição
- adicionada a camada local `Escala e recência do mapeamento geológico` com as 13 coberturas detalhadas usadas no cálculo
- fichas IMC passam a informar percentuais por escala e folhas de suporte
- projetos detalhados conhecidos sem geometria exata materializada permanecem marcados como pendentes e não são imputados
- IPG da V31 preservado
