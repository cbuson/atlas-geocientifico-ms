# V38.4.9 · 2026-08-14 · ICP Caracterização Petrográfica

- materializa o snapshot local da camada Petrografia do Serviço Geológico do Brasil para Mato Grosso do Sul
- calcula ICP de forma independente em 250, 500 e 1000 km²
- congela `ICP_h = 100 × (P × U × Q)^(1/3)` e `P = sqrt(D* × O)`
- impede que lâminas repetidas do mesmo afloramento e rocha inflem a presença espacial
- usa o mapa geológico estadual para estimar a representatividade litoestratigráfica U
- define Q como completude documental de oito blocos de metadados, sem tratá-la como qualidade laboratorial
- mantém ausência de caracterização como `null` e preenchimento transparente
- incorpora análise de sensibilidade de P e mantém a sensibilidade do suporte U para revisão antes dos índices integradores
- preserva integralmente o IOD V38.4.8 e os índices anteriores

## V38.4.8 · 2026-08-14 · IOD Observação Direta

- materializa AFLO SGB para Mato Grosso do Sul
- calcula IOD em 250, 500 e 1000 km² diretamente da fonte
- congela micromalha basal de 5 km e normalização D* P95
- usa ocupação espacial O e equilíbrio de Shannon E
- mantém hexágonos sem observação com valor nulo e preenchimento transparente
- executa sensibilidade 2,5 km, 5 km e 10 km com P90, P95 e P99
- registra SHA-256 da resposta SGB e auditoria runtime
- não incorpora automaticamente registros da caderneta de campo

# V38.4.7 · METODOLOGIA-ANTECEDENTES-APA7 · 2026-08-14

- acrescenta posicionamento explícito dos índices perante antecedentes metodológicos nacionais e internacionais
- adiciona REF-174 a REF-177 com metadados conferidos em fontes primárias ou editoriais
- diferencia corretamente Ford et al. 2023a e 2023b no sistema autor-data da APA 7
- distingue PlanGeo 2025–2034 de mapeamento geológico básico e PlanGeo 2026–2035 de pesquisa de recursos minerais
- registra o Caderno 1 do Plano Nacional de Mineração 2050 como antecedente de diagnóstico do conhecimento geológico
- explicita que antecedentes não transferem pesos, fórmulas ou finalidade aos índices do Atlas
- registra PIG e ICG como produtos ainda planejados na versão atual
- não altera dados, geometrias, sensores, GPS, navegação, PAG ETR, fórmulas ou resultados de índices

# V38.4.6 · UX-CAMPO-03 · 2026-08-14

- Corrige mistura de HTML novo com CSS e JavaScript antigos causada por cache do PWA.
- Adiciona versionamento `?v=38.4.6` aos recursos críticos do aplicativo.
- Service Worker passa a usar rede primeiro para código e estilos, preservando fallback offline.
- Registro do Service Worker usa `updateViaCache: none`.
- Navegação da caderneta em celular passa a usar etapas horizontais roláveis com alvos táteis maiores.
- Melhora legibilidade dos instrumentos em telas pequenas.
- Reduz discretamente o marcador permanente de localização sem perder a convenção vermelho-amarelo-vermelho.

## V38.4.5 · UX-CAMPO-02 · instrumentos do dispositivo · 2026-08-14
- adiciona ativação explícita de orientação e movimento no módulo Campo;
- integra bússola, clinômetro, nível, aceleração e rotação em painel ao vivo;
- adiciona captura de plano, lineação e azimute com procedência instrumental;
- calcula planos com matriz de orientação Z X' Y'' quando a orientação absoluta está disponível;
- não preenche azimute quando o navegador fornece apenas referência relativa;
- preserva snapshot de sensores, horário, correção angular manual e estabilidade em cada medida;
- acrescenta HUD discreto de orientação no mapa enquanto os instrumentos estão ativos;
- mantém medidas manuais com bússola geológica e registra claramente o método;
- atualiza o esquema de campo para 0.4 e amplia o CSV de medidas com metadados dos sensores.

