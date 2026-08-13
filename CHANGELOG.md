# PATCH 07 · correção de tela e responsividade móvel · 2026-08-13

- cabeçalho ajustado para evitar excesso de altura e distorção visual do ícone
- faixa científica encurtada e truncada em uma linha para não invadir o mapa
- descrição institucional compactada em resoluções menores
- correções de largura e overflow horizontal no modal Dados
- painel Dados reorganizado em telas pequenas para não ultrapassar a largura do celular
- linhas de grupos agora quebram corretamente em mobile
- cache da PWA atualizado

# PATCH 06 · identidade visual reforçada e reconhecimento institucional · 2026-08-13

- patch cumulativo que preserva o novo ícone da aplicação
- cabeçalho atualizado com o ícone oficial da PWA
- selo visual de reconhecimento aos povos originários
- subtítulo institucional com ênfase no conhecimento local e ancestral do território
- faixa científica superior atualizada com esse reconhecimento
- ajustes responsivos do cabeçalho e da PWA
- cache da PWA atualizado

# PATCH 05 · ícone da aplicação e reconhecimento aos povos originários · 2026-08-13

- novo ícone geocientífico da aplicação com hexágono e símbolo de informação
- atualização dos arquivos icon-192, icon-512 e icon-maskable-512
- favicon adicionado
- manifest atualizado
- texto de Ajuda reforçado com a importância do conhecimento local e ancestral
- descrição do Projeto ampliada com reconhecimento aos povos originários
- seção Nome do projeto refinada para explicitar esse reconhecimento com cautela metodológica
- cache da PWA atualizado

# PATCH 04 · motor analítico multiescalar completo · 2026-08-13

- painel Pesquisa reorganizado como motor analítico multiescalar
- 12 famílias de índices exibidas em cartões visuais
- 36 camadas analíticas explicitadas em 250, 500 e 1000 km²
- estado de cada índice lido dinamicamente do catálogo
- distinção visual entre incorporado, parcial e planejado
- acesso direto à bibliografia específica de cada índice
- manutenção das fórmulas completas e regras científicas existentes
- cache da PWA atualizado

# PATCH 03 · Dados estatísticos completos e visuais · 2026-08-13

- painel Dados redesenhado como dashboard visual
- métricas dinâmicas de catálogo, estados, grupos, arquivos locais e bibliografia
- gráfico circular do estado do catálogo
- barras empilhadas por grupo geocientífico
- cartões das três malhas analíticas
- painel visual dos 12 índices multiescalares
- bloco de rastreabilidade científica
- estrutura para estatísticas públicas de uso e visitas
- integração opcional e separada com GoatCounter
- nenhum número de visitantes é simulado quando o serviço não está configurado
- cache da PWA atualizado

# PATCH 02 · bibliografia acadêmica por camada e índice · 2026-08-13

- registro mestre normalizado em APA 7 com metadados de qualidade e verificação
- correção da referência do mapa geológico estadual de 2006 segundo o RIGeo
- correção da referência do Mapa do Conhecimento Geológico de Corumbá de 2026 segundo o RIGeo
- correção do PlanGeo 2025–2034 para a autoria e o ano bibliográfico de 2024 registrados pelo SGB
- incorporação da referência científica atual da International Chronostratigraphic Chart, Cohen et al. 2025
- incorporação da fonte oficial ANAC para aeródromos
- vínculo bibliográfico explícito em todas as camadas do catálogo
- bibliografia metodológica e de fontes estruturantes reforçada nos 12 índices multiescalares
- página pública `docs/referencias/index.html` com bibliografia por camada e por índice
- matriz auditável `docs/referencias/bibliografia-camadas-indices.json`
- cada cartão de camada passa a oferecer acesso direto à sua bibliografia
- exportação CSV ampliada com DOI, classe de qualidade e nível de verificação
- cache da PWA atualizado para distribuir a revisão bibliográfica

# PATCH 01 · unificação pt-BR · 2026-08-13

- interface e textos operacionais revisados para português do Brasil
- corrigido trecho misto espanhol-português em Tectônica e estruturas
- cache da PWA atualizado para propagar a correção aos dispositivos instalados
- metadado de versão atualizado para `V35-beta-camadas-separadas-patch01-ptbr`

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
