#!/usr/bin/env python3
from pathlib import Path
import argparse, json, math, statistics, datetime, hashlib, html, sys

EXPECTED='V38.4.19-VCG-VAZIOS-CONHECIMENTO-GEOCIENTIFICO-20260815'
VERSION='V38.4.20-GATE-PIG-20260815'
SCALES=['250','500','1000']
GRIDS={
 '250':'docs/camadas/arquivos/malha_r5_250km2.geojson',
 '500':'docs/camadas/arquivos/malha_500km2.geojson',
 '1000':'docs/camadas/arquivos/malha_1000km2.geojson',
}
GEOLOGY='docs/camadas/arquivos/mapa_geologico_ms.geojson'
VCG='docs/indices/vcg_v38419_snapshot.json'
BASE_STEP_KM=2.5
SENS_STEPS_KM=[1.25,5.0]
PCTS=[90,95,99]
MIN_SUPPORT=4
MIN_PAIRS=2
R=6371007.181
LON0=math.radians(-54.5); LAT0=math.radians(-20.5)


def now_iso(): return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump_json(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def pct(vals,p):
    v=sorted(float(x) for x in vals if x is not None and math.isfinite(float(x)))
    if not v:return None
    if len(v)==1:return v[0]
    q=(len(v)-1)*p/100.0;i=int(math.floor(q));j=int(math.ceil(q))
    return v[i] if i==j else v[i]+(v[j]-v[i])*(q-i)
def rankdata(vals):
    a=sorted(enumerate(vals),key=lambda x:x[1]);r=[0.0]*len(vals);i=0
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
    lam=math.radians(lon);phi=math.radians(lat)
    den=1+math.sin(LAT0)*math.sin(phi)+math.cos(LAT0)*math.cos(phi)*math.cos(lam-LON0)
    k=math.sqrt(2/max(den,1e-15))
    return (R*k*math.cos(phi)*math.sin(lam-LON0), R*k*(math.cos(LAT0)*math.sin(phi)-math.sin(LAT0)*math.cos(phi)*math.cos(lam-LON0)))

def proj_geom(g):
    typ=g.get('type');c=g.get('coordinates')
    if typ=='Polygon': return {'type':'Polygon','coordinates':[[laea(x,y) for x,y in ring] for ring in c]}
    if typ=='MultiPolygon': return {'type':'MultiPolygon','coordinates':[[[laea(x,y) for x,y in ring] for ring in poly] for poly in c]}
    raise RuntimeError('geometria nao poligonal no suporte PIG: '+str(typ))
def rings(g):
    if g['type']=='Polygon':return [g['coordinates']]
    out=[]
    for p in g['coordinates']:out.append(p)
    return out
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
            hole=False
            for h in poly[1:]:
                if point_ring(x,y,h):hole=True;break
            if not hole:return True
    return False
def bbox_overlap(a,b):return not(a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])

def prepare_geology(fc):
    out=[]
    for i,f in enumerate(fc.get('features',[])):
        p=f.get('properties') or {};g=proj_geom(f.get('geometry') or {})
        uid=str(p.get('ID_UNIDADE_ESTRATIGRAFICA') or p.get('SIGLA') or p.get('NOME') or ('U'+str(i)))
        out.append({'uid':uid,'sigla':p.get('SIGLA'),'nome':p.get('NOME'),'geom':g,'bbox':bbox_geom(g)})
    if not out:raise RuntimeError('mapa geologico sem feicoes')
    return out

def shannon_neff(counts):
    n=sum(counts.values())
    if n<=0:return None
    h=0.0
    for c in counts.values():
        if c<=0:continue
        p=c/n;h-=p*math.log(p)
    return math.exp(h)

def build_bins(items,bin_m=50000.0):
    bins={}
    for idx,z in enumerate(items):
        b=z['bbox'];ix0=math.floor(b[0]/bin_m);ix1=math.floor(b[2]/bin_m);iy0=math.floor(b[1]/bin_m);iy1=math.floor(b[3]/bin_m)
        for ix in range(ix0,ix1+1):
            for iy in range(iy0,iy1+1):bins.setdefault((ix,iy),[]).append(idx)
    return bins

