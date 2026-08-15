
from pathlib import Path
import argparse,re,shutil

ALLOWED={
 "V38.4.28-SNAPSHOT-FIRST-DUAL-SOURCE-R8-20260815",
 "V38.4.29-MOBILE-MAP-TOOLS-INTEGRADOS-20260815",
 "V38.4.30-CAMPO-GEOFOTO-1.0-20260815"
}
FINAL="V38.4.31-CAMPO-MASTER-2.0-20260815"

def read(p):return Path(p).read_text(encoding="utf-8-sig")
def write(p,t):Path(p).write_text(t,encoding="utf-8",newline="\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True);ap.add_argument("--payload",required=True);a=ap.parse_args()
    repo=Path(a.repo).resolve();payload=Path(a.payload).resolve()
    cur=read(repo/"VERSION").strip()
    if cur not in ALLOWED:raise RuntimeError("Base nao reconhecida  "+cur)

    index=repo/"docs/index.html";t=read(index)
    start=t.find('<div class="modal" id="campoModal">')
    end=t.find('<div class="modal" id="autoriaModal">',start)
    if start<0 or end<0:raise RuntimeError("Bloco Campo nao localizado de forma segura")

    modal=(payload/"CAMPO_MODAL_MASTER.html").read_text(encoding="utf-8")
    t=t[:start]+modal+t[end:]

    # Remove previous GeoFoto assets from loading, if present
    t=re.sub(r'\s*<link[^>]+campo-geofoto-v38430\.css[^>]*>','',t,flags=re.I)
    t=re.sub(r'\s*<script[^>]+campo-geofoto-v38430\.js[^>]*></script>','',t,flags=re.I)

    css_tag='<link rel="stylesheet" href="./assets/css/campo-master-v38431.css?v=38.4.31">'
    if "campo-master-v38431.css" not in t:
        t=t.replace("</head>",css_tag+"\n</head>",1)

    script='<script src="./assets/js/campo-master-v38431.js?v=38.4.31"></script>'
    if "campo-master-v38431.js" not in t:
        pat=r'(<script\b[^>]*src=["\']\./assets/js/app\.js(?:\?[^"\']*)?["\'][^>]*></script>)'
        m=re.search(pat,t,re.I)
        if m:t=t[:m.end()]+"\n"+script+t[m.end():]
        else:t=t.replace("</body>",script+"\n</body>",1)
    write(index,t)

    for rel in ["docs/assets/css/campo-master-v38431.css","docs/assets/js/campo-master-v38431.js","docs/documentos/protocolo-campo-master.html"]:
        src=payload/rel;dst=repo/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)

    sw=repo/"docs/service-worker.js"
    if sw.exists():
        s=read(sw);s=re.sub(r"const ITA_CACHE\s*=\s*['\"][^'\"]+['\"];","const ITA_CACHE = 'ita-arandu-v38-4-31-campo-master';",s,count=1)
        marker="const ITA_CORE = ["
        entries=['./assets/css/campo-master-v38431.css?v=38.4.31','./assets/js/campo-master-v38431.js?v=38.4.31','./documentos/protocolo-campo-master.html']
        if marker in s:
            for e in entries:
                if e not in s:s=s.replace(marker,marker+'\n  "'+e+'",',1)
        write(sw,s)

    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=read(ch)
        if "V38.4.31 · Campo Master 2.0" not in c:
            c=c.rstrip()+"""

## V38.4.31 · Campo Master 2.0 · 2026-08-15

- Substitui o protótipo de Campo por um Caderno de Campo Geocientífico Digital completo.
- Cria modos Essencial e Avançado sobre um único esquema 2.0.
- Estrutura litologia, mineralogia, alteração, estruturas, medidas, hidrogeologia, mineralização, geotecnia e amostras.
- Preserva GPS original separado de edições manuais.
- Identifica município pela malha municipal local quando disponível.
- Integra GeoFoto, GPS EXIF de importação, orientação auxiliar e SHA256.
- Adiciona croquis, relações pai-filho e sequência de perfil.
- Adiciona revisão, sensibilidade, completude e checklist.
- Exporta JSON, GeoJSON, KML e pacote ZIP completo.
- Usa uma nova base IndexedDB de Campo porque ainda não existem registros de produção a migrar.
- Não altera camadas, snapshots, catálogo científico ou índices.
"""
            write(ch,c+"\n")
    write(repo/"VERSION",FINAL+"\n")
    print("V38.4.31 Campo Master 2.0 aplicado")

if __name__=="__main__":main()
