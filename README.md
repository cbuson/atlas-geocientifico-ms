# ITA ARANDU MS

## Atlas geocientífico educativo e científico de Mato Grosso do Sul

ITA ARANDU MS é uma ferramenta educativa, científica e digital concebida para apoiar a alfabetização geocientífica, o ensino, a pesquisa e a leitura crítica e multiescalar do território.

A proposta não é apenas mostrar mapas. O Atlas procura ensinar a observar evidências, verificar fontes, comparar escalas, reconhecer incertezas, identificar vazios de conhecimento e formular novas perguntas.

O projeto reconhece também a importância dos povos originários e dos conhecimentos locais e ancestrais na compreensão do território, mantendo como princípios o respeito, a validação cultural adequada e a distinção entre fontes científicas, conhecimentos tradicionais e produtos derivados.



## Modo Aprender

A navegação principal inclui uma entrada educativa própria. O Modo Aprender organiza o Atlas para uso estudantil por meio de localização, missões, trabalho de campo, caderno local e princípios de leitura crítica dos dados. Nesta versão inicial, `Onde estou?` e a integração com `Campo` são funcionais. As missões são piloto e `Meu caderno` reutiliza provisoriamente os registros locais do módulo de campo.


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
