from __future__ import annotations
from pathlib import Path
import argparse, json, urllib.request, urllib.parse, urllib.error
import hashlib, csv, io, re, unicodedata, html as htmlmod, time, copy, sys
from html.parser import HTMLParser
from datetime import datetime, timezone

VERSION_BASE = "V38.4.40B-CAMADAS-UX-CLEAN-1.0-20260816"
VERSION_FINAL = "V38.4.41-MATERIALIZACAO-OFFLINE-I-1.0-20260816"

ESTRADAS_ID = "estradas_vicinais_ms"
HIDRO_ID = "hidrografia_referencia_ms"
RIOS_ID = "rios_principais_ms"
AERO_ID = "aeroportos_aerodromos_ms"

ESTRADAS_LAYER = "https://www.pinms.ms.gov.br/arcgis/rest/services/AGRAER_SERVICOS/Estradas_Vicinais/MapServer/0"
HIDRO_LAYER = "https://www.pinms.ms.gov.br/arcgis/rest/services/AGRAER_SERVICOS/Hidrografia_MS/FeatureServer/0"

ANAC_PUBLIC_PAGE = "https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/aerodromos/lista-de-aerodromos-publicos-v2"
ANAC_PRIVATE_PAGE = "https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/aerodromos/lista-de-aerodromos-privados-v2"

UA = "ITA-ARANDU-MS/38.4.41 scientific-snapshot-materializer"

def log(s):
    print(s, flush=True)

def req(url, timeout=90, binary=False):
    r = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(r, timeout=timeout) as h:
        data = h.read()
        ctype = h.headers.get_content_charset() or "utf-8"
        final = h.geturl()
    if binary:
        return data, final
    for enc in [ctype, "utf-8-sig", "latin-1"]:
        try:
            return data.decode(enc), final
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", "replace"), final

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def write_geojson(path, obj):
    # stable UTF-8 compact encoding keeps repository size reasonable
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return sha256_bytes(raw)

def geom_types(fc):
    return sorted({(f.get("geometry") or {}).get("type") for f in fc.get("features", []) if f.get("geometry")})

def validate_fc(fc, expected=None, allow_empty=False):
    if not isinstance(fc, dict) or fc.get("type") != "FeatureCollection" or not isinstance(fc.get("features"), list):
        raise RuntimeError("GeoJSON não é FeatureCollection válida")
    if not allow_empty and len(fc["features"]) == 0:
        raise RuntimeError("GeoJSON retornou zero feições")
    bad = [i for i,f in enumerate(fc["features"]) if f.get("type") != "Feature" or not isinstance(f.get("properties"), dict)]
    if bad:
        raise RuntimeError(f"GeoJSON contém feições inválidas: {bad[:5]}")
    types = geom_types(fc)
    if expected:
        ok = all(t in expected for t in types)
        if not ok:
            raise RuntimeError(f"Geometria inesperada: {types}; esperado {expected}")
    return types

def arcgis_layer_meta(layer_url):
    txt,_ = req(layer_url + "?f=json")
    j = json.loads(txt)
    if "error" in j:
        raise RuntimeError(f"ArcGIS metadata error: {j['error']}")
    return j

def arcgis_count(layer_url, where="1=1"):
    q = urllib.parse.urlencode({
        "where":where,
        "returnCountOnly":"true",
        "f":"json",
    })
    txt,_=req(layer_url+"/query?"+q)
    j=json.loads(txt)
    if "error" in j:
        raise RuntimeError(f"ArcGIS count error: {j['error']}")
    return int(j["count"])

