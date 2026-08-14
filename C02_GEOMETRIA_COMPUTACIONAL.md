# C02 · Validação geométrica da base e das malhas

**Versão resultante** · V38.4.3  
**Método** · Shapely 2.1.2 · make_valid()

## Resultado

- 250 km² · 1.554 células · 0 inválidas · original intacta
- 500 km² · 793 células · 3 inválidas no original · 0 na cópia computacional
- 1000 km² · 412 células · 3 inválidas no original · 0 na cópia computacional
- limite estadual · 1 feição inválida no original · 0 na cópia computacional
- hidrogeologia · 1 Formação Pantanal inválida no original · 0 na cópia computacional

## Regra para índices

A malha 250 não será reclipada contra o limite estadual atual. Cada escala usa sua própria geometria efetiva congelada.

Para 500/1000, os cálculos espaciais futuros resolvem a geometria por `hex_id` em `docs/dados/geometria-computacional/`.

IPG e PAG ETR não foram reescritos.

## Linhagem 250

A união das 1.554 células apresenta diferença simétrica de 135.858 km² em relação ao limite estadual atualmente materializado. Isso é documentado como diferença de linhagem/recorte e não como autorização para alterar a malha.

Há 8 micro-sobreposições >1 m², totalizando 0.004444 km². São preservadas e devem ser consideradas em agregações de área.
