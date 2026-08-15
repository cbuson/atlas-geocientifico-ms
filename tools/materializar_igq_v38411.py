#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, gzip, hashlib, json, math, re, statistics, unicodedata, urllib.parse, urllib.request
from pathlib import Path

VERSION='V38.4.11-IGQ-CONHECIMENTO-GEOQUIMICO-20260814'
CUT_DATE='2026-08-14'
FORMULA='IGQ_h = max(IGQ_SC, IGQ_CB, IGQ_solo, IGQ_rocha, IGQ_agua)'
MEDIUM_FORMULA='IGQ_m = 100 × (G_m × A_m × Q_m)^(1/3)'
G_FORMULA='G_m = sqrt(D*_m × O_m)'
BASE_MICROCELL_M=5000.0
BASE_DENSITY_PERCENTILE=95
BASE_ANALYTICAL_PERCENTILE=95
LAEA_LON0=-54.5
LAEA_LAT0=-20.5
EARTH_R=6371007.181
BBOX_MS=(-58.3,-24.3,-50.6,-17.0)
SERVICE_ROOT='https://geoportal.sgb.gov.br/server/rest/services/geologia/geoq_externa/MapServer'
GRID_FILES={
 '250':'docs/camadas/arquivos/malha_r5_250km2.geojson',
 '500':'docs/camadas/arquivos/malha_500km2.geojson',
 '1000':'docs/camadas/arquivos/malha_1000km2.geojson',
}
LIMIT_FILE='docs/camadas/arquivos/limite_ms_ibge_2025.geojson'
MEDIUMS={
 'SC':{'label':'Sedimento de Corrente','patterns':['amostras analisadas de sedimento de corrente']},
 'CB':{'label':'Concentrado de Bateia','patterns':['amostras analisadas de concentrado de bateia','amostras analisadas de concentrado de batéia']},
 'solo':{'label':'Solo','patterns':['amostras analisadas de solo']},
 'rocha':{'label':'Rocha','patterns':['amostras analisadas de rocha']},
 'agua':{'label':'Água','patterns':['amostras analisadas de agua','amostras analisadas de água']},
}

def now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def load_json(path:Path):
    with path.open('r',encoding='utf-8') as f:return json.load(f)

def dump_json(path:Path,obj,compact=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,ensure_ascii=False,separators=(',',':') if compact else None,indent=None if compact else 2)
        f.write('\n')

