#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

EXPECTED_VERSION='V38.4.8-IOD-OBSERVACAO-DIRETA-20260814'
EXPECTED_GRID_COUNTS={'250':1554,'500':793,'1000':412}

def load_json(p):
    with open(p,encoding='utf-8') as f:return json.load(f)

def check(cond,msg,checks):
    checks.append({'check':msg,'pass':bool(cond)})
    if not cond: print('FAIL ·',msg)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');args=ap.parse_args()
    repo=Path(args.repo).resolve(); checks=[]
    version=(repo/'VERSION').read_text(encoding='utf-8').strip() if (repo/'VERSION').exists() else ''
    check(version==EXPECTED_VERSION,'VERSION V38.4.8 correta',checks)
    files=['docs/indices/iod_v3848_snapshot.json','docs/indices/iod-v3848.js','docs/camadas/arquivos/afloramentos_geosgb_ms.geojson','docs/documentos/metodologia-iod.html','AUDITORIA_V38_4_8_IOD_RUNTIME.json']
    for f in files: check((repo/f).exists(),f'arquivo presente · {f}',checks)
    if not all((repo/f).exists() for f in files[:3]):
        return 2
    snap=load_json(repo/'docs/indices/iod_v3848_snapshot.json')
    src=load_json(repo/'docs/camadas/arquivos/afloramentos_geosgb_ms.geojson')
    runtime=load_json(repo/'AUDITORIA_V38_4_8_IOD_RUNTIME.json') if (repo/'AUDITORIA_V38_4_8_IOD_RUNTIME.json').exists() else {}
    check(snap.get('metadata',{}).get('index')=='IOD','snapshot identifica IOD',checks)
    check(snap.get('metadata',{}).get('formula')=='IOD_h = 100 × (D* × O × E)^(1/3)','fórmula congelada',checks)
    check(snap.get('metadata',{}).get('microcell_m')==5000.0,'micromalha basal 5 km',checks)
    check(snap.get('metadata',{}).get('density_percentile')==95,'normalização D* por P95',checks)
    check(len(src.get('features',[]))>0,'snapshot AFLO contém observações',checks)
    ids=[]
    for f in src.get('features',[]):
        p=f.get('properties') or {}; v=p.get('ID_AFLORAMENTO')
        if v not in (None,''): ids.append(str(v))
    check(len(ids)==len(set(ids)),'ID_AFLORAMENTO sem duplicação após materialização',checks)
    for scale,count in EXPECTED_GRID_COUNTS.items():
        rows=snap.get('grids',{}).get(scale,{})
        check(len(rows)==count,f'IOD {scale} · {count} células',checks)
        good=True; null_good=True
        for row in rows.values():
            if not isinstance(row,list) or len(row)<9: good=False;break
            iod,D,O,E,n=row[:5]
            if iod is not None and not (0<=iod<=100):good=False
            if n==0 and iod is not None:null_good=False
        check(good,f'IOD {scale} · estrutura e faixa 0–100 válidas',checks)
        check(null_good,f'IOD {scale} · ausência de observação permanece null',checks)
    app=(repo/'docs/assets/js/app.js').read_text(encoding='utf-8')
    idx=(repo/'docs/index.html').read_text(encoding='utf-8')
    sw=(repo/'docs/service-worker.js').read_text(encoding='utf-8')
    check("renderer==='index_iod'" in app,'renderer IOD ativo',checks)
    check('buildIodSnapshotV3848' in app,'builder IOD ativo',checks)
    check("const IOD_SCALE_LAYERS=['iod_250','iod_500','iod_1000']" in app,'exclusividade entre escalas IOD',checks)
    check('./indices/iod-v3848.js?v=38.4.8' in idx,'snapshot IOD carregado pelo index',checks)
    check('metodologia-iod.html' in idx,'metodologia IOD vinculada na interface',checks)
    check('iod-v3848.js?v=38.4.8' in sw,'PWA inclui snapshot IOD',checks)
    check('afloramentos_geosgb_ms.geojson' in (repo/'docs/camadas/catalogo-local.js').read_text(encoding='utf-8'),'AFLO registrado como camada local',checks)
    refs=(repo/'docs/dados/registros.js').read_text(encoding='utf-8')
    for rid in ['REF-083','REF-105','REF-106','REF-111','REF-112','REF-113']:
        check(rid in refs,f'referência disponível · {rid}',checks)
    check(runtime.get('status')=='PASS','auditoria runtime PASS',checks)
    ok=all(c['pass'] for c in checks)
    out={'audit':'V38.4.8 IOD final','status':'PASS' if ok else 'FAIL','checks_total':len(checks),'checks_passed':sum(c['pass'] for c in checks),'checks':checks}
    (repo/'AUDITORIA_V38_4_8_IOD_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'AUDITORIA IOD V38.4.8 · {out["status"]} · {out["checks_passed"]}/{out["checks_total"]}')
    return 0 if ok else 3

if __name__=='__main__': raise SystemExit(main())
