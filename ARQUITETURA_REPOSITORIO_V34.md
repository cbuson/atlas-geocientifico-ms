# ITA ARANDU MS · Arquitetura modular da beta V34

A aplicação deixa de concentrar código, dados e camadas em `docs/index.html`.

`docs/index.html` funciona como ponto de entrada da aplicação.

A interface e a lógica ficam em `docs/assets`.

Os dados gerais ficam em `docs/dados`.

As referências ficam em `docs/referencias`.

Os índices ficam em `docs/indices`.

As camadas ficam em `docs/camadas`.

Os documentos públicos ficam em `docs/documentos`.

Os snapshots-fonte continuam preservados também na pasta `data` na raiz do repositório.

Esta organização permite auditar, substituir e versionar dados e camadas sem reconstruir um HTML monolítico.
