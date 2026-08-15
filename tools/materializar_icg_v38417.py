#!/usr/bin/env python3
from pathlib import Path
import argparse, json, math, statistics, datetime, hashlib, re

EXPECTED='V38.4.16-GATE-ICG-20260815'
VERSION='V38.4.17-ICG-CONHECIMENTO-GEOCIENTIFICO-20260815'
TOKEN='38.4.17'
CUT_DATE='2026-08-15'
DIMS=['IMC','IOD','ICP','IGC','IGQ','IGF','ICS']
SCALES=['250','500','1000']
SNAPS={
 'IMC':'docs/indices/imc_v32_snapshot.json',
 'IOD':'docs/indices/iod_v3848_snapshot.json',
 'ICP':'docs/indices/icp_v3849_snapshot.json',
 'IGC':'docs/indices/igc_v38410_snapshot.json',
 'IGQ':'docs/indices/igq_v38411_snapshot.json',
 'IGF':'docs/indices/igf_v38412_snapshot.json',
 'ICS':'docs/indices/ics_v38413_snapshot.json',
}
IDE='docs/indices/ide_v38415_snapshot.json'
POLICY='docs/indices/politica-icg-v38416.json'
GRIDS={
 '250':'docs/camadas/arquivos/malha_r5_250km2.geojson',
 '500':'docs/camadas/arquivos/malha_500km2.geojson',
 '1000':'docs/camadas/arquivos/malha_1000km2.geojson',
}
FORMULA='ICG_h = 100 × (n_obs/7) × M_h'
MFORM='M_h = max(0, μ_h − σ²_h/μ_h)'
SFORM='S_j = X_j / 100 apenas entre dimensões numéricas observadas'

