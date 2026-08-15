
from pathlib import Path
import argparse,re,shutil

BASE="V38.4.28-SNAPSHOT-FIRST-DUAL-SOURCE-R8-20260815"
FINAL="V38.4.29-MOBILE-MAP-TOOLS-INTEGRADOS-20260815"
RESET_ICON="<svg class=\"ita-map-tool-icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M8 3H4a1 1 0 0 0-1 1v4M16 3h4a1 1 0 0 1 1 1v4M21 16v4a1 1 0 0 1-1 1h-4M8 21H4a1 1 0 0 1-1-1v-4\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/><circle cx=\"12\" cy=\"12\" r=\"2.2\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\"/></svg>"
BASE_ICON="<svg class=\"ita-map-tool-icon ita-ms-outline\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M 5.67 16.65 L 2.48 16.06 L 2.97 12.90 L 2.01 10.95 L 2.85 10.22 L 2.10 9.63 L 3.32 7.56 L 3.11 7.26 L 3.68 5.44 L 3.97 5.41 L 3.23 4.30 L 3.21 3.48 L 3.97 4.51 L 5.10 4.03 L 5.96 2.87 L 6.77 2.93 L 7.67 2.47 L 10.40 3.82 L 11.90 3.31 L 12.58 3.84 L 13.27 3.72 L 14.32 2.64 L 14.32 3.85 L 13.90 3.95 L 13.63 4.41 L 13.65 4.56 L 16.07 4.87 L 15.99 5.64 L 16.93 5.74 L 16.37 6.27 L 16.50 6.54 L 17.77 6.68 L 21.96 8.81 L 21.62 10.94 L 20.15 12.07 L 20.07 12.89 L 19.37 13.43 L 19.41 14.00 L 18.76 14.55 L 18.82 15.03 L 17.68 16.42 L 14.60 18.43 L 12.82 21.49 L 11.66 20.82 L 10.91 21.25 L 9.60 21.24 L 8.98 18.65 L 9.05 17.62 L 8.39 16.59 L 7.41 16.58 L 6.90 16.02 L 5.67 16.65 Z\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.45\" stroke-linejoin=\"round\"/><path d=\"M15.8 18.4h5.1M16.8 20.6h4.1\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.45\" stroke-linecap=\"round\"/></svg>"
LEGEND_ICON="<svg class=\"ita-map-tool-icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><circle cx=\"5\" cy=\"6\" r=\"2\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.6\"/><line x1=\"9\" y1=\"6\" x2=\"20\" y2=\"6\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\"/><rect x=\"3.2\" y=\"10.2\" width=\"3.6\" height=\"3.6\" rx=\".5\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\"/><line x1=\"9\" y1=\"12\" x2=\"20\" y2=\"12\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\"/><line x1=\"3.2\" y1=\"18\" x2=\"6.8\" y2=\"18\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\"/><line x1=\"9\" y1=\"18\" x2=\"20\" y2=\"18\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\"/></svg>"
JS_FRAGMENT="/* V38.4.29 mobile map toolbar integrated */\n(function itaInstallMobileMapToolbarState(){\n  if(window.__ITA_MOBILE_MAP_TOOLBAR_38429__)return;\n  window.__ITA_MOBILE_MAP_TOOLBAR_38429__=true;\n  const sync=()=>{\n    const base=document.getElementById('basemapPanel');\n    const legend=document.getElementById('mapLegend');\n    document.getElementById('mobileBaseBtn')?.classList.toggle('is-open',!!base?.classList.contains('mobile-open'));\n    document.getElementById('mobileLegendBtn')?.classList.toggle('is-open',!!legend?.classList.contains('mobile-open'));\n  };\n  ['mobileBaseBtn','mobileLegendBtn','closeBasePanel','closeLegendPanel'].forEach(id=>{\n    document.getElementById(id)?.addEventListener('click',()=>requestAnimationFrame(sync));\n  });\n  document.querySelectorAll('input[name=\"basemap\"]').forEach(el=>{\n    el.addEventListener('change',()=>requestAnimationFrame(sync));\n  });\n  const observe=id=>{\n    const el=document.getElementById(id);\n    if(el)new MutationObserver(sync).observe(el,{attributes:true,attributeFilter:['class']});\n  };\n  observe('basemapPanel');\n  observe('mapLegend');\n  sync();\n})();"

def read(p):
    return Path(p).read_text(encoding='utf-8-sig')

def write(p,t):
    Path(p).write_text(t,encoding='utf-8',newline='\n')

