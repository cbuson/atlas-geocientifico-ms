#!/usr/bin/env python3
from pathlib import Path
import argparse, json, math, statistics, datetime, hashlib, re

EXPECTED='V38.4.14.2-GATE-IDE-20260815'
VERSION='V38.4.15-IDE-DIVERSIDADE-EVIDENCIAS-20260815'
TOKEN='38.4.15'
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
GRIDS={
 '250':'docs/camadas/arquivos/malha_r5_250km2.geojson',
 '500':'docs/camadas/arquivos/malha_500km2.geojson',
 '1000':'docs/camadas/arquivos/malha_1000km2.geojson',
}
FORMULA='IDE_h = 100 × exp(H_h) / 7'
HFORM='H_h = -Σ p_j ln(p_j)'
PFORM='p_j = S_j / Σ S_j apenas entre dimensões numéricas observadas na célula'


def now_iso(): return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump_json(p,obj,compact=False):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None)+'\n',encoding='utf-8',newline='\n')
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def finite(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def num(v):
    if finite(v): return float(v)
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except Exception:return None

def grid_ids(fc):
    out=[]
    for f in fc.get('features',[]):
        hid=str((f.get('properties') or {}).get('hex_id') or '')
        if not hid:raise RuntimeError('malha contém feição sem hex_id')
        out.append(hid)
    if len(out)!=len(set(out)):raise RuntimeError('malha contém hex_id duplicado')
    return out

def score_from(snap,dim,scale,hid):
    grids=snap.get('grids',{})
    g=grids.get(scale)
    if not isinstance(g,dict):return None
    if dim=='IMC':
        scores=g.get('scores')
        if isinstance(scores,dict):
            r=scores.get(hid)
            if isinstance(r,dict):return num(r.get('imc_100'))
            if isinstance(r,(list,tuple)) and r:return num(r[0])
        r=g.get(hid)
        if isinstance(r,dict):return num(r.get('imc_100'))
        if isinstance(r,(list,tuple)) and r:return num(r[0])
        return None
    r=g.get(hid)
    if isinstance(r,(list,tuple)) and r:return num(r[0])
    if isinstance(r,dict):
        for k in (dim.lower()+'_100',dim.lower(),'score','value'):
            if k in r:return num(r.get(k))
    return None

def ide_from_scores(vals):
    obs={k:float(v) for k,v in vals.items() if finite(v)}
    if not obs:return None
    for k,v in obs.items():
        if v<0 or v>100:raise RuntimeError(f'{k} fora do intervalo 0–100: {v}')
    positive={k:v for k,v in obs.items() if v>0}
    total=sum(positive.values())
    if total<=0:return None
    ps=[v/total for v in positive.values()]
    H=-sum(p*math.log(p) for p in ps if p>0)
    neff=math.exp(H)
    ide=100*neff/7.0
    return {'ide':ide,'H':H,'neff':neff,'n_obs':len(obs),'n_pos':len(positive),'sum_scores':total,'observed':list(obs),'positive':list(positive)}

def class_ide(v):
    if v is None:return 'sem dados calculáveis'
    if v<20:return 'muito baixo'
    if v<40:return 'baixo'
    if v<60:return 'médio'
    if v<75:return 'alto'
    return 'muito alto'
def support_class(n):
    if n<=2:return 'suporte muito limitado'
    if n<=4:return 'suporte parcial'
    if n<=6:return 'suporte amplo'
    return 'suporte completo'
def mask_for(obs):
    m=0
    for i,d in enumerate(DIMS):
        if d in obs:m|=(1<<i)
    return m

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
def spearman_pairs(a,b):
    pairs=[(x,y) for x,y in zip(a,b) if finite(x) and finite(y)]
    if len(pairs)<3:return None
    x=[p[0] for p in pairs];y=[p[1] for p in pairs];rx=rankdata(x);ry=rankdata(y);mx=statistics.fmean(rx);my=statistics.fmean(ry)
    nume=sum((u-mx)*(v-my) for u,v in zip(rx,ry));den=(sum((u-mx)**2 for u in rx)*sum((v-my)**2 for v in ry))**0.5
    return None if den==0 else nume/den

def transformed_ide(vals,mode):
    vv={}
    for k,v in vals.items():
        if not finite(v):continue
        x=float(v)
        if mode=='sqrt':x=100*math.sqrt(max(0,x)/100.0)
        elif mode=='log1p':x=100*math.log1p(max(0,x))/math.log(101)
        vv[k]=x
    r=ide_from_scores(vv)
    return None if not r else r['ide']

def summary(rows):
    vals=[r['ide'] for r in rows.values() if r['ide'] is not None]
    byn={str(k):sum(1 for r in rows.values() if r['n_obs']==k) for k in range(1,8)}
    bysup={x:sum(1 for r in rows.values() if r['support']==x) for x in ['suporte muito limitado','suporte parcial','suporte amplo','suporte completo']}
    return {
      'cells':len(rows),'cells_with_ide':len(vals),'cells_without_ide':len(rows)-len(vals),
      'ide_min':None if not vals else round(min(vals),4),'ide_p05':None if not vals else round(percentile(vals,5),4),
      'ide_median':None if not vals else round(statistics.median(vals),4),'ide_mean':None if not vals else round(statistics.fmean(vals),4),
      'ide_p95':None if not vals else round(percentile(vals,95),4),'ide_max':None if not vals else round(max(vals),4),
      'dimension_count_distribution':byn,'support_classes':bysup
    }

def compact_rows(rows):
    # [IDE,Neff,H,nObs,nPos,fracObs,mask,sum,IMC,IOD,ICP,IGC,IGQ,IGF,ICS]
    out={}
    for hid,r in rows.items():
        vals=r['values']
        out[hid]=[
          None if r['ide'] is None else round(r['ide'],4),
          None if r['neff'] is None else round(r['neff'],6),
          None if r['H'] is None else round(r['H'],8),
          r['n_obs'],r['n_pos'],round(r['n_obs']/7,6),r['mask'],round(r['sum_scores'],6),
          *[None if vals[d] is None else round(vals[d],4) for d in DIMS]
        ]
    return out

def patch_catalog_obj(cat):
    layers=cat.get('layers',[]) if isinstance(cat,dict) else cat
    cfgs={
      'ide_250':('250','malha_r5_250km2',1554),
      'ide_500':('500','malha_500km2',793),
      'ide_1000':('1000','malha_1000km2',412),
    }
    for item in layers:
        iid=item.get('id') if isinstance(item,dict) else None
        if iid in cfgs:
            scale,grid,count=cfgs[iid]
            item.update({
              'status':'incorporada','count':count,
              'source':'ITA ARANDU MS · IDE V38.4.15 · sete dimensões base certificadas',
              'validation':'V38.4.15 · cálculo de diversidade efetiva segundo gate V38.4.14.2 · null preservado',
              'note':'Diversidade efetiva das famílias IMC, IOD, ICP, IGC, IGQ, IGF e ICS. Dimensões ausentes permanecem null e não recebem zero. O denominador 7 permanece fixo. Cada célula publica número de dimensões observadas e ausentes.',
              'derive_type':'ide_snapshot_v38415','grid_source_id':grid,'ide_scale':scale,
              'reference_ids':['REF-111','REF-112','REF-113','REF-115','REF-105']
            })
    return cat

def patch_catalog_files(repo):
    jp=repo/'docs/camadas/catalogo-local.json'
    if jp.exists():
        obj=load_json(jp);obj=patch_catalog_obj(obj);dump_json(jp,obj)
    js=repo/'docs/camadas/catalogo-local.js'
    if js.exists():
        t=js.read_text(encoding='utf-8-sig')
        # O arquivo normalmente contém somente o mapa de arquivos locais. IDE é derivado e não precisa de arquivo GeoJSON próprio.
        js.write_text(t,encoding='utf-8',newline='\n')

def patch_app(repo):
    p=repo/'docs/assets/js/app.js';txt=p.read_text(encoding='utf-8-sig')
    prefix='const CATALOG=';pos=txt.find(prefix)
    if pos<0:raise RuntimeError('CATALOG não localizado em app.js')
    pos+=len(prefix);cat,end=json.JSONDecoder().raw_decode(txt[pos:]);cat=patch_catalog_obj(cat);txt=txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:]
    color_marker="function icsColor(v){const c=icsClass(v);return ITA_ICS_COLORS[c]||'rgba(0,0,0,0)'}"
    if 'const ITA_IDE_COLORS=' not in txt:
        add="\nconst ITA_IDE_COLORS={'muito baixo':'#e0f2f1','baixo':'#b2dfdb','médio':'#80cbc4','alto':'#26a69a','muito alto':'#00695c'};\nfunction ideClass(v){const x=Number(v);if(v===null||v===undefined||!Number.isFinite(x))return'sem dados calculáveis';if(x<20)return'muito baixo';if(x<40)return'baixo';if(x<60)return'médio';if(x<75)return'alto';return'muito alto'}\nfunction ideColor(v){const c=ideClass(v);return ITA_IDE_COLORS[c]||'rgba(0,0,0,0)'}"
        if color_marker not in txt:raise RuntimeError('marcador icsColor não encontrado em app.js')
        txt=txt.replace(color_marker,color_marker+add,1)
    fs0=txt.find('function featureStyle(cfg,feat){');fs1=txt.find('function pathGeometry',fs0)
    if fs0<0 or fs1<0:raise RuntimeError('featureStyle não localizado')
    fseg=txt[fs0:fs1]
    if "st.renderer==='index_ide'" not in fseg:
        marker="if(st.renderer==='index_ics'){fill=icsColor(p.ics_100);stroke='#4a4a4a';}"
        if marker not in fseg:raise RuntimeError('renderer ICS não encontrado em featureStyle')
        fseg=fseg.replace(marker,marker+" if(st.renderer==='index_ide'){fill=ideColor(p.ide_100);stroke='#4a4a4a';}",1)
        txt=txt[:fs0]+fseg+txt[fs1:]
    # A legenda deve ficar somente em layerLegendHtml, nunca dentro de featureStyle.
    lg0=txt.find('function layerLegendHtml(cfg){');lg1=txt.find('function updateLegend',lg0)
    if lg0<0:raise RuntimeError('layerLegendHtml não localizado')
    if lg1<0:lg1=txt.find('function ',lg0+30)
    lseg=txt[lg0:lg1 if lg1>lg0 else len(txt)]
    if "if(st.renderer==='index_ide')return" not in lseg:
        marker="if(st.renderer==='index_ics')return"
        i=lseg.find(marker)
        if i<0:raise RuntimeError('legenda ICS não encontrada em layerLegendHtml. Aplique primeiro V38.4.14.1.')
        e=lseg.find('\n',i)
        if e<0:e=len(lseg)
        legend=" if(st.renderer==='index_ide')return `<div class=\"legend-layer-title\">${esc(cfg.name)}</div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#e0f2f1;border:1px solid #4a4a4a\"></span><span>0–&lt;20 · muito baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#b2dfdb;border:1px solid #4a4a4a\"></span><span>20–&lt;40 · baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#80cbc4;border:1px solid #4a4a4a\"></span><span>40–&lt;60 · médio</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#26a69a;border:1px solid #4a4a4a\"></span><span>60–&lt;75 · alto</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#00695c;border:1px solid #4a4a4a\"></span><span>75–100 · muito alto</span></div><div class=\"legend-note\">IDE = 100 × exp(H) / 7. H usa apenas dimensões numéricas observadas. null não vira zero. O denominador 7 permanece fixo. Uma única família positiva produz IDE ≈ 14,29; o máximo 100 requer sete famílias positivas com contribuição equilibrada.</div>`;"
        lseg=lseg[:e+1]+legend+'\n'+lseg[e+1:]
        txt=txt[:lg0]+lseg+txt[lg1 if lg1>lg0 else len(txt):]
    if 'async function buildIdeSnapshotV38415' not in txt:
        marker='async function buildImcPreview(cfg)';i=txt.find(marker)
        if i<0:raise RuntimeError('ponto de inserção do builder IDE não encontrado')
        builder="""async function buildIdeSnapshotV38415(cfg){
 const gridCfg=CATALOG.layers.find(x=>x.id===cfg.grid_source_id);
 if(!gridCfg)throw new Error('Malha do IDE V38.4.15 não encontrada no catálogo');
 const grid=await ensure(gridCfg),key=String(cfg.ide_scale||''),scores=window.ITA_IDE_V38415?.grids?.[key],meta=window.ITA_IDE_V38415?.metadata||{};
 if(!scores)throw new Error('Snapshot IDE V38.4.15 não encontrado para esta escala. Execute o materializador do patch.');
 const dims=['IMC','IOD','ICP','IGC','IGQ','IGF','ICS'];
 const features=(grid.features||[]).map(hf=>{const hid=String(hf.properties?.hex_id||''),r=scores[hid];if(!r)return {...hf,properties:{...(hf.properties||{}),ide_100:null,classe_ide:'sem dados calculáveis'}};const [ide,neff,H,nObs,nPos,frac,mask,sum,imc,iod,icp,igc,igq,igf,ics]=r;const vals=[imc,iod,icp,igc,igq,igf,ics];const obs=dims.filter((d,j)=>(mask&(1<<j))!==0),aus=dims.filter((d,j)=>(mask&(1<<j))===0);const support=nObs<=2?'suporte muito limitado':nObs<=4?'suporte parcial':nObs<=6?'suporte amplo':'suporte completo';return {...hf,properties:{...(hf.properties||{}),ide_100:ide,classe_ide:ideClass(ide),diversidade_efetiva:neff,entropia_shannon:H,n_dim_observadas:nObs,n_dim_positivas:nPos,fracao_dim_observadas:frac,dimensoes_observadas:obs.join(' · '),dimensoes_ausentes:aus.join(' · '),classe_suporte_ide:support,soma_escores_observados:sum,imc_100_base:imc,iod_100_base:iod,icp_100_base:icp,igc_100_base:igc,igq_100_base:igq,igf_100_base:igf,ics_100_base:ics,status_igf_no_corte:meta.igf_cut_status||'PARCIAL_DOCUMENTADO · MT NAO_AVALIAVEL_NO_CORTE',formula:'IDE_h = 100 × exp(H_h) / 7',formula_H:'H_h = -Σ p_j ln(p_j)',formula_p:'p_j = S_j / Σ S_j entre dimensões numéricas observadas',regra_null:'null permanece ausente e não recebe zero. Zero numérico observado permanece zero.',regra_denominador:'7 permanece fixo. A ausência de famílias reduz o teto efetivo sem imputação.',metodo:'V38.4.15 · síntese por célula das sete dimensões base na mesma escala',data_corte:meta.cut_date||'2026-08-15'}};});
 return {type:'FeatureCollection',features,atlas_metadata:{indice:'IDE',versao:'V38.4.15',escala:key,formula:'IDE_h = 100 × exp(H_h) / 7',regra_null:'null não é zero',regra_suporte:'cada célula publica n de dimensões observadas',limite:'IDE mede diversidade efetiva de famílias de evidência, não volume total de conhecimento, favorabilidade mineral ou valor econômico'}};
}
"""
        txt=txt[:i]+builder+txt[i:]
    chain="if(!d&&cfg.derive_type==='ics_snapshot_v38413')d=await buildIcsSnapshotV38413(cfg);"
    if "derive_type==='ide_snapshot_v38415'" not in txt:
        if chain not in txt:raise RuntimeError('cadeia derive ICS não encontrada')
        txt=txt.replace(chain,chain+"if(!d&&cfg.derive_type==='ide_snapshot_v38415')d=await buildIdeSnapshotV38415(cfg);",1)
    scale_marker="const ICS_SCALE_LAYERS=['ics_250','ics_500','ics_1000'];"
    if 'const IDE_SCALE_LAYERS=' not in txt:
        if scale_marker not in txt:raise RuntimeError('grupo de escalas ICS não encontrado')
        txt=txt.replace(scale_marker,scale_marker+" const IDE_SCALE_LAYERS=['ide_250','ide_500','ide_1000'];",1)
    toggle_marker='async function toggle(id,on){const cfg=CATALOG.layers.find(x=>x.id===id);if(!cfg)return;'
    if 'IDE_SCALE_LAYERS.includes(id)' not in txt:
        i=txt.find(toggle_marker)
        if i<0:raise RuntimeError('toggle não encontrado')
        j=i+len(toggle_marker)
        inject='if(on&&IDE_SCALE_LAYERS.includes(id)){for(const other of IDE_SCALE_LAYERS){if(other===id)continue;state.active.delete(other);const ocb=document.querySelector(`input[data-layer="${other}"]`);if(ocb)ocb.checked=false;updateLayerCard(other)}}'
        txt=txt[:j]+inject+txt[j:]
    # Cache bust do registro do service worker dentro de app.js
    txt=re.sub(r'service-worker\.js\?v=[0-9.]+','service-worker.js?v='+TOKEN,txt,count=1)
    p.write_text(txt,encoding='utf-8',newline='\n')

