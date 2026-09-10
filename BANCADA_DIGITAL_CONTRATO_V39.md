# Bancada Digital ARANDU · contrato V39

Este documento define o formato obrigatório das ferramentas atuais e futuras da Bancada Digital do ITA ARANDU MS.

## Estrutura obrigatória

Cada ferramenta deve possuir

1. Identificador estável e exclusivo
2. Título e grupo temático
3. Cartão de acesso na Bancada
4. Janela principal identificada como diálogo
5. Finalidade educativa explícita
6. Instruções de uso
7. Ciência e método
8. Limitações e qualidade
9. Referências completas em APA 7
10. Estados de espera, funcionamento, erro e indisponibilidade
11. Controles utilizáveis em telas móveis
12. Funcionamento seguro quando o sensor necessário não existe

## Registro obrigatório

Toda ferramenta deve registrar os cinco campos abaixo no núcleo comum.

```js
window.ITA_BANCADA.register({
  id:'identificador-estavel',
  title:'Nome da ferramenta',
  group:'grupo-tematico',
  modal:'idDaJanelaModal',
  method:'metodologia-da-ferramenta.html'
});
```

O registro permite que o núcleo comum aplique acessibilidade, navegação, retorno de foco, fechamento por Escape e identidade visual.

## Cartão de acesso

```html
<article class="ita-tool-card" data-search="termos de busca">
  <div class="ita-tool-top">
    <span class="ita-tool-icon" aria-hidden="true">◎</span>
    <span class="ita-tool-status operacional">OPERACIONAL</span>
  </div>
  <h4>Nome da ferramenta</h4>
  <p>Finalidade educativa em uma frase.</p>
  <div class="ita-tool-actions">
    <button type="button" class="action-btn primary" data-tool-action="identificador-estavel">Abrir</button>
    <a class="action-btn" href="./documentos/metodologia-da-ferramenta.html">Ciência</a>
  </div>
</article>
```

## Janela principal

```html
<div class="modal" id="idDaJanelaModal" aria-hidden="true">
  <div class="modal-box">
    <div class="modal-head">
      <div>
        <div class="kicker">BANCADA DIGITAL · GRUPO TEMÁTICO</div>
        <h2>Nome da ferramenta</h2>
      </div>
      <div class="ita-tool-head-actions">
        <button type="button" class="ita-tool-back">Voltar à Bancada</button>
        <button type="button" class="close-modal" aria-label="Fechar">×</button>
      </div>
    </div>
    <div class="modal-body">
      Conteúdo da ferramenta
    </div>
  </div>
</div>
```

## Regras de interface

Os controles devem ter pelo menos 44 por 44 pixels. Campos numéricos devem aceitar teclado móvel adequado. A ferramenta deve funcionar entre 320 e 768 pixels sem rolagem horizontal da página.

O cabeçalho deve conservar título, grupo, retorno à Bancada e fechamento. Os controles principais devem permanecer próximos da visualização ou leitura que modificam.

## Regras científicas

Uma leitura de sensor deve distinguir estabilidade, precisão, calibração e qualidade. Estabilidade recente não significa exatidão garantida.

Uma simulação deve declarar suas hipóteses, domínio de validade e limitações. Resultado calculado não deve ser apresentado como observação direta.

Cada metodologia deve possuir bibliografia completa em APA 7 e ligação com a Biblioteca Bibliográfica do Atlas.

## Verificação de entrada

Uma ferramenta somente pode ser classificada como operacional depois de passar por

1. Validação de sintaxe
2. Teste de abertura e fechamento
3. Teste de retorno à Bancada
4. Teste em 320, 360, 375, 390, 412, 430 e 768 pixels
5. Teste sem conexão
6. Teste sem o sensor solicitado
7. Teste dos cálculos com casos conhecidos
8. Teste das exportações
9. Revisão da metodologia e das referências
10. Revisão de acessibilidade