def candidates_for(x,y,bins,bin_m=50000.0):return bins.get((math.floor(x/bin_m),math.floor(y/bin_m)),[])

def prepare_cells(repo):
    out={}
    for sc in SCALES:
        arr=[]
        for f in load_json(repo/GRIDS[sc]).get('features',[]):
            hid=str((f.get('properties') or {}).get('hex_id') or '')
            if not hid:raise RuntimeError('hex sem hex_id')
            g=proj_geom(f['geometry']);arr.append({'hid':hid,'geom':g,'bbox':bbox_geom(g)})
        out[sc]={'cells':arr,'bins':build_bins(arr,50000.0)}
    return out

def state_bbox(cells250):
    bs=[z['bbox'] for z in cells250]
    return min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs)

def classify_microgrid(geology,bbox,step_km):
    step=step_km*1000.0;gbins=build_bins(geology,50000.0)
    x0=math.floor(bbox[0]/step)*step;y0=math.floor(bbox[1]/step)*step
    x1=math.ceil(bbox[2]/step)*step;y1=math.ceil(bbox[3]/step)*step
    pts={};iy=0;y=y0+step/2
    while y<=y1:
        ix=0;x=x0+step/2
        while x<=x1:
            hits=[]
            for gi in candidates_for(x,y,gbins,50000.0):
                z=geology[gi];b=z['bbox']
                if b[0]<=x<=b[2] and b[1]<=y<=b[3] and point_geom(x,y,z['geom']):hits.append(z['uid'])
            if hits:pts[(ix,iy)]={'x':x,'y':y,'uid':hits[0],'overlap':len(hits)>1}
            ix+=1;x+=step
        iy+=1;y+=step
    return pts

def assign_points_to_cells(points,cellpack):
    assigned={z['hid']:{} for z in cellpack['cells']}
    cells=cellpack['cells'];bins=cellpack['bins']
    for key,p in points.items():
        for ci in candidates_for(p['x'],p['y'],bins,50000.0):
            z=cells[ci];b=z['bbox']
            if b[0]<=p['x']<=b[2] and b[1]<=p['y']<=b[3] and point_geom(p['x'],p['y'],z['geom']):
                assigned[z['hid']][key]=p;break
    return assigned

def raw_from_assignment(assigned):
    rows={}
    for hid,pts in assigned.items():
        counts={};ov=0
        for p in pts.values():counts[p['uid']]=counts.get(p['uid'],0)+1;ov+=int(p['overlap'])
        pairs=trans=0
        keys=set(pts)
        for ix,iy in keys:
            u=pts[(ix,iy)]['uid']
            for nb in ((ix+1,iy),(ix,iy+1)):
                if nb in keys:
                    pairs+=1;trans+=int(u!=pts[nb]['uid'])
        ne=shannon_neff(counts)
        rows[hid]={'n_support':len(pts),'overlap_fraction':ov/len(pts) if pts else 0.0,'n_units':len(counts),'unit_neff':ne,
                   'unit_excess':max(0.0,(ne or 0)-1.0),'transition_fraction':trans/pairs if pairs else 0.0,'transition_pairs':pairs,
                   'evaluable':len(pts)>=MIN_SUPPORT and pairs>=MIN_PAIRS}
    return rows

def normalize_complexity(rows,percentile=95):
    ev=[r for r in rows.values() if r['evaluable']]
    dpos=[r['unit_excess'] for r in ev if r['unit_excess']>0];tpos=[r['transition_fraction'] for r in ev if r['transition_fraction']>0]
    dp=pct(dpos,percentile) or 1.0;tp=pct(tpos,percentile) or 1.0
    vals={}
    for hid,r in rows.items():
        if not r['evaluable']:vals[hid]=None;continue
        d=min(1.0,r['unit_excess']/dp) if dp>0 else 0.0;t=min(1.0,r['transition_fraction']/tp) if tp>0 else 0.0
        vals[hid]=100*math.sqrt(max(0.0,d*t))
    return vals,{'D_excess_P':dp,'T_transicao_P':tp,'percentile':percentile}

