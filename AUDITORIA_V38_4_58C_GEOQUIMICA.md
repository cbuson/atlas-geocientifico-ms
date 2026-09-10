# ITA ARANDU MS · Auditoria V38.4.58C · hotfix geoquímico

## Falha observada
As vistas temáticas geoquímicas exibiam 0 feições porque o motor procurava `CLASSE` ou `Classe`, enquanto o snapshot materializado preserva o atributo `classe` em minúsculas. A camada de resultados multielementares também era marcada como incorporada sem possuir um arquivo geométrico próprio carregável.

## Correção
O filtro aceita `CLASSE`, `Classe`, `classe` e `__atlas_meio_nome`. A camada de resultados passa a ser uma vista derivada das localizações das 1.117 amostras materializadas que já possuem resultados analíticos relacionados. Nenhuma concentração é interpolada ou criada.

## Contagens esperadas no snapshot local
- Solo 588
- Sedimento de corrente 319
- Rocha 153
- Concentrado de bateia 57
- Água 0
- Vegetação 0
- Total 1.117

## Limites
O hotfix corrige apenas carregamento e representação. Não altera o conteúdo do GeoJSON, não recalcula IGQ ou outros índices, não adiciona camadas e não adiciona ferramentas.
