#!/usr/bin/env python3
from pathlib import Path
import argparse,json,math,statistics,datetime,hashlib,re,sys
EXPECTED='V38.4.20-GATE-PIG-20260815'
VERSION='V38.4.21-PIG-PRIORIDADE-INVESTIGACAO-GEOCIENTIFICA-20260815'
TOKEN='38.4.21'
CUT_DATE='2026-08-15'
SCALES=['250','500','1000']
GRIDS={'250':'docs/camadas/arquivos/malha_r5_250km2.geojson','500':'docs/camadas/arquivos/malha_500km2.geojson','1000':'docs/camadas/arquivos/malha_1000km2.geojson'}
GEOLOGY='docs/camadas/arquivos/mapa_geologico_ms.geojson'
VCG='docs/indices/vcg_v38419_snapshot.json'
POLICY='docs/indices/politica-pig-v38420.json'
BASE_STEP=2.5
SENS_STEPS=[1.25,5.0]
PCTS=[90,95,99]
MIN_SUPPORT=4
MIN_PAIRS=2
R=6371007.181
LON0=math.radians(-54.5);LAT0=math.radians(-20.5)
PROTECTED=[
 'docs/indices/imc_v32_snapshot.json','docs/indices/iod_v3848_snapshot.json','docs/indices/icp_v3849_snapshot.json','docs/indices/igc_v38410_snapshot.json','docs/indices/igq_v38411_snapshot.json','docs/indices/igf_v38412_snapshot.json','docs/indices/ics_v38413_snapshot.json',
 'docs/indices/ide_v38415_snapshot.json','docs/indices/icg_v38417_snapshot.json','docs/indices/vcg_v38419_snapshot.json','docs/indices/politica-pig-v38420.json',
 GEOLOGY,*GRIDS.values(),
 'AUDITORIA_V38_4_19_VCG_FINAL.json','AUDITORIA_V38_4_20_GATE_PIG_FINAL.json'
]

def now_iso():return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load_json(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump_json(p,obj,compact=False):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None)+'\n',encoding='utf-8',newline='\n')
def sha256_file(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def num(v):
 if finite(v):return float(v)
 try:
  x=float(v);return x if math.isfinite(x) else None
 except:return None
def percentile(vals,p):
 a=sorted(float(x) for x in vals if x is not None and math.isfinite(float(x)))
 if not a:return None
 if len(a)==1:return a[0]
 q=(len(a)-1)*p/100.0;i=int(math.floor(q));j=int(math.ceil(q))
 return a[i] if i==j else a[i]+(a[j]-a[i])*(q-i)
def rankdata(vals):
 a=sorted(enumerate(vals),key=lambda z:z[1]);r=[0.0]*len(vals);i=0
 while i<len(a):
  j=i+1
  while j<len(a) and a[j][1]==a[i][1]:j+=1
  rr=(i+j-1)/2+1
  for k in range(i,j):r[a[k][0]]=rr
  i=j
 return r
def spearman(a,b):
 if len(a)!=len(b) or len(a)<3:return None
 ra,rb=rankdata(a),rankdata(b);ma=statistics.fmean(ra);mb=statistics.fmean(rb)
 den=(sum((x-ma)**2 for x in ra)*sum((y-mb)**2 for y in rb))**0.5
 return None if den==0 else sum((x-ma)*(y-mb) for x,y in zip(ra,rb))/den

def laea(lon,lat):
 lam=math.radians(lon);phi=math.radians(lat);den=1+math.sin(LAT0)*math.sin(phi)+math.cos(LAT0)*math.cos(phi)*math.cos(lam-LON0);k=math.sqrt(2/max(den,1e-15))
 return (R*k*math.cos(phi)*math.sin(lam-LON0),R*k*(math.cos(LAT0)*math.sin(phi)-math.sin(LAT0)*math.cos(phi)*math.cos(lam-LON0)))
def proj_geom(g):
 typ=g.get('type');c=g.get('coordinates')
 if typ=='Polygon':return {'type':'Polygon','coordinates':[[laea(x,y) for x,y in ring] for ring in c]}
 if typ=='MultiPolygon':return {'type':'MultiPolygon','coordinates':[[[laea(x,y) for x,y in ring] for ring in poly] for poly in c]}
 raise RuntimeError('geometria nao poligonal: '+str(typ))
def rings(g):
 if g['type']=='Polygon':return [g['coordinates']]
 return list(g['coordinates'])
def bbox_geom(g):
 xs=[];ys=[]
 for poly in rings(g):
  for ring in poly:
   for x,y in ring:xs.append(x);ys.append(y)
 return min(xs),min(ys),max(xs),max(ys)
def point_ring(x,y,ring):
 inside=False;j=len(ring)-1
 for i in range(len(ring)):
  xi,yi=ring[i];xj,yj=ring[j]
  if ((yi>y)!=(yj>y)):
   xx=(xj-xi)*(y-yi)/(yj-yi)+xi
   if x<xx:inside=not inside
  j=i
 return inside
def point_geom(x,y,g):
 for poly in rings(g):
  if not poly:continue
  if point_ring(x,y,poly[0]):
   if not any(point_ring(x,y,h) for h in poly[1:]):return True
 return False

def build_bins(items,bin_m=50000.0):
 bins={}
 for idx,z in enumerate(items):
  b=z['bbox'];ix0=math.floor(b[0]/bin_m);ix1=math.floor(b[2]/bin_m);iy0=math.floor(b[1]/bin_m);iy1=math.floor(b[3]/bin_m)
  for ix in range(ix0,ix1+1):
   for iy in range(iy0,iy1+1):bins.setdefault((ix,iy),[]).append(idx)
 return bins
def candidates_for(x,y,bins,bin_m=50000.0):return bins.get((math.floor(x/bin_m),math.floor(y/bin_m)),[])
def prepare_geology(fc):
 out=[]
 for i,f in enumerate(fc.get('features',[])):
  p=f.get('properties') or {};geom=f.get('geometry')
  if not geom:continue
  g=proj_geom(geom);uid=str(p.get('ID_UNIDADE_ESTRATIGRAFICA') or p.get('SIGLA') or p.get('NOME') or ('U'+str(i)))
  out.append({'uid':uid,'sigla':p.get('SIGLA'),'nome':p.get('NOME'),'geom':g,'bbox':bbox_geom(g)})
 if not out:raise RuntimeError('mapa geologico sem feicoes')
 return out
def prepare_cells(repo):
 out={}
 for sc in SCALES:
  arr=[]
  for f in load_json(repo/GRIDS[sc]).get('features',[]):
   hid=str((f.get('properties') or {}).get('hex_id') or '')
   if not hid:raise RuntimeError('hex sem hex_id')
   g=proj_geom(f['geometry']);arr.append({'hid':hid,'geom':g,'bbox':bbox_geom(g)})
  out[sc]={'cells':arr,'bins':build_bins(arr)}
 return out
def state_bbox(cells250):
 bs=[z['bbox'] for z in cells250];return min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs)
