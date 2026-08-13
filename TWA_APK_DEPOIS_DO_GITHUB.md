# ITA ARANDU MS · Android APK por Trusted Web Activity

A V33 Beta já contém a PWA instalável. O APK Android deve ser gerado depois que a URL pública do GitHub Pages estiver ativa.

## Por que o APK vem depois

Trusted Web Activity verifica que o site e o aplicativo pertencem ao mesmo responsável. A verificação usa Digital Asset Links e depende da URL pública e do certificado usado para assinar o APK.

Sem essa associação o aplicativo pode abrir como Custom Tab em vez de Trusted Web Activity verificada.

## Depois de publicar a PWA

1. Confirme que o endereço público abre normalmente por HTTPS.

2. Confirme que o manifesto abre no navegador a partir de `manifest.webmanifest`.

3. No Windows instale Node.js se ainda não estiver instalado.

4. Abra PowerShell e instale Bubblewrap.

```powershell
npm i -g @bubblewrap/cli
```

5. Crie uma pasta separada para o projeto Android.

6. Inicialize o projeto usando a URL pública exata do manifesto.

```powershell
bubblewrap init --manifest=https://SEU-DOMINIO/SEU-CAMINHO/manifest.webmanifest
```

7. Guarde com segurança a chave de assinatura criada durante a configuração. Não publique a chave privada no GitHub.

8. Gere o APK.

```powershell
bubblewrap build
```

9. O processo produz `app-release-signed.apk`.

10. Antes de considerar o APK uma TWA verificada, publique o `assetlinks.json` em `.well-known/assetlinks.json` na raiz do domínio usado pela PWA. O arquivo deve conter o identificador real do pacote Android e a impressão SHA-256 do certificado real de assinatura.

## Atenção com GitHub Pages de projeto

Quando o Atlas é publicado em um caminho como `usuario.github.io/ita-arandu-ms/`, a origem é `usuario.github.io`. O Digital Asset Links deve estar disponível na raiz dessa origem. Por isso a etapa do `assetlinks.json` deve ser resolvida depois de sabermos a URL definitiva e a assinatura definitiva do APK.

Não foi criado um `assetlinks.json` fictício nesta versão.