def update_web(repo):
    ip=repo/'docs/index.html'
    if ip.exists():
        s=ip.read_text(encoding='utf-8-sig')
        s=re.sub(r'\?v=[0-9]+(?:\.[0-9]+)+','?v='+TOKEN,s)
        script=f'<script src="./indices/ide-v38415.js?v={TOKEN}"></script>'
        if 'ide-v38415.js' not in s:
            marker=re.search(r'<script[^>]+src=["\']\./indices/ics-v38413\.js\?v=[^"\']+["\'][^>]*></script>',s)
            if marker:s=s[:marker.end()]+'\n'+script+s[marker.end():]
            else:
                b=s.rfind('</body>')
                if b<0:raise RuntimeError('index.html sem </body> para inserir IDE')
                s=s[:b]+script+'\n'+s[b:]
        ip.write_text(s,encoding='utf-8',newline='\n')
    bp=repo/'docs/assets/js/bootstrap.js'
    if bp.exists():
        t=bp.read_text(encoding='utf-8-sig');t=re.sub(r'app\.js\?v=[0-9.]+','app.js?v='+TOKEN,t,count=1);t=re.sub(r'campo-sensores\.js\?v=[0-9.]+','campo-sensores.js?v='+TOKEN,t,count=1);bp.write_text(t,encoding='utf-8',newline='\n')
    swp=repo/'docs/service-worker.js'
    if swp.exists():
        sw=swp.read_text(encoding='utf-8-sig');sw,n=re.subn(r"const ITA_CACHE\s*=\s*'[^']+';","const ITA_CACHE = 'ita-arandu-v38-4-15-ide-diversidade-evidencias';",sw,count=1)
        if n!=1:raise RuntimeError('ITA_CACHE não localizado em service-worker.js')
        sw=re.sub(r'\?v=[0-9]+(?:\.[0-9]+)+','?v='+TOKEN,sw)
        assets=[f'./indices/ide-v38415.js?v={TOKEN}','./documentos/metodologia-ide.html','./indices/politica-sintese-v384142.json']
        for asset in assets:
            if asset in sw:continue
            end=sw.find('];')
            if end<0:raise RuntimeError('fim de ITA_CORE não localizado em service-worker.js')
            sw=sw[:end]+'  "'+asset+'",\n'+sw[end:]
        swp.write_text(sw,encoding='utf-8',newline='\n')
    dp=repo/'docs/documentos/index.html'
    if dp.exists():
        d=dp.read_text(encoding='utf-8-sig')
        if 'metodologia-ide.html' not in d:d=d.replace('</body>','<p><a href="./metodologia-ide.html">IDE · Diversidade de Evidências · metodologia V38.4.15</a></p></body>',1)
        dp.write_text(d,encoding='utf-8',newline='\n')