def shannon_neff(counts):
 n=sum(counts.values())
 if n<=0:return None
 h=0.0
 for c in counts.values():
  if c>0:
   p=c/n;h-=p*math.log(p)
 return math.exp(h)
def grid_params(bbox,step_km):
 step=step_km*1000.0;x0=math.floor(bbox[0]/step)*step;y0=math.floor(bbox[1]/step)*step
 return step,x0,y0
def ring_intervals(ring,y):
 xs=[];n=len(ring)
 for i in range(n-1):
  x1,y1=ring[i];x2,y2=ring[i+1]
  if (y1>y)!=(y2>y):xs.append(x1+(y-y1)*(x2-x1)/(y2-y1))
 if ring and ring[0]!=ring[-1]:
  x1,y1=ring[-1];x2,y2=ring[0]
  if (y1>y)!=(y2>y):xs.append(x1+(y-y1)*(x2-x1)/(y2-y1))
 xs.sort();return [(xs[i],xs[i+1]) for i in range(0,len(xs)-1,2)]
def ix_ranges(intervals,step,x0):
 out=[]
 for a,b in intervals:
  i0=math.ceil((a-x0)/step-0.5-1e-12);i1=math.ceil((b-x0)/step-0.5-1e-12)-1
  if i1>=i0:out.append((i0,i1))
 return out
def in_ranges(ix,ranges):return any(a<=ix<=b for a,b in ranges)
def raster_geom_keys(geom,step,x0,y0):
 keys=set();minx,miny,maxx,maxy=bbox_geom(geom);iy0=math.ceil((miny-y0)/step-0.5-1e-12);iy1=math.floor((maxy-y0)/step-0.5+1e-12)
 for poly in rings(geom):
  if not poly:continue
  outer=poly[0];holes=poly[1:]
  for iy in range(iy0,iy1+1):
   y=y0+(iy+0.5)*step;ors=ix_ranges(ring_intervals(outer,y),step,x0)
   if not ors:continue
   hrs=[]
   for h in holes:hrs.extend(ix_ranges(ring_intervals(h,y),step,x0))
   for a,b in ors:
    for ix in range(a,b+1):
     if not in_ranges(ix,hrs):keys.add((ix,iy))
 return keys
def classify_geology_raster(geology,step,x0,y0):
 geo={};overlaps=set()
 for z in geology:
  for k in raster_geom_keys(z['geom'],step,x0,y0):
   if k in geo:
    if geo[k]!=z['uid']:overlaps.add(k)
   else:geo[k]=z['uid']
 return geo,overlaps
def raw_cell_from_keys(keys,geo,overlaps):
 classified={k:geo[k] for k in keys if k in geo};counts={}
 for uid in classified.values():counts[uid]=counts.get(uid,0)+1
 pairs=trans=0;ck=set(classified)
 for ix,iy in ck:
  u=classified[(ix,iy)]
  for nb in ((ix+1,iy),(ix,iy+1)):
   if nb in ck:pairs+=1;trans+=int(u!=classified[nb])
 ne=shannon_neff(counts);n=len(classified)
 return {'n_support':n,'overlap_fraction':sum(k in overlaps for k in classified)/n if n else 0.0,'n_units':len(counts),'unit_neff':ne,'unit_excess':max(0.0,(ne or 0)-1.0),'transition_fraction':trans/pairs if pairs else 0.0,'transition_pairs':pairs,'evaluable':n>=MIN_SUPPORT and pairs>=MIN_PAIRS}
def prepare_raw(repo,geology,cells,bbox,step_km):
 print(f'Complexidade · rasterizando micromalha global {step_km:g} km...',flush=True);step,x0,y0=grid_params(bbox,step_km);geo,overlaps=classify_geology_raster(geology,step,x0,y0);print(f'Complexidade · {len(geo)} microcelulas geologicas classificadas · sobreposicoes {len(overlaps)}',flush=True);out={}
 for sc in SCALES:
  rows={}
  for z in cells[sc]['cells']:rows[z['hid']]=raw_cell_from_keys(raster_geom_keys(z['geom'],step,x0,y0),geo,overlaps)
  out[sc]=rows;print(f'Complexidade · escala {sc} km2 associada',flush=True)
 return out