def toolbar_span(t):
    m=re.search(r'<div class=["\']map-toolbar["\']>',t,re.I)
    if not m:
        raise RuntimeError('map-toolbar nao localizada em docs/index.html')
    start=m.start()
    pos=m.end()
    depth=1
    tag=re.compile(r'</?div\b[^>]*>',re.I)
    while True:
        x=tag.search(t,pos)
        if not x:
            raise RuntimeError('Fim de map-toolbar nao localizado')
        if x.group(0).lower().startswith('</div'):
            depth-=1
            if depth==0:
                return start,x.end()
        else:
            depth+=1
        pos=x.end()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True)
    ap.add_argument('--payload',required=True)
    a=ap.parse_args()

    repo=Path(a.repo).resolve()
    payload=Path(a.payload).resolve()

    version=read(repo/'VERSION').strip()
    if version!=BASE:
        raise RuntimeError('Base incorreta  '+version+' | esperada  '+BASE)

    index=repo/'docs/index.html'
    app=repo/'docs/assets/js/app.js'
    sw=repo/'docs/service-worker.js'
    changelog=repo/'CHANGELOG.md'

    t=read(index)
    for required in ('mobileBaseBtn','mobileLegendBtn','resetView','openTempoMap'):
        if required not in t:
            raise RuntimeError('Controle nao localizado em index.html  '+required)

    t,n=re.subn(
        r'<div class=["\']mobile-map-tools["\']>\s*<button\b[^>]*id=["\']mobileBaseBtn["\'][^>]*>.*?</button>\s*<button\b[^>]*id=["\']mobileLegendBtn["\'][^>]*>.*?</button>\s*</div>',
        '',
        t,
        count=1,
        flags=re.I|re.S
    )
    if n!=1:
        raise RuntimeError('Grupo mobile-map-tools antigo nao localizado de forma unica')

    t,n=re.subn(
        r'(<button\b[^>]*id=["\']resetView["\'][^>]*>).*?(</button>)',
        lambda m:m.group(1)+RESET_ICON+m.group(2),
        t,
        count=1,
        flags=re.I|re.S
    )
    if n!=1:
        raise RuntimeError('Botao resetView nao localizado')

    base_btn='<button type="button" id="mobileBaseBtn" class="mobile-integrated-tool" title="Mapa base" aria-label="Escolher mapa base">'+BASE_ICON+'</button>'
    legend_btn='<button type="button" id="mobileLegendBtn" class="mobile-integrated-tool" title="Legenda" aria-label="Abrir legenda cartografica">'+LEGEND_ICON+'</button>'

    a0,b0=toolbar_span(t)
    toolbar=t[a0:b0]
    if 'mobileBaseBtn' in toolbar or 'mobileLegendBtn' in toolbar:
        raise RuntimeError('Controles mobile ja presentes na map-toolbar')
    last=toolbar.rfind('</div>')
    toolbar=toolbar[:last]+base_btn+legend_btn+toolbar[last:]
    t=t[:a0]+toolbar+t[b0:]

    css_tag='<link rel="stylesheet" href="./assets/css/mobile-map-toolbar-v38429.css?v=38.4.29">'
    if 'mobile-map-toolbar-v38429.css' not in t:
        if '</head>' not in t:
            raise RuntimeError('Fecho head nao localizado')
        t=t.replace('</head>',css_tag+'\n</head>',1)
    write(index,t)

    css_src=payload/'docs/assets/css/mobile-map-toolbar-v38429.css'
    css_dst=repo/'docs/assets/css/mobile-map-toolbar-v38429.css'
    css_dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(css_src,css_dst)

    js=read(app)
    if 'V38.4.29 mobile map toolbar integrated' not in js:
        js=js.rstrip()+'\n\n'+JS_FRAGMENT+'\n'
        write(app,js)

    if sw.exists():
        s=read(sw)
        s=re.sub(r"const ITA_CACHE\s*=\s*['\"][^'\"]+['\"];","const ITA_CACHE = 'ita-arandu-v38-4-29-mobile-map-toolbar';",s,count=1)
        entry='./assets/css/mobile-map-toolbar-v38429.css?v=38.4.29'
        if entry not in s and 'const ITA_CORE = [' in s:
            s=s.replace('const ITA_CORE = [','const ITA_CORE = [\n  "'+entry+'",',1)
        write(sw,s)

    if changelog.exists():
        c=read(changelog)
        if 'V38.4.29 · Mobile map toolbar' not in c:
            c=c.rstrip()+'''

## V38.4.29 · Mobile map toolbar · 2026-08-15

- Integra Mapa base e Legenda na barra cartografica superior esquerda em telas moveis.
- Remove os dois botoes flutuantes isolados da direita.
- O botao de mapa base usa a silhueta simplificada de Mato Grosso do Sul derivada do limite IBGE ja incorporado ao Atlas.
- A legenda usa simbolo cartografico de lista de simbolos.
- Mantem os mesmos paineis e eventos sem alterar dados, camadas, snapshots ou indices.
- Reposiciona os paineis moveis sob a barra unica.
'''
            write(changelog,c+'\n')

    write(repo/'VERSION',FINAL+'\n')
    print('V38.4.29 mobile toolbar aplicada')
    print('Base e legenda integradas na barra esquerda')
    print('Camadas e indices nao alterados')

if __name__=='__main__':
    main()
