# ITA ARANDU MS · V38.4.52

## Ponte nativa Android para sensores

- Magnetômetro · Amostras tenta primeiro a ponte nativa Android `ItaSensors` e mantém a API Web Magnetometer como fallback.
- Magnetômetro · Mapa usa a mesma fonte nativa quando disponível.
- A ponte entrega X, Y e Z do `TYPE_MAGNETIC_FIELD` em µT e o front-end calcula |B|.
- Na Web comum, o comportamento científico permanece conservador e nenhum valor é estimado quando o navegador não expõe magnetometria quantitativa.
- Versão visual atualizada para V38.4.52.

## Segurança

A ponte nativa foi projetada para conteúdo empacotado no próprio APK. Links HTTP/HTTPS externos são abertos fora do WebView, reduzindo a exposição da interface JavaScript a conteúdo não confiável.
