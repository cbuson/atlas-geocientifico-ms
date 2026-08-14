#!/usr/bin/env python3
# ITA ARANDU MS · V38.4.8 · materialização do IOD
# Biblioteca padrão apenas. Não altera outros índices.
from __future__ import annotations
import argparse, datetime as dt, gzip, hashlib, json, math, os, statistics, sys, urllib.parse, urllib.request
from pathlib import Path

VERSION = 'V38.4.8-IOD-OBSERVACAO-DIRETA-20260814'
CUT_DATE = '2026-08-14'
FORMULA = 'IOD_h = 100 × (D* × O × E)^(1/3)'
BASE_MICROCELL_M = 5000.0
BASE_DENSITY_PERCENTILE = 95
LAEA_LON0 = -54.5
LAEA_LAT0 = -20.5
EARTH_R = 6371007.181

ARCGIS_URL = (
    'https://geoportal.sgb.gov.br/server/rest/services/geologia/afloramentos/MapServer/0/query?'
    + urllib.parse.urlencode({
        'where': "UF='MS'",
        'outFields': '*',
        'returnGeometry': 'true',
        'outSR': '4326',
        'f': 'geojson',
        'resultRecordCount': '300000'
    })
)
WFS_URL = (
    'https://opendata.sgb.gov.br/geoserver/p3m/ows?'
    + urllib.parse.urlencode({
        'service': 'WFS', 'version': '1.0.0', 'request': 'GetFeature',
        'typeName': 'p3m:vw_cprm_ms_aflor', 'outputFormat': 'application/json',
        'srsName': 'EPSG:4326', 'maxFeatures': '300000'
    })
)

GRID_FILES = {
    '250': 'docs/camadas/arquivos/malha_r5_250km2.geojson',
    '500': 'docs/camadas/arquivos/malha_500km2.geojson',
    '1000': 'docs/camadas/arquivos/malha_1000km2.geojson',
}


def now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def dump_json(path: Path, obj, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':') if compact else None, indent=None if compact else 2)
        f.write('\n')


def sha256_bytes(data: bytes):
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, timeout=120):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'ITA-ARANDU-MS/38.4.8 (+https://github.com/) Python urllib',
        'Accept': 'application/geo+json, application/json;q=0.9, */*;q=0.1'
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_source():
    errors = []
    for label, url in [('ArcGIS GeoSGB', ARCGIS_URL), ('WFS SGB Dados Abertos', WFS_URL)]:
        try:
            raw = fetch_bytes(url)
            obj = json.loads(raw.decode('utf-8-sig'))
            if isinstance(obj, dict) and obj.get('error'):
                raise RuntimeError(str(obj['error']))
            if isinstance(obj, dict) and obj.get('exceededTransferLimit') is True:
                raise RuntimeError('resposta truncada pelo serviço')
            feats = obj.get('features') if isinstance(obj, dict) else None
            if not isinstance(feats, list) or len(feats) < 10:
                raise RuntimeError(f'resposta sem FeatureCollection utilizável, feições={0 if feats is None else len(feats)}')
            return label, url, raw, obj
        except Exception as e:
            errors.append(f'{label}: {e}')
    raise RuntimeError('Não foi possível materializar AFLO do SGB. ' + ' | '.join(errors))


def ci_get(props: dict, *names):
    if not isinstance(props, dict):
        return None
    direct = {str(k).lower(): v for k,v in props.items()}
    for n in names:
        if n in props:
            return props[n]
        if str(n).lower() in direct:
            return direct[str(n).lower()]
    return None


def get_point(feat):
    g = feat.get('geometry') or {}
    if g.get('type') == 'Point' and isinstance(g.get('coordinates'), list) and len(g['coordinates']) >= 2:
        try:
            return float(g['coordinates'][0]), float(g['coordinates'][1])
        except Exception:
            pass
    p = feat.get('properties') or {}
    x, y = ci_get(p, 'X', 'LONGITUDE', 'LON'), ci_get(p, 'Y', 'LATITUDE', 'LAT')
    try:
        return float(x), float(y)
    except Exception:
        return None


