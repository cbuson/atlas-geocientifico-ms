#!/usr/bin/env python3
from pathlib import Path
import argparse,json,math,statistics,datetime,hashlib,re
EXPECTED='V38.4.18-GATE-VCG-20260815'
VERSION='V38.4.19-VCG-VAZIOS-CONHECIMENTO-GEOCIENTIFICO-20260815'
TOKEN='38.4.19'
CUT_DATE='2026-08-15'
DIMS=['IMC','IOD','ICP','IGC','IGQ','IGF','ICS']
SCALES=['250','500','1000']
SNAPS={
 'IMC':'docs/indices/imc_v32_snapshot.json','IOD':'docs/indices/iod_v3848_snapshot.json','ICP':'docs/indices/icp_v3849_snapshot.json',
 'IGC':'docs/indices/igc_v38410_snapshot.json','IGQ':'docs/indices/igq_v38411_snapshot.json','IGF':'docs/indices/igf_v38412_snapshot.json','ICS':'docs/indices/ics_v38413_snapshot.json'}
IDE='docs/indices/ide_v38415_snapshot.json'; ICG='docs/indices/icg_v38417_snapshot.json'; POLICY='docs/indices/politica-vcg-v38418.json'
GRIDS={'250':'docs/camadas/arquivos/malha_r5_250km2.geojson','500':'docs/camadas/arquivos/malha_500km2.geojson','1000':'docs/camadas/arquivos/malha_1000km2.geojson'}

