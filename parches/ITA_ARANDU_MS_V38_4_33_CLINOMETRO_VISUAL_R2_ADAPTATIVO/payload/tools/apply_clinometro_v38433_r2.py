
from pathlib import Path
import argparse,re,shutil,json,html

BASE="V38.4.32-CAMPO-UX-FECHO-20260815"
FINAL="V38.4.33-CLINOMETRO-VISUAL-ARANDU-1.0-R2-20260815"
REFS=json.loads('[{"key": "lee2013", "citation": "Lee, S., Suh, J., &amp; Park, H. D. (2013). Smart Compass-Clinometer: A smartphone application for easy and rapid geological site investigation. <i>Computers &amp; Geosciences, 61</i>, 32–42. https://doi.org/10.1016/j.cageo.2013.07.014", "url": "https://doi.org/10.1016/j.cageo.2013.07.014", "fingerprint": "10.1016/j.cageo.2013.07.014", "note": "Fundamenta o uso e a validação de sensores de smartphone para bússola-clinômetro geológico."}, {"key": "novakova2017", "citation": "Novakova, L., &amp; Pavlis, T. L. (2017). Assessment of the precision of smart phones and tablets for measurement of planar orientations: A case study. <i>Journal of Structural Geology, 97</i>, 93–103. https://doi.org/10.1016/j.jsg.2017.02.015", "url": "https://doi.org/10.1016/j.jsg.2017.02.015", "fingerprint": "10.1016/j.jsg.2017.02.015", "note": "Avalia a precisão de dispositivos móveis para orientações planares e sustenta a cautela entre dispositivos."}, {"key": "allmendinger2017", "citation": "Allmendinger, R. W., Siron, C. R., &amp; Scott, C. P. (2017). Structural data collection with mobile devices: Accuracy, redundancy, and best practices. <i>Journal of Structural Geology, 102</i>, 98–112. https://doi.org/10.1016/j.jsg.2017.07.011", "url": "https://doi.org/10.1016/j.jsg.2017.07.011", "fingerprint": "10.1016/j.jsg.2017.07.011", "note": "Fundamenta redundância, incerteza, boas práticas e controle de interferência magnética."}, {"key": "wang2020", "citation": "Wang, J., Ju, N., He, C., Cai, J., &amp; Zheng, D. (2020). Assessment of the accuracy of several methods for measuring the spatial attitude of geological bodies using an Android smartphone. <i>Computers &amp; Geosciences, 136</i>, 104393. https://doi.org/10.1016/j.cageo.2019.104393", "url": "https://doi.org/10.1016/j.cageo.2019.104393", "fingerprint": "10.1016/j.cageo.2019.104393", "note": "Compara métodos de cálculo de atitude espacial em smartphone Android."}, {"key": "w3c2025", "citation": "World Wide Web Consortium. (2025, February 12). <i>Device Orientation and Motion</i> (W3C Candidate Recommendation Draft). https://www.w3.org/TR/orientation-event/", "url": "https://www.w3.org/TR/orientation-event/", "fingerprint": "https://www.w3.org/TR/orientation-event/", "note": "Especificação técnica para eixos, ângulos, orientação relativa, orientação absoluta e permissões."}]')

def read(p):
    return Path(p).read_text(encoding="utf-8-sig")

def write(p,t):
    Path(p).write_text(t,encoding="utf-8",newline="\n")

def unique_ref_ids(text):
    return [int(x) for x in re.findall(r'id=["\']ref-(\d+)["\']',text,re.I)]

def find_ref_id_for_fingerprint(text,fingerprint):
    pos=text.lower().find(fingerprint.lower())
    if pos < 0:
        return None
    # Prefer the section enclosing the occurrence
    starts=list(re.finditer(r'<section\b[^>]*\bid=["\']ref-(\d+)["\'][^>]*>',text[:pos+1],re.I))
    if not starts:
        return None
    m=starts[-1]
    close=text.find("</section>",m.end())
    if close < 0 or pos > close:
        return None
    return int(m.group(1))

def allocate_refs(text):
    ids=set(unique_ref_ids(text))
    next_id=max(ids or {0})+1
    mapping={}
    missing=[]
    for ref in REFS:
        existing=find_ref_id_for_fingerprint(text,ref["fingerprint"])
        if existing is not None:
            mapping[ref["key"]]={"id":existing,"status":"reused","fingerprint":ref["fingerprint"]}
            continue
        while next_id in ids:
            next_id+=1
        mapping[ref["key"]]={"id":next_id,"status":"added","fingerprint":ref["fingerprint"]}
        missing.append((next_id,ref))
        ids.add(next_id)
        next_id+=1
    return mapping,missing