def now_iso(): return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump_json(p,obj,compact=False):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None)+'\n',encoding='utf-8',newline='\n')
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def finite(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def num(v):
    if finite(v): return float(v)
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception: return None

def grid_ids(fc):
    ids=[]
    for f in fc.get('features',[]):
        hid=str((f.get('properties') or {}).get('hex_id') or '')
        if not hid: raise RuntimeError('malha contém feição sem hex_id')
        ids.append(hid)
    if len(ids)!=len(set(ids)): raise RuntimeError('malha contém hex_id duplicado')
    return ids

def score_from(snap,dim,scale,hid):
    grids=snap.get('grids',{}); g=grids.get(scale)
    if not isinstance(g,dict): return None
    if dim=='IMC':
        scores=g.get('scores')
        if isinstance(scores,dict):
            r=scores.get(hid)
            if isinstance(r,dict): return num(r.get('imc_100'))
            if isinstance(r,(list,tuple)) and r: return num(r[0])
        r=g.get(hid)
        if isinstance(r,dict): return num(r.get('imc_100'))
        if isinstance(r,(list,tuple)) and r: return num(r[0])
        return None
    r=g.get(hid)
    if isinstance(r,(list,tuple)) and r: return num(r[0])
    if isinstance(r,dict):
        for k in (dim.lower()+'_100',dim.lower(),'score','value'):
            if k in r: return num(r.get(k))
    return None

def ide_score(ide_snap,scale,hid):
    r=(ide_snap.get('grids',{}).get(scale) or {}).get(hid)
    if isinstance(r,(list,tuple)) and r: return num(r[0])
    if isinstance(r,dict): return num(r.get('ide_100') if 'ide_100' in r else r.get('ide'))
    return None

def support_class(n):
    if n<2:return 'não elegível'
    if n==2:return 'suporte limitado'
    if n<=4:return 'suporte parcial'
    if n<=6:return 'suporte amplo'
    return 'suporte completo'

def class_icg(v):
    if v is None:return 'sem síntese elegível'
    if v<20:return 'muito baixo'
    if v<40:return 'baixo'
    if v<60:return 'médio'
    if v<75:return 'alto'
    return 'muito alto'

def icg_from_scores(vals,alpha=1.0):
    obs={k:float(v) for k,v in vals.items() if finite(v)}
    for k,v in obs.items():
        if v<0 or v>100: raise RuntimeError(f'{k} fora do intervalo 0–100: {v}')
    n=len(obs)
    if n<2: return None
    ss=[v/100.0 for v in obs.values()]
    mu=statistics.fmean(ss)
    var=sum((x-mu)**2 for x in ss)/n
    m=0.0 if mu<=0 else max(0.0,mu-var/mu)
    c=(n/7.0)**float(alpha)
    icg=100.0*c*m
    cap=100.0*c
    if icg>cap+1e-9: raise RuntimeError(f'ICG supera teto teórico: {icg} > {cap}')
    return {'icg':icg,'m':m,'mu':mu,'var':var,'n_obs':n,'c':c,'observed':list(obs)}

def percentile(vals,p):
    vals=sorted(vals)
    if not vals:return None
    if len(vals)==1:return vals[0]
    x=(len(vals)-1)*p/100.0;i=int(math.floor(x));j=int(math.ceil(x))
    return vals[i] if i==j else vals[i]+(vals[j]-vals[i])*(x-i)
def rankdata(vals):
    pairs=sorted(enumerate(vals),key=lambda z:z[1]);r=[0.0]*len(vals);i=0
    while i<len(pairs):
        j=i+1
        while j<len(pairs) and pairs[j][1]==pairs[i][1]:j+=1
        rr=(i+j-1)/2+1
        for k in range(i,j):r[pairs[k][0]]=rr
        i=j
    return r
def spearman(a,b):
    pairs=[(x,y) for x,y in zip(a,b) if finite(x) and finite(y)]
    if len(pairs)<3:return None
    x=[p[0] for p in pairs];y=[p[1] for p in pairs];rx=rankdata(x);ry=rankdata(y);mx=statistics.fmean(rx);my=statistics.fmean(ry)
    den=(sum((u-mx)**2 for u in rx)*sum((v-my)**2 for v in ry))**0.5
    return None if den==0 else sum((u-mx)*(v-my) for u,v in zip(rx,ry))/den

def summary(rows):
    vals=[r['icg'] for r in rows.values() if r['icg'] is not None]
    classes={k:sum(1 for r in rows.values() if r['support']==k) for k in ['não elegível','suporte limitado','suporte parcial','suporte amplo','suporte completo']}
    nobs={str(k):sum(1 for r in rows.values() if r['n_obs']==k) for k in range(0,8)}
    return {'cells':len(rows),'cells_with_icg':len(vals),'cells_without_icg':len(rows)-len(vals),'icg_min':None if not vals else round(min(vals),4),'icg_p05':None if not vals else round(percentile(vals,5),4),'icg_median':None if not vals else round(statistics.median(vals),4),'icg_mean':None if not vals else round(statistics.fmean(vals),4),'icg_p95':None if not vals else round(percentile(vals,95),4),'icg_max':None if not vals else round(max(vals),4),'dimension_count_distribution':nobs,'support_classes':classes}

def compact_rows(rows):
    out={}
    for hid,r in rows.items():
        vals=r['values'];mask=0
        for i,d in enumerate(DIMS):
            if vals[d] is not None:mask|=1<<i
        out[hid]=[None if r['icg'] is None else round(r['icg'],4),None if r['m'] is None else round(r['m']*100,4),None if r['mu'] is None else round(r['mu'],8),None if r['var'] is None else round(r['var'],8),r['n_obs'],round(r['n_obs']/7,6),mask,None if r['ide'] is None else round(r['ide'],4),*[None if vals[d] is None else round(vals[d],4) for d in DIMS]]
    return out

def patch_catalog_obj(cat):
    layers=cat.get('layers',[]) if isinstance(cat,dict) else cat
    cfgs={'icg_250':('250','malha_r5_250km2',1554),'icg_500':('500','malha_500km2',793),'icg_1000':('1000','malha_1000km2',412)}
    for item in layers:
        iid=item.get('id') if isinstance(item,dict) else None
        if iid in cfgs:
            scale,grid,count=cfgs[iid]
            item.update({'status':'incorporada','count':count,'source':'ITA ARANDU MS · ICG V38.4.17 · sete dimensões base certificadas','validation':'V38.4.17 · agregação parcialmente não compensatória · gate V38.4.16 · sensibilidade α auditada','note':'Índice de conhecimento geocientífico integrado. Requer pelo menos duas dimensões observadas. null permanece ausência e não recebe zero. O fator n_obs/7 penaliza suporte estreito e o componente M penaliza desequilíbrio. IDE permanece indicador complementar e não entra na fórmula.','derive_type':'icg_snapshot_v38417','grid_source_id':grid,'icg_scale':scale,'reference_ids':['REF-104','REF-105','REF-115']})
    return cat

def patch_catalog_files(repo):
    jp=repo/'docs/camadas/catalogo-local.json'
    if jp.exists(): dump_json(jp,patch_catalog_obj(load_json(jp)))

def patch_app(repo):
    p=repo/'docs/assets/js/app.js';txt=p.read_text(encoding='utf-8-sig')
    prefix='const CATALOG=';pos=txt.find(prefix)
    if pos<0:raise RuntimeError('CATALOG não localizado em app.js')
    pos+=len(prefix);cat,end=json.JSONDecoder().raw_decode(txt[pos:]);cat=patch_catalog_obj(cat);txt=txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:]
    color_marker="function ideColor(v){const c=ideClass(v);return ITA_IDE_COLORS[c]||'rgba(0,0,0,0)'}"
    if 'const ITA_ICG_COLORS=' not in txt:
        add="\nconst ITA_ICG_COLORS={'muito baixo':'#e8eaf6','baixo':'#c5cae9','médio':'#9fa8da','alto':'#5c6bc0','muito alto':'#283593'};\nfunction icgClass(v){const x=Number(v);if(v===null||v===undefined||!Number.isFinite(x))return'sem síntese elegível';if(x<20)return'muito baixo';if(x<40)return'baixo';if(x<60)return'médio';if(x<75)return'alto';return'muito alto'}\nfunction icgColor(v){const c=icgClass(v);return ITA_ICG_COLORS[c]||'rgba(0,0,0,0)'}"
        if color_marker not in txt:raise RuntimeError('marcador ideColor não encontrado em app.js')
        txt=txt.replace(color_marker,color_marker+add,1)
    fs0=txt.find('function featureStyle(cfg,feat){');fs1=txt.find('function pathGeometry',fs0)
    if fs0<0 or fs1<0:raise RuntimeError('featureStyle não localizado')
    fseg=txt[fs0:fs1]
    if "st.renderer==='index_icg'" not in fseg:
        marker="if(st.renderer==='index_ide'){fill=ideColor(p.ide_100);stroke='#4a4a4a';}"
        if marker not in fseg:raise RuntimeError('renderer IDE não encontrado em featureStyle')
        fseg=fseg.replace(marker,marker+" if(st.renderer==='index_icg'){fill=icgColor(p.icg_100);stroke='#4a4a4a';}",1)
        txt=txt[:fs0]+fseg+txt[fs1:]
    lg0=txt.find('function layerLegendHtml(cfg){');lg1=txt.find('function updateLegend',lg0)
    if lg0<0:raise RuntimeError('layerLegendHtml não localizado')
    if lg1<0:lg1=txt.find('function ',lg0+30)
    lseg=txt[lg0:lg1 if lg1>lg0 else len(txt)]
    if "if(st.renderer==='index_icg')return" not in lseg:
        marker="if(st.renderer==='index_ide')return";i=lseg.find(marker)
        if i<0:raise RuntimeError('legenda IDE não encontrada em layerLegendHtml')
        e=lseg.find('\n',i)
        if e<0:e=len(lseg)
        legend=" if(st.renderer==='index_icg')return `<div class=\"legend-layer-title\">${esc(cfg.name)}</div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#e8eaf6;border:1px solid #4a4a4a\"></span><span>0–&lt;20 · muito baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#c5cae9;border:1px solid #4a4a4a\"></span><span>20–&lt;40 · baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#9fa8da;border:1px solid #4a4a4a\"></span><span>40–&lt;60 · médio</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#5c6bc0;border:1px solid #4a4a4a\"></span><span>60–&lt;75 · alto</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#283593;border:1px solid #4a4a4a\"></span><span>75–100 · muito alto</span></div><div class=\"legend-note\">ICG = 100 × (n_obs/7) × max(0, μ − σ²/μ). Exige n_obs ≥ 2. null não vira zero. A ficha publica amplitude de suporte, dimensões ausentes, IDE companheiro e estado do IGF no corte.</div>`;"
        lseg=lseg[:e+1]+legend+'\n'+lseg[e+1:];txt=txt[:lg0]+lseg+txt[lg1 if lg1>lg0 else len(txt):]
    if 'async function buildIcgSnapshotV38417' not in txt:
        marker='async function buildIdeSnapshotV38415';i=txt.find(marker)
        if i<0:raise RuntimeError('builder IDE não encontrado')
        builder="""async function buildIcgSnapshotV38417(cfg){
 const gridCfg=CATALOG.layers.find(x=>x.id===cfg.grid_source_id);
 if(!gridCfg)throw new Error('Malha do ICG V38.4.17 não encontrada no catálogo');
 const grid=await ensure(gridCfg),key=String(cfg.icg_scale||''),scores=window.ITA_ICG_V38417?.grids?.[key],meta=window.ITA_ICG_V38417?.metadata||{};
 if(!scores)throw new Error('Snapshot ICG V38.4.17 não encontrado para esta escala. Execute o materializador do patch.');
 const dims=['IMC','IOD','ICP','IGC','IGQ','IGF','ICS'];
 const features=(grid.features||[]).map(hf=>{const hid=String(hf.properties?.hex_id||''),r=scores[hid];if(!r)return {...hf,properties:{...(hf.properties||{}),icg_100:null,classe_icg:'sem síntese elegível'}};const [icg,m100,mu,vvar,nObs,frac,mask,ide,imc,iod,icp,igc,igq,igf,ics]=r;const obs=dims.filter((d,j)=>(mask&(1<<j))!==0),aus=dims.filter((d,j)=>(mask&(1<<j))===0);const support=nObs<2?'não elegível':nObs===2?'suporte limitado':nObs<=4?'suporte parcial':nObs<=6?'suporte amplo':'suporte completo';return {...hf,properties:{...(hf.properties||{}),icg_100:icg,classe_icg:icgClass(icg),m_noncomp_100:m100,mu_obs:mu,var_obs:vvar,n_dim_observadas:nObs,fracao_dim_observadas:frac,dimensoes_observadas:obs.join(' · '),dimensoes_ausentes:aus.join(' · '),classe_suporte_icg:support,ide_100_companheiro:ide,imc_100_base:imc,iod_100_base:iod,icp_100_base:icp,igc_100_base:igc,igq_100_base:igq,igf_100_base:igf,ics_100_base:ics,status_igf_no_corte:meta.igf_cut_status||'MT NAO_AVALIAVEL_NO_CORTE',formula:'ICG_h = 100 × (n_obs/7) × M_h',formula_M:'M_h = max(0, μ_h − σ²_h/μ_h)',regra_elegibilidade:'mínimo 2 dimensões numéricas observadas na mesma escala',regra_null:'null permanece ausente e não recebe zero. Zero numérico observado continua zero.',regra_ide:'IDE é indicador companheiro e não entra na fórmula ICG.',metodo:'V38.4.17 · síntese parcialmente não compensatória · gate V38.4.16',data_corte:meta.cut_date||'2026-08-15'}};});
 return {type:'FeatureCollection',features,atlas_metadata:{indice:'ICG',versao:'V38.4.17',escala:key,formula:'ICG_h = 100 × (n_obs/7) × max(0, μ − σ²/μ)',elegibilidade:'n_obs ≥ 2',regra_null:'null não é zero',regra_ide:'IDE não entra na fórmula',limite:'ICG mede conhecimento geocientífico integrado documentado. Não mede favorabilidade mineral, recurso, reserva ou valor econômico.'}};
}
"""
        txt=txt[:i]+builder+txt[i:]
    chain="if(!d&&cfg.derive_type==='ide_snapshot_v38415')d=await buildIdeSnapshotV38415(cfg);"
    if "derive_type==='icg_snapshot_v38417'" not in txt:
        if chain not in txt:raise RuntimeError('cadeia derive IDE não encontrada')
        txt=txt.replace(chain,chain+"if(!d&&cfg.derive_type==='icg_snapshot_v38417')d=await buildIcgSnapshotV38417(cfg);",1)
    scale_marker="const IDE_SCALE_LAYERS=['ide_250','ide_500','ide_1000'];"
    if 'const ICG_SCALE_LAYERS=' not in txt:
        if scale_marker not in txt:raise RuntimeError('grupo de escalas IDE não encontrado')
        txt=txt.replace(scale_marker,scale_marker+" const ICG_SCALE_LAYERS=['icg_250','icg_500','icg_1000'];",1)
    toggle_marker='async function toggle(id,on){const cfg=CATALOG.layers.find(x=>x.id===id);if(!cfg)return;'
    if 'ICG_SCALE_LAYERS.includes(id)' not in txt:
        i=txt.find(toggle_marker)
        if i<0:raise RuntimeError('toggle não encontrado')
        j=i+len(toggle_marker);inject='if(on&&ICG_SCALE_LAYERS.includes(id)){for(const other of ICG_SCALE_LAYERS){if(other===id)continue;state.active.delete(other);const ocb=document.querySelector(`input[data-layer="${other}"]`);if(ocb)ocb.checked=false;updateLayerCard(other)}}';txt=txt[:j]+inject+txt[j:]
    txt=re.sub(r'service-worker\.js\?v=[0-9.]+','service-worker.js?v='+TOKEN,txt,count=1)
    p.write_text(txt,encoding='utf-8',newline='\n')

