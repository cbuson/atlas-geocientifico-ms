
## V38.4.20 · Gate metodológico PIG · 2026-08-15

- Congelada complexidade litoestratigráfica cartográfica independente a partir do mapa geológico SGB 1:1.000.000.
- Congelada ordenação por fronts de dominância de Pareto entre VCG e C_geo, sem soma ponderada.
- Empates preservados. PIG_100 será transformação ordinal de front apenas para simbologia.
- Sensibilidade obrigatória de micromalha 1,25/2,5/5 km e normalização P90/P95/P99.
- PIG ainda não materializado nesta versão.

## V38.4.14.1 · correção de renderização dos índices

Correção estritamente visual. Os retornos HTML de legenda de ICP, IGC, IGQ, IGF e ICS foram retirados de `featureStyle` e movidos para `layerLegendHtml`. Nenhum snapshot, fórmula, valor, malha ou resultado da auditoria V38.4.14 foi recalculado. Cache PWA versionado para forçar a atualização do navegador.

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

## V38.4.14 · Auditoria das sete dimensões

- Auditoria conjunta de IMC, IOD, ICP, IGC, IGQ, IGF e ICS nas três escalas.
- Verificação de alinhamento espacial, faixas, nulls, distribuições, correlações, redundância, sensibilidade e bordas.
- Gate de síntese: BLOCKED.
- Nenhum índice base recalculado.


## V38.4.14.2 · Gate para IDE

- Auditoria conjunta preservada.
- Política explícita de null congelada.
- MT congelado como não avaliável no corte, sem imputação de zero.
- IDE liberado para materialização. ICG, VCG e PIG permanecem bloqueados.


## V38.4.15 · IDE · Diversidade de Evidências

- materializa IDE em 250, 500 e 1000 km²
- preserva null nas sete dimensões base e não imputa zero
- mantém denominador sete fixo e publica o suporte efetivamente observado por célula
- registra MT como não avaliável no corte conforme gate V38.4.14.2
- mantém ICG, VCG e PIG bloqueados até regras próprias
## V38.4.16 · Gate metodológico para ICG · 2026-08-15

- Congelada a política de incompletude do ICG sem converter null em zero.
- Elegibilidade mínima de duas dimensões observadas na mesma escala.
- Fórmula basal ICG = 100 × (n_obs/7) × max(0, μ − σ²/μ).
- IDE permanece indicador complementar e não entra na fórmula do ICG.
- Definido plano obrigatório de sensibilidade do fator de suporte antes da certificação do ICG.
- Nenhuma dimensão base, IDE ou malha é recalculada nesta etapa.

## V38.4.17 · ICG · Índice de Conhecimento Geocientífico

- materializa ICG em 250, 500 e 1000 km² conforme gate V38.4.16
- exige pelo menos duas dimensões observadas e preserva null
- aplica fator n_obs/7 e penalização não compensatória por variância
- mantém IDE fora da fórmula e o publica somente como indicador companheiro
- executa sensibilidade obrigatória com α 0,5 · 1 · 2
- mantém VCG e PIG bloqueados até regras próprias
## V38.4.18 - Gate metodologico para VCG - 2026-08-15

- Congelada a distincao entre deficit medido e lacuna documental.
- null permanece null nos snapshots fonte e nao e convertido em zero numerico.
- Ausencia documental entra no VCG como componente explicito de lacuna da familia.
- VCG nao e 100-ICG. IDE e ICG permanecem indicadores companheiros e fora da formula.
- Indisponibilidade do modulo MT nao cria uma oitava lacuna quando IGF possui valor numerico.
- Definido plano de sensibilidade para o peso da lacuna documental antes da certificacao do VCG.
- Nenhum indice cientifico ou malha e recalculado nesta etapa.

## V38.4.19 · VCG · Vazios de Conhecimento Geocientífico

- materializa VCG em 250, 500 e 1000 km² conforme gate V38.4.18
- separa déficit medido de lacuna documental sem converter null em zero
- publica lacunas dominantes e secundárias com empates preservados
- mantém IDE e ICG como indicadores companheiros fora da fórmula
- propaga a indisponibilidade MT sem criar uma oitava lacuna
- executa sensibilidade obrigatória para lambda documental 1,00 · 0,75 · 0,50
- mantém PIG bloqueado até gate próprio

