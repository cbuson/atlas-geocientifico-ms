from pathlib import Path
import argparse, json, urllib.request, urllib.parse, urllib.error
import time, hashlib, csv, io, re, unicodedata, html as htmlmod
from html.parser import HTMLParser
from datetime import datetime, timezone

BASE_VERSION="V38.4.41A-ESTRADAS-VICINAIS-OFFLINE-1.0-20260816"
FINAL_VERSION="V38.4.41B-RIOS-NOMEADOS-AERODROMOS-OFFLINE-1.0-20260816"

RIOS_ID="rios_principais_ms"
AERO_ID="aeroportos_aerodromos_ms"

HIDRO_LAYER="https://www.pinms.ms.gov.br/arcgis/rest/services/AGRAER_SERVICOS/Hidrografia_MS/FeatureServer/0"
RIOS_WHERE="NOME IS NOT NULL AND NOME <> ''"

ANAC_PUBLIC_PAGE="https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/aerodromos/lista-de-aerodromos-publicos-v2"
ANAC_PRIVATE_PAGE="https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/aerodromos/lista-de-aerodromos-privados-v2"

UA="ITA-ARANDU-MS/38.4.41B"

def log(x): print(x,flush=True)

def get(url,timeout=90,retries=6,binary=False):
    last=None
    for attempt in range(1,retries+1):
        try:
            r=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*","Connection":"close"})
            with urllib.request.urlopen(r,timeout=timeout) as h:
                data=h.read()
                final=h.geturl()
                enc=h.headers.get_content_charset() or "utf-8"
            if binary:return data,final
            for e in [enc,"utf-8-sig","latin-1"]:
                try:return data.decode(e),final
                except UnicodeDecodeError:pass
            return data.decode("utf-8","replace"),final
        except Exception as e:
            last=e
            if attempt==retries: raise
            wait=min(20,2**attempt)
            log(f"  conexão interrompida · tentativa {attempt}/{retries} · aguardando {wait}s")
            time.sleep(wait)
    raise last

def request_json(url):
    txt,_=get(url)
    return json.loads(txt)

def arcgis_meta(url):
    j=request_json(url+"?f=json")
    if "error" in j:raise RuntimeError(j["error"])
    return j

def arcgis_count(url,where):
    q=urllib.parse.urlencode({"where":where,"returnCountOnly":"true","f":"json"})
    j=request_json(url+"/query?"+q)
    if "error" in j:raise RuntimeError(j["error"])
    return int(j["count"])

def download_named_rivers():
    meta=arcgis_meta(HIDRO_LAYER)
    fields={x.get("name") for x in meta.get("fields",[])}
    if "NOME" not in fields:
        raise RuntimeError(f"Campo NOME não localizado na hidrografia. Campos: {sorted(fields)[:40]}")
    total=arcgis_count(HIDRO_LAYER,RIOS_WHERE)
    if total<=0:raise RuntimeError("Consulta de rios nomeados retornou zero feições")
    page=min(200,int(meta.get("maxRecordCount") or 1000))
    feats=[];offset=0
    while offset<total:
        q=urllib.parse.urlencode({
            "where":RIOS_WHERE,
            "outFields":"OBJECTID,REGIME,NOME,TRACADO,COMPR_m",
            "returnGeometry":"true",
            "outSR":"4326",
            "resultOffset":str(offset),
            "resultRecordCount":str(page),
            "orderByFields":"OBJECTID",
            "f":"geojson"
        })
        j=request_json(HIDRO_LAYER+"/query?"+q)
        if j.get("type")!="FeatureCollection":
            raise RuntimeError(f"Rios nomeados · resposta inválida em offset {offset}")
        b=j.get("features") or []
        if not b:raise RuntimeError(f"Rios nomeados · página vazia em offset {offset}")
        feats.extend(b);offset+=len(b)
        log(f"  rios nomeados {len(feats)}/{total}")
        time.sleep(.15)
    if len(feats)!=total:raise RuntimeError(f"Rios nomeados · contagem divergente {len(feats)} != {total}")
    fc={"type":"FeatureCollection","name":"rios_principais_ms","features":feats,
        "atlas_metadata":{
            "source":"PIN MS / AGRAER · Hidrografia MS",
            "source_url":HIDRO_LAYER,
            "capture_utc":datetime.now(timezone.utc).isoformat(),
            "filter":RIOS_WHERE,
            "output_crs":"EPSG:4326",
            "method":"consulta direta da fonte oficial somente com NOME informado",
            "continuous_hydrology_snapshot":False
        }}
    return fc,total,meta

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.href=None;self.txt=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            self.href=dict(attrs).get("href");self.txt=[]
    def handle_data(self,data):
        if self.href is not None:self.txt.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self.href is not None:
            self.links.append((self.href," ".join(self.txt).strip()))
            self.href=None;self.txt=[]

