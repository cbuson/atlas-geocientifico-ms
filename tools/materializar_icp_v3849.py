#!/usr/bin/env python3
# ITA ARANDU MS · V38.4.9 · materialização do ICP
# Biblioteca padrão apenas. Não altera resultados de outros índices.
from __future__ import annotations
import argparse, datetime as dt, gzip, hashlib, json, math, statistics, sys, urllib.parse, urllib.request
from pathlib import Path

VERSION='V38.4.9-ICP-CARACTERIZACAO-PETROGRAFICA-20260814'
CUT_DATE='2026-08-14'
FORMULA='ICP_h = 100 × (P × U × Q)^(1/3)'
P_FORMULA='P = sqrt(D* × O)'
BASE_MICROCELL_M=5000.0
BASE_DENSITY_PERCENTILE=95
SUPPORT_N=9
LAEA_LON0=-54.5
LAEA_LAT0=-20.5
EARTH_R=6371007.181
BBOX_MS=(-58.3,-24.3,-50.6,-17.0)
SERVICE='https://geoportal.sgb.gov.br/server/rest/services/geologia/petrografia/MapServer/0'
GRID_FILES={
 '250':'docs/camadas/arquivos/malha_r5_250km2.geojson',
 '500':'docs/camadas/arquivos/malha_500km2.geojson',
 '1000':'docs/camadas/arquivos/malha_1000km2.geojson',
}
LIMIT_FILE='docs/camadas/arquivos/limite_ms_ibge_2025.geojson'
GEOLOGY_FILE='docs/camadas/arquivos/mapa_geologico_ms.geojson'


def now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def load_json(path:Path):
    with path.open('r',encoding='utf-8') as f:return json.load(f)

def dump_json(path:Path,obj,compact=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,ensure_ascii=False,separators=(',',':') if compact else None,indent=None if compact else 2)
        f.write('\n')