def update_bibliography(repo):
    jp=repo/'docs/referencias/bibliografia-camadas-indices.json'
    if jp.exists():
        o=load_json(jp)
        for e in o.get('entries',[]):
            if isinstance(e,dict) and e.get('id') in {'ide_250','ide_500','ide_1000'}:e['status']='incorporada'
        dump_json(jp,o)
    hp=repo/'docs/referencias/index.html'
    if hp.exists():
        h=hp.read_text(encoding='utf-8-sig')
        for lid in ['ide_250','ide_500','ide_1000']:
            sm=f'id="layer-{lid}"';start=h.find(sm)
            if start<0:continue
            s0=h.rfind('<section',0,start);s1=h.find('</section>',start)
            if s0<0 or s1<0:continue
            s1+=len('</section>');sec=h[s0:s1].replace(' · planejada ·',' · incorporada ·');h=h[:s0]+sec+h[s1:]
        hp.write_text(h,encoding='utf-8',newline='\n')

def write_methodology(repo,audit,snap):
    rows=[]
    for sc in SCALES:
        sm=snap['summary'][sc];dist=sm['dimension_count_distribution']
        rows.append('<tr><td>'+sc+' km²</td><td>'+str(sm['cells'])+'</td><td>'+str(sm['cells_with_ide'])+'</td><td>'+str(dist.get('1',0))+'</td><td>'+str(dist.get('2',0))+'</td><td>'+str(dist.get('3',0))+'</td><td>'+str(dist.get('4',0))+'</td><td>'+str(dist.get('5',0))+'</td><td>'+str(dist.get('6',0))+'</td><td>'+str(dist.get('7',0))+'</td></tr>')
    html='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ITA ARANDU MS · IDE V38.4.15</title><style>body{font-family:system-ui,Arial,sans-serif;max-width:1120px;margin:auto;padding:28px;line-height:1.58;color:#18212b}h1,h2{color:#0b4f76}code{background:#eef3f6;padding:.12rem .3rem;border-radius:4px}table{border-collapse:collapse;width:100%;font-size:.91rem}th,td{border:1px solid #ccd6dd;padding:7px;text-align:right}th:first-child,td:first-child{text-align:left}.warn{background:#fff7e6;padding:12px;border-left:5px solid #b7791f}.ok{background:#e9f7ef;padding:12px;border-left:5px solid #238636}</style></head><body>'''
    html+='<h1>IDE · Diversidade de Evidências · V38.4.15</h1><p class="ok"><b>Estado</b> · índice materializado nas três escalas após o gate científico V38.4.14.2.</p>'
    html+='<h2>Objetivo</h2><p>O IDE mede a diversidade efetiva das sete famílias de evidência geocientífica do Atlas. Não mede quantidade total de dados, favorabilidade mineral, recurso, reserva ou valor econômico.</p>'
    html+='<h2>Fórmula</h2><p><code>IDE_h = 100 × exp(H_h) / 7</code></p><p><code>H_h = −Σ p_j ln(p_j)</code></p><p><code>p_j = S_j / Σ S_j</code> apenas entre dimensões numéricas observadas na célula.</p>'
    html+='<p>As sete famílias são IMC, IOD, ICP, IGC, IGQ, IGF e ICS. A formulação usa o número efetivo de categorias associado à entropia de Shannon. O denominador sete permanece fixo. Assim, poucas famílias não podem produzir diversidade máxima.</p>'
    html+='<h2>Tratamento de ausência</h2><p class="warn"><b>null não é zero.</b> Uma dimensão sem evidência materializada permanece ausente da normalização. Um zero numérico efetivamente observado permanece zero, conta como dimensão observada, mas não contribui ao termo de Shannon. O IDE é calculável quando existe pelo menos uma dimensão numérica e a soma dos escores positivos é maior que zero.</p>'
    html+='<p>Como o IMC possui suporte numérico em toda a malha no corte atual, todas as células podem receber IDE. Uma única família positiva produz aproximadamente 14,29 pontos. Isso representa diversidade de uma única família, não conhecimento completo.</p>'
    html+='<h2>Suporte documental</h2><p>Cada célula publica o número de dimensões observadas, as famílias presentes e ausentes, a fração de dimensões observadas e a situação do IGF no corte. Classes de suporte. 1–2 muito limitado. 3–4 parcial. 5–6 amplo. 7 completo.</p>'
    html+='<table><thead><tr><th>Escala</th><th>Células</th><th>IDE calculável</th><th>1 dim</th><th>2 dim</th><th>3 dim</th><th>4 dim</th><th>5 dim</th><th>6 dim</th><th>7 dim</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
    html+='<h2>IGF no corte</h2><p>O módulo magnetotelúrico permanece <b>NAO_AVALIAVEL_NO_CORTE</b> por indisponibilidade remota documentada. Não recebeu zero nem valor imputado. O IDE utiliza o valor IGF materializado com a proveniência parcial explicitamente preservada.</p>'
    html+='<h2>Leitura correta</h2><p>IDE alto significa que várias famílias de evidência estão simultaneamente representadas e com contribuições relativamente equilibradas. IDE baixo pode resultar de poucas famílias disponíveis ou de forte concentração do conhecimento em uma família. Por isso, o mapa deve ser lido junto com <code>n_dim_observadas</code> e <code>dimensoes_ausentes</code>.</p>'
    html+='<h2>Referências</h2><p>Hill, M. O. (1973). Diversity and evenness. A unifying notation and its consequences. <i>Ecology, 54</i>(2), 427–432. https://doi.org/10.2307/1934352</p><p>Jost, L. (2006). Entropy and diversity. <i>Oikos, 113</i>(2), 363–375. https://doi.org/10.1111/j.2006.0030-1299.14714.x</p><p>Shannon, C. E. (1948). A mathematical theory of communication. <i>Bell System Technical Journal, 27</i>(3), 379–423. https://doi.org/10.1002/j.1538-7305.1948.tb01338.x</p><p>Saisana, M., Saltelli, A., &amp; Tarantola, S. (2005). Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators. <i>Journal of the Royal Statistical Society. Series A, 168</i>(2), 307–323. https://doi.org/10.1111/j.1467-985X.2005.00350.x</p><p>Busón Buesa, C., &amp; Gabas, S. G. (2026). <i>Protocolo dos índices multiescalares de conhecimento geocientífico de ITA ARANDU MS</i> [Documento de trabalho]. Universidade Federal de Mato Grosso do Sul.</p>'
    html+='</body></html>'
    p=repo/'docs/documentos/metodologia-ide.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(html,encoding='utf-8',newline='\n')