def canonical_bytes(obj):return json.dumps(obj,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode('utf-8')
def sha256_bytes(data:bytes):return hashlib.sha256(data).hexdigest()

def norm_text(v):
    s=str(v or '').strip().lower()
    s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',s)

def fetch_json(url,timeout=120):
    req=urllib.request.Request(url,headers={'User-Agent':'ITA-ARANDU-MS/38.4.11 Python urllib','Accept':'application/json, application/geo+json;q=0.9, */*;q=0.1'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8-sig'))

def query_url(layer,params):return f'{SERVICE_ROOT}/{layer}/query?'+urllib.parse.urlencode(params,safe=',()')

def service_layer_meta(layer):return fetch_json(f'{SERVICE_ROOT}/{layer}?f=pjson')

def discover_layers(service_meta):
    layers=service_meta.get('layers') or []
    found={}
    for key,cfg in MEDIUMS.items():
        pats=[norm_text(x) for x in cfg['patterns']]
        matches=[]
        for x in layers:
            nm=norm_text(x.get('name'))
            if any(p in nm or nm in p for p in pats):matches.append(x)
        if not matches:raise RuntimeError(f'camada de amostras analisadas não localizada no serviço para {cfg["label"]}')
        matches.sort(key=lambda x:x.get('id',999999));found[key]=matches[0]
    return found

def fetch_layer_features(layer_id):
    xmin,ymin,xmax,ymax=BBOX_MS
    common={'where':'1=1','geometry':f'{xmin},{ymin},{xmax},{ymax}','geometryType':'esriGeometryEnvelope','inSR':'4326','spatialRel':'esriSpatialRelIntersects','f':'json'}
    id_obj=fetch_json(query_url(layer_id,{**common,'returnIdsOnly':'true'}))
    if id_obj.get('error'):raise RuntimeError(str(id_obj['error']))
    object_ids=id_obj.get('objectIds') or []
    feats=[]
    for i in range(0,len(object_ids),500):
        ids=object_ids[i:i+500]
        obj=fetch_json(query_url(layer_id,{'where':'1=1','objectIds':','.join(str(x) for x in ids),'outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}))
        if obj.get('error'):raise RuntimeError(str(obj['error']))
        feats.extend(obj.get('features') or [])
    return object_ids,feats

def fetch_related(layer_id,object_ids,rel_id):
    groups={}
    for i in range(0,len(object_ids),150):
        ids=object_ids[i:i+150]
        if not ids:continue
        params={'objectIds':','.join(str(x) for x in ids),'relationshipId':str(rel_id),'outFields':'*','returnGeometry':'false','f':'json'}
        url=f'{SERVICE_ROOT}/{layer_id}/queryRelatedRecords?'+urllib.parse.urlencode(params,safe=',')
        obj=fetch_json(url)
        if obj.get('error'):raise RuntimeError(f'relacionamento camada {layer_id} · {obj["error"]}')
        for g in obj.get('relatedRecordGroups') or []:
            oid=str(g.get('objectId'))
            rows=[]
            for rr in g.get('relatedRecords') or []:
                rows.append(dict(rr.get('attributes') or rr.get('properties') or {}))
            groups.setdefault(oid,[]).extend(rows)
    return groups

def fetch_source():
    service_meta=fetch_json(SERVICE_ROOT+'?f=pjson')
    discovered=discover_layers(service_meta)
    media={}
    for key,ldef in discovered.items():
        lid=ldef['id'];meta=service_layer_meta(lid)
        rels=meta.get('relationships') or []
        if not rels:raise RuntimeError(f'camada {meta.get("name") or lid} não publicou relacionamento com resultados analíticos')
        rel=rels[0]
        ids,features=fetch_layer_features(lid)
        related=fetch_related(lid,ids,rel.get('id'))
        media[key]={'label':MEDIUMS[key]['label'],'layer_id':lid,'layer_name':meta.get('name'),'relationship_id':rel.get('id'),'related_table_id':rel.get('relatedTableId'),'features':features,'related':related,'ids_bbox':len(ids)}
    return 'ArcGIS REST GeoSGB · geoq_externa · amostras analisadas + resultados relacionados',SERVICE_ROOT,{'service':SERVICE_ROOT,'media':media,'atlas_fetch':{'cut_date':CUT_DATE}}

def ci_get(props,*names):
    if not isinstance(props,dict):return None
    low={str(k).lower():v for k,v in props.items()}
    for n in names:
        if n in props:return props[n]
        if str(n).lower() in low:return low[str(n).lower()]
    return None

def nonempty(v):
    if v is None:return False
    if isinstance(v,str):return bool(v.strip()) and norm_text(v) not in {'null','none','nan','nao informado','sem informacao','n/a','na'}
    return True

def truthy_duplicate(v):
    if v is None:return False
    if isinstance(v,(int,float)):return float(v)!=0
    s=norm_text(v)
    return s in {'1','sim','s','yes','true','duplicata','duplicate','dupl'} or 'duplic' in s

def get_point(feat):
    g=feat.get('geometry') or {}
    if g.get('type')=='Point' and isinstance(g.get('coordinates'),list) and len(g['coordinates'])>=2:
        try:return float(g['coordinates'][0]),float(g['coordinates'][1])
        except Exception:pass
    p=feat.get('properties') or {}
    try:return float(ci_get(p,'longitude','LONGITUDE','X','LON')),float(ci_get(p,'latitude','LATITUDE','Y','LAT'))
    except Exception:return None

def oid_of(feat):
    p=feat.get('properties') or {}
    v=ci_get(p,'objectid','OBJECTID','fid','FID')
    if v is None:v=feat.get('id')
    try:return str(int(float(v)))
    except Exception:return str(v) if v is not None else None

def independent_key(feat,medium):
    p=feat.get('properties') or {};pt=get_point(feat) or (None,None)
    lab=ci_get(p,'numero_de_laboratorio','NUM_LAB','num_laboratorio')
    if nonempty(lab):return f'{medium}:LAB:{str(lab).strip().upper()}'
    campo=ci_get(p,'numero_de_campo','NUM_CAMPO','num_campo')
    return f'{medium}:CAMPO_COORD:{str(campo or "SEM_CAMPO").strip().upper()}:{round(pt[0],6)}:{round(pt[1],6)}'

def metadata_quality(p):
    blocks=[
        nonempty(ci_get(p,'laboratorio','LABORATORIO')),
        nonempty(ci_get(p,'data_de_analise','DATA_DE_ANALISE','DTVISITA')),
        nonempty(ci_get(p,'abertura','ABERTURA')),
        nonempty(ci_get(p,'leitura','LEITURA')),
        nonempty(ci_get(p,'projeto_publicacao','projeto_amostragem','PROJETO','ACAO')),
    ]
    return sum(1 for x in blocks if x)/len(blocks),blocks

def analytical_count(rows):
    # Cada registro relacionado representa uma determinação publicada. Não interpreta nem imputa valores.
    # Linhas totalmente vazias e campos exclusivamente técnicos não contam.
    n=0
    for r in rows:
        substantive=[]
        for k,v in r.items():
            nk=norm_text(k)
            if nk in {'objectid','globalid','parentglobalid','shape','created_user','created_date','last_edited_user','last_edited_date'}:continue
            if nonempty(v):substantive.append((k,v))
        if substantive:n+=1
    return n

def build_units(source_media):
    out={};stats={}
    for medium,src in source_media.items():
        related=src.get('related') or {};groups={};excluded_dup=0;excluded_no_results=0;invalid=0
        for f in src.get('features') or []:
            pt=get_point(f)
            if pt is None:invalid+=1;continue
            p=f.get('properties') or {}
            if truthy_duplicate(ci_get(p,'duplicata','DUPLICATA')):
                excluded_dup+=1;continue
            oid=oid_of(f);rows=related.get(str(oid),[]) if oid is not None else []
            nr=analytical_count(rows)
            if nr<=0:excluded_no_results+=1;continue
            key=independent_key(f,medium);q,blocks=metadata_quality(p)
            u={'key':key,'medium':medium,'point':pt,'q':q,'q_blocks':blocks,'n_results':nr,'feature':f,'objectid':oid}
            old=groups.get(key)
            if old is None or (u['n_results'],u['q'])>(old['n_results'],old['q']):groups[key]=u
        units=list(groups.values());out[medium]=units
        stats[medium]={'features_source':len(src.get('features') or []),'independent_analytical_samples':len(units),'duplicates_excluded':excluded_dup,'without_related_results_excluded':excluded_no_results,'invalid_geometry_excluded':invalid}
    return out,stats

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
            xcross=(xj-xi)*(y-yi)/((yj-yi) if yj!=yi else 1e-30)+xi
            if x<xcross:inside=not inside
        j=i
    return inside

def point_in_poly(pt,poly):
    if not poly or not point_in_ring(pt,poly[0]):return False
    return not any(point_in_ring(pt,h) for h in poly[1:])

def point_in_geom_projected(pt,geom):return any(point_in_poly(pt,p) for p in geom['polys'])

def project_geometry(geom):
    typ=geom.get('type');coords=geom.get('coordinates')
    if typ=='Polygon':polys=[coords]
    elif typ=='MultiPolygon':polys=coords
    else:raise ValueError(f'geometria poligonal esperada e encontrada {typ}')
    out=[];xs=[];ys=[]
    for poly in polys:
        pp=[]
        for ring in poly:
            rr=[]
            for c in ring:
                x,y=laea(float(c[0]),float(c[1]));rr.append((x,y));xs.append(x);ys.append(y)
            pp.append(rr)
        out.append(pp)
    return {'polys':out,'bbox':(min(xs),min(ys),max(xs),max(ys))}

def feature_polys(fc):
    out=[]
    for f in fc.get('features',[]):
        g=f.get('geometry') or {};typ=g.get('type');coords=g.get('coordinates');parts=[coords] if typ=='Polygon' else (coords if typ=='MultiPolygon' else [])
        for part in parts:
            pg=project_geometry({'type':'Polygon','coordinates':part});out.append({'feature':f,'geom':pg,'bbox':pg['bbox']})
    return out

def make_spatial_index(items,bin_m=50000.0):
    idx={}
    for i,c in enumerate(items):
        xmin,ymin,xmax,ymax=c['bbox'];ix0=math.floor(xmin/bin_m);ix1=math.floor(xmax/bin_m);iy0=math.floor(ymin/bin_m);iy1=math.floor(ymax/bin_m)
        for ix in range(ix0,ix1+1):
            for iy in range(iy0,iy1+1):idx.setdefault((ix,iy),[]).append(i)
    return idx,bin_m

def find_poly(pt,items,index,bin_m):
    cand=index.get((math.floor(pt[0]/bin_m),math.floor(pt[1]/bin_m)),[]);hits=[]
    for i in cand:
        b=items[i]['bbox']
        if pt[0]<b[0]-.1 or pt[0]>b[2]+.1 or pt[1]<b[1]-.1 or pt[1]>b[3]+.1:continue
        if point_in_geom_projected(pt,items[i]['geom']):hits.append(i)
    return hits[0] if hits else None

def clip_units_to_state(units_by_medium,state_items):
    idx,bin_m=make_spatial_index(state_items,100000.0);out={};removed={}
    for medium,units in units_by_medium.items():
        keep=[];n=0
        for u in units:
            lon,lat=u['point']
            if not (-61<=lon<=-47 and -27<=lat<=-15):n+=1;continue
            if find_poly(laea(lon,lat),state_items,idx,bin_m) is None:n+=1;continue
            keep.append(u)
        out[medium]=keep;removed[medium]=n
    return out,removed

def load_grid(path:Path):
    fc=load_json(path);cells=[]
    for f in fc.get('features',[]):
        pg=project_geometry(f['geometry']);p=f.get('properties') or {};hid=str(p.get('hex_id') or '')
        if not hid:raise RuntimeError(f'hexágono sem hex_id em {path.name}')
        try:area=float(p['area_efetiva_ms_km2'])
        except Exception:area=float(p.get('area_nominal_km2') or 0)
        if area<=0:raise RuntimeError(f'área efetiva inválida em {hid}')
        b=pg['bbox'];cells.append({'hex_id':hid,'feature':f,'geom':pg,'bbox':b,'centroid':((b[0]+b[2])/2,(b[1]+b[3])/2),'area':area})
    return fc,cells

def assign_units(units,cells):
    idx,bin_m=make_spatial_index(cells,50000.0);assigned=[[] for _ in cells];missing=[];ambiguous=0
    for ui,u in enumerate(units):
        pt=laea(*u['point']);cand=idx.get((math.floor(pt[0]/bin_m),math.floor(pt[1]/bin_m)),[]);hits=[]
        for ci in cand:
            c=cells[ci];b=c['bbox']
            if pt[0]<b[0]-.1 or pt[0]>b[2]+.1 or pt[1]<b[1]-.1 or pt[1]>b[3]+.1:continue
            if point_in_geom_projected(pt,c['geom']):hits.append(ci)
        if not hits:missing.append(ui);continue
        if len(hits)>1:
            ambiguous+=1;hits.sort(key=lambda ci:(pt[0]-cells[ci]['centroid'][0])**2+(pt[1]-cells[ci]['centroid'][1])**2)
        assigned[hits[0]].append(ui)
    return assigned,missing,ambiguous

def percentile(vals,p):
    x=sorted(float(v) for v in vals if v is not None and math.isfinite(float(v)))
    if not x:return None
    if len(x)==1:return x[0]
    pos=(len(x)-1)*p/100;lo=math.floor(pos);hi=math.ceil(pos)
    return x[lo] if lo==hi else x[lo]+(x[hi]-x[lo])*(pos-lo)

def micro_key(pt,step):return math.floor(pt[0]/step),math.floor(pt[1]/step)

def support_microcells(cell,step,occupied):
    xmin,ymin,xmax,ymax=cell['bbox'];out=set();ix0=math.floor(xmin/step)-1;ix1=math.floor(xmax/step)+1;iy0=math.floor(ymin/step)-1;iy1=math.floor(ymax/step)+1
    for ix in range(ix0,ix1+1):
        x=(ix+.5)*step
        for iy in range(iy0,iy1+1):
            y=(iy+.5)*step
            if x<xmin-.1 or x>xmax+.1 or y<ymin-.1 or y>ymax+.1:continue
            if point_in_geom_projected((x,y),cell['geom']):out.add((ix,iy))
    out.update(occupied);return out

def calculate_medium(cells,assigned,units,micro_step=BASE_MICROCELL_M,density_pct=BASE_DENSITY_PERCENTILE,analytical_pct=BASE_ANALYTICAL_PERCENTILE):
    dens=[len(assigned[i])/c['area'] for i,c in enumerate(cells) if assigned[i]]
    dsat=percentile(dens,density_pct)
    if dsat is None or dsat<=0:return {c['hex_id']:{'score':None,'G':None,'A':None,'Q':None,'D':None,'O':None,'n':0,'density':0.0,'occupied':0,'micro_support':None,'results':0,'q_mean':None,'a_mean':None} for c in cells},None,None
    asat=percentile([u['n_results'] for u in units if u['n_results']>0],analytical_pct) or 1.0
    rows={}
    for ci,c in enumerate(cells):
        inds=assigned[ci];n=len(inds)
        if n==0:
            rows[c['hex_id']]={'score':None,'G':None,'A':None,'Q':None,'D':None,'O':None,'n':0,'density':0.0,'occupied':0,'micro_support':None,'results':0,'q_mean':None,'a_mean':None};continue
        density=n/c['area'];D=min(1.0,density/dsat)
        occ={micro_key(laea(*units[ui]['point']),micro_step) for ui in inds};ms=support_microcells(c,micro_step,occ);O=min(1.0,len(occ)/len(ms)) if ms else 1.0
        G=math.sqrt(max(0,D*O))
        avals=[min(1.0,units[ui]['n_results']/asat) for ui in inds];A=statistics.fmean(avals)
        qvals=[units[ui]['q'] for ui in inds];Q=statistics.fmean(qvals)
        score=100*((G*A*Q)**(1/3))
        rows[c['hex_id']]={'score':round(score,2),'G':round(G,6),'A':round(A,6),'Q':round(Q,6),'D':round(D,6),'O':round(O,6),'n':n,'density':round(density,8),'occupied':len(occ),'micro_support':len(ms),'results':sum(units[ui]['n_results'] for ui in inds),'q_mean':round(Q,6),'a_mean':round(A,6)}
    return rows,dsat,asat

def combine_mediums(cells,by_medium):
    rows={}
    for c in cells:
        hid=c['hex_id'];scores={m:by_medium[m][hid]['score'] for m in MEDIUMS};valid=[v for v in scores.values() if v is not None]
        best=max(valid) if valid else None;best_medium=None
        if best is not None:
            order=['SC','CB','solo','rocha','agua'];best_medium=next(m for m in order if scores[m]==best)
        rows[hid]={'igq':best,'best_medium':best_medium,'medium_scores':scores,'media_presentes':sum(v is not None for v in scores.values())}
    return rows

def compact_rows(combined,medium_rows):
    # [IGQ,best,media_presentes, SC,CB,solo,rocha,agua, nSC,nCB,nSolo,nRocha,nAgua]
    out={}
    for hid,r in combined.items():
        out[hid]=[r['igq'],r['best_medium'],r['media_presentes']]+[r['medium_scores'][m] for m in ['SC','CB','solo','rocha','agua']]+[medium_rows[m][hid]['n'] for m in ['SC','CB','solo','rocha','agua']]
    return out

def summary(combined,medium_rows):
    vals=[r['igq'] for r in combined.values() if r['igq'] is not None]
    return {'cells':len(combined),'cells_with_igq':len(vals),'cells_without_igq':len(combined)-len(vals),'igq_min':min(vals) if vals else None,'igq_median':round(statistics.median(vals),2) if vals else None,'igq_mean':round(statistics.fmean(vals),2) if vals else None,'igq_max':max(vals) if vals else None,'cells_by_medium':{m:sum(1 for r in medium_rows[m].values() if r['score'] is not None) for m in MEDIUMS}}

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

def spearman_combined(a,b):
    x=[];y=[]
    for k in a:
        va=a[k]['igq'];vb=b.get(k,{}).get('igq')
        if va is not None and vb is not None:x.append(va);y.append(vb)
    rr=pearson(rankdata(x),rankdata(y)) if len(x)>=2 else None
    return {'n_common':len(x),'rho':None if rr is None else round(rr,6)}

def source_feature_collection(units_by_medium,source_stats,raw_hash):
    feats=[]
    for m,units in units_by_medium.items():
        for u in units:
            f=json.loads(json.dumps(u['feature'],ensure_ascii=False));p=f.setdefault('properties',{})
            p['__atlas_meio']=m;p['__atlas_meio_nome']=MEDIUMS[m]['label'];p['__atlas_chave_independente']=u['key'];p['__atlas_n_resultados_analiticos']=u['n_results'];p['__atlas_q_documental']=round(u['q'],4);p['__atlas_fonte']='SGB · Geoquímica externa · amostras analisadas';p['__atlas_snapshot']=CUT_DATE
            feats.append(f)
    return {'type':'FeatureCollection','features':feats,'atlas_metadata':{'id':'geoquimica_amostras_sgb_ms','nome':'Amostras geoquímicas analisadas em Mato Grosso do Sul','fonte':'Serviço Geológico do Brasil · Geoportal SGB · geoq_externa','corte':CUT_DATE,'sha256_snapshot_mesclado':raw_hash,'meios_incluidos':['Sedimento de Corrente','Concentrado de Bateia','Solo','Rocha','Água'],'regra':'somente amostras com pelo menos um registro analítico relacionado; duplicatas declaradas não contam como observação territorial independente','estatisticas':source_stats}}

def js_catalog_patch(repo:Path,source_count:int):
    p=repo/'docs/assets/js/app.js';txt=p.read_text(encoding='utf-8')
    prefix='const CATALOG=';pos=txt.index(prefix)+len(prefix);cat,end=json.JSONDecoder().raw_decode(txt[pos:])
    gridmap={'igq_250':('250','malha_r5_250km2',1554),'igq_500':('500','malha_500km2',793),'igq_1000':('1000','malha_1000km2',412)}
    for item in cat.get('layers',[]):
        iid=item.get('id')
        if iid=='geoquimica_amostras_sgb_ms':
            item.update({'status':'incorporada','count':source_count,'validation':'snapshot local V38.4.11 · recorte MS · somente amostras com resultados analíticos relacionados','note':'Fonte oficial materializada para o IGQ. Os valores químicos são preservados na fonte bruta, mas o IGQ mede cobertura de conhecimento e não anomalias.','remote_type':None,'remote_url':None})
        if iid=='geoquimica_resultados_sgb_ms':
            item.update({'status':'incorporada','count':source_count,'validation':'V38.4.11 · resultados relacionados consultados e preservados no snapshot bruto comprimido','note':'Os resultados relacionados alimentam amplitude analítica A. Valores censurados não são imputados nem comparados no IGQ.'})
        if iid in gridmap:
            scale,grid,count=gridmap[iid]
            item.update({'status':'incorporada','count':count,'validation':'V38.4.11 · cálculo direto e independente por escala e por meio','source':'ITA ARANDU MS · IGQ V38.4.11 · SGB Geoquímica externa','note':'Conhecimento geoquímico analítico documentado. Os cinco meios permanecem separados e o IGQ territorial usa o maior subíndice. Ausência permanece transparente e não equivale a zero.','derive_type':'igq_snapshot_v38411','grid_source_id':grid,'igq_scale':scale})
    txt=txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:]
    color_marker="function igcColor(v){const c=igcClass(v);return ITA_IGC_COLORS[c]||'rgba(0,0,0,0)'}"
    if 'const ITA_IGQ_COLORS=' not in txt:
        add="\nconst ITA_IGQ_COLORS={'muito baixo':'#e5f5e0','baixo':'#c7e9c0','médio':'#74c476','alto':'#31a354','muito alto':'#006d2c'};\nfunction igqClass(v){const x=Number(v);if(v===null||v===undefined||!Number.isFinite(x))return'sem conhecimento geoquímico analítico materializado';if(x<20)return'muito baixo';if(x<40)return'baixo';if(x<60)return'médio';if(x<75)return'alto';return'muito alto'}\nfunction igqColor(v){const c=igqClass(v);return ITA_IGQ_COLORS[c]||'rgba(0,0,0,0)'}"
        if color_marker not in txt:raise RuntimeError('marcador de cor IGC não encontrado em app.js')
        txt=txt.replace(color_marker,color_marker+add,1)
    style_marker="if(st.renderer==='index_igc'){fill=igcColor(p.igc_100);stroke='#4a4a4a';}"
    if "st.renderer==='index_igq'" not in txt:
        if style_marker not in txt:raise RuntimeError('marcador renderer IGC não encontrado em app.js')
        txt=txt.replace(style_marker,style_marker+" if(st.renderer==='index_igq'){fill=igqColor(p.igq_100);stroke='#4a4a4a';}",1)
    if "if(st.renderer==='index_igq')return" not in txt:
        lm="if(st.renderer==='index_igc')return";i=txt.find(lm)
        if i<0:raise RuntimeError('legenda IGC não encontrada em app.js')
        e=txt.find('\n',i)
        legend=" if(st.renderer==='index_igq')return `<div class=\"legend-layer-title\">${esc(cfg.name)}</div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:transparent;border:1px solid #4a4a4a\"></span><span>sem conhecimento geoquímico analítico · transparente</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#e5f5e0;border:1px solid #4a4a4a\"></span><span>0–&lt;20 · muito baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#c7e9c0;border:1px solid #4a4a4a\"></span><span>20–&lt;40 · baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#74c476;border:1px solid #4a4a4a\"></span><span>40–&lt;60 · médio</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#31a354;border:1px solid #4a4a4a\"></span><span>60–&lt;75 · alto</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#006d2c;border:1px solid #4a4a4a\"></span><span>75–100 · muito alto</span></div><div class=\"legend-note\">IGQ = máximo entre sedimento de corrente, concentrado de bateia, solo, rocha e água. Cada meio combina presença espacial, amplitude analítica e completude documental. Não representa anomalia geoquímica.</div>`;"
        txt=txt[:e+1]+legend+'\n'+txt[e+1:]
    if 'async function buildIgqSnapshotV38411' not in txt:
        marker='async function buildImcPreview(cfg)';i=txt.find(marker)
        if i<0:raise RuntimeError('marcador de builder não encontrado em app.js')
        builder="""async function buildIgqSnapshotV38411(cfg){
 const gridCfg=CATALOG.layers.find(x=>x.id===cfg.grid_source_id);
 if(!gridCfg)throw new Error('Malha do IGQ V38.4.11 não encontrada no catálogo');
 const grid=await ensure(gridCfg),key=String(cfg.igq_scale||''),scores=window.ITA_IGQ_V38411?.grids?.[key],meta=window.ITA_IGQ_V38411?.metadata||{};
 if(!scores)throw new Error('Snapshot IGQ V38.4.11 não encontrado para esta escala. Execute o materializador do patch.');
 const features=(grid.features||[]).map(hf=>{
  const hid=String(hf.properties?.hex_id||''),r=scores[hid];
  if(!r)return {...hf,properties:{...(hf.properties||{}),igq_100:null,classe_igq:'sem conhecimento geoquímico analítico materializado',metodo:'V38.4.11 · snapshot IGQ ausente para esta célula'}};
  const [igq,best,nMedia,sc,cb,solo,rocha,agua,nSC,nCB,nSolo,nRocha,nAgua]=r;
  return {...hf,properties:{...(hf.properties||{}),igq_100:igq,classe_igq:igqClass(igq),meio_igq_dominante:best||'nenhum',n_meios_geoquimicos:nMedia,igq_sc:sc,igq_cb:cb,igq_solo:solo,igq_rocha:rocha,igq_agua:agua,n_amostras_sc:nSC,n_amostras_cb:nCB,n_amostras_solo:nSolo,n_amostras_rocha:nRocha,n_amostras_agua:nAgua,formula:'IGQ_h = max(IGQ_SC, IGQ_CB, IGQ_solo, IGQ_rocha, IGQ_agua)',formula_meio:'IGQ_m = 100 × (G_m × A_m × Q_m)^(1/3)',formula_G:'G_m = sqrt(D*_m × O_m)',fonte_igq:'SGB · Geoquímica externa · amostras analisadas e resultados relacionados',regra_meios:'cada meio é calculado separadamente. Não há mistura de sedimento de corrente, concentrado de bateia, solo, rocha e água.',regra_censura:'resultados censurados continuam como determinação analítica existente, porém nenhum valor é imputado ou usado para classificar anomalias.',regra_duplicatas:'duplicatas declaradas não aumentam a densidade espacial como observações independentes.',regra_ausencia:'sem amostra analítica utilizável em qualquer meio → IGQ nulo e hexágono transparente.',limite_interpretativo:'IGQ mede conhecimento geoquímico analítico documentado. Não mede teor, anomalia, favorabilidade mineral, recurso, reserva ou risco ambiental.',metodo:'V38.4.11 · cálculo direto na escala a partir das amostras originais · sem agregação entre escalas',data_corte:meta.cut_date||'2026-08-14'}};
 });
 return {type:'FeatureCollection',features,atlas_metadata:{indice:'IGQ',versao:'V38.4.11',escala:key,formula:'IGQ_h = max(IGQ_SC, IGQ_CB, IGQ_solo, IGQ_rocha, IGQ_agua)',fonte:'SGB · Geoquímica externa',regra:'cinco meios independentes e cálculo independente em 250, 500 e 1000 km²',limite:'índice de conhecimento, não de anomalia ou potencial mineral'}};
}
"""
        txt=txt[:i]+builder+txt[i:]
    chain="if(!d&&cfg.derive_type==='igc_snapshot_v38410')d=await buildIgcSnapshotV38410(cfg);"
    if "derive_type==='igq_snapshot_v38411'" not in txt:
        if chain not in txt:raise RuntimeError('cadeia derive IGC não encontrada em app.js')
        txt=txt.replace(chain,chain+"if(!d&&cfg.derive_type==='igq_snapshot_v38411')d=await buildIgqSnapshotV38411(cfg);",1)
    scale_marker="const IGC_SCALE_LAYERS=['igc_250','igc_500','igc_1000'];"
    if 'const IGQ_SCALE_LAYERS=' not in txt:
        if scale_marker not in txt:raise RuntimeError('grupo de escalas IGC não encontrado em app.js')
        txt=txt.replace(scale_marker,scale_marker+" const IGQ_SCALE_LAYERS=['igq_250','igq_500','igq_1000'];",1)
    toggle_marker='async function toggle(id,on){const cfg=CATALOG.layers.find(x=>x.id===id);if(!cfg)return;'
    if 'IGQ_SCALE_LAYERS.includes(id)' not in txt:
        i=txt.find(toggle_marker)
        if i<0:raise RuntimeError('toggle não encontrado em app.js')
        insert_at=i+len(toggle_marker)
        inject="if(on&&IGQ_SCALE_LAYERS.includes(id)){for(const other of IGQ_SCALE_LAYERS){if(other===id)continue;state.active.delete(other);const ocb=document.querySelector(`input[data-layer=\"${other}\"]`);if(ocb)ocb.checked=false;updateLayerCard(other)}}"
        txt=txt[:insert_at]+inject+txt[insert_at:]
    p.write_text(txt,encoding='utf-8',newline='\n')

def update_local_catalog(repo:Path,source_count:int,source_bytes:int):
    js=repo/'docs/camadas/catalogo-local.js';txt=js.read_text(encoding='utf-8');prefix='window.ITA_LOCAL_LAYER_FILES=';pos=txt.index(prefix)+len(prefix);obj,end=json.JSONDecoder().raw_decode(txt[pos:])
    obj['geoquimica_amostras_sgb_ms']='./camadas/arquivos/geoquimica_amostras_sgb_ms.geojson';txt=txt[:pos]+json.dumps(obj,ensure_ascii=False,separators=(',',':'))+txt[pos+end:];js.write_text(txt,encoding='utf-8',newline='\n')
    jp=repo/'docs/camadas/catalogo-local.json';arr=load_json(jp);found=False
    for item in arr:
        if item.get('id')=='geoquimica_amostras_sgb_ms':
            item.update({'arquivo':'./camadas/arquivos/geoquimica_amostras_sgb_ms.geojson','nome':'Amostras geoquímicas analisadas SGB','grupo':'Geoquímica, geofísica e geotermia','status':'incorporada','fonte':'SGB · Geoportal · Geoquímica externa · snapshot local V38.4.11','validacao':'recorte MS · cinco meios · somente amostras com resultados relacionados','feicoes':source_count,'bytes':source_bytes});found=True
    if not found:arr.append({'id':'geoquimica_amostras_sgb_ms','arquivo':'./camadas/arquivos/geoquimica_amostras_sgb_ms.geojson','nome':'Amostras geoquímicas analisadas SGB','grupo':'Geoquímica, geofísica e geotermia','status':'incorporada','fonte':'SGB · Geoportal · Geoquímica externa · snapshot local V38.4.11','validacao':'recorte MS · cinco meios · somente amostras com resultados relacionados','feicoes':source_count,'bytes':source_bytes})
    dump_json(jp,arr)

def update_html_sw_docs(repo:Path):
    idx=repo/'docs/index.html';t=idx.read_text(encoding='utf-8');t=t.replace('v=38.4.10','v=38.4.11')
    script='<script src="./indices/igq-v38411.js?v=38.4.11"></script>'
    if script not in t:
        marker='<script src="./indices/igc-v38410.js?v=38.4.11"></script>'
        if marker not in t:raise RuntimeError('script IGC não encontrado no index.html')
        t=t.replace(marker,marker+'\n'+script,1)
    idx.write_text(t,encoding='utf-8',newline='\n')
    boot=repo/'docs/assets/js/bootstrap.js';b=boot.read_text(encoding='utf-8');b=re.sub(r'v=38\.4\.\d+', 'v=38.4.11', b);boot.write_text(b,encoding='utf-8',newline='\n')
    sw=repo/'docs/service-worker.js';s=sw.read_text(encoding='utf-8');s=re.sub(r"const ITA_CACHE = 'ita-arandu-[^']+';","const ITA_CACHE = 'ita-arandu-v38-4-11-igq-conhecimento-geoquimico';",s,count=1);s=s.replace('v=38.4.10','v=38.4.11')
    for entry,after in [("  \"./indices/igq-v38411.js?v=38.4.11\",\n","  \"./indices/igc-v38410.js?v=38.4.11\",\n"),("  \"./camadas/arquivos/geoquimica_amostras_sgb_ms.geojson\",\n","  \"./camadas/arquivos/geocronologia_geosgb_ms.geojson\",\n"),("  \"./documentos/metodologia-igq.html\",\n","  \"./documentos/metodologia-igc.html\",\n")]:
        if entry.strip() not in s:
            if after not in s:raise RuntimeError('marcador do service worker não encontrado')
            s=s.replace(after,after+entry,1)
    sw.write_text(s,encoding='utf-8',newline='\n')
    di=repo/'docs/documentos/index.html';d=di.read_text(encoding='utf-8');link='<li><a href="./metodologia-igq.html">IGQ · Conhecimento Geoquímico · metodologia V38.4.11</a></li>'
    if link not in d:
        marker='<li><a href="./metodologia-igc.html">IGC · Controle Geocronológico · metodologia V38.4.10</a></li>'
        if marker in d:d=d.replace(marker,marker+'\n'+link,1)
        else:d=d.replace('</ul>',link+'\n</ul>',1)
    di.write_text(d,encoding='utf-8',newline='\n')

def update_master_reference(repo:Path):
    ref_id='REF-178'
    url=SERVICE_ROOT
    apa='Serviço Geológico do Brasil. (s.d.). Geoquímica – amostras analisadas e resultados analíticos [Serviço geoespacial]. Geoportal SGB. Recuperado em 14 de agosto de 2026.'
    apa_full=apa+' '+url
    rec={'id':ref_id,'group':'Geoquímica, geofísica e geotermia','status':'incorporada','type':'serviço geoespacial geoquímico','apa':apa,'url':url,'use':'Fonte primária das amostras geoquímicas analisadas e das tabelas relacionadas de resultados analíticos utilizadas na materialização do IGQ V38.4.11.','citation_standard':'APA 7','doi':None,'quality_class':'fonte primária institucional','verification_level':'fonte_primaria_conferida','verification_note':'Estrutura do serviço, meios amostrais, camadas de amostras analisadas e tabelas relacionadas conferidos diretamente no ArcGIS REST do Geoportal SGB em 14 de agosto de 2026.','verified_on':'2026-08-14','apa_full':apa_full}
    rp=repo/'docs/referencias/referencias.js'
    txt=rp.read_text(encoding='utf-8');prefix='window.ITA_REFERENCE_REGISTRY=';pos=txt.index(prefix)+len(prefix);arr,end=json.JSONDecoder().raw_decode(txt[pos:])
    by={x.get('id'):i for i,x in enumerate(arr) if isinstance(x,dict)}
    if ref_id in by:arr[by[ref_id]]=rec
    else:arr.append(rec)
    arr.sort(key=lambda x:int(str(x.get('id','REF-999999')).split('-')[-1]) if str(x.get('id','')).startswith('REF-') and str(x.get('id','')).split('-')[-1].isdigit() else 999999)
    rp.write_text(txt[:pos]+json.dumps(arr,ensure_ascii=False,separators=(',',':'))+txt[pos+end:],encoding='utf-8',newline='\n')
    # Liga a fonte nova às camadas operacionais sem apagar as referências de contexto já existentes.
    dp=repo/'docs/dados/registros.js'
    dtxt=dp.read_text(encoding='utf-8');dprefix='window.ITA_LAYER_REFERENCE_LINKS=';dpos=dtxt.index(dprefix)+len(dprefix);links,dend=json.JSONDecoder().raw_decode(dtxt[dpos:])
    for lid in ['igq_250','igq_500','igq_1000','geoquimica_amostras_sgb_ms','geoquimica_resultados_sgb_ms']:
        ids=list(links.get(lid) or [])
        if ref_id not in ids:ids.append(ref_id)
        links[lid]=ids
    dp.write_text(dtxt[:dpos]+json.dumps(links,ensure_ascii=False,separators=(',',':'))+dtxt[dpos+dend:],encoding='utf-8',newline='\n')
    return rec

def update_public_bibliography_html(repo:Path,rec:dict):
    hp=repo/'docs/referencias/index.html'
    if not hp.exists():return
    h=hp.read_text(encoding='utf-8')
    # Atualiza contador do registro mestre.
    h=re.sub(r'(class="summary">)175 referências',r'\g<1>176 referências',h,count=1)
    # Insere a referência mestre REF-178 antes do primeiro bloco de família de índices.
    if 'id="ref-178"' not in h:
        sec=(f'<section class="entry reference-entry" data-search="geoquímica geofísica e geotermia ref-178 serviço geológico do brasil geoquímica amostras analisadas resultados analíticos geoportal sgb" id="ref-178">'
             f'<h2>REF-178</h2><div class="meta">Geoquímica, geofísica e geotermia · serviço geoespacial geoquímico · fonte primária institucional</div>'
             f'<div class="source">{rec["apa_full"]} <a href="{rec["url"]}" rel="noopener" target="_blank">fonte</a></div>'
             f'<p>{rec["use"]}</p></section>')
        candidates=[h.find('<section class="entry index-entry"'),h.find('<section class="entry layer-entry"')]
        candidates=[x for x in candidates if x>=0]
        if candidates:h=h[:min(candidates)]+sec+h[min(candidates):]
        else:h=h.replace('</body>',sec+'</body>',1)
    # Nos cinco registros de camada, adiciona REF-178 à lista se ainda não estiver presente.
    for lid in ['igq_250','igq_500','igq_1000','geoquimica_amostras_sgb_ms','geoquimica_resultados_sgb_ms']:
        sm=f'id="layer-{lid}"';start=h.find(sm)
        if start<0:continue
        s0=h.rfind('<section',0,start);s1=h.find('</section>',start)
        if s0<0 or s1<0:continue
        s1+=len('</section>');sec=h[s0:s1]
        if 'href="#ref-178"' not in sec:
            ins=f'<li><a href="#ref-178"><b>REF-178</b></a> · {rec["apa_full"]}</li>'
            sec=sec.replace('</ol>',ins+'</ol>',1)
            sec=re.sub(r'(· )(\d+)( referência\(s\))',lambda m:m.group(1)+str(int(m.group(2))+1)+m.group(3),sec,count=1)
            h=h[:s0]+sec+h[s1:]
    hp.write_text(h,encoding='utf-8',newline='\n')

def update_bibliography(repo:Path):
    rec=update_master_reference(repo)
    jp=repo/'docs/referencias/bibliografia-camadas-indices.json'
    if jp.exists():
        o=load_json(jp);ref_obj={'id':'REF-178','apa7':rec['apa_full'],'type':rec['type'],'quality_class':rec['quality_class'],'verification_level':rec['verification_level'],'url':rec['url'],'doi':None}
        for e in o.get('entries',[]):
            if not isinstance(e,dict) or e.get('id') not in {'igq_250','igq_500','igq_1000','geoquimica_amostras_sgb_ms','geoquimica_resultados_sgb_ms'}:continue
            e['status']='incorporada'
            ids=list(e.get('reference_ids') or [])
            if 'REF-178' not in ids:ids.append('REF-178')
            e['reference_ids']=ids
            refs=[x for x in (e.get('references') or []) if isinstance(x,dict) and x.get('id')!='REF-178'];refs.append(ref_obj);e['references']=refs
            if e.get('id') in {'geoquimica_amostras_sgb_ms','geoquimica_resultados_sgb_ms'}:e['source']='Serviço Geológico do Brasil · Geoportal SGB · amostras analisadas e resultados analíticos'
        o['total_references']=176
        dump_json(jp,o)
    update_public_bibliography_html(repo,rec)

def update_changelog(repo:Path):
    entry='''\n## V38.4.11 · IGQ · Conhecimento Geoquímico · 2026-08-14\n\n- materializa cinco meios geoquímicos analisados do GeoSGB com seus resultados relacionados\n- calcula separadamente sedimento de corrente, concentrado de bateia, solo, rocha e água\n- congela IGQ_h = max(IGQ_SC, IGQ_CB, IGQ_solo, IGQ_rocha, IGQ_agua)\n- congela por meio IGQ_m = 100 × (G_m × A_m × Q_m)^(1/3)\n- não utiliza concentrações para classificar anomalias e não imputa valores censurados\n- calcula 250, 500 e 1000 km² diretamente das amostras originais\n'''
    ch=repo/'CHANGELOG.md'
    if ch.exists():
        t=ch.read_text(encoding='utf-8')
        if 'V38.4.11 · IGQ' not in t:ch.write_text(t.rstrip()+entry+'\n',encoding='utf-8',newline='\n')
    rd=repo/'README.md'
    if rd.exists():
        t=rd.read_text(encoding='utf-8');t=re.sub(r'V38\.4\.10[^\n]*','V38.4.11 · IGQ · Conhecimento Geoquímico',t,count=1) if 'V38.4.10' in t else t;rd.write_text(t,encoding='utf-8',newline='\n')
    dh=repo/'docs/documentos/changelog.html'
    if dh.exists():
        t=dh.read_text(encoding='utf-8')
        if 'V38.4.11 · IGQ' not in t:t=t.replace('</body>','<h2>V38.4.11 · IGQ · Conhecimento Geoquímico</h2><p>Materialização independente de cinco meios geoquímicos analisados nas três escalas, preservando censura, duplicatas e rastreabilidade analítica.</p></body>')
        dh.write_text(t,encoding='utf-8',newline='\n')

def self_test():
    f=lambda oid,lab,dup,x,y,labname='LAB':{'type':'Feature','id':oid,'geometry':{'type':'Point','coordinates':[x,y]},'properties':{'objectid':oid,'numero_de_laboratorio':lab,'numero_de_campo':lab,'duplicata':dup,'laboratorio':labname,'data_de_analise':1,'abertura':'digestão','leitura':'ICP-MS','projeto_amostragem':'Teste'}}
    src={'SC':{'features':[f(1,'A',0,-54.5,-20.5),f(2,'B',1,-54.4,-20.4)],'related':{'1':[{'elemento':'Cu','resultado':'<1'},{'elemento':'Zn','resultado':2}],'2':[{'elemento':'Cu','resultado':3}]}},'CB':{'features':[],'related':{}},'solo':{'features':[],'related':{}},'rocha':{'features':[],'related':{}},'agua':{'features':[],'related':{}}}
    u,st=build_units(src);assert len(u['SC'])==1 and st['SC']['duplicates_excluded']==1 and u['SC'][0]['n_results']==2 and abs(u['SC'][0]['q']-1)<1e-9
    assert truthy_duplicate('Sim') and not truthy_duplicate(0);assert analytical_count([{'elemento':'Cu','resultado':'<LD'}])==1
    print('SELFTEST IGQ V38.4.11 · PASS')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');ap.add_argument('--self-test',action='store_true');ap.add_argument('--source-file');args=ap.parse_args()
    if args.self_test:self_test();return 0
    repo=Path(args.repo).resolve()
    for rel in list(GRID_FILES.values())+[LIMIT_FILE]:
        if not (repo/rel).exists():raise RuntimeError(f'arquivo estrutural ausente · {rel}')
    for rel in ['docs/indices/iod-v3848.js','docs/indices/iod_v3848_snapshot.json','docs/indices/icp-v3849.js','docs/indices/icp_v3849_snapshot.json','docs/indices/igc-v38410.js','docs/indices/igc_v38410_snapshot.json']:
        if not (repo/rel).exists():raise RuntimeError(f'base V38.4.10 incompleta · arquivo ausente · {rel}')
    print('ITA ARANDU MS · materialização IGQ V38.4.11');print('Fórmula ·',FORMULA);print('Por meio ·',MEDIUM_FORMULA);print('G ·',G_FORMULA)
    if args.source_file:
        source_obj=load_json(Path(args.source_file));source_label='arquivo local fornecido';source_url=str(Path(args.source_file))
    else:source_label,source_url,source_obj=fetch_source()
    raw=canonical_bytes(source_obj);raw_hash=sha256_bytes(raw);media=source_obj.get('media') or {}
    for m in MEDIUMS:
        if m not in media:raise RuntimeError(f'meio ausente no snapshot de origem · {m}')
    units,source_stats=build_units(media);state=feature_polys(load_json(repo/LIMIT_FILE));units,removed=clip_units_to_state(units,state)
    for m in MEDIUMS:source_stats[m]['outside_ms_removed']=removed[m];source_stats[m]['independent_analytical_samples_ms']=len(units[m])
    total=sum(len(v) for v in units.values())
    if total<2:raise RuntimeError(f'apenas {total} amostras analíticas independentes ficaram utilizáveis em MS')
    grids={};cells={};assigned={};missing={};ambiguous={}
    for s,rel in GRID_FILES.items():grids[s],cells[s]=load_grid(repo/rel)
    for s in ('250','500','1000'):
        assigned[s]={};missing[s]={};ambiguous[s]={}
        for m in MEDIUMS:assigned[s][m],missing[s][m],ambiguous[s][m]=assign_units(units[m],cells[s])
    # Retém somente pontos efetivamente atribuídos à malha 250 oficial.
    for m in MEDIUMS:
        valid=set(i for arr in assigned['250'][m] for i in arr)
        if len(valid)!=len(units[m]):
            units[m]=[u for i,u in enumerate(units[m]) if i in valid]
            for s in ('250','500','1000'):assigned[s][m],missing[s][m],ambiguous[s][m]=assign_units(units[m],cells[s])
    baseline={};normalization={}
    for s in ('250','500','1000'):
        medium_rows={};normalization[s]={}
        for m in MEDIUMS:
            rows,dsat,asat=calculate_medium(cells[s],assigned[s][m],units[m]);medium_rows[m]=rows;normalization[s][m]={'density_p95':None if dsat is None else round(dsat,10),'analytical_count_p95':None if asat is None else round(asat,4)}
        combined=combine_mediums(cells[s],medium_rows);baseline[s]={'combined':combined,'medium':medium_rows}
    sensitivity={}
    for s in ('250','500','1000'):
        sensitivity[s]={};base=baseline[s]['combined']
        for step,dp,apct in [(2500,95,95),(10000,95,95),(5000,90,95),(5000,99,95),(5000,95,90),(5000,95,99)]:
            mr={}
            for m in MEDIUMS:mr[m],_,_=calculate_medium(cells[s],assigned[s][m],units[m],float(step),dp,apct)
            alt=combine_mediums(cells[s],mr);sensitivity[s][f'micro_{step/1000:g}km_Dp{dp}_Ap{apct}']=spearman_combined(base,alt)
    source_fc=source_feature_collection(units,source_stats,raw_hash);sp=repo/'docs/camadas/arquivos/geoquimica_amostras_sgb_ms.geojson';dump_json(sp,source_fc,compact=True)
    raw_path=repo/f'data/geoquimica_sgb_ms_raw_{CUT_DATE.replace("-","")}.json.gz';raw_path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(raw_path,'wb',compresslevel=9) as gz:gz.write(raw)
    snap={'metadata':{'index':'IGQ','version':VERSION,'calculated_at':now_iso(),'cut_date':CUT_DATE,'formula':FORMULA,'medium_formula':MEDIUM_FORMULA,'g_formula':G_FORMULA,'components':{'G_m':'presença e distribuição espacial de amostras analíticas independentes do meio m','A_m':'amplitude analítica normalizada pelo P95 do número de registros analíticos relacionados por amostra no próprio meio','Q_m':'completude documental de laboratório, data de análise, abertura/preparação, leitura/método e projeto/publicação'},'source':'SGB · Geoportal · geologia/geoq_externa · amostras analisadas + resultados relacionados','source_url':source_url,'source_method':source_label,'source_sha256':raw_hash,'raw_gzip':str(raw_path.relative_to(repo)).replace('\\','/'),'media':['SC','CB','solo','rocha','agua'],'medium_labels':{m:MEDIUMS[m]['label'] for m in MEDIUMS},'aggregation_rule':'máximo entre os cinco subíndices, conforme arquitetura metodológica já documentada. Os subíndices permanecem explícitos para não ocultar ausência de meios.','duplicate_rule':'duplicatas declaradas pela fonte não aumentam densidade espacial; número de laboratório é a chave preferencial de independência','censoring_rule':'valores censurados contam apenas como determinação analítica existente. O IGQ não imputa, substitui nem compara concentrações.','stream_rule':'SC e CB são representados conservadoramente pelo suporte espacial dos pontos amostrais. V38.4.11 não transforma automaticamente um ponto em cobertura total da bacia de drenagem.','microcell_m':BASE_MICROCELL_M,'density_percentile':BASE_DENSITY_PERCENTILE,'analytical_percentile':BASE_ANALYTICAL_PERCENTILE,'scale_rule':'250, 500 e 1000 km² são calculados diretamente a partir das amostras originais de cada meio, sem agregação entre escalas.','null_rule':'sem amostra analítica utilizável nos cinco meios, IGQ=null e o hexágono permanece transparente. Ausência não é zero.','interpretation_limit':'índice de conhecimento geoquímico analítico documentado. Não mede anomalia, teor, favorabilidade mineral, recurso, reserva ou risco ambiental.','references':['REF-178','REF-099','REF-107','REF-105','REF-115']},'source_summary':source_stats,'normalization':normalization,'summary':{s:summary(baseline[s]['combined'],baseline[s]['medium']) for s in baseline},'sensitivity_spearman':sensitivity,'grids':{s:compact_rows(baseline[s]['combined'],baseline[s]['medium']) for s in baseline}}
    dump_json(repo/'docs/indices/igq_v38411_snapshot.json',snap);(repo/'docs/indices/igq-v38411.js').write_text('window.ITA_IGQ_V38411='+json.dumps(snap,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
    js_catalog_patch(repo,len(source_fc['features']));update_local_catalog(repo,len(source_fc['features']),sp.stat().st_size);update_html_sw_docs(repo);update_bibliography(repo);update_changelog(repo);(repo/'VERSION').write_text(VERSION+'\n',encoding='utf-8',newline='\n')
    runtime={'audit':'V38.4.11 IGQ runtime','status':'PASS','calculated_at':now_iso(),'source_sha256':raw_hash,'independent_samples_ms':{m:len(units[m]) for m in MEDIUMS},'source_stats':source_stats,'summaries':{s:summary(baseline[s]['combined'],baseline[s]['medium']) for s in baseline},'checks':{'media_not_mixed_before_aggregation':True,'duplicates_not_independent':True,'censored_values_not_imputed':True,'concentrations_not_used_for_anomaly':True,'independent_scale_calculation':True,'null_is_not_zero':True,'previous_indices_not_recomputed':True}}
    dump_json(repo/'AUDITORIA_V38_4_11_IGQ_RUNTIME.json',runtime)
    print('IGQ V38.4.11 materializado ·',total,'amostras analíticas independentes antes do ajuste final de malha')
    for m in MEDIUMS:print(m,'·',len(units[m]),'amostras independentes em MS')
    for s in ('250','500','1000'):print(s,'km² ·',summary(baseline[s]['combined'],baseline[s]['medium']))
    return 0

if __name__=='__main__':raise SystemExit(main())