def arcgis_download(layer_url, out_fields="*", where="1=1", page_size=None):
    meta = arcgis_layer_meta(layer_url)
    cap = int(meta.get("maxRecordCount") or 1000)
    if page_size:
        cap = min(cap, int(page_size))
    total = arcgis_count(layer_url, where)
    log(f"  serviço reporta {total} feições")
    all_features=[]
    offset=0
    while offset < total:
        params={
            "where":where,
            "outFields":out_fields,
            "returnGeometry":"true",
            "outSR":"4326",
            "resultOffset":str(offset),
            "resultRecordCount":str(cap),
            "f":"geojson",
        }
        url=layer_url+"/query?"+urllib.parse.urlencode(params)
        txt,_=req(url)
        j=json.loads(txt)
        if j.get("type")!="FeatureCollection":
            raise RuntimeError(f"ArcGIS não retornou GeoJSON na página offset={offset}")
        feats=j.get("features",[])
        if not feats:
            raise RuntimeError(f"Paginação interrompida em offset={offset}")
        all_features.extend(feats)
        offset += len(feats)
        log(f"  {len(all_features)}/{total}")
    if len(all_features)!=total:
        raise RuntimeError(f"Contagem divergente após paginação: {len(all_features)} != {total}")
    return {
        "type":"FeatureCollection",
        "name":None,
        "features":all_features,
        "atlas_metadata":{
            "source_url":layer_url,
            "capture_utc":datetime.now(timezone.utc).isoformat(),
            "arcgis_reported_count":total,
            "source_spatial_reference":meta.get("extent",{}).get("spatialReference"),
            "output_crs":"EPSG:4326"
        }
    },meta

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self._href=None
        self._txt=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower()=="a":
            self._href=dict(attrs).get("href")
            self._txt=[]
    def handle_data(self,data):
        if self._href is not None:
            self._txt.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self._href is not None:
            self.links.append((self._href," ".join(self._txt).strip()))
            self._href=None
            self._txt=[]

def page_links(url):
    txt,final=req(url)
    p=Links();p.feed(txt)
    return [(urllib.parse.urljoin(final,h),t) for h,t in p.links if h]

def discover_anac_directory(page_url):
    links=page_links(page_url)
    scored=[]
    for u,t in links:
        n=norm(t+" "+u)
        score=0
        if "csv" in n: score+=4
        if "json" in n: score+=4
        if "formato" in n: score+=2
        if "aerodrom" in n: score+=2
        if "sistemas.anac.gov.br/dadosabertos" in u.lower(): score+=8
        if score:
            scored.append((score,u,t))
    scored.sort(reverse=True)
    if not scored:
        raise RuntimeError("ANAC: link CSV/JSON não localizado na página oficial")
    # Resolve redirect if page points to intermediary.
    candidate=scored[0][1]
    try:
        _,final=req(candidate)
        return final
    except Exception:
        return candidate

def discover_data_file(directory_or_page):
    txt,final=req(directory_or_page)
    # If final itself is data
    if re.search(r"\.(csv|json)(?:$|\?)", final, re.I):
        return final
    p=Links();p.feed(txt)
    candidates=[]
    for h,t in p.links:
        u=urllib.parse.urljoin(final,h)
        low=u.lower()
        if low.endswith(".csv") or ".csv?" in low:
            candidates.append((4,u))
        elif low.endswith(".json") or ".json?" in low:
            candidates.append((3,u))
    if not candidates:
        # extract raw URLs/hrefs from directory listing
        for h in re.findall(r'href=["\']([^"\']+)["\']',txt,re.I):
            u=urllib.parse.urljoin(final,htmlmod.unescape(h))
            low=u.lower()
            if low.endswith(".csv"): candidates.append((4,u))
            elif low.endswith(".json"): candidates.append((3,u))
    if not candidates:
        raise RuntimeError(f"ANAC: nenhum arquivo CSV/JSON encontrado em {final}")
    # favor CSV because dialect/encoding is easier to diagnose and preserve
    candidates.sort(reverse=True)
    return candidates[0][1]

def norm(s):
    s=unicodedata.normalize("NFKD",str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).strip().lower()

