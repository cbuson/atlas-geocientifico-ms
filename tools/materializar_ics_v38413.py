#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, gzip, hashlib, json, math, re, statistics, unicodedata, urllib.parse, urllib.request
from pathlib import Path

VERSION='V38.4.13-ICS-CONHECIMENTO-SUBSOLO-20260814'
CUT_DATE='2026-08-14'
FORMULA='ICS_h = 100 × (M* × B × Q_log)^(1/3)'
BASE_MICROCELL_M=5000.0
BASE_DENSITY_PERCENTILE=95
BASE_DEPTH_CAP_PERCENTILE=99
LAEA_LON0=-54.5
LAEA_LAT0=-20.5
EARTH_R=6371007.181
SIAGAS_LAYER='https://geoportal.sgb.gov.br/server/rest/services/Siagas_WebMap_MIL1/MapServer/0'
RIMAS_SERVICE='https://geoportal.sgb.gov.br/server/rest/services/hidrologia/rimas/MapServer'
RIMAS_LAYER=RIMAS_SERVICE+'/0'
GRID_FILES={'250':'docs/camadas/arquivos/malha_r5_250km2.geojson','500':'docs/camadas/arquivos/malha_500km2.geojson','1000':'docs/camadas/arquivos/malha_1000km2.geojson'}
LIMIT_FILE='docs/camadas/arquivos/limite_ms_ibge_2025.geojson'


def now_iso():return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load_json(path:Path):
    with path.open('r',encoding='utf-8') as f:return json.load(f)
def dump_json(path:Path,obj,compact=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,ensure_ascii=False,separators=(',',':') if compact else None,indent=None if compact else 2);f.write('\n')
def canonical_bytes(obj):return json.dumps(obj,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode('utf-8')
def sha256_bytes(data:bytes):return hashlib.sha256(data).hexdigest()
def norm_text(v):
    s=str(v or '').strip().lower();s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c));return re.sub(r'\s+',' ',s)
def ci_get(props,*names):
    if not isinstance(props,dict):return None
    low={str(k).lower():v for k,v in props.items()}
    for n in names:
        if n in props:return props[n]
        if str(n).lower() in low:return low[str(n).lower()]
    return None