def norm(s):
    s=unicodedata.normalize("NFKD",str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).strip().lower()

def page_links(url):
    txt,final=get(url)
    p=Links();p.feed(txt)
    return [(urllib.parse.urljoin(final,h),t) for h,t in p.links if h]

def discover_anac_entry(page):
    links=page_links(page)
    scored=[]
    for u,t in links:
        n=norm(t+" "+u);score=0
        if "csv" in n:score+=5
        if "json" in n:score+=5
        if "formato" in n:score+=3
        if "aerodrom" in n:score+=2
        if "dadosabertos" in u.lower():score+=8
        if score:scored.append((score,u,t))
    if not scored:raise RuntimeError(f"ANAC · link CSV/JSON não localizado em {page}")
    scored.sort(reverse=True)
    return scored[0][1]

def discover_data_file(entry):
    txt,final=get(entry)
    if re.search(r"\.(csv|json)(?:$|\?)",final,re.I):return final
    p=Links();p.feed(txt)
    candidates=[]
    for h,t in p.links:
        u=urllib.parse.urljoin(final,h);low=u.lower()
        if low.endswith(".csv") or ".csv?" in low:candidates.append((5,u))
        elif low.endswith(".json") or ".json?" in low:candidates.append((4,u))
    if not candidates:
        for h in re.findall(r'href=["\']([^"\']+)["\']',txt,re.I):
            u=urllib.parse.urljoin(final,htmlmod.unescape(h));low=u.lower()
            if low.endswith(".csv"):candidates.append((5,u))
            elif low.endswith(".json"):candidates.append((4,u))
    if not candidates:raise RuntimeError(f"ANAC · arquivo CSV/JSON não localizado em {final}")
    candidates.sort(reverse=True)
    return candidates[0][1]

def read_rows(url):
    data,final=get(url,binary=True)
    rawsha=hashlib.sha256(data).hexdigest()
    if final.lower().endswith(".json") or data.lstrip().startswith((b"[",b"{")):
        obj=None
        for enc in ["utf-8-sig","latin-1"]:
            try:obj=json.loads(data.decode(enc));break
            except Exception:pass
        if obj is None:raise RuntimeError("ANAC · JSON inválido")
        if isinstance(obj,dict):
            for k in ["data","records","items","features"]:
                if isinstance(obj.get(k),list):obj=obj[k];break
        rows=[]
        if not isinstance(obj,list):raise RuntimeError("ANAC · JSON não tabular")
        for x in obj:
            if isinstance(x,dict) and x.get("type")=="Feature":
                y=dict(x.get("properties") or {})
                y["_geometry"]=x.get("geometry")
                rows.append(y)
            elif isinstance(x,dict):rows.append(x)
        return rows,final,rawsha
    text=None
    for enc in ["utf-8-sig","latin-1"]:
        try:text=data.decode(enc);break
        except UnicodeDecodeError:pass
    if text is None:text=data.decode("utf-8","replace")
    try:dialect=csv.Sniffer().sniff(text[:12000],delimiters=";,|\t")
    except Exception:
        dialect=csv.excel;dialect.delimiter=";"
    return list(csv.DictReader(io.StringIO(text),dialect=dialect)),final,rawsha