## V38.4.4 · UX-CAMPO-01 · 2026-08-14
- transforma Campo em Caderneta Geológica Digital por estações;
- adiciona navegação em 8 etapas e modos Completo, Rápido e Aprender;
- separa observação, litologia, medidas estruturais, amostras, fotos e interpretação;
- gera códigos automáticos de estação, medida, foto e amostra coletada;
- adiciona etiqueta imprimível da amostra e IGSN opcional, nunca inferido;
- adiciona rascunho local automático, revisão e estados de validação;
- exporta JSON, GeoJSON e CSV de amostras/medidas;
- mantém registros fora do IOD até validação científica posterior.

## V38.4.3 · C02 · 2026-08-14
- adiciona geometria computacional validada para limite estadual, malhas 500/1000 e uma feição hidrogeológica;
- preserva snapshots e IDs originais;
- documenta diferença de linhagem da malha 250 e micro-sobreposições sem regenerá-la;
- define resolução por `hex_id` para IPG/PAG ETR em cálculos futuros.

## V38.4.2 · C01 · integridade de versão e navegação residual · 2026-08-14

- Sincroniza `VERSION`, `meta.js`, `<title>` e nome do cache PWA.
- Completa o registro bibliográfico de `contexto_geoetico_250km2` e `unidades_conservacao_cnuc_ms` no HTML e JSON mestre.
- Remove abertura em nova aba de links documentais internos residuais; fontes externas continuam externas.
- Atualiza a identificação de versão no protocolo transversal de geoética.
- Não altera dados, geometrias, fórmulas, índices, PAG ETR, GPS ou simbologia científica.

## V38.4.1 · PATCH 03 rev.2 · navegação interna + GPS discreto · 2026-08-14

- Mantém a navegação documental segura da V38.4.
- Reduz o marcador HUD de localização e adapta seu tamanho ao zoom: 18 px em visão regional, 20 px em zoom intermediário, 22 px em detalhe e máximo de 24 px em grande aproximação.
- Preserva o padrão vermelho–amarelo–vermelho e o marcador continua acima de todas as camadas temáticas.
- Não altera precisão GPS, círculo de precisão, dados, índices, PAG ETR ou bibliografia.

## V38.4 · PATCH 03 · navegação interna segura · 2026-08-14

- Remove `history.back()` do iframe documental.
- Adota pilha própria de documentos do ITA ARANDU MS.
- A seta interna volta apenas entre documentos do Atlas; sem histórico interno, fecha o visor.
- O botão Voltar do navegador fecha primeiro o visor documental por estado sentinela no mesmo URL/origem.
- `Esc`, `×` e clique no fundo fecham o visor sem saltar para páginas externas.
- Navegações internas do iframe usam substituição de localização para não contaminar o histórico conjunto do navegador.
- Corrige o service worker: documentos navegados não sobrescrevem mais o cache de `index.html`.
- Nenhuma camada, índice, PAG ETR, GPS, geoética ou bibliografia foi alterada.

## V38.3 · PATCH 02 · fundamentos de leitura geocientífica · 2026-08-14

- Integra no Modo Aprender cinco fundamentos transversais: Fonte, Escala, Evidência, Incerteza e Geoética.
- Adiciona três páginas internas: evidências/rastreabilidade, incerteza/inferência e leitura de índices/produtos derivados.
- Insere a regra “Pare e verifique” nas fichas cartográficas.
- Acrescenta perguntas que todo mapa deve responder e links contextuais nas missões.
- Integra Tempo profundo, Campo e roteiro “Observe antes de interpretar” como segundo nível pedagógico.
- Centraliza a bibliografia educativa e adiciona REF-171 a REF-173 ao registro mestre.
- Atualiza a PWA para cachear os novos documentos.