def canonical_bytes(obj):
    return json.dumps(obj,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode('utf-8')

def sha256_bytes(data:bytes):return hashlib.sha256(data).hexdigest()

def fetch_json(url,timeout=120):
    req=urllib.request.Request(url,headers={'User-Agent':'ITA-ARANDU-MS/38.4.9 Python urllib','Accept':'application/json, application/geo+json;q=0.9, */*;q=0.1'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8-sig'))

def service_query(params):
    return SERVICE+'/query?'+urllib.parse.urlencode(params,safe=',')

def fetch_source():
    xmin,ymin,xmax,ymax=BBOX_MS
    common={
      'where':'1=1','geometry':f'{xmin},{ymin},{xmax},{ymax}','geometryType':'esriGeometryEnvelope',
      'inSR':'4326','spatialRel':'esriSpatialRelIntersects','f':'json'
    }
    id_obj=fetch_json(service_query({**common,'returnIdsOnly':'true'}))
    if id_obj.get('error'):raise RuntimeError(str(id_obj['error']))
    ids=id_obj.get('objectIds') or []
    if not ids:raise RuntimeError('GeoSGB Petrografia não retornou identificadores no envelope de MS')
    feats=[]
    batch=250
    for i in range(0,len(ids),batch):
        part_ids=ids[i:i+batch]
        params={
          'where':'1=1','objectIds':','.join(str(x) for x in part_ids),'outFields':'*',
          'returnGeometry':'true','outSR':'4326','f':'geojson'
        }
        obj=fetch_json(service_query(params))
        if obj.get('error'):raise RuntimeError(str(obj['error']))
        fs=obj.get('features') or []
        if not isinstance(fs,list):raise RuntimeError('lote GeoSGB sem FeatureCollection utilizável')
        feats.extend(fs)
    if len(feats)<10:raise RuntimeError(f'GeoSGB Petrografia retornou apenas {len(feats)} registros no envelope')
    # Dedup de linha por OBJECTID, pois lotes podem ser repetidos por serviço intermediário.
    seen=set(); clean=[]
    for f in feats:
        p=f.get('properties') or {}; oid=p.get('OBJECTID',f.get('id'))
        key=('oid',str(oid)) if oid not in (None,'') else ('raw',json.dumps([f.get('geometry'),p],ensure_ascii=False,sort_keys=True))
        if key in seen:continue
        seen.add(key);clean.append(f)
    obj={'type':'FeatureCollection','features':clean,'atlas_fetch':{'service':SERVICE,'query_mode':'returnIdsOnly + objectIds em lotes','ids_bbox':len(ids),'retrieved':len(clean)}}
    return 'ArcGIS REST GeoSGB · consulta por IDs em lotes',SERVICE,obj


def ci_get(props,*names):
    if not isinstance(props,dict):return None
    low={str(k).lower():v for k,v in props.items()}
    for n in names:
        if n in props:return props[n]
        if str(n).lower() in low:return low[str(n).lower()]
    return None

def nonempty(v):
    if v is None:return False
    if isinstance(v,str):return bool(v.strip()) and v.strip().lower() not in {'null','none','nan','não informado','nao informado'}
    return True

def get_point(feat):
    g=feat.get('geometry') or {}
    if g.get('type')=='Point' and isinstance(g.get('coordinates'),list) and len(g['coordinates'])>=2:
        try:return float(g['coordinates'][0]),float(g['coordinates'][1])
        except Exception:pass
    p=feat.get('properties') or {}
    try:return float(ci_get(p,'X','LONGITUDE','LON')),float(ci_get(p,'Y','LATITUDE','LAT'))
    except Exception:return None

_lon0=math.radians(LAEA_LON0);_lat0=math.radians(LAEA_LAT0);_sin0=math.sin(_lat0);_cos0=math.cos(_lat0)
def laea(lon,lat):
    lam=math.radians(lon);phi=math.radians(lat);dl=lam-_lon0;sp=math.sin(phi);cp=math.cos(phi)
    den=1+_sin0*sp+_cos0*cp*math.cos(dl)
    if den<=1e-15:raise ValueError('coordenada antipodal à projeção')
    k=math.sqrt(2/den)
    return EARTH_R*k*cp*math.sin(dl),EARTH_R*k*(_cos0*sp-_sin0*cp*math.cos(dl))

def point_on_segment(pt,a,b,tol=.05):
    x,y=pt;x1,y1=a;x2,y2=b;dx=x2-x1;dy=y2-y1;l2=dx*dx+dy*dy
    if l2==0:return (x-x1)**2+(y-y1)**2<=tol*tol
    t=((x-x1)*dx+(y-y1)*dy)/l2
    if t<0 or t>1:return False
    px=x1+t*dx;py=y1+t*dy
    return (x-px)**2+(y-py)**2<=tol*tol

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
        g=f.get('geometry') or {};typ=g.get('type');coords=g.get('coordinates')
        parts=[coords] if typ=='Polygon' else (coords if typ=='MultiPolygon' else [])
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
    cand=index.get((math.floor(pt[0]/bin_m),math.floor(pt[1]/bin_m)),[])
    hits=[]
    for i in cand:
        b=items[i]['bbox']
        if pt[0]<b[0]-.1 or pt[0]>b[2]+.1 or pt[1]<b[1]-.1 or pt[1]>b[3]+.1:continue
        if point_in_geom_projected(pt,items[i]['geom']):hits.append(i)
    return hits[0] if hits else None

def clip_to_state(features,state_items):
    idx,bin_m=make_spatial_index(state_items,100000.0);kept=[];invalid=0;outside=0
    for f in features:
        pt=get_point(f)
        if pt is None:invalid+=1;continue
        if not (-61<=pt[0]<=-47 and -27<=pt[1]<=-15):invalid+=1;continue
        pxy=laea(*pt)
        if find_poly(pxy,state_items,idx,bin_m) is None:outside+=1;continue
        kept.append(f)
    return kept,{'invalid_geometry_removed':invalid,'outside_ms_removed':outside}

def q_blocks(props):
    blocks={
      'amostra':nonempty(ci_get(props,'COD_AMOSTRA','NUM_CAMPO_AMOSTRA')),
      'lamina':nonempty(ci_get(props,'COD_LAMINA','NUM_CAMPO_LAMINA','NUM_LAB_LAMINA')),
      'classificacao':nonempty(ci_get(props,'ROCHA','COD_CLASSIFICACAO','PROTOLITO')),
      'mineralogia':nonempty(ci_get(props,'MINERAIS_IDENTIFICADOS')),
      'secao':nonempty(ci_get(props,'TIPO_SECAO')),
      'responsavel':nonempty(ci_get(props,'PETROGRAFO')),
      'contexto':nonempty(ci_get(props,'PROJETO','BASE_CARTOGRAFICA')),
      'documentacao':nonempty(ci_get(props,'FICHA','LINK','NOTAS')),
    }
    return blocks

def independent_key(feat):
    p=feat.get('properties') or {};pt=get_point(feat) or (None,None)
    afl=ci_get(p,'COD_AFLORAMENTO');rock=ci_get(p,'COD_ROCHA')
    if nonempty(afl) and nonempty(rock):return f'AFLOR_ROCHA:{str(afl).strip()}:{str(rock).strip()}'
    am=ci_get(p,'COD_AMOSTRA')
    if nonempty(am):return f'AMOSTRA:{str(am).strip()}'
    nca=ci_get(p,'NUM_CAMPO_AMOSTRA')
    if nonempty(nca):return 'CAMPO:'+str(nca).strip().upper()
    clas=ci_get(p,'ROCHA','COD_CLASSIFICACAO','PROTOLITO')
    return f'COORD_ROCHA:{round(pt[0],6)}:{round(pt[1],6)}:{str(clas or "SEM_CLASSIFICACAO").strip().upper()}'

def merge_groups(features):
    groups={}
    for f in features:
        k=independent_key(f);p=f.get('properties') or {};b=q_blocks(p)
        g=groups.setdefault(k,{'key':k,'features':[],'blocks':{x:False for x in b},'points':[]})
        g['features'].append(f);g['points'].append(get_point(f))
        for x,v in b.items():g['blocks'][x]=g['blocks'][x] or v
    units=[]
    for k,g in groups.items():
        # representante espacial determinístico pela mediana das coordenadas do grupo
        pts=[p for p in g['points'] if p]
        lon=statistics.median([p[0] for p in pts]);lat=statistics.median([p[1] for p in pts])
        q=sum(1 for v in g['blocks'].values() if v)/len(g['blocks'])
        props={}
        # combina o primeiro valor não vazio de cada atributo oficial sem fabricar conteúdo
        keys=set()
        for f in g['features']:keys.update((f.get('properties') or {}).keys())
        for name in keys:
            for f in g['features']:
                v=(f.get('properties') or {}).get(name)
                if nonempty(v):props[name]=v;break
        units.append({'key':k,'point':(lon,lat),'q':q,'blocks':g['blocks'],'n_records':len(g['features']),'props':props})
    units.sort(key=lambda u:u['key'])
    return units

def geology_records(fc):
    items=[]
    for f in fc.get('features',[]):
        g=f.get('geometry') or {};typ=g.get('type');coords=g.get('coordinates');p=f.get('properties') or {}
        uid=ci_get(p,'ID_UNIDADE_ESTRATIGRAFICA','SIGLA','NOME')
        if uid in (None,''):continue
        parts=[coords] if typ=='Polygon' else (coords if typ=='MultiPolygon' else [])
        for part in parts:
            pg=project_geometry({'type':'Polygon','coordinates':part})
            items.append({'feature':f,'geom':pg,'bbox':pg['bbox'],'uid':str(uid),'sigla':str(ci_get(p,'SIGLA') or ''),'nome':str(ci_get(p,'NOME') or '')})
    return items

def annotate_geology(units,geo_items):
    idx,bin_m=make_spatial_index(geo_items,50000.0);missing=0
    for u in units:
        pt=laea(*u['point']);i=find_poly(pt,geo_items,idx,bin_m)
        if i is None:
            u['geology_uid']=None;u['geology_sigla']='';u['geology_nome']='';missing+=1
        else:
            g=geo_items[i];u['geology_uid']=g['uid'];u['geology_sigla']=g['sigla'];u['geology_nome']=g['nome']
    return missing

def annotate_source_features(features,units):
    gm={u['key']:u for u in units}
    for f in features:
        p=f.setdefault('properties',{});u=gm[independent_key(f)];b=q_blocks(p)
        p['__atlas_chave_independente']=u['key'];p['__atlas_n_registros_grupo']=u['n_records']
        p['__atlas_q_registro']=round(sum(b.values())/len(b),4);p['__atlas_q_grupo']=round(u['q'],4)
        p['__atlas_unidade_geologica_id']=u.get('geology_uid');p['__atlas_unidade_geologica_sigla']=u.get('geology_sigla')
        p['__atlas_unidade_geologica_nome']=u.get('geology_nome');p['__atlas_fonte']='SGB · GeoSGB · Petrografia';p['__atlas_snapshot']=CUT_DATE

def load_grid(path:Path):
    fc=load_json(path);cells=[]
    for f in fc.get('features',[]):
        pg=project_geometry(f['geometry']);p=f.get('properties') or {};hid=str(p.get('hex_id') or '')
        if not hid:raise RuntimeError(f'hexágono sem hex_id em {path.name}')
        try:area=float(p['area_efetiva_ms_km2'])
        except Exception:area=float(p.get('area_nominal_km2') or 0)
        if area<=0:raise RuntimeError(f'área efetiva inválida em {hid}')
        b=pg['bbox'];centroid=((b[0]+b[2])/2,(b[1]+b[3])/2)
        cells.append({'hex_id':hid,'feature':f,'geom':pg,'bbox':b,'centroid':centroid,'area':area})
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
    x=sorted(float(v) for v in vals if math.isfinite(float(v)))
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

def geology_at(pt,geo_items,idx,bin_m):
    i=find_poly(pt,geo_items,idx,bin_m)
    return None if i is None else geo_items[i]['uid']

def support_geology(cell,represented,geo_items,geo_idx,geo_bin,n=SUPPORT_N):
    xmin,ymin,xmax,ymax=cell['bbox'];total=0;rep=0;units=set()
    dx=(xmax-xmin)/n;dy=(ymax-ymin)/n
    for ix in range(n):
        x=xmin+(ix+.5)*dx
        for iy in range(n):
            y=ymin+(iy+.5)*dy
            if not point_in_geom_projected((x,y),cell['geom']):continue
            uid=geology_at((x,y),geo_items,geo_idx,geo_bin)
            if uid is None:continue
            total+=1;units.add(uid)
            if uid in represented:rep+=1
    return rep,total,len(units)

def icp_class(v):
    if v is None:return 'sem caracterização petrográfica materializada'
    if v<20:return 'muito baixo'
    if v<40:return 'baixo'
    if v<60:return 'médio'
    if v<75:return 'alto'
    return 'muito alto'

_U_CACHE={}
def calculate_scale(cells,assigned,units,geo_items,micro_step=BASE_MICROCELL_M,density_percentile=BASE_DENSITY_PERCENTILE,support_n=SUPPORT_N):
    dens=[len(assigned[i])/c['area'] for i,c in enumerate(cells) if assigned[i]]
    sat=percentile(dens,density_percentile)
    if sat is None or sat<=0:raise RuntimeError('não há densidade petrográfica positiva para normalização')
    geo_idx,geo_bin=make_spatial_index(geo_items,50000.0);rows={}
    for ci,c in enumerate(cells):
        inds=assigned[ci];n=len(inds)
        if n==0:
            rows[c['hex_id']]={'icp':None,'P':None,'U':None,'Q':None,'D':None,'O':None,'n':0,'density':0.0,'occupied':0,'micro_support':None,'geo_rep':0,'geo_total':None,'geo_units':0}
            continue
        density=n/c['area'];D=min(1.0,density/sat)
        occ={micro_key(laea(*units[ui]['point']),micro_step) for ui in inds};ms=support_microcells(c,micro_step,occ);O=min(1.0,len(occ)/len(ms)) if ms else 1.0
        P=math.sqrt(max(0,D*O))
        represented={units[ui].get('geology_uid') for ui in inds if units[ui].get('geology_uid')}
        ck=(c['hex_id'],tuple(sorted(represented)),int(support_n))
        if ck in _U_CACHE:grepr,gtotal,gunits=_U_CACHE[ck]
        else:
            grepr,gtotal,gunits=support_geology(c,represented,geo_items,geo_idx,geo_bin,support_n)
            _U_CACHE[ck]=(grepr,gtotal,gunits)
        U=(grepr/gtotal) if gtotal else None
        Q=statistics.fmean(units[ui]['q'] for ui in inds)
        icp=100*((P*U*Q)**(1/3)) if U is not None else None
        rows[c['hex_id']]={'icp':None if icp is None else round(icp,2),'P':round(P,6),'U':None if U is None else round(U,6),'Q':round(Q,6),'D':round(D,6),'O':round(O,6),'n':n,'density':round(density,8),'occupied':len(occ),'micro_support':len(ms),'geo_rep':grepr,'geo_total':gtotal,'geo_units':len(represented)}
    return rows,sat

def summary(rows):
    vals=[r['icp'] for r in rows.values() if r['icp'] is not None];ns=[r['n'] for r in rows.values()]
    return {'cells':len(rows),'cells_with_petrografia':len(vals),'cells_without_petrografia':len(rows)-len(vals),'icp_min':min(vals) if vals else None,'icp_median':round(statistics.median(vals),2) if vals else None,'icp_mean':round(statistics.fmean(vals),2) if vals else None,'icp_max':max(vals) if vals else None,'independent_units_sum':sum(ns),'max_units_cell':max(ns) if ns else 0}

def compact_rows(rows):
    # [ICP,P,U,Q,D,O,n,density,occupied,micro_support,geo_rep,geo_total,geo_units]
    return {k:[v['icp'],v['P'],v['U'],v['Q'],v['D'],v['O'],v['n'],v['density'],v['occupied'],v['micro_support'],v['geo_rep'],v['geo_total'],v['geo_units']] for k,v in rows.items()}

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

def spearman_maps(a,b):
    x=[];y=[]
    for k in a:
        va=a[k]['icp'];vb=b.get(k,{}).get('icp')
        if va is not None and vb is not None:x.append(va);y.append(vb)
    rr=pearson(rankdata(x),rankdata(y)) if len(x)>=2 else None
    return {'n_common':len(x),'rho':None if rr is None else round(rr,6)}

def update_catalog_files(repo:Path,source_count:int,source_bytes:int):
    # app.js já tem a configuração estática V38.4.9. Aqui entram apenas contagens reais de snapshots.
    p=repo/'docs/assets/js/app.js';txt=p.read_text(encoding='utf-8');prefix='const CATALOG=';pos=txt.index(prefix)+len(prefix);cat,end=json.JSONDecoder().raw_decode(txt[pos:])
    aflo_count=None
    aflo_path=repo/'docs/camadas/arquivos/afloramentos_geosgb_ms.geojson'
    if aflo_path.exists():
        try:aflo_count=len(load_json(aflo_path).get('features',[]))
        except Exception:aflo_count=None
    for item in cat.get('layers',[]):
        if item.get('id')=='petrografia_geosgb_ms':item['count']=source_count
        if item.get('id')=='afloramentos_geosgb_ms' and aflo_count is not None:item['count']=aflo_count
    p.write_text(txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:],encoding='utf-8',newline='\n')
    jp=repo/'docs/camadas/catalogo-local.json';arr=load_json(jp)
    for item in arr:
        if item.get('id')=='petrografia_geosgb_ms':item['feicoes']=source_count;item['bytes']=source_bytes
        if item.get('id')=='afloramentos_geosgb_ms' and aflo_count is not None:
            item['feicoes']=aflo_count;item['bytes']=aflo_path.stat().st_size
    dump_json(jp,arr)
    hp=repo/'docs/camadas/index.html'
    if hp.exists():
        h=hp.read_text(encoding='utf-8').replace('__ICP_PETRO_COUNT__',str(source_count))
        if aflo_count is not None:h=h.replace('__IOD_AFLO_COUNT__',str(aflo_count))
        hp.write_text(h,encoding='utf-8',newline='\n')

def self_test():
    # Teste sintético do agrupamento, completude e fórmula. Não entra no Atlas.
    feats=[]
    for i,(lon,lat,afl,rock,mineral) in enumerate([(-54.52,-20.52,1,10,'quartzo'),(-54.52001,-20.52001,1,10,''),(-54.48,-20.48,2,20,'feldspato')]):
        feats.append({'type':'Feature','geometry':{'type':'Point','coordinates':[lon,lat]},'properties':{'OBJECTID':i+1,'COD_AFLORAMENTO':afl,'COD_ROCHA':rock,'COD_AMOSTRA':100+i,'COD_LAMINA':200+i,'ROCHA':'granito','MINERAIS_IDENTIFICADOS':mineral,'TIPO_SECAO':'Delgada','PETROGRAFO':'Teste','PROJETO':'Teste','FICHA':'sim'}})
    units=merge_groups(feats)
    assert len(units)==2 and all(0<u['q']<=1 for u in units)
    print('SELFTEST ICP V38.4.9 · PASS')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');ap.add_argument('--self-test',action='store_true');ap.add_argument('--source-file');args=ap.parse_args()
    if args.self_test:self_test();return 0
    repo=Path(args.repo).resolve()
    for rel in list(GRID_FILES.values())+[LIMIT_FILE,GEOLOGY_FILE]:
        if not (repo/rel).exists():raise RuntimeError(f'arquivo estrutural ausente · {rel}')
    # exige que a versão anterior materializada esteja íntegra sem reprocessá-la
    for rel in ['docs/indices/iod-v3848.js','docs/indices/iod_v3848_snapshot.json','docs/camadas/arquivos/afloramentos_geosgb_ms.geojson']:
        if not (repo/rel).exists():raise RuntimeError(f'V38.4.8 incompleta · arquivo IOD ausente · {rel}')
    print('ITA ARANDU MS · materialização ICP V38.4.9')
    print('Fonte · SGB GeoSGB · Petrografia')
    print('Fórmula ·',FORMULA)
    print('P · sqrt(D* × O) · D* P95 por escala · micromalha 5 km')
    print('U · representatividade areal aproximada das unidades litoestratigráficas locais · suporte determinístico 9 × 9')
    print('Q · completude média de oito blocos de metadados do GeoSGB')
    if args.source_file:
        source_obj=load_json(Path(args.source_file));source_label='arquivo local fornecido';source_url=str(Path(args.source_file))
    else:
        source_label,source_url,source_obj=fetch_source()
    raw_merged=canonical_bytes(source_obj);raw_hash=sha256_bytes(raw_merged)
    state=feature_polys(load_json(repo/LIMIT_FILE));features,cleanup=clip_to_state(source_obj.get('features',[]),state)
    if len(features)<5:raise RuntimeError(f'apenas {len(features)} registros petrográficos ficaram dentro do limite oficial de MS')
    units=merge_groups(features)
    if len(units)<3:raise RuntimeError(f'apenas {len(units)} unidades petrográficas independentes após deduplicação')
    geo_items=geology_records(load_json(repo/GEOLOGY_FILE))
    if not geo_items:raise RuntimeError('mapa geológico sem polígonos utilizáveis')
    missing_geo=annotate_geology(units,geo_items);annotate_source_features(features,units)
    grids={};cells={};assigned={};missing={};ambiguous={}
    for s,rel in GRID_FILES.items():grids[s],cells[s]=load_grid(repo/rel)
    for s in ('250','500','1000'):assigned[s],missing[s],ambiguous[s]=assign_units(units,cells[s])
    # o recorte científico é a malha 250. Registros fora dela não entram em nenhuma escala.
    valid=set(i for arr in assigned['250'] for i in arr)
    if len(valid)<3:raise RuntimeError('menos de três unidades petrográficas independentes caem na malha oficial de MS')
    if len(valid)!=len(units):
        keep_keys={units[i]['key'] for i in valid};features=[f for f in features if independent_key(f) in keep_keys];units=[u for u in units if u['key'] in keep_keys]
        annotate_source_features(features,units)
        for s in ('250','500','1000'):assigned[s],missing[s],ambiguous[s]=assign_units(units,cells[s])
    for s in ('250','500','1000'):
        if missing[s]:raise RuntimeError(f'{len(missing[s])} unidades petrográficas não foram atribuídas à malha {s}')
    baseline={};sats={}
    for s in ('250','500','1000'):baseline[s],sats[s]=calculate_scale(cells[s],assigned[s],units,geo_items)
    # Sensibilidade limitada aos parâmetros de P e ao suporte de U. Não altera o resultado basal.
    sensitivity={}
    for s in ('250','500','1000'):
        sensitivity[s]={};base=baseline[s]
        for step,pct,n in [(2500,95,SUPPORT_N),(5000,90,SUPPORT_N),(5000,99,SUPPORT_N),(10000,95,SUPPORT_N)]:
            alt,_=calculate_scale(cells[s],assigned[s],units,geo_items,float(step),pct,n)
            sensitivity[s][f'micro_{step/1000:g}km_P{pct}_U{n}x{n}']=spearman_maps(base,alt)
    source_fc={'type':'FeatureCollection','features':features,'atlas_metadata':{
      'id':'petrografia_geosgb_ms','nome':'Registros petrográficos e lâminas descritas','fonte':'Serviço Geológico do Brasil · GeoSGB · Petrografia',
      'fonte_materializada_por':source_label,'url_consulta':source_url,'corte':CUT_DATE,'sha256_snapshot_mesclado':raw_hash,
      'registros_recortados_ms':len(features),'unidades_independentes':len(units),
      'deduplicacao':'COD_AFLORAMENTO + COD_ROCHA quando disponíveis; depois COD_AMOSTRA; depois NUM_CAMPO_AMOSTRA; fallback coordenada + classificação',
      'regra':'múltiplas lâminas ou registros do mesmo afloramento e rocha não aumentam P como evidências independentes',**cleanup}}
    sp=repo/'docs/camadas/arquivos/petrografia_geosgb_ms.geojson';dump_json(sp,source_fc,compact=True);update_catalog_files(repo,len(features),sp.stat().st_size)
    raw_path=repo/f'data/petrografia_geosgb_ms_raw_{CUT_DATE.replace("-","")}.geojson.gz';raw_path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(raw_path,'wb',compresslevel=9) as gz:gz.write(raw_merged)
    q_stats=[u['q'] for u in units]
    snap={'metadata':{
      'index':'ICP','version':VERSION,'calculated_at':now_iso(),'cut_date':CUT_DATE,'formula':FORMULA,'p_formula':P_FORMULA,
      'components':{
        'P':'presença espacial de caracterizações independentes. P = sqrt(D* × O), com D* como densidade por área efetiva saturada no P95 positivo de cada escala e O como ocupação da micromalha fixa de 5 km',
        'U':'fração do suporte areal determinístico do hexágono cuja unidade litoestratigráfica do mapa SGB 1:1.000.000 possui ao menos uma caracterização petrográfica independente local',
        'Q':'média da completude de oito blocos de metadados. amostra, lâmina, classificação, mineralogia, tipo de seção, responsável, contexto de projeto e suporte documental'
      },
      'source':'SGB · GeoSGB · Petrografia','source_url':source_url,'source_method':source_label,'source_sha256':raw_hash,'source_records':len(features),'independent_units':len(units),'raw_gzip':str(raw_path.relative_to(repo)).replace('\\','/'),
      'deduplication':'COD_AFLORAMENTO+COD_ROCHA → COD_AMOSTRA → NUM_CAMPO_AMOSTRA → coordenada+classificação',
      'quality_rule':'Q mede completude documental dos metadados disponíveis no serviço. Não é nota de precisão petrográfica nem de qualidade laboratorial.',
      'geology_source':'SGB/CPRM · mapa geológico de Mato Grosso do Sul 1:1.000.000 · snapshot local do Atlas','u_support':f'{SUPPORT_N} × {SUPPORT_N} pontos determinísticos por bbox, retidos apenas quando dentro do hexágono e de unidade geológica mapeada',
      'microcell_m':BASE_MICROCELL_M,'density_percentile':BASE_DENSITY_PERCENTILE,
      'scale_rule':'250, 500 e 1000 km² são calculados diretamente a partir das unidades petrográficas independentes. Não há agregação de resultados entre escalas.',
      'null_rule':'hexágonos sem caracterização petrográfica independente recebem ICP=null e permanecem transparentes. Ausência não é convertida em zero.',
      'field_rule':'amostras da caderneta ITA ARANDU não entram automaticamente. A futura incorporação exige validação, metadados mínimos e reconciliação com a base institucional.',
      'references':['REF-002','REF-059','REF-082','REF-084','REF-105','REF-106','REF-115']
     },
     'source_cleanup':cleanup,'geology_assignment':{'independent_units_without_mapped_unit':missing_geo},
     'quality_summary':{'q_min':round(min(q_stats),4),'q_mean':round(statistics.fmean(q_stats),4),'q_median':round(statistics.median(q_stats),4),'q_max':round(max(q_stats),4)},
     'grid_assignment':{s:{'ambiguous_boundary_resolved':ambiguous[s],'missing':len(missing[s])} for s in ('250','500','1000')},
     'density_saturation':{s:round(sats[s],8) for s in sats},'summaries':{s:summary(baseline[s]) for s in baseline},'sensitivity':sensitivity,'grids':{s:compact_rows(baseline[s]) for s in baseline}}
    dump_json(repo/'docs/indices/icp_v3849_snapshot.json',snap);(repo/'docs/indices/icp-v3849.js').write_text('window.ITA_ICP_V3849='+json.dumps(snap,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
    runtime={'audit':'ICP V38.4.9 runtime','status':'PASS','generated_at':now_iso(),'version':VERSION,'source':{'method':source_label,'url':source_url,'sha256':raw_hash,'records':len(features),'independent_units':len(units),**cleanup},'quality_summary':snap['quality_summary'],'geology_assignment':snap['geology_assignment'],'scales':{s:{**summary(baseline[s]),'density_p95':round(sats[s],8),'ambiguous_boundary_resolved':ambiguous[s]} for s in ('250','500','1000')},'sensitivity':sensitivity,'checks':{'source_records_positive':len(features)>0,'independent_units_positive':len(units)>0,'all_units_assigned_each_scale':all(len(missing[s])==0 for s in missing),'grid_counts':{s:len(baseline[s]) for s in baseline},'score_range_valid':all(r['icp'] is None or 0<=r['icp']<=100 for rows in baseline.values() for r in rows.values()),'zero_record_is_null':all(r['n']>0 or r['icp'] is None for rows in baseline.values() for r in rows.values()),'independent_scale_calculation':True,'q_is_metadata_completeness_not_lab_quality':True}}
    dump_json(repo/'AUDITORIA_V38_4_9_ICP_RUNTIME.json',runtime)
    print(f'Petrografia SGB · {len(features)} registros · {len(units)} unidades independentes dentro da malha de MS')
    for s in ('250','500','1000'):
        sm=runtime['scales'][s];print(f'ICP {s} km² · {sm["cells_with_petrografia"]}/{sm["cells"]} células com petrografia · min {sm["icp_min"]} · mediana {sm["icp_median"]} · max {sm["icp_max"]}')
    print('AUDITORIA RUNTIME · PASS');return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        print('ERRO ICP V38.4.9 ·',e,file=sys.stderr);raise SystemExit(2)
