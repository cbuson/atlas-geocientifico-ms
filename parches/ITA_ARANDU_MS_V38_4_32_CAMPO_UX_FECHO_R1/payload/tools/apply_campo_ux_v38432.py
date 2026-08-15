
from pathlib import Path
import argparse,re,shutil

BASE="V38.4.31-CAMPO-MASTER-2.0-20260815"
FINAL="V38.4.32-CAMPO-UX-FECHO-20260815"

def read(p): return Path(p).read_text(encoding="utf-8-sig")
def write(p,t): Path(p).write_text(t,encoding="utf-8",newline="\n")

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

    required=[
      'id="campoModal"',
      'id="campoModoEssencial"',
      'id="campoModoAvancado"',
      'id="campoCompletudeText"',
      'id="campoChecklist"',
      'campo-master-v38431.js'
    ]
    for token in required:
        if token not in t: raise RuntimeError("Estrutura Campo Master ausente  "+token)

    # Public version sync
    t=re.sub(
      r'<title>ITA ARANDU MS · Atlas Geocientífico de Mato Grosso do Sul · V[^<]+</title>',
      '<title>ITA ARANDU MS · Atlas Geocientífico de Mato Grosso do Sul · V38.4.32</title>',
      t,
      count=1
    )

    # Visible version badge, idempotent
    if 'ita-version-badge' not in t:
        target='<div class="brand-main">ITA ARANDU MS</div>'
        if target not in t: raise RuntimeError("brand-main nao localizado")
        t=t.replace(target,target+'<span class="ita-version-badge">V38.4.32</span>',1)
    else:
        t=re.sub(r'(<span class="ita-version-badge">)V[^<]+(</span>)',r'\1V38.4.32\2',t,count=1)

    # Meu caderno is no longer partial
    old='<div class="aprender-card-top"><h3>Meu caderno</h3><span class="aprender-status partial">parcial</span></div>'
    new='<div class="aprender-card-top"><h3>Meu caderno</h3><span class="aprender-status functional">funcional</span></div>'
    if old not in t: raise RuntimeError("Estado antigo de Meu caderno nao localizado")
    t=t.replace(old,new,1)

    oldp='Utiliza os registros locais do módulo Campo como primeiro caderno digital. A interface própria de caderno, exportação pedagógica e relatório do estudante serão incorporadas em versões posteriores.'
    newp='Caderno de Campo Geocientífico Digital integrado. Organiza estações, GPS, litologia, observação, medidas, amostras, GeoFoto, croquis, revisão e exportações locais sem incorporar automaticamente registros de campo à base científica do Atlas.'
    if oldp not in t: raise RuntimeError("Texto antigo de Meu caderno nao localizado")
    t=t.replace(oldp,newp,1)

    oldfoot='<b>Versão inicial do Modo Aprender</b>'
    newfoot='<b>Modo Aprender integrado ao Campo</b>'
    if oldfoot in t:t=t.replace(oldfoot,newfoot,1)

    oldspan='Esta integração não declara concluídos os módulos educacionais. Onde estou, Campo e leitura do Atlas já possuem ligação funcional. Missões e Meu caderno constituem a estrutura inicial para desenvolvimento progressivo sem alterar o núcleo científico do Atlas.'
    newsp='Onde estou, Campo, Meu caderno e leitura do Atlas possuem ligação funcional. As missões permanecem como estrutura pedagógica evolutiva, enquanto o Caderno de Campo 2.0 já oferece aquisição geocientífica estruturada, revisão e exportação local.'
    if oldspan in t:t=t.replace(oldspan,newsp,1)

    css_tag='<link rel="stylesheet" href="./assets/css/campo-ux-v38432.css?v=38.4.32">'
    if "campo-ux-v38432.css" not in t:
        t=t.replace("</head>",css_tag+"\n</head>",1)

    js_tag='<script src="./assets/js/campo-ux-v38432.js?v=38.4.32"></script>'
    if "campo-ux-v38432.js" not in t:
        # load after Campo Master
        pat=r'(<script\b[^>]*src=["\']\./assets/js/campo-master-v38431\.js(?:\?[^"\']*)?["\'][^>]*></script>)'
        m=re.search(pat,t,re.I)
        if not m: raise RuntimeError("Carga do Campo Master nao localizada")
        t=t[:m.end()]+"\n"+js_tag+t[m.end():]

    write(index,t)

    for rel in ["docs/assets/css/campo-ux-v38432.css","docs/assets/js/campo-ux-v38432.js"]:
        src=payload/rel
        dst=repo/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)

    sw=repo/"docs/service-worker.js"
    if sw.exists():
        s=read(sw)
        s=re.sub(
          r"const ITA_CACHE\s*=\s*['\"][^'\"]+['\"];",
          "const ITA_CACHE = 'ita-arandu-v38-4-32-campo-ux-fecho';",
          s,
          count=1
        )
        marker="const ITA_CORE = ["
        entries=[
          './assets/css/campo-ux-v38432.css?v=38.4.32',
          './assets/js/campo-ux-v38432.js?v=38.4.32'
        ]
        if marker in s:
            for e in entries:
                if e not in s:s=s.replace(marker,marker+'\n  "'+e+'",',1)
        write(sw,s)

    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=read(ch)
        if "V38.4.32 · Fechamento UX do Campo" not in c:
            c=c.rstrip()+"""

## V38.4.32 · Fechamento UX do Campo · 2026-08-15

- Sincroniza a versão pública com V38.4.32.
- Atualiza Meu caderno de parcial para funcional.
- Renomeia os modos para Estudante · Essencial e Especialista · Avançado.
- Converte os 14 blocos do Campo em acordeões inteligentes no celular.
- Mantém os blocos abertos em telas maiores.
- Adiciona navegação Anterior, Próximo e seletor de seção.
- Faz a completude indicar também o primeiro item essencial pendente.
- Permite tocar no checklist móvel para saltar para um bloco pendente.
- Não altera o esquema científico 2.0, IndexedDB, camadas, snapshots ou índices.
"""
            write(ch,c+"\n")

    write(repo/"VERSION",FINAL+"\n")
    print("V38.4.32 fechamento UX do Campo aplicado")

if __name__=="__main__": main()
