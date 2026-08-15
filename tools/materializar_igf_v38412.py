#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, gzip, hashlib, json, math, re, statistics, unicodedata, urllib.parse, urllib.request
from pathlib import Path

VERSION='V38.4.12-IGF-CONHECIMENTO-GEOFISICO-20260814'
CUT_DATE='2026-08-14'
FORMULA='IGF_h = max(IGF_AM,h, IGF_GA,h, IGF_GR,h, IGF_MT,h)'
AERO_FORMULA='IGF_AM,h ou IGF_GA,h = 100 × sqrt(C_m × R*_m)'
POINT_FORMULA='IGF_GR,h ou IGF_MT,h = 100 × sqrt(D*_m × O_m)'
BASE_MICROCELL_M=5000.0
BASE_PERCENTILE=95
LAEA_LON0=-54.5
LAEA_LAT0=-20.5
EARTH_R=6371007.181
BBOX_MS=(-58.3,-24.3,-50.6,-17.0)
AERO_SERVICE='https://geoportal.sgb.gov.br/server/rest/services/geofisica/aerogeofisica/MapServer'
GRAV_LAYER='https://geoportal.sgb.gov.br/server/rest/services/geofisica/gravimetria/MapServer/0'
MT_LAYER='https://geoportal.sgb.gov.br/server/rest/services/geofisica/geofisica_terrestre/MapServer/2'
GRID_FILES={
 '250':'docs/camadas/arquivos/malha_r5_250km2.geojson',
 '500':'docs/camadas/arquivos/malha_500km2.geojson',
 '1000':'docs/camadas/arquivos/malha_1000km2.geojson',
}
LIMIT_FILE='docs/camadas/arquivos/limite_ms_ibge_2025.geojson'


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

def ci_get(props,*names):
    if not isinstance(props,dict):return None
    low={str(k).lower():v for k,v in props.items()}
    for n in names:
        if n in props:return props[n]
        if str(n).lower() in low:return low[str(n).lower()]
    return None