def update_web(repo):
    ip=repo/'docs/index.html'
    if ip.exists():
        s=ip.read_text(encoding='utf-8-sig');s=re.sub(r'\?v=[0-9]+(?:\.[0-9]+)+','?v='+TOKEN,s)
        script=f'<script src="./indices/icg-v38417.js?v={TOKEN}"></script>'
        if 'icg-v38417.js' not in s:
            m=re.search(r'<script[^>]+src=["\']\./indices/ide-v38415\.js\?v=[^"\']+["\'][^>]*></script>',s)
            if m:s=s[:m.end()]+'\n'+script+s[m.end():]
            else:
                b=s.rfind('</body>')
                if b<0:raise RuntimeError('index.html sem </body>')
                s=s[:b]+script+'\n'+s[b:]
        ip.write_text(s,encoding='utf-8',newline='\n')
    bp=repo/'docs/assets/js/bootstrap.js'
    if bp.exists():
        t=bp.read_text(encoding='utf-8-sig');t=re.sub(r'app\.js\?v=[0-9.]+','app.js?v='+TOKEN,t,count=1);t=re.sub(r'campo-sensores\.js\?v=[0-9.]+','campo-sensores.js?v='+TOKEN,t,count=1);bp.write_text(t,encoding='utf-8',newline='\n')
    swp=repo/'docs/service-worker.js'
    if swp.exists():
        sw=swp.read_text(encoding='utf-8-sig');sw,n=re.subn(r"const ITA_CACHE\s*=\s*'[^']+';","const ITA_CACHE = 'ita-arandu-v38-4-17-icg-conhecimento-geocientifico';",sw,count=1)
        if n!=1:raise RuntimeError('ITA_CACHE não localizado')
        sw=re.sub(r'\?v=[0-9]+(?:\.[0-9]+)+','?v='+TOKEN,sw)
        for asset in [f'./indices/icg-v38417.js?v={TOKEN}','./documentos/metodologia-icg.html','./indices/politica-icg-v38416.json']:
            if asset in sw:continue
            end=sw.find('];')
            if end<0:raise RuntimeError('fim de ITA_CORE não localizado')
            sw=sw[:end]+'  "'+asset+'",\n'+sw[end:]
        swp.write_text(sw,encoding='utf-8',newline='\n')
    dp=repo/'docs/documentos/index.html'
    if dp.exists():
        d=dp.read_text(encoding='utf-8-sig')
        if 'metodologia-icg.html' not in d:d=d.replace('</body>','<p><a href="./metodologia-icg.html">ICG · Índice de Conhecimento Geocientífico · metodologia V38.4.17</a></p></body>',1)
        dp.write_text(d,encoding='utf-8',newline='\n')

