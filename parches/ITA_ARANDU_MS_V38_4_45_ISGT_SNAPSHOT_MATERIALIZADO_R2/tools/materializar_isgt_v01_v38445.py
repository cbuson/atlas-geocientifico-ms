from __future__ import annotations
from pathlib import Path
import argparse, json, urllib.request, urllib.parse, urllib.error
import hashlib, time, sys, subprocess, site, importlib
from datetime import datetime, timezone
from collections import Counter

EXPECTED="V38.4.44-ISGT-UI-FIX-1.0-20260816"
FINAL="V38.4.45-ISGT-V01-SNAPSHOT-MATERIALIZADO-1.0-20260816"
UA="ITA-ARANDU-MS/38.4.45-ISGT"

SOURCES={
 "terras_indigenas_poligonos":{
   "base":"https://pamgia.ibama.gov.br/server/rest/services/01_Publicacoes_Bases/lim_terra_indigena_a/FeatureServer/12",
   "where":"1=1",
   "label":"Terras Indígenas · FUNAI",
   "file":"terras_indigenas_funai_ms.geojson",
   "mandatory":True
 },
 "territorios_quilombolas_poligonos":{
   "base":"https://pamgia.ibama.gov.br/server/rest/services/BasesSincronizadas/lim_quilombos_incra_a/FeatureServer/0",
   "where":"1=1",
   "label":"Territórios Quilombolas · INCRA",
   "file":"territorios_quilombolas_incra_ms.geojson",
   "mandatory":True
 },
 "unidades_conservacao_cnuc_ms":{
   "base":"https://pamgia.ibama.gov.br/server/rest/services/BasesSincronizadas/lim_unidades_conserva%C3%A7%C3%A3o_mma_a/FeatureServer/0",
   "where":"1=1",
   "label":"Unidades de Conservação · CNUC/MMA",
   "file":"unidades_conservacao_cnuc_ms.geojson",
   "mandatory":True
 },
 "zonas_amortecimento_ms":{
   "base":"https://www.pinms.ms.gov.br/arcgis/rest/services/IMASUL/CAMADAS_API_SISGEO_v1/FeatureServer/2",
   "where":"1=1",
   "label":"Zonas de amortecimento · IMASUL/PIN MS",
   "file":"zonas_amortecimento_ms.geojson",
   "mandatory":True
 },
 "corredores_ecologicos_ms":{
   "base":"https://www.pinms.ms.gov.br/arcgis/rest/services/IMASUL/CAMADAS_API_SISGEO_v1/FeatureServer/16",
   "where":"1=1",
   "label":"Corredores ecológicos · IMASUL/PIN MS",
   "file":"corredores_ecologicos_ms.geojson",
   "mandatory":True
 },
 "areas_uso_restrito_ms":{
   "base":"https://www.pinms.ms.gov.br/arcgis/rest/services/IMASUL/CAMADAS_API_SISGEO_v1/FeatureServer/12",
   "where":"1=1",
   "label":"Áreas de uso restrito · IMASUL/PIN MS",
   "file":"areas_uso_restrito_ms.geojson",
   "mandatory":True
 },
 "aur_pantanal_ms":{
   "base":"https://www.pinms.ms.gov.br/arcgis/rest/services/IMASUL/CAMADAS_API_SISGEO_v1/FeatureServer/17",
   "where":"1=1",
   "label":"Área de uso restrito do Pantanal · IMASUL/PIN MS",
   "file":"aur_pantanal_ms.geojson",
   "mandatory":True
 }
}

def log(s=""):
    print(s, flush=True)

def ensure_spatial_deps():
    try:
        import shapely, pyproj
        return
    except Exception:
        log("Dependências espaciais ausentes · instalando Shapely e pyproj no perfil do usuário")
        subprocess.check_call([
            sys.executable,"-m","pip","install","--user","--disable-pip-version-check",
            "shapely>=2.0","pyproj>=3.6"
        ])
        site.addsitedir(site.getusersitepackages())
        importlib.invalidate_caches()
        import shapely, pyproj

