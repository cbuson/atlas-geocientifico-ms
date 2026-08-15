
from pathlib import Path
import argparse,re,shutil

BASES={
 "V38.4.28-SNAPSHOT-FIRST-DUAL-SOURCE-R8-20260815",
 "V38.4.29-MOBILE-MAP-TOOLS-INTEGRADOS-20260815"
}
FINAL="V38.4.30-CAMPO-GEOFOTO-1.0-20260815"

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

    cur=read(repo/"VERSION").strip()
    if cur not in BASES:
        raise RuntimeError("Base nao reconhecida  "+cur)

    index=repo/"docs/index.html"
    app=repo/"docs/assets/js/app.js"
    if not index.exists() or not app.exists():
        raise RuntimeError("Estrutura principal do Atlas nao localizada")

    t=read(index)
    required=["campoModal","campoForm","campoFotos","campoSalvar","campoGps","campoSampleLocal"]
    for rid in required:
        if f'id="{rid}"' not in t:
            raise RuntimeError("Elemento Campo nao localizado  "+rid)

    css_src=payload/"docs/assets/css/campo-geofoto-v38430.css"
    js_src=payload/"docs/assets/js/campo-geofoto-v38430.js"
    doc_src=payload/"docs/documentos/protocolo-campo-geofoto.html"
    css_dst=repo/"docs/assets/css/campo-geofoto-v38430.css"
    js_dst=repo/"docs/assets/js/campo-geofoto-v38430.js"
    doc_dst=repo/"docs/documentos/protocolo-campo-geofoto.html"
    for src,dst in [(css_src,css_dst),(js_src,js_dst),(doc_src,doc_dst)]:
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)

    css_tag='<link rel="stylesheet" href="./assets/css/campo-geofoto-v38430.css?v=38.4.30">'
    if "campo-geofoto-v38430.css" not in t:
        if "</head>" not in t:raise RuntimeError("Fecho head nao localizado")
        t=t.replace("</head>",css_tag+"\n</head>",1)

    script='<script src="./assets/js/campo-geofoto-v38430.js?v=38.4.30"></script>'
    if "campo-geofoto-v38430.js" not in t:
        # Must run after app.js, because it upgrades existing Campo handlers.
        pat=r'(<script\b[^>]*src=["\']\./assets/js/app\.js(?:\?[^"\']*)?["\'][^>]*></script>)'
        m=re.search(pat,t,re.I)
        if m:
            t=t[:m.end()]+"\n"+script+t[m.end():]
        elif "</body>" in t:
            t=t.replace("</body>",script+"\n</body>",1)
        else:
            raise RuntimeError("Ponto de carga JS nao localizado")
    write(index,t)

    sw=repo/"docs/service-worker.js"
    if sw.exists():
        s=read(sw)
        s=re.sub(r"const ITA_CACHE\s*=\s*['\"][^'\"]+['\"];","const ITA_CACHE = 'ita-arandu-v38-4-30-campo-geofoto';",s,count=1)
        entries=[
          './assets/css/campo-geofoto-v38430.css?v=38.4.30',
          './assets/js/campo-geofoto-v38430.js?v=38.4.30',
          './documentos/protocolo-campo-geofoto.html'
        ]
        marker="const ITA_CORE = ["
        if marker in s:
            for e in entries:
                if e not in s:s=s.replace(marker,marker+'\n  "'+e+'",',1)
        write(sw,s)

    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=read(ch)
        if "V38.4.30 · Campo GeoFoto 1.0" not in c:
            c=c.rstrip()+"""

## V38.4.30 · Campo GeoFoto 1.0 · 2026-08-15

- Evolui ITA ARANDU Campo para Caderno de Campo Geocientífico Digital.
- Integra câmera web com captura sem placa e cópia cartográfica opcional.
- Registra posição WGS84, UTM dinâmica, precisão, altitude e qualidade GPS.
- Integra orientação do dispositivo como informação auxiliar da fotografia.
- Calcula SHA256 de imagens originais e cópias com placa.
- Lê GPS EXIF de JPEG importado quando disponível.
- Distingue EXIF original de georreferência atribuída posteriormente.
- Mantém Spot, amostras, IGSN opcional e IndexedDB local.
- Exporta JSON, GeoJSON e KML.
- Não altera camadas, snapshots, catálogo científico ou índices.
"""
            write(ch,c+"\n")

    write(repo/"VERSION",FINAL+"\n")
    print("V38.4.30 Campo GeoFoto 1.0 aplicado")
    print("Camadas e indices nao alterados")

if __name__=="__main__":
    main()