def prepare_raw(repo,step_km):
    geology=prepare_geology(load_json(repo/GEOLOGY));cells=prepare_cells(repo);bb=state_bbox(cells['250']['cells'])
    points=classify_microgrid(geology,bb,step_km);out={}
    for sc in SCALES:out[sc]=raw_from_assignment(assign_points_to_cells(points,cells[sc]))
    return out

def diagnose_raw(repo,raw,percentile=95,step_km=BASE_STEP_KM):
    vcg=load_json(repo/VCG);result={}
    for sc in SCALES:
        vals,norm=normalize_complexity(raw[sc],percentile);points=[];vcgs=[];comps=[]
        for hid,c in vals.items():
            v=vcg_for(vcg,sc,hid)
            if v is not None and c is not None:points.append((hid,float(v),float(c)));vcgs.append(float(v));comps.append(float(c))
        if not points:raise RuntimeError('nenhuma celula elegivel PIG na escala '+sc)
        fronts=nondominated_fronts(points);fmax=max(fronts);front_counts={str(k):fronts.count(k) for k in range(1,fmax+1)}
        supports=[r['n_support'] for r in raw[sc].values()];ovs=[r['overlap_fraction'] for r in raw[sc].values()]
        ne=[r['unit_neff'] or 0 for r in raw[sc].values() if r['evaluable']];tr=[r['transition_fraction'] for r in raw[sc].values() if r['evaluable']]
        result[sc]={'cells':len(raw[sc]),'microgrid_km':step_km,'eligible_cells':len(points),'eligible_fraction':round(len(points)/len(raw[sc]),6),'normalization':norm,
                    'complexity':summarize(comps),'vcg_eligible':summarize(vcgs),'pareto_fronts':fmax,'front_1_cells':fronts.count(1),'front_counts':front_counts,
                    'support_min':min(supports),'support_median':statistics.median(supports),'overlap_fraction_max':round(max(ovs),6),
                    'unit_neff_median':round(statistics.median(ne),4) if ne else None,'transition_fraction_median':round(statistics.median(tr),6) if tr else None,
                    '_fronts':fronts,'_ids':[p[0] for p in points],'_complexity_values':{p[0]:p[2] for p in points}}
    return result

def vcg_for(vcg,scale,hid):
    r=(vcg.get('grids') or {}).get(scale,{}).get(hid)
    if isinstance(r,(list,tuple)) and r:
        try:return float(r[0])
        except:return None
    if isinstance(r,dict):
        for k in ('vcg_100','vcg','score'):
            if k in r:
                try:return float(r[k])
                except:return None
    return None

def nondominated_fronts(points):
    # 2D non-dominated sorting. Higher is better in both objectives.
    order=sorted(range(len(points)),key=lambda i:(-points[i][1],-points[i][2],points[i][0]))
    front=[None]*len(points)
    done=[]
    for i in order:
        _,vi,ci=points[i];best=0
        for j in done:
            _,vj,cj=points[j]
            if vj>=vi and cj>=ci and (vj>vi or cj>ci):
                if front[j]>best:best=front[j]
        front[i]=best+1
        done.append(i)
    return front

