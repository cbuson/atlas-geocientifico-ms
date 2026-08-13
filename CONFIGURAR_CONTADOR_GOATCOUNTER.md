# Configurar o contador público de uso

O painel Dados já está preparado para exibir visitas acumuladas, visitas de hoje, últimos sete dias e mês atual.

O Atlas não inclui uma conta de analytics inventada e não publica chaves privadas.

## 1

Crie um site no GoatCounter para o endereço público do Atlas.

## 2

Nas configurações do site no GoatCounter, habilite a opção que permite adicionar contadores de visitantes ao próprio site.

## 3

Abra

`docs/analytics/config.js`

e altere somente

```js
window.ITA_ANALYTICS = {
  provider: "goatcounter",
  enabled: true,
  siteCode: "SEU_CODIGO",
  baseUrl: "",
  publicDashboardUrl: "",
  publicCountersEnabled: true,
  counterPath: "TOTAL",
  note: "GoatCounter"
};
```

`siteCode` é somente o código público que antecede `.goatcounter.com`. Não coloque token de API, senha ou chave privada no GitHub.

Se utilizar uma instalação própria do GoatCounter, deixe `siteCode` vazio e informe a URL pública em `baseUrl`.

## 4

Faça commit e Push origin.

Depois recarregue o Atlas.

O próprio Atlas enviará a visita pelo `count.js` e carregará os contadores públicos em JSON.

Os números públicos podem ter atraso porque o serviço de contador utiliza cache.
