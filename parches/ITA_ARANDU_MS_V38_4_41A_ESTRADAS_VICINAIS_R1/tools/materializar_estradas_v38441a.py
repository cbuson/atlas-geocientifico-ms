from pathlib import Path
import argparse, json, urllib.request, urllib.parse, time, hashlib, sys
from datetime import datetime, timezone

BASE_VERSION="V38.4.40B-CAMADAS-UX-CLEAN-1.0-20260816"
FINAL_VERSION="V38.4.41A-ESTRADAS-VICINAIS-OFFLINE-1.0-20260816"
LAYER_ID="estradas_vicinais_ms"
LAYER_URL="https://www.pinms.ms.gov.br/arcgis/rest/services/AGRAER_SERVICOS/Estradas_Vicinais/MapServer/0"
OUT_FIELDS="OBJECTID_1,FID_Estrad,OBJECTID,PIST,ID,NOME,JURD,COBE,TIPO,GEOMETRY_L,dist_km"
UA="ITA-ARANDU-MS/38.4.41A"

def log(x):
    print(x,flush=True)

def get(url,timeout=90,retries=6):
    last=None
    for attempt in range(1,retries+1):
        try:
            r=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*","Connection":"close"})
            with urllib.request.urlopen(r,timeout=timeout) as h:
                return h.read()
        except Exception as e:
            last=e
            if attempt==retries:
                raise
            wait=min(20,2**attempt)
            log(f"  conexão interrompida · tentativa {attempt}/{retries} · aguardando {wait}s")
            time.sleep(wait)
    raise last

def request_json(url):
    return json.loads(get(url).decode("utf-8"))

def meta():
    j=request_json(LAYER_URL+"?f=json")
    if "error" in j: raise RuntimeError(j["error"])
    return j

def count():
    q=urllib.parse.urlencode({"where":"1=1","returnCountOnly":"true","f":"json"})
    j=request_json(LAYER_URL+"/query?"+q)
    if "error" in j: raise RuntimeError(j["error"])
    return int(j["count"])

def download():
    m=meta()
    total=count()
    page=min(250,int(m.get("maxRecordCount") or 1000))
    feats=[]
    offset=0
    while offset<total:
        q=urllib.parse.urlencode({
            "where":"1=1",
            "outFields":OUT_FIELDS,
            "returnGeometry":"true",
            "outSR":"4326",
            "resultOffset":str(offset),
            "resultRecordCount":str(page),
            "orderByFields":"OBJECTID_1",
            "f":"geojson"
        })
        j=request_json(LAYER_URL+"/query?"+q)
        if j.get("type")!="FeatureCollection":
            raise RuntimeError(f"Resposta inválida em offset {offset}")
        batch=j.get("features") or []
        if not batch:
            raise RuntimeError(f"Página vazia em offset {offset}")
        feats.extend(batch)
        offset+=len(batch)
        log(f"  {len(feats)}/{total} feições")
        time.sleep(0.15)
    if len(feats)!=total:
        raise RuntimeError(f"Contagem divergente {len(feats)} != {total}")
    fc={
        "type":"FeatureCollection",
        "name":"estradas_vicinais_ms",
        "features":feats,
        "atlas_metadata":{
            "source":"PIN MS / AGRAER · Estradas Vicinais MS",
            "source_url":LAYER_URL,
            "capture_utc":datetime.now(timezone.utc).isoformat(),
            "source_crs":"EPSG:4674",
            "output_crs":"EPSG:4326",
            "arcgis_reported_count":total,
            "method":"ArcGIS REST paginado · 250 feições por requisição · retries automáticos"
        }
    }
    return fc,m,total

def validate(fc,total):
    if fc.get("type")!="FeatureCollection": raise RuntimeError("GeoJSON inválido")
    if len(fc.get("features") or [])!=total: raise RuntimeError("Contagem final inválida")
    if total<1000: raise RuntimeError(f"Contagem inesperadamente baixa {total}")
    types={f.get("geometry",{}).get("type") for f in fc["features"] if f.get("geometry")}
    if not types or not types.issubset({"LineString","MultiLineString"}):
        raise RuntimeError(f"Geometrias inesperadas {sorted(types)}")
    return sorted(types)

def sha(b): return hashlib.sha256(b).hexdigest()

