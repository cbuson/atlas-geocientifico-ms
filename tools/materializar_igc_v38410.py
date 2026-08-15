#!/usr/bin/env python3
# ITA ARANDU MS · V38.4.10 · materialização do IGC
# Biblioteca padrão apenas. Não altera resultados de IOD ou ICP.
from __future__ import annotations
import argparse, datetime as dt, gzip, hashlib, json, math, re, statistics, urllib.parse, urllib.request
from pathlib import Path

VERSION='V38.4.10-IGC-CONTROLE-GEOCRONOLOGICO-20260814'
CUT_DATE='2026-08-14'
FORMULA='IGC_h = 100 × (G × U_age × Q_age)^(1/3)'
G_FORMULA='G = sqrt(D* × O)'
BASE_MICROCELL_M=5000.0
BASE_DENSITY_PERCENTILE=95
SUPPORT_N=9
LAEA_LON0=-54.5
LAEA_LAT0=-20.5
EARTH_R=6371007.181
BBOX_MS=(-58.3,-24.3,-50.6,-17.0)
SERVICE_ROOT='https://geoportal.sgb.gov.br/server/rest/services/geologia/geocronologia/MapServer'
MAIN_SERVICE=SERVICE_ROOT+'/0'
TABLES={1:'concordia',2:'frequencia',3:'isocrona',4:'pb_evap',5:'simples'}
# IDs dos relacionamentos publicados pela camada 0 do GeoSGB.
# R2 preserva explicitamente o OBJECTID da feição de origem em cada linha relacionada.
# Isso evita depender exclusivamente de CODIGO para reconstruir o vínculo amostra ↔ resultado.
RELATIONSHIPS={0:'pb_evap',1:'simples',2:'concordia',3:'isocrona',4:'frequencia'}
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
    req=urllib.request.Request(url,headers={'User-Agent':'ITA-ARANDU-MS/38.4.10 Python urllib','Accept':'application/json, application/geo+json;q=0.9, */*;q=0.1'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8-sig'))

def query_url(layer,params):
    return f'{SERVICE_ROOT}/{layer}/query?'+urllib.parse.urlencode(params,safe=',()')

def id_key(v):
    if v is None:return None
    try:
        x=float(v)
        if math.isfinite(x) and abs(x-round(x))<1e-8:return str(int(round(x)))
    except Exception:pass
    s=str(v).strip()
    return s or None

def fmt_sql_number(v):
    k=id_key(v)
    if k is None:return None
    try:return str(int(k))
    except Exception:
        try:return ('%.12g'%float(k))
        except Exception:return None

def related_query_url(params):
    return MAIN_SERVICE+'/queryRelatedRecords?'+urllib.parse.urlencode(params,safe=',()')

def _append_related_groups(obj,name,rows,origin_to_sample=None):
    groups=obj.get('relatedRecordGroups') or []
    n0=len(rows)
    origin_to_sample=origin_to_sample or {}
    for group in groups:
        origin=id_key(group.get('objectId'))
        sample_id=origin_to_sample.get(origin)
        for rec in group.get('relatedRecords') or []:
            attrs=rec.get('attributes') or rec.get('properties') or {}
            attrs=dict(attrs)
            attrs['__atlas_tabela_metodo']=name
            if origin is not None:attrs['__atlas_origin_objectid']=origin
            if sample_id is not None:attrs['__atlas_sample_id']=sample_id
            rows.append(attrs)
    return len(rows)-n0

def _fetch_table_direct(layer,name,sample_ids):
    rows=[]
    for i in range(0,len(sample_ids),100):
        part=sample_ids[i:i+100]
        if not part:continue
        where='CODIGO IN ('+','.join(part)+')'
        obj=fetch_json(query_url(layer,{'where':where,'outFields':'*','returnGeometry':'false','f':'json'}))
        if obj.get('error'):raise RuntimeError(f'tabela {name} · {obj["error"]}')
        for row in obj.get('features') or []:
            attrs=row.get('attributes') or row.get('properties') or {}
            attrs=dict(attrs);attrs['__atlas_tabela_metodo']=name
            sid=id_key(ci_get(attrs,'CODIGO'))
            if sid is not None:attrs['__atlas_sample_id']=sid
            rows.append(attrs)
    return rows

def fetch_source():
    xmin,ymin,xmax,ymax=BBOX_MS
    common={'where':'1=1','geometry':f'{xmin},{ymin},{xmax},{ymax}','geometryType':'esriGeometryEnvelope','inSR':'4326','spatialRel':'esriSpatialRelIntersects','f':'json'}
    id_obj=fetch_json(query_url(0,{**common,'returnIdsOnly':'true'}))
    if id_obj.get('error'):raise RuntimeError(str(id_obj['error']))
    object_ids=id_obj.get('objectIds') or []
    if not object_ids:raise RuntimeError('GeoSGB Geocronologia não retornou identificadores no envelope de MS')
    feats=[]
    for i in range(0,len(object_ids),250):
        ids=object_ids[i:i+250]
        obj=fetch_json(query_url(0,{'where':'1=1','objectIds':','.join(str(x) for x in ids),'outFields':'*','returnGeometry':'true','outSR':'4326','f':'geojson'}))
        if obj.get('error'):raise RuntimeError(str(obj['error']))
        feats.extend(obj.get('features') or [])
    seen=set();main=[]
    for f in feats:
        p=f.get('properties') or {};oid=p.get('OBJECTID',f.get('id'))
        key=('oid',str(oid)) if oid not in (None,'') else ('raw',json.dumps([f.get('geometry'),p],ensure_ascii=False,sort_keys=True))
        if key in seen:continue
        seen.add(key);main.append(f)

    sample_ids=[];origin_oids=[];origin_to_sample={}
    for f in main:
        p=f.get('properties') or {}
        n=fmt_sql_number(p.get('ID'))
        if n is not None:sample_ids.append(n)
        oo=id_key(p.get('OBJECTID',f.get('id')))
        if oo is not None:
            origin_oids.append(oo)
            if n is not None:origin_to_sample[oo]=id_key(n)
    sample_ids=list(dict.fromkeys(sample_ids));origin_oids=list(dict.fromkeys(origin_oids))

    table_rows={name:[] for name in TABLES.values()}
    fetch_mode={name:'none' for name in TABLES.values()}
    relation_errors={}

    # Via primária R1 · relacionamentos oficiais da camada 0.
    # O endpoint queryRelatedRecords usa OBJECTID da feição de origem e evita
    # o problema observado no corte anterior, no qual filtros CODIGO IN (...)
    # podiam retornar zero linhas embora o relacionamento existisse no serviço.
    for rel_id,name in RELATIONSHIPS.items():
        rows=[];failed=None
        for i in range(0,len(origin_oids),100):
            part=origin_oids[i:i+100]
            if not part:continue
            try:
                obj=fetch_json(related_query_url({'objectIds':','.join(part),'relationshipId':str(rel_id),'outFields':'*','returnGeometry':'false','f':'json'}))
                if obj.get('error'):
                    failed=str(obj['error']);break
                _append_related_groups(obj,name,rows,origin_to_sample)
            except Exception as exc:
                failed=str(exc);break
        if rows:
            table_rows[name]=rows;fetch_mode[name]='queryRelatedRecords'
        if failed:relation_errors[name]=failed

    # Fallback compatível com o materializador original. É usado por tabela,
    # somente quando queryRelatedRecords não retornou linhas para aquele método.
    for layer,name in TABLES.items():
        if table_rows[name]:continue
        try:
            rows=_fetch_table_direct(layer,name,sample_ids)
            if rows:
                table_rows[name]=rows;fetch_mode[name]='CODIGO_IN_fallback'
        except Exception as exc:
            relation_errors[name]=(relation_errors.get(name,'')+' | fallback '+str(exc)).strip(' |')

    total_related=sum(len(v) for v in table_rows.values())
    print(f'GeoSGB · registros pontuais recuperados no envelope · {len(main)}')
    print(f'GeoSGB · amostras com ID institucional · {len(sample_ids)}')
    print('GeoSGB · resultados relacionados · '+', '.join(f'{k}={len(v)}' for k,v in table_rows.items()))
    print('GeoSGB · modo de captura · '+', '.join(f'{k}={fetch_mode[k]}' for k in sorted(fetch_mode)))
    if total_related==0:
        detail='; '.join(f'{k}: {v}' for k,v in relation_errors.items())
        raise RuntimeError('GeoSGB retornou pontos geocronológicos, mas nenhuma linha analítica relacionada pôde ser recuperada. '+('Diagnóstico: '+detail if detail else 'Relacionamentos sem linhas para as amostras consultadas.'))

    merged={'main':{'type':'FeatureCollection','features':main},'tables':table_rows,'atlas_fetch':{'service':SERVICE_ROOT,'main_ids_bbox':len(object_ids),'main_retrieved':len(main),'sample_ids':len(sample_ids),'origin_objectids':len(origin_oids),'related_rows':{k:len(v) for k,v in table_rows.items()},'related_fetch_mode':fetch_mode,'related_fetch_errors':relation_errors,'fix':'R2 · queryRelatedRecords com vínculo explícito OBJECTID origem → ID amostra + CODIGO/AMOSTRA fallback'}}
    return 'ArcGIS REST GeoSGB · queryRelatedRecords com vínculo explícito de origem + fallback CODIGO/AMOSTRA',SERVICE_ROOT,merged


def ci_get(props,*names):
    if not isinstance(props,dict):return None
    low={str(k).lower():v for k,v in props.items()}
    for n in names:
        if n in props:return props[n]
        if str(n).lower() in low:return low[str(n).lower()]
    return None

def nonempty(v):
    if v is None:return False
    if isinstance(v,str):return bool(v.strip()) and v.strip().lower() not in {'null','none','nan','não informado','nao informado','sem informação','sem informacao'}
    return True

def num(v):
    try:
        x=float(v);return x if math.isfinite(x) else None
    except Exception:return None

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
        if find_poly(laea(*pt),state_items,idx,bin_m) is None:outside+=1;continue
        kept.append(f)
    return kept,{'invalid_geometry_removed':invalid,'outside_ms_removed':outside}

def norm_text(v):
    if v is None:return None
    t=re.sub(r'\s+',' ',str(v).strip()).upper()
    return t or None

def method_rows_by_sample(table_rows):
    out={}
    for name,rows in table_rows.items():
        for r in rows:
            # R2 · o vínculo nativo do ArcGIS tem prioridade. CODIGO permanece fallback.
            k=id_key(ci_get(r,'__atlas_sample_id')) or id_key(ci_get(r,'CODIGO'))
            rr=dict(r);rr['__atlas_tabela_metodo']=name
            if k is not None:out.setdefault('ID:'+k,[]).append(rr)
            am=norm_text(ci_get(r,'AMOSTRA'))
            if am:out.setdefault('AMOSTRA:'+am,[]).append(rr)
    return out

def row_blocks(row,main_props):
    method=ci_get(row,'METODO_ANALITICO') or ci_get(main_props,'METODOS')
    material=ci_get(row,'MATERIAL_ANALISADO') or ci_get(main_props,'MATERIAIS_ANALISADOS')
    age=num(ci_get(row,'IDADE_MAX'))
    if age is None or age<=0:
        age2=num(ci_get(row,'IDADE_MIN'));age=age2 if age2 is not None and age2>0 else None
    err=num(ci_get(row,'ERRO_MAX'))
    if err is None:err=num(ci_get(row,'ERRO_MIN'))
    bib=ci_get(row,'BIBLIOGRAFIA');authors=ci_get(row,'AUTORES');year=ci_get(row,'ANO_PUB')
    ref=nonempty(bib) or (nonempty(authors) and nonempty(year))
    return {'metodo':nonempty(method),'material':nonempty(material),'idade':age is not None,'incerteza':err is not None and err>=0,'referencia':ref},method,material,age,err,bib,authors,year

def independent_key(feat):
    p=feat.get('properties') or {};pt=get_point(feat) or (None,None)
    k=id_key(ci_get(p,'ID'))
    if k:return 'ID:'+k
    am=ci_get(p,'AMOSTRA')
    return f'AMOSTRA_COORD:{str(am or "SEM_AMOSTRA").strip().upper()}:{round(pt[0],6)}:{round(pt[1],6)}'

def build_units(features,rows_by_id):
    groups={}
    for f in features:
        k=independent_key(f);p=f.get('properties') or {};sid=id_key(ci_get(p,'ID'));rows=[]
        if sid:rows.extend(rows_by_id.get('ID:'+sid,[]))
        if not rows:
            am=norm_text(ci_get(p,'AMOSTRA'))
            if am:rows.extend(rows_by_id.get('AMOSTRA:'+am,[]))
        g=groups.setdefault(k,{'key':k,'features':[],'points':[],'rows':[]})
        g['features'].append(f);g['points'].append(get_point(f));g['rows'].extend(rows)
    units=[];excluded_no_direct=0
    for k,g in groups.items():
        # dedup dos resultados relacionados por tabela + OBJECTID
        seen=set();rows=[]
        for r in g['rows']:
            rk=(str(r.get('__atlas_tabela_metodo','')),str(ci_get(r,'OBJECTID') or json.dumps(r,ensure_ascii=False,sort_keys=True)))
            if rk in seen:continue
            seen.add(rk);rows.append(r)
        props={}
        keys=set()
        for f in g['features']:keys.update((f.get('properties') or {}).keys())
        for name in keys:
            for f in g['features']:
                v=(f.get('properties') or {}).get(name)
                if nonempty(v):props[name]=v;break
        scored=[]
        for r in rows:
            blocks,method,material,age,err,bib,authors,year=row_blocks(r,props)
            q=sum(1 for v in blocks.values() if v)/5
            core=blocks['metodo'] and blocks['idade']
            if core:scored.append({'row':r,'blocks':blocks,'q':q,'method':method,'material':material,'age':age,'error':err,'bibliography':bib,'authors':authors,'year':year})
        if not scored:
            excluded_no_direct+=1;continue
        scored.sort(key=lambda z:(z['q'],z['blocks']['incerteza'],z['blocks']['referencia']),reverse=True)
        best=scored[0];pts=[p for p in g['points'] if p]
        lon=statistics.median([p[0] for p in pts]);lat=statistics.median([p[1] for p in pts])
        units.append({'key':k,'point':(lon,lat),'q':best['q'],'blocks':best['blocks'],'best':best,'n_main_records':len(g['features']),'n_related_core':len(scored),'props':props})
    units.sort(key=lambda u:u['key'])
    return units,excluded_no_direct

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
        i=find_poly(laea(*u['point']),geo_items,idx,bin_m)
        if i is None:u['geology_uid']=None;u['geology_sigla']='';u['geology_nome']='';missing+=1
        else:
            g=geo_items[i];u['geology_uid']=g['uid'];u['geology_sigla']=g['sigla'];u['geology_nome']=g['nome']
    return missing

def annotate_source_features(features,units):
    gm={u['key']:u for u in units}
    out=[]
    for f in features:
        k=independent_key(f)
        if k not in gm:continue
        u=gm[k];p=f.setdefault('properties',{});b=u['best']
        p['__atlas_chave_independente']=u['key'];p['__atlas_q_age']=round(u['q'],4)
        p['__atlas_idade_ma']=b['age'];p['__atlas_incerteza_ma']=b['error'];p['__atlas_metodo_analitico']=b['method'];p['__atlas_material_analisado']=b['material']
        p['__atlas_referencia']=b['bibliography'] or ('; '.join(str(x) for x in [b['authors'],b['year']] if nonempty(x)) or None)
        p['__atlas_n_resultados_diretos']=u['n_related_core'];p['__atlas_unidade_geologica_id']=u.get('geology_uid');p['__atlas_unidade_geologica_sigla']=u.get('geology_sigla');p['__atlas_unidade_geologica_nome']=u.get('geology_nome')
        p['__atlas_fonte']='SGB · GeoSGB · Datações geocronológicas';p['__atlas_snapshot']=CUT_DATE
        out.append(f)
    return out

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
    xmin,ymin,xmax,ymax=cell['bbox'];total=0;rep=0;units=set();dx=(xmax-xmin)/n;dy=(ymax-ymin)/n
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

_U_CACHE={}
def calculate_scale(cells,assigned,units,geo_items,micro_step=BASE_MICROCELL_M,density_percentile=BASE_DENSITY_PERCENTILE,support_n=SUPPORT_N):
    dens=[len(assigned[i])/c['area'] for i,c in enumerate(cells) if assigned[i]]
    sat=percentile(dens,density_percentile)
    if sat is None or sat<=0:raise RuntimeError('não há densidade geocronológica positiva para normalização')
    geo_idx,geo_bin=make_spatial_index(geo_items,50000.0);rows={}
    for ci,c in enumerate(cells):
        inds=assigned[ci];n=len(inds)
        if n==0:
            rows[c['hex_id']]={'igc':None,'G':None,'U':None,'Q':None,'D':None,'O':None,'n':0,'density':0.0,'occupied':0,'micro_support':None,'geo_rep':0,'geo_total':None,'geo_units':0,'q_min':None,'q_mean':None,'q_max':None}
            continue
        density=n/c['area'];D=min(1.0,density/sat)
        occ={micro_key(laea(*units[ui]['point']),micro_step) for ui in inds};ms=support_microcells(c,micro_step,occ);O=min(1.0,len(occ)/len(ms)) if ms else 1.0
        G=math.sqrt(max(0,D*O))
        represented={units[ui].get('geology_uid') for ui in inds if units[ui].get('geology_uid')}
        ck=(c['hex_id'],tuple(sorted(represented)),int(support_n))
        if ck in _U_CACHE:grepr,gtotal,gunits=_U_CACHE[ck]
        else:
            grepr,gtotal,gunits=support_geology(c,represented,geo_items,geo_idx,geo_bin,support_n);_U_CACHE[ck]=(grepr,gtotal,gunits)
        U=(grepr/gtotal) if gtotal else None
        qs=[units[ui]['q'] for ui in inds];Q=statistics.fmean(qs)
        igc=100*((G*U*Q)**(1/3)) if U is not None else None
        rows[c['hex_id']]={'igc':None if igc is None else round(igc,2),'G':round(G,6),'U':None if U is None else round(U,6),'Q':round(Q,6),'D':round(D,6),'O':round(O,6),'n':n,'density':round(density,8),'occupied':len(occ),'micro_support':len(ms),'geo_rep':grepr,'geo_total':gtotal,'geo_units':len(represented),'q_min':round(min(qs),6),'q_mean':round(Q,6),'q_max':round(max(qs),6)}
    return rows,sat

def summary(rows):
    vals=[r['igc'] for r in rows.values() if r['igc'] is not None];ns=[r['n'] for r in rows.values()]
    return {'cells':len(rows),'cells_with_geochronology':len(vals),'cells_without_geochronology':len(rows)-len(vals),'igc_min':min(vals) if vals else None,'igc_median':round(statistics.median(vals),2) if vals else None,'igc_mean':round(statistics.fmean(vals),2) if vals else None,'igc_max':max(vals) if vals else None,'independent_samples_sum':sum(ns),'max_samples_cell':max(ns) if ns else 0}

def compact_rows(rows):
    # [IGC,G,U,Q,D,O,n,density,occupied,micro_support,geo_rep,geo_total,geo_units,q_min,q_mean,q_max]
    return {k:[v['igc'],v['G'],v['U'],v['Q'],v['D'],v['O'],v['n'],v['density'],v['occupied'],v['micro_support'],v['geo_rep'],v['geo_total'],v['geo_units'],v['q_min'],v['q_mean'],v['q_max']] for k,v in rows.items()}

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
        va=a[k]['igc'];vb=b.get(k,{}).get('igc')
        if va is not None and vb is not None:x.append(va);y.append(vb)
    rr=pearson(rankdata(x),rankdata(y)) if len(x)>=2 else None
    return {'n_common':len(x),'rho':None if rr is None else round(rr,6)}

def js_catalog_patch(repo:Path,source_count:int):
    p=repo/'docs/assets/js/app.js';txt=p.read_text(encoding='utf-8')
    prefix='const CATALOG=';pos=txt.index(prefix)+len(prefix);cat,end=json.JSONDecoder().raw_decode(txt[pos:])
    gridmap={'igc_250':('250','malha_r5_250km2',1554),'igc_500':('500','malha_500km2',793),'igc_1000':('1000','malha_1000km2',412)}
    for item in cat.get('layers',[]):
        iid=item.get('id')
        if iid=='geocronologia_geosgb_ms':
            item.update({'status':'incorporada','count':source_count,'validation':'snapshot local V38.4.10 · recorte MS · resultados analíticos relacionados preservados','note':'Fonte oficial materializada para o IGC. A camada pontual mantém a amostra e uma síntese auditável do resultado direto mais completo.','remote_type':None,'remote_url':None})
        if iid in gridmap:
            scale,grid,count=gridmap[iid]
            item.update({'status':'incorporada','count':count,'validation':'V38.4.10 · cálculo materializado e auditável · direto na escala','source':'ITA ARANDU MS · IGC V38.4.10 · SGB GeoSGB Geocronologia + mapa geológico estadual','note':'Controle geocronológico direto. Ausência de amostras utilizáveis permanece transparente e não equivale a zero.','derive_type':'igc_snapshot_v38410','grid_source_id':grid,'igc_scale':scale})
    txt=txt[:pos]+json.dumps(cat,ensure_ascii=False,separators=(',',':'))+txt[pos+end:]
    color_marker="function icpColor(v){const c=icpClass(v);return ITA_ICP_COLORS[c]||'rgba(0,0,0,0)'}"
    if 'const ITA_IGC_COLORS=' not in txt:
        add="\nconst ITA_IGC_COLORS={'muito baixo':'#e3f1ee','baixo':'#beddd6','médio':'#83bbb0','alto':'#4a9487','muito alto':'#1f6f64'};\nfunction igcClass(v){const x=Number(v);if(v===null||v===undefined||!Number.isFinite(x))return'sem controle geocronológico direto materializado';if(x<20)return'muito baixo';if(x<40)return'baixo';if(x<60)return'médio';if(x<75)return'alto';return'muito alto'}\nfunction igcColor(v){const c=igcClass(v);return ITA_IGC_COLORS[c]||'rgba(0,0,0,0)'}"
        if color_marker not in txt:raise RuntimeError('marcador de cor ICP não encontrado em app.js')
        txt=txt.replace(color_marker,color_marker+add,1)
    style_marker="if(st.renderer==='index_icp'){fill=icpColor(p.icp_100);stroke='#4a4a4a';}"
    if "st.renderer==='index_igc'" not in txt:
        if style_marker not in txt:raise RuntimeError('marcador renderer ICP não encontrado em app.js')
        txt=txt.replace(style_marker,style_marker+" if(st.renderer==='index_igc'){fill=igcColor(p.igc_100);stroke='#4a4a4a';}",1)
    if "if(st.renderer==='index_igc')return" not in txt:
        lm="if(st.renderer==='index_icp')return"
        i=txt.find(lm)
        if i<0:raise RuntimeError('legenda ICP não encontrada em app.js')
        e=txt.find('\n',i)
        legend=" if(st.renderer==='index_igc')return `<div class=\"legend-layer-title\">${esc(cfg.name)}</div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:transparent;border:1px solid #4a4a4a\"></span><span>sem controle geocronológico direto · transparente</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#e3f1ee;border:1px solid #4a4a4a\"></span><span>0–&lt;20 · muito baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#beddd6;border:1px solid #4a4a4a\"></span><span>20–&lt;40 · baixo</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#83bbb0;border:1px solid #4a4a4a\"></span><span>40–&lt;60 · médio</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#4a9487;border:1px solid #4a4a4a\"></span><span>60–&lt;75 · alto</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#1f6f64;border:1px solid #4a4a4a\"></span><span>75–100 · muito alto</span></div><div class=\"legend-note\">IGC = 100 × (G × U_age × Q_age)^(1/3). G combina densidade normalizada e ocupação espacial de amostras com idade direta. U_age mede suporte litoestratigráfico local controlado. Q_age mede completude de método, material, idade, incerteza e referência.</div>`;"
        txt=txt[:e+1]+legend+'\n'+txt[e+1:]
    if 'async function buildIgcSnapshotV38410' not in txt:
        marker='async function buildImcPreview(cfg)'
        i=txt.find(marker)
        if i<0:raise RuntimeError('marcador de builder não encontrado em app.js')
        builder="""async function buildIgcSnapshotV38410(cfg){
 const gridCfg=CATALOG.layers.find(x=>x.id===cfg.grid_source_id);
 if(!gridCfg)throw new Error('Malha do IGC V38.4.10 não encontrada no catálogo');
 const grid=await ensure(gridCfg),key=String(cfg.igc_scale||''),scores=window.ITA_IGC_V38410?.grids?.[key],meta=window.ITA_IGC_V38410?.metadata||{};
 if(!scores)throw new Error('Snapshot IGC V38.4.10 não encontrado para esta escala. Execute o materializador do patch.');
 const features=(grid.features||[]).map(hf=>{
  const hid=String(hf.properties?.hex_id||''),r=scores[hid];
  if(!r)return {...hf,properties:{...(hf.properties||{}),igc_100:null,classe_igc:'sem controle geocronológico direto materializado',n_amostras_geocronologicas:0,metodo:'V38.4.10 · snapshot IGC ausente para esta célula'}};
  const [igc,G,U,Q,D,O,n,density,occupied,microSupport,geoRep,geoTotal,geoUnits,qMin,qMean,qMax]=r;
  return {...hf,properties:{...(hf.properties||{}),igc_100:igc,classe_igc:igcClass(igc),n_amostras_geocronologicas:n,densidade_geocronologica_km2:density,g_presenca_distribuicao:G,d_densidade_normalizada:D,o_ocupacao_espacial:O,u_age_representatividade_litoestratigrafica:U,q_age_completude:Q,q_age_min:qMin,q_age_media:qMean,q_age_max:qMax,microcelulas_ocupadas:occupied,microcelulas_suporte:microSupport,suporte_geologico_representado:geoRep,suporte_geologico_total:geoTotal,unidades_litoestratigraficas_representadas:geoUnits,formula:'IGC_h = 100 × (G × U_age × Q_age)^(1/3)',formula_G:'G = sqrt(D* × O)',fonte_igc:'SGB · GeoSGB · Datações geocronológicas e tabelas relacionadas + mapa geológico estadual SGB/CPRM 1:1.000.000',normalizacao_G:'D* saturado no P95 das densidades positivas da escala · O em micromalha fixa de 5 km',suporte_U_age:'9 × 9 pontos determinísticos no bbox do hexágono, usando somente suporte interno com unidade geológica mapeada',definicao_Q_age:'completude de cinco blocos. método, material, idade, incerteza e referência. Não representa exatidão analítica.',regra_duplicatas:'múltiplos resultados da mesma amostra não aumentam G como observações independentes',regra_ausencia:'Sem amostra direta utilizável → IGC nulo e hexágono transparente. Ausência não equivale a zero.',metodo:'V38.4.10 · cálculo direto na escala a partir das amostras geocronológicas independentes · sem agregação entre escalas',data_corte:meta.cut_date||'2026-08-14'}};
 });
 return {type:'FeatureCollection',features,atlas_metadata:{indice:'IGC',versao:'V38.4.10',escala:key,formula:'IGC_h = 100 × (G × U_age × Q_age)^(1/3)',fonte:'SGB · GeoSGB · Geocronologia + mapa geológico estadual',regra:'cálculo independente em 250, 500 e 1000 km²',limite:'IGC mede controle geocronológico direto documentado. Não substitui reprocessamento isotópico nem avaliação especializada de qualidade analítica.'}};
}
"""
        txt=txt[:i]+builder+txt[i:]
    chain="if(!d&&cfg.derive_type==='icp_snapshot_v3849')d=await buildIcpSnapshotV3849(cfg);"
    if "derive_type==='igc_snapshot_v38410'" not in txt:
        if chain not in txt:raise RuntimeError('cadeia derive ICP não encontrada em app.js')
        txt=txt.replace(chain,chain+"if(!d&&cfg.derive_type==='igc_snapshot_v38410')d=await buildIgcSnapshotV38410(cfg);",1)
    scale_marker="const ICP_SCALE_LAYERS=['icp_250','icp_500','icp_1000'];"
    if 'const IGC_SCALE_LAYERS=' not in txt:
        if scale_marker not in txt:raise RuntimeError('grupo de escalas ICP não encontrado em app.js')
        txt=txt.replace(scale_marker,scale_marker+" const IGC_SCALE_LAYERS=['igc_250','igc_500','igc_1000'];",1)
    toggle_marker='async function toggle(id,on){const cfg=CATALOG.layers.find(x=>x.id===id);if(!cfg)return;if(on){'
    if 'IGC_SCALE_LAYERS.includes(id)' not in txt:
        if toggle_marker not in txt:raise RuntimeError('toggle não encontrado em app.js')
        inject="async function toggle(id,on){const cfg=CATALOG.layers.find(x=>x.id===id);if(!cfg)return;if(on&&IGC_SCALE_LAYERS.includes(id)){for(const other of IGC_SCALE_LAYERS){if(other===id)continue;state.active.delete(other);const ocb=document.querySelector(`input[data-layer=\"${other}\"]`);if(ocb)ocb.checked=false;updateLayerCard(other)}}if(on){"
        txt=txt.replace(toggle_marker,inject,1)
    p.write_text(txt,encoding='utf-8',newline='\n')

def update_local_catalog(repo:Path,source_count:int,source_bytes:int):
    js=repo/'docs/camadas/catalogo-local.js';txt=js.read_text(encoding='utf-8')
    prefix='window.ITA_LOCAL_LAYER_FILES=';pos=txt.index(prefix)+len(prefix);obj,end=json.JSONDecoder().raw_decode(txt[pos:])
    obj['geocronologia_geosgb_ms']='./camadas/arquivos/geocronologia_geosgb_ms.geojson'
    txt=txt[:pos]+json.dumps(obj,ensure_ascii=False,separators=(',',':'))+txt[pos+end:];js.write_text(txt,encoding='utf-8',newline='\n')
    jp=repo/'docs/camadas/catalogo-local.json';arr=load_json(jp)
    found=False
    for item in arr:
        if item.get('id')=='geocronologia_geosgb_ms':
            item.update({'arquivo':'./camadas/arquivos/geocronologia_geosgb_ms.geojson','nome':'Dados geocronológicos','grupo':'Geologia e estratigrafia','status':'incorporada','fonte':'SGB · GeoSGB · Datações geocronológicas · snapshot local V38.4.10','validacao':'recorte MS · amostras diretas e síntese de resultados relacionados','feicoes':source_count,'bytes':source_bytes});found=True
    if not found:arr.insert(2,{'id':'geocronologia_geosgb_ms','arquivo':'./camadas/arquivos/geocronologia_geosgb_ms.geojson','nome':'Dados geocronológicos','grupo':'Geologia e estratigrafia','status':'incorporada','fonte':'SGB · GeoSGB · Datações geocronológicas · snapshot local V38.4.10','validacao':'recorte MS · amostras diretas e síntese de resultados relacionados','feicoes':source_count,'bytes':source_bytes})
    dump_json(jp,arr)

def update_html_sw_docs(repo:Path):
    idx=repo/'docs/index.html';t=idx.read_text(encoding='utf-8')
    t=t.replace('v=38.4.9','v=38.4.10')
    script='<script src="./indices/igc-v38410.js?v=38.4.10"></script>'
    if script not in t:
        marker='<script src="./indices/icp-v3849.js?v=38.4.10"></script>'
        if marker not in t:raise RuntimeError('script ICP não encontrado no index.html')
        t=t.replace(marker,marker+'\n'+script,1)
    idx.write_text(t,encoding='utf-8',newline='\n')
    boot=repo/'docs/assets/js/bootstrap.js';b=boot.read_text(encoding='utf-8');b=re.sub(r'v=38\.4\.\d+', 'v=38.4.10', b);boot.write_text(b,encoding='utf-8',newline='\n')
    sw=repo/'docs/service-worker.js';s=sw.read_text(encoding='utf-8');s=re.sub(r"const ITA_CACHE = 'ita-arandu-[^']+';","const ITA_CACHE = 'ita-arandu-v38-4-10-igc-controle-geocronologico';",s,count=1);s=s.replace('v=38.4.9','v=38.4.10')
    for entry,after in [("  \"./indices/igc-v38410.js?v=38.4.10\",\n","  \"./indices/icp-v3849.js?v=38.4.10\",\n"),("  \"./camadas/arquivos/geocronologia_geosgb_ms.geojson\",\n","  \"./camadas/arquivos/petrografia_geosgb_ms.geojson\",\n"),("  \"./documentos/metodologia-igc.html\",\n","  \"./documentos/metodologia-icp.html\",\n")]:
        if entry.strip() not in s:
            if after not in s:raise RuntimeError('marcador do service worker não encontrado')
            s=s.replace(after,after+entry,1)
    sw.write_text(s,encoding='utf-8',newline='\n')
    di=repo/'docs/documentos/index.html';d=di.read_text(encoding='utf-8')
    link='<li><a href="./metodologia-igc.html">IGC · Controle Geocronológico · metodologia V38.4.10</a></li>'
    if link not in d:
        marker='<li><a href="./metodologia-icp.html">ICP · Caracterização Petrográfica · metodologia V38.4.9</a></li>'
        if marker in d:d=d.replace(marker,marker+'\n'+link,1)
        else:d=d.replace('</ul>',link+'\n</ul>',1)
    di.write_text(d,encoding='utf-8',newline='\n')

def update_bibliography(repo:Path):
    jp=repo/'docs/referencias/bibliografia-camadas-indices.json'
    if jp.exists():
        o=load_json(jp)
        for e in o.get('entries',[]):
            if isinstance(e,dict) and e.get('id') in {'igc_250','igc_500','igc_1000','geocronologia_geosgb_ms'}:e['status']='incorporada'
        dump_json(jp,o)
    hp=repo/'docs/referencias/index.html'
    if hp.exists():
        h=hp.read_text(encoding='utf-8')
        for lid in ['igc_250','igc_500','igc_1000']:
            pattern=re.compile(r'(<section class="entry layer-entry"[^>]*id="layer-'+re.escape(lid)+r'".*?<div class="meta"><code>'+re.escape(lid)+r'</code> · Conhecimento geocientífico e análises · )planejada( · .*?</section>)',re.S)
            h=pattern.sub(r'\1incorporada\2',h,count=1)
        pattern=re.compile(r'(<section class="entry layer-entry"[^>]*id="layer-geocronologia_geosgb_ms".*?<div class="meta"><code>geocronologia_geosgb_ms</code> · Geologia e estratigrafia · )conectada( · .*?</section>)',re.S)
        h=pattern.sub(r'\1incorporada\2',h,count=1)
        hp.write_text(h,encoding='utf-8',newline='\n')

def update_changelog(repo:Path):
    entry='''\n## V38.4.10 · IGC · Controle Geocronológico · 2026-08-14\n\n- materializa Datações geocronológicas do GeoSGB e tabelas analíticas relacionadas\n- calcula IGC em 250, 500 e 1000 km² diretamente a partir das amostras geocronológicas independentes\n- congela IGC_h = 100 × (G × U_age × Q_age)^(1/3) e G = sqrt(D* × O)\n- preserva ausência de controle direto como null e hexágono transparente\n- registra análise de sensibilidade e auditoria de rastreabilidade\n'''
    ch=repo/'CHANGELOG.md'
    if ch.exists():
        t=ch.read_text(encoding='utf-8')
        if 'V38.4.10 · IGC' not in t:ch.write_text(t.rstrip()+entry+'\n',encoding='utf-8',newline='\n')
    rd=repo/'README.md'
    if rd.exists():
        t=rd.read_text(encoding='utf-8');t=re.sub(r'V38\.4\.9[^\n]*','V38.4.10 · IGC · Controle Geocronológico',t,count=1) if 'V38.4.9' in t else t
        rd.write_text(t,encoding='utf-8',newline='\n')
    dh=repo/'docs/documentos/changelog.html'
    if dh.exists():
        t=dh.read_text(encoding='utf-8')
        if 'V38.4.10 · IGC' not in t:t=t.replace('</body>','<h2>V38.4.10 · IGC · Controle Geocronológico</h2><p>Materialização do controle geocronológico direto nas três escalas, com rastreabilidade dos resultados analíticos relacionados e análise de sensibilidade.</p></body>')
        dh.write_text(t,encoding='utf-8',newline='\n')

def self_test():
    rr=[]
    _append_related_groups({'relatedRecordGroups':[{'objectId':7,'relatedRecords':[{'attributes':{'IDADE_MAX':123,'METODO_ANALITICO':'U-Pb','MATERIAL_ANALISADO':'zircão'}}]}]},'simples',rr,{'7':'1'})
    assert len(rr)==1 and rr[0]['__atlas_sample_id']=='1' and rr[0]['__atlas_origin_objectid']=='7' and rr[0]['__atlas_tabela_metodo']=='simples'
    main=[{'type':'Feature','geometry':{'type':'Point','coordinates':[-54.52,-20.52]},'properties':{'ID':1,'AMOSTRA':'A','METODOS':'U-Pb','MATERIAIS_ANALISADOS':'zircão'}},{'type':'Feature','geometry':{'type':'Point','coordinates':[-54.48,-20.48]},'properties':{'ID':2,'AMOSTRA':'B','METODOS':'Rb-Sr','MATERIAIS_ANALISADOS':'rocha total'}}]
    rows={'simples':[{'CODIGO':1,'METODO_ANALITICO':'U-Pb','MATERIAL_ANALISADO':'zircão','IDADE_MAX':1000,'ERRO_MAX':5,'BIBLIOGRAFIA':'Teste','__atlas_tabela_metodo':'simples'},{'CODIGO':2,'METODO_ANALITICO':'Rb-Sr','MATERIAL_ANALISADO':'rocha total','IDADE_MAX':500,'ERRO_MAX':None,'AUTORES':'Teste','ANO_PUB':'2020','__atlas_tabela_metodo':'simples'}]}
    u,ex=build_units(main,method_rows_by_sample(rows));assert ex==0 and len(u)==2 and abs(u[0]['q']-1)<1e-9 and 0.7<=u[1]['q']<=0.9
    main_missing=[{'type':'Feature','geometry':{'type':'Point','coordinates':[-54.50,-20.50]},'properties':{'ID':3,'AMOSTRA':'C','METODOS':'U-Pb','MATERIAIS_ANALISADOS':None}}]
    rows_missing={'concordia':[{'CODIGO':3,'METODO_ANALITICO':'U-Pb','IDADE_MAX':780,'ERRO_MAX':None,'__atlas_tabela_metodo':'concordia'}]}
    um,exm=build_units(main_missing,method_rows_by_sample(rows_missing));assert exm==0 and len(um)==1 and abs(um[0]['q']-0.4)<1e-9 and um[0]['blocks']['material'] is False
    assert independent_key(main[0])=='ID:1'
    print('SELFTEST IGC V38.4.10 · PASS')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');ap.add_argument('--self-test',action='store_true');ap.add_argument('--source-file');args=ap.parse_args()
    if args.self_test:self_test();return 0
    repo=Path(args.repo).resolve()
    for rel in list(GRID_FILES.values())+[LIMIT_FILE,GEOLOGY_FILE]:
        if not (repo/rel).exists():raise RuntimeError(f'arquivo estrutural ausente · {rel}')
    for rel in ['docs/indices/iod-v3848.js','docs/indices/iod_v3848_snapshot.json','docs/camadas/arquivos/afloramentos_geosgb_ms.geojson','docs/indices/icp-v3849.js','docs/indices/icp_v3849_snapshot.json','docs/camadas/arquivos/petrografia_geosgb_ms.geojson']:
        if not (repo/rel).exists():raise RuntimeError(f'base V38.4.9 incompleta · arquivo ausente · {rel}')
    print('ITA ARANDU MS · materialização IGC V38.4.10')
    print('Fonte · SGB GeoSGB · Datações geocronológicas + tabelas relacionadas')
    print('Fórmula ·',FORMULA);print('G · sqrt(D* × O) · D* P95 por escala · micromalha 5 km');print('U_age · suporte litoestratigráfico 9 × 9 · Q_age · método + material + idade + incerteza + referência')
    if args.source_file:
        source_obj=load_json(Path(args.source_file));source_label='arquivo local fornecido';source_url=str(Path(args.source_file))
    else:source_label,source_url,source_obj=fetch_source()
    raw=canonical_bytes(source_obj);raw_hash=sha256_bytes(raw)
    mainfc=source_obj.get('main') or {};tables=source_obj.get('tables') or {}
    state=feature_polys(load_json(repo/LIMIT_FILE));features,cleanup=clip_to_state(mainfc.get('features',[]),state)
    if len(features)<3:raise RuntimeError(f'apenas {len(features)} registros geocronológicos ficaram dentro do limite oficial de MS')
    rows_index=method_rows_by_sample(tables)
    units,excluded=build_units(features,rows_index)
    linked_by_id=sum(1 for f in features if id_key(ci_get(f.get('properties') or {},'ID')) and ('ID:'+id_key(ci_get(f.get('properties') or {},'ID'))) in rows_index)
    linked_by_name=sum(1 for f in features if norm_text(ci_get(f.get('properties') or {},'AMOSTRA')) and ('AMOSTRA:'+norm_text(ci_get(f.get('properties') or {},'AMOSTRA'))) in rows_index)
    print(f'GeoSGB · amostras recortadas com linhas vinculadas por ID · {linked_by_id}')
    print(f'GeoSGB · amostras recortadas com linhas vinculadas por nome · {linked_by_name}')
    main_material=sum(1 for f in features if nonempty(ci_get(f.get('properties') or {},'MATERIAIS_ANALISADOS')))
    main_methods=sum(1 for f in features if nonempty(ci_get(f.get('properties') or {},'METODOS')))
    print(f'GeoSGB · amostras principais com METODOS publicado · {main_methods}')
    print(f'GeoSGB · amostras principais com MATERIAIS_ANALISADOS publicado · {main_material}')
    print(f'GeoSGB · amostras diretas utilizáveis após filtro método + idade · {len(units)}')
    if len(units)<2:
        # Diagnóstico R3 · material analisado é um bloco de Q_age, não um gate de elegibilidade.
        diag={'rows_total':0,'metodo':0,'material':0,'idade':0,'metodo_idade':0,'metodo_material_idade':0}
        seen=set()
        for vals in rows_index.values():
            for r in vals:
                rid=(str(r.get('__atlas_tabela_metodo','')),str(ci_get(r,'OBJECTID') or json.dumps(r,ensure_ascii=False,sort_keys=True)))
                if rid in seen:continue
                seen.add(rid);diag['rows_total']+=1
                # usa apenas campos da linha para diagnóstico global; a decisão final continua em build_units com fallback da amostra principal
                m=nonempty(ci_get(r,'METODO_ANALITICO'));ma=nonempty(ci_get(r,'MATERIAL_ANALISADO'));a=num(ci_get(r,'IDADE_MAX'));aok=a is not None and a>0
                diag['metodo']+=int(m);diag['material']+=int(ma);diag['idade']+=int(aok);diag['metodo_idade']+=int(m and aok);diag['metodo_material_idade']+=int(m and ma and aok)
        print('GeoSGB · diagnóstico dos campos relacionados · '+', '.join(f'{k}={v}' for k,v in diag.items()))
        print(f'GeoSGB · diagnóstico da camada principal · metodos={main_methods}, materiais_analisados={main_material}')
        raise RuntimeError(f'apenas {len(units)} amostras possuem resultado geocronológico direto utilizável')
    geo_items=geology_records(load_json(repo/GEOLOGY_FILE));missing_geo=annotate_geology(units,geo_items)
    grids={};cells={};assigned={};missing={};ambiguous={}
    for s,rel in GRID_FILES.items():grids[s],cells[s]=load_grid(repo/rel)
    for s in ('250','500','1000'):assigned[s],missing[s],ambiguous[s]=assign_units(units,cells[s])
    valid=set(i for arr in assigned['250'] for i in arr)
    if len(valid)<2:raise RuntimeError('menos de duas amostras geocronológicas diretas caem na malha oficial de MS')
    if len(valid)!=len(units):
        keep={units[i]['key'] for i in valid};units=[u for u in units if u['key'] in keep]
        for s in ('250','500','1000'):assigned[s],missing[s],ambiguous[s]=assign_units(units,cells[s])
    for s in ('250','500','1000'):
        if missing[s]:raise RuntimeError(f'{len(missing[s])} amostras geocronológicas não foram atribuídas à malha {s}')
    baseline={};sats={}
    for s in ('250','500','1000'):baseline[s],sats[s]=calculate_scale(cells[s],assigned[s],units,geo_items)
    sensitivity={}
    for s in ('250','500','1000'):
        sensitivity[s]={};base=baseline[s]
        for step,pct,n in [(2500,95,SUPPORT_N),(10000,95,SUPPORT_N),(5000,90,SUPPORT_N),(5000,99,SUPPORT_N),(5000,95,7),(5000,95,11)]:
            alt,_=calculate_scale(cells[s],assigned[s],units,geo_items,float(step),pct,n)
            sensitivity[s][f'micro_{step/1000:g}km_P{pct}_U{n}x{n}']=spearman_maps(base,alt)
    out_features=annotate_source_features(features,units)
    source_fc={'type':'FeatureCollection','features':out_features,'atlas_metadata':{'id':'geocronologia_geosgb_ms','nome':'Dados geocronológicos','fonte':'Serviço Geológico do Brasil · GeoSGB · Datações geocronológicas','fonte_materializada_por':source_label,'correcao_runtime':'R3 · vínculo OBJECTID origem → ID amostra + elegibilidade por método e idade; material preservado em Q_age','url_consulta':source_url,'corte':CUT_DATE,'sha256_snapshot_mesclado':raw_hash,'registros_pontuais_recortados_ms':len(features),'amostras_diretas_independentes':len(units),'registros_sem_resultado_direto_utilizavel':excluded,'tabelas_relacionadas':{k:len(v) for k,v in tables.items()},'regra_independencia':'ID institucional da amostra; fallback AMOSTRA + coordenada','regra_direta':'exige resultado relacionado com método analítico e idade positiva. Material analisado permanece como bloco de completude em Q_age e nunca é inferido quando ausente',**cleanup}}
    sp=repo/'docs/camadas/arquivos/geocronologia_geosgb_ms.geojson';dump_json(sp,source_fc,compact=True)
    raw_path=repo/f'data/geocronologia_geosgb_ms_raw_{CUT_DATE.replace("-","")}.json.gz';raw_path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(raw_path,'wb',compresslevel=9) as gz:gz.write(raw)
    snap={'metadata':{'index':'IGC','version':VERSION,'calculated_at':now_iso(),'cut_date':CUT_DATE,'formula':FORMULA,'g_formula':G_FORMULA,'components':{'G':'presença e distribuição espacial de amostras geocronológicas independentes. G = sqrt(D* × O), D* saturado no P95 positivo de cada escala e O em micromalha fixa de 5 km','U_age':'fração do suporte litoestratigráfico do hexágono pertencente a unidades com ao menos uma amostra geocronológica direta local','Q_age':'média da melhor completude por amostra entre cinco blocos. método, material, idade, incerteza e referência'},'source':'SGB · GeoSGB · Datações geocronológicas + tabelas relacionadas','source_url':source_url,'source_method':source_label,'source_sha256':raw_hash,'source_point_records':len(features),'independent_direct_samples':len(units),'raw_gzip':str(raw_path.relative_to(repo)).replace('\\','/'),'direct_rule':'entra em G e U_age somente amostra com resultado relacionado contendo método analítico e idade positiva. Material analisado é avaliado separadamente em Q_age','quality_rule':'Q_age mede completude de cinco blocos publicados: método, material, idade, incerteza e referência. Material ausente reduz Q_age, mas não apaga uma datação direta com método e idade. Não é nota de exatidão analítica e não reprocessa dados isotópicos.','geology_source':'SGB/CPRM · mapa geológico de Mato Grosso do Sul 1:1.000.000 · snapshot local do Atlas','u_support':f'{SUPPORT_N} × {SUPPORT_N} pontos determinísticos por bbox, retidos apenas dentro do hexágono e de unidade geológica mapeada','microcell_m':BASE_MICROCELL_M,'density_percentile':BASE_DENSITY_PERCENTILE,'scale_rule':'250, 500 e 1000 km² são calculados diretamente a partir das amostras geocronológicas independentes. Não há agregação de resultados entre escalas.','null_rule':'hexágonos sem amostra geocronológica direta utilizável recebem IGC=null e permanecem transparentes. Ausência não é convertida em zero.','references':['REF-002','REF-082','REF-085','REF-105','REF-108','REF-115']},'summary':{s:summary(baseline[s]) for s in baseline},'normalization_p95_density':{s:round(sats[s],10) for s in sats},'sensitivity_spearman':sensitivity,'grids':{s:compact_rows(baseline[s]) for s in baseline}}
    dump_json(repo/'docs/indices/igc_v38410_snapshot.json',snap);(repo/'docs/indices/igc-v38410.js').write_text('window.ITA_IGC_V38410='+json.dumps(snap,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
    js_catalog_patch(repo,len(out_features));update_local_catalog(repo,len(out_features),sp.stat().st_size);update_html_sw_docs(repo);update_bibliography(repo);update_changelog(repo)
    (repo/'VERSION').write_text(VERSION+'\n',encoding='utf-8',newline='\n')
    runtime={'audit':'V38.4.10 IGC runtime','status':'PASS','calculated_at':now_iso(),'source_records_ms':len(features),'direct_independent_samples':len(units),'excluded_without_direct_result':excluded,'missing_geology_assignment':missing_geo,'tables_related_counts':{k:len(v) for k,v in tables.items()},'source_sha256':raw_hash,'main_records_with_methods':main_methods,'main_records_with_materials':main_material,'direct_samples_without_material':sum(1 for u in units if not u['blocks']['material']),'summaries':{s:summary(baseline[s]) for s in baseline},'checks':{'independent_scale_calculation':True,'null_is_not_zero':True,'direct_age_requires_method_and_age':True,'missing_material_penalizes_q_age_without_being_imputed':True,'q_age_is_documentary_completeness_not_accuracy':True,'previous_indices_not_recomputed':True}}
    dump_json(repo/'AUDITORIA_V38_4_10_IGC_RUNTIME.json',runtime)
    print('IGC V38.4.10 materializado ·',len(units),'amostras diretas independentes')
    for s in ('250','500','1000'):print(s,'km² ·',summary(baseline[s]))
    return 0

if __name__=='__main__':raise SystemExit(main())