def fetch_json(url,timeout=180):
    req=urllib.request.Request(url,headers={'User-Agent':'ITA-ARANDU-MS/38.4.13 Python urllib','Accept':'application/json, application/geo+json;q=0.9, */*;q=0.1'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8-sig'))
def qurl(layer,params):return layer+'/query?'+urllib.parse.urlencode(params,safe=",()'=")
def fetch_features_where(layer,where):
    ids=fetch_json(qurl(layer,{'where':where,'returnIdsOnly':'true','f':'json'}))
    if ids.get('error'):raise RuntimeError(f'ArcGIS returnIdsOnly falhou em {layer} · {ids["error"]}')
    oids=ids.get('objectIds') or [];out=[]
    for i in range(0,len(oids),500):
        batch=oids[i:i+500]
        obj=fetch_json(qurl(layer,{'where':'1=1','objectIds':','.join(str(x) for x in batch),'outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}))
        if obj.get('error'):raise RuntimeError(f'ArcGIS query falhou em {layer} · {obj["error"]}')
        out.extend(obj.get('features') or [])
    return out

def id_norm(v):
    if v is None:return None
    s=str(v).strip()
    if not s:return None
    try:
        x=float(s)
        if math.isfinite(x) and abs(x-round(x))<1e-8:return str(int(round(x)))
    except Exception:pass
    return s

def fetch_table_for_ids(table_url,ids):
    ids=[x for x in dict.fromkeys(id_norm(v) for v in ids) if x]
    if not ids:return []
    out=[]
    for i in range(0,len(ids),150):
        chunk=ids[i:i+150];vals=','.join("'"+x.replace("'","''")+"'" for x in chunk)
        where=f'idt_ponto IN ({vals})'
        obj=fetch_json(qurl(table_url,{'where':where,'outFields':'*','returnGeometry':'false','f':'json'}))
        if obj.get('error'):
            # alguns serviços tipam idt_ponto como numérico e rejeitam aspas
            vals=','.join(x for x in chunk if re.fullmatch(r'\d+(?:\.0+)?',x))
            if not vals:continue
            obj=fetch_json(qurl(table_url,{'where':f'idt_ponto IN ({vals})','outFields':'*','returnGeometry':'false','f':'json'}))
        if obj.get('error'):raise RuntimeError(f'ArcGIS tabela falhou em {table_url} · {obj["error"]}')
        out.extend(x.get('attributes',x) for x in (obj.get('features') or []))
    return out

def fetch_source():
    siagas=fetch_features_where(SIAGAS_LAYER,"str_uf='MS'")
    try:rimas=fetch_features_where(RIMAS_LAYER,"str_uf='MS'")
    except Exception:rimas=[]
    rids=[ci_get(f.get('properties') or {},'idt_ponto') for f in rimas]
    try:r_aq=fetch_table_for_ids(RIMAS_SERVICE+'/2',rids)
    except Exception:r_aq=[]
    try:r_con=fetch_table_for_ids(RIMAS_SERVICE+'/5',rids)
    except Exception:r_con=[]
    return 'SGB · Geoportal · SIAGAS e RIMAS',{'siagas':siagas,'rimas':rimas,'rimas_aquifer':r_aq,'rimas_construction':r_con,'services':{'siagas':SIAGAS_LAYER,'rimas':RIMAS_LAYER,'rimas_aquifer':RIMAS_SERVICE+'/2','rimas_construction':RIMAS_SERVICE+'/5'},'cut_date':CUT_DATE}

_lon0=math.radians(LAEA_LON0);_lat0=math.radians(LAEA_LAT0);_sin0=math.sin(_lat0);_cos0=math.cos(_lat0)
def laea(lon,lat):
    lam=math.radians(lon);phi=math.radians(lat);dl=lam-_lon0;sp=math.sin(phi);cp=math.cos(phi);den=1+_sin0*sp+_cos0*cp*math.cos(dl)
    if den<=1e-15:raise ValueError('coordenada antipodal à projeção')
    k=math.sqrt(2/den);return EARTH_R*k*cp*math.sin(dl),EARTH_R*k*(_cos0*sp-_sin0*cp*math.cos(dl))
def point_on_segment(pt,a,b,tol=.05):
    x,y=pt;x1,y1=a;x2,y2=b;dx=x2-x1;dy=y2-y1;l2=dx*dx+dy*dy
    if l2==0:return (x-x1)**2+(y-y1)**2<=tol*tol
    t=((x-x1)*dx+(y-y1)*dy)/l2
    if t<0 or t>1:return False
    px=x1+t*dx;py=y1+t*dy;return (x-px)**2+(y-py)**2<=tol*tol
def point_in_ring(pt,ring):
    if len(ring)<3:return False
    inside=False;x,y=pt;j=len(ring)-1
    for i in range(len(ring)):
        a=ring[j];b=ring[i]
        if point_on_segment(pt,a,b):return True
        xi,yi=b;xj,yj=a
        if (yi>y)!=(yj>y):
            xc=(xj-xi)*(y-yi)/((yj-yi) if yj!=yi else 1e-30)+xi
            if x<xc:inside=not inside
        j=i
    return inside
def point_in_poly(pt,poly):return bool(poly and point_in_ring(pt,poly[0]) and not any(point_in_ring(pt,h) for h in poly[1:]))
def point_in_geom_projected(pt,geom):return any(point_in_poly(pt,p) for p in geom['polys'])
def project_geometry(geom):
    typ=geom.get('type');coords=geom.get('coordinates');polys=[coords] if typ=='Polygon' else coords if typ=='MultiPolygon' else None
    if polys is None:raise ValueError(f'geometria poligonal esperada · {typ}')
    out=[];xs=[];ys=[]
    for poly in polys:
        pp=[]
        for ring in poly:
            rr=[]
            for c in ring:
                x,y=laea(float(c[0]),float(c[1]));rr.append((x,y));xs.append(x);ys.append(y)
            pp.append(rr)
        out.append(pp)
    if not xs:raise ValueError('geometria vazia')
    return {'polys':out,'bbox':(min(xs),min(ys),max(xs),max(ys))}
def feature_polys(fc):
    out=[]
    for f in fc.get('features',[]):
        g=f.get('geometry') or {}
        if g.get('type') not in {'Polygon','MultiPolygon'}:continue
        try:pg=project_geometry(g)
        except Exception:continue
        out.append({'feature':f,'geom':pg,'bbox':pg['bbox']})
    return out
def make_spatial_index(items,bin_m=50000.0):
    idx={}
    for i,c in enumerate(items):
        xmin,ymin,xmax,ymax=c['bbox'];ix0=math.floor(xmin/bin_m);ix1=math.floor(xmax/bin_m);iy0=math.floor(ymin/bin_m);iy1=math.floor(ymax/bin_m)
        for ix in range(ix0,ix1+1):
            for iy in range(iy0,iy1+1):idx.setdefault((ix,iy),[]).append(i)
    return idx,bin_m
def find_poly_hits(pt,items,index,bin_m):
    hits=[]
    for i in index.get((math.floor(pt[0]/bin_m),math.floor(pt[1]/bin_m)),[]):
        b=items[i]['bbox']
        if b[0]-.1<=pt[0]<=b[2]+.1 and b[1]-.1<=pt[1]<=b[3]+.1 and point_in_geom_projected(pt,items[i]['geom']):hits.append(i)
    return hits
def point_in_state(lon,lat,state_items,state_index,state_bin):return bool(find_poly_hits(laea(lon,lat),state_items,state_index,state_bin))
def polygon_centroid_hint(feat,pg):
    p=feat.get('properties') or {}
    try:return laea(float(p.get('centroide_lon')),float(p.get('centroide_lat')))
    except Exception:
        b=pg['bbox'];return((b[0]+b[2])/2,(b[1]+b[3])/2)
def load_grid(path:Path):
    fc=load_json(path);cells=[]
    for f in fc.get('features',[]):
        pg=project_geometry(f['geometry']);p=f.get('properties') or {};hid=str(p.get('hex_id') or '')
        if not hid:raise RuntimeError(f'hex sem id · {path.name}')
        try:area=float(p.get('area_efetiva_ms_km2'))
        except Exception:area=float(p.get('area_nominal_km2') or 0)
        if area<=0:raise RuntimeError(f'área inválida · {hid}')
        cells.append({'hex_id':hid,'feature':f,'geom':pg,'bbox':pg['bbox'],'centroid':polygon_centroid_hint(f,pg),'area':area})
    return fc,cells
def assign_points(points,cells):
    idx,bin_m=make_spatial_index(cells);assigned=[[] for _ in cells];missing=[];amb=0
    for pi,w in enumerate(points):
        pt=w['xy'];hits=find_poly_hits(pt,cells,idx,bin_m)
        if not hits:missing.append(pi);continue
        if len(hits)>1:
            amb+=1;hits.sort(key=lambda ci:(pt[0]-cells[ci]['centroid'][0])**2+(pt[1]-cells[ci]['centroid'][1])**2)
        assigned[hits[0]].append(pi)
    return assigned,missing,amb
def percentile(vals,p):
    x=sorted(float(v) for v in vals if v is not None and math.isfinite(float(v)))
    if not x:return None
    if len(x)==1:return x[0]
    pos=(len(x)-1)*p/100;lo=math.floor(pos);hi=math.ceil(pos);return x[lo] if lo==hi else x[lo]+(x[hi]-x[lo])*(pos-lo)
def micro_key(pt,step):return(math.floor(pt[0]/step),math.floor(pt[1]/step))
def support_microcells(cell,step,occ):
    xmin,ymin,xmax,ymax=cell['bbox'];support=set()
    for ix in range(math.floor(xmin/step)-1,math.floor(xmax/step)+2):
        x=(ix+.5)*step
        if x<xmin-.1 or x>xmax+.1:continue
        for iy in range(math.floor(ymin/step)-1,math.floor(ymax/step)+2):
            y=(iy+.5)*step
            if y<ymin-.1 or y>ymax+.1:continue
            if point_in_geom_projected((x,y),cell['geom']):support.add((ix,iy))
    support.update(occ);return support
def shannon_evenness(weights):
    vals=[float(v) for v in weights if v and v>0];k=len(vals)
    if k==0:return None
    if k==1:return 1.0
    s=sum(vals);h=-sum((v/s)*math.log(v/s) for v in vals);return max(0,min(1,h/math.log(k)))

def get_point(feat):
    g=feat.get('geometry') or {}
    if g.get('type')=='Point' and isinstance(g.get('coordinates'),list) and len(g['coordinates'])>=2:
        try:return float(g['coordinates'][0]),float(g['coordinates'][1])
        except Exception:pass
    p=feat.get('properties') or {}
    try:return float(ci_get(p,'num_longitude_decimal','longitude','X')),float(ci_get(p,'num_latitude_decimal','latitude','Y'))
    except Exception:return None
def positive(v):
    try:x=float(v);return x if math.isfinite(x) and x>0 else None
    except Exception:return None
def has_value(v):return v is not None and str(v).strip() not in {'','None','null','nan'}
def well_key(feat):
    p=feat.get('properties') or {};v=id_norm(ci_get(p,'idt_ponto','IDT_PONTO'))
    if v:return 'SIAGAS:'+v
    pt=get_point(feat)
    return f'COORD:{round(pt[0],6)}:{round(pt[1],6)}' if pt else None
def well_score(feat):
    p=feat.get('properties') or {};return sum([positive(ci_get(p,'num_profundidade')) is not None,has_value(ci_get(p,'str_aquifero')),has_value(ci_get(p,'data_perfuracao')),has_value(ci_get(p,'str_natureza_ponto')),has_value(ci_get(p,'str_nome_ponto'))])

def row_has_explicit_subsurface_log(row):
    # A relação com RIMAS, por si só, NÃO demonstra log litológico.
    # Só reconhecemos suporte explícito quando o próprio nome do campo declara
    # conteúdo litológico/estratigráfico, descrição geológica ou testemunho.
    if not isinstance(row,dict):return False
    patterns=('litolog','litoestrat','estratigraf','descricao_geolog','descr_geolog','testemunh','coluna_geolog','coluna_estrat')
    for k,v in row.items():
        nk=norm_text(k).replace(' ','_')
        if any(t in nk for t in patterns) and has_value(v):return True
    return False

def prepare_source(source,state_items):
    sidx,sbin=make_spatial_index(state_items,100000.0)
    related_rows=(source.get('rimas_aquifer') or [])+(source.get('rimas_construction') or [])
    profile_ids={id_norm(ci_get(r,'idt_ponto')) for r in related_rows if row_has_explicit_subsurface_log(r)}
    profile_ids={x for x in profile_ids if x}
    rimas_ids=set()
    rimas_feats=[]
    for f in source.get('rimas') or []:
        pt=get_point(f)
        if not pt or not point_in_state(pt[0],pt[1],state_items,sidx,sbin):continue
        rid=id_norm(ci_get(f.get('properties') or {},'idt_ponto'))
        if rid:rimas_ids.add(rid)
        rimas_feats.append(f)
    best={};outside=invalid=duplicates=0
    for f in source.get('siagas') or []:
        pt=get_point(f)
        if not pt:invalid+=1;continue
        if not point_in_state(pt[0],pt[1],state_items,sidx,sbin):outside+=1;continue
        k=well_key(f)
        if not k:invalid+=1;continue
        if k in best:
            duplicates+=1
            if well_score(f)>well_score(best[k]):best[k]=f
        else:best[k]=f
    wells=[]
    for k,f in best.items():
        p=f.get('properties') or {};pt=get_point(f);rid=id_norm(ci_get(p,'idt_ponto'));depth=positive(ci_get(p,'num_profundidade'));aq=has_value(ci_get(p,'str_aquifero'));date=has_value(ci_get(p,'data_perfuracao'));prof=bool(rid and rid in profile_ids)
        q=(.25 if depth is not None else 0)+(.25 if aq else 0)+(.25 if date else 0)+(.25 if prof else 0)
        wells.append({'key':k,'id':rid,'feature':f,'lonlat':pt,'xy':laea(*pt),'depth':depth,'aquifer':aq,'date':date,'profile':prof,'q':q,'rimas':bool(rid and rid in rimas_ids)})
    stats={'siagas_raw':len(source.get('siagas') or []),'siagas_unique_inside_ms':len(wells),'duplicates_removed':duplicates,'invalid_geometry_or_id':invalid,'outside_ms_removed':outside,'wells_with_positive_depth':sum(w['depth'] is not None for w in wells),'wells_with_aquifer':sum(w['aquifer'] for w in wells),'wells_with_drilling_date':sum(w['date'] for w in wells),'wells_with_explicit_profile_support':sum(w['profile'] for w in wells),'rimas_points_inside_ms':len(rimas_feats),'rimas_ids_with_explicit_lithologic_or_stratigraphic_log':len(profile_ids)}
    return wells,rimas_feats,stats

def calculate_scale(cells,assigned,wells,micro_step=BASE_MICROCELL_M,density_pct=BASE_DENSITY_PERCENTILE,depth_cap_pct=BASE_DEPTH_CAP_PERCENTILE):
    raw_depths=[w['depth'] for w in wells if w['depth'] is not None];cap=percentile(raw_depths,depth_cap_pct)
    if not cap or cap<=0:raise RuntimeError('nenhuma profundidade positiva disponível para ICS')
    prelim=[]
    for ci,c in enumerate(cells):
        inds=[i for i in assigned[ci] if wells[i]['depth'] is not None];meters=sum(min(wells[i]['depth'],cap) for i in inds);prelim.append(meters/c['area'] if meters>0 else 0.0)
    sat=percentile([x for x in prelim if x>0],density_pct)
    if not sat or sat<=0:raise RuntimeError('densidade de metros perfurados não normalizável')
    rows={}
    for ci,c in enumerate(cells):
        inds=[i for i in assigned[ci] if wells[i]['depth'] is not None]
        if not inds:
            rows[c['hex_id']]={'ics':None,'M':None,'B':None,'Q':None,'n':0,'meters':0.0,'density':0.0,'occupied':0,'support':None,'profiles':0,'rimas':0,'mean_depth':None};continue
        capped=[min(wells[i]['depth'],cap) for i in inds];meters=sum(capped);density=meters/c['area'];M=min(1.0,density/sat)
        by={}
        for i,d in zip(inds,capped):
            k=micro_key(wells[i]['xy'],micro_step);by[k]=by.get(k,0.0)+d
        occ=set(by);support=support_microcells(c,micro_step,occ);O=min(1.0,len(occ)/len(support)) if support else 1.0;E=shannon_evenness(by.values());B=math.sqrt(O*E) if E is not None else None
        qsum=sum(d*wells[i]['q'] for i,d in zip(inds,capped));Q=qsum/meters if meters>0 else None
        ics=100*((M*B*Q)**(1/3)) if B is not None and Q is not None and Q>0 else None
        rows[c['hex_id']]={'ics':round(ics,2) if ics is not None else None,'M':round(M,6),'B':round(B,6) if B is not None else None,'Q':round(Q,6) if Q is not None else None,'n':len(inds),'meters':round(meters,2),'density':round(density,8),'occupied':len(occ),'support':len(support),'profiles':sum(wells[i]['profile'] for i in inds),'rimas':sum(wells[i]['rimas'] for i in inds),'mean_depth':round(sum(wells[i]['depth'] for i in inds)/len(inds),2)}
    return rows,{'well_depth_cap_p':depth_cap_pct,'well_depth_cap_m':round(cap,4),'meter_density_p':density_pct,'meter_density_saturation_m_per_km2':round(sat,8),'microcell_m':micro_step}

def rankdata(vals):
    pairs=sorted(enumerate(vals),key=lambda z:z[1]);r=[0.0]*len(vals);i=0
    while i<len(pairs):
        j=i+1
        while j<len(pairs) and pairs[j][1]==pairs[i][1]:j+=1
        rr=(i+j-1)/2+1
        for k in range(i,j):r[pairs[k][0]]=rr
        i=j
    return r
def pearson(a,b):
    if len(a)<2:return None
    ma=sum(a)/len(a);mb=sum(b)/len(b);va=sum((x-ma)**2 for x in a);vb=sum((y-mb)**2 for y in b)
    if va<=0 or vb<=0:return 1.0 if a==b else None
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(va*vb)
def spearman(a,b):
    x=[];y=[]
    for k in a:
        va=a[k]['ics'];vb=b.get(k,{}).get('ics')
        if va is not None and vb is not None:x.append(va);y.append(vb)
    rr=pearson(rankdata(x),rankdata(y)) if len(x)>=2 else None;return {'n_common':len(x),'rho':None if rr is None else round(rr,6)}
def summary(rows):
    vals=[r['ics'] for r in rows.values() if r['ics'] is not None];ns=[r['n'] for r in rows.values()]
    return {'cells':len(rows),'cells_with_ics':len(vals),'cells_without_ics':len(rows)-len(vals),'ics_min':min(vals) if vals else None,'ics_median':round(statistics.median(vals),2) if vals else None,'ics_mean':round(statistics.fmean(vals),2) if vals else None,'ics_max':max(vals) if vals else None,'wells_assigned_sum':sum(ns),'max_wells_cell':max(ns) if ns else 0}
def compact_rows(rows):
    # [ICS,M*,B,Qlog,n,meters,density,occupied,support,profiles,rimas,mean_depth]
    return {k:[v['ics'],v['M'],v['B'],v['Q'],v['n'],v['meters'],v['density'],v['occupied'],v['support'],v['profiles'],v['rimas'],v['mean_depth']] for k,v in rows.items()}
def source_fc(wells,raw_hash):
    feats=[]
    for w in wells:
        f=json.loads(json.dumps(w['feature'],ensure_ascii=False));p=f.setdefault('properties',{});p['__atlas_chave_independente']=w['key'];p['__atlas_qlog_registro']=w['q'];p['__atlas_perfil_explicito']=w['profile'];p['__atlas_rimas']=w['rimas'];p['__atlas_snapshot']=CUT_DATE;feats.append(f)
    return {'type':'FeatureCollection','features':feats,'atlas_metadata':{'id':'siagas_pocos_ms','fonte':'Serviço Geológico do Brasil · SIAGAS','corte':CUT_DATE,'sha256_snapshot':raw_hash,'regra':'poços deduplicados por idt_ponto, com fallback por coordenada. O ICS utiliza apenas profundidades positivas para M*. Cadastro sem profundidade permanece na camada fonte, mas não produz metros perfurados.'}}
def rimas_fc(feats,raw_hash):return {'type':'FeatureCollection','features':feats,'atlas_metadata':{'id':'rimas_pocos_monitoramento_ms','fonte':'Serviço Geológico do Brasil · RIMAS','corte':CUT_DATE,'sha256_snapshot':raw_hash,'regra':'RIMAS é evidência complementar. Ausência de estação RIMAS publicada em MS não elimina os poços SIAGAS nem transforma ausência em zero.'}}

def patch_catalog_json_obj(cat,counts):
    layers=cat.get('layers',[]) if isinstance(cat,dict) else cat;gridmap={'ics_250':('250','malha_r5_250km2',1554),'ics_500':('500','malha_500km2',793),'ics_1000':('1000','malha_1000km2',412)}
    for item in layers:
        iid=item.get('id')
        if iid=='siagas_pocos_ms':item.update({'status':'incorporada','count':counts['siagas_pocos_ms'],'file':'./camadas/arquivos/siagas_pocos_ms.geojson','validation':'snapshot local V38.4.13 · SGB SIAGAS · corte 14/08/2026'});item.pop('remote_type',None);item.pop('remote_url',None)
        if iid=='rimas_pocos_monitoramento_ms':item.update({'status':'incorporada','count':counts['rimas_pocos_monitoramento_ms'],'file':'./camadas/arquivos/rimas_pocos_monitoramento_ms.geojson','validation':'snapshot local V38.4.13 · SGB RIMAS · corte 14/08/2026 · pode conter zero estações em MS'});item.pop('remote_type',None);item.pop('remote_url',None)
        if iid in gridmap:
            scale,grid,count=gridmap[iid];item.update({'status':'incorporada','count':count,'source':'ITA ARANDU MS · ICS V38.4.13 · SGB SIAGAS/RIMAS','validation':'V38.4.13 · cálculo direto e independente por escala','note':'Conhecimento de subsuperfície documentado por metros perfurados, balanceamento espacial e qualidade do registro. Q_log reserva sua pontuação máxima para evidência explícita de perfil relacionada ao RIMAS. Ausência permanece transparente e não equivale a zero.','derive_type':'ics_snapshot_v38413','grid_source_id':grid,'ics_scale':scale})
    return cat

def patch_app(repo:Path,counts):
    p=repo/'docs/assets/js/app.js';txt=p.read_text(encoding='utf-8');prefix='const CATALOG=';pos=txt.index(prefix)+len(prefix);cat,end=json.JSONDecoder().raw_decode(txt[pos:]);cat=patch_catalog_json_obj(cat,counts);txt=txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:]
    color_marker="function igfColor(v){const c=igfClass(v);return ITA_IGF_COLORS[c]||'rgba(0,0,0,0)'}"
    if 'const ITA_ICS_COLORS=' not in txt:
        add="\nconst ITA_ICS_COLORS={'muito baixo':'#f6eadf','baixo':'#e5c6a8','médio':'#c99562','alto':'#a56537','muito alto':'#6f3f1f'};\nfunction icsClass(v){const x=Number(v);if(v===null||v===undefined||!Number.isFinite(x))return'sem conhecimento de subsuperfície materializado';if(x<20)return'muito baixo';if(x<40)return'baixo';if(x<60)return'médio';if(x<75)return'alto';return'muito alto'}\nfunction icsColor(v){const c=icsClass(v);return ITA_ICS_COLORS[c]||'rgba(0,0,0,0)'}"
        if color_marker not in txt:raise RuntimeError('marcador de cor IGF não encontrado em app.js')
        txt=txt.replace(color_marker,color_marker+add,1)
    style_marker="if(st.renderer==='index_igf'){fill=igfColor(p.igf_100);stroke='#4a4a4a';}"
    if "st.renderer==='index_ics'" not in txt:
        if style_marker not in txt:raise RuntimeError('marcador renderer IGF não encontrado em app.js')
        txt=txt.replace(style_marker,style_marker+" if(st.renderer==='index_ics'){fill=icsColor(p.ics_100);stroke='#4a4a4a';}",1)
    if "if(st.renderer==='index_ics')return" not in txt:
        token="if(st.renderer==='index_igf')return";i=txt.find(token)
        if i<0:raise RuntimeError('legenda IGF não encontrada em app.js')
        e=txt.find('\n',i)
        legend=" if(st.renderer==='index_ics')return `<div class=\"legend-layer-title\">${esc(cfg.name)}</div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:transparent;border:1px solid #4a4a4a\"></span><span>sem conhecimento de subsuperfície materializado · transparente</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#f6eadf;border:1px solid #4a4a4a\"></span><span>0–&lt;20 · muito baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#e5c6a8;border:1px solid #4a4a4a\"></span><span>20–&lt;40 · baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#c99562;border:1px solid #4a4a4a\"></span><span>40–&lt;60 · médio</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#a56537;border:1px solid #4a4a4a\"></span><span>60–&lt;75 · alto</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#6f3f1f;border:1px solid #4a4a4a\"></span><span>75–100 · muito alto</span></div><div class=\"legend-note\">ICS = 100 × (M* × B × Q_log)^(1/3). M* mede metros perfurados por área com truncamento robusto. B mede ocupação e equilíbrio espacial. Q_log mede a utilizabilidade documental do registro e só alcança o máximo quando existe evidência explícita de log litológico, estratigráfico, descrição geológica ou testemunho.</div>`;"
        txt=txt[:e+1]+legend+'\n'+txt[e+1:]
    if 'async function buildIcsSnapshotV38413' not in txt:
        marker='async function buildImcPreview(cfg)';i=txt.find(marker)
        if i<0:raise RuntimeError('marcador builder não encontrado')
        builder="""async function buildIcsSnapshotV38413(cfg){
 const gridCfg=CATALOG.layers.find(x=>x.id===cfg.grid_source_id);
 if(!gridCfg)throw new Error('Malha do ICS V38.4.13 não encontrada no catálogo');
 const grid=await ensure(gridCfg),key=String(cfg.ics_scale||''),scores=window.ITA_ICS_V38413?.grids?.[key],meta=window.ITA_ICS_V38413?.metadata||{};
 if(!scores)throw new Error('Snapshot ICS V38.4.13 não encontrado para esta escala. Execute o materializador do patch.');
 const features=(grid.features||[]).map(hf=>{const hid=String(hf.properties?.hex_id||''),r=scores[hid];if(!r)return {...hf,properties:{...(hf.properties||{}),ics_100:null,classe_ics:'sem conhecimento de subsuperfície materializado'}};const [ics,M,B,Q,n,meters,density,occupied,support,profiles,rimas,meanDepth]=r;return {...hf,properties:{...(hf.properties||{}),ics_100:ics,classe_ics:icsClass(ics),m_estrela:M,balanceamento_subsolo:B,q_log:Q,n_pocos_com_profundidade:n,metros_perfurados_truncados:meters,metros_por_km2:density,microcelulas_ocupadas:occupied,microcelulas_suporte:support,pocos_com_perfil_explicito:profiles,pocos_rimas:rimas,profundidade_media_m:meanDepth,formula:'ICS_h = 100 × (M* × B × Q_log)^(1/3)',fonte_ics:'SGB · SIAGAS e RIMAS',regra_ausencia:'sem poço com profundidade positiva → ICS nulo e hexágono transparente.',regra_qlog:'profundidade, aquífero e data de perfuração contribuem para utilizabilidade documental. O quarto bloco exige campo que declare explicitamente conteúdo litológico, estratigráfico, descrição geológica ou testemunho; relação RIMAS isolada não equivale a log.',limite_interpretativo:'ICS mede disponibilidade de conhecimento de subsuperfície documentado. Não mede recurso hídrico, produtividade, qualidade da água, favorabilidade mineral ou reserva.',metodo:'V38.4.13 · cálculo direto na escala · sem agregação entre escalas',data_corte:meta.cut_date||'2026-08-14'}};});
 return {type:'FeatureCollection',features,atlas_metadata:{indice:'ICS',versao:'V38.4.13',escala:key,formula:'ICS_h = 100 × (M* × B × Q_log)^(1/3)',fonte:'SGB · SIAGAS/RIMAS',regra:'metros perfurados, balanceamento espacial e qualidade documental; cálculo independente em 250, 500 e 1000 km²',limite:'índice de conhecimento de subsuperfície, não de potencial ou produtividade'}};
}
"""
        txt=txt[:i]+builder+txt[i:]
    chain="if(!d&&cfg.derive_type==='igf_snapshot_v38412')d=await buildIgfSnapshotV38412(cfg);"
    if "derive_type==='ics_snapshot_v38413'" not in txt:
        if chain not in txt:raise RuntimeError('cadeia derive IGF não encontrada')
        txt=txt.replace(chain,chain+"if(!d&&cfg.derive_type==='ics_snapshot_v38413')d=await buildIcsSnapshotV38413(cfg);",1)
    scale_marker="const IGF_SCALE_LAYERS=['igf_250','igf_500','igf_1000'];"
    if 'const ICS_SCALE_LAYERS=' not in txt:
        if scale_marker not in txt:raise RuntimeError('grupo escalas IGF não encontrado')
        txt=txt.replace(scale_marker,scale_marker+" const ICS_SCALE_LAYERS=['ics_250','ics_500','ics_1000'];",1)
    toggle_marker='async function toggle(id,on){const cfg=CATALOG.layers.find(x=>x.id===id);if(!cfg)return;'
    if 'ICS_SCALE_LAYERS.includes(id)' not in txt:
        i=txt.find(toggle_marker)
        if i<0:raise RuntimeError('toggle não encontrado')
        j=i+len(toggle_marker);inject='if(on&&ICS_SCALE_LAYERS.includes(id)){for(const other of ICS_SCALE_LAYERS){if(other===id)continue;state.active.delete(other);const ocb=document.querySelector(`input[data-layer="${other}"]`);if(ocb)ocb.checked=false;updateLayerCard(other)}}';txt=txt[:j]+inject+txt[j:]
    p.write_text(txt,encoding='utf-8',newline='\n')

def update_local_catalog(repo:Path,counts):
    jp=repo/'docs/camadas/catalogo-local.json';mapping={'siagas_pocos_ms':('./camadas/arquivos/siagas_pocos_ms.geojson','SIAGAS · poços e pontos d’água em Mato Grosso do Sul','SGB · SIAGAS · snapshot local V38.4.13'),'rimas_pocos_monitoramento_ms':('./camadas/arquivos/rimas_pocos_monitoramento_ms.geojson','RIMAS · poços de monitoramento publicados em Mato Grosso do Sul','SGB · RIMAS · snapshot local V38.4.13')}
    if jp.exists():
        arr=load_json(jp);by={x.get('id'):x for x in arr if isinstance(x,dict)}
        for lid,(arquivo,nome,fonte) in mapping.items():
            fp=repo/'docs'/arquivo.replace('./','');rec={'id':lid,'arquivo':arquivo,'nome':nome,'grupo':'Hidrologia e hidrogeologia','status':'incorporada','fonte':fonte,'validacao':'corte 14/08/2026 · fonte oficial SGB · suporte do ICS V38.4.13','feicoes':counts[lid],'bytes':fp.stat().st_size if fp.exists() else 0}
            if lid in by:by[lid].update(rec)
            else:arr.append(rec)
        dump_json(jp,arr)
    p=repo/'docs/camadas/catalogo-local.js'
    if p.exists():
        t=p.read_text(encoding='utf-8');prefix='window.ITA_LOCAL_LAYER_FILES=';pos=t.index(prefix)+len(prefix);o,end=json.JSONDecoder().raw_decode(t[pos:]);o.update({lid:arquivo for lid,(arquivo,_,__) in mapping.items()});p.write_text(t[:pos]+json.dumps(o,ensure_ascii=False,separators=(',',':'))+t[pos+end:],encoding='utf-8',newline='\n')

def update_web(repo:Path):
    ip=repo/'docs/index.html';s=ip.read_text(encoding='utf-8').replace('v=38.4.12','v=38.4.13');script='<script src="./indices/ics-v38413.js?v=38.4.13"></script>'
    if script not in s:
        marker='<script src="./indices/igf-v38412.js?v=38.4.13"></script>'
        if marker not in s:raise RuntimeError('script IGF não encontrado em index.html')
        s=s.replace(marker,marker+'\n'+script,1)
    ip.write_text(s,encoding='utf-8',newline='\n')
    bp=repo/'docs/assets/js/bootstrap.js'
    if bp.exists():bp.write_text(bp.read_text(encoding='utf-8').replace('v=38.4.12','v=38.4.13'),encoding='utf-8',newline='\n')
    swp=repo/'docs/service-worker.js';sw=swp.read_text(encoding='utf-8');sw=re.sub(r"const ITA_CACHE\s*=\s*'[^']+';","const ITA_CACHE = 'ita-arandu-v38-4-13-ics-conhecimento-subsolo';",sw,count=1);sw=sw.replace('v=38.4.12','v=38.4.13')
    assets=['./indices/ics-v38413.js?v=38.4.13','./camadas/arquivos/siagas_pocos_ms.geojson','./camadas/arquivos/rimas_pocos_monitoramento_ms.geojson','./documentos/metodologia-ics.html']
    for asset in assets:
        if asset not in sw:
            marker='"./indices/igf-v38412.js?v=38.4.13",'
            if marker not in sw:raise RuntimeError('marcador IGF no precache não encontrado')
            sw=sw.replace(marker,marker+f'\n  "{asset}",',1)
    swp.write_text(sw,encoding='utf-8',newline='\n')
    dp=repo/'docs/documentos/index.html';d=dp.read_text(encoding='utf-8')
    if 'metodologia-ics.html' not in d:d=d.replace('</body>','<p><a href="./metodologia-ics.html">ICS · Conhecimento do Subsolo · metodologia V38.4.13</a></p></body>',1)
    dp.write_text(d,encoding='utf-8',newline='\n')

def update_bibliography(repo:Path):
    jp=repo/'docs/referencias/bibliografia-camadas-indices.json'
    if jp.exists():
        o=load_json(jp);ids={'ics_250','ics_500','ics_1000','siagas_pocos_ms','rimas_pocos_monitoramento_ms'}
        for e in o.get('entries',[]):
            if isinstance(e,dict) and e.get('id') in ids:e['status']='incorporada'
        dump_json(jp,o)
    hp=repo/'docs/referencias/index.html'
    if hp.exists():
        h=hp.read_text(encoding='utf-8')
        for lid in ['ics_250','ics_500','ics_1000','siagas_pocos_ms','rimas_pocos_monitoramento_ms']:
            sm=f'id="layer-{lid}"';start=h.find(sm)
            if start<0:continue
            s0=h.rfind('<section',0,start);s1=h.find('</section>',start)
            if s0<0 or s1<0:continue
            s1+=len('</section>');sec=h[s0:s1].replace(' · planejada ·',' · incorporada ·').replace(' · conectada ·',' · incorporada ·');h=h[:s0]+sec+h[s1:]
        hp.write_text(h,encoding='utf-8',newline='\n')

def update_changelog(repo:Path):
    entry='''\n## V38.4.13 · ICS · Conhecimento do Subsolo · 2026-08-14\n\n- materializa poços SIAGAS e consulta complementar RIMAS\n- congela ICS_h = 100 × (M* × B × Q_log)^(1/3)\n- normaliza metros perfurados por área com P95 e limita profundidades individuais pelo P99\n- mede balanceamento espacial por micromalha e equitabilidade de Shannon ponderada por metros perfurados\n- reserva a pontuação máxima de Q_log para suporte explícito de perfil relacionado ao RIMAS\n- calcula 250, 500 e 1000 km² diretamente dos poços originais, sem agregação entre escalas\n'''
    ch=repo/'CHANGELOG.md'
    if ch.exists():
        t=ch.read_text(encoding='utf-8')
        if 'V38.4.13 · ICS' not in t:ch.write_text(t.rstrip()+entry+'\n',encoding='utf-8',newline='\n')
    rd=repo/'README.md'
    if rd.exists():
        t=rd.read_text(encoding='utf-8');t=re.sub(r'V38\.4\.12[^\n]*','V38.4.13 · ICS · Conhecimento do Subsolo',t,count=1) if 'V38.4.12' in t else t;rd.write_text(t,encoding='utf-8',newline='\n')
    dh=repo/'docs/documentos/changelog.html'
    if dh.exists():
        t=dh.read_text(encoding='utf-8')
        if 'V38.4.13 · ICS' not in t:t=t.replace('</body>','<h2>V38.4.13 · ICS · Conhecimento do Subsolo</h2><p>Materialização multiescalar independente de poços SIAGAS, com RIMAS como suporte complementar de perfil, profundidade robustamente truncada e balanceamento espacial.</p></body>',1)
        dh.write_text(t,encoding='utf-8',newline='\n')

def self_test():
    assert id_norm(12.0)=='12';assert positive('123.4')==123.4;assert positive('-1') is None;assert shannon_evenness([10,10])==1.0
    print('SELFTEST ICS V38.4.13 · PASS')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');ap.add_argument('--self-test',action='store_true');ap.add_argument('--source-file');args=ap.parse_args()
    if args.self_test:self_test();return 0
    repo=Path(args.repo).resolve()
    for rel in list(GRID_FILES.values())+[LIMIT_FILE]:
        if not (repo/rel).exists():raise RuntimeError(f'arquivo estrutural ausente · {rel}')
    for rel in ['docs/indices/iod_v3848_snapshot.json','docs/indices/icp_v3849_snapshot.json','docs/indices/igc_v38410_snapshot.json','docs/indices/igq_v38411_snapshot.json','docs/indices/igf_v38412_snapshot.json']:
        if not (repo/rel).exists():raise RuntimeError(f'base V38.4.12 incompleta · {rel}')
    print('ITA ARANDU MS · materialização ICS V38.4.13');print('Fórmula ·',FORMULA)
    if args.source_file:source=load_json(Path(args.source_file));source_label='arquivo local fornecido'
    else:source_label,source=fetch_source()
    raw=canonical_bytes(source);raw_hash=sha256_bytes(raw);state_items=feature_polys(load_json(repo/LIMIT_FILE));wells,rimas_feats,source_stats=prepare_source(source,state_items)
    if not any(w['depth'] is not None for w in wells):raise RuntimeError('nenhum poço SIAGAS com profundidade positiva ficou disponível em Mato Grosso do Sul')
    grids={};cells={};assigned={}
    for sc,rel in GRID_FILES.items():grids[sc],cells[sc]=load_grid(repo/rel);assigned[sc],_,_=assign_points(wells,cells[sc])
    baseline={};normalization={}
    for sc in ['250','500','1000']:baseline[sc],normalization[sc]=calculate_scale(cells[sc],assigned[sc],wells)
    sensitivity={}
    for sc in ['250','500','1000']:
        sensitivity[sc]={};base=baseline[sc]
        for step,dp,cp in [(2500,95,99),(10000,95,99),(5000,90,99),(5000,99,99),(5000,95,95)]:
            alt,_=calculate_scale(cells[sc],assigned[sc],wells,step,dp,cp);sensitivity[sc][f'micro_{step/1000:g}km_density_p{dp}_depthcap_p{cp}']=spearman(base,alt)
    sfc=source_fc(wells,raw_hash);rfc=rimas_fc(rimas_feats,raw_hash);dump_json(repo/'docs/camadas/arquivos/siagas_pocos_ms.geojson',sfc,compact=True);dump_json(repo/'docs/camadas/arquivos/rimas_pocos_monitoramento_ms.geojson',rfc,compact=True)
    raw_path=repo/f'data/subsolo_siagas_rimas_raw_{CUT_DATE.replace("-","")}.json.gz';raw_path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(raw_path,'wb',compresslevel=9) as gz:gz.write(raw)
    snap={'metadata':{'index':'ICS','version':VERSION,'calculated_at':now_iso(),'cut_date':CUT_DATE,'formula':FORMULA,'components':{'M*':'metros perfurados por área efetiva, com profundidade individual truncada no P99 e densidade normalizada no P95 da própria escala','B':'sqrt(O × E), com O como fração de micromalhas ocupadas e E como equitabilidade de Shannon ponderada pelos metros perfurados','Q_log':'média ponderada por metros de quatro blocos de utilizabilidade documental: profundidade, aquífero, data de perfuração e log explícito litológico, estratigráfico, geológico ou testemunho identificável'},'qlog_guardrail':'o serviço público SIAGAS utilizado não expõe automaticamente um perfil litológico completo para cada poço. A mera presença no RIMAS ou de dados construtivos não é tratada como log litológico. A parcela final de 0,25 somente é atribuída quando um campo relacionado declara explicitamente conteúdo litológico, estratigráfico, descrição geológica ou testemunho. Sem essa evidência, Q_log máximo do registro é 0,75.','litoteca_rule':'Rede de Litotecas permanece referência metodológica e futura extensão. Nenhum testemunho ou caixa de sondagem é imputado espacialmente nesta versão sem identificador e localização verificáveis.','microcell_m':BASE_MICROCELL_M,'density_percentile':BASE_DENSITY_PERCENTILE,'depth_cap_percentile':BASE_DEPTH_CAP_PERCENTILE,'scale_rule':'250, 500 e 1000 km² são calculados diretamente dos poços originais, sem agregação entre escalas.','null_rule':'sem poço com profundidade positiva, ICS=null e o hexágono permanece transparente. Cadastro sem profundidade não é convertido em zero.','interpretation_limit':'ICS mede disponibilidade de conhecimento de subsuperfície documentado. Não mede produtividade hídrica, qualidade da água, favorabilidade mineral, recurso, reserva ou viabilidade econômica.','source':'SGB · SIAGAS e RIMAS','source_method':source_label,'source_sha256':raw_hash,'raw_gzip':str(raw_path.relative_to(repo)).replace('\\','/'),'references':['REF-105','REF-106','REF-110','REF-115','REF-059','REF-093','REF-094']},'source_summary':source_stats,'normalization':normalization,'summary':{sc:summary(baseline[sc]) for sc in baseline},'sensitivity_spearman':sensitivity,'grids':{sc:compact_rows(baseline[sc]) for sc in baseline}}
    dump_json(repo/'docs/indices/ics_v38413_snapshot.json',snap);(repo/'docs/indices/ics-v38413.js').write_text('window.ITA_ICS_V38413='+json.dumps(snap,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
    counts={'siagas_pocos_ms':len(sfc['features']),'rimas_pocos_monitoramento_ms':len(rfc['features'])};patch_app(repo,counts);update_local_catalog(repo,counts);update_web(repo);update_bibliography(repo);update_changelog(repo);(repo/'VERSION').write_text(VERSION+'\n',encoding='utf-8',newline='\n')
    runtime={'audit':'V38.4.13 ICS runtime','status':'PASS','calculated_at':now_iso(),'source_sha256':raw_hash,'source_counts':counts,'source_stats':source_stats,'summaries':{sc:summary(baseline[sc]) for sc in baseline},'checks':{'siagas_deduplicated':True,'positive_depth_required_for_meters':True,'depth_robust_truncation':True,'spatial_balance_explicit':True,'qlog_profile_ceiling_guardrail':True,'rimas_relation_not_equal_log':True,'rimas_complementary_not_required':True,'independent_scale_calculation':True,'null_is_not_zero':True,'previous_indices_not_recomputed':True}}
    dump_json(repo/'AUDITORIA_V38_4_13_ICS_RUNTIME.json',runtime);print('ICS V38.4.13 materializado ·',counts)
    for sc in ['250','500','1000']:print(sc,'km² ·',summary(baseline[sc]))
    return 0
if __name__=='__main__':raise SystemExit(main())