def update_bibliography(repo):
    jp=repo/'docs/referencias/bibliografia-camadas-indices.json'
    if jp.exists():
        o=load_json(jp)
        for e in o.get('entries',[]):
            if isinstance(e,dict) and e.get('id') in {'icg_250','icg_500','icg_1000'}:
                e['status']='incorporada';e['reference_ids']=['REF-104','REF-105','REF-115']
                if isinstance(e.get('references'),list):e['references']=[r for r in e['references'] if r.get('id') in {'REF-104','REF-105','REF-115'}]
        dump_json(jp,o)
    hp=repo/'docs/referencias/index.html'
    if hp.exists():
        h=hp.read_text(encoding='utf-8-sig')
        for lid in ['icg_250','icg_500','icg_1000']:
            sm=f'id="layer-{lid}"';start=h.find(sm)
            if start<0:continue
            s0=h.rfind('<section',0,start);s1=h.find('</section>',start)
            if s0<0 or s1<0:continue
            s1+=len('</section>');sec=h[s0:s1].replace(' · planejada ·',' · incorporada ·');h=h[:s0]+sec+h[s1:]
        hp.write_text(h,encoding='utf-8',newline='\n')

def write_methodology(repo,snap):
    rows=[]
    for sc in SCALES:
        sm=snap['summary'][sc];sens=snap['sensitivity'][sc]
        rows.append(f"<tr><td>{sc} km²</td><td>{sm['cells']}</td><td>{sm['cells_with_icg']}</td><td>{sm['cells_without_icg']}</td><td>{sm['icg_median']}</td><td>{sm['icg_p95']}</td><td>{sm['icg_max']}</td><td>{sens['alpha_0_5']['rho_vs_baseline']}</td><td>{sens['alpha_2']['rho_vs_baseline']}</td></tr>")
    html="""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ITA ARANDU MS · ICG V38.4.17</title><style>body{font-family:system-ui,Arial,sans-serif;max-width:1120px;margin:auto;padding:28px;line-height:1.58;color:#18212b}h1,h2{color:#303f9f}code{background:#eef0f8;padding:.12rem .3rem;border-radius:4px}table{border-collapse:collapse;width:100%;font-size:.91rem}th,td{border:1px solid #ccd6dd;padding:7px;text-align:right}th:first-child,td:first-child{text-align:left}.warn{background:#fff7e6;padding:12px;border-left:5px solid #b7791f}.ok{background:#e8eaf6;padding:12px;border-left:5px solid #3949ab}</style></head><body>"""
    html+='<h1>ICG · Índice de Conhecimento Geocientífico · V38.4.17</h1><p class="ok"><b>Estado</b> · materializado em 250, 500 e 1000 km² após o gate metodológico V38.4.16.</p>'
    html+='<h2>Função</h2><p>O ICG sintetiza intensidade, amplitude de suporte e equilíbrio do conhecimento geocientífico documentado. Não é índice de favorabilidade mineral e não estima recurso, reserva ou probabilidade de depósito.</p>'
    html+='<h2>Fórmula basal</h2><p><code>S_j = X_j / 100</code></p><p><code>μ_h = média das dimensões observadas</code></p><p><code>σ²_h = Σ(S_j − μ_h)² / n_obs</code></p><p><code>M_h = max(0, μ_h − σ²_h/μ_h)</code></p><p><code>C_h = n_obs / 7</code></p><p><b><code>ICG_h = 100 × C_h × M_h</code></b></p>'
    html+='<h2>Elegibilidade e null</h2><p class="warn">São necessárias pelo menos duas dimensões numéricas observadas. Com n_obs = 1 o ICG permanece null. null nunca é convertido automaticamente em zero. Zero numérico explicitamente observado participa da média e da variância.</p>'
    html+='<p>O teto teórico depende do suporte. Com 2 dimensões o máximo é 28,57. Com 3 é 42,86. Com 4 é 57,14. Com 5 é 71,43. Com 6 é 85,71. Apenas 7 dimensões podem alcançar 100.</p>'
    html+='<h2>IDE</h2><p>IDE permanece indicador companheiro. É publicado na ficha, mas não entra na fórmula do ICG para evitar dupla penalização de diversidade e equilíbrio.</p>'
    html+='<h2>Sensibilidade do fator de suporte</h2><p>O baseline α = 1 foi comparado com α = 0,5 e α = 2 em <code>ICG_h(α) = 100 × (n_obs/7)^α × M_h</code>. A auditoria registra correlação de Spearman, mediana da diferença absoluta e mudança de classe.</p>'
    html+='<table><thead><tr><th>Escala</th><th>Células</th><th>ICG</th><th>null</th><th>Mediana</th><th>P95</th><th>Máx.</th><th>ρ α0,5</th><th>ρ α2</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
    html+='<h2>Leitura cartográfica</h2><p>Valores baixos claros e altos escuros. Células não elegíveis ficam transparentes com borda cinza escuro. A comparação entre células deve considerar também a classe de suporte e as dimensões ausentes.</p>'
    html+='<h2>IGF no corte</h2><p>O estado magnetotelúrico não avaliável no corte é propagado como metadado. Não recebe zero nem imputação.</p>'
    html+='<h2>Referências</h2><p>Mazziotta, M., &amp; Pareto, A. (2013). Methods for constructing composite indices. One for all or all for one? <i>Rivista Italiana di Economia Demografia e Statistica, 67</i>(2), 67–80.</p><p>Saisana, M., Saltelli, A., &amp; Tarantola, S. (2005). Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators. <i>Journal of the Royal Statistical Society. Series A, 168</i>(2), 307–323. https://doi.org/10.1111/j.1467-985X.2005.00350.x</p><p>Busón Buesa, C., &amp; Gabas, S. G. (2026). <i>Protocolo dos índices multiescalares de conhecimento geocientífico de ITA ARANDU MS</i> [Documento de trabalho]. Universidade Federal de Mato Grosso do Sul.</p></body></html>'
    p=repo/'docs/documentos/metodologia-icg.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(html,encoding='utf-8',newline='\n')