## V38.4.21 · PIG · Prioridade de Investigação Geocientífica

- materializa PIG em 250, 500 e 1000 km² conforme gate V38.4.20
- calcula C_geo independentemente a partir do mapa geológico estadual SGB 1:1.000.000
- ordena VCG e C_geo por fronts de dominância de Pareto, sem soma ponderada
- preserva empates e publica tamanho do front
- publica PIG_100 somente como transformação ordinal para simbologia
- executa sensibilidade de micromalha 1,25/2,5/5 km e P90/P95/P99
- próxima etapa obrigatória é auditoria ZERO final da família de índices

## V38.4.22 · 2026-08-15 · AUDITORIA ZERO FINAL DA FAMÍLIA DE ÍNDICES

- Auditoria conjunta IMC, IOD, ICP, IGC, IGQ, IGF, ICS, IDE, ICG, VCG e PIG.
- Nenhum índice científico é recalculado.
- Corrige a sintaxe do precache PWA herdada entre changelog e IDE e sincroniza o versionamento técnico para V38.4.22.
- A robustez do PIG em 250 km² permanece registrada como ressalva quando o cenário microgrid 5 km P95 altera mais de 25% das classes.
- Front de Pareto permanece a saída científica primária do PIG.

## V38.4.24 · 2026-08-15 · Design System · tipografia e espaçamento

- Introduz folha transversal `design-system-v38424.css`, carregada por último.
- Aumenta legibilidade em Camadas, Ficha, Tempo, Aprender, Dados, Campo, sensores e modais.
- Adota escala tipográfica consistente e alvos tácteis maiores em dispositivos de toque.
- Ajusta larguras e reflow sem alterar ciência, dados, snapshots ou simbologia dos índices.
- Próxima fase prevista: navegação Ajuda → Tempo e depois opacidade por camada.

## V38.4.26 · 2026-08-15 · UX Master, metodologias e opacidade

- Consolida as correções móveis de Pesquisa, Ajuda, Tempo e Campo.
- Elimina palavras coladas e cartões de índices em duas colunas estreitas no telefone.
- Atualiza os resumos visíveis de ICG, VCG e PIG para as formulações congeladas após as auditorias.
- Adiciona metodologia individual para IMC, IOD, ICP, IGC, IGQ, IGF, ICS, IDE, ICG, VCG, PIG e IPG, com referências APA 7.
- Adiciona documento de antecedentes, nicho acadêmico e finalidade com formulação cautelosa de originalidade.
- Consolida Ajuda → Tempo, Tempo em tela integral e a navegação móvel de oito destinos.
- Adiciona opacidade 0–100% por camada, persistente e estritamente visual.
- Nenhum índice, snapshot, malha ou geometria científica é recalculado.

## V38.4.28 · Dual Source R8 · 2026-08-15

- Preserva as camadas operacionais locais.
- Registra snapshots oficiais brutos de 15/08/2026 em pasta separada.
- Ativa consulta online sob demanda.
- Não substitui GeoJSON local quando o esquema de atributos difere.
- Não recalcula índices precalculados.

## V38.4.29 · Mobile map toolbar · 2026-08-15

- Integra Mapa base e Legenda na barra cartografica superior esquerda em telas moveis.
- Remove os dois botoes flutuantes isolados da direita.
- O botao de mapa base usa a silhueta simplificada de Mato Grosso do Sul derivada do limite IBGE ja incorporado ao Atlas.
- A legenda usa simbolo cartografico de lista de simbolos.
- Mantem os mesmos paineis e eventos sem alterar dados, camadas, snapshots ou indices.
- Reposiciona os paineis moveis sob a barra unica.

## V38.4.31 · Campo Master 2.0 · 2026-08-15

- Substitui o protótipo de Campo por um Caderno de Campo Geocientífico Digital completo.
- Cria modos Essencial e Avançado sobre um único esquema 2.0.
- Estrutura litologia, mineralogia, alteração, estruturas, medidas, hidrogeologia, mineralização, geotecnia e amostras.
- Preserva GPS original separado de edições manuais.
- Identifica município pela malha municipal local quando disponível.
- Integra GeoFoto, GPS EXIF de importação, orientação auxiliar e SHA256.
- Adiciona croquis, relações pai-filho e sequência de perfil.
- Adiciona revisão, sensibilidade, completude e checklist.
- Exporta JSON, GeoJSON, KML e pacote ZIP completo.
- Usa uma nova base IndexedDB de Campo porque ainda não existem registros de produção a migrar.
- Não altera camadas, snapshots, catálogo científico ou índices.