def insert_bibliography(text):
    marker="<script>const q=document.getElementById('q');"
    if marker not in text:
        raise RuntimeError("Marcador final da bibliografia nao localizado")

    mapping,missing=allocate_refs(text)

    # Add only references that are semantically absent
    new_entries=[]
    for rid,ref in missing:
        new_entries.append(
            '<section class="entry reference-entry" '
            'data-search="instrumentos de campo clinometro smartphone orientacao estrutural '+ref["key"]+'" '
            'id="ref-'+str(rid)+'">'
            '<h2>REF-'+str(rid)+'</h2>'
            '<div class="meta">Instrumentos de campo · referência metodológica · APA 7</div>'
            '<div class="source">'+ref["citation"]+' '
            '<a href="'+ref["url"]+'" rel="noopener" target="_blank">fonte</a></div>'
            '<p>'+ref["note"]+'</p>'
            '</section>'
        )

    # Always create an independent thematic heading. No dependency on a specific REF number.
    if 'id="instrumentos-campo"' not in text:
        links=[]
        for ref in REFS:
            rid=mapping[ref["key"]]["id"]
            links.append('<a class="badge" href="#ref-'+str(rid)+'">REF-'+str(rid)+'</a>')
        thematic=(
            '<h1 id="instrumentos-campo">Instrumentos digitais de campo</h1>'
            '<p class="section-lead">Referências metodológicas para aquisição estrutural assistida por sensores móveis. '
            'Estabilidade operacional do sensor não equivale a precisão metrológica universal.</p>'
            '<div class="principle"><b>Clinômetro Visual ARANDU · referências vinculadas</b>'
            '<div class="nav">'+"".join(links)+'</div></div>'
        )
    else:
        thematic=""

    block=thematic+"".join(new_entries)
    if block:
        text=text.replace(marker,block+marker,1)

    # Navigation badge, inserted adaptively
    if 'href="#instrumentos-campo"' not in text:
        idx=re.search(r'<div class="nav">',text,re.I)
        if idx:
            end=text.find("</div>",idx.end())
            if end>=0:
                text=text[:end]+'<a class="badge" href="#instrumentos-campo">Instrumentos</a>'+text[end:]

    # Count actual UNIQUE reference IDs, not a hardcoded prior count
    all_ids=unique_ref_ids(text)
    unique_count=len(set(all_ids))
    if len(all_ids)!=unique_count:
        dup=sorted({x for x in all_ids if all_ids.count(x)>1})
        raise RuntimeError("IDs bibliograficos duplicados detectados  "+",".join(map(str,dup)))
    text=re.sub(r'\b\d+\s+referências no registro mestre\b',str(unique_count)+' referências no registro mestre',text,count=1)

    return text,mapping,unique_count

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
        'id="campoAddMedida"',
        'campo-master-v38431.js',
        'campo-ux-v38432.js'
    ]
    for token in required:
        if token not in t:
            raise RuntimeError("Estrutura Campo ausente  "+token)

    target='<div class="ita-array-head ita-spaced"><span>Medidas</span><button class="action-btn primary" type="button" id="campoAddMedida">Adicionar medida</button></div>'
    if target not in t:
        raise RuntimeError("Bloco de medidas nao localizado")

    launch='<div class="ita-clino-launch"><div><b>Clinômetro Visual ARANDU</b><small>Contato assistido + estimativa visual por câmera, repetições, dispersão e validação frente a instrumento de referência.</small></div><button class="action-btn primary" type="button" id="abrirClinometroArandu">Abrir instrumento</button><a class="action-btn" href="./documentos/metodologia-clinometro-visual-arandu.html" target="_blank" rel="noopener">Metodologia</a></div>'
    if "abrirClinometroArandu" not in t:
        t=t.replace(target,launch+target,1)

    modal=(payload/"CLINOMETRO_MODAL.html").read_text(encoding="utf-8")
    if 'id="clinometroAranduModal"' not in t:
        pos=t.find('<div class="modal" id="autoriaModal">')
        if pos<0:
            raise RuntimeError("Ponto de insercao do modal nao localizado")
        t=t[:pos]+modal+"\n"+t[pos:]

    css_tag='<link rel="stylesheet" href="./assets/css/clinometro-visual-v38433.css?v=38.4.33r2">'
    if "clinometro-visual-v38433.css" not in t:
        t=t.replace("</head>",css_tag+"\n</head>",1)

    js_tag='<script src="./assets/js/clinometro-visual-v38433.js?v=38.4.33r2"></script>'
    if "clinometro-visual-v38433.js" not in t:
        pat=r'(<script\b[^>]*src=["\']\./assets/js/campo-ux-v38432\.js(?:\?[^"\']*)?["\'][^>]*></script>)'
        m=re.search(pat,t,re.I)
        if not m:
            raise RuntimeError("Carga Campo UX V38.4.32 nao localizada")
        t=t[:m.end()]+"\n"+js_tag+t[m.end():]

    t=re.sub(r'(<span class="ita-version-badge">)V[^<]+(</span>)',r'\1V38.4.33\2',t,count=1)
    t=re.sub(
        r'<title>ITA ARANDU MS · Atlas Geocientífico de Mato Grosso do Sul · V[^<]+</title>',
        '<title>ITA ARANDU MS · Atlas Geocientífico de Mato Grosso do Sul · V38.4.33</title>',
        t,count=1
    )
    write(index,t)

    for rel in [
        "docs/assets/css/clinometro-visual-v38433.css",
        "docs/assets/js/clinometro-visual-v38433.js",
        "docs/documentos/metodologia-clinometro-visual-arandu.html"
    ]:
        src=payload/rel
        dst=repo/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)

    # Adaptive bibliography by semantic fingerprint
    bib=repo/"docs/referencias/index.html"
    b=read(bib)
    b,mapping,count=insert_bibliography(b)
    write(bib,b)

    # Traceability sidecar with the ACTUAL IDs used in this repository
    sidecar={
        "tool":"Clinômetro Visual ARANDU",
        "methodology_id":"ITA-CLINO-V1.0",
        "version":"V38.4.33-R2",
        "date":"2026-08-15",
        "bibliography_total_after_install":count,
        "references":[
            {
                "key":ref["key"],
                "ref_id":"REF-"+str(mapping[ref["key"]]["id"]),
                "status":mapping[ref["key"]]["status"],
                "fingerprint":ref["fingerprint"],
                "url":ref["url"]
            }
            for ref in REFS
        ]
    }
    side=repo/"docs/documentos/clinometro-visual-referencias.json"
    side.write_text(json.dumps(sidecar,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    # Add actual reference IDs to methodology
    meth=repo/"docs/documentos/metodologia-clinometro-visual-arandu.html"
    mt=read(meth)
    links=" · ".join(
        "REF-"+str(mapping[ref["key"]]["id"])
        for ref in REFS
    )
    anchor="<h2>Referências · APA 7</h2>"
    if anchor in mt and "IDs no registro mestre" not in mt:
        mt=mt.replace(anchor,anchor+'<p><b>IDs no registro mestre deste repositório</b> '+links+'</p>',1)
    write(meth,mt)

    sw=repo/"docs/service-worker.js"
    if sw.exists():
        s=read(sw)
        s=re.sub(
            r"const ITA_CACHE\s*=\s*['\"][^'\"]+['\"];",
            "const ITA_CACHE = 'ita-arandu-v38-4-33-clinometro-r2';",
            s,count=1
        )
        marker="const ITA_CORE = ["
        entries=[
            './assets/css/clinometro-visual-v38433.css?v=38.4.33r2',
            './assets/js/clinometro-visual-v38433.js?v=38.4.33r2',
            './documentos/metodologia-clinometro-visual-arandu.html',
            './documentos/clinometro-visual-referencias.json',
            './referencias/index.html'
        ]
        if marker in s:
            for e in entries:
                if e not in s:
                    s=s.replace(marker,marker+'\n  "'+e+'",',1)
        write(sw,s)

    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=read(ch)
        if "V38.4.33 · Clinômetro Visual ARANDU R2" not in c:
            c=c.rstrip()+"""

## V38.4.33 · Clinômetro Visual ARANDU R2 · 2026-08-15

- Integra contato assistido e estimativa visual assistida por câmera.
- Preserva repetições, estatística, origem, referência angular e validação.
- Inclui metodologia, fórmulas, limitações e bibliografia APA 7.
- A bibliografia é integrada por DOI ou URL canônica, sem pressupor números REF livres.
- Referências existentes são reutilizadas e referências novas recebem IDs acima do maior ID já utilizado.
- O total bibliográfico é recalculado pelos IDs únicos realmente presentes.
- Gera clinometro-visual-referencias.json com os IDs efetivamente vinculados.
- Não altera Campo Master, camadas, snapshots ou índices.
"""
            write(ch,c+"\n")

    write(repo/"VERSION",FINAL+"\n")
    print("V38.4.33 Clinometro Visual ARANDU R2 aplicado")
    for ref in REFS:
        info=mapping[ref["key"]]
        print(ref["key"],"REF-"+str(info["id"]),info["status"])
    print("Bibliografia total",count)

if __name__=="__main__":
    main()