def find_field(row,aliases):
    keys={norm(k):k for k in row}
    for a in aliases:
        if norm(a) in keys:return keys[norm(a)]
    for a in aliases:
        na=norm(a)
        for nk,k in keys.items():
            if na in nk:return k
    return None

def coord(v):
    if v is None:return None
    if isinstance(v,(int,float)):return float(v)
    s=str(v).strip()
    if not s:return None
    try:return float(s.replace(",","."))
    except:pass
    nums=[float(x.replace(",",".")) for x in re.findall(r"\d+(?:[.,]\d+)?",s)]
    if not nums:return None
    x=nums[0]+(nums[1]/60 if len(nums)>1 else 0)+(nums[2]/3600 if len(nums)>2 else 0)
    if re.search(r"[SW]",s,re.I):x=-x
    return x

def anac_features(rows,kind):
    if not rows:raise RuntimeError(f"ANAC {kind} · tabela vazia")
    sample=rows[0]
    uf=find_field(sample,["UF","Unidade Federativa","Estado"])
    lat=find_field(sample,["Latitude","LAT"])
    lon=find_field(sample,["Longitude","LON","LONG"])
    if not uf:raise RuntimeError(f"ANAC {kind} · campo UF não identificado · {list(sample)[:25]}")
    if (not lat or not lon) and "_geometry" not in sample:
        raise RuntimeError(f"ANAC {kind} · latitude/longitude não identificadas · {list(sample)[:25]}")
    feats=[];rejected=0
    for r in rows:
        if norm(r.get(uf)) not in {"ms","mato grosso do sul"}:continue
        g=r.get("_geometry")
        if not g:
            y=coord(r.get(lat));x=coord(r.get(lon))
            if y is None or x is None or not(-25.5<=y<=-16.0 and -59.5<=x<=-49.0):
                rejected+=1;continue
            g={"type":"Point","coordinates":[x,y]}
        p={str(k):v for k,v in r.items() if k!="_geometry"}
        p["_ita_tipo_cadastro"]=kind
        feats.append({"type":"Feature","geometry":g,"properties":p})
    if not feats:raise RuntimeError(f"ANAC {kind} · zero pontos válidos em MS")
    return feats,rejected,{"uf":uf,"lat":lat,"lon":lon}

def download_anac():
    feats=[];sources=[]
    for kind,page in [("publico",ANAC_PUBLIC_PAGE),("privado",ANAC_PRIVATE_PAGE)]:
        log(f"ANAC · {kind}")
        entry=discover_anac_entry(page)
        file=discover_data_file(entry)
        log(f"  arquivo {file}")
        rows,final,rawsha=read_rows(file)
        f,rejected,fields=anac_features(rows,kind)
        feats.extend(f)
        sources.append({"kind":kind,"page":page,"entry":entry,"file":final,"source_sha256":rawsha,"records_ms":len(f),"rejected_ms":rejected,"fields":fields})
    fc={"type":"FeatureCollection","name":"aeroportos_aerodromos_ms","features":feats,
        "atlas_metadata":{"source":"ANAC · Dados Abertos","capture_utc":datetime.now(timezone.utc).isoformat(),
                          "output_crs":"EPSG:4326","sources":sources}}
    return fc,len(feats),sources

def validate_fc(fc,allowed):
    if fc.get("type")!="FeatureCollection" or not isinstance(fc.get("features"),list):
        raise RuntimeError("FeatureCollection inválida")
    if not fc["features"]:raise RuntimeError("FeatureCollection vazia")
    types={f.get("geometry",{}).get("type") for f in fc["features"] if f.get("geometry")}
    if not types.issubset(set(allowed)):raise RuntimeError(f"Geometrias inesperadas {sorted(types)}")
    return sorted(types)