def update_changelog(repo):
    ch=repo/'CHANGELOG.md';t=ch.read_text(encoding='utf-8-sig') if ch.exists() else '# Changelog\n'
    if 'V38.4.17 · ICG · Índice de Conhecimento Geocientífico' not in t:
        t=t.rstrip()+"""\n\n## V38.4.17 · ICG · Índice de Conhecimento Geocientífico\n\n- materializa ICG em 250, 500 e 1000 km² conforme gate V38.4.16\n- exige pelo menos duas dimensões observadas e preserva null\n- aplica fator n_obs/7 e penalização não compensatória por variância\n- mantém IDE fora da fórmula e o publica somente como indicador companheiro\n- executa sensibilidade obrigatória com α 0,5 · 1 · 2\n- mantém VCG e PIG bloqueados até regras próprias\n"""
        ch.write_text(t+'\n',encoding='utf-8',newline='\n')

def calculate(repo):
    cur=(repo/'VERSION').read_text(encoding='utf-8-sig').strip()
    if cur!=EXPECTED:raise RuntimeError(f'base esperada {EXPECTED}, encontrada {cur}')
    policy=load_json(repo/POLICY)
    if policy.get('status')!='PASS' or int((policy.get('eligibility') or {}).get('minimum_observed_dimensions',0))!=2:raise RuntimeError('gate V38.4.16 inválido')
    gatefinal=load_json(repo/'AUDITORIA_V38_4_16_GATE_ICG_FINAL.json')
    if gatefinal.get('status')!='PASS':raise RuntimeError('auditoria final do gate ICG não está PASS')
    snaps={d:load_json(repo/rel) for d,rel in SNAPS.items()};ide=load_json(repo/IDE)
    base_hashes={rel:sha256_file(repo/rel) for rel in SNAPS.values()};base_hashes[IDE]=sha256_file(repo/IDE);base_hashes[POLICY]=sha256_file(repo/POLICY)
    grid_hashes={rel:sha256_file(repo/rel) for rel in GRIDS.values()}
    allrows={};sensitivity={};summaries={}
    for sc in SCALES:
        ids=grid_ids(load_json(repo/GRIDS[sc]));rows={};b05=[];b1=[];b2=[]
        for hid in ids:
            vals={d:score_from(snaps[d],d,sc,hid) for d in DIMS}
            r=icg_from_scores(vals,1.0);r05=icg_from_scores(vals,0.5);r2=icg_from_scores(vals,2.0);idev=ide_score(ide,sc,hid)
            n=sum(v is not None for v in vals.values())
            if r is None: row={'icg':None,'m':None,'mu':None,'var':None,'n_obs':n,'support':support_class(n),'ide':idev,'values':vals}
            else: row={'icg':r['icg'],'m':r['m'],'mu':r['mu'],'var':r['var'],'n_obs':r['n_obs'],'support':support_class(r['n_obs']),'ide':idev,'values':vals}
            rows[hid]=row;b1.append(None if r is None else r['icg']);b05.append(None if r05 is None else r05['icg']);b2.append(None if r2 is None else r2['icg'])
        def sens(alt):
            pairs=[(a,b) for a,b in zip(b1,alt) if finite(a) and finite(b)];dif=[abs(a-b) for a,b in pairs];changed=sum(1 for a,b in pairs if class_icg(a)!=class_icg(b))
            return {'rho_vs_baseline':None if len(pairs)<3 else round(spearman([x[0] for x in pairs],[x[1] for x in pairs]),6),'median_abs_diff':None if not dif else round(statistics.median(dif),4),'class_changes':changed,'class_change_fraction':None if not pairs else round(changed/len(pairs),6),'n':len(pairs)}
        sensitivity[sc]={'alpha_0_5':sens(b05),'alpha_1':{'rho_vs_baseline':1.0,'median_abs_diff':0.0,'class_changes':0,'class_change_fraction':0.0,'n':sum(finite(x) for x in b1)},'alpha_2':sens(b2)}
        summaries[sc]=summary(rows);allrows[sc]=rows
        diag=(policy.get('diagnostic_current_cut') or {}).get(sc) or {};exp=int(diag.get('cells_eligible_n_obs_ge_2',-1));act=summaries[sc]['cells_with_icg']
        if exp>=0 and act!=exp:raise RuntimeError(f'{sc} km² · elegibilidade diverge do gate: {act} != {exp}')
    snapshot={'metadata':{'index':'ICG','version':VERSION,'cut_date':CUT_DATE,'generated_at':now_iso(),'formula':FORMULA,'formula_M':MFORM,'standardization':SFORM,'eligibility':'n_obs >= 2','null_rule':'null permanece ausência e não recebe zero','numeric_zero_rule':'zero numérico observado participa do cálculo','ide_rule':'IDE é indicador companheiro e não entra na fórmula','igf_cut_status':'MT NAO_AVALIAVEL_NO_CORTE quando assim documentado pelo gate','references':['REF-104','REF-105','REF-115']},'protected_base_sha256':base_hashes,'protected_grid_sha256':grid_hashes,'summary':summaries,'sensitivity':sensitivity,'grids':{sc:compact_rows(allrows[sc]) for sc in SCALES}}
    dump_json(repo/'docs/indices/icg_v38417_snapshot.json',snapshot)
    js='window.ITA_ICG_V38417='+json.dumps({'metadata':snapshot['metadata'],'summary':snapshot['summary'],'sensitivity':snapshot['sensitivity'],'grids':snapshot['grids']},ensure_ascii=False,separators=(',',':'))+';\n';(repo/'docs/indices/icg-v38417.js').write_text(js,encoding='utf-8',newline='\n')
    patch_catalog_files(repo);patch_app(repo);update_web(repo);update_bibliography(repo);write_methodology(repo,snapshot);update_changelog(repo)
    for rel,h in base_hashes.items():
        if sha256_file(repo/rel)!=h:raise RuntimeError(f'arquivo científico protegido alterado: {rel}')
    for rel,h in grid_hashes.items():
        if sha256_file(repo/rel)!=h:raise RuntimeError(f'malha protegida alterada: {rel}')
    dump_json(repo/'AUDITORIA_V38_4_17_ICG_RUNTIME.json',{'audit':'V38.4.17 · ICG · materialização runtime','version':VERSION,'generated_at':now_iso(),'status':'PASS','summary':summaries,'sensitivity':sensitivity,'protected_base_sha256':base_hashes,'protected_grid_sha256':grid_hashes})
    (repo/'VERSION').write_text(VERSION+'\n',encoding='utf-8',newline='\n')
    print('ICG V38.4.17 materializado')
    for sc in SCALES: print(sc+' km² · '+json.dumps(summaries[sc],ensure_ascii=False))
    print('Sensibilidade alpha 0,5 / 1 / 2 concluída')