## V38.4.32 · Fechamento UX do Campo · 2026-08-15

- Sincroniza a versão pública com V38.4.32.
- Atualiza Meu caderno de parcial para funcional.
- Renomeia os modos para Estudante · Essencial e Especialista · Avançado.
- Converte os 14 blocos do Campo em acordeões inteligentes no celular.
- Mantém os blocos abertos em telas maiores.
- Adiciona navegação Anterior, Próximo e seletor de seção.
- Faz a completude indicar também o primeiro item essencial pendente.
- Permite tocar no checklist móvel para saltar para um bloco pendente.
- Não altera o esquema científico 2.0, IndexedDB, camadas, snapshots ou índices.

## V38.4.33 · Clinômetro Visual ARANDU R2 · 2026-08-15

- Integra contato assistido e estimativa visual assistida por câmera.
- Preserva repetições, estatística, origem, referência angular e validação.
- Inclui metodologia, fórmulas, limitações e bibliografia APA 7.
- A bibliografia é integrada por DOI ou URL canônica, sem pressupor números REF livres.
- Referências existentes são reutilizadas e referências novas recebem IDs acima do maior ID já utilizado.
- O total bibliográfico é recalculado pelos IDs únicos realmente presentes.
- Gera clinometro-visual-referencias.json com os IDs efetivamente vinculados.
- Não altera Campo Master, camadas, snapshots ou índices.

## V38.4.34 · Geoética e Governança CARE · 2026-08-15

- Adota Geoética como princípio transversal do ITA ARANDU MS.
- Cria Protocolo Geoético e Protocolo CARE para Curadoria da Camada Ancestral.
- Reforça o Caderno de Campo com origem, nível de acesso, autorização, autoridade, finalidade, reutilização e canal de revisão ou retirada.
- CARE não é convertido em índice ou pontuação.
- Cria política legível por máquina ITA-GEOETHICS-CARE-1.0.
- Integra referências por DOI ou URL canônica sem presumir números REF livres.
- Não altera camadas, snapshots nem índices.

## V38.4.35 · Ferramentas Geocientíficas · Hub 1.0 · 2026-08-15

- Cria entrada superior Ferramentas com ícone martelo geológico + bússola.
- Integra Clinômetro, GeoCâmera via Campo, GPS via Campo, Amostras, Colunas Estratigráficas e Tempo Profundo.
- Ferramentas ainda não implementadas permanecem marcadas como próxima etapa.
- Não altera camadas, snapshots nem índices.

## V38.4.36 · Bússola geológica + Nível digital · 2026-08-15

- Ativa Bússola e Nível no Hub Ferramentas.
- Integra ambos ao Caderno de Campo como medidas auxiliares.
- Distingue orientação absoluta e relativa.
- Bússola aceita declinação manual, sem afirmar cálculo WMM automático.
- Nível mede a inclinação do plano da tela em relação à horizontal.
- Inclui estabilidade, metodologia, limitações e referências APA 7 centralizadas.
- Não altera camadas, snapshots nem índices.

## V38.4.37 · Estereograma ARANDU + Calculadora estrutural · 2026-08-15

- Ativa Estereograma e Calculadora no Hub Ferramentas.
- Estereograma usa projeção de área igual no hemisfério inferior, com planos e polos.
- Importa medidas estruturais válidas do Caderno de Campo.
- Calcula média vetorial dos polos e força vetorial R como síntese descritiva.
- Calculadora inclui strike RHR ↔ dip direction, mergulho aparente/verdadeiro e interseção entre dois planos.
- Exporta estereograma em SVG.
- Inclui metodologias e referências APA 7 centralizadas.
- Não altera camadas, snapshots nem índices.

## V38.4.37A · Contador agregado de visitas · 2026-08-15