## V38.1 · PATCH 00 · restauração operacional PAG ETR · 2026-08-14
- Restaura o grupo **Metalogenia e prospecção mineral** no catálogo executável.
- Materializa PAG ETR nas malhas independentes de 250, 500 e 1000 km².
- Restaura as geometrias de evidência M2 Feixe dos Morros, M4 Bocaina/Tamengo e pontos de fósforo.
- Mantém o piloto conservador: somente N0/N1 no snapshot espacial restaurado. Nenhum N2/N3 foi criado por este patch.
- Implementa legenda vermelha N0–N4 e ficha PAG ETR com salvaguardas de interpretação.
- M9 Granito Scardine continua não espacializado enquanto a geometria detalhada primária não estiver materializada.
- Este patch não altera IMC, IPG nem os demais índices geocientíficos.
# V38 · 14 de agosto de 2026

- Criada página transversal sobre escala, generalização e princípios de cartografia geológica.
- Bibliografia cartográfica concentrada na página mestre, com referências SGB, IGME, ICGC, BGS, BRGM e USGS.
- Implementada camada derivada `contexto_geoetico_250km2` para salvaguardas territoriais por hexágono em sessão.
- Adicionada conexão nacional CNUC/MMA para unidades de conservação, preservando esfera e órgão gestor e mantendo ICMBio como referência para limites federais.
- O motor diferencia polígonos territoriais de localidades pontuais e nunca infere Terra Indígena a partir de aldeia.
- Estados de cobertura incompleta impedem transformar falha de fonte remota em ausência territorial.
- Modo Aprender passa a incluir missão funcional `Detetive das lacunas`, conectando IMC e IPG sem tratá-los como o mesmo indicador.
- Fichas de camadas com escala declarada passam a remeter à metodologia cartográfica e alertar que zoom não altera a escala científica da fonte.

# V37 · 14 de agosto de 2026

- Criado protocolo transversal de geoética, governança dos dados e uso responsável.
- Implementados estados qualitativos de publicação sem pontuação geoética.
- Fichas de feição passam a exibir salvaguardas geoéticas.
- Bibliografia científica concentrada em uma única página mestre com seções específicas de Geoética e PAG ETR.
- Removida a referência JOAJU da metodologia científica de Geografia e território.
- Fontes territoriais passam a ser atribuídas diretamente a IBGE, FUNAI, INCRA, IMASUL e serviços institucionais correspondentes.
- Metodologia PAG ETR passa a remeter à bibliografia central e incorpora salvaguardas geoéticas.
- Corrigida a referência do Projeto Aquidauana para 2001 e a referência Watts e Mercer para Geochimica et Cosmochimica Acta 272, 54–77.

# V36 · 2026-08-14 · Geografia e território

- recupera e migra do JOAJU MS as localidades indígenas e quilombolas do IBGE
- conecta Terras Indígenas FUNAI, Territórios Quilombolas INCRA e assentamentos rurais INCRA
- incorpora o bloco ambiental territorial do IMASUL e PIN MS
- cria grupo Geografia e território no catálogo
- documenta a separação entre contexto territorial e resultados geocientíficos ou PAG ETR
- registra conflitos e disputas territoriais como lacuna em avaliação, sem inventar geometria
- adiciona metodologia própria e referências APA 7

# PATCH 10 · fundamentação em educação geocientífica · 2026-08-13

- Modo Aprender fundamentado explicitamente em literatura de educação geocientífica
- Ajuda recebe seção detalhada com oito eixos pedagógicos
- Metodologia recebe seção extensa sobre alfabetização geocientífica, investigação, campo, lugar, raciocínio espacial, perguntas profundas e uso do celular
- ciclo educativo próprio declarado como síntese operacional do projeto, ainda sujeito a validação com usuários
- separação didática entre observação, evidência, hipótese, interpretação, produto derivado e vazio de conhecimento
- dez referências metodológicas verificadas adicionadas ao registro mestre, REF-119 a REF-128
- registro mestre passa de 118 para 128 referências
- página pública de bibliografia recebe bloco específico de educação geocientífica
- novo documento público `docs/documentos/metodologia-educativa.html`
- PWA atualizada para incluir a nova documentação e CSS