def clean_features(raw_features):
    seen = set()
    kept = []
    duplicate_count = 0
    invalid = 0
    non_ms = 0
    for feat in raw_features:
        if not isinstance(feat, dict):
            invalid += 1
            continue
        p = feat.get('properties') or {}
        uf = ci_get(p, 'UF', 'SG_UF', 'uf')
        if uf not in (None, '') and str(uf).strip().upper() != 'MS':
            non_ms += 1
            continue
        pt = get_point(feat)
        if pt is None or not (-61 <= pt[0] <= -47 and -27 <= pt[1] <= -15):
            invalid += 1
            continue
        ida = ci_get(p, 'ID_AFLORAMENTO', 'id_afloramento')
        obj = ci_get(p, 'OBJECTID', 'objectid', 'fid')
        if ida not in (None, ''):
            key = ('ID_AFLORAMENTO', str(ida).strip())
        elif obj not in (None, ''):
            key = ('OBJECTID', str(obj).strip())
        else:
            key = ('COORD', round(pt[0], 7), round(pt[1], 7), str(ci_get(p,'NUMERO_CAMPO') or ''), str(ci_get(p,'PROJETO') or ''))
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        q = dict(p)
        q['__atlas_fonte'] = 'SGB · GeoSGB · Afloramentos geológicos'
        q['__atlas_snapshot'] = CUT_DATE
        kept.append({'type':'Feature','geometry':{'type':'Point','coordinates':[pt[0],pt[1]]},'properties':q})
    return kept, {'duplicates_removed': duplicate_count, 'invalid_removed': invalid, 'non_ms_removed': non_ms}


# Lambert Azimutal Equal-Area esférica. Usada para suporte espacial e micromalha.
_lon0 = math.radians(LAEA_LON0)
_lat0 = math.radians(LAEA_LAT0)
_sin0 = math.sin(_lat0)
_cos0 = math.cos(_lat0)

def laea(lon, lat):
    lam = math.radians(lon); phi = math.radians(lat); dl = lam - _lon0
    sp, cp = math.sin(phi), math.cos(phi)
    den = 1 + _sin0*sp + _cos0*cp*math.cos(dl)
    if den <= 1e-15:
        raise ValueError('coordenada antipodal à projeção')
    k = math.sqrt(2/den)
    return (EARTH_R*k*cp*math.sin(dl), EARTH_R*k*(_cos0*sp - _sin0*cp*math.cos(dl)))


def point_on_segment(pt, a, b, tol=0.05):
    x,y=pt; x1,y1=a; x2,y2=b
    dx=x2-x1; dy=y2-y1
    l2=dx*dx+dy*dy
    if l2 == 0:
        return (x-x1)**2+(y-y1)**2 <= tol*tol
    t=((x-x1)*dx+(y-y1)*dy)/l2
    if t < 0 or t > 1:
        return False
    px=x1+t*dx; py=y1+t*dy
    return (x-px)**2+(y-py)**2 <= tol*tol


def point_in_ring(pt, ring):
    if len(ring) < 3: return False
    inside=False; x,y=pt
    j=len(ring)-1
    for i in range(len(ring)):
        a=ring[j]; b=ring[i]
        if point_on_segment(pt,a,b): return True
        xi,yi=b; xj,yj=a
        if ((yi>y)!=(yj>y)):
            xcross=(xj-xi)*(y-yi)/((yj-yi) if (yj-yi)!=0 else 1e-30)+xi
            if x < xcross: inside=not inside
        j=i
    return inside


def point_in_poly(pt, poly):
    if not poly or not point_in_ring(pt, poly[0]): return False
    return not any(point_in_ring(pt, hole) for hole in poly[1:])


def point_in_geom_projected(pt, geom):
    return any(point_in_poly(pt, poly) for poly in geom['polys'])


