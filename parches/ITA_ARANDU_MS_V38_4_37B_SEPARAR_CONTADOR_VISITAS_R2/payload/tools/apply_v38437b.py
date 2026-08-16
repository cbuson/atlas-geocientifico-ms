
from pathlib import Path
import argparse,re,shutil

BASE="V38.4.37A-CONTADOR-VISITAS-1.0-20260815"
FINAL="V38.4.37B-CONTADOR-VISITAS-SEPARADO-1.0-20260815"

def read(p):
    return Path(p).read_text(encoding="utf-8-sig")

def write(p,t):
    Path(p).write_text(t,encoding="utf-8",newline="\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    ap.add_argument("--payload",required=True)
    a=ap.parse_args()

    repo=Path(a.repo).resolve()
    payload=Path(a.payload).resolve()

    current=read(repo/"VERSION").strip()
    if current!=BASE:
        raise RuntimeError("Base incorreta  "+current+" | esperada  "+BASE)

    index=repo/"docs/index.html"
    t=read(index)

    tracker='data-goatcounter="https://ita-arandu.goatcounter.com/count"'
    reader='./assets/js/contador-visitas-v38437a.js?v=38.4.37a'

    if tracker not in t:
        raise RuntimeError("Tracker GoatCounter nao localizado")
    if reader not in t:
        raise RuntimeError("Leitor contador-visitas-v38437a.js nao localizado")

    # Remove somente o leitor que interfere na tela Dados.
    t=re.sub(
        r'\s*<script\s+src=["\']\./assets/js/contador-visitas-v38437a\.js\?v=38\.4\.37a["\']\s*></script>\s*',
        '\n',
        t,
        count=1,
        flags=re.I
    )

    # Link independente e discreto.
    link='<a href="./visitas/" class="ita-visitas-link" title="Visitas do Atlas">Visitas</a>'
    if 'class="ita-visitas-link"' not in t:
        # tenta colocar ao lado de Ajuda
        matches=list(re.finditer(r'<(?:a|button)\b[^>]*>[^<]*Ajuda[^<]*</(?:a|button)>',t,re.I))
        if matches:
            m=matches[-1]
            t=t[:m.end()]+" "+link+t[m.end():]
        else:
            t=t.replace("</body>",link+"\n</body>",1)

    css = """
<style id="ita-visitas-link-style">
.ita-visitas-link{
display:inline-flex;
align-items:center;
justify-content:center;
padding:7px 10px;
border:1px solid rgba(255,255,255,.22);
border-radius:9px;
color:inherit;
text-decoration:none;
font-size:11px;
font-weight:800
}
@media(max-width:760px){
.ita-visitas-link{
font-size:10px;
padding:6px 8px
}
}
</style>
"""
    if 'id="ita-visitas-link-style"' not in t:
        t=t.replace("</head>",css+"\n</head>",1)

    t=re.sub(
        r'(<span class="ita-version-badge">)V[^<]+(</span>)',
        r'\1V38.4.37B\2',
        t,
        count=1
    )

    write(index,t)

    dst=repo/"docs/visitas/index.html"
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(payload/"docs/visitas/index.html",dst)

    sw=repo/"docs/service-worker.js"
    if sw.exists():
        s=read(sw)
        s=re.sub(
            r"const ITA_CACHE\s*=\s*['\"][^'\"]+['\"];",
            "const ITA_CACHE = 'ita-arandu-v38-4-37b-visitas-separado';",
            s,
            count=1
        )
        s=re.sub(
            r'\s*["\']\./assets/js/contador-visitas-v38437a\.js\?v=38\.4\.37a["\'],?',
            '',
            s
        )
        marker="const ITA_CORE = ["
        if marker in s and './visitas/' not in s:
            s=s.replace(marker,marker+'\n  "./visitas/",',1)
        write(sw,s)

    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=read(ch)
        if "V38.4.37B · Contador de visitas separado" not in c:
            c=c.rstrip()+"""

## V38.4.37B · Contador de visitas separado · 2026-08-15

- Retira o leitor GoatCounter de Dados estatísticos.
- Mantém o tracker GoatCounter responsável por registrar visitas.
- Cria página independente Visitas do Atlas.
- Falhas do provedor deixam de afetar a interface principal.
- Não altera camadas, snapshots ou índices.
"""
            write(ch,c+"\n")

    write(repo/"VERSION",FINAL+"\n")
    print("V38.4.37B contador separado aplicado")

if __name__=="__main__":
    main()