def update_changelog(repo):
    ch=repo/'CHANGELOG.md'
    if ch.exists():
        t=ch.read_text(encoding='utf-8-sig')
        if 'V38.4.15 · IDE · Diversidade de Evidências' not in t:
            t+='\n\n## V38.4.15 · IDE · Diversidade de Evidências\n\n- materializa IDE em 250, 500 e 1000 km²\n- preserva null nas sete dimensões base e não imputa zero\n- mantém denominador sete fixo e publica o suporte efetivamente observado por célula\n- registra MT como não avaliável no corte conforme gate V38.4.14.2\n- mantém ICG, VCG e PIG bloqueados até regras próprias\n'
            ch.write_text(t,encoding='utf-8',newline='\n')

def calculate(repo):
    version=(repo/'VERSION').read_text(encoding='utf-8-sig').strip()
    if version!=EXPECTED:raise RuntimeError(f'base esperada {EXPECTED}, encontrada {version}')
    policy=load_json(repo/'docs/indices/politica-sintese-v384142.json')
    if policy.get('decision',{}).get('IDE')!='PASS_PARA_MATERIALIZACAO':raise RuntimeError('gate V38.4.14.2 não libera IDE')
    audit=load_json(repo/'AUDITORIA_V38_4_14_SETE_DIMENSOES.json')
    if audit.get('status')!='PASS':raise RuntimeError('auditoria conjunta V38.4.14 não está PASS')
    snaps={d:load_json(repo/rel) for d,rel in SNAPS.items()}
    base_hashes={rel:sha256_file(repo/rel) for rel in SNAPS.values()}
    grid_hashes={rel:sha256_file(repo/rel) for rel in GRIDS.values()}
    rows={};support_match={};per_dim_counts={}
    sensitivity={}
    for sc in SCALES:
        ids=grid_ids(load_json(repo/GRIDS[sc]));rows[sc]={};counts={d:0 for d in DIMS}
        base_vals=[];sqrt_vals=[];log_vals=[];ceiling=[]
        loo={d:{'a':[],'b':[],'diff':[]} for d in DIMS}
        for hid in ids:
            vals={d:score_from(snaps[d],d,sc,hid) for d in DIMS}
            for d,v in vals.items():
                if v is not None:
                    if v<0 or v>100:raise RuntimeError(f'{d} {sc} {hid} fora de 0–100: {v}')
                    counts[d]+=1
            res=ide_from_scores(vals)
            if res is None:
                r={'ide':None,'H':None,'neff':None,'n_obs':sum(v is not None for v in vals.values()),'n_pos':sum((v or 0)>0 for v in vals.values() if v is not None),'sum_scores':sum(v for v in vals.values() if v and v>0),'values':vals,'mask':mask_for([d for d,v in vals.items() if v is not None]),'support':support_class(sum(v is not None for v in vals.values()))}
            else:
                r={**res,'values':vals,'mask':mask_for(res['observed']),'support':support_class(res['n_obs'])}
                base_vals.append(res['ide']);sqrt_vals.append(transformed_ide(vals,'sqrt'));log_vals.append(transformed_ide(vals,'log1p'));ceiling.append(100*res['n_obs']/7)
                for d in DIMS:
                    if vals[d] is None:continue
                    vv=dict(vals);vv[d]=None;alt=ide_from_scores(vv)
                    if alt is not None:
                        loo[d]['a'].append(res['ide']);loo[d]['b'].append(alt['ide']);loo[d]['diff'].append(abs(res['ide']-alt['ide']))
            rows[sc][hid]=r
        per_dim_counts[sc]=counts
        expected_counts={d:int(audit['distributions'][sc][d]['n']) for d in DIMS}
        if counts!=expected_counts:raise RuntimeError(f'contagem de suporte por dimensão diverge da auditoria V38.4.14 em {sc} km² · {counts} != {expected_counts}')
        actual_dist={str(k):sum(1 for r in rows[sc].values() if r['n_obs']==k) for k in range(0,8)}
        expdist={str(k):int(v) for k,v in audit['complete_support'][sc]['dimension_count_distribution'].items()}
        # auditoria omite zero se não ocorrer
        for k in range(0,8):
            if actual_dist.get(str(k),0)!=expdist.get(str(k),0):raise RuntimeError(f'distribuição de número de dimensões diverge em {sc} km² · k={k} · {actual_dist.get(str(k),0)} != {expdist.get(str(k),0)}')
        support_match[sc]=True
        sensitivity[sc]={
          'sqrt_scores_rho':spearman_pairs(base_vals,sqrt_vals),
          'log1p_scores_rho':spearman_pairs(base_vals,log_vals),
          'support_ceiling_rho':spearman_pairs(base_vals,ceiling),
          'leave_one_dimension_out':{d:{'n':len(loo[d]['a']),'rho':spearman_pairs(loo[d]['a'],loo[d]['b']),'median_abs_diff':None if not loo[d]['diff'] else round(statistics.median(loo[d]['diff']),4)} for d in DIMS}
        }
    snap={
      'metadata':{
        'index':'IDE','version':VERSION,'calculated_at':now_iso(),'cut_date':CUT_DATE,
        'formula':FORMULA,'entropy_formula':HFORM,'proportion_formula':PFORM,'dimensions':DIMS,
        'definition':'diversidade efetiva de famílias de evidência geocientífica, escalada pelo total fixo de sete famílias',
        'null_rule':'null permanece ausente e não é convertido em zero. Zero numérico observado permanece zero e conta como dimensão observada, mas não contribui ao somatório de Shannon.',
        'denominator_rule':'o denominador 7 permanece fixo. O máximo 100 exige sete famílias positivas com contribuições equilibradas.',
        'eligibility':'ao menos uma dimensão numérica e soma dos escores positivos maior que zero',
        'support_rule':'cada célula publica n_dim_observadas, máscara de famílias presentes e fração observada. 1–2 muito limitado, 3–4 parcial, 5–6 amplo, 7 completo.',
        'igf_cut_status':'PARCIAL_DOCUMENTADO · MT NAO_AVALIAVEL_NO_CORTE · sem zero e sem imputação',
        'source':'IMC, IOD, ICP, IGC, IGQ, IGF e ICS certificados no corte V38.4.14.2',
        'source_audit':'AUDITORIA_V38_4_14_SETE_DIMENSOES.json','gate_policy':'docs/indices/politica-sintese-v384142.json',
        'references':['REF-111','REF-112','REF-113','REF-115','REF-105'],
        'interpretation_limit':'IDE mede diversidade efetiva das famílias de evidência. Não mede volume total de conhecimento, favorabilidade mineral, recurso, reserva, risco ou valor econômico.',
        'row_schema':['IDE','diversidade_efetiva','H','n_dim_observadas','n_dim_positivas','fracao_dim_observadas','mascara_dimensoes','soma_escores_positivos','IMC','IOD','ICP','IGC','IGQ','IGF','ICS']
      },
      'protected_base_sha256':base_hashes,'protected_grid_sha256':grid_hashes,
      'summary':{sc:summary(rows[sc]) for sc in SCALES},'support_matches_audit_v38414':support_match,'sensitivity':sensitivity,
      'grids':{sc:compact_rows(rows[sc]) for sc in SCALES}
    }
    return snap,base_hashes,grid_hashes,per_dim_counts