def normalize_complexity(rows,pct_norm=95):
 ev=[r for r in rows.values() if r['evaluable']];dpos=[r['unit_excess'] for r in ev if r['unit_excess']>0];tpos=[r['transition_fraction'] for r in ev if r['transition_fraction']>0];dp=percentile(dpos,pct_norm) or 1.0;tp=percentile(tpos,pct_norm) or 1.0;vals={}
 for hid,r in rows.items():
  if not r['evaluable']:vals[hid]=None;continue
  ds=min(1.0,r['unit_excess']/dp) if dp>0 else 0.0;ts=min(1.0,r['transition_fraction']/tp) if tp>0 else 0.0;vals[hid]=100*math.sqrt(max(0.0,ds*ts))
 return vals,{'D_excess_P':dp,'T_transicao_P':tp,'percentile':pct_norm}
def vcg_record(vcg,sc,hid):
 r=(vcg.get('grids') or {}).get(sc,{}).get(hid)
 if not isinstance(r,list) or len(r)<10:return None
 return {'vcg':num(r[0]),'measured':num(r[1]),'documentary':num(r[2]),'n_obs':r[3],'dominant':r[8] or '','secondary':r[9] or ''}
def class_pig(v):
 if v is None:return 'sem cálculo'
 if v<20:return 'muito baixa'
 if v<40:return 'baixa'
 if v<60:return 'média'
 if v<80:return 'alta'
 return 'muito alta'
def nondominated_fronts(points):
 # Higher is better in both objectives. Rank is the Pareto layer number.
 order=sorted(range(len(points)),key=lambda i:(-points[i][1],-points[i][2],points[i][0]));front=[None]*len(points);done=[]
 for i in order:
  _,vi,ci=points[i];best=0
  for j in done:
   _,vj,cj=points[j]
   if vj>=vi and cj>=ci and (vj>vi or cj>ci):best=max(best,front[j])
  front[i]=best+1;done.append(i)
 return front
def pig100(front,fmax):
 if front is None:return None
 return 100.0 if fmax<=1 else 100.0*(1.0-(front-1)/(fmax-1))
def make_scenario(vcg,raw_by_scale,pct_norm):
 out={}
 for sc in SCALES:
  comp,norm=normalize_complexity(raw_by_scale[sc],pct_norm);pts=[]
  for hid,c in comp.items():
   vr=vcg_record(vcg,sc,hid)
   if c is not None and vr and vr['vcg'] is not None:pts.append((hid,float(vr['vcg']),float(c)))
  fronts=nondominated_fronts(pts);fmax=max(fronts) if fronts else 0;front_sizes={f:fronts.count(f) for f in set(fronts)};rows={}
  for (hid,v,c),fr in zip(pts,fronts):rows[hid]={'cgeo':c,'front':fr,'fmax':fmax,'pig':pig100(fr,fmax),'class':class_pig(pig100(fr,fmax)),'front_size':front_sizes[fr]}
  out[sc]={'rows':rows,'normalization':norm,'fronts_total':fmax,'front1_cells':fronts.count(1) if fronts else 0,'eligible_cells':len(rows)}
 return out
def compare_scenario(base,alt):
 common=sorted(set(base)&set(alt));b_c=[base[h]['cgeo'] for h in common];a_c=[alt[h]['cgeo'] for h in common];b_p=[base[h]['pig'] for h in common];a_p=[alt[h]['pig'] for h in common]
 rho_c=spearman(b_c,a_c) if common else None;rho_p=spearman(b_p,a_p) if common else None;frontchg=sum(base[h]['front']!=alt[h]['front'] for h in common);classchg=sum(base[h]['class']!=alt[h]['class'] for h in common);b1={h for h in base if base[h]['front']==1};a1={h for h in alt if alt[h]['front']==1};union=b1|a1
 return {'common_cells':len(common),'eligibility_changes':len(set(base)^set(alt)),'spearman_cgeo':None if rho_c is None else round(rho_c,6),'spearman_pig100':None if rho_p is None else round(rho_p,6),'median_abs_diff_cgeo':round(statistics.median([abs(x-y) for x,y in zip(b_c,a_c)]),4) if common else None,'median_abs_diff_pig100':round(statistics.median([abs(x-y) for x,y in zip(b_p,a_p)]),4) if common else None,'front_changes':frontchg,'front_change_fraction':round(frontchg/len(common),6) if common else None,'class_changes':classchg,'class_change_fraction':round(classchg/len(common),6) if common else None,'front1_jaccard':round(len(b1&a1)/len(union),6) if union else 1.0}
def summarize(vals):
 if not vals:return {'n':0}
 return {'n':len(vals),'min':round(min(vals),4),'p05':round(percentile(vals,5),4),'median':round(statistics.median(vals),4),'mean':round(statistics.fmean(vals),4),'p95':round(percentile(vals,95),4),'max':round(max(vals),4)}
def compact_rows(ids,baseline,raw,vcg):
 out={}
 for hid in ids:
  r=baseline.get(hid);rr=raw.get(hid) or {};vr=vcg_record(vcg[0],vcg[1],hid)
  if r is None:
   out[hid]=[None,None,None,vr['vcg'] if vr else None,None,None,rr.get('unit_neff'),rr.get('transition_fraction'),rr.get('n_support'),rr.get('n_units'),rr.get('overlap_fraction'), 'sem cálculo',None,vr['measured'] if vr else None,vr['documentary'] if vr else None,vr['n_obs'] if vr else None,vr['dominant'] if vr else '',vr['secondary'] if vr else '']
  else:
   out[hid]=[round(r['pig'],4),r['front'],r['fmax'],round(vr['vcg'],4),round(r['cgeo'],4),r['front_size'],None if rr.get('unit_neff') is None else round(rr['unit_neff'],4),round(rr.get('transition_fraction') or 0,6),rr.get('n_support'),rr.get('n_units'),round(rr.get('overlap_fraction') or 0,6),class_pig(round(r['pig'],4)),r['front_size'],round(vr['measured'],4),round(vr['documentary'],4),vr['n_obs'],vr['dominant'],vr['secondary']]
 return out