- Ativa contagem pública por GoatCounter.
- Exibe visitas acumuladas, hoje, últimos sete dias e mês atual.
- Usa somente o contador público JSON para leitura dos indicadores.
- Não inclui token de API no navegador ou no repositório.
- Não simula valores quando o provedor está indisponível.
- Integra metodologia e referências APA 7.
- Não altera camadas, snapshots ou índices.

## V38.4.37B · Contador de visitas separado · 2026-08-15

- Retira o leitor GoatCounter de Dados estatísticos.
- Mantém o tracker GoatCounter responsável por registrar visitas.
- Cria página independente Visitas do Atlas.
- Falhas do provedor deixam de afetar a interface principal.
- Não altera camadas, snapshots ou índices.



## V38.4.37F · recuperação do arranque · 2026-08-15

- Remove o carregamento dinâmico de app.js por bootstrap.js.
- app.js passa a carregar de forma síncrona antes dos módulos Campo, Ferramentas e instrumentos.
- campo-sensores.js carrega imediatamente depois do motor principal.
- Corrige a condição de corrida que podia deixar Camadas e Dados sem renderização.
- Service worker atualizado para não reutilizar o bootstrap antigo.
- Nenhum GeoJSON científico e nenhum índice foi recalculado.


## V38.4.37G · correção fatal de inicialização · 2026-08-15

- Remove ligação obsoleta e não protegida ao elemento inexistente openTempoMap.
- O erro ocorria antes de init(), impedindo buildLayers() e a renderização completa de Dados.
- Mantém a ligação protegida já existente para openTempoMap, caso o elemento volte a existir.
- Não altera GeoJSON, snapshots, catálogo científico nem cálculos de índices.


## V38.4.38 · saneamento funcional · 2026-08-16

- Coluna temporal de Mato Grosso do Sul passa a carregar automaticamente o GeoJSON geológico local quando a ferramenta é aberta.
- A abertura da coluna temporal não ativa a camada geológica no mapa e não altera o estado cartográfico do usuário.
- Falhas de carregamento de camadas deixam de abrir alertas bloqueantes e passam a ser registradas na interface e no console.
- Avisos de geolocalização deixam de interromper a navegação com caixas modais do navegador.
- Dependências externas permanecem opcionais e não bloqueiam Camadas, Dados ou ferramentas locais.
- Nenhum GeoJSON científico, snapshot ou cálculo de índice foi modificado ou recalculado.


## V38.4.39 · câmera móvel e MacroGeo · 2026-08-16

- Remove o buscador do hub Ferramentas em telas desktop e móveis.
- Ativa MacroGeo como ferramenta operacional.
- Introduz motor de câmera com preferência traseira e fallback progressivo.
- Enumera câmeras após permissão e usa zoom/foco apenas quando a capacidade é exposta pelo navegador.
- Campo passa a usar o mesmo fallback robusto de câmera.
- MacroGeo registra escala apenas como declaração do usuário, sem inferência metrológica automática.
- Metodologia e referências APA 7 integradas.
- Não altera camadas, snapshots ou índices.


## V38.4.40 · Saída de Campo ARANDU · 2026-08-16

- Percurso por pontos de observação.
- Não grava track GPS contínuo na PWA.
- Cada ponto registra coordenadas, precisão, hora, categoria, confiança e descrição.
- Linha tracejada representa apenas sequência entre pontos.
- Exporta JSON, GeoJSON e KML.
- Não altera camadas, snapshots ou índices.


## V38.4.40A · Saída de Campo em Ferramentas · 2026-08-16

- Saída de Campo ARANDU integrada ao hub Ferramentas como ferramenta operacional.
- Mantido o acesso já existente dentro de Campo.
- Ambos os acessos usam a mesma saída persistida localmente.
- Nenhuma duplicação de registros.
- Não altera camadas, snapshots ou índices.


## V38.4.40B · Camadas UX Clean · 2026-08-16

- Remove somente da apresentação das tarjetas o bloco redundante de proveniência.
- Deixa de mostrar LOCAL · PROVENIÊNCIA PARCIAL, snapshot em uso, registros locais e Abrir fonte oficial dentro de cada tarjeta.
- Mantém o botão principal de fonte, bibliografia, estado e opacidade já existentes na tarjeta.
- Mantém intactos os metadados de proveniência, modos de fonte, fichas, Dados, referências e documentação.
- Não altera camadas, snapshots, índices ou cálculos.
