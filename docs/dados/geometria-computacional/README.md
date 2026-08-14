# C02 · Geometria computacional validada

Esta pasta não substitui `docs/camadas/arquivos`.

**geometria de publicação ≠ geometria computacional**

Método executado neste corte: `Shapely 2.1.2 · make_valid()`.

Nenhum ID foi alterado e nenhuma malha foi regenerada.

## Malha 250 km²
1.554 células individualmente válidas. A malha permanece congelada e não deve ser reclipada contra o limite estadual atual.

## Malhas 500 e 1000 km²
As cópias computacionais corrigem 3 células em cada escala que continham auto-interseções/segmentos degenerados.

## Hidrogeologia
Uma feição da Formação Pantanal recebe cópia computacional válida, sem alteração de atributos.

## Produtos derivados
IPG e PAG ETR mantêm seus arquivos originais. Para cálculos, a geometria deve ser resolvida por `hex_id` na malha computacional correspondente.