def patch_catalog_obj(cat,summary):
 layers=cat.get('layers',[]) if isinstance(cat,dict) else cat;cfgs={'pig_250':('250','malha_r5_250km2',1554),'pig_500':('500','malha_500km2',793),'pig_1000':('1000','malha_1000km2',412)}
 for item in layers:
  iid=item.get('id') if isinstance(item,dict) else None
  if iid in cfgs:
   sc,grid,count=cfgs[iid];sm=summary.get(sc,{})
   item.update({'status':'incorporada','count':count,'source':'ITA ARANDU MS · PIG V38.4.21 · VCG V38.4.19 + complexidade litoestratigráfica SGB 1:1.000.000','validation':'V38.4.21 · gate V38.4.20 · Pareto sem soma ponderada · sensibilidade 1,25/2,5/5 km e P90/P95/P99 auditada','note':'PIG ordena prioridade relativa de investigação por fronts de Pareto entre VCG e C_geo. PIG_100 é transformação ordinal apenas para simbologia. Não indica favorabilidade mineral, jazida, recurso, reserva ou valor econômico.','derive_type':'pig_snapshot_v38421','grid_source_id':grid,'pig_scale':sc,'reference_ids':['REF-002','REF-004','REF-082','REF-105','REF-115','REF-116']})
 return cat
def patch_catalog_files(repo,summary):
 p=repo/'docs/camadas/catalogo-local.json'
 if p.exists():dump_json(p,patch_catalog_obj(load_json(p),summary))
def patch_app(repo,summary):
 p=repo/'docs/assets/js/app.js';txt=p.read_text(encoding='utf-8-sig');prefix='const CATALOG=';pos=txt.find(prefix)
 if pos<0:raise RuntimeError('CATALOG nao localizado em app.js')
 pos+=len(prefix);cat,end=json.JSONDecoder().raw_decode(txt[pos:]);cat=patch_catalog_obj(cat,summary);txt=txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:]
 marker="function vcgColor(v){const c=vcgClass(v);return ITA_VCG_COLORS[c]||'rgba(0,0,0,0)'}"
 if 'const ITA_PIG_COLORS=' not in txt:
  add="\nconst ITA_PIG_COLORS={'muito baixa':'#f3e5f5','baixa':'#e1bee7','média':'#ce93d8','alta':'#8e44ad','muito alta':'#4a148c'};\nfunction pigClass(v){const x=Number(v);if(v===null||v===undefined||!Number.isFinite(x))return'sem cálculo';if(x<20)return'muito baixa';if(x<40)return'baixa';if(x<60)return'média';if(x<80)return'alta';return'muito alta'}\nfunction pigColor(v){const c=pigClass(v);return ITA_PIG_COLORS[c]||'rgba(0,0,0,0)'}"
  if marker not in txt:raise RuntimeError('marcador vcgColor nao encontrado')
  txt=txt.replace(marker,marker+add,1)
 fs0=txt.find('function featureStyle(cfg,feat){');fs1=txt.find('function pathGeometry',fs0);seg=txt[fs0:fs1]
 if "st.renderer==='index_pig'" not in seg:
  m="if(st.renderer==='index_vcg'){fill=vcgColor(p.vcg_100);stroke='#4a4a4a';}"
  if m not in seg:raise RuntimeError('renderer VCG nao encontrado')
  seg=seg.replace(m,m+" if(st.renderer==='index_pig'){fill=pigColor(p.pig_100);stroke='#4a4a4a';}",1);txt=txt[:fs0]+seg+txt[fs1:]
 lg0=txt.find('function layerLegendHtml(cfg){');lg1=txt.find('function updateLegend',lg0);seg=txt[lg0:lg1 if lg1>lg0 else len(txt)]
 if "if(st.renderer==='index_pig')return" not in seg:
  needle="if(st.renderer==='index_vcg')return";i=seg.find(needle)
  if i<0:raise RuntimeError('legenda VCG nao encontrada')
  e=seg.find('\n',i);e=len(seg) if e<0 else e
  legend=" if(st.renderer==='index_pig')return `<div class=\"legend-layer-title\">${esc(cfg.name)}</div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#f3e5f5;border:1px solid #4a4a4a\"></span><span>0–&lt;20 · prioridade ordinal muito baixa</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#e1bee7;border:1px solid #4a4a4a\"></span><span>20–&lt;40 · baixa</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#ce93d8;border:1px solid #4a4a4a\"></span><span>40–&lt;60 · média</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#8e44ad;border:1px solid #4a4a4a\"></span><span>60–&lt;80 · alta</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#4a148c;border:1px solid #4a4a4a\"></span><span>80–100 · muito alta</span></div><div class=\"legend-note\">PIG_100 é transformação ordinal do front de Pareto entre VCG e C_geo. Front 1 é a prioridade científica primária. Não interpretar diferenças de PIG_100 como distâncias cardinais.</div>`;"
  seg=seg[:e+1]+legend+'\n'+seg[e+1:];txt=txt[:lg0]+seg+txt[lg1 if lg1>lg0 else len(txt):]
 if 'async function buildPigSnapshotV38421' not in txt:
  i=txt.find('async function buildVcgSnapshotV38419')
  if i<0:raise RuntimeError('builder VCG nao encontrado')
  builder="""async function buildPigSnapshotV38421(cfg){
 const gridCfg=CATALOG.layers.find(x=>x.id===cfg.grid_source_id);if(!gridCfg)throw new Error('Malha do PIG V38.4.21 não encontrada no catálogo');
 const grid=await ensure(gridCfg),key=String(cfg.pig_scale||''),scores=window.ITA_PIG_V38421?.grids?.[key],meta=window.ITA_PIG_V38421?.metadata||{};if(!scores)throw new Error('Snapshot PIG V38.4.21 não encontrado para esta escala. Execute o materializador do patch.');
 const features=(grid.features||[]).map(hf=>{const hid=String(hf.properties?.hex_id||''),r=scores[hid];if(!r)return {...hf,properties:{...(hf.properties||{}),pig_100:null,pareto_front:null,classe_pig:'sem cálculo'}};const [pig,front,fmax,vcg,cgeo,frontSize,neff,tr,nSupport,nUnits,overlap,classe,frontSize2,vcgMed,vcgDoc,nObs,dom,sec]=r;return {...hf,properties:{...(hf.properties||{}),pig_100:pig,pareto_front:front,pareto_fronts_total:fmax,classe_pig:classe||pigClass(pig),tamanho_front:frontSize,vcg_100:vcg,complexidade_geo_100:cgeo,diversidade_efetiva_unidades:neff,fracao_transicoes_litoestratigraficas:tr,n_suportes_geologicos:nSupport,n_unidades_litoestratigraficas:nUnits,sobreposicao_geologica_fracao:overlap,vcg_medido_100:vcgMed,vcg_documental_100:vcgDoc,n_dim_observadas_vcg:nObs,lacunas_dominantes:dom||'',lacunas_secundarias:sec||'',regra_pareto:'maximizar simultaneamente VCG e C_geo; sem soma ponderada; empates permanecem no mesmo front',regra_pig100:'PIG_100 = transformação ordinal do front para simbologia; não é escala cardinal',fonte_complexidade:'Mapa geológico estadual SGB 1:1.000.000 · micromalha global 2,5 km',limitacao_complexidade:'C_geo mede heterogeneidade litoestratigráfica cartografada; não é densidade de falhas, complexidade estrutural total ou favorabilidade mineral',data_corte:meta.cut_date||'2026-08-15'}};});
 return {type:'FeatureCollection',features,atlas_metadata:{indice:'PIG',versao:'V38.4.21',escala:key,objetivos:'VCG + C_geo por dominância de Pareto',saida_primaria:'pareto_front',pig100:'transformação ordinal para simbologia',limite:'Prioridade relativa de investigação geocientífica. Não representa favorabilidade mineral, jazida, recurso, reserva ou valor econômico.'}};
}
"""
  txt=txt[:i]+builder+txt[i:]
 chain="if(!d&&cfg.derive_type==='vcg_snapshot_v38419')d=await buildVcgSnapshotV38419(cfg);"
 if "derive_type==='pig_snapshot_v38421'" not in txt:
  if chain not in txt:raise RuntimeError('cadeia derive VCG nao encontrada')
  txt=txt.replace(chain,chain+"if(!d&&cfg.derive_type==='pig_snapshot_v38421')d=await buildPigSnapshotV38421(cfg);",1)
 scale="const VCG_SCALE_LAYERS=['vazios_250','vazios_500','vazios_1000'];"
 if 'const PIG_SCALE_LAYERS=' not in txt:
  if scale not in txt:raise RuntimeError('grupo VCG nao encontrado')
  txt=txt.replace(scale,scale+" const PIG_SCALE_LAYERS=['pig_250','pig_500','pig_1000'];",1)
 toggle='async function toggle(id,on){const cfg=CATALOG.layers.find(x=>x.id===id);if(!cfg)return;'
 if 'PIG_SCALE_LAYERS.includes(id)' not in txt:
  i=txt.find(toggle)
  if i<0:raise RuntimeError('toggle nao encontrado')
  j=i+len(toggle);inject='if(on&&PIG_SCALE_LAYERS.includes(id)){for(const other of PIG_SCALE_LAYERS){if(other===id)continue;state.active.delete(other);const ocb=document.querySelector(`input[data-layer="${other}"]`);if(ocb)ocb.checked=false;updateLayerCard(other)}}';txt=txt[:j]+inject+txt[j:]
 txt=re.sub(r'service-worker\.js\?v=[0-9.]+','service-worker.js?v='+TOKEN,txt,count=1);p.write_text(txt,encoding='utf-8',newline='\n')
