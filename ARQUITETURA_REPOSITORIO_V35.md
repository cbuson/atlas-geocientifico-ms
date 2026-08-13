# ITA ARANDU MS · Arquitetura da beta V35

`docs/index.html` é a entrada da aplicação e não contém as camadas.

As camadas locais válidas ficam em `docs/camadas/arquivos`.

Quantidade de camadas locais válidas

26

Cada camada possui um GeoJSON independente.

Os snapshots herdados que falharam na verificação de integridade ficam em `docs/camadas/pendentes`.

Quantidade em avaliação

2

Esses arquivos não são apresentados como camadas incorporadas até reconstrução verificável.

A interface fica em `docs/assets`.

Os metadados ficam em `docs/dados`.

As referências ficam em `docs/referencias`.

Os índices ficam em `docs/indices`.

Os documentos públicos ficam em `docs/documentos`.

A aplicação carrega apenas as bases essenciais no arranque e busca as outras camadas locais sob demanda.