def self_test():
    tests=[]
    def ck(name,ok):tests.append((name,bool(ok)))
    r=icg_from_scores({'A':100,'B':100},1);ck('cap_2_dims',abs(r['icg']-200/7)<1e-9)
    r=icg_from_scores({'A':100,'B':100,'C':100,'D':100,'E':100,'F':100,'G':100},1);ck('cap_7_dims',abs(r['icg']-100)<1e-9)
    r=icg_from_scores({'A':100,'B':0},1);ck('imbalance_penalty',r['icg']<100/7)
    ck('one_dimension_null',icg_from_scores({'A':100},1) is None);ck('all_null_null',icg_from_scores({},1) is None)
    r05=icg_from_scores({'A':50,'B':50},0.5);r1=icg_from_scores({'A':50,'B':50},1);r2=icg_from_scores({'A':50,'B':50},2);ck('alpha_order',r05['icg']>r1['icg']>r2['icg'])
    passed=sum(v for _,v in tests);print(f'SELF TEST ICG V38.4.17 · {passed}/{len(tests)}')
    return 0 if passed==len(tests) else 1

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo');ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:return self_test()
    if not a.repo:raise SystemExit('--repo é obrigatório')
    calculate(Path(a.repo).resolve());return 0
if __name__=='__main__':raise SystemExit(main())