def update_web(repo):
 ip=repo/'docs/index.html'
 if ip.exists():
  s=ip.read_text(encoding='utf-8-sig');s=re.sub(r'\?v=[0-9]+(?:\.[0-9]+)+','?v='+TOKEN,s);script=f'<script src="./indices/pig-v38421.js?v={TOKEN}"></script>'
  if 'pig-v38421.js' not in s:
   m=re.search(r'<script[^>]+src=["\']\./indices/vcg-v38419\.js\?v=[^"\']+["\'][^>]*></script>',s)
   if m:s=s[:m.end()]+'\n'+script+s[m.end():]
   else:s=s.replace('</body>',script+'\n</body>',1)
  ip.write_text(s,encoding='utf-8',newline='\n')
 bp=repo/'docs/assets/js/bootstrap.js'
 if bp.exists():
  t=bp.read_text(encoding='utf-8-sig');t=re.sub(r'app\.js\?v=[0-9.]+','app.js?v='+TOKEN,t,count=1);t=re.sub(r'campo-sensores\.js\?v=[0-9.]+','campo-sensores.js?v='+TOKEN,t,count=1);bp.write_text(t,encoding='utf-8',newline='\n')
 swp=repo/'docs/service-worker.js'
 if swp.exists():
  sw=swp.read_text(encoding='utf-8-sig');sw,n=re.subn(r"const ITA_CACHE\s*=\s*'[^']+';","const ITA_CACHE = 'ita-arandu-v38-4-21-pig-prioridade-investigacao';",sw,count=1)
  if n!=1:raise RuntimeError('ITA_CACHE nao localizado')
  sw=re.sub(r'\?v=[0-9]+(?:\.[0-9]+)+','?v='+TOKEN,sw)
  for asset in [f'./indices/pig-v38421.js?v={TOKEN}','./documentos/metodologia-pig.html','./indices/politica-pig-v38420.json']:
   if asset not in sw:
    end=sw.find('];')
    if end<0:raise RuntimeError('fim ITA_CORE nao localizado')
    sw=sw[:end]+'  "'+asset+'",\n'+sw[end:]
  swp.write_text(sw,encoding='utf-8',newline='\n')
 dp=repo/'docs/documentos/index.html'
 if dp.exists():
  d=dp.read_text(encoding='utf-8-sig')
  if 'metodologia-pig.html' not in d:d=d.replace('</body>','<p><a href="./metodologia-pig.html">PIG · Prioridade de Investigação Geocientífica · metodologia V38.4.21</a></p></body>',1)
  dp.write_text(d,encoding='utf-8',newline='\n')