# PATCH 09 · Modo Aprender · 2026-08-13

- nova entrada `Aprender` no menu principal desktop e móvel
- modal educativo próprio integrado ao sistema
- `Onde estou?` conectado à geolocalização do dispositivo e ao mapa
- três missões pedagógicas iniciais incorporadas como estrutura piloto
- acesso direto ao módulo ITA ARANDU Campo
- `Meu caderno` conectado provisoriamente aos registros locais de Campo
- bloco `Como ler o Atlas` com seis operações de alfabetização geocientífica
- Ajuda passa a oferecer acesso direto ao Modo Aprender
- funções incompletas são identificadas como piloto ou parcial, sem simular funcionalidades
- cache PWA atualizado

# PATCH 08 · identidade educativa do projeto · 2026-08-13

- a proposta educativa passa a ser apresentada como missão central do Atlas
- cabeçalho reformulado como Atlas geocientífico educativo e científico
- faixa superior reformulada para explicar que o objetivo é aprender a ler geocientificamente o território
- Ajuda passa a abrir com uma apresentação explícita da proposta educativa
- Projeto passa a definir alfabetização geocientífica e leitura crítica multiescalar como missão central
- seis usos pedagógicos apresentados visualmente em Ajuda
- novo princípio estrutural de educação geocientífica
- novo documento público `docs/documentos/proposta-educativa.html`
- README e manifesto PWA atualizados
- reconhecimento aos povos originários e aos conhecimentos locais e ancestrais mantido integrado à missão educativa
- cache da PWA atualizado

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
## V38.4.10 · IGC · Controle Geocronológico · 2026-08-14

- materializa Datações geocronológicas do GeoSGB e tabelas analíticas relacionadas
- calcula IGC em 250, 500 e 1000 km² diretamente a partir das amostras geocronológicas independentes
- congela IGC_h = 100 × (G × U_age × Q_age)^(1/3) e G = sqrt(D* × O)
- preserva ausência de controle direto como null e hexágono transparente
- registra análise de sensibilidade e auditoria de rastreabilidade
## V38.4.11 · IGQ · Conhecimento Geoquímico · 2026-08-14

- materializa cinco meios geoquímicos analisados do GeoSGB com seus resultados relacionados
- calcula separadamente sedimento de corrente, concentrado de bateia, solo, rocha e água
- congela IGQ_h = max(IGQ_SC, IGQ_CB, IGQ_solo, IGQ_rocha, IGQ_agua)
- congela por meio IGQ_m = 100 × (G_m × A_m × Q_m)^(1/3)
- não utiliza concentrações para classificar anomalias e não imputa valores censurados
- calcula 250, 500 e 1000 km² diretamente das amostras originais
## V38.4.12 · IGF · Conhecimento Geofísico · 2026-08-14

- materializa footprints dos levantamentos aerogeofísicos SGB e estações de gravimetria e magnetotelúrico
- separa aeromagnetometria, gamaespectrometria, gravimetria e magnetotelúrico em módulos auditáveis
- congela IGF_h = max(IGF_AM,h, IGF_GA,h, IGF_GR,h, IGF_MT,h)
- pondera aerogeofísica por cobertura e resolução relativa do espaçamento de linhas
- não interpola anomalias nem interpreta valores geofísicos como favorabilidade mineral
- calcula 250, 500 e 1000 km² diretamente das evidências originais
## V38.4.13 · ICS · Conhecimento do Subsolo · 2026-08-14

- materializa poços SIAGAS e consulta complementar RIMAS
- congela ICS_h = 100 × (M* × B × Q_log)^(1/3)
- normaliza metros perfurados por área com P95 e limita profundidades individuais pelo P99
- mede balanceamento espacial por micromalha e equitabilidade de Shannon ponderada por metros perfurados
- reserva a pontuação máxima de Q_log para suporte explícito de perfil relacionado ao RIMAS
- calcula 250, 500 e 1000 km² diretamente dos poços originais, sem agregação entre escalas