def read_table_from_url(url):
    data,final=req(url,binary=True)
    low=final.lower()
    if low.endswith(".json") or data.lstrip().startswith((b"[",b"{")):
        for enc in ["utf-8-sig","latin-1"]:
            try:
                j=json.loads(data.decode(enc));break
            except Exception:
                j=None
        if j is None: raise RuntimeError("ANAC JSON inválido")
        if isinstance(j,dict):
            for key in ["data","records","items","features"]:
                if isinstance(j.get(key),list):
                    j=j[key];break
        if not isinstance(j,list):
            raise RuntimeError("ANAC JSON não contém lista tabular")
        rows=[]
        for x in j:
            if isinstance(x,dict) and x.get("type")=="Feature" and isinstance(x.get("properties"),dict):
                y=dict(x["properties"])
                if x.get("geometry"): y["_geometry"]=x["geometry"]
                rows.append(y)
            elif isinstance(x,dict):
                rows.append(x)
        return rows,final,sha256_bytes(data)
    text=None
    for enc in ["utf-8-sig","latin-1"]:
        try:
            text=data.decode(enc);break
        except UnicodeDecodeError: pass
    if text is None:text=data.decode("utf-8","replace")
    sample=text[:10000]
    try: dialect=csv.Sniffer().sniff(sample,delimiters=";,|\t")
    except Exception:
        dialect=csv.excel;dialect.delimiter=";"
    rows=list(csv.DictReader(io.StringIO(text),dialect=dialect))
    return rows,final,sha256_bytes(data)

def field_lookup(row, aliases):
    nm={norm(k):k for k in row.keys()}
    # exact first
    for a in aliases:
        if norm(a) in nm:return nm[norm(a)]
    # contains fallback
    for a in aliases:
        na=norm(a)
        for nk,k in nm.items():
            if na in nk:return k
    return None

def decimal_coord(v, is_lon=False):
    if v is None:return None
    if isinstance(v,(int,float)):
        x=float(v)
        return x
    s=str(v).strip()
    if not s:return None
    s=s.replace(",",".")
    # plain decimal
    try:return float(s)
    except:pass
    # DMS: 20° 28' 12.3" S
    nums=[float(x.replace(",",".")) for x in re.findall(r"\d+(?:[.,]\d+)?",s)]
    if not nums:return None
    x=nums[0]+(nums[1]/60 if len(nums)>1 else 0)+(nums[2]/3600 if len(nums)>2 else 0)
    if re.search(r"[SW]",s,re.I):x=-x
    return x

def anac_rows_to_features(rows, origin):
    if not rows:
        raise RuntimeError(f"ANAC {origin}: tabela vazia")
    sample=rows[0]
    uf_key=field_lookup(sample,["UF","Unidade Federativa","Estado"])
    lat_key=field_lookup(sample,["Latitude","LATITUDE","LAT"])
    lon_key=field_lookup(sample,["Longitude","LONGITUDE","LON","LONG"])
    if not uf_key:
        raise RuntimeError(f"ANAC {origin}: campo UF não identificado. Cabeçalhos: {list(sample)[:30]}")
    if not lat_key or not lon_key:
        # Sometimes a geometry object exists.
        if "_geometry" not in sample:
            raise RuntimeError(f"ANAC {origin}: latitude/longitude não identificadas. Cabeçalhos: {list(sample)[:30]}")
    feats=[]
    rejected=0
    for r in rows:
        if norm(r.get(uf_key)) not in {"ms","mato grosso do sul"}:
            continue
        geom=r.get("_geometry")
        if not geom:
            lat=decimal_coord(r.get(lat_key))
            lon=decimal_coord(r.get(lon_key),True)
            if lat is None or lon is None or not(-25.5<=lat<=-16.0 and -59.5<=lon<=-49.5):
                rejected+=1;continue
            geom={"type":"Point","coordinates":[lon,lat]}
        props={str(k):v for k,v in r.items() if k!="_geometry"}
        props["_ita_origem_anac"]=origin
        feats.append({"type":"Feature","geometry":geom,"properties":props})
    if not feats:
        raise RuntimeError(f"ANAC {origin}: zero pontos válidos em MS; rejeitados={rejected}")
    return feats,rejected,{"uf":uf_key,"lat":lat_key,"lon":lon_key}