def write_fc(path,fc):
    raw=json.dumps(fc,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

def extract_catalog(txt):
    pref="const CATALOG=";end=txt.find(";",len(pref))
    return json.loads(txt[len(pref):end]),end

def update(repo,counts,shas,paths):
    app=repo/"docs/assets/js/app.js";txt=app.read_text(encoding="utf-8")
    cat,end=extract_catalog(txt);by={x["id"]:x for x in cat["layers"]}
    for id_ in [RIOS_ID,AERO_ID]:
        if id_ not in by:raise RuntimeError(f"Camada ausente no catálogo {id_}")
    by[RIOS_ID].update({
        "status":"incorporada","count":counts[RIOS_ID],
        "validation":"snapshot local seletivo da fonte oficial PIN MS / AGRAER · somente NOME informado · 16/08/2026",
        "note":"Consulta direta apenas dos trechos nomeados. A hidrografia completa não foi materializada neste corte.",
        "expected_geometry":"LineString"
    })
    by[AERO_ID].update({
        "status":"incorporada","count":counts[AERO_ID],"scope_level":"MS",
        "validation":"snapshot local de dados abertos ANAC V2 · públicos e privados · filtro MS · 16/08/2026",
        "note":"Aeródromos públicos e privados para apoio logístico de campanhas de campo.",
        "source_url":ANAC_PUBLIC_PAGE,
        "expected_geometry":"Point"
    })
    app.write_text("const CATALOG="+json.dumps(cat,ensure_ascii=False,separators=(",",":"))+txt[end:],encoding="utf-8",newline="\n")

    cp=repo/"docs/camadas/catalogo-local.js";ct=cp.read_text(encoding="utf-8")
    pref="window.ITA_LOCAL_LAYER_FILES=";st=ct.find(pref);en=ct.find(";",st)
    reg=json.loads(ct[st+len(pref):en]);reg.update(paths)
    cp.write_text(ct[:st]+pref+json.dumps(reg,ensure_ascii=False,separators=(",",":"))+ct[en:],encoding="utf-8",newline="\n")

    pp=repo/"docs/camadas/proveniencia-snapshots.js";pt=pp.read_text(encoding="utf-8")
    pref2="window.ITA_LAYER_PROVENANCE=";st=pt.find(pref2);en=pt.find(";",st)
    prov=json.loads(pt[st+len(pref2):en])
    prov[RIOS_ID]={
        **prov.get(RIOS_ID,{}),"id":RIOS_ID,"name":by[RIOS_ID]["name"],
        "institution":"PIN MS / AGRAER","source":"PIN MS / AGRAER · Hidrografia MS",
        "source_type":"institucional_externa","provenance_status":"local_operacional_verificado",
        "source_url":HIDRO_LAYER,"local_file":paths[RIOS_ID],"local_feature_count":counts[RIOS_ID],
        "local_sha256":shas[RIOS_ID],"has_local":True,"has_local_file":True,
        "capture_date":"2026-08-16","metadata_complete":True,
        "derivation":"consulta direta com NOME IS NOT NULL AND NOME <> ''",
        "note":"Snapshot seletivo de trechos nomeados. Hidrografia completa não materializada."
    }
    prov[AERO_ID]={
        **prov.get(AERO_ID,{}),"id":AERO_ID,"name":by[AERO_ID]["name"],
        "institution":"ANAC","source":"ANAC · Dados Abertos · Aeródromos V2",
        "source_type":"institucional_externa","provenance_status":"local_operacional_verificado",
        "source_url":ANAC_PUBLIC_PAGE,"local_file":paths[AERO_ID],"local_feature_count":counts[AERO_ID],
        "local_sha256":shas[AERO_ID],"has_local":True,"has_local_file":True,
        "capture_date":"2026-08-16","metadata_complete":True,
        "note":"Dados públicos e privados V2 filtrados para Mato Grosso do Sul."
    }
    pp.write_text(pt[:st]+pref2+json.dumps(prov,ensure_ascii=False,separators=(",",":"))+pt[en:],encoding="utf-8",newline="\n")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo",required=True);args=ap.parse_args()
    repo=Path(args.repo).resolve()
    current=(repo/"VERSION").read_text(encoding="utf-8-sig").strip()
    if current!=BASE_VERSION:raise RuntimeError(f"Base incorreta {current} | esperada {BASE_VERSION}")

    log("1/2 · Rios nomeados · PIN MS")
    rios,rcount,rmeta=download_named_rivers()
    rtypes=validate_fc(rios,{"LineString","MultiLineString"})
    rpath=repo/"docs/camadas/arquivos/rios_principais_ms.geojson"
    rsha=write_fc(rpath,rios)

    log("2/2 · Aeroportos e aeródromos · ANAC")
    aero,acount,asources=download_anac()
    atypes=validate_fc(aero,{"Point"})
    if acount<5:raise RuntimeError(f"ANAC · contagem inesperadamente baixa em MS {acount}")
    apath=repo/"docs/camadas/arquivos/aeroportos_aerodromos_ms.geojson"
    asha=write_fc(apath,aero)

    counts={RIOS_ID:rcount,AERO_ID:acount}
    shas={RIOS_ID:rsha,AERO_ID:asha}
    paths={RIOS_ID:"./camadas/arquivos/rios_principais_ms.geojson",AERO_ID:"./camadas/arquivos/aeroportos_aerodromos_ms.geojson"}
    update(repo,counts,shas,paths)

    manifest={
        "version":FINAL_VERSION,"capture_date":"2026-08-16","created_at_utc":datetime.now(timezone.utc).isoformat(),
        "hydrography_full_materialized":False,
        "layers":{
            RIOS_ID:{"count":rcount,"geometry_types":rtypes,"sha256":rsha,"source_url":HIDRO_LAYER,"where":RIOS_WHERE,"file":paths[RIOS_ID]},
            AERO_ID:{"count":acount,"geometry_types":atypes,"sha256":asha,"sources":asources,"file":paths[AERO_ID]}
        },
        "indices_recalculated":False
    }
    mp=repo/"docs/dados/snapshots/rios_nomeados_aerodromos_20260816.json"
    mp.parent.mkdir(parents=True,exist_ok=True)
    mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    (repo/"VERSION").write_text(FINAL_VERSION+"\n",encoding="utf-8")
    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=ch.read_text(encoding="utf-8-sig")
        c+="""\n\n## V38.4.41B · Rios nomeados e aeródromos offline · 2026-08-16\n\n- Rios nomeados materializados diretamente do serviço oficial PIN MS / AGRAER por consulta seletiva do campo NOME.\n- Hidrografia completa permanece conectada e não foi materializada.\n- Aeródromos públicos e privados V2 da ANAC materializados e filtrados para Mato Grosso do Sul.\n- Snapshots locais registrados com SHA256 e contagens.\n- Estradas vicinais da V38.4.41A permanecem intactas.\n- Nenhum índice foi recalculado.\n"""
        ch.write_text(c,encoding="utf-8",newline="\n")
    audit={"status":"PASS","version":FINAL_VERSION,"counts":counts,"geometry":{"rios":rtypes,"aerodromos":atypes},"hydrography_full_materialized":False,"indices_recalculated":0}
    (repo/"AUDITORIA_V38_4_41B_RIOS_AERODROMOS.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    log("")
    log("PASS · V38.4.41B")
    log(f"  rios nomeados · {rcount} feições")
    log(f"  aeródromos · {acount} pontos")
    log("  hidrografia completa · não materializada")
    log("  estradas vicinais · preservadas")
    log("  0 índices recalculados")

if __name__=="__main__":
    main()