def self_test():
    r=ide_from_scores({'IMC':50,'IOD':None,'ICP':None,'IGC':None,'IGQ':None,'IGF':None,'ICS':None});assert abs(r['ide']-100/7)<1e-9 and r['n_obs']==1
    r=ide_from_scores({d:50 for d in DIMS});assert abs(r['ide']-100)<1e-9
    r=ide_from_scores({'IMC':50,'IOD':0});assert r['n_obs']==2 and r['n_pos']==1 and abs(r['ide']-100/7)<1e-9
    r=ide_from_scores({'IMC':50,'IOD':50});assert abs(r['ide']-200/7)<1e-9
    print('SELFTEST IDE V38.4.15 · PASS')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');ap.add_argument('--self-test',action='store_true');args=ap.parse_args()
    if args.self_test:self_test();return 0
    repo=Path(args.repo).resolve();snap,base_hashes,grid_hashes,counts=calculate(repo)
    dump_json(repo/'docs/indices/ide_v38415_snapshot.json',snap)
    (repo/'docs/indices/ide-v38415.js').write_text('window.ITA_IDE_V38415='+json.dumps(snap,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
    patch_app(repo);patch_catalog_files(repo);update_web(repo);update_bibliography(repo);write_methodology(repo,load_json(repo/'AUDITORIA_V38_4_14_SETE_DIMENSOES.json'),snap);update_changelog(repo)
    (repo/'VERSION').write_text(VERSION+'\n',encoding='utf-8',newline='\n')
    runtime={'audit':'V38.4.15 IDE runtime','status':'PASS','generated_at':now_iso(),'formula':FORMULA,'support_matches_audit_v38414':snap['support_matches_audit_v38414'],'per_dimension_numeric_counts':counts,'summary':snap['summary'],'sensitivity':snap['sensitivity'],'protected_base_sha256':base_hashes,'protected_grid_sha256':grid_hashes,'guards':{'null_not_zero':True,'denominator_fixed_7':True,'base_indices_not_recomputed':True,'same_scale_only':True,'igf_mt_not_imputed':True,'ICG_not_calculated':True,'VCG_not_calculated':True,'PIG_not_calculated':True}}
    dump_json(repo/'AUDITORIA_V38_4_15_IDE_RUNTIME.json',runtime)
    print('ITA ARANDU MS · IDE V38.4.15 MATERIALIZADO')
    print('Fórmula · '+FORMULA)
    for sc in SCALES:print(sc+' km² · '+json.dumps(snap['summary'][sc],ensure_ascii=False))
    print('null permanece null · denominador 7 fixo · MT não imputado')
    return 0
if __name__=='__main__':raise SystemExit(main())