def download_anac():
    allf=[];sources=[];details={}
    for origin,page in [("publico",ANAC_PUBLIC_PAGE),("privado",ANAC_PRIVATE_PAGE)]:
        log(f"ANAC · descobrindo arquivo {origin}")
        directory=discover_anac_directory(page)
        file_url=discover_data_file(directory)
        log(f"  arquivo {origin}: {file_url}")
        rows,final,rawsha=read_table_from_url(file_url)
        feats,rejected,fields=anac_rows_to_features(rows,origin)
        allf.extend(feats)
        sources.append({"origin":origin,"page":page,"directory":directory,"file":final,"source_sha256":rawsha,"records_ms":len(feats),"rejected_ms":rejected,"fields":fields})
    return {"type":"FeatureCollection","name":"aeroportos_aerodromos_ms","features":allf,
            "atlas_metadata":{"capture_utc":datetime.now(timezone.utc).isoformat(),"source":"ANAC dados abertos","sources":sources,"output_crs":"EPSG:4326"}},sources

def extract_catalog(app_text):
    prefix="const CATALOG="
    if not app_text.startswith(prefix):
        raise RuntimeError("app.js não começa com const CATALOG=")
    end=app_text.find(";",len(prefix))
    if end<0:raise RuntimeError("CATALOG não terminada")
    return json.loads(app_text[len(prefix):end]),end

def update_catalog(repo, counts, paths, manifest):
    p=repo/"docs/assets/js/app.js"
    txt=p.read_text(encoding="utf-8")
    cat,end=extract_catalog(txt)
    by={x["id"]:x for x in cat["layers"]}
    for id_ in [ESTRADAS_ID,HIDRO_ID,RIOS_ID,AERO_ID]:
        if id_ not in by:raise RuntimeError(f"Camada ausente no CATALOG: {id_}")
    by[ESTRADAS_ID].update({
        "status":"incorporada","count":counts[ESTRADAS_ID],
        "validation":"snapshot local reconstruído e verificado da fonte oficial PIN MS / AGRAER · 16/08/2026",
        "note":"Snapshot local reconstruído a partir do serviço oficial após descarte do blob herdado com CRC inválido.",
        "expected_geometry":"LineString",
    })
    by[HIDRO_ID].update({
        "status":"incorporada","count":counts[HIDRO_ID],
        "validation":"snapshot local oficial materializado do PIN MS / AGRAER · 16/08/2026",
        "note":"Camada mestre local para uso offline e origem da derivação Rios nomeados.",
    })
    by[RIOS_ID].update({
        "status":"incorporada","count":counts[RIOS_ID],
        "validation":"derivada local verificável do snapshot Hidrografia MS · NOME não vazio · 16/08/2026",
        "note":"Derivação do mesmo snapshot mestre de hidrografia, sem segunda descarga independente.",
    })
    by[AERO_ID].update({
        "status":"incorporada","count":counts[AERO_ID],"scope_level":"MS",
        "validation":"snapshot local materializado de dados abertos oficiais ANAC · públicos e privados · filtro UF=MS · 16/08/2026",
        "note":"Camada logística de referência para campanhas de campo. Preserva atributos de origem e distingue aeródromos públicos e privados.",
        "source_url":ANAC_PUBLIC_PAGE,
    })
    new=json.dumps(cat,ensure_ascii=False,separators=(",",":"))
    p.write_text("const CATALOG="+new+txt[end:],encoding="utf-8",newline="\n")

    # local registry
    cp=repo/"docs/camadas/catalogo-local.js"
    ct=cp.read_text(encoding="utf-8")
    pref="window.ITA_LOCAL_LAYER_FILES="
    st=ct.find(pref); en=ct.find(";",st)
    reg=json.loads(ct[st+len(pref):en])
    reg.update(paths)
    cp.write_text(ct[:st]+pref+json.dumps(reg,ensure_ascii=False,separators=(",",":"))+ct[en:],encoding="utf-8",newline="\n")

    # provenance registry
    pp=repo/"docs/camadas/proveniencia-snapshots.js"
    pt=pp.read_text(encoding="utf-8")
    pref2="window.ITA_LAYER_PROVENANCE="
    st=pt.find(pref2);en=pt.find(";",st)
    prov=json.loads(pt[st+len(pref2):en])
    for id_ in [ESTRADAS_ID,HIDRO_ID,RIOS_ID,AERO_ID]:
        layer=by[id_]
        entry={
            "id":id_,"name":layer["name"],"institution":layer.get("source"),
            "source":layer.get("source"),"source_type":"institucional_externa" if id_!=RIOS_ID else "derivada_local",
            "provenance_status":"local_operacional_verificado",
            "source_url":layer.get("source_url"),
            "local_file":paths[id_],
            "local_feature_count":counts[id_],
            "local_sha256":manifest["layers"][id_]["sha256"],
            "has_local_file":True,"has_local":True,
            "capture_date":"2026-08-16",
            "metadata_complete":True,
            "precomputed_indices_recalculated":False,
            "note":layer.get("note"),
        }
        if id_==RIOS_ID:
            entry["derived_from"]=HIDRO_ID
            entry["derivation"]="NOME informado e não vazio"
        if id_ in [ESTRADAS_ID,HIDRO_ID]:
            entry["online_query_url"]=layer.get("remote_url")
            entry["online_remote_type"]="arcgis_geojson"
            entry["online_remote_paged"]=True
        prov[id_]=entry
    pp.write_text(pt[:st]+pref2+json.dumps(prov,ensure_ascii=False,separators=(",",":"))+pt[en:],encoding="utf-8",newline="\n")