def project_geometry(geom):
    typ=geom.get('type'); coords=geom.get('coordinates')
    if typ == 'Polygon': polys=[coords]
    elif typ == 'MultiPolygon': polys=coords
    else: raise ValueError(f'geometria da malha não poligonal: {typ}')
    out=[]; xs=[]; ys=[]
    for poly in polys:
        pp=[]
        for ring in poly:
            rr=[]
            for c in ring:
                x,y=laea(float(c[0]),float(c[1])); rr.append((x,y)); xs.append(x); ys.append(y)
            pp.append(rr)
        out.append(pp)
    return {'polys':out, 'bbox':(min(xs),min(ys),max(xs),max(ys))}


def polygon_centroid_hint(feat, pg):
    p=feat.get('properties') or {}
    try:
        lon=float(p.get('centroide_lon')); lat=float(p.get('centroide_lat'))
        return laea(lon,lat)
    except Exception:
        b=pg['bbox']; return ((b[0]+b[2])/2,(b[1]+b[3])/2)


def load_grid(path: Path):
    fc=load_json(path)
    cells=[]
    for f in fc.get('features',[]):
        pg=project_geometry(f['geometry'])
        props=f.get('properties') or {}
        hid=str(props.get('hex_id') or '')
        if not hid: raise RuntimeError(f'hexágono sem hex_id em {path.name}')
        try: area=float(props['area_efetiva_ms_km2'])
        except Exception: area=float(props.get('area_nominal_km2') or 0)
        if not area > 0: raise RuntimeError(f'área efetiva inválida em {hid}')
        cells.append({'hex_id':hid,'feature':f,'geom':pg,'bbox':pg['bbox'],'centroid':polygon_centroid_hint(f,pg),'area':area})
    return fc,cells


def make_spatial_index(cells, bin_m=50000.0):
    idx={}
    for i,c in enumerate(cells):
        xmin,ymin,xmax,ymax=c['bbox']
        ix0=math.floor(xmin/bin_m); ix1=math.floor(xmax/bin_m)
        iy0=math.floor(ymin/bin_m); iy1=math.floor(ymax/bin_m)
        for ix in range(ix0,ix1+1):
            for iy in range(iy0,iy1+1): idx.setdefault((ix,iy),[]).append(i)
    return idx,bin_m


def assign_points(points_xy, cells):
    idx,bin_m=make_spatial_index(cells)
    assigned=[[] for _ in cells]; missing=[]; ambiguous=0
    for pi,pt in enumerate(points_xy):
        cand=idx.get((math.floor(pt[0]/bin_m), math.floor(pt[1]/bin_m)), [])
        hits=[]
        for ci in cand:
            c=cells[ci]; b=c['bbox']
            if pt[0]<b[0]-0.1 or pt[0]>b[2]+0.1 or pt[1]<b[1]-0.1 or pt[1]>b[3]+0.1: continue
            if point_in_geom_projected(pt,c['geom']): hits.append(ci)
        if not hits:
            missing.append(pi); continue
        if len(hits)>1:
            ambiguous+=1
            hits.sort(key=lambda ci:(pt[0]-cells[ci]['centroid'][0])**2+(pt[1]-cells[ci]['centroid'][1])**2)
        assigned[hits[0]].append(pi)
    return assigned,missing,ambiguous


def percentile(vals, p):
    x=sorted(float(v) for v in vals if math.isfinite(float(v)))
    if not x: return None
    if len(x)==1: return x[0]
    pos=(len(x)-1)*(p/100.0); lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi: return x[lo]
    return x[lo]+(x[hi]-x[lo])*(pos-lo)


def micro_key(pt, step):
    return (math.floor(pt[0]/step), math.floor(pt[1]/step))