def update(repo,count,local_sha):
    app=repo/"docs/assets/js/app.js"
    txt=app.read_text(encoding="utf-8")
    prefix="const CATALOG="
    end=txt.find(";",len(prefix))
    cat=json.loads(txt[len(prefix):end])
    layer=next((x for x in cat["layers"] if x.get("id")==LAYER_ID),None)
    if not layer: raise RuntimeError("Camada estradas_vicinais_ms não localizada no CATALOG")
    layer.update({
        "status":"incorporada",
        "count":count,
        "validation":"snapshot local reconstruído e verificado a partir do serviço oficial PIN MS / AGRAER · 16/08/2026",
        "note":"Snapshot legado com falha CRC descartado. Esta versão usa reconstrução integral da fonte oficial.",
        "expected_geometry":"LineString"
    })
    app.write_text(prefix+json.dumps(cat,ensure_ascii=False,separators=(",",":"))+txt[end:],encoding="utf-8",newline="\n")

    cp=repo/"docs/camadas/catalogo-local.js"
    ct=cp.read_text(encoding="utf-8")
    pref="window.ITA_LOCAL_LAYER_FILES="
    st=ct.find(pref); en=ct.find(";",st)
    reg=json.loads(ct[st+len(pref):en])
    reg[LAYER_ID]="./camadas/arquivos/estradas_vicinais_ms.geojson"
    cp.write_text(ct[:st]+pref+json.dumps(reg,ensure_ascii=False,separators=(",",":"))+ct[en:],encoding="utf-8",newline="\n")

    pp=repo/"docs/camadas/proveniencia-snapshots.js"
    pt=pp.read_text(encoding="utf-8")
    pref2="window.ITA_LAYER_PROVENANCE="
    st=pt.find(pref2); en=pt.find(";",st)
    prov=json.loads(pt[st+len(pref2):en])
    old=prov.get(LAYER_ID,{})
    old.update({
        "id":LAYER_ID,
        "name":"Estradas vicinais e acessos rurais de Mato Grosso do Sul",
        "institution":"PIN MS / AGRAER",
        "source":"PIN MS / AGRAER · Estradas Vicinais MS",
        "source_type":"institucional_externa",
        "provenance_status":"local_operacional_verificado",
        "source_url":LAYER_URL,
        "local_file":"./camadas/arquivos/estradas_vicinais_ms.geojson",
        "local_feature_count":count,
        "local_sha256":local_sha,
        "has_local":True,
        "has_local_file":True,
        "capture_date":"2026-08-16",
        "metadata_complete":True,
        "note":"Reconstrução integral da fonte oficial. O snapshot herdado com falha CRC não foi reutilizado."
    })
    prov[LAYER_ID]=old
    pp.write_text(pt[:st]+pref2+json.dumps(prov,ensure_ascii=False,separators=(",",":"))+pt[en:],encoding="utf-8",newline="\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    args=ap.parse_args()
    repo=Path(args.repo).resolve()
    current=(repo/"VERSION").read_text(encoding="utf-8-sig").strip()
    if current!=BASE_VERSION:
        raise RuntimeError(f"Base incorreta {current} | esperada {BASE_VERSION}")

    log("ITA ARANDU MS · Estradas Vicinais · materialização offline")
    fc,m,total=download()
    types=validate(fc,total)
    raw=json.dumps(fc,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    out=repo/"docs/camadas/arquivos/estradas_vicinais_ms.geojson"
    out.write_bytes(raw)
    digest=sha(raw)

    update(repo,total,digest)

    manifest={
        "version":FINAL_VERSION,
        "capture_date":"2026-08-16",
        "layer_id":LAYER_ID,
        "source_url":LAYER_URL,
        "count":total,
        "geometry_types":types,
        "sha256":digest,
        "file":"docs/camadas/arquivos/estradas_vicinais_ms.geojson",
        "source_max_record_count":m.get("maxRecordCount"),
        "page_size_used":250,
        "indices_recalculated":False
    }
    mp=repo/"docs/dados/snapshots/estradas_vicinais_20260816.json"
    mp.parent.mkdir(parents=True,exist_ok=True)
    mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    (repo/"VERSION").write_text(FINAL_VERSION+"\n",encoding="utf-8")
    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=ch.read_text(encoding="utf-8-sig")
        c+="""\n\n## V38.4.41A · Estradas Vicinais Offline · 2026-08-16\n\n- Reconstrução integral de Estradas Vicinais MS a partir do serviço oficial PIN MS / AGRAER.\n- Snapshot herdado com falha CRC descartado.\n- Download paginado em blocos de 250 feições com reintentos automáticos.\n- Snapshot local validado e registrado com SHA256.\n- Nenhum índice foi recalculado.\n"""
        ch.write_text(c,encoding="utf-8",newline="\n")

    audit={"status":"PASS","version":FINAL_VERSION,"count":total,"geometry_types":types,"sha256":digest,"indices_recalculated":0}
    (repo/"AUDITORIA_V38_4_41A_ESTRADAS_VICINAIS.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    log("")
    log("PASS · Estradas vicinais incorporadas")
    log(f"  {total} feições")
    log(f"  geometrias {types}")
    log(f"  SHA256 {digest}")
    log("  0 índices recalculados")

if __name__=="__main__":
    main()