def summarize(vals):
    return {'min':round(min(vals),4),'p05':round(pct(vals,5),4),'median':round(statistics.median(vals),4),'mean':round(statistics.fmean(vals),4),'p95':round(pct(vals,95),4),'max':round(max(vals),4)}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo');ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:
        pts=[('a',90,80),('b',80,90),('c',70,70),('d',90,80)]
        fr=nondominated_fronts(pts)
        assert fr[0]==1 and fr[1]==1 and fr[3]==1 and fr[2]>1
        fake={'a':{'unit_excess':0,'transition_fraction':0,'evaluable':True},'b':{'unit_excess':1,'transition_fraction':.2,'evaluable':True},'c':{'unit_excess':3,'transition_fraction':.5,'evaluable':True}}
        vals,n=normalize_complexity(fake,95);assert vals['a']==0 and vals['c']>vals['b']
        print('SELF-TEST GATE PIG V38.4.20 · PASS');return 0
    if not a.repo:raise RuntimeError('--repo obrigatorio')
    repo=Path(a.repo).resolve();cur=(repo/'VERSION').read_text(encoding='utf-8-sig').strip()
    if cur!=EXPECTED:raise RuntimeError(f'base incorreta: {cur}')
    final_vcg=load_json(repo/'AUDITORIA_V38_4_19_VCG_FINAL.json')
    if final_vcg.get('status')!='PASS':raise RuntimeError('auditoria final VCG V38.4.19 nao esta PASS')
    if not (repo/GEOLOGY).exists():raise RuntimeError('mapa geologico estadual ausente')
    if not (repo/VCG).exists():raise RuntimeError('snapshot VCG ausente')

    geo_fc=load_json(repo/GEOLOGY)
    geo_features=geo_fc.get('features',[])
    if not geo_features:raise RuntimeError('mapa geologico sem feicoes')
    req=['ID_UNIDADE_ESTRATIGRAFICA','SIGLA','NOME']
    field_counts={k:sum(1 for f in geo_features if (f.get('properties') or {}).get(k) not in (None,'')) for k in req}
    units=len(set(str((f.get('properties') or {}).get('ID_UNIDADE_ESTRATIGRAFICA') or (f.get('properties') or {}).get('SIGLA') or (f.get('properties') or {}).get('NOME')) for f in geo_features))
    vcg=load_json(repo/VCG)
    public_diag={}
    for sc in SCALES:
        grid=load_json(repo/GRIDS[sc]);ids=[str((f.get('properties') or {}).get('hex_id') or '') for f in grid.get('features',[])]
        vg=(vcg.get('grids') or {}).get(sc,{})
        n_vcg=sum(1 for hid in ids if vcg_for(vcg,sc,hid) is not None)
        public_diag[sc]={'cells':len(ids),'vcg_numeric_cells':n_vcg,'vcg_complete_for_grid':n_vcg==len(ids)}
    sens={sc:{'status':'OBRIGATORIA_NA_V38.4.21','microgrids_km':[1.25,2.5,5.0],'normalization_percentiles':[90,95,99]} for sc in SCALES}

    policy={
      'policy':'V38.4.20 - Gate metodologico PIG - Prioridade de Investigacao Geocientifica',
      'version':VERSION,'generated_at':now_iso(),'status':'PASS','scales_km2':SCALES,
      'role':'PIG ordena prioridade relativa de investigacao geocientifica. Nao representa favorabilidade mineral, probabilidade de jazida, recurso, reserva, risco ou valor economico.',
      'inputs':{'knowledge_gap':'VCG V38.4.19','geological_complexity':'Mapa geologico estadual SGB 1:1.000.000, atributos e geometria das unidades litoestratigraficas'},
      'independence':'A complexidade usa somente heterogeneidade cartografica da geologia de base. Nao usa IOD, ICP, IGC, IGQ, IGF, ICS, IDE, ICG, VCG, IPG, PAG-ETR ou ocorrencias minerais para construir o eixo geologico.',
      'complexity_baseline':{
        'name':'C_geo - complexidade litoestratigrafica cartografica de base',
        'support':'micromalha global fixa de 2,5 km em projecao Lambert azimutal equal-area; apenas centros contidos na geometria efetiva de cada celula participam',
        'D_raw':'N_eff - 1, com N_eff = exp(H) e H de Shannon sobre proporcoes de suporte das unidades litoestratigraficas classificadas.',
        'T_raw':'fracao de pares ortogonais adjacentes de microcelulas classificadas, dentro da mesma celula analitica, que mudam de unidade litoestratigrafica; proxy de compartimentacao cartografica, nao densidade de falhas.',
        'normalization':'D* = min(1,D_raw/P95(D_raw>0)); T* = min(1,T_raw/P95(T_raw>0)), recalculados independentemente por escala.',
        'formula':'C_geo = 100 * sqrt(D* * T*).',
        'edge_rule':'somente centros da micromalha dentro da geometria efetiva recortada participam. Exige no minimo 4 suportes e 2 pares adjacentes; suporte insuficiente gera C_geo null, nunca zero.',
        'limitations':'C_geo depende da generalizacao do mapa 1:1.000.000 e mede complexidade litoestratigrafica cartografada. Nao equivale a complexidade estrutural total, densidade de falhas, deformacao, favorabilidade ou potencial mineral.'
      },
      'pareto':{
        'objectives':'maximizar simultaneamente VCG e C_geo.',
        'dominance':'A domina B se VCG_A >= VCG_B e C_geo_A >= C_geo_B e pelo menos uma desigualdade for estrita.',
        'fronts':'Front 1 contem as celulas nao dominadas. Removido o front 1, repete-se o procedimento para front 2 e sucessivos.',
        'ties':'Celulas com o mesmo par VCG/C_geo permanecem empatadas no mesmo front. Nao se aplica soma ponderada nem desempate arbitrario.',
        'primary_output':'pareto_front e a medida cientifica primaria do PIG.',
        'display_100':'PIG_100 = 100 * (1 - (front-1)/(Fmax-1)) quando Fmax>1; e apenas transformacao ordinal para simbologia. Distancias entre valores nao sao interpretadas como intervalares.',
        'classes':'muito alta >=80; alta >=60; media >=40; baixa >=20; muito baixa <20, aplicadas somente ao PIG_100 ordinal.',
        'eligibility':'VCG numerico e C_geo calculavel. C_geo=0 continua elegivel e nao e convertido em null.'
      },
      'sensitivity_required':{'support_lattices':['1.25 km','2.5 km baseline','5 km'],'normalization_percentiles':['P90','P95 baseline','P99'],'checks':['Spearman de C_geo','numero de fronts','tamanho do front 1','mudancas de classe no PIG final']},
      'cartography':{'low_to_high':'prioridade baixa clara e prioridade alta escura','border':'#4a4a4a','null':'transparente','front_1':'deve permanecer identificavel na ficha mesmo quando PIG_100 for usado para legenda'},
      'required_properties':['pig_100','pareto_front','pareto_fronts_total','vcg_100','complexidade_geo_100','unit_neff','transition_fraction','classe_pig','regra_pareto','fonte_complexidade','limitacao_complexidade'],
      'references':['REF-002','REF-004','REF-082','REF-105','REF-115','REF-116'],
      'diagnostic':public_diag,'geology_source_diagnostic':{'features':len(geo_features),'unique_units':units,'field_counts':field_counts},'sensitivity_diagnostic':sens,
      'next_step':'V38.4.21 - materializacao PIG 250 / 500 / 1000 km2, seguida de auditoria ZERO final da familia de indices.'
    }
    dump_json(repo/'docs/indices/politica-pig-v38420.json',policy)
    runtime={'audit':'V38.4.20 gate PIG runtime','status':'PASS','version':VERSION,'generated_at':now_iso(),'diagnostic':public_diag,'geology_source':{'features':len(geo_features),'unique_units':units,'field_counts':field_counts},'sensitivity':sens,'source_sha256':{GEOLOGY:sha256(repo/GEOLOGY),VCG:sha256(repo/VCG),**{GRIDS[s]:sha256(repo/GRIDS[s]) for s in SCALES}}}
    dump_json(repo/'AUDITORIA_V38_4_20_GATE_PIG_RUNTIME.json',runtime)
    html_doc=f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>PIG · Gate metodológico V38.4.20</title><style>body{{font-family:system-ui;max-width:980px;margin:32px auto;padding:0 18px;line-height:1.55;color:#24343f}}code{{background:#eef2f4;padding:2px 5px;border-radius:5px}}.box{{background:#f5f8fa;border-left:4px solid #315d7d;padding:12px 14px;margin:14px 0}}</style><h1>PIG · Prioridade de Investigação Geocientífica</h1><p><b>Gate metodológico V38.4.20</b></p><div class="box"><b>Princípio</b><br>PIG ordena prioridades relativas de investigação. Não mede favorabilidade mineral, probabilidade de jazida, recurso, reserva ou valor econômico.</div><h2>Dois objetivos independentes</h2><p><b>VCG</b> representa vazios do conhecimento documentado. <b>C_geo</b> representa complexidade litoestratigráfica cartográfica da geologia de base.</p><h2>Complexidade geológica de base</h2><p><code>D_raw = N_eff - 1</code>, com <code>N_eff = exp(H)</code> para diversidade areal das unidades. <code>T_raw</code> é a fração de transições entre unidades em pares adjacentes de uma micromalha global fixa de 2,5 km. Ambos são normalizados por P95 dentro de cada escala.</p><p><code>C_geo = 100 × sqrt(D* × T*)</code></p><p>É uma medida de heterogeneidade litoestratigráfica cartografada a 1:1.000.000. Não é densidade de falhas nem complexidade estrutural total.</p><h2>Dominância de Pareto</h2><p>Maximizam-se VCG e C_geo simultaneamente. Uma célula domina outra somente se não for pior em nenhum dos dois objetivos e for melhor em pelo menos um. Não existe soma ponderada. Empates permanecem empates.</p><p>O número do front de Pareto é a saída científica primária. Um PIG de 0 a 100 será apenas transformação ordinal do front para visualização, sem interpretação de distância intervalar.</p><h2>Sensibilidade obrigatória</h2><p>Micromalha 1,25 km, 2,5 km e 5 km. Normalização P90, P95 e P99. A versão final deverá auditar correlação, mudanças de classe, número de fronts e tamanho do primeiro front.</p><h2>Referências</h2><p>REF-002, REF-004 e REF-082 para o mapa geológico estadual. REF-105 para sensibilidade. REF-115 para o protocolo multiescalar. REF-116 para ordenação por dominância de Pareto.</p></html>"""
    dp=repo/'docs/documentos/politica-gate-pig-v38420.html';dp.parent.mkdir(parents=True,exist_ok=True);dp.write_text(html_doc,encoding='utf-8',newline='\n')
    idx=repo/'docs/documentos/index.html'
    if idx.exists():
        t=idx.read_text(encoding='utf-8-sig')
        if 'politica-gate-pig-v38420.html' not in t:t=t.replace('</body>','<p><a href="./politica-gate-pig-v38420.html">PIG · gate metodológico V38.4.20</a></p></body>',1)
        idx.write_text(t,encoding='utf-8',newline='\n')
    ch=repo/'CHANGELOG.md'
    old=ch.read_text(encoding='utf-8-sig') if ch.exists() else ''
    entry="""\n## V38.4.20 · Gate metodológico PIG · 2026-08-15\n\n- Congelada complexidade litoestratigráfica cartográfica independente a partir do mapa geológico SGB 1:1.000.000.\n- Congelada ordenação por fronts de dominância de Pareto entre VCG e C_geo, sem soma ponderada.\n- Empates preservados. PIG_100 será transformação ordinal de front apenas para simbologia.\n- Sensibilidade obrigatória de suporte 13/17/21 e normalização P90/P95/P99.\n- PIG ainda não materializado nesta versão.\n"""
    if 'V38.4.20 · Gate metodológico PIG' not in old:ch.write_text(entry+old,encoding='utf-8',newline='\n')
    (repo/'VERSION').write_text(VERSION+'\n',encoding='utf-8',newline='\n')
    print('GATE PIG V38.4.20 · PASS')
    for sc in SCALES:
        d=public_diag[sc];print(f"{sc} km2 · VCG numerico {d['vcg_numeric_cells']}/{d['cells']} · base pronta para materializacao Pareto")
    print('PIG ainda NAO calculado. Proximo passo V38.4.21.')
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        print('ERRO GATE PIG:',e,file=sys.stderr);raise