def update_bibliography(repo):
 p=repo/'docs/referencias/bibliografia-camadas-indices.json'
 if p.exists():
  o=load_json(p)
  for e in o.get('entries',[]):
   if isinstance(e,dict) and e.get('id') in {'pig_250','pig_500','pig_1000'}:e['status']='incorporada';e['reference_ids']=['REF-002','REF-004','REF-082','REF-105','REF-115','REF-116']
  dump_json(p,o)
 hp=repo/'docs/referencias/index.html'
 if hp.exists():
  h=hp.read_text(encoding='utf-8-sig')
  for lid in ['pig_250','pig_500','pig_1000']:
   start=h.find(f'id="layer-{lid}"')
   if start<0:continue
   s0=h.rfind('<section',0,start);s1=h.find('</section>',start)
   if s0>=0 and s1>=0:
    s1+=len('</section>');sec=h[s0:s1].replace(' · planejada ·',' · incorporada ·');h=h[:s0]+sec+h[s1:]
  hp.write_text(h,encoding='utf-8',newline='\n')
def write_methodology(repo,snapshot):
 rows=[]
 for sc in SCALES:
  sm=snapshot['summary'][sc];se=snapshot['sensitivity'][sc]
  rows.append(f"<tr><td>{sc} km²</td><td>{sm['eligible_cells']}</td><td>{sm['pareto_fronts']}</td><td>{sm['front_1_cells']}</td><td>{sm['cgeo']['median']}</td><td>{sm['vcg_eligible']['median']}</td><td>{se['microgrid_1_25_P95']['spearman_cgeo']}</td><td>{se['microgrid_5_P95']['spearman_cgeo']}</td><td>{se['normalizacao_P90']['front1_jaccard']}</td><td>{se['normalizacao_P99']['front1_jaccard']}</td></tr>")
 html="""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ITA ARANDU MS · PIG V38.4.21</title><style>body{font-family:system-ui,Arial,sans-serif;max-width:1120px;margin:auto;padding:28px;line-height:1.58;color:#18212b}h1,h2{color:#4a148c}code{background:#f3e5f5;padding:.12rem .3rem;border-radius:4px}table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{border:1px solid #ccd6dd;padding:7px;text-align:right}th:first-child,td:first-child{text-align:left}.warn{background:#fff8e1;padding:12px;border-left:5px solid #f9a825}.ok{background:#f3e5f5;padding:12px;border-left:5px solid #4a148c}</style></head><body>"""
 html+='<h1>PIG · Prioridade de Investigação Geocientífica · V38.4.21</h1><p class="ok"><b>Estado</b> · materializado em 250, 500 e 1000 km² após o gate V38.4.20.</p>'
 html+='<h2>Função</h2><p>O PIG ordena prioridades relativas de investigação geocientífica. Não mede favorabilidade mineral, probabilidade de jazida, recurso, reserva, teor econômico ou valor econômico.</p>'
 html+='<h2>Dois objetivos</h2><p><b>VCG</b> representa vazios do conhecimento documentado. <b>C_geo</b> representa heterogeneidade litoestratigráfica cartografada independentemente do VCG.</p>'
 html+='<p><code>D_raw = N_eff − 1</code>, com <code>N_eff = exp(H)</code>. <code>T_raw</code> é a fração de transições entre unidades em pares ortogonais adjacentes da micromalha global de 2,5 km. <code>D*</code> e <code>T*</code> saturam em P95 por escala.</p><p><b><code>C_geo = 100 × √(D* × T*)</code></b></p>'
 html+='<h2>Dominância de Pareto</h2><p>Maximizam-se simultaneamente VCG e C_geo. Uma célula domina outra se não for pior em nenhum objetivo e for estritamente melhor em pelo menos um. Não existe soma ponderada. Empates permanecem no mesmo front.</p>'
 html+='<p>O <b>front de Pareto</b> é a saída científica primária. Front 1 contém as células não dominadas.</p><p><code>PIG_100 = 100 × [1 − (front−1)/(Fmax−1)]</code> quando Fmax &gt; 1. PIG_100 é apenas transformação ordinal para simbologia e não pode ser interpretado como distância cardinal.</p>'
 html+='<h2>Sensibilidade</h2><p>Foram comparadas micromalhas de 1,25 km, 2,5 km e 5 km e normalizações P90, P95 e P99. A auditoria registra Spearman de C_geo e PIG_100, mudanças de front, mudanças de classe, elegibilidade e Jaccard do front 1.</p>'
 html+='<table><thead><tr><th>Escala</th><th>Elegíveis</th><th>Fronts</th><th>Front 1</th><th>Mediana C_geo</th><th>Mediana VCG</th><th>ρ Cgeo 1,25</th><th>ρ Cgeo 5</th><th>Jaccard F1 P90</th><th>Jaccard F1 P99</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
 html+='<h2>Limitações</h2><p>C_geo depende do mapa geológico estadual a 1:1.000.000 e mede complexidade litoestratigráfica cartografada. Não equivale a densidade de falhas, deformação, complexidade estrutural total ou favorabilidade mineral. PIG é prioridade relativa dentro do corte e escala analisados.</p>'
 html+='<h2>Referências</h2><p>Lacerda Filho, J. V., et al. (2006). <i>Geologia e recursos minerais do estado de Mato Grosso do Sul</i>. CPRM. Escala 1:1.000.000.</p><p>Serviço Geológico do Brasil. (s.d.). <i>Mato Grosso do Sul, 1:1.000.000 [2006]. Litoestratigrafia dos estados</i> [Camada geoespacial]. Geoportal SGB.</p><p>Saisana, M., Saltelli, A., &amp; Tarantola, S. (2005). Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators. <i>Journal of the Royal Statistical Society. Series A, 168</i>(2), 307–323. https://doi.org/10.1111/j.1467-985X.2005.00350.x</p><p>Deb, K., Pratap, A., Agarwal, S., &amp; Meyarivan, T. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. <i>IEEE Transactions on Evolutionary Computation, 6</i>(2), 182–197. https://doi.org/10.1109/4235.996017</p><p>Busón Buesa, C., &amp; Gabas, S. G. (2026). <i>Protocolo dos índices multiescalares de conhecimento geocientífico de ITA ARANDU MS</i> [Documento de trabalho]. Universidade Federal de Mato Grosso do Sul.</p></body></html>'
 p=repo/'docs/documentos/metodologia-pig.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(html,encoding='utf-8',newline='\n')