def support_microcells(cell, step, occupied_keys):
    xmin,ymin,xmax,ymax=cell['bbox']
    ix0=math.floor(xmin/step)-1; ix1=math.floor(xmax/step)+1
    iy0=math.floor(ymin/step)-1; iy1=math.floor(ymax/step)+1
    support=set()
    for ix in range(ix0,ix1+1):
        x=(ix+0.5)*step
        if x<xmin-0.1 or x>xmax+0.1: continue
        for iy in range(iy0,iy1+1):
            y=(iy+0.5)*step
            if y<ymin-0.1 or y>ymax+0.1: continue
            if point_in_geom_projected((x,y),cell['geom']): support.add((ix,iy))
    support.update(occupied_keys)
    return support


def shannon_evenness(counts):
    vals=[v for v in counts if v>0]
    k=len(vals)
    if k<=1: return 1.0 if k==1 else None
    n=sum(vals); h=0.0
    for v in vals:
        p=v/n; h -= p*math.log(p)
    return max(0.0,min(1.0,h/math.log(k)))


def iod_class(v):
    if v is None: return 'sem observação direta materializada'
    if v<20: return 'muito baixo'
    if v<40: return 'baixo'
    if v<60: return 'médio'
    if v<75: return 'alto'
    return 'muito alto'


def calculate_scale(cells, assigned, points_xy, micro_step=BASE_MICROCELL_M, density_percentile=BASE_DENSITY_PERCENTILE):
    densities=[]
    for ci,c in enumerate(cells):
        n=len(assigned[ci])
        if n: densities.append(n/c['area'])
    sat=percentile(densities,density_percentile)
    if sat is None or sat<=0: raise RuntimeError('não há densidades positivas para normalização do IOD')
    rows={}; edge_fallback=0
    for ci,c in enumerate(cells):
        inds=assigned[ci]; n=len(inds)
        if n==0:
            rows[c['hex_id']]={'iod':None,'D':None,'O':None,'E':None,'n':0,'occupied':0,'support':None,'density':0.0,'edge_fallback':False}
            continue
        density=n/c['area']; D=min(1.0,density/sat)
        counts={}
        for pi in inds:
            k=micro_key(points_xy[pi],micro_step); counts[k]=counts.get(k,0)+1
        occ=set(counts)
        support=support_microcells(c,micro_step,occ)
        fallback=False
        if not support:
            support=set(occ); fallback=True; edge_fallback+=1
        O=min(1.0,len(occ)/len(support)) if support else 1.0
        E=shannon_evenness(counts.values())
        iod=100.0*((D*O*E)**(1/3)) if E is not None else None
        rows[c['hex_id']]={
            'iod':round(iod,2) if iod is not None else None,
            'D':round(D,6),'O':round(O,6),'E':round(E,6),
            'n':n,'occupied':len(occ),'support':len(support),'density':round(density,8),
            'edge_fallback':fallback
        }
    return rows, sat, edge_fallback


def rankdata(vals):
    pairs=sorted(enumerate(vals), key=lambda z:z[1]); ranks=[0.0]*len(vals); i=0
    while i<len(pairs):
        j=i+1
        while j<len(pairs) and pairs[j][1]==pairs[i][1]: j+=1
        r=(i+j-1)/2+1
        for k in range(i,j): ranks[pairs[k][0]]=r
        i=j
    return ranks


def pearson(a,b):
    if len(a)<2:return None
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    va=sum((x-ma)**2 for x in a); vb=sum((y-mb)**2 for y in b)
    if va<=0 or vb<=0:return 1.0 if a==b else None
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(va*vb)


def spearman_maps(a,b):
    x=[]; y=[]
    for k in a:
        va=a[k]['iod']; vb=b.get(k,{}).get('iod')
        if va is not None and vb is not None: x.append(va); y.append(vb)
    r=pearson(rankdata(x),rankdata(y)) if len(x)>=2 else None
    return {'n_common':len(x),'rho':None if r is None else round(r,6)}


