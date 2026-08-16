
from pathlib import Path
import argparse,re,shutil,json
BASE="V38.4.37-ESTEREOGRAMA-CALCULADORA-1.0-20260815"
FINAL="V38.4.37A-CONTADOR-VISITAS-1.0-20260815"
REFS=json.loads('[{"key": "goatcounter_main", "fingerprint": "goatcounter.com/", "url": "https://www.goatcounter.com/", "citation": "GoatCounter. (n.d.). <i>GoatCounter · Open source web analytics</i>. https://www.goatcounter.com/", "note": "Descrição institucional do projeto, arquitetura orientada à privacidade, código aberto e condições gerais do serviço alojado."}, {"key": "goatcounter_visitor", "fingerprint": "goatcounter.com/help/visitor-counter", "url": "https://www.goatcounter.com/help/visitor-counter", "citation": "GoatCounter. (n.d.). <i>Visitor counter</i>. https://www.goatcounter.com/help/visitor-counter", "note": "Documentação do contador público JSON, caminho TOTAL, filtros start/end e política de cache."}, {"key": "goatcounter_js", "fingerprint": "goatcounter.com/help/js", "url": "https://www.goatcounter.com/help/js", "citation": "GoatCounter. (n.d.). <i>JavaScript API</i>. https://www.goatcounter.com/help/js", "note": "Documentação do script de contagem e comportamento durante desenvolvimento local."}]')

def read(p): return Path(p).read_text(encoding="utf-8-sig")
def write(p,t): Path(p).write_text(t,encoding="utf-8",newline="\n")
def ids(t): return [int(x) for x in re.findall(r'id=["\']ref-(\d+)["\']',t,re.I)]

def ref_for(t,fp):
    pos=t.lower().find(fp.lower())
    if pos<0:return None
    starts=list(re.finditer(r'<section\b[^>]*\bid=["\']ref-(\d+)["\'][^>]*>',t[:pos+1],re.I))
    if not starts:return None
    m=starts[-1]; end=t.find("</section>",m.end())
    return int(m.group(1)) if end>=pos else None

def integrate_refs(t):
    marker="<script>const q=document.getElementById('q');"
    if marker not in t: raise RuntimeError("Marcador do registro mestre nao localizado")
    used=set(ids(t)); n=max(used or {0})+1; mapping={}; blocks=[]
    for r in REFS:
        old=ref_for(t,r["fingerprint"])
        if old is not None:
            mapping[r["key"]]={"id":old,"status":"reused"}; continue
        while n in used:n+=1
        rid=n;used.add(rid);n+=1
        mapping[r["key"]]={"id":rid,"status":"added"}
        blocks.append('<section class="entry reference-entry" data-search="contador visitas estatisticas privacidade goatcounter '+r["key"]+'" id="ref-'+str(rid)+'"><h2>REF-'+str(rid)+'</h2><div class="meta">Uso público do Atlas · contador de visitas · APA 7</div><div class="source">'+r["citation"]+' <a href="'+r["url"]+'" rel="noopener" target="_blank">fonte</a></div><p>'+r["note"]+'</p></section>')
    t=t.replace(marker,''.join(blocks)+marker,1)
    allids=ids(t)
    if len(allids)!=len(set(allids)):raise RuntimeError("IDs REF duplicados")
    t=re.sub(r'\b\d+\s+referências no registro mestre\b',str(len(set(allids)))+' referências no registro mestre',t,count=1)
    return t,mapping

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    ap.add_argument("--payload",required=True)
    ap.add_argument("--code",required=True)
    a=ap.parse_args()
    code=a.code.strip().lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,62}',code):
        raise RuntimeError("Codigo GoatCounter invalido")
    repo=Path(a.repo).resolve(); payload=Path(a.payload).resolve()
    cur=read(repo/"VERSION").strip()
    if cur!=BASE:raise RuntimeError("Base incorreta  "+cur+" | esperada  "+BASE)

    tpl=read(payload/"docs/assets/js/contador-visitas-v38437a.js.tpl")
    js=tpl.replace("__GOATCODE__",code)
    dst=repo/"docs/assets/js/contador-visitas-v38437a.js"
    dst.parent.mkdir(parents=True,exist_ok=True);write(dst,js)
    shutil.copy2(payload/"docs/documentos/metodologia-contador-visitas.html",repo/"docs/documentos/metodologia-contador-visitas.html")

    idx=repo/"docs/index.html";t=read(idx)
    tracker='<script data-goatcounter="https://'+code+'.goatcounter.com/count" async src="https://gc.zgo.at/count.v5.js" crossorigin="anonymous" integrity="sha384-atnOLvQb9t+jTSipvd75X2yginT4PjVbqDdlJAmxMm+wYElFmeR6EmLP5bYeoRVQ"></script>'
    app='<script src="./assets/js/contador-visitas-v38437a.js?v=38.4.37a"></script>'
    if 'data-goatcounter=' not in t:t=t.replace("</body>",tracker+"\n"+app+"\n</body>",1)
    elif 'contador-visitas-v38437a.js' not in t:t=t.replace("</body>",app+"\n</body>",1)
    t=re.sub(r'(<span class="ita-version-badge">)V[^<]+(</span>)',r'\1V38.4.37A\2',t,count=1)
    write(idx,t)

    bib=repo/"docs/referencias/index.html";b,mapping=integrate_refs(read(bib));write(bib,b)
    side={"module":"Contador agregado de visitas","version":"1.0","date":"2026-08-15","provider":"GoatCounter","site_code":code,"references":[{"key":r["key"],"ref_id":"REF-"+str(mapping[r["key"]]["id"]),"status":mapping[r["key"]]["status"],"url":r["url"]} for r in REFS]}
    (repo/"docs/documentos/contador-visitas-referencias.json").write_text(json.dumps(side,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    sw=repo/"docs/service-worker.js"
    if sw.exists():
        s=read(sw)
        s=re.sub(r"const ITA_CACHE\s*=\s*['\"][^'\"]+['\"];","const ITA_CACHE = 'ita-arandu-v38-4-37a-contador-visitas';",s,count=1)
        marker="const ITA_CORE = ["
        for e in ['./assets/js/contador-visitas-v38437a.js?v=38.4.37a','./documentos/metodologia-contador-visitas.html','./documentos/contador-visitas-referencias.json']:
            if marker in s and e not in s:s=s.replace(marker,marker+'\n  "'+e+'",',1)
        write(sw,s)

    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=read(ch)
        if "V38.4.37A · Contador agregado de visitas" not in c:
            c=c.rstrip()+"\n\n## V38.4.37A · Contador agregado de visitas · 2026-08-15\n\n- Ativa contagem pública por GoatCounter.\n- Exibe visitas acumuladas, hoje, últimos sete dias e mês atual.\n- Usa somente o contador público JSON para leitura dos indicadores.\n- Não inclui token de API no navegador ou no repositório.\n- Não simula valores quando o provedor está indisponível.\n- Integra metodologia e referências APA 7.\n- Não altera camadas, snapshots ou índices.\n"
            write(ch,c+"\n")
    write(repo/"VERSION",FINAL+"\n")
    print("V38.4.37A contador de visitas aplicado")
    print("GoatCounter",code)

if __name__=="__main__":main()
