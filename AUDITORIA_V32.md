# Auditoria V32 · correção do IMC

## Problema identificado

Na V31 o IMC era calculado por 49 pontos regulares dentro de cada hexágono. Cada ponto começava com a escala 1:1.000.000 como valor mínimo. Por isso praticamente todo Mato Grosso do Sul recebia IMC 10 e aparecia na mesma primeira classe visual quando a cobertura detalhada não era capturada de forma suficiente.

## Correção aplicada

A V32 materializa previamente o IMC e não depende da consulta remota do SGB durante a visualização.

O cálculo usa a área real de cada hexágono em uma projeção Lambert Azimutal Equal-Area centrada em Mato Grosso do Sul.

A fórmula materializada é

`IMC_h = 100 × [1,00 A100 + 0,40 A250 + 0,10 A1000] / A_h`

`A100` corresponde à área do hexágono coberta por folhas 1:100.000 verificadas.

`A250` corresponde à área restante coberta por folhas 1:250.000 verificadas.

`A1000` corresponde ao restante coberto pelo mapa estadual 1:1.000.000.

A escala mais detalhada prevalece nas sobreposições.

## Resultado numérico

### 250 km²

- 1554 células válidas
- mínimo 10,0
- máximo 100,0
- média 18,629
- 103 valores diferentes após arredondamento a uma casa decimal
- 304 células apresentam valor superior ao nível basal 10

### 500 km²

- 793 células válidas
- mínimo 10,0
- máximo 100,0
- média 18,811
- 68 valores diferentes após arredondamento a uma casa decimal
- 165 células apresentam valor superior ao nível basal 10

### 1000 km²

- 412 células válidas
- mínimo 10,0
- máximo 100,0
- média 18,916
- 52 valores diferentes após arredondamento a uma casa decimal
- 94 células apresentam valor superior ao nível basal 10

A uniformidade observada na V31 deixa portanto de existir.

## Limite conservador do corte

A V32 somente atribui espacialmente uma cobertura detalhada quando o código da folha e sua escala foram verificados e a extensão cartográfica pode ser reconstruída sem adivinhação.

Continuam pendentes de geometria exata local, entre outros, Projeto Rio Apa 1:100.000, Projeto Bonito–Aquidauana 1:50.000, PIMA Fosfato da Serra da Bodoquena 1:50.000 e Projeto Bodoquena 1:250.000.

Esses projetos não são tratados como inexistentes. Apenas não alteram o IMC até que sua geometria seja materializada de forma verificável.