def request_bytes(url, timeout=90, retries=7):
    last=None
    for attempt in range(1,retries+1):
        try:
            req=urllib.request.Request(url, headers={
                "User-Agent":UA,
                "Accept":"application/json, application/geo+json, */*",
                "Connection":"close"
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last=e
            if attempt==retries:
                raise
            wait=min(30, 2**attempt)
            log(f"  conexão interrompida · tentativa {attempt}/{retries} · aguardando {wait}s")
            time.sleep(wait)
    raise last

def request_json(url):
    data=request_bytes(url)
    for enc in ("utf-8-sig","utf-8","latin-1"):
        try:
            return json.loads(data.decode(enc))
        except Exception:
            pass
    raise RuntimeError("Resposta JSON inválida")

def arcgis_params(where, bbox=None):
    p={"where":where,"f":"json"}
    if bbox:
        p.update({
            "geometry":",".join(f"{v:.10f}" for v in bbox),
            "geometryType":"esriGeometryEnvelope",
            "inSR":"4326",
            "spatialRel":"esriSpatialRelIntersects"
        })
    return p

def arcgis_feature_collection(base, where, bbox):
    meta=request_json(base+"?f=json")
    if "error" in meta:
        raise RuntimeError(f"Metadata ArcGIS inválida · {meta['error']}")
    if meta.get("geometryType")!="esriGeometryPolygon":
        raise RuntimeError(f"Geometria inesperada em {base} · {meta.get('geometryType')}")

    p=arcgis_params(where,bbox)
    p["returnIdsOnly"]="true"
    idsj=request_json(base+"/query?"+urllib.parse.urlencode(p))
    if "error" in idsj:
        raise RuntimeError(f"ArcGIS IDs · {idsj['error']}")
    ids=idsj.get("objectIds") or []
    oid_field=idsj.get("objectIdFieldName") or meta.get("objectIdField") or "OBJECTID"
    if not ids:
        raise RuntimeError("Fonte retornou zero feições para o recorte de Mato Grosso do Sul")

    all_features=[]
    batch_size=350
    for i in range(0,len(ids),batch_size):
        chunk=ids[i:i+batch_size]
        q={
            "objectIds":",".join(str(x) for x in chunk),
            "outFields":"*",
            "returnGeometry":"true",
            "outSR":"4326",
            "f":"geojson"
        }
        j=request_json(base+"/query?"+urllib.parse.urlencode(q))
        if j.get("type")!="FeatureCollection":
            raise RuntimeError(f"ArcGIS não retornou GeoJSON · lote {i//batch_size+1}")
        all_features.extend(j.get("features") or [])
        log(f"  {min(i+batch_size,len(ids))}/{len(ids)} feições")
        time.sleep(.08)

    if len(all_features)!=len(ids):
        raise RuntimeError(f"Contagem divergente · IDs {len(ids)} · GeoJSON {len(all_features)}")

    return {
        "type":"FeatureCollection",
        "features":all_features,
        "atlas_metadata":{
            "source_url":base,
            "where":where,
            "capture_utc":datetime.now(timezone.utc).isoformat(),
            "object_id_field":oid_field,
            "arcgis_id_count":len(ids),
            "output_crs":"EPSG:4326"
        }
    }

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def write_json(path,obj,indent=None):
    raw=json.dumps(obj,ensure_ascii=False,indent=indent,separators=None if indent else (",",":")).encode("utf-8")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    return sha_bytes(raw)

def compact_fc(path,fc):
    return write_json(path,fc,indent=None)

def patch_registry(repo, mappings):
    p=repo/"docs/camadas/catalogo-local.js"
    txt=p.read_text(encoding="utf-8")
    pref="window.ITA_LOCAL_LAYER_FILES="
    st=txt.find(pref)
    en=txt.find(";",st)
    if st<0 or en<0:
        raise RuntimeError("catalogo-local.js não reconhecido")
    reg=json.loads(txt[st+len(pref):en])
    reg.update(mappings)
    p.write_text(txt[:st]+pref+json.dumps(reg,ensure_ascii=False,separators=(",",":"))+txt[en:],encoding="utf-8",newline="\n")

def patch_provenance(repo, source_meta, isgt_sha):
    p=repo/"docs/camadas/proveniencia-snapshots.js"
    if not p.exists():
        return
    txt=p.read_text(encoding="utf-8")
    pref="window.ITA_LAYER_PROVENANCE="
    st=txt.find(pref)
    en=txt.find(";",st)
    if st<0 or en<0:
        return
    prov=json.loads(txt[st+len(pref):en])
    for id_,m in source_meta.items():
        old=prov.get(id_,{})
        old.update({
            "id":id_,
            "provenance_status":"local_operacional_verificado",
            "local_file":"./camadas/arquivos/"+SOURCES[id_]["file"],
            "local_feature_count":m["count"],
            "local_sha256":m["sha256"],
            "has_local":True,
            "has_local_file":True,
            "capture_date":m["capture_date"],
            "metadata_complete":True,
            "note":"Snapshot local materializado para o ISGT V0.1 a partir da fonte institucional configurada no Atlas."
        })
        prov[id_]=old
    old=prov.get("contexto_geoetico_250km2",{})
    old.update({
        "id":"contexto_geoetico_250km2",
        "name":"ISGT V0.1 · Triagem de Sensibilidade Geoética Territorial · 250 km²",
        "provenance_status":"local_operacional_verificado",
        "local_file":"./camadas/arquivos/isgt_v01_250km2.geojson",
        "local_feature_count":1554,
        "local_sha256":isgt_sha,
        "has_local":True,
        "has_local_file":True,
        "capture_date":datetime.now(timezone.utc).date().isoformat(),
        "metadata_complete":True,
        "note":"Proposta metodológica experimental materializada. Classificação por regras transparentes, sem score numérico final."
    })
    prov["contexto_geoetico_250km2"]=old
    p.write_text(txt[:st]+pref+json.dumps(prov,ensure_ascii=False,separators=(",",":"))+txt[en:],encoding="utf-8",newline="\n")

def patch_app(repo, source_meta, class_counts):
    p=repo/"docs/assets/js/app.js"
    txt=p.read_text(encoding="utf-8")
    marker="/* V38.4.45 ISGT SNAPSHOT MATERIALIZADO */"
    if marker in txt:
        raise RuntimeError("V38.4.45 já aplicada")

    block=[marker]
    block.append("""{
 const c=CATALOG.layers.find(x=>x.id==='contexto_geoetico_250km2');
 if(c){
   c.name='ISGT V0.1 · Triagem de Sensibilidade Geoética Territorial · 250 km²';
   c.status='incorporada';
   c.kind='derived';
   c.count=1554;
   c.source='ITA ARANDU MS · snapshot local materializado a partir de FUNAI, INCRA, IBGE, CNUC/MMA e IMASUL/PIN MS';
   c.validation='snapshot local · 1.554 hexágonos · proposta metodológica experimental V0.1 · regras transparentes · sem score numérico final';
   c.note='O ISGT V0.1 classifica contextos de atuação geocientífica segundo evidências territoriais e comunitárias documentadas. Não classifica povos ou comunidades, não mede risco ou vulnerabilidade e não constitui autorização de acesso, coleta, fotografia, prospecção ou publicação.';
   delete c.derive_type;
   c.style={color:'#444b50',weight:0.82,fillOpacity:0.76,renderer:'isgt_v01_snapshot'};
 }
}""")
    for id_,m in source_meta.items():
        block.append(f"""{{const c=CATALOG.layers.find(x=>x.id==='{id_}');if(c){{c.status='incorporada';c.count={m['count']};c.validation='snapshot local materializado para ISGT V0.1 · corte {m['capture_date']} · SHA256 {m['sha256'][:12]}…';}}}}""")
    block.append("/* FIM V38.4.45 ISGT SNAPSHOT MATERIALIZADO */")
    anchor="/* V38.4.42 ISGT BASE METODOLOGICA END */"
    if anchor not in txt:
        raise RuntimeError("Âncora ISGT V38.4.42 não localizada")
    txt=txt.replace(anchor,anchor+"\n"+"\n".join(block),1)

    old="if(st.renderer==='geoethics_context'){stroke='#444b50';const gs=String(p.geo_context_status||'');fill=gs==='CONTEXTO_TERRITORIAL_IDENTIFICADO'?'#d9eef3':gs==='CONTEXTO_IDENTIFICADO_COM_COBERTURA_PARCIAL'?'#eef4d8':'rgba(0,0,0,0)';} if(st.renderer==='geoethics_context'){stroke='#444b50';const gs=String(p.geo_context_status||'');fill=gs==='CONTEXTO_TERRITORIAL_IDENTIFICADO'?'#d9eef3':gs==='CONTEXTO_IDENTIFICADO_COM_COBERTURA_PARCIAL'?'#eef4d8':'rgba(0,0,0,0)';}"
    new="""if(st.renderer==='isgt_v01_snapshot'){
   stroke='#444b50';
   const c=String(p.isgt_v01_classe||'SEM_EVIDENCIA_DOCUMENTADA');
   fill=c==='PRESENCA_COMUNITARIA'?'#f5edcf':
        c==='CONTEXTO_TERRITORIAL'?'#deebf7':
        c==='CONTEXTO_TERRITORIAL_E_COMUNITARIO'?'#9ecae1':
        c==='COMPLEXIDADE_TERRITORIAL'?'#4f81bd':
        c==='COBERTURA_INCOMPLETA'?'#e2e2e2':
        'rgba(0,0,0,0)';
 }"""
    if old in txt:
        txt=txt.replace(old,new,1)
    else:
        anchor2="if(st.renderer==='ipg')"
        i=txt.find(anchor2)
        if i<0: raise RuntimeError("Renderer IPG não localizado")
        txt=txt[:i]+new+" "+txt[i:]

    legend_old="if(st.renderer==='geoethics_context')return `<div class=\"legend-layer-title\">${esc(cfg.name)}</div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#d9eef3;border:1px solid #444b50\"></span><span>contexto territorial identificado</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:#eef4d8;border:1px solid #444b50\"></span><span>contexto identificado com cobertura parcial</span></div><div class=\"legend-row\"><span class=\"swatch\" style=\"background:transparent;border:1px solid #444b50\"></span><span>sem interseção identificada ou cobertura incompleta · consultar ficha</span></div><div class=\"legend-note\">As cores descrevem contexto e cobertura. Não representam risco nem pontuação. Ausência de fonte na sessão nunca é convertida em ausência territorial.</div>`;"
    legend_new="""if(st.renderer==='isgt_v01_snapshot')return `<div class="legend-layer-title">${esc(cfg.name)}</div>
<div class="legend-row"><span class="swatch" style="background:transparent;border:1px solid #444b50"></span><span>sem evidência documentada nas fontes do corte</span></div>
<div class="legend-row"><span class="swatch" style="background:#f5edcf;border:1px solid #444b50"></span><span>presença comunitária</span></div>
<div class="legend-row"><span class="swatch" style="background:#deebf7;border:1px solid #444b50"></span><span>contexto territorial</span></div>
<div class="legend-row"><span class="swatch" style="background:#9ecae1;border:1px solid #444b50"></span><span>contexto territorial e comunitário</span></div>
<div class="legend-row"><span class="swatch" style="background:#4f81bd;border:1px solid #444b50"></span><span>complexidade territorial documentada</span></div>
<div class="legend-row"><span class="swatch" style="background:#e2e2e2;border:1px solid #444b50"></span><span>cobertura incompleta</span></div>
<div class="legend-note">ISGT V0.1 é uma proposta experimental por regras transparentes. As classes descrevem diligência da atuação geocientífica e não risco, vulnerabilidade ou valor de povos e comunidades. Dado público não significa autorização.</div>`;"""
    if legend_old in txt:
        txt=txt.replace(legend_old,legend_new,1)
    else:
        anchor3="if(st.renderer==='pag_etr')return"
        i=txt.find(anchor3)
        if i<0: raise RuntimeError("Âncora de legenda não localizada")
        txt=txt[:i]+legend_new+"\n "+txt[i:]

    p.write_text(txt,encoding="utf-8",newline="\n")

def sync_cache_and_version(repo):
    idx=repo/"docs/index.html"
    if idx.exists():
        t=idx.read_text(encoding="utf-8-sig")
        t=t.replace("V38.4.44","V38.4.45")
        t=t.replace("./assets/js/app.js?v=38.4.38","./assets/js/app.js?v=38.4.45")
        t=t.replace("./camadas/catalogo-local.js?v=38.4.26","./camadas/catalogo-local.js?v=38.4.45")
        idx.write_text(t,encoding="utf-8",newline="\n")
    sw=repo/"docs/service-worker.js"
    if sw.exists():
        t=sw.read_text(encoding="utf-8-sig")
        import re
        t=re.sub(r"const ITA_CACHE = '[^']+';","const ITA_CACHE = 'ita-arandu-v38-4-45-isgt-snapshot';",t,count=1)
        t=t.replace("'./assets/js/app.js?v=38.4.38'","'./assets/js/app.js?v=38.4.45'")
        t=t.replace("'./camadas/catalogo-local.js?v=38.4.26'","'./camadas/catalogo-local.js?v=38.4.45'")
        sw.write_text(t,encoding="utf-8",newline="\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    args=ap.parse_args()
    repo=Path(args.repo).resolve()

    cur=(repo/"VERSION").read_text(encoding="utf-8-sig").strip()
    if cur!=EXPECTED:
        raise RuntimeError(f"Base incorreta · {cur} · esperada {EXPECTED}")

    ensure_spatial_deps()
    from shapely.geometry import shape, mapping
    from shapely.strtree import STRtree
    from shapely.ops import transform, unary_union
    from shapely import make_valid
    from pyproj import Transformer

    data_dir=repo/"docs/camadas/arquivos"
    grid_fc=json.loads((data_dir/"malha_r5_250km2.geojson").read_text(encoding="utf-8-sig"))
    ind_fc=json.loads((data_dir/"localidades_indigenas_ibge.geojson").read_text(encoding="utf-8-sig"))
    qui_fc=json.loads((data_dir/"localidades_quilombolas_ibge.geojson").read_text(encoding="utf-8-sig"))
    limit_fc=json.loads((data_dir/"limite_ms_ibge_2025.geojson").read_text(encoding="utf-8-sig"))

    if len(grid_fc.get("features",[]))!=1554:
        raise RuntimeError(f"Malha 250 km² inesperada · {len(grid_fc.get('features',[]))} feições")
    if len(ind_fc.get("features",[]))!=518:
        raise RuntimeError(f"Localidades indígenas inesperadas · {len(ind_fc.get('features',[]))}")
    if len(qui_fc.get("features",[]))!=27:
        raise RuntimeError(f"Localidades quilombolas inesperadas · {len(qui_fc.get('features',[]))}")

    state_ll=make_valid(shape(limit_fc["features"][0]["geometry"]))
    bbox=state_ll.bounds
    capture_date=datetime.now(timezone.utc).date().isoformat()

    log("ITA ARANDU MS · ISGT V0.1 · MATERIALIZAÇÃO SNAPSHOT")
    log("Base local validada · 1.554 hexágonos · 518 localidades indígenas · 27 localidades quilombolas")
    log("")

    source_fc={}
    source_meta={}
    for id_,cfg in SOURCES.items():
        log(cfg["label"])
        fc=arcgis_feature_collection(cfg["base"],cfg["where"],bbox)
        kept=[]
        for f in fc.get("features",[]):
            try:
                g=make_valid(shape(f["geometry"]))
                if not g.is_empty and g.intersects(state_ll):
                    kept.append(f)
            except Exception:
                pass
        if not kept:
            raise RuntimeError(f"{cfg['label']} · zero feições após interseção com MS")
        fc["features"]=kept
        fc["name"]=id_
        fc["atlas_metadata"].update({
            "filtered_to_ms_by_local_boundary":True,
            "ms_feature_count":len(kept),
            "capture_date":capture_date,
            "purpose":"fonte territorial do ISGT V0.1",
            "ms_filter_method":"spatial_envelope_then_exact_intersection_with_ibge_ms_boundary"
        })
        path=data_dir/cfg["file"]
        digest=compact_fc(path,fc)
        source_fc[id_]=fc
        source_meta[id_]={
            "count":len(kept),
            "sha256":digest,
            "capture_date":capture_date,
            "file":"./camadas/arquivos/"+cfg["file"],
            "source_url":cfg["base"]
        }
        log(f"  PASS · {len(kept)} feições · SHA256 {digest[:12]}…")
        log("")

    # Equal-area LAEA centered on Mato Grosso do Sul
    transformer=Transformer.from_crs(
        "EPSG:4326",
        "+proj=laea +lat_0=-20.5 +lon_0=-54.5 +datum=WGS84 +units=m +no_defs",
        always_xy=True
    )
    project=lambda g: transform(transformer.transform,g)

    grid_ll=[make_valid(shape(f["geometry"])) for f in grid_fc["features"]]
    grid_pr=[project(g) for g in grid_ll]
    grid_ids=[str(f.get("properties",{}).get("hex_id") or f"HX-{i}") for i,f in enumerate(grid_fc["features"])]
    grid_tree=STRtree(grid_ll)

    # Assign point records once. Boundary tie is deterministic by hex_id.
    def assign_points(fc):
        counts=Counter()
        names={}
        unassigned=[]
        for pf in fc["features"]:
            p=shape(pf["geometry"])
            idxs=list(grid_tree.query(p,predicate="intersects"))
            if not idxs:
                unassigned.append(pf)
                continue
            idx=min(idxs,key=lambda i:grid_ids[int(i)])
            hid=grid_ids[int(idx)]
            counts[hid]+=1
            props=pf.get("properties") or {}
            nm=props.get("NM_LI") or props.get("NM_CQ") or props.get("NM_TQ") or props.get("NM_AGLOM")
            if nm:
                names.setdefault(hid,[])
                if str(nm) not in names[hid]:
                    names[hid].append(str(nm))
        return counts,names,unassigned

    ai_counts,ai_names,ai_unassigned=assign_points(ind_fc)
    cq_counts,cq_names,cq_unassigned=assign_points(qui_fc)
    if ai_unassigned or cq_unassigned:
        raise RuntimeError(f"Pontos fora da malha · indígenas {len(ai_unassigned)} · quilombolas {len(cq_unassigned)}")
    if sum(ai_counts.values())!=518 or sum(cq_counts.values())!=27:
        raise RuntimeError("Contagem de pontos após associação hexagonal não fecha com os snapshots IBGE")

    # Prepare polygon indexes and projected geometry
    prepared={}
    for id_,fc in source_fc.items():
        ll=[]; pr=[]; feats=[]
        for f in fc["features"]:
            try:
                g=make_valid(shape(f["geometry"]))
                if g.is_empty:
                    continue
                gp=project(g)
                if gp.is_empty:
                    continue
                ll.append(g); pr.append(gp); feats.append(f)
            except Exception:
                continue
        if not ll:
            raise RuntimeError(f"Geometrias válidas ausentes em {id_}")
        prepared[id_]={"ll":ll,"pr":pr,"features":feats,"tree":STRtree(ll)}

    def first_text(props,keys):
        for k in keys:
            v=props.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
        return ""

    core_names={
      "terras_indigenas_poligonos":["terrai_nom","TERRA_INDIG","nome","NOME"],
      "territorios_quilombolas_poligonos":["nome","NOME","nm_comunid","NM_COMUNID","comunidade","COMUNIDADE","territorio","TERRITORIO","nm_quilombo","NM_QUILOMBO"]
    }

    out_features=[]
    class_counts=Counter()
    tiny_area_m2=1.0

    for hi,hf in enumerate(grid_fc["features"]):
        hid=grid_ids[hi]
        hll=grid_ll[hi]
        hpr=grid_pr[hi]
        harea=max(hpr.area,1.0)
        props=dict(hf.get("properties") or {})

        intersections_by={}
        feature_counts={}
        source_names={}

        for id_,s in prepared.items():
            idxs=list(s["tree"].query(hll,predicate="intersects"))
            ints=[]
            n=0
            names=[]
            for idx in idxs:
                idx=int(idx)
                try:
                    inter=hpr.intersection(s["pr"][idx])
                except Exception:
                    continue
                if inter.is_empty or inter.area<=tiny_area_m2:
                    continue
                n+=1
                ints.append(inter)
                if id_ in core_names:
                    nm=first_text(s["features"][idx].get("properties") or {},core_names[id_])
                    if nm and nm not in names:
                        names.append(nm)
            intersections_by[id_]=ints
            feature_counts[id_]=n
            source_names[id_]=names

        def union_area(id_):
            ints=intersections_by.get(id_) or []
            if not ints:return 0.0
            return unary_union(ints).area

        area_ti=union_area("terras_indigenas_poligonos")
        area_tq=union_area("territorios_quilombolas_poligonos")
        ti_tq_ints=(intersections_by.get("terras_indigenas_poligonos") or [])+(intersections_by.get("territorios_quilombolas_poligonos") or [])
        area_joint=unary_union(ti_tq_ints).area if ti_tq_ints else 0.0

        n_ai=int(ai_counts.get(hid,0))
        n_cq=int(cq_counts.get(hid,0))
        pres=n_ai+n_cq
        tem_ti=feature_counts.get("terras_indigenas_poligonos",0)>0
        tem_tq=feature_counts.get("territorios_quilombolas_poligonos",0)>0
        tem_territorio=tem_ti or tem_tq
        tem_presenca=pres>0

        concurrent_ids=[
          "unidades_conservacao_cnuc_ms",
          "zonas_amortecimento_ms",
          "corredores_ecologicos_ms",
          "areas_uso_restrito_ms",
          "aur_pantanal_ms"
        ]
        concurrent_categories=sum(1 for x in concurrent_ids if feature_counts.get(x,0)>0)
        community_regimes=(1 if tem_ti else 0)+(1 if tem_tq else 0)

        classe="SEM_EVIDENCIA_DOCUMENTADA"
        if not tem_territorio and tem_presenca:
            classe="PRESENCA_COMUNITARIA"
        elif tem_territorio and not tem_presenca:
            classe="CONTEXTO_TERRITORIAL"
        elif tem_territorio and tem_presenca:
            classe="CONTEXTO_TERRITORIAL_E_COMUNITARIO"
        if tem_territorio and (community_regimes>1 or concurrent_categories>0):
            classe="COMPLEXIDADE_TERRITORIAL"

        class_counts[classe]+=1

        props.update({
          "isgt_v01_status":"PROPOSTA_METODOLOGICA_EXPERIMENTAL_NAO_VALIDADA",
          "isgt_v01_classe":classe,
          "isgt_v01_formula_numerica":"NAO_DEFINIDA",
          "isgt_v01_pesos":"NAO_APLICADOS",
          "isgt_v01_objeto_avaliado":"DILIGENCIA_DA_ATUACAO_GEOCIENTIFICA",
          "isgt_v01_nao_avalia":"RISCO_VULNERABILIDADE_VALOR_OU_IMPORTANCIA_DAS_COMUNIDADES",
          "isgt_v01_aldeias_indigenas":n_ai,
          "isgt_v01_localidades_quilombolas":n_cq,
          "isgt_v01_presencas_total":pres,
          "isgt_v01_presencas_peso":"EQUIVALENTE_1_POR_OCORRENCIA",
          "isgt_v01_n_ti":feature_counts.get("terras_indigenas_poligonos",0),
          "isgt_v01_n_tq":feature_counts.get("territorios_quilombolas_poligonos",0),
          "isgt_v01_tem_ti":"SIM" if tem_ti else "NAO",
          "isgt_v01_tem_tq":"SIM" if tem_tq else "NAO",
          "isgt_v01_area_ti_km2":round(area_ti/1e6,4),
          "isgt_v01_pct_hex_ti":round(100*area_ti/harea,3),
          "isgt_v01_area_tq_km2":round(area_tq/1e6,4),
          "isgt_v01_pct_hex_tq":round(100*area_tq/harea,3),
          "isgt_v01_area_ti_tq_uniao_km2":round(area_joint/1e6,4),
          "isgt_v01_pct_cobertura_ti_tq":round(100*area_joint/harea,3),
          "isgt_v01_ti_nomes":" · ".join(source_names.get("terras_indigenas_poligonos",[])[:12]),
          "isgt_v01_tq_nomes":" · ".join(source_names.get("territorios_quilombolas_poligonos",[])[:12]),
          "isgt_v01_aldeias_nomes":" · ".join(ai_names.get(hid,[])[:12]),
          "isgt_v01_quilombolas_nomes":" · ".join(cq_names.get(hid,[])[:12]),
          "isgt_v01_n_uc":feature_counts.get("unidades_conservacao_cnuc_ms",0),
          "isgt_v01_n_za":feature_counts.get("zonas_amortecimento_ms",0),
          "isgt_v01_n_corredor":feature_counts.get("corredores_ecologicos_ms",0),
          "isgt_v01_n_aur":feature_counts.get("areas_uso_restrito_ms",0),
          "isgt_v01_n_aur_pantanal":feature_counts.get("aur_pantanal_ms",0),
          "isgt_v01_salvaguardas_concorrentes_n":concurrent_categories,
          "isgt_v01_fontes_primarias_completas":"SIM",
          "isgt_v01_fontes_concorrentes_completas":"SIM",
          "isgt_v01_cobertura_metodo":"UNIAO_GEOMETRICA_TI_TQ" if ti_tq_ints else "SEM_INTERSECAO",
          "isgt_v01_area_metodo":"LAEA_LOCAL_CENTRADA_EM_MS",
          "isgt_v01_regra_ponto_fronteira":"associacao_unica_deterministica_por_hex_id",
          "isgt_v01_corte_dados":capture_date,
          "isgt_v01_versao_metodo":"V0.1",
          "isgt_v01_interpretacao":
             "Há presença comunitária pontual documentada. Pontos não delimitam território e recomendam diligência prévia."
             if classe=="PRESENCA_COMUNITARIA" else
             "Há interseção com territorialidade comunitária documentada. A interseção não constitui autorização de acesso ou coleta."
             if classe=="CONTEXTO_TERRITORIAL" else
             "Há simultaneamente territorialidade e presença comunitária documentadas. Recomenda-se diligência reforçada antes do trabalho de campo."
             if classe=="CONTEXTO_TERRITORIAL_E_COMUNITARIO" else
             "Há territorialidade comunitária associada a mais de um regime territorial comunitário ou ambiental documentado. A classe descreve complexidade de contexto, não risco da comunidade."
             if classe=="COMPLEXIDADE_TERRITORIAL" else
             "Nenhuma evidência foi identificada nas fontes deste corte. O resultado não prova ausência de comunidade, território ou direito.",
          "isgt_v01_orientacao_campo":
             "Dado público não significa autorização. Antes de atividade geocientífica, verificar condições de acesso, autorizações aplicáveis, protocolos comunitários, consentimento quando pertinente e sensibilidade dos dados."
        })

        out_features.append({
            "type":"Feature",
            "properties":props,
            "geometry":hf["geometry"]
        })

    if len(out_features)!=1554:
        raise RuntimeError("ISGT não fechou em 1.554 hexágonos")
    if len({f["properties"]["hex_id"] for f in out_features})!=1554:
        raise RuntimeError("hex_id duplicado no ISGT")
    if sum(class_counts.values())!=1554:
        raise RuntimeError("Distribuição de classes não fecha em 1.554")

    isgt_fc={
      "type":"FeatureCollection",
      "name":"isgt_v01_250km2",
      "features":out_features,
      "atlas_metadata":{
        "produto":"ISGT · Índice de Sensibilidade Geoética Territorial · proposta metodológica experimental V0.1",
        "estado":"NAO_VALIDADO_EXTERNAMENTE",
        "grid":"250 km²",
        "grid_features":1554,
        "classification":"rule_based_experimental",
        "numeric_score":False,
        "weighted_formula":False,
        "capture_date":capture_date,
        "area_method":"Lambert Azimuthal Equal Area local centered on Mato Grosso do Sul",
        "point_rule":"Cada localidade pontual é associada a um único hexágono. Pontos não delimitam território.",
        "principle":"O ISGT avalia necessidade de diligência da atuação geocientífica, não povos ou comunidades.",
        "class_counts":dict(class_counts),
        "sources":{k:source_meta[k] for k in source_meta},
        "local_points":{
          "localidades_indigenas_ibge":518,
          "localidades_quilombolas_ibge":27
        }
      }
    }

    isgt_path=data_dir/"isgt_v01_250km2.geojson"
    isgt_sha=compact_fc(isgt_path,isgt_fc)

    manifest={
      "version":FINAL,
      "capture_date":capture_date,
      "status":"PASS",
      "grid_features":1554,
      "class_counts":dict(class_counts),
      "source_layers":source_meta,
      "isgt":{
        "file":"docs/camadas/arquivos/isgt_v01_250km2.geojson",
        "sha256":isgt_sha,
        "count":1554
      },
      "checks":{
        "grid_exact_1554":True,
        "unique_hex_id_1554":True,
        "indigenous_points_assigned":518,
        "quilombola_points_assigned":27,
        "formula_numeric_defined":False,
        "weights_applied":False,
        "external_validation":False
      }
    }

    manifest_path=repo/"docs/dados/snapshots/isgt_v01_250km2_20260816.json"
    manifest_path.parent.mkdir(parents=True,exist_ok=True)
    write_json(manifest_path,manifest,indent=2)

    mappings={"contexto_geoetico_250km2":"./camadas/arquivos/isgt_v01_250km2.geojson"}
    for id_,m in source_meta.items():
        mappings[id_]=m["file"]
    patch_registry(repo,mappings)
    patch_provenance(repo,source_meta,isgt_sha)
    patch_app(repo,source_meta,class_counts)
    sync_cache_and_version(repo)

    audit={
      "status":"PASS",
      "version":FINAL,
      "grid_features":1554,
      "class_counts":dict(class_counts),
      "source_counts":{k:v["count"] for k,v in source_meta.items()},
      "point_counts":{"indigenas":518,"quilombolas":27},
      "isgt_sha256":isgt_sha,
      "weighted_formula":False,
      "numeric_score":False,
      "external_validation":False,
      "method_state":"PROPOSTA_METODOLOGICA_EXPERIMENTAL_V0.1"
    }
    write_json(repo/"AUDITORIA_V38_4_45_ISGT_SNAPSHOT.json",audit,indent=2)

    (repo/"VERSION").write_text(FINAL+"\n",encoding="utf-8")

    ch=repo/"CHANGELOG.md"
    if ch.exists():
        c=ch.read_text(encoding="utf-8-sig")
        c+=f"""

## V38.4.45 · ISGT V0.1 · snapshot materializado · {capture_date}

- Materializa fisicamente o ISGT V0.1 em 1.554 hexágonos de 250 km².
- Materializa localmente as fontes territoriais usadas no corte: Terras Indígenas FUNAI, Territórios Quilombolas INCRA, CNUC/MMA e salvaguardas IMASUL/PIN MS.
- Mantém as 518 localidades indígenas e 27 localidades quilombolas IBGE como ocorrências pontuais, sem inferir limites territoriais.
- Uma ocorrência indígena e uma quilombola recebem tratamento equivalente como presença contextual.
- Calcula área de TI e TQ por interseção em projeção LAEA local e cobertura conjunta por união geométrica.
- Usa classificação experimental por regras, sem score numérico e sem pesos.
- O resultado continua explicitamente identificado como proposta metodológica não validada externamente.
- O navegador passa a carregar snapshot local em vez de recalcular o ISGT em sessão.
"""
        ch.write_text(c,encoding="utf-8",newline="\n")

    log("")
    log("PASS · ISGT V0.1 MATERIALIZADO")
    log(f"  snapshot · {isgt_path}")
    log(f"  hexágonos · 1554")
    for k in sorted(class_counts):
        log(f"  {k} · {class_counts[k]}")
    log("")
    for k,m in source_meta.items():
        log(f"  {k} · {m['count']} feições")
    log("")
    log(f"  SHA256 ISGT · {isgt_sha}")
    log("  score numérico · NÃO")
    log("  pesos · NÃO")
    log("  validação externa · PENDENTE")

if __name__=="__main__":
    main()