def now_iso(): return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump_json(p,obj,compact=False):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None)+'\n',encoding='utf-8',newline='\n')
def sha256_file(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def finite(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def num(v):
 if finite(v): return float(v)
 try:
  x=float(v);return x if math.isfinite(x) else None
 except Exception:return None

def grid_ids(fc):
 ids=[]
 for f in fc.get('features',[]):
  hid=str((f.get('properties') or {}).get('hex_id') or '')
  if not hid:raise RuntimeError('malha contem feicao sem hex_id')
  ids.append(hid)
 if len(ids)!=len(set(ids)):raise RuntimeError('malha contem hex_id duplicado')
 return ids

def score_from(snap,dim,scale,hid):
 g=(snap.get('grids') or {}).get(scale)
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

def companion_score(snap,scale,hid,key):
 r=(snap.get('grids',{}).get(scale) or {}).get(hid)
 if isinstance(r,(list,tuple)) and r:return num(r[0])
 if isinstance(r,dict):return num(r.get(key) if key in r else r.get('score'))
 return None

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
 if len(a)!=len(b) or len(a)<3:return None
 rx=rankdata(a);ry=rankdata(b);mx=statistics.fmean(rx);my=statistics.fmean(ry)
 den=(sum((u-mx)**2 for u in rx)*sum((v-my)**2 for v in ry))**0.5
 return None if den==0 else sum((u-mx)*(v-my) for u,v in zip(rx,ry))/den

def class_vcg(v):
 if v is None:return 'sem cálculo'
 if v<20:return 'muito baixo'
 if v<40:return 'baixo'
 if v<60:return 'médio'
 if v<75:return 'alto'
 return 'muito alto'
def confidence(n):
 if n<=1:return 'muito limitada'
 if n==2:return 'limitada'
 if n<=4:return 'moderada'
 if n<=6:return 'boa'
 return 'alta'
def vcg_from_scores(vals,lambda_doc=1.0):
 obs={d:float(v) for d,v in vals.items() if finite(v)}
 for d,v in obs.items():
  if v<0 or v>100:raise RuntimeError(f'{d} fora do intervalo 0-100: {v}')
 missing=[d for d in DIMS if d not in obs]
 contrib={}
 for d in DIMS:
  if d in obs:contrib[d]=1.0-obs[d]/100.0
  else:contrib[d]=float(lambda_doc)
 measured_sq=sum((1.0-v/100.0)**2 for v in obs.values())/7.0
 documentary_sq=len(missing)*(float(lambda_doc)**2)/7.0
 total=100.0*math.sqrt(measured_sq+documentary_sq)
 measured=100.0*math.sqrt(measured_sq);documentary=100.0*math.sqrt(documentary_sq)
 mx=max(contrib.values()) if contrib else None
 dom=[d for d,v in contrib.items() if mx is not None and abs(v-mx)<1e-12]
 unique=sorted(set(round(v,12) for v in contrib.values()),reverse=True)
 second=unique[1] if len(unique)>1 else None
 secondary=[] if second is None else [d for d,v in contrib.items() if abs(v-second)<1e-12]
 profile='predominio_documental' if documentary_sq>measured_sq else ('predominio_deficit_medido' if measured_sq>documentary_sq else 'equilibrado')
 return {'vcg':total,'measured':measured,'documentary':documentary,'n_obs':len(obs),'n_missing':len(missing),'observed':list(obs),'missing':missing,'contrib':contrib,'dominant':dom,'secondary':secondary,'profile':profile,'confidence':confidence(len(obs))}

def summarize(rows):
 vals=[r['vcg'] for r in rows.values()]
 return {'cells':len(rows),'cells_with_vcg':len(vals),'cells_without_vcg':0,'vcg_min':round(min(vals),4),'vcg_p05':round(percentile(vals,5),4),'vcg_median':round(statistics.median(vals),4),'vcg_mean':round(statistics.fmean(vals),4),'vcg_p95':round(percentile(vals,95),4),'vcg_max':round(max(vals),4),'measured_median':round(statistics.median([r['measured'] for r in rows.values()]),4),'documentary_median':round(statistics.median([r['documentary'] for r in rows.values()]),4),'cells_with_documentary_gaps':sum(r['n_missing']>0 for r in rows.values()),'cells_complete_support':sum(r['n_missing']==0 for r in rows.values()),'profiles':{k:sum(r['profile']==k for r in rows.values()) for k in ['predominio_documental','predominio_deficit_medido','equilibrado']},'confidence_classes':{k:sum(r['confidence']==k for r in rows.values()) for k in ['muito limitada','limitada','moderada','boa','alta']}}

def compact_rows(rows):
 out={}
 for hid,r in rows.items():
  vals=r['values'];mask=0
  for i,d in enumerate(DIMS):
   if vals[d] is not None:mask|=1<<i
  out[hid]=[round(r['vcg'],4),round(r['measured'],4),round(r['documentary'],4),r['n_obs'],r['n_missing'],mask,r['profile'],r['confidence'],'|'.join(r['dominant']),'|'.join(r['secondary']),None if r['ide'] is None else round(r['ide'],4),None if r['icg'] is None else round(r['icg'],4),*[None if vals[d] is None else round(vals[d],4) for d in DIMS]]
 return out

def patch_catalog_obj(cat):
 layers=cat.get('layers',[]) if isinstance(cat,dict) else cat
 cfgs={'vazios_250':('250','malha_r5_250km2',1554),'vazios_500':('500','malha_500km2',793),'vazios_1000':('1000','malha_1000km2',412)}
 for item in layers:
  iid=item.get('id') if isinstance(item,dict) else None
  if iid in cfgs:
   sc,grid,count=cfgs[iid]
   item.update({'status':'incorporada','count':count,'source':'ITA ARANDU MS · VCG V38.4.19 · sete dimensões base certificadas','validation':'V38.4.19 · gate V38.4.18 · decomposição entre déficit medido e lacuna documental · sensibilidade lambda auditada','note':'VCG mede vazios do conhecimento geocientífico documentado. null permanece null nas fontes e gera componente documental separado. VCG não é 100 menos ICG. A ficha identifica lacunas dominantes, secundárias e confiança do componente medido.','derive_type':'vcg_snapshot_v38419','grid_source_id':grid,'vcg_scale':sc,'reference_ids':['REF-105','REF-115','REF-114']})
 return cat

def patch_catalog_files(repo):
 jp=repo/'docs/camadas/catalogo-local.json'
 if jp.exists():dump_json(jp,patch_catalog_obj(load_json(jp)))

def patch_app(repo):
 p=repo/'docs/assets/js/app.js';txt=p.read_text(encoding='utf-8-sig')
 prefix='const CATALOG=';pos=txt.find(prefix)
 if pos<0:raise RuntimeError('CATALOG nao localizado em app.js')
 pos+=len(prefix);cat,end=json.JSONDecoder().raw_decode(txt[pos:]);cat=patch_catalog_obj(cat);txt=txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:]
 marker="function icgColor(v){const c=icgClass(v);return ITA_ICG_COLORS[c]||'rgba(0,0,0,0)'}"
 if 'const ITA_VCG_COLORS=' not in txt:
  add="\nconst ITA_VCG_COLORS={'muito baixo':'#fff3e0','baixo':'#ffe0b2','médio':'#ffb74d','alto':'#ef6c00','muito alto':'#8e244d'};\nfunction vcgClass(v){const x=Number(v);if(v===null||v===undefined||!Number.isFinite(x))return'sem cálculo';if(x<20)return'muito baixo';if(x<40)return'baixo';if(x<60)return'médio';if(x<75)return'alto';return'muito alto'}\nfunction vcgColor(v){const c=vcgClass(v);return ITA_VCG_COLORS[c]||'rgba(0,0,0,0)'}"
  if marker not in txt:raise RuntimeError('marcador icgColor nao encontrado')
  txt=txt.replace(marker,marker+add,1)
 fs0=txt.find('function featureStyle(cfg,feat){');fs1=txt.find('function pathGeometry',fs0);fseg=txt[fs0:fs1]
 if fs0<0 or fs1<0:raise RuntimeError('featureStyle nao localizado')
 if "st.renderer==='index_vcg'" not in fseg:
  m="if(st.renderer==='index_icg'){fill=icgColor(p.icg_100);stroke='#4a4a4a';}"
  if m not in fseg:raise RuntimeError('renderer ICG nao encontrado')
  fseg=fseg.replace(m,m+" if(st.renderer==='index_vcg'){fill=vcgColor(p.vcg_100);stroke='#4a4a4a';}",1);txt=txt[:fs0]+fseg+txt[fs1:]
 lg0=txt.find('function layerLegendHtml(cfg){');lg1=txt.find('function updateLegend',lg0);lseg=txt[lg0:lg1 if lg1>lg0 else len(txt)]
 if "if(st.renderer==='index_vcg')return" not in lseg:
  needle="if(st.renderer==='index_icg')return";i=lseg.find(needle)
  if i<0:raise RuntimeError('legenda ICG nao encontrada')
  e=lseg.find('\n',i);e=len(lseg) if e<0 else e
  legend=" if(st.renderer==='index_vcg')return `<div class=\"legend-layer-title\">${esc(cfg.name)}</div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#fff3e0;border:1px solid #4a4a4a\"></span><span>0–&lt;20 · vazio muito baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#ffe0b2;border:1px solid #4a4a4a\"></span><span>20–&lt;40 · vazio baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#ffb74d;border:1px solid #4a4a4a\"></span><span>40–&lt;60 · vazio médio</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#ef6c00;border:1px solid #4a4a4a\"></span><span>60–&lt;75 · vazio alto</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#8e244d;border:1px solid #4a4a4a\"></span><span>75–100 · vazio muito alto</span></div><div class=\"legend-note\">VCG = 100 × √(L_medido + L_documental). null permanece null nas fontes e é contabilizado separadamente como lacuna documental. VCG não é 100 − ICG.</div>`;"
  lseg=lseg[:e+1]+legend+'\n'+lseg[e+1:];txt=txt[:lg0]+lseg+txt[lg1 if lg1>lg0 else len(txt):]
 if 'async function buildVcgSnapshotV38419' not in txt:
  i=txt.find('async function buildIcgSnapshotV38417')
  if i<0:raise RuntimeError('builder ICG nao encontrado')
  builder="""async function buildVcgSnapshotV38419(cfg){
 const gridCfg=CATALOG.layers.find(x=>x.id===cfg.grid_source_id);
 if(!gridCfg)throw new Error('Malha do VCG V38.4.19 não encontrada no catálogo');
 const grid=await ensure(gridCfg),key=String(cfg.vcg_scale||''),scores=window.ITA_VCG_V38419?.grids?.[key],meta=window.ITA_VCG_V38419?.metadata||{};
 if(!scores)throw new Error('Snapshot VCG V38.4.19 não encontrado para esta escala. Execute o materializador do patch.');
 const dims=['IMC','IOD','ICP','IGC','IGQ','IGF','ICS'];
 const features=(grid.features||[]).map(hf=>{const hid=String(hf.properties?.hex_id||''),r=scores[hid];if(!r)return {...hf,properties:{...(hf.properties||{}),vcg_100:null,classe_vcg:'sem cálculo'}};const [vcg,med,doc,nObs,nMiss,mask,profile,conf,domStr,secStr,ide,icg,imc,iod,icp,igc,igq,igf,ics]=r;const obs=dims.filter((d,j)=>(mask&(1<<j))!==0),aus=dims.filter((d,j)=>(mask&(1<<j))===0),dom=(domStr||'').split('|').filter(Boolean),sec=(secStr||'').split('|').filter(Boolean);return {...hf,properties:{...(hf.properties||{}),vcg_100:vcg,classe_vcg:vcgClass(vcg),vcg_medido_100:med,vcg_documental_100:doc,n_dim_observadas:nObs,n_dim_ausentes:nMiss,dimensoes_observadas:obs.join(' · '),dimensoes_ausentes:aus.join(' · '),lacunas_dominantes:dom.join(' · '),lacunas_secundarias:sec.join(' · '),perfil_vcg:profile,confianca_deficit_medido:conf,ide_100_companheiro:ide,icg_100_companheiro:icg,imc_100_base:imc,iod_100_base:iod,icp_100_base:icp,igc_100_base:igc,igq_100_base:igq,igf_100_base:igf,ics_100_base:ics,status_igf_no_corte:meta.igf_cut_status||'MT NAO_AVALIAVEL_NO_CORTE',formula:'VCG_h = 100 × sqrt(L_medido + L_documental)',regra_null:'null permanece null na fonte e gera componente documental separado; não é zero geocientífico.',regra_icg:'VCG não é 100 − ICG. ICG é somente indicador companheiro.',metodo:'V38.4.19 · gate V38.4.18 · RMS de déficits com decomposição documental',data_corte:meta.cut_date||'2026-08-15'}};});
 return {type:'FeatureCollection',features,atlas_metadata:{indice:'VCG',versao:'V38.4.19',escala:key,formula:'VCG_h = 100 × sqrt(L_medido + L_documental)',regra_null:'null permanece null nas fontes',limite:'VCG representa vazios do conhecimento documentado. Não representa ausência de geologia, favorabilidade mineral, recurso, reserva ou valor econômico.'}};
}
"""
  txt=txt[:i]+builder+txt[i:]
 chain="if(!d&&cfg.derive_type==='icg_snapshot_v38417')d=await buildIcgSnapshotV38417(cfg);"
 if "derive_type==='vcg_snapshot_v38419'" not in txt:
  if chain not in txt:raise RuntimeError('cadeia derive ICG nao encontrada')
  txt=txt.replace(chain,chain+"if(!d&&cfg.derive_type==='vcg_snapshot_v38419')d=await buildVcgSnapshotV38419(cfg);",1)
 scale="const ICG_SCALE_LAYERS=['icg_250','icg_500','icg_1000'];"
 if 'const VCG_SCALE_LAYERS=' not in txt:
  if scale not in txt:raise RuntimeError('grupo de escalas ICG nao encontrado')
  txt=txt.replace(scale,scale+" const VCG_SCALE_LAYERS=['vazios_250','vazios_500','vazios_1000'];",1)
 toggle='async function toggle(id,on){const cfg=CATALOG.layers.find(x=>x.id===id);if(!cfg)return;'
 if 'VCG_SCALE_LAYERS.includes(id)' not in txt:
  i=txt.find(toggle)
  if i<0:raise RuntimeError('toggle nao encontrado')
  j=i+len(toggle);inject='if(on&&VCG_SCALE_LAYERS.includes(id)){for(const other of VCG_SCALE_LAYERS){if(other===id)continue;state.active.delete(other);const ocb=document.querySelector(`input[data-layer="${other}"]`);if(ocb)ocb.checked=false;updateLayerCard(other)}}';txt=txt[:j]+inject+txt[j:]
 txt=re.sub(r'service-worker\.js\?v=[0-9.]+','service-worker.js?v='+TOKEN,txt,count=1)
 p.write_text(txt,encoding='utf-8',newline='\n')

def update_web(repo):
 ip=repo/'docs/index.html'
 if ip.exists():
  s=ip.read_text(encoding='utf-8-sig');s=re.sub(r'\?v=[0-9]+(?:\.[0-9]+)+','?v='+TOKEN,s)
  script=f'<script src="./indices/vcg-v38419.js?v={TOKEN}"></script>'
  if 'vcg-v38419.js' not in s:
   m=re.search(r'<script[^>]+src=["\']\./indices/icg-v38417\.js\?v=[^"\']+["\'][^>]*></script>',s)
   if m:s=s[:m.end()]+'\n'+script+s[m.end():]
   else:s=s.replace('</body>',script+'\n</body>',1)
  ip.write_text(s,encoding='utf-8',newline='\n')
 bp=repo/'docs/assets/js/bootstrap.js'
 if bp.exists():
  t=bp.read_text(encoding='utf-8-sig');t=re.sub(r'app\.js\?v=[0-9.]+','app.js?v='+TOKEN,t,count=1);t=re.sub(r'campo-sensores\.js\?v=[0-9.]+','campo-sensores.js?v='+TOKEN,t,count=1);bp.write_text(t,encoding='utf-8',newline='\n')
 swp=repo/'docs/service-worker.js'
 if swp.exists():
  sw=swp.read_text(encoding='utf-8-sig');sw,n=re.subn(r"const ITA_CACHE\s*=\s*'[^']+';","const ITA_CACHE = 'ita-arandu-v38-4-19-vcg-vazios-conhecimento';",sw,count=1)
  if n!=1:raise RuntimeError('ITA_CACHE nao localizado')
  sw=re.sub(r'\?v=[0-9]+(?:\.[0-9]+)+','?v='+TOKEN,sw)
  for asset in [f'./indices/vcg-v38419.js?v={TOKEN}','./documentos/metodologia-vcg.html','./indices/politica-vcg-v38418.json']:
   if asset in sw:continue
   end=sw.find('];')
   if end<0:raise RuntimeError('fim de ITA_CORE nao localizado')
   sw=sw[:end]+'  "'+asset+'",\n'+sw[end:]
  swp.write_text(sw,encoding='utf-8',newline='\n')
 dp=repo/'docs/documentos/index.html'
 if dp.exists():
  d=dp.read_text(encoding='utf-8-sig')
  if 'metodologia-vcg.html' not in d:d=d.replace('</body>','<p><a href="./metodologia-vcg.html">VCG · Vazios de Conhecimento Geocientífico · metodologia V38.4.19</a></p></body>',1)
  dp.write_text(d,encoding='utf-8',newline='\n')

def update_bibliography(repo):
 jp=repo/'docs/referencias/bibliografia-camadas-indices.json'
 if jp.exists():
  o=load_json(jp)
  for e in o.get('entries',[]):
   if isinstance(e,dict) and e.get('id') in {'vazios_250','vazios_500','vazios_1000'}:
    e['status']='incorporada';e['reference_ids']=['REF-105','REF-115','REF-114']
  dump_json(jp,o)
 hp=repo/'docs/referencias/index.html'
 if hp.exists():
  h=hp.read_text(encoding='utf-8-sig')
  for lid in ['vazios_250','vazios_500','vazios_1000']:
   sm=f'id="layer-{lid}"';start=h.find(sm)
   if start<0:continue
   s0=h.rfind('<section',0,start);s1=h.find('</section>',start)
   if s0<0 or s1<0:continue
   s1+=len('</section>');sec=h[s0:s1].replace(' · planejada ·',' · incorporada ·');h=h[:s0]+sec+h[s1:]
  hp.write_text(h,encoding='utf-8',newline='\n')

def write_methodology(repo,snap):
 rows=[]
 for sc in SCALES:
  sm=snap['summary'][sc];se=snap['sensitivity'][sc]
  rows.append(f"<tr><td>{sc} km²</td><td>{sm['cells']}</td><td>{sm['vcg_median']}</td><td>{sm['vcg_p95']}</td><td>{sm['vcg_max']}</td><td>{sm['measured_median']}</td><td>{sm['documentary_median']}</td><td>{se['lambda_0_75']['rho_vs_baseline']}</td><td>{se['lambda_0_5']['rho_vs_baseline']}</td></tr>")
 html="""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ITA ARANDU MS · VCG V38.4.19</title><style>body{font-family:system-ui,Arial,sans-serif;max-width:1120px;margin:auto;padding:28px;line-height:1.58;color:#18212b}h1,h2{color:#8e244d}code{background:#fff3e0;padding:.12rem .3rem;border-radius:4px}table{border-collapse:collapse;width:100%;font-size:.91rem}th,td{border:1px solid #ccd6dd;padding:7px;text-align:right}th:first-child,td:first-child{text-align:left}.warn{background:#fff7e6;padding:12px;border-left:5px solid #ef6c00}.ok{background:#fff3e0;padding:12px;border-left:5px solid #8e244d}</style></head><body>"""
 html+='<h1>VCG · Vazios de Conhecimento Geocientífico · V38.4.19</h1><p class="ok"><b>Estado</b> · materializado em 250, 500 e 1000 km² após o gate V38.4.18.</p>'
 html+='<h2>Função</h2><p>O VCG mede a intensidade e a natureza dos vazios do conhecimento geocientífico documentado. Não representa ausência de geologia, favorabilidade mineral, recurso, reserva ou valor econômico.</p>'
 html+='<h2>Fórmula</h2><p>Para cada dimensão observada <code>S_j = X_j/100</code> e <code>d_j = 1 − S_j</code>. Para cada dimensão sem evidência o valor fonte permanece <code>null</code> e registra-se uma lacuna documental <code>g_j = 1</code>.</p><p><code>L_medido = Σ d_j² / 7</code></p><p><code>L_documental = n_sem_evidencia / 7</code></p><p><b><code>VCG_h = 100 × √(L_medido + L_documental)</code></b></p>'
 html+='<h2>Decomposição</h2><p><code>VCG_medido = 100 × √L_medido</code> e <code>VCG_documental = 100 × √L_documental</code>. As duas parcelas são publicadas separadamente para impedir que ausência documental seja interpretada como valor geocientífico zero.</p>'
 html+='<h2>Lacunas dominantes</h2><p>A contribuição por família é <code>1 − S_j</code> quando observada e 1 quando falta evidência. Empates são preservados. O Atlas não escolhe arbitrariamente uma única lacuna quando várias possuem a mesma contribuição máxima.</p>'
 html+='<h2>Sensibilidade</h2><p>O baseline usa peso documental λ = 1 e é comparado com λ = 0,75 e λ = 0,50. A auditoria registra correlação de Spearman, diferenças absolutas e mudanças de classe.</p>'
 html+='<table><thead><tr><th>Escala</th><th>Células</th><th>Mediana VCG</th><th>P95</th><th>Máx.</th><th>Mediana medida</th><th>Mediana documental</th><th>ρ λ0,75</th><th>ρ λ0,50</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
 html+='<h2>Leitura cartográfica</h2><p>Vazios baixos usam tons claros e vazios altos tons escuros. O contorno é cinza escuro. A ficha mostra VCG total, componentes medido e documental, famílias observadas e ausentes, lacunas dominantes e secundárias, IDE e ICG como indicadores companheiros.</p>'
 html+='<h2>IGF e MT no corte</h2><p>Se IGF possui valor, a indisponibilidade magnetotelúrica não cria uma oitava lacuna e não zera IGF. O estado MT permanece documentado.</p>'
 html+='<h2>Referências</h2><p>Saisana, M., Saltelli, A., &amp; Tarantola, S. (2005). Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators. <i>Journal of the Royal Statistical Society. Series A, 168</i>(2), 307–323. https://doi.org/10.1111/j.1467-985X.2005.00350.x</p><p>Busón Buesa, C., &amp; Gabas, S. G. (2026). <i>Protocolo dos índices multiescalares de conhecimento geocientífico de ITA ARANDU MS</i> [Documento de trabalho]. Universidade Federal de Mato Grosso do Sul.</p></body></html>'
 p=repo/'docs/documentos/metodologia-vcg.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(html,encoding='utf-8',newline='\n')

def update_changelog(repo):
 ch=repo/'CHANGELOG.md';t=ch.read_text(encoding='utf-8-sig') if ch.exists() else '# Changelog\n'
 if 'V38.4.19 · VCG · Vazios de Conhecimento Geocientífico' not in t:
  t=t.rstrip()+"""\n\n## V38.4.19 · VCG · Vazios de Conhecimento Geocientífico\n\n- materializa VCG em 250, 500 e 1000 km² conforme gate V38.4.18\n- separa déficit medido de lacuna documental sem converter null em zero\n- publica lacunas dominantes e secundárias com empates preservados\n- mantém IDE e ICG como indicadores companheiros fora da fórmula\n- propaga a indisponibilidade MT sem criar uma oitava lacuna\n- executa sensibilidade obrigatória para lambda documental 1,00 · 0,75 · 0,50\n- mantém PIG bloqueado até gate próprio\n"""
  ch.write_text(t+'\n',encoding='utf-8',newline='\n')

def calculate(repo):
 cur=(repo/'VERSION').read_text(encoding='utf-8-sig').strip()
 if cur!=EXPECTED:raise RuntimeError(f'base esperada {EXPECTED}, encontrada {cur}')
 pol=load_json(repo/POLICY);gate=load_json(repo/'AUDITORIA_V38_4_18_GATE_VCG_FINAL.json')
 if pol.get('status')!='PASS' or gate.get('status')!='PASS':raise RuntimeError('gate VCG V38.4.18 nao esta PASS')
 snaps={d:load_json(repo/p) for d,p in SNAPS.items()};ide=load_json(repo/IDE);icg=load_json(repo/ICG)
 protected={p:sha256_file(repo/p) for p in list(SNAPS.values())+[IDE,ICG,POLICY,'AUDITORIA_V38_4_17_ICG_FINAL.json','AUDITORIA_V38_4_15_IDE_FINAL.json']}
 grid_hash={p:sha256_file(repo/p) for p in GRIDS.values()}
 allrows={};summary={};sensitivity={}
 for sc in SCALES:
  ids=grid_ids(load_json(repo/GRIDS[sc]));rows={};scenarios={1.0:[],0.75:[],0.5:[]}
  for hid in ids:
   vals={d:score_from(snaps[d],d,sc,hid) for d in DIMS};r=vcg_from_scores(vals,1.0);r['values']=vals;r['ide']=companion_score(ide,sc,hid,'ide_100');r['icg']=companion_score(icg,sc,hid,'icg_100');rows[hid]=r
   for lam in scenarios:scenarios[lam].append(vcg_from_scores(vals,lam)['vcg'])
  base=scenarios[1.0];sensitivity[sc]={}
  for lam in (0.75,0.5):
   alt=scenarios[lam];dif=[abs(a-b) for a,b in zip(base,alt)];changed=sum(class_vcg(a)!=class_vcg(b) for a,b in zip(base,alt));rho=spearman(base,alt)
   sensitivity[sc]['lambda_'+str(lam).replace('.','_')]={'rho_vs_baseline':None if rho is None else round(rho,6),'median_abs_diff':round(statistics.median(dif),4),'p95_abs_diff':round(percentile(dif,95),4),'max_abs_diff':round(max(dif),4),'class_changes':changed,'class_change_fraction':round(changed/len(base),6)}
  sensitivity[sc]['lambda_1_0']={'rho_vs_baseline':1.0,'median_abs_diff':0.0,'p95_abs_diff':0.0,'max_abs_diff':0.0,'class_changes':0,'class_change_fraction':0.0}
  allrows[sc]=rows;summary[sc]=summarize(rows)
 snapshot={'metadata':{'index':'VCG','version':VERSION,'cut_date':CUT_DATE,'generated_at':now_iso(),'formula':'VCG_h = 100 × sqrt(L_medido + L_documental)','measured_term':'L_medido = Σ(1-S_j)^2 / 7 para dimensões observadas','documentary_term':'L_documental = n_sem_evidencia / 7','null_rule':'null permanece null no snapshot fonte e gera componente documental separado; não é valor geocientífico zero','not_icg_complement':'VCG não é 100 − ICG','igf_cut_status':'MT NAO_AVALIAVEL_NO_CORTE quando documentado; não cria oitava lacuna se IGF possui valor','references':['REF-105','REF-115','REF-114']},'protected_input_sha256':protected,'protected_grid_sha256':grid_hash,'summary':summary,'sensitivity':sensitivity,'grids':{sc:compact_rows(allrows[sc]) for sc in SCALES}}
 dump_json(repo/'docs/indices/vcg_v38419_snapshot.json',snapshot)
 js='window.ITA_VCG_V38419='+json.dumps({'metadata':snapshot['metadata'],'summary':summary,'sensitivity':sensitivity,'grids':snapshot['grids']},ensure_ascii=False,separators=(',',':'))+';\n';(repo/'docs/indices/vcg-v38419.js').write_text(js,encoding='utf-8',newline='\n')
 patch_catalog_files(repo);patch_app(repo);update_web(repo);update_bibliography(repo);write_methodology(repo,snapshot);update_changelog(repo)
 for rel,h in protected.items():
  if sha256_file(repo/rel)!=h:raise RuntimeError('arquivo cientifico protegido alterado: '+rel)
 for rel,h in grid_hash.items():
  if sha256_file(repo/rel)!=h:raise RuntimeError('malha protegida alterada: '+rel)
 dump_json(repo/'AUDITORIA_V38_4_19_VCG_RUNTIME.json',{'audit':'V38.4.19 · VCG · materialização runtime','version':VERSION,'generated_at':now_iso(),'status':'PASS','summary':summary,'sensitivity':sensitivity,'protected_input_sha256':protected,'protected_grid_sha256':grid_hash})
 (repo/'VERSION').write_text(VERSION+'\n',encoding='utf-8',newline='\n')
 print('VCG V38.4.19 materializado')
 for sc in SCALES:print(sc+' km2 - '+json.dumps(summary[sc],ensure_ascii=False))
 print('Sensibilidade lambda documental 1.00 / 0.75 / 0.50 concluida')

def self_test():
 tests=[]
 def ck(n,x):tests.append((n,bool(x)))
 r=vcg_from_scores({d:100 for d in DIMS});ck('all_100_zero_gap',abs(r['vcg'])<1e-9)
 r=vcg_from_scores({d:0 for d in DIMS});ck('all_zero_full_gap',abs(r['vcg']-100)<1e-9 and r['documentary']==0)
 r=vcg_from_scores({'IMC':100});ck('missing_documentary',r['n_missing']==6 and r['documentary']>0 and r['measured']==0)
 r=vcg_from_scores({'IMC':0});ck('zero_distinct_from_null',r['measured']>0 and r['documentary']>0)
 r1=vcg_from_scores({'IMC':100},1);r05=vcg_from_scores({'IMC':100},.5);ck('lambda_order',r1['vcg']>r05['vcg'])
 r=vcg_from_scores({});ck('all_missing_100',abs(r['vcg']-100)<1e-9 and r['n_obs']==0)
 ck('ties_preserved',len(vcg_from_scores({'IMC':100})['dominant'])==6)
 print(f'SELF TEST VCG V38.4.19 - {sum(v for _,v in tests)}/{len(tests)}')
 for n,v in tests:
  if not v:print('FAIL - '+n)
 return 0 if all(v for _,v in tests) else 1

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo');ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
 if a.self_test:return self_test()
 if not a.repo:raise SystemExit('--repo e obrigatorio')
 calculate(Path(a.repo).resolve());return 0
if __name__=='__main__':raise SystemExit(main())
