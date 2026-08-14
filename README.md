## V38.4.8 · IOD · Observação Direta

Materialização reproduzível do IOD em 250, 500 e 1000 km² a partir de Afloramentos geológicos do SGB. O instalador captura a fonte oficial, deduplica as observações, calcula D*, O e E de forma independente em cada escala, executa análise de sensibilidade e só conclui a atualização se a auditoria runtime passar.

# ITA ARANDU MS

## Atlas geocientífico educativo e científico de Mato Grosso do Sul

ITA ARANDU MS é uma ferramenta educativa, científica e digital concebida para apoiar a alfabetização geocientífica, o ensino, a pesquisa e a leitura crítica e multiescalar do território.

A proposta não é apenas mostrar mapas. O Atlas procura ensinar a observar evidências, verificar fontes, comparar escalas, reconhecer incertezas, identificar vazios de conhecimento e formular novas perguntas.

O projeto reconhece também a importância dos povos originários e dos conhecimentos locais e ancestrais na compreensão do território, mantendo como princípios o respeito, a validação cultural adequada e a distinção entre fontes científicas, conhecimentos tradicionais e produtos derivados.



## V38.4.5 · UX-CAMPO-02 · instrumentos do dispositivo

A caderneta de campo incorpora sensores do telefone mediante autorização explícita. O painel reúne bússola, clinômetro, nível, acelerômetro e giroscópio, permite capturar planos, lineações e azimutes e preserva a procedência instrumental dentro de cada medida. Leituras sem orientação absoluta nunca são convertidas em azimute geográfico. As medidas manuais continuam disponíveis e o método permanece registrado.

## V38.4.2 · C01 · integridade de versão e navegação residual

Primeiro patch formal pós-Auditoria Zero. Sincroniza VERSION, meta, título HTML e cache PWA; completa as âncoras bibliográficas de `contexto_geoetico_250km2` e `unidades_conservacao_cnuc_ms`; e integra ao navegador documental os links internos residuais. Não altera dados, geometrias, índices, PAG ETR ou resultados científicos.


## Modo Aprender

A navegação principal inclui uma entrada educativa própria. O Modo Aprender organiza o Atlas para uso estudantil por meio de localização, missões, trabalho de campo, caderno local e princípios de leitura crítica dos dados. Nesta versão inicial, `Onde estou?` e a integração com `Campo` são funcionais. As missões são piloto e `Meu caderno` reutiliza provisoriamente os registros locais do módulo de campo.


## V37 · Geografia e território

Incorpora ao Atlas o núcleo territorial auditado do JOAJU MS. Inclui 518 localidades indígenas e 27 localidades quilombolas como snapshots locais do IBGE, além de conexões oficiais para Terras Indígenas, Territórios Quilombolas, assentamentos rurais, unidades de conservação, zonas de amortecimento, corredores ecológicos e áreas de uso restrito. Conflitos e disputas territoriais permanecem em avaliação sem geometria até fechamento de uma metodologia e fonte verificável.

## Beta V35 com repositório modular e camadas separadas

O `index.html` não contém mais as camadas do Atlas.

Há 26 camadas locais válidas em arquivos GeoJSON independentes.

Há 2 snapshots herdados em avaliação de integridade, preservados mas desativados.

```text
docs/
  index.html
  assets/
    css/
    js/
  dados/
  referencias/
  indices/
  camadas/
    index.html
    catalogo-local.json
    catalogo-local.js
    arquivos/
      uma camada por arquivo GeoJSON
    pendentes/
      blobs preservados para auditoria
  documentos/
  icons/
```

# ITA ARANDU MS

## Estrutura da beta V34

```text
docs/
  index.html
  manifest.webmanifest
  service-worker.js
  assets/
    css/
    js/
  dados/
    meta.js
    registros.js
    atlas-data.js
  referencias/
    referencias.js
  indices/
    imc-v32.js
    imc_v32_snapshot.json
  camadas/
    camadas-compactadas.js
    cobertura_cartografica_v32.geojson
  documentos/
    index.html
    fontes.html
    auditoria.html
    changelog.html
  icons/

data/
  imc_v32_snapshot.json
  cobertura_cartografica_v32.geojson
```

O `index.html` não contém mais o conjunto de dados e camadas do Atlas. Ele apenas carrega os módulos necessários.

# ITA ARANDU MS · V33 Beta PWA

Versão beta do Atlas Geocientífico de Mato Grosso do Sul preparada para publicação no GitHub Pages.

A base científica da V32 foi preservada. O IMC continua calculado por interseção areal exata e as coberturas detalhadas verificadas permanecem materializadas.

## Novidade V33 Beta

- PWA instalável em navegador compatível
- botão `Instalar aplicativo` dentro de Ajuda
- `manifest.webmanifest`
- `service-worker.js`
- ícones 192 e 512 pixels com variante maskable
- atualização controlada do cache do núcleo da aplicação
- estrutura pronta para empacotamento Android como Trusted Web Activity depois da publicação da URL
- guia específico para gerar APK com Bubblewrap
- guia de primeira publicação usando GitHub Desktop

## Limite offline

A instalação PWA não torna automaticamente os serviços externos disponíveis offline. Mapas base, consultas conectadas e serviços científicos remotos continuam dependendo de internet quando não existe snapshot local.

## GitHub Pages

Publique a pasta `docs` a partir da branch `main`.


## Geoética e bibliografia central

A V37 adota um protocolo transversal de geoética e governança de dados para todas as camadas e produtos derivados. Não existe pontuação geoética. Estados qualitativos de publicação orientam precisão, restrição e exposição de dados. Toda a bibliografia científica e institucional é concentrada em `docs/referencias/index.html`, com seções específicas para Geoética e PAG ETR.


## V38 · cartografia, geoética operacional e Modo Aprender

A V38 adiciona metodologia transversal de escala e generalização cartográfica, missão pedagógica Detetive das lacunas e motor de contexto territorial por hexágono. A bibliografia permanece concentrada em `docs/referencias/index.html`. O motor geoético não gera pontuação e não altera resultados geocientíficos.


## V38.3 · fundamentos de leitura crítica

O Modo Aprender passa a explicitar Fonte → Escala → Evidência → Incerteza → Responsabilidade → Interpretação. Três documentos internos novos aprofundam rastreabilidade, limites da inferência e leitura de índices. A bibliografia continua concentrada em `docs/referencias/index.html`.

## C02 · Geometria computacional · 14/08/2026

A V38.4.3 adiciona geometria computacional topologicamente válida sem substituir snapshots originais nem regenerar malhas. Ver `C02_GEOMETRIA_COMPUTACIONAL.md`.

## UX-CAMPO-01 · Caderneta Geológica Digital · 14/08/2026

A V38.4.4 transforma Campo em uma caderneta por estações, com navegação por etapas, modo rápido/completo/aprender, medidas estruturais repetíveis, amostras com código local automático, etiquetas, fotos classificadas, rascunho local, revisão e exportações JSON/GeoJSON/CSV. Nenhuma estação entra automaticamente no IOD.


## Atualização V38.4.6
A V38.4.6 introduz invalidação explícita de cache para impedir que GitHub Pages/PWA combinem arquivos de versões diferentes. Recursos críticos usam identificador de versão e estratégia network-first com fallback offline.


## Atualização V38.4.7

A V38.4.7 fecha o bloco documental de posicionamento metodológico dos índices. Acrescenta antecedentes nacionais e internacionais com referências APA 7 verificadas, separa explicitamente comparação de transferência metodológica e registra como planejados os produtos ainda não materializados. Nenhum cálculo, geometria, sensor, GPS ou comportamento cartográfico é alterado.