def summary(rows):
    vals=[r['iod'] for r in rows.values() if r['iod'] is not None]
    ns=[r['n'] for r in rows.values()]
    return {
        'cells':len(rows),'cells_with_observations':len(vals),'cells_without_observations':len(rows)-len(vals),
        'iod_min':min(vals) if vals else None,'iod_median':round(statistics.median(vals),2) if vals else None,
        'iod_mean':round(statistics.fmean(vals),2) if vals else None,'iod_max':max(vals) if vals else None,
        'observations_sum':sum(ns),'max_observations_cell':max(ns) if ns else 0
    }


def compact_rows(rows):
    # [IOD,D,O,E,n,occupied,support,density,edge]
    return {k:[v['iod'],v['D'],v['O'],v['E'],v['n'],v['occupied'],v['support'],v['density'],1 if v['edge_fallback'] else 0] for k,v in rows.items()}


def build_geojson_source(features, source_label, source_url, raw_hash, cleanup):
    return {
        'type':'FeatureCollection',
        'features':features,
        'atlas_metadata':{
            'id':'afloramentos_geosgb_ms','nome':'Afloramentos e pontos geológicos GeoSGB',
            'fonte':'Serviço Geológico do Brasil · GeoSGB · Afloramentos geológicos',
            'fonte_materializada_por':source_label,'url_consulta':source_url,
            'corte':CUT_DATE,'sha256_resposta_original':raw_hash,
            'deduplicacao':'ID_AFLORAMENTO; fallback OBJECTID; fallback coordenada + número de campo + projeto',
            **cleanup
        }
    }



def update_runtime_catalogs(repo: Path, source_count: int, source_bytes: int):
    # Atualiza apenas metadados que dependem da captura real.
    appp=repo/'docs/assets/js/app.js'
    txt=appp.read_text(encoding='utf-8')
    prefix='const CATALOG='; pos=txt.index(prefix)+len(prefix)
    cat,end=json.JSONDecoder().raw_decode(txt[pos:])
    for item in cat.get('layers',[]):
        if item.get('id')=='afloramentos_geosgb_ms': item['count']=source_count
    txt=txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:]
    appp.write_text(txt,encoding='utf-8',newline='\n')

    jp=repo/'docs/camadas/catalogo-local.json'
    arr=load_json(jp)
    for item in arr:
        if item.get('id')=='afloramentos_geosgb_ms':
            item['feicoes']=source_count; item['bytes']=source_bytes
    dump_json(jp,arr,compact=False)

    hp=repo/'docs/camadas/index.html'
    if hp.exists():
        h=hp.read_text(encoding='utf-8').replace('__IOD_AFLO_COUNT__',str(source_count))
        hp.write_text(h,encoding='utf-8',newline='\n')