def add_runtime_layer_registry(repo, ids_to_path):
    # catalog-local.js is the authoritative local loader mapping.
    # nothing else needed; keep files external from index.
    pass

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    args=ap.parse_args()
    repo=Path(args.repo).resolve()
    if not (repo/"docs").is_dir():
        raise RuntimeError("Pasta docs não encontrada")
    current=(repo/"VERSION").read_text(encoding="utf-8-sig").strip()
    if current!=VERSION_BASE:
        raise RuntimeError(f"Base incorreta: {current} | esperada {VERSION_BASE}")

    capture="2026-08-16"
    target=repo/"docs/camadas/arquivos"
    manifest={"version":"V38.4.41","capture_date":capture,"created_at_utc":datetime.now(timezone.utc).isoformat(),
              "principle":"snapshots locais verificáveis para uso offline; nenhum índice precalculado recalculado",
              "layers":{}}

    log("1/4 · Estradas vicinais · PIN MS")
    estr,estrmeta=arcgis_download(ESTRADAS_LAYER,
        "OBJECTID_1,FID_Estrad,OBJECTID,PIST,ID,NOME,JURD,COBE,TIPO,GEOMETRY_L,dist_km")
    estr["name"]="estradas_vicinais_ms"
    validate_fc(estr,{"LineString","MultiLineString"})
    ep=target/"estradas_vicinais_ms.geojson"
    esha=write_geojson(ep,estr)
    manifest["layers"][ESTRADAS_ID]={"file":"./camadas/arquivos/estradas_vicinais_ms.geojson","count":len(estr["features"]),"geometry_types":geom_types(estr),"sha256":esha,"source_url":ESTRADAS_LAYER}

    log("2/4 · Hidrografia · PIN MS")
    hidro,hmeta=arcgis_download(HIDRO_LAYER,"OBJECTID,REGIME,NOME,TRACADO,COMPR_m")
    hidro["name"]="hidrografia_referencia_ms"
    validate_fc(hidro,{"LineString","MultiLineString"})
    hp=target/"hidrografia_referencia_ms.geojson"
    hsha=write_geojson(hp,hidro)
    manifest["layers"][HIDRO_ID]={"file":"./camadas/arquivos/hidrografia_referencia_ms.geojson","count":len(hidro["features"]),"geometry_types":geom_types(hidro),"sha256":hsha,"source_url":HIDRO_LAYER}

    log("3/4 · Rios nomeados · derivação local")
    rios=copy.deepcopy(hidro)
    rios["name"]="rios_principais_ms"
    rios["features"]=[f for f in hidro["features"] if str((f.get("properties") or {}).get("NOME") or "").strip()]
    rios["atlas_metadata"]=dict(hidro.get("atlas_metadata",{}))
    rios["atlas_metadata"].update({"derived_from":HIDRO_ID,"derivation":"NOME não nulo e não vazio","derived_at_utc":datetime.now(timezone.utc).isoformat()})
    validate_fc(rios,{"LineString","MultiLineString"})
    rp=target/"rios_principais_ms.geojson"
    rsha=write_geojson(rp,rios)
    manifest["layers"][RIOS_ID]={"file":"./camadas/arquivos/rios_principais_ms.geojson","count":len(rios["features"]),"geometry_types":geom_types(rios),"sha256":rsha,"derived_from":HIDRO_ID,"filter":"NOME não vazio"}

    log("4/4 · Aeroportos e aeródromos · ANAC")
    aero,sources=download_anac()
    validate_fc(aero,{"Point"})
    apath=target/"aeroportos_aerodromos_ms.geojson"
    asha=write_geojson(apath,aero)
    manifest["layers"][AERO_ID]={"file":"./camadas/arquivos/aeroportos_aerodromos_ms.geojson","count":len(aero["features"]),"geometry_types":geom_types(aero),"sha256":asha,"sources":sources}

    counts={k:v["count"] for k,v in manifest["layers"].items()}
    paths={k:v["file"] for k,v in manifest["layers"].items()}

    # sanity checks
    if counts[ESTRADAS_ID] < 1000:
        raise RuntimeError(f"Estradas: contagem inesperadamente baixa {counts[ESTRADAS_ID]}")
    if counts[HIDRO_ID] < 1000:
        raise RuntimeError(f"Hidrografia: contagem inesperadamente baixa {counts[HIDRO_ID]}")
    if not (0 < counts[RIOS_ID] <= counts[HIDRO_ID]):
        raise RuntimeError("Rios nomeados: relação de contagem inválida")
    if counts[AERO_ID] < 5:
        raise RuntimeError(f"Aeródromos MS: contagem inesperadamente baixa {counts[AERO_ID]}")

    update_catalog(repo,counts,paths,manifest)

    mp=repo/"docs/dados/snapshots/materializacao_offline_20260816.json"
    mp.parent.mkdir(parents=True,exist_ok=True)
    mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    # Version + changelog
    (repo/"VERSION").write_text(VERSION_FINAL+"\n",encoding="utf-8")
    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=ch.read_text(encoding="utf-8-sig")
        c+=f"""

## V38.4.41 · Materialização Offline I · {capture}

- Estradas vicinais reconstruídas diretamente do serviço oficial PIN MS / AGRAER.
- Hidrografia MS materializada como snapshot local mestre.
- Rios nomeados derivados localmente da hidrografia pelo campo NOME informado.
- Aeroportos e aeródromos materializados dos dados abertos oficiais ANAC, públicos e privados, com filtro UF=MS.
- SHA256, contagens, fontes e método registrados no manifesto de materialização.
- Nenhum índice precalculado foi recalculado.
"""
        ch.write_text(c,encoding="utf-8",newline="\n")

    # final audit
    audit={"version":VERSION_FINAL,"status":"PASS","capture_date":capture,"counts":counts,
           "checks":{
             "estradas_geometry":geom_types(estr),
             "hidrografia_geometry":geom_types(hidro),
             "rios_geometry":geom_types(rios),
             "aerodromos_geometry":geom_types(aero),
             "rios_subset":counts[RIOS_ID] <= counts[HIDRO_ID],
             "all_nonzero":all(v>0 for v in counts.values()),
             "manifest":str(mp.relative_to(repo)).replace("\\","/")
           }}
    (repo/"AUDITORIA_V38_4_41_MATERIALIZACAO_OFFLINE_I.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    log("")
    log("PASS · V38.4.41 MATERIALIZAÇÃO OFFLINE I")
    for k,v in counts.items():log(f"  {k} · {v} feições")
    log("  0 índices recalculados")

if __name__=="__main__":
    main()
