
from pathlib import Path
import argparse,re,shutil,json
BASE="V38.4.32-CAMPO-UX-FECHO-20260815"
FINAL="V38.4.33-CLINOMETRO-VISUAL-ARANDU-1.0-20260815"
REFS=json.loads('[["174", "Lee, S., Suh, J., &amp; Park, H. D. (2013). Smart Compass-Clinometer: A smartphone application for easy and rapid geological site investigation. <i>Computers &amp; Geosciences, 61</i>, 32–42. https://doi.org/10.1016/j.cageo.2013.07.014", "https://doi.org/10.1016/j.cageo.2013.07.014", "Fundamenta o uso e a validação de sensores de smartphone para bússola-clinômetro geológico."], ["175", "Novakova, L., &amp; Pavlis, T. L. (2017). Assessment of the precision of smart phones and tablets for measurement of planar orientations: A case study. <i>Journal of Structural Geology, 97</i>, 93–103. https://doi.org/10.1016/j.jsg.2017.02.015", "https://doi.org/10.1016/j.jsg.2017.02.015", "Avalia a precisão de dispositivos móveis para orientações planares e sustenta a cautela entre dispositivos."], ["176", "Allmendinger, R. W., Siron, C. R., &amp; Scott, C. P. (2017). Structural data collection with mobile devices: Accuracy, redundancy, and best practices. <i>Journal of Structural Geology, 102</i>, 98–112. https://doi.org/10.1016/j.jsg.2017.07.011", "https://doi.org/10.1016/j.jsg.2017.07.011", "Fundamenta redundância, incerteza, boas práticas e controle de interferência magnética."], ["177", "Wang, J., Ju, N., He, C., Cai, J., &amp; Zheng, D. (2020). Assessment of the accuracy of several methods for measuring the spatial attitude of geological bodies using an Android smartphone. <i>Computers &amp; Geosciences, 136</i>, 104393. https://doi.org/10.1016/j.cageo.2019.104393", "https://doi.org/10.1016/j.cageo.2019.104393", "Compara métodos de cálculo de atitude espacial em smartphone Android."], ["178", "World Wide Web Consortium. (2025, February 12). <i>Device Orientation and Motion</i> (W3C Candidate Recommendation Draft). https://www.w3.org/TR/orientation-event/", "https://www.w3.org/TR/orientation-event/", "Especificação técnica para eixos, ângulos, orientação relativa, orientação absoluta e permissões."]]')
def read(p):return Path(p).read_text(encoding="utf-8-sig")
def write(p,t):Path(p).write_text(t,encoding="utf-8",newline="\n")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo",required=True);ap.add_argument("--payload",required=True);a=ap.parse_args()
    repo=Path(a.repo).resolve();payload=Path(a.payload).resolve()
    cur=read(repo/"VERSION").strip()
    if cur!=BASE:raise RuntimeError("Base incorreta  "+cur+" | esperada  "+BASE)
    index=repo/"docs/index.html";t=read(index)
    target='<div class="ita-array-head ita-spaced"><span>Medidas</span><button class="action-btn primary" type="button" id="campoAddMedida">Adicionar medida</button></div>'
    if target not in t:raise RuntimeError("Bloco de medidas nao localizado")
    launch='<div class="ita-clino-launch"><div><b>Clinômetro Visual ARANDU</b><small>Contato assistido + estimativa visual por câmera, repetições, dispersão e validação frente a instrumento de referência.</small></div><button class="action-btn primary" type="button" id="abrirClinometroArandu">Abrir instrumento</button><a class="action-btn" href="./documentos/metodologia-clinometro-visual-arandu.html" target="_blank" rel="noopener">Metodologia</a></div>'
    if "abrirClinometroArandu" not in t:t=t.replace(target,launch+target,1)
    modal=(payload/"CLINOMETRO_MODAL.html").read_text(encoding="utf-8")
    if 'id="clinometroAranduModal"' not in t:
        pos=t.find('<div class="modal" id="autoriaModal">')
        if pos<0:raise RuntimeError("Ponto de insercao modal nao localizado")
        t=t[:pos]+modal+"\n"+t[pos:]
    css_tag='<link rel="stylesheet" href="./assets/css/clinometro-visual-v38433.css?v=38.4.33">'
    if "clinometro-visual-v38433.css" not in t:t=t.replace("</head>",css_tag+"\n</head>",1)
    js_tag='<script src="./assets/js/clinometro-visual-v38433.js?v=38.4.33"></script>'
    if "clinometro-visual-v38433.js" not in t:
        pat=r'(<script\b[^>]*src=["\']\./assets/js/campo-ux-v38432\.js(?:\?[^"\']*)?["\'][^>]*></script>)'
        m=re.search(pat,t,re.I)
        if not m:raise RuntimeError("Campo UX V38.4.32 nao localizado")
        t=t[:m.end()]+"\n"+js_tag+t[m.end():]
    t=re.sub(r'(<span class="ita-version-badge">)V[^<]+(</span>)',r'\1V38.4.33\2',t,count=1)
    t=re.sub(r'<title>ITA ARANDU MS · Atlas Geocientífico de Mato Grosso do Sul · V[^<]+</title>','<title>ITA ARANDU MS · Atlas Geocientífico de Mato Grosso do Sul · V38.4.33</title>',t,count=1)
    write(index,t)
    for rel in ["docs/assets/css/clinometro-visual-v38433.css","docs/assets/js/clinometro-visual-v38433.js","docs/documentos/metodologia-clinometro-visual-arandu.html"]:
        src=payload/rel;dst=repo/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    bib=repo/"docs/referencias/index.html";b=read(bib)
    marker="<script>const q=document.getElementById('q');"
    if marker not in b:raise RuntimeError("Marcador final da bibliografia nao localizado")
    for rid,citation,url,note in REFS:
        if f'id="ref-{rid}"' in b:continue
        section='<section class="entry reference-entry" data-search="instrumentos de campo clinometro smartphone orientacao estrutural ref-'+rid+'" id="ref-'+rid+'"><h2>REF-'+rid+'</h2><div class="meta">Instrumentos de campo · referência metodológica · APA 7</div><div class="source">'+citation+' <a href="'+url+'" rel="noopener" target="_blank">fonte</a></div><p>'+note+'</p></section>'
        b=b.replace(marker,section+marker,1)
    b=b.replace("171 referências no registro mestre","176 referências no registro mestre")
    if 'id="instrumentos-campo"' not in b:
        lead='<h1 id="instrumentos-campo">Instrumentos digitais de campo</h1><p class="section-lead">Referências metodológicas para aquisição estrutural assistida por sensores móveis. Estabilidade do sensor não equivale a precisão metrológica universal.</p>'
        first='<section class="entry reference-entry" data-search="instrumentos de campo clinometro smartphone orientacao estrutural ref-174"'
        b=b.replace(first,lead+first,1)
    if 'href="#instrumentos-campo"' not in b:
        b=b.replace('<a class="badge" href="#indices">Índices</a>','<a class="badge" href="#instrumentos-campo">Instrumentos</a><a class="badge" href="#indices">Índices</a>',1)
    write(bib,b)
    sw=repo/"docs/service-worker.js"
    if sw.exists():
        s=read(sw);s=re.sub(r"const ITA_CACHE\s*=\s*['\"][^'\"]+['\"];","const ITA_CACHE = 'ita-arandu-v38-4-33-clinometro';",s,count=1)
        m="const ITA_CORE = ["
        for e in ['./assets/css/clinometro-visual-v38433.css?v=38.4.33','./assets/js/clinometro-visual-v38433.js?v=38.4.33','./documentos/metodologia-clinometro-visual-arandu.html','./referencias/index.html']:
            if m in s and e not in s:s=s.replace(m,m+'\n  "'+e+'",',1)
        write(sw,s)
    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=read(ch)
        if "V38.4.33 · Clinômetro Visual ARANDU" not in c:
            c=c.rstrip()+"\n\n## V38.4.33 · Clinômetro Visual ARANDU 1.0 · 2026-08-15\n\n- Integra contato assistido e estimativa visual assistida por câmera.\n- Preserva repetições, estatística, origem, referência angular e validação.\n- Inclui metodologia, fórmulas, limitações e referências APA 7.\n- Acrescenta REF-174 a REF-178 à bibliografia mestre.\n- Não altera camadas, snapshots ou índices.\n"
            write(ch,c+"\n")
    write(repo/"VERSION",FINAL+"\n")
    print("V38.4.33 Clinometro Visual ARANDU aplicado")
if __name__=="__main__":main()