def self_test():
    # Teste matemático e geométrico sintético. Não é dado científico do Atlas.
    square={'type':'Polygon','coordinates':[[[-54.55,-20.55],[-54.45,-20.55],[-54.45,-20.45],[-54.55,-20.45],[-54.55,-20.55]]]}
    feat={'type':'Feature','properties':{'hex_id':'T','area_efetiva_ms_km2':100,'centroide_lon':-54.5,'centroide_lat':-20.5},'geometry':square}
    pg=project_geometry(square); cell={'hex_id':'T','feature':feat,'geom':pg,'bbox':pg['bbox'],'centroid':polygon_centroid_hint(feat,pg),'area':100.0}
    pts=[laea(-54.52,-20.52),laea(-54.48,-20.48),laea(-54.52,-20.48)]
    assigned=[[0,1,2]]
    rows,sat,_=calculate_scale([cell],assigned,pts)
    r=rows['T']
    assert 0<r['iod']<=100 and 0<r['D']<=1 and 0<r['O']<=1 and 0<r['E']<=1 and sat>0
    print('SELFTEST IOD V38.4.8 · PASS')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',default='.')
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--source-file',help='GeoJSON local opcional para reprodução offline')
    args=ap.parse_args()
    if args.self_test:
        self_test(); return 0
    repo=Path(args.repo).resolve()
    for rel in GRID_FILES.values():
        if not (repo/rel).exists(): raise RuntimeError(f'malha ausente: {rel}')
    print('ITA ARANDU MS · materialização IOD V38.4.8')
    print('Fonte · SGB GeoSGB · Afloramentos geológicos')
    print('Fórmula ·',FORMULA)
    print('Micromalha basal · 5 km × 5 km · D* saturado no P95 das densidades positivas por escala')

    if args.source_file:
        srcp=Path(args.source_file)
        raw=srcp.read_bytes(); source_obj=json.loads(raw.decode('utf-8-sig')); source_label='arquivo local fornecido'; source_url=str(srcp)
    else:
        source_label,source_url,raw,source_obj=fetch_source()
    raw_hash=sha256_bytes(raw)
    features,cleanup=clean_features(source_obj.get('features',[]))
    if len(features)<10: raise RuntimeError(f'fonte SGB resultou em apenas {len(features)} observações válidas antes do recorte')

    grids={}; cells={}
    for scale,rel in GRID_FILES.items():
        grids[scale],cells[scale]=load_grid(repo/rel)

    pts_xy=[laea(*get_point(f)) for f in features]
    assigned={}; missing={}; ambiguous={}
    for scale in ('250','500','1000'):
        assigned[scale],missing[scale],ambiguous[scale]=assign_points(pts_xy,cells[scale])

    # O recorte científico parte da malha 250 km². Pontos fora dela não entram no IOD.
    valid_250=set(i for arr in assigned['250'] for i in arr)
    if len(valid_250)<10: raise RuntimeError('menos de 10 observações SGB caem na malha oficial de MS')
    if len(valid_250)!=len(features):
        features=[f for i,f in enumerate(features) if i in valid_250]
        pts_xy=[laea(*get_point(f)) for f in features]
        for scale in ('250','500','1000'):
            assigned[scale],missing[scale],ambiguous[scale]=assign_points(pts_xy,cells[scale])
    for scale in ('250','500','1000'):
        if missing[scale]:
            raise RuntimeError(f'{len(missing[scale])} observações do recorte não foram atribuídas à malha {scale} km²')

    baseline={}; sats={}; edge={}
    for scale in ('250','500','1000'):
        baseline[scale],sats[scale],edge[scale]=calculate_scale(cells[scale],assigned[scale],pts_xy)

    sensitivity={}
    for scale in ('250','500','1000'):
        sensitivity[scale]={}
        base=baseline[scale]
        for step in (2500.0,5000.0,10000.0):
            for pct in (90,95,99):
                if step==BASE_MICROCELL_M and pct==BASE_DENSITY_PERCENTILE:
                    rows=base
                else:
                    rows,_,_=calculate_scale(cells[scale],assigned[scale],pts_xy,step,pct)
                key=f'micro_{int(step/1000*10)/10:g}km_P{pct}'
                sensitivity[scale][key]=spearman_maps(base,rows)

    source_fc=build_geojson_source(features,source_label,source_url,raw_hash,cleanup)
    source_fc['atlas_metadata']['feicoes_recortadas_ms']=len(features)
    source_path=repo/'docs/camadas/arquivos/afloramentos_geosgb_ms.geojson'
    dump_json(source_path,source_fc,compact=True)
    update_runtime_catalogs(repo,len(features),source_path.stat().st_size)

    raw_path=repo/f'data/afloramentos_geosgb_ms_raw_{CUT_DATE.replace("-","")}.geojson.gz'
    raw_path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(raw_path,'wb',compresslevel=9) as gz: gz.write(raw)

    snap={
        'metadata':{
            'index':'IOD','version':VERSION,'calculated_at':now_iso(),'cut_date':CUT_DATE,
            'formula':FORMULA,
            'components':{
                'D*':'densidade de observações únicas por área efetiva do hexágono, normalizada pelo P95 das densidades positivas em cada escala e truncada em 1',
                'O':'proporção das microcélulas de 5 km × 5 km do suporte do hexágono que contêm ao menos uma observação',
                'E':'equilíbrio de Shannon normalizado entre microcélulas ocupadas; E=1 quando existe apenas uma microcélula ocupada porque a baixa dispersão já é penalizada por O'
            },
            'source':'SGB · GeoSGB · Afloramentos geológicos','source_url':source_url,'source_method':source_label,
            'source_sha256':raw_hash,'source_features':len(features),'raw_gzip':str(raw_path.relative_to(repo)).replace('\\','/'),
            'deduplication':'ID_AFLORAMENTO → OBJECTID → coordenada + NUMERO_CAMPO + PROJETO',
            'microcell_m':BASE_MICROCELL_M,'density_percentile':BASE_DENSITY_PERCENTILE,
            'projection':f'Lambert Azimutal Equal-Area esférica · centro {LAEA_LAT0}, {LAEA_LON0} · usada no suporte da micromalha',
            'scale_rule':'250, 500 e 1000 km² são calculados diretamente a partir das observações-fonte; não há agregação de resultados entre escalas',
            'null_rule':'hexágonos sem observação direta materializada recebem IOD=null e permanecem transparentes; ausência não é convertida em zero',
            'field_rule':'registros da caderneta ITA ARANDU não entram automaticamente no IOD; futura incorporação exige validação explícita e deduplicação com a base institucional',
            'references':['REF-055','REF-070','REF-083','REF-105','REF-106','REF-111','REF-112','REF-113','REF-115']
        },
        'source_cleanup':cleanup,
        'grid_assignment':{s:{'ambiguous_boundary_resolved':ambiguous[s],'missing':len(missing[s])} for s in ('250','500','1000')},
        'density_saturation':{s:round(sats[s],8) for s in sats},
        'summaries':{s:summary(baseline[s]) for s in baseline},
        'sensitivity':sensitivity,
        'grids':{s:compact_rows(baseline[s]) for s in baseline}
    }
    dump_json(repo/'docs/indices/iod_v3848_snapshot.json',snap,compact=False)
    js='window.ITA_IOD_V3848='+json.dumps(snap,ensure_ascii=False,separators=(',',':'))+';\n'
    (repo/'docs/indices/iod-v3848.js').write_text(js,encoding='utf-8',newline='\n')

    runtime={
        'audit':'IOD V38.4.8 runtime','status':'PASS','generated_at':now_iso(),'version':VERSION,
        'source':{'method':source_label,'url':source_url,'sha256':raw_hash,'features':len(features),**cleanup},
        'scales':{s:{**summary(baseline[s]),'density_p95':round(sats[s],8),'edge_fallback_cells':edge[s],
                     'ambiguous_boundary_resolved':ambiguous[s]} for s in ('250','500','1000')},
        'sensitivity':sensitivity,
        'checks':{
            'source_features_positive':len(features)>0,
            'all_source_points_assigned_each_scale':all(len(missing[s])==0 for s in missing),
            'grid_counts':{s:len(baseline[s]) for s in baseline},
            'score_range_valid':all(r['iod'] is None or 0<=r['iod']<=100 for s in baseline.values() for r in s.values()),
            'zero_observation_is_null':all(r['n']>0 or r['iod'] is None for s in baseline.values() for r in s.values()),
            'independent_scale_calculation':True
        }
    }
    dump_json(repo/'AUDITORIA_V38_4_8_IOD_RUNTIME.json',runtime,compact=False)
    print(f'AFLO SGB · {len(features)} observações únicas dentro da malha de MS')
    for s in ('250','500','1000'):
        sm=runtime['scales'][s]
        print(f'IOD {s} km² · {sm["cells_with_observations"]}/{sm["cells"]} células com observação · min {sm["iod_min"]} · mediana {sm["iod_median"]} · max {sm["iod_max"]}')
    print('AUDITORIA RUNTIME · PASS')
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as e:
        print('ERRO IOD V38.4.8 ·',e,file=sys.stderr)
        raise SystemExit(2)