def update_changelog(repo):
 p=repo/'CHANGELOG.md';t=p.read_text(encoding='utf-8-sig') if p.exists() else '# Changelog\n';t=t.replace('Sensibilidade obrigatória de suporte 13/17/21 e normalização P90/P95/P99.','Sensibilidade obrigatória de micromalha 1,25/2,5/5 km e normalização P90/P95/P99.')
 if 'V38.4.21 · PIG · Prioridade de Investigação Geocientífica' not in t:
  t=t.rstrip()+"""\n\n## V38.4.21 · PIG · Prioridade de Investigação Geocientífica\n\n- materializa PIG em 250, 500 e 1000 km² conforme gate V38.4.20\n- calcula C_geo independentemente a partir do mapa geológico estadual SGB 1:1.000.000\n- ordena VCG e C_geo por fronts de dominância de Pareto, sem soma ponderada\n- preserva empates e publica tamanho do front\n- publica PIG_100 somente como transformação ordinal para simbologia\n- executa sensibilidade de micromalha 1,25/2,5/5 km e P90/P95/P99\n- próxima etapa obrigatória é auditoria ZERO final da família de índices\n"""
 p.write_text(t+'\n',encoding='utf-8',newline='\n')
def calculate(repo):
 cur=(repo/'VERSION').read_text(encoding='utf-8-sig').strip()
 if cur!=EXPECTED:raise RuntimeError(f'base esperada {EXPECTED}, encontrada {cur}')
 gate=load_json(repo/'AUDITORIA_V38_4_20_GATE_PIG_FINAL.json');policy=load_json(repo/POLICY);vcg=load_json(repo/VCG)
 if gate.get('status')!='PASS' or policy.get('status')!='PASS':raise RuntimeError('gate PIG V38.4.20 nao esta PASS')
 for rel in PROTECTED:
  if not (repo/rel).exists():raise RuntimeError('arquivo protegido ausente: '+rel)
 protected={rel:sha256_file(repo/rel) for rel in PROTECTED}
 geology=prepare_geology(load_json(repo/GEOLOGY));cells=prepare_cells(repo);bbox=state_bbox(cells['250']['cells'])
 raw_base=prepare_raw(repo,geology,cells,bbox,BASE_STEP);base=make_scenario(vcg,raw_base,95)
 alt_step={}
 for step in SENS_STEPS:
  raw_alt=prepare_raw(repo,geology,cells,bbox,step);alt_step[step]=make_scenario(vcg,raw_alt,95)
 alt_pct={90:make_scenario(vcg,raw_base,90),99:make_scenario(vcg,raw_base,99)}
 grids={};summary={};sensitivity={}
 for sc in SCALES:
  ids=[z['hid'] for z in cells[sc]['cells']];brows=base[sc]['rows'];grids[sc]=compact_rows(ids,brows,raw_base[sc],(vcg,sc));cvals=[r['cgeo'] for r in brows.values()];vvals=[vcg_record(vcg,sc,h)['vcg'] for h in brows];pvals=[r['pig'] for r in brows.values()]
  classes={k:sum(r['class']==k for r in brows.values()) for k in ['muito baixa','baixa','média','alta','muito alta']};f1=sum(r['front']==1 for r in brows.values());nulls=len(ids)-len(brows)
  summary[sc]={'cells':len(ids),'eligible_cells':len(brows),'cells_without_pig':nulls,'eligible_fraction':round(len(brows)/len(ids),6),'pareto_fronts':base[sc]['fronts_total'],'front_1_cells':f1,'front_1_fraction':round(f1/len(brows),6) if brows else 0,'pig_100':summarize(pvals),'cgeo':summarize(cvals),'vcg_eligible':summarize(vvals),'cgeo_zero_cells':sum(abs(x)<1e-12 for x in cvals),'classes':classes,'normalization':base[sc]['normalization'],'unit_neff_median':round(statistics.median([r['unit_neff'] or 0 for r in raw_base[sc].values() if r['evaluable']]),4),'transition_fraction_median':round(statistics.median([r['transition_fraction'] for r in raw_base[sc].values() if r['evaluable']]),6)}
  sensitivity[sc]={
   'baseline_2_5_P95':{'eligible_cells':len(brows),'pareto_fronts':base[sc]['fronts_total'],'front_1_cells':base[sc]['front1_cells']},
   'microgrid_1_25_P95':{**compare_scenario(brows,alt_step[1.25][sc]['rows']),'eligible_cells':alt_step[1.25][sc]['eligible_cells'],'pareto_fronts':alt_step[1.25][sc]['fronts_total'],'front_1_cells':alt_step[1.25][sc]['front1_cells']},
   'microgrid_5_P95':{**compare_scenario(brows,alt_step[5.0][sc]['rows']),'eligible_cells':alt_step[5.0][sc]['eligible_cells'],'pareto_fronts':alt_step[5.0][sc]['fronts_total'],'front_1_cells':alt_step[5.0][sc]['front1_cells']},
   'normalizacao_P90':{**compare_scenario(brows,alt_pct[90][sc]['rows']),'eligible_cells':alt_pct[90][sc]['eligible_cells'],'pareto_fronts':alt_pct[90][sc]['fronts_total'],'front_1_cells':alt_pct[90][sc]['front1_cells']},
   'normalizacao_P99':{**compare_scenario(brows,alt_pct[99][sc]['rows']),'eligible_cells':alt_pct[99][sc]['eligible_cells'],'pareto_fronts':alt_pct[99][sc]['fronts_total'],'front_1_cells':alt_pct[99][sc]['front1_cells']}}
 # robustness is diagnostic, not silently forced to PASS
 warnings=[]
 for sc in SCALES:
  for nm,s in sensitivity[sc].items():
   if nm.startswith('baseline'):continue
   if s.get('spearman_cgeo') is not None and s['spearman_cgeo']<0.8:warnings.append(f'{sc} {nm}: Spearman C_geo < 0.8')
   if s.get('class_change_fraction') is not None and s['class_change_fraction']>0.25:warnings.append(f'{sc} {nm}: mudanca de classe > 25%')
 snapshot={'metadata':{'index':'PIG','version':VERSION,'cut_date':CUT_DATE,'generated_at':now_iso(),'primary_output':'pareto_front','objectives':'maximizar VCG e C_geo simultaneamente','dominance':'sem soma ponderada; empates permanecem no mesmo front','pig_100_rule':'transformacao ordinal do front para simbologia; nao e escala cardinal','complexity_formula':'C_geo = 100 × sqrt(D* × T*)','complexity_source':'Mapa geologico estadual SGB 1:1.000.000','complexity_support':'micromalha global fixa 2,5 km em LAEA','complexity_limit':'heterogeneidade litoestratigrafica cartografada; nao densidade de falhas ou complexidade estrutural total','interpretation_limit':'prioridade relativa de investigacao; nao favorabilidade mineral, jazida, recurso, reserva ou valor economico','references':['REF-002','REF-004','REF-082','REF-105','REF-115','REF-116']},'protected_input_sha256':protected,'summary':summary,'sensitivity':sensitivity,'robustness_warnings':warnings,'grids':grids}
 dump_json(repo/'docs/indices/pig_v38421_snapshot.json',snapshot);(repo/'docs/indices/pig-v38421.js').write_text('window.ITA_PIG_V38421='+json.dumps({'metadata':snapshot['metadata'],'summary':summary,'sensitivity':sensitivity,'robustness_warnings':warnings,'grids':grids},ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
 patch_catalog_files(repo,summary);patch_app(repo,summary);update_web(repo);update_bibliography(repo);write_methodology(repo,snapshot);update_changelog(repo)
 for rel,h in protected.items():
  if sha256_file(repo/rel)!=h:raise RuntimeError('arquivo cientifico protegido alterado: '+rel)
 dump_json(repo/'AUDITORIA_V38_4_21_PIG_RUNTIME.json',{'audit':'V38.4.21 PIG runtime','version':VERSION,'generated_at':now_iso(),'status':'PASS','summary':summary,'sensitivity':sensitivity,'robustness_warnings':warnings,'protected_input_sha256':protected})
 (repo/'VERSION').write_text(VERSION+'\n',encoding='utf-8',newline='\n')
 print('PIG V38.4.21 materializado',flush=True)
 for sc in SCALES:print(sc+' km2 - '+json.dumps(summary[sc],ensure_ascii=False),flush=True)
 print('Sensibilidade 1.25 / 2.5 / 5 km e P90 / P95 / P99 concluida',flush=True)
 if warnings:print('AVISOS DE ROBUSTEZ - '+json.dumps(warnings,ensure_ascii=False),flush=True)
def self_test():
 tests=[]
 def ck(n,x):tests.append((n,bool(x)))
 pts=[('a',90,80),('b',80,90),('c',70,70),('d',90,80)];fr=nondominated_fronts(pts);ck('pareto_front1',fr[0]==1 and fr[1]==1 and fr[3]==1);ck('pareto_dominated',fr[2]>1);ck('ties_same_front',fr[0]==fr[3]);ck('pig_front1_100',abs(pig100(1,5)-100)<1e-9);ck('pig_last_0',abs(pig100(5,5))<1e-9);ck('classes',class_pig(100)=='muito alta' and class_pig(0)=='muito baixa');fake={'a':{'unit_excess':0,'transition_fraction':0,'evaluable':True},'b':{'unit_excess':1,'transition_fraction':.2,'evaluable':True},'c':{'unit_excess':3,'transition_fraction':.5,'evaluable':True}};vals,n=normalize_complexity(fake,95);ck('complexity_zero_valid',vals['a']==0);ck('complexity_order',vals['c']>vals['b']);print(f'SELF TEST PIG V38.4.21 - {sum(v for _,v in tests)}/{len(tests)}');
 for n,v in tests:
  if not v:print('FAIL - '+n)
 return 0 if all(v for _,v in tests) else 1
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo');ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
 if a.self_test:return self_test()
 if not a.repo:raise SystemExit('--repo e obrigatorio')
 calculate(Path(a.repo).resolve());return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as e:print('ERRO PIG:',e,file=sys.stderr);raise