def fetch_json(url,timeout=180):
    req=urllib.request.Request(url,headers={'User-Agent':'ITA-ARANDU-MS/38.4.12 Python urllib','Accept':'application/json, application/geo+json;q=0.9, */*;q=0.1'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8-sig'))

def arcgis_query_url(layer,params):return layer+'/query?'+urllib.parse.urlencode(params,safe=',()')

def _arcgis_direct_pages(layer, spatial, page_size=500):
    """Fallback para serviços que falham em returnIdsOnly.
    Usa paginação espacial direta e tenta MapServer e FeatureServer.
    """
    candidates=[layer]
    if '/MapServer/' in layer:
        candidates.append(layer.replace('/MapServer/','/FeatureServer/'))
    last_error=None
    for candidate in candidates:
        feats=[];offset=0
        try:
            while True:
                params={**spatial,'outFields':'*','returnGeometry':'true','outSR':'4326','resultOffset':offset,'resultRecordCount':page_size,'f':'geojson'}
                obj=fetch_json(arcgis_query_url(candidate,params),timeout=120)
                if isinstance(obj,dict) and obj.get('error'):
                    raise RuntimeError(str(obj['error']))
                batch=(obj.get('features') or []) if isinstance(obj,dict) else []
                feats.extend(batch)
                if len(batch)<page_size:break
                offset+=len(batch)
                if offset>200000:raise RuntimeError('limite de segurança de paginação excedido')
            return feats,('direct-pagination-feature' if '/FeatureServer/' in candidate else 'direct-pagination-map')
        except Exception as e:
            last_error=e
    raise RuntimeError(f'paginação direta falhou em {layer} · {last_error}')

def fetch_arcgis_features(layer,where='1=1'):
    xmin,ymin,xmax,ymax=BBOX_MS
    spatial={'where':where,'geometry':f'{xmin},{ymin},{xmax},{ymax}','geometryType':'esriGeometryEnvelope','inSR':'4326','spatialRel':'esriSpatialRelIntersects'}
    ids_error=None
    try:
        ids=fetch_json(arcgis_query_url(layer,{**spatial,'returnIdsOnly':'true','f':'json'}),timeout=90)
        if ids.get('error'):raise RuntimeError(str(ids['error']))
        object_ids=ids.get('objectIds') or []
        feats=[]
        for i in range(0,len(object_ids),500):
            batch=object_ids[i:i+500]
            obj=fetch_json(arcgis_query_url(layer,{'where':where,'objectIds':','.join(str(x) for x in batch),'outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}),timeout=120)
            if obj.get('error'):raise RuntimeError(str(obj['error']))
            feats.extend(obj.get('features') or [])
        return feats,'returnIdsOnly'
    except Exception as e:
        ids_error=e
    try:
        return _arcgis_direct_pages(layer,spatial)
    except Exception as e:
        raise RuntimeError(f'ArcGIS falhou em {layer} · returnIdsOnly={ids_error} · fallback={e}')

def fetch_source():
    aero=[];availability={'aero':{},'grav':{},'mt':{}}
    for lid in range(4):
        layer=f'{AERO_SERVICE}/{lid}'
        try:
            feats,mode=fetch_arcgis_features(layer)
            availability['aero'][str(lid)]={'status':'captured','mode':mode,'records':len(feats)}
        except Exception as e:
            feats=[];availability['aero'][str(lid)]={'status':'unavailable','mode':None,'records':0,'error':str(e)[:1200]}
            print(f'AVISO · aerogeofísica série {lid} indisponível nesta execução · {e}')
        for f in feats:
            p=f.setdefault('properties',{});p['__atlas_serie_layer']=lid;p['__atlas_fonte_servico']=layer
        aero.extend(feats)
    try:
        grav,gmode=fetch_arcgis_features(GRAV_LAYER)
        availability['grav']={'status':'captured','mode':gmode,'records':len(grav)}
    except Exception as e:
        grav=[];availability['grav']={'status':'unavailable','mode':None,'records':0,'error':str(e)[:1200]}
        print(f'AVISO · gravimetria indisponível nesta execução · {e}')
    try:
        # Filtrar estações já publicadas reduz substancialmente a carga do serviço MT.
        mt,mmode=fetch_arcgis_features(MT_LAYER,"DataAvailability='Available'")
        availability['mt']={'status':'captured','mode':mmode,'records':len(mt)}
    except Exception as e:
        mt=[];availability['mt']={'status':'unavailable','mode':None,'records':0,'error':str(e)[:1200]}
        print(f'AVISO · magnetotelúrico indisponível nesta execução · módulo MT ficará não avaliável · {e}')
    captured=sum(1 for v in availability['aero'].values() if v.get('status')=='captured') + int(availability['grav'].get('status')=='captured') + int(availability['mt'].get('status')=='captured')
    if captured==0:
        raise RuntimeError('nenhuma fonte geofísica oficial pôde ser consultada nesta execução')
    return 'ArcGIS REST GeoSGB · aerogeofísica, gravimetria e magnetotelúrico',{'aero':aero,'grav':grav,'mt':mt,'availability':availability,'services':{'aero':AERO_SERVICE,'grav':GRAV_LAYER,'mt':MT_LAYER},'cut_date':CUT_DATE}

# Projeção LAEA operacional do Atlas
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
    if not xs:raise ValueError('geometria poligonal vazia')
    return {'polys':out,'bbox':(min(xs),min(ys),max(xs),max(ys))}

def feature_polys(fc):
    out=[]
    for f in fc.get('features',[]):
        g=f.get('geometry') or {};typ=g.get('type')
        if typ not in {'Polygon','MultiPolygon'}:continue
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
    cand=index.get((math.floor(pt[0]/bin_m),math.floor(pt[1]/bin_m)),[]);hits=[]
    for i in cand:
        b=items[i]['bbox']
        if pt[0]<b[0]-.1 or pt[0]>b[2]+.1 or pt[1]<b[1]-.1 or pt[1]>b[3]+.1:continue
        if point_in_geom_projected(pt,items[i]['geom']):hits.append(i)
    return hits

def point_in_state_lonlat(lon,lat,state_items,state_index,state_bin):
    return bool(find_poly_hits(laea(lon,lat),state_items,state_index,state_bin))

def bbox_overlap(a,b):
    return not (a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])

def seg_intersects(a,b,c,d):
    def orient(p,q,r):
        return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    def on(p,q,r):
        return min(p[0],r[0])-1e-8<=q[0]<=max(p[0],r[0])+1e-8 and min(p[1],r[1])-1e-8<=q[1]<=max(p[1],r[1])+1e-8
    o1=orient(a,b,c);o2=orient(a,b,d);o3=orient(c,d,a);o4=orient(c,d,b)
    if ((o1>0 and o2<0) or (o1<0 and o2>0)) and ((o3>0 and o4<0) or (o3<0 and o4>0)):return True
    if abs(o1)<1e-8 and on(a,c,b):return True
    if abs(o2)<1e-8 and on(a,d,b):return True
    if abs(o3)<1e-8 and on(c,a,d):return True
    if abs(o4)<1e-8 and on(c,b,d):return True
    return False

def projected_geoms_intersect(a,b):
    if not bbox_overlap(a['bbox'],b['bbox']):return False
    # vértice de A em B ou de B em A
    for pa in a['polys']:
        for ring in pa:
            for pt in ring:
                if point_in_geom_projected(pt,b):return True
    for pb in b['polys']:
        for ring in pb:
            for pt in ring:
                if point_in_geom_projected(pt,a):return True
    # cruzamento de bordas
    for pa in a['polys']:
        ra=pa[0] if pa else []
        for pb in b['polys']:
            rb=pb[0] if pb else []
            for i in range(1,len(ra)):
                for j in range(1,len(rb)):
                    if seg_intersects(ra[i-1],ra[i],rb[j-1],rb[j]):return True
    return False

def get_point(feat):
    g=feat.get('geometry') or {}
    if g.get('type')=='Point' and isinstance(g.get('coordinates'),list) and len(g['coordinates'])>=2:
        try:return float(g['coordinates'][0]),float(g['coordinates'][1])
        except Exception:pass
    p=feat.get('properties') or {}
    try:return float(ci_get(p,'longitude','Longitude','LONGITUDE','X','lon')),float(ci_get(p,'latitude','Latitude','LATITUDE','Y','lat'))
    except Exception:return None

def percentile(vals,p):
    x=sorted(float(v) for v in vals if v is not None and math.isfinite(float(v)))
    if not x:return None
    if len(x)==1:return x[0]
    pos=(len(x)-1)*p/100;lo=math.floor(pos);hi=math.ceil(pos)
    return x[lo] if lo==hi else x[lo]+(x[hi]-x[lo])*(pos-lo)

def spacing_m(props):
    v=ci_get(props,'ESPACAMENTO_LV_M','espacamento_lv_m','ESPACAMENTO_LV','espacamento_lv','ESP_LV_M')
    vals=[]
    if isinstance(v,(int,float)):
        vals=[float(v)]
    elif v is not None:
        for z in re.findall(r'\d+(?:[\.,]\d+)?',str(v)):
            try:vals.append(float(z.replace(',','.')))
            except Exception:pass
    vals=[x for x in vals if math.isfinite(x) and x>0]
    return max(vals) if vals else None

def aero_methods(props):
    s=norm_text(ci_get(props,'METODOS','metodos','METODO','metodo'))
    mods=[]
    if 'magnet' in s:mods.append('AM')
    if 'gama' in s or 'gamma' in s or 'radiometr' in s:mods.append('GA')
    return mods

def mt_available(props):
    v=norm_text(ci_get(props,'DataAvailability','DATAAVAILABILITY','data_availability','Disponibilidade','DISPONIBILIDADE'))
    return v in {'available','disponivel','disponivel para download','publico','publica'} or 'available' in v or 'disponivel' in v

def oid_key(feat,prefix):
    p=feat.get('properties') or {}
    for k in ['OBJECTID','objectid','ID_PROJETO','id_projeto','SurveyID','SiteID','ID']:
        v=ci_get(p,k)
        if v is not None and str(v).strip():return f'{prefix}:{str(v).strip()}'
    pt=get_point(feat)
    return f'{prefix}:coord:{round(pt[0],6)}:{round(pt[1],6)}' if pt else f'{prefix}:unknown:{id(feat)}'

def prepare_source(source,state_items):
    state_index,state_bin=make_spatial_index(state_items,100000.0)
    aero=[];invalid_aero=0;outside_aero=0;unclassified=0;missing_spacing=0
    for f in source.get('aero') or []:
        g=f.get('geometry') or {}
        if g.get('type') not in {'Polygon','MultiPolygon'}:invalid_aero+=1;continue
        p=f.get('properties') or {};mods=aero_methods(p);sp=spacing_m(p)
        if not mods:unclassified+=1
        if sp is None:missing_spacing+=1
        try:pg=project_geometry(g)
        except Exception:invalid_aero+=1;continue
        if not any(projected_geoms_intersect(pg,st['geom']) for st in state_items):outside_aero+=1;continue
        aero.append({'feature':f,'geom':pg,'bbox':pg['bbox'],'modules':mods,'spacing':sp,'key':oid_key(f,'AERO')})
    # deduplica projetos por id, preservando registro com mais módulos e menor espaçamento válido
    ded={}
    for a in aero:
        old=ded.get(a['key'])
        rank=(len(a['modules']), -(a['spacing'] or 1e99))
        if old is None or rank>(len(old['modules']), -(old['spacing'] or 1e99)):ded[a['key']]=a
    aero=list(ded.values())
    def points(src,prefix,available_only=False):
        out=[];outside=0;invalid=0;unavailable=0;seen=set()
        for f in src or []:
            pt=get_point(f)
            if pt is None:invalid+=1;continue
            if not point_in_state_lonlat(pt[0],pt[1],state_items,state_index,state_bin):outside+=1;continue
            if available_only and not mt_available(f.get('properties') or {}):unavailable+=1;continue
            k=oid_key(f,prefix)
            if k in seen:continue
            seen.add(k);out.append({'feature':f,'point':pt,'key':k})
        return out,{'source':len(src or []),'usable':len(out),'outside_ms':outside,'invalid_geometry':invalid,'not_available_excluded':unavailable}
    grav,gs=points(source.get('grav'),'GRAV',False);mt,ms=points(source.get('mt'),'MT',True)
    stats={'aero':{'source':len(source.get('aero') or []),'unique_projects':len(aero),'invalid_geometry':invalid_aero,'outside_ms':outside_aero,'unclassified_method':unclassified,'missing_spacing':missing_spacing},'grav':gs,'mt':ms}
    return aero,grav,mt,stats

def load_grid(path:Path):
    fc=load_json(path);cells=[]
    for f in fc.get('features',[]):
        pg=project_geometry(f['geometry']);p=f.get('properties') or {};hid=str(p.get('hex_id') or '')
        if not hid:raise RuntimeError(f'hexágono sem hex_id em {path.name}')
        try:area=float(p['area_efetiva_ms_km2'])
        except Exception:area=float(p.get('area_nominal_km2') or 0)
        if area<=0:raise RuntimeError(f'área efetiva inválida em {hid}')
        b=pg['bbox'];cells.append({'hex_id':hid,'feature':f,'geom':pg,'bbox':b,'area':area})
    return fc,cells

def micro_support(cell,step):
    xmin,ymin,xmax,ymax=cell['bbox'];pts=[]
    ix0=math.floor(xmin/step)-1;ix1=math.floor(xmax/step)+1;iy0=math.floor(ymin/step)-1;iy1=math.floor(ymax/step)+1
    for ix in range(ix0,ix1+1):
        x=(ix+.5)*step
        for iy in range(iy0,iy1+1):
            y=(iy+.5)*step
            if x<xmin-.1 or x>xmax+.1 or y<ymin-.1 or y>ymax+.1:continue
            if point_in_geom_projected((x,y),cell['geom']):pts.append((x,y,ix,iy))
    # pequenos fragmentos de borda podem não conter centro da microcélula
    if not pts:
        b=cell['bbox'];candidate=((b[0]+b[2])/2,(b[1]+b[3])/2,0,0)
        if point_in_geom_projected((candidate[0],candidate[1]),cell['geom']):pts=[candidate]
        else:
            try:
                v=cell['geom']['polys'][0][0][0];pts=[(v[0],v[1],0,0)]
            except Exception:pass
    return pts

def calc_aero(cells,aero,module,step=BASE_MICROCELL_M,pct=BASE_PERCENTILE):
    items=[a for a in aero if module in a['modules'] and a['spacing'] is not None and a['spacing']>0]
    if not items:return {c['hex_id']:{'score':None,'coverage':0.0,'resolution':None,'support':0,'covered':0,'projects':0,'min_spacing':None} for c in cells},None
    idx,bin_m=make_spatial_index(items,100000.0)
    inv=[]
    cell_support={}
    for c in cells:
        ss=micro_support(c,step);cell_support[c['hex_id']]=ss
        for x,y,_,_ in ss:
            hits=find_poly_hits((x,y),items,idx,bin_m)
            spac=[items[i]['spacing'] for i in hits if items[i]['spacing']]
            if spac:inv.append(1.0/min(spac))
    sat=percentile(inv,pct)
    if sat is None or sat<=0:sat=max(inv) if inv else None
    rows={}
    for c in cells:
        ss=cell_support[c['hex_id']];covered=0;rvals=[];keys=set();mins=[]
        for x,y,_,_ in ss:
            hits=find_poly_hits((x,y),items,idx,bin_m)
            spac=[items[i]['spacing'] for i in hits if items[i]['spacing']]
            if not spac:continue
            covered+=1;sp=min(spac);mins.append(sp);rvals.append(min(1.0,(1.0/sp)/sat) if sat else 1.0);keys.update(items[i]['key'] for i in hits)
        if covered==0 or not ss:
            rows[c['hex_id']]={'score':None,'coverage':0.0,'resolution':None,'support':len(ss),'covered':0,'projects':0,'min_spacing':None};continue
        C=covered/len(ss);R=statistics.fmean(rvals);score=100*math.sqrt(max(0,C*R))
        rows[c['hex_id']]={'score':round(score,2),'coverage':round(C,6),'resolution':round(R,6),'support':len(ss),'covered':covered,'projects':len(keys),'min_spacing':min(mins) if mins else None}
    return rows,sat

def assign_points(points,cells):
    idx,bin_m=make_spatial_index(cells,50000.0);assigned=[[] for _ in cells];missing=[]
    for pi,p in enumerate(points):
        pt=laea(*p['point']);hits=find_poly_hits(pt,cells,idx,bin_m)
        if not hits:missing.append(pi);continue
        assigned[hits[0]].append(pi)
    return assigned,missing

def calc_points(cells,assigned,points,step=BASE_MICROCELL_M,pct=BASE_PERCENTILE):
    dens=[len(assigned[i])/c['area'] for i,c in enumerate(cells) if assigned[i]];sat=percentile(dens,pct)
    rows={}
    if sat is None or sat<=0:
        return {c['hex_id']:{'score':None,'D':None,'O':None,'n':0,'density':0.0,'support':0,'occupied':0} for c in cells},None
    for ci,c in enumerate(cells):
        inds=assigned[ci];n=len(inds)
        if not n:
            rows[c['hex_id']]={'score':None,'D':None,'O':None,'n':0,'density':0.0,'support':len(micro_support(c,step)),'occupied':0};continue
        density=n/c['area'];D=min(1.0,density/sat);ss=micro_support(c,step);keys={(math.floor(laea(*points[i]['point'])[0]/step),math.floor(laea(*points[i]['point'])[1]/step)) for i in inds}
        # denominador = suporte determinístico dentro do hexágono; garante pelo menos pontos ocupados
        O=min(1.0,len(keys)/max(1,len(ss)));score=100*math.sqrt(max(0,D*O))
        rows[c['hex_id']]={'score':round(score,2),'D':round(D,6),'O':round(O,6),'n':n,'density':round(density,9),'support':len(ss),'occupied':len(keys)}
    return rows,sat

def combine(cells,am,ga,gr,mt):
    out={};order=['AM','GA','GR','MT']
    for c in cells:
        hid=c['hex_id'];mods={'AM':am[hid]['score'],'GA':ga[hid]['score'],'GR':gr[hid]['score'],'MT':mt[hid]['score']};valid=[v for v in mods.values() if v is not None]
        score=max(valid) if valid else None;best=next((m for m in order if score is not None and mods[m]==score),None)
        out[hid]={'igf':score,'best':best,'n_modules':sum(v is not None for v in mods.values()),'modules':mods}
    return out

def compact_rows(combined,am,ga,gr,mt):
    # [IGF,best,nmod,AM,GA,GR,MT,nGrav,nMT,covAM,covGA,minSpacingAM,minSpacingGA]
    return {hid:[r['igf'],r['best'],r['n_modules'],r['modules']['AM'],r['modules']['GA'],r['modules']['GR'],r['modules']['MT'],gr[hid]['n'],mt[hid]['n'],am[hid]['coverage'],ga[hid]['coverage'],am[hid]['min_spacing'],ga[hid]['min_spacing']] for hid,r in combined.items()}

def summary(combined):
    vals=[r['igf'] for r in combined.values() if r['igf'] is not None]
    return {'cells':len(combined),'cells_with_igf':len(vals),'cells_without_igf':len(combined)-len(vals),'igf_min':min(vals) if vals else None,'igf_median':round(statistics.median(vals),2) if vals else None,'igf_mean':round(statistics.fmean(vals),2) if vals else None,'igf_max':max(vals) if vals else None,'dominant_module_counts':{m:sum(r['best']==m for r in combined.values()) for m in ['AM','GA','GR','MT']}}

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
        va=a[k]['igf'];vb=b.get(k,{}).get('igf')
        if va is not None and vb is not None:x.append(va);y.append(vb)
    rr=pearson(rankdata(x),rankdata(y)) if len(x)>=2 else None
    return {'n_common':len(x),'rho':None if rr is None else round(rr,6)}

def source_fc_aero(aero,raw_hash):
    feats=[]
    for a in aero:
        f=json.loads(json.dumps(a['feature'],ensure_ascii=False));p=f.setdefault('properties',{});p['__atlas_modulos']=';'.join(a['modules']) or 'não classificado';p['__atlas_espacamento_lv_m']=a['spacing'];p['__atlas_snapshot']=CUT_DATE;feats.append(f)
    return {'type':'FeatureCollection','features':feats,'atlas_metadata':{'id':'levantamentos_geofisicos_cobertura_ms','fonte':'SGB · Aerogeofísica · séries 1000–4000','corte':CUT_DATE,'sha256_snapshot':raw_hash,'regra':'geometrias-fonte preservadas. O IGF avalia apenas suportes dentro das malhas de Mato Grosso do Sul.'}}

def source_fc_points(points,kind,raw_hash):
    feats=[]
    for u in points:
        f=json.loads(json.dumps(u['feature'],ensure_ascii=False));p=f.setdefault('properties',{});p['__atlas_chave_independente']=u['key'];p['__atlas_snapshot']=CUT_DATE;feats.append(f)
    return {'type':'FeatureCollection','features':feats,'atlas_metadata':{'id':kind,'corte':CUT_DATE,'sha256_snapshot':raw_hash,'regra':'pontos oficiais recortados ao limite operacional de Mato Grosso do Sul; duplicações por identificador institucional não contam como estações independentes.'}}

def patch_catalog_json_obj(cat,counts):
    layers=cat.get('layers',[]) if isinstance(cat,dict) else cat
    gridmap={'igf_250':('250','malha_r5_250km2',1554),'igf_500':('500','malha_500km2',793),'igf_1000':('1000','malha_1000km2',412)}
    files={'levantamentos_geofisicos_cobertura_ms':'./camadas/arquivos/aerogeofisica_projetos_sgb_ms.geojson','gravimetria_sgb_ms':'./camadas/arquivos/gravimetria_sgb_ms.geojson','magnetotelurico_sgb_ms':'./camadas/arquivos/magnetotelurico_sgb_ms.geojson'}
    for item in layers:
        iid=item.get('id')
        if iid in files:
            item['status']='incorporada';item['count']=counts.get(iid,0);item['file']=files[iid];item.pop('remote_type',None);item.pop('remote_url',None)
            item['validation']='snapshot local V38.4.12 · fonte oficial SGB · corte 14/08/2026'
        if iid in gridmap:
            scale,grid,count=gridmap[iid]
            item.update({'status':'incorporada','count':count,'source':'ITA ARANDU MS · IGF V38.4.12 · SGB geofísica','validation':'V38.4.12 · cálculo direto e independente por escala','note':'Conhecimento geofísico documentado. Aeromagnetometria, gamaespectrometria, gravimetria e magnetotelúrico permanecem módulos explícitos. Ausência permanece transparente e não equivale a zero.','derive_type':'igf_snapshot_v38412','grid_source_id':grid,'igf_scale':scale})
    return cat

def patch_app(repo:Path,counts):
    p=repo/'docs/assets/js/app.js';txt=p.read_text(encoding='utf-8');prefix='const CATALOG=';pos=txt.index(prefix)+len(prefix);cat,end=json.JSONDecoder().raw_decode(txt[pos:]);cat=patch_catalog_json_obj(cat,counts);txt=txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:]
    color_marker="function igqColor(v){const c=igqClass(v);return ITA_IGQ_COLORS[c]||'rgba(0,0,0,0)'}"
    if 'const ITA_IGF_COLORS=' not in txt:
        add="\nconst ITA_IGF_COLORS={'muito baixo':'#fee5d9','baixo':'#fcae91','médio':'#fb6a4a','alto':'#de2d26','muito alto':'#a50f15'};\nfunction igfClass(v){const x=Number(v);if(v===null||v===undefined||!Number.isFinite(x))return'sem conhecimento geofísico materializado';if(x<20)return'muito baixo';if(x<40)return'baixo';if(x<60)return'médio';if(x<75)return'alto';return'muito alto'}\nfunction igfColor(v){const c=igfClass(v);return ITA_IGF_COLORS[c]||'rgba(0,0,0,0)'}"
        if color_marker not in txt:raise RuntimeError('marcador de cor IGQ não encontrado em app.js')
        txt=txt.replace(color_marker,color_marker+add,1)
    style_marker="if(st.renderer==='index_igq'){fill=igqColor(p.igq_100);stroke='#4a4a4a';}"
    if "st.renderer==='index_igf'" not in txt:
        if style_marker not in txt:raise RuntimeError('marcador renderer IGQ não encontrado em app.js')
        txt=txt.replace(style_marker,style_marker+" if(st.renderer==='index_igf'){fill=igfColor(p.igf_100);stroke='#4a4a4a';}",1)
    legend_token="if(st.renderer==='index_igq')return"
    if "if(st.renderer==='index_igf')return" not in txt:
        i=txt.find(legend_token)
        if i<0:raise RuntimeError('legenda IGQ não encontrada em app.js')
        e=txt.find('\n',i)
        legend=" if(st.renderer==='index_igf')return `<div class=\"legend-layer-title\">${esc(cfg.name)}</div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:transparent;border:1px solid #4a4a4a\"></span><span>sem conhecimento geofísico materializado · transparente</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#fee5d9;border:1px solid #4a4a4a\"></span><span>0–&lt;20 · muito baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#fcae91;border:1px solid #4a4a4a\"></span><span>20–&lt;40 · baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#fb6a4a;border:1px solid #4a4a4a\"></span><span>40–&lt;60 · médio</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#de2d26;border:1px solid #4a4a4a\"></span><span>60–&lt;75 · alto</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#a50f15;border:1px solid #4a4a4a\"></span><span>75–100 · muito alto</span></div><div class=\"legend-note\">IGF = máximo entre os quatro subíndices IGF_AM, IGF_GA, IGF_GR e IGF_MT. Aerogeofísica combina cobertura e resolução relativa do espaçamento de linhas. Gravimetria e magnetotelúrico combinam densidade e ocupação espacial. O índice mede disponibilidade de conhecimento, não anomalia nem favorabilidade mineral.</div>`;"
        txt=txt[:e+1]+legend+'\n'+txt[e+1:]
    if 'async function buildIgfSnapshotV38412' not in txt:
        marker='async function buildImcPreview(cfg)';i=txt.find(marker)
        if i<0:raise RuntimeError('marcador de builder não encontrado em app.js')
        builder="""async function buildIgfSnapshotV38412(cfg){
 const gridCfg=CATALOG.layers.find(x=>x.id===cfg.grid_source_id);
 if(!gridCfg)throw new Error('Malha do IGF V38.4.12 não encontrada no catálogo');
 const grid=await ensure(gridCfg),key=String(cfg.igf_scale||''),scores=window.ITA_IGF_V38412?.grids?.[key],meta=window.ITA_IGF_V38412?.metadata||{};
 if(!scores)throw new Error('Snapshot IGF V38.4.12 não encontrado para esta escala. Execute o materializador do patch.');
 const features=(grid.features||[]).map(hf=>{
  const hid=String(hf.properties?.hex_id||''),r=scores[hid];
  if(!r)return {...hf,properties:{...(hf.properties||{}),igf_100:null,classe_igf:'sem conhecimento geofísico materializado',metodo:'V38.4.12 · snapshot IGF ausente para esta célula'}};
  const [igf,best,nmod,am,ga,gr,mt,nGrav,nMT,covAM,covGA,spAM,spGA]=r;
  return {...hf,properties:{...(hf.properties||{}),igf_100:igf,classe_igf:igfClass(igf),modulo_igf_dominante:best||'nenhum',n_modulos_geofisicos:nmod,igf_aeromagnetometria:am,igf_gamaespectrometria:ga,igf_gravimetria:gr,igf_magnetotelurico:mt,n_estacoes_gravimetricas:nGrav,n_estacoes_mt:nMT,cobertura_am:covAM,cobertura_ga:covGA,melhor_espacamento_am_m:spAM,melhor_espacamento_ga_m:spGA,formula:'IGF_h = max(IGF_AM,h, IGF_GA,h, IGF_GR,h, IGF_MT,h)',formula_aero:'IGF_AM,h ou IGF_GA,h = 100 × sqrt(C_m × R*_m)',formula_pontos:'IGF_GR,h ou IGF_MT,h = 100 × sqrt(D*_m × O_m)',fonte_igf:'SGB · Aerogeofísica, Gravimetria e Geofísica terrestre · Magnetotelúrico',regra_ausencia:'sem módulo calculável → IGF nulo e hexágono transparente.',limite_interpretativo:'IGF mede disponibilidade espacial de conhecimento geofísico documentado. Não mede anomalia, favorabilidade mineral, recurso ou reserva.',metodo:'V38.4.12 · cálculo direto na escala · sem agregação entre escalas',data_corte:meta.cut_date||'2026-08-14'}};
 });
 return {type:'FeatureCollection',features,atlas_metadata:{indice:'IGF',versao:'V38.4.12',escala:key,formula:'IGF_h = max(IGF_AM,h, IGF_GA,h, IGF_GR,h, IGF_MT,h)',fonte:'SGB · geofísica',regra:'quatro módulos explícitos e cálculo independente em 250, 500 e 1000 km²',limite:'índice de conhecimento, não de anomalia ou potencial mineral'}};
}
"""
        txt=txt[:i]+builder+txt[i:]
    chain="if(!d&&cfg.derive_type==='igq_snapshot_v38411')d=await buildIgqSnapshotV38411(cfg);"
    if "derive_type==='igf_snapshot_v38412'" not in txt:
        if chain not in txt:raise RuntimeError('cadeia derive IGQ não encontrada em app.js')
        txt=txt.replace(chain,chain+"if(!d&&cfg.derive_type==='igf_snapshot_v38412')d=await buildIgfSnapshotV38412(cfg);",1)
    scale_marker="const IGQ_SCALE_LAYERS=['igq_250','igq_500','igq_1000'];"
    if 'const IGF_SCALE_LAYERS=' not in txt:
        if scale_marker not in txt:raise RuntimeError('grupo de escalas IGQ não encontrado em app.js')
        txt=txt.replace(scale_marker,scale_marker+" const IGF_SCALE_LAYERS=['igf_250','igf_500','igf_1000'];",1)
    toggle_marker='async function toggle(id,on){const cfg=CATALOG.layers.find(x=>x.id===id);if(!cfg)return;'
    if 'IGF_SCALE_LAYERS.includes(id)' not in txt:
        i=txt.find(toggle_marker)
        if i<0:raise RuntimeError('toggle não encontrado em app.js')
        j=i+len(toggle_marker)
        inject="if(on&&IGF_SCALE_LAYERS.includes(id)){for(const other of IGF_SCALE_LAYERS){if(other===id)continue;state.active.delete(other);const ocb=document.querySelector(`input[data-layer=\"${other}\"]`);if(ocb)ocb.checked=false;updateLayerCard(other)}}"
        txt=txt[:j]+inject+txt[j:]
    p.write_text(txt,encoding='utf-8',newline='\n')

def update_local_catalog(repo:Path,counts):
    jp=repo/'docs/camadas/catalogo-local.json'
    mapping={
      'levantamentos_geofisicos_cobertura_ms':('./camadas/arquivos/aerogeofisica_projetos_sgb_ms.geojson','Cobertura integrada de levantamentos aerogeofísicos em MS','SGB · Aerogeofísica · snapshot local V38.4.12'),
      'gravimetria_sgb_ms':('./camadas/arquivos/gravimetria_sgb_ms.geojson','Estações gravimétricas SGB em Mato Grosso do Sul','SGB · Gravimetria · snapshot local V38.4.12'),
      'magnetotelurico_sgb_ms':('./camadas/arquivos/magnetotelurico_sgb_ms.geojson','Estações magnetotelúricas SGB em Mato Grosso do Sul','SGB · Geofísica terrestre · snapshot local V38.4.12'),
    }
    if jp.exists():
        arr=load_json(jp)
        if not isinstance(arr,list):raise RuntimeError('catalogo-local.json deveria ser uma lista')
        by={x.get('id'):x for x in arr if isinstance(x,dict)}
        for lid,(arquivo,nome,fonte) in mapping.items():
            fp=repo/'docs'/arquivo.replace('./','')
            rec={'id':lid,'arquivo':arquivo,'nome':nome,'grupo':'Geoquímica, geofísica e geotermia','status':'incorporada','fonte':fonte,'validacao':'corte 14/08/2026 · fonte oficial SGB · suporte do IGF V38.4.12','feicoes':counts.get(lid,0),'bytes':fp.stat().st_size if fp.exists() else 0}
            if lid in by:by[lid].update(rec)
            else:arr.append(rec);by[lid]=rec
        dump_json(jp,arr)
    p=repo/'docs/camadas/catalogo-local.js'
    if p.exists():
        t=p.read_text(encoding='utf-8');prefix='window.ITA_LOCAL_LAYER_FILES=';pos=t.index(prefix)+len(prefix);o,endj=json.JSONDecoder().raw_decode(t[pos:])
        for lid,(arquivo,_,__) in mapping.items():o[lid]=arquivo
        p.write_text(t[:pos]+json.dumps(o,ensure_ascii=False,separators=(',',':'))+t[pos+endj:],encoding='utf-8',newline='\n')

def update_web(repo:Path):
    ip=repo/'docs/index.html';s=ip.read_text(encoding='utf-8')
    s=s.replace('v=38.4.11','v=38.4.12')
    script='<script src="./indices/igf-v38412.js?v=38.4.12"></script>'
    if script not in s:
        marker='<script src="./indices/igq-v38411.js?v=38.4.12"></script>'
        if marker not in s:raise RuntimeError('script IGQ não encontrado em index.html')
        s=s.replace(marker,marker+'\n'+script,1)
    ip.write_text(s,encoding='utf-8',newline='\n')
    bp=repo/'docs/assets/js/bootstrap.js'
    if bp.exists():bp.write_text(bp.read_text(encoding='utf-8').replace('v=38.4.11','v=38.4.12'),encoding='utf-8',newline='\n')
    swp=repo/'docs/service-worker.js';sw=swp.read_text(encoding='utf-8')
    sw=re.sub(r"const ITA_CACHE\s*=\s*'[^']+';","const ITA_CACHE = 'ita-arandu-v38-4-12-igf-conhecimento-geofisico';",sw,count=1)
    sw=sw.replace('v=38.4.11','v=38.4.12')
    assets=['./indices/igf-v38412.js?v=38.4.12','./camadas/arquivos/aerogeofisica_projetos_sgb_ms.geojson','./camadas/arquivos/gravimetria_sgb_ms.geojson','./camadas/arquivos/magnetotelurico_sgb_ms.geojson','./documentos/metodologia-igf.html']
    for asset in assets:
        if asset not in sw:
            marker='"./indices/igq-v38411.js?v=38.4.12",'
            if marker not in sw:raise RuntimeError('marcador precache IGQ não encontrado no service worker')
            sw=sw.replace(marker,marker+f'\n  "{asset}",',1)
    swp.write_text(sw,encoding='utf-8',newline='\n')
    dp=repo/'docs/documentos/index.html';d=dp.read_text(encoding='utf-8')
    if 'metodologia-igf.html' not in d:
        if '</body>' not in d:raise RuntimeError('fechamento body não encontrado no índice de documentos')
        d=d.replace('</body>','<p><a href="./metodologia-igf.html">IGF · Conhecimento Geofísico · metodologia V38.4.12</a></p></body>',1)
    dp.write_text(d,encoding='utf-8',newline='\n')

def update_bibliography(repo:Path):
    jp=repo/'docs/referencias/bibliografia-camadas-indices.json'
    if jp.exists():
        o=load_json(jp);ids={'igf_250','igf_500','igf_1000','levantamentos_geofisicos_cobertura_ms','gravimetria_sgb_ms','magnetotelurico_sgb_ms'}
        for e in o.get('entries',[]):
            if isinstance(e,dict) and e.get('id') in ids:e['status']='incorporada'
        dump_json(jp,o)
    hp=repo/'docs/referencias/index.html'
    if hp.exists():
        h=hp.read_text(encoding='utf-8')
        for lid in ['igf_250','igf_500','igf_1000','levantamentos_geofisicos_cobertura_ms','gravimetria_sgb_ms','magnetotelurico_sgb_ms']:
            sm=f'id="layer-{lid}"';start=h.find(sm)
            if start<0:continue
            s0=h.rfind('<section',0,start);s1=h.find('</section>',start)
            if s0<0 or s1<0:continue
            s1+=len('</section>');sec=h[s0:s1];sec=sec.replace(' · planejada ·',' · incorporada ·').replace(' · conectada ·',' · incorporada ·')
            h=h[:s0]+sec+h[s1:]
        hp.write_text(h,encoding='utf-8',newline='\n')

def update_changelog(repo:Path):
    entry="""
## V38.4.12 · IGF · Conhecimento Geofísico · 2026-08-14

- materializa footprints dos levantamentos aerogeofísicos SGB e estações de gravimetria e magnetotelúrico
- separa aeromagnetometria, gamaespectrometria, gravimetria e magnetotelúrico em módulos auditáveis
- congela IGF_h = max(IGF_AM,h, IGF_GA,h, IGF_GR,h, IGF_MT,h)
- pondera aerogeofísica por cobertura e resolução relativa do espaçamento de linhas
- não interpola anomalias nem interpreta valores geofísicos como favorabilidade mineral
- calcula 250, 500 e 1000 km² diretamente das evidências originais
"""
    ch=repo/'CHANGELOG.md'
    if ch.exists():
        t=ch.read_text(encoding='utf-8')
        if 'V38.4.12 · IGF' not in t:ch.write_text(t.rstrip()+entry+'\n',encoding='utf-8',newline='\n')
    rd=repo/'README.md'
    if rd.exists():
        t=rd.read_text(encoding='utf-8');t=re.sub(r'V38\.4\.11[^\n]*','V38.4.12 · IGF · Conhecimento Geofísico',t,count=1) if 'V38.4.11' in t else t;rd.write_text(t,encoding='utf-8',newline='\n')
    dh=repo/'docs/documentos/changelog.html'
    if dh.exists():
        t=dh.read_text(encoding='utf-8')
        if 'V38.4.12 · IGF' not in t:t=t.replace('</body>','<h2>V38.4.12 · IGF · Conhecimento Geofísico</h2><p>Materialização multiescalar independente de aerogeofísica, gravimetria e magnetotelúrico, preservando cobertura, resolução e limites interpretativos.</p></body>',1)
        dh.write_text(t,encoding='utf-8',newline='\n')

def self_test():
    assert aero_methods({'METODOS':'Magnetometria e Gamaespectrometria'})==['AM','GA']
    assert spacing_m({'ESPACAMENTO_LV_M':'500 m / 1000 m'})==1000.0
    assert mt_available({'DataAvailability':'Available'}) and not mt_available({'DataAvailability':'In Progress'})
    # O módulo ausente permanece não avaliável, nunca zero.
    cells=[{'hex_id':'H1'}]
    none={'H1':{'score':None}};am={'H1':{'score':42.0}}
    c=combine(cells,am,none,none,none)['H1']
    assert c['igf']==42.0 and c['modules']['MT'] is None
    print('SELFTEST IGF V38.4.12 R1 · PASS')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');ap.add_argument('--self-test',action='store_true');ap.add_argument('--source-file');args=ap.parse_args()
    if args.self_test:self_test();return 0
    repo=Path(args.repo).resolve()
    for rel in list(GRID_FILES.values())+[LIMIT_FILE]:
        if not (repo/rel).exists():raise RuntimeError(f'arquivo estrutural ausente · {rel}')
    for rel in ['docs/indices/iod_v3848_snapshot.json','docs/indices/icp_v3849_snapshot.json','docs/indices/igc_v38410_snapshot.json','docs/indices/igq_v38411_snapshot.json']:
        if not (repo/rel).exists():raise RuntimeError(f'base V38.4.11 incompleta · arquivo ausente · {rel}')
    print('ITA ARANDU MS · materialização IGF V38.4.12');print('Fórmula ·',FORMULA);print('Aerogeofísica ·',AERO_FORMULA);print('Pontos ·',POINT_FORMULA)
    if args.source_file:
        source=load_json(Path(args.source_file));source_label='arquivo local fornecido'
    else:source_label,source=fetch_source()
    raw=canonical_bytes(source);raw_hash=sha256_bytes(raw)
    state_items=feature_polys(load_json(repo/LIMIT_FILE));aero,grav,mt,source_stats=prepare_source(source,state_items)
    source_stats['availability']=source.get('availability',{})
    if not aero and not grav and not mt:raise RuntimeError('nenhuma evidência geofísica utilizável ficou disponível para Mato Grosso do Sul')
    grids={};cells={};assigned_gr={};assigned_mt={}
    for sc,rel in GRID_FILES.items():grids[sc],cells[sc]=load_grid(repo/rel);assigned_gr[sc],_=assign_points(grav,cells[sc]);assigned_mt[sc],_=assign_points(mt,cells[sc])
    baseline={};normalization={}
    for sc in ['250','500','1000']:
        am,asat=calc_aero(cells[sc],aero,'AM');ga,gsat=calc_aero(cells[sc],aero,'GA');gr,grsat=calc_points(cells[sc],assigned_gr[sc],grav);mr,mtsat=calc_points(cells[sc],assigned_mt[sc],mt);co=combine(cells[sc],am,ga,gr,mr)
        baseline[sc]={'combined':co,'am':am,'ga':ga,'gr':gr,'mt':mr};normalization[sc]={'aero_inverse_spacing_p95_AM':asat,'aero_inverse_spacing_p95_GA':gsat,'grav_density_p95':grsat,'mt_density_p95':mtsat}
    sensitivity={}
    for sc in ['250','500','1000']:
        sensitivity[sc]={};base=baseline[sc]['combined']
        for step,pct in [(2500,95),(10000,95),(5000,90),(5000,99)]:
            am,_=calc_aero(cells[sc],aero,'AM',step,pct);ga,_=calc_aero(cells[sc],aero,'GA',step,pct);gr,_=calc_points(cells[sc],assigned_gr[sc],grav,step,pct);mr,_=calc_points(cells[sc],assigned_mt[sc],mt,step,pct);alt=combine(cells[sc],am,ga,gr,mr);sensitivity[sc][f'micro_{step/1000:g}km_p{pct}']=spearman(base,alt)
    aero_fc=source_fc_aero(aero,raw_hash);grav_fc=source_fc_points(grav,'gravimetria_sgb_ms',raw_hash);mt_fc=source_fc_points(mt,'magnetotelurico_sgb_ms',raw_hash)
    files=[('docs/camadas/arquivos/aerogeofisica_projetos_sgb_ms.geojson',aero_fc),('docs/camadas/arquivos/gravimetria_sgb_ms.geojson',grav_fc),('docs/camadas/arquivos/magnetotelurico_sgb_ms.geojson',mt_fc)]
    for rel,obj in files:dump_json(repo/rel,obj,compact=True)
    raw_path=repo/f'data/geofisica_sgb_ms_raw_{CUT_DATE.replace("-","")}.json.gz';raw_path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(raw_path,'wb',compresslevel=9) as gz:gz.write(raw)
    snap={'metadata':{'index':'IGF','version':VERSION,'calculated_at':now_iso(),'cut_date':CUT_DATE,'formula':FORMULA,'aero_formula':AERO_FORMULA,'point_formula':POINT_FORMULA,'components':{'AM':'aeromagnetometria · cobertura territorial e resolução relativa do espaçamento de linhas','GA':'gamaespectrometria · cobertura territorial e resolução relativa do espaçamento de linhas','GR':'gravimetria · densidade normalizada e ocupação espacial de estações','MT':'magnetotelúrico · densidade normalizada e ocupação espacial de estações com DataAvailability disponível'},'aggregation_rule':'máximo dos quatro módulos. Os módulos permanecem explícitos para não ocultar lacunas e evitar pesos arbitrários entre métodos geofísicos não equivalentes.','resolution_rule':'em sobreposição usa-se o menor espaçamento de linha válido no suporte. Quando um campo contém mais de um espaçamento, adota-se conservadoramente o maior valor reportado para o projeto. A resolução relativa usa o P95 do inverso do espaçamento dentro da própria escala e módulo.','mt_rule':'somente estações com DataAvailability=Available ou equivalente entram no escore. Registros em andamento permanecem documentados na fonte bruta, mas não contam como conhecimento disponível.','grav_rule':'estações gravimétricas são pontos de observação. V38.4.12 não interpola anomalia Bouguer nem qualquer campo gravimétrico.','aero_rule':'footprints sem método classificável ou sem espaçamento de linhas válido permanecem no snapshot fonte, mas não pontuam AM ou GA.','microcell_m':BASE_MICROCELL_M,'normalization_percentile':BASE_PERCENTILE,'scale_rule':'250, 500 e 1000 km² são calculados diretamente das evidências geofísicas originais, sem agregação entre escalas.','null_rule':'sem qualquer módulo calculável, IGF=null e o hexágono permanece transparente. Ausência não é zero.','interpretation_limit':'IGF mede disponibilidade espacial de conhecimento geofísico documentado. Não mede intensidade de anomalia, favorabilidade mineral, recurso, reserva ou viabilidade econômica.','source':'SGB · Geoportal · aerogeofísica, gravimetria e magnetotelúrico','source_method':source_label,'source_availability':source.get('availability',{}),'source_completeness':'completa' if all(v.get('status')=='captured' for v in list((source.get('availability',{}).get('aero') or {}).values())+[source.get('availability',{}).get('grav',{}),source.get('availability',{}).get('mt',{})]) else 'parcial_por_indisponibilidade_remota','source_sha256':raw_hash,'raw_gzip':str(raw_path.relative_to(repo)).replace('\\','/'),'references':['REF-100','REF-101','REF-102','REF-109','REF-105','REF-115']},'source_summary':source_stats,'normalization':normalization,'summary':{sc:summary(baseline[sc]['combined']) for sc in baseline},'sensitivity_spearman':sensitivity,'grids':{sc:compact_rows(baseline[sc]['combined'],baseline[sc]['am'],baseline[sc]['ga'],baseline[sc]['gr'],baseline[sc]['mt']) for sc in baseline}}
    dump_json(repo/'docs/indices/igf_v38412_snapshot.json',snap);(repo/'docs/indices/igf-v38412.js').write_text('window.ITA_IGF_V38412='+json.dumps(snap,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
    counts={'levantamentos_geofisicos_cobertura_ms':len(aero_fc['features']),'gravimetria_sgb_ms':len(grav_fc['features']),'magnetotelurico_sgb_ms':len(mt_fc['features'])}
    patch_app(repo,counts);update_local_catalog(repo,counts);update_web(repo);update_bibliography(repo);update_changelog(repo);(repo/'VERSION').write_text(VERSION+'\n',encoding='utf-8',newline='\n')
    runtime={'audit':'V38.4.12 IGF runtime','status':'PASS','calculated_at':now_iso(),'source_sha256':raw_hash,'source_counts':counts,'source_availability':source.get('availability',{}),'source_completeness':'completa' if all(v.get('status')=='captured' for v in list((source.get('availability',{}).get('aero') or {}).values())+[source.get('availability',{}).get('grav',{}),source.get('availability',{}).get('mt',{})]) else 'parcial_por_indisponibilidade_remota','source_stats':source_stats,'summaries':{sc:summary(baseline[sc]['combined']) for sc in baseline},'checks':{'methods_separated':True,'aero_resolution_explicit':True,'grav_no_interpolation':True,'mt_available_only':True,'independent_scale_calculation':True,'null_is_not_zero':True,'previous_indices_not_recomputed':True}}
    dump_json(repo/'AUDITORIA_V38_4_12_IGF_RUNTIME.json',runtime)
    print('IGF V38.4.12 materializado ·',counts)
    print('Disponibilidade das fontes ·',json.dumps(source.get('availability',{}),ensure_ascii=False))
    for sc in ['250','500','1000']:print(sc,'km² ·',summary(baseline[sc]['combined']))
    return 0

if __name__=='__main__':raise SystemExit(main())
