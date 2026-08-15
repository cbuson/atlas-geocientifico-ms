#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
EXPECTED_VERSION='V38.4.9-ICP-CARACTERIZACAO-PETROGRAFICA-20260814'
EXPECTED_GRID_COUNTS={'250':1554,'500':793,'1000':412}
REFS=['REF-002','REF-059','REF-082','REF-084','REF-105','REF-106','REF-115','REF-174']

def load_json(p):
    with open(p,encoding='utf-8') as f:return json.load(f)
def check(cond,msg,checks):
    checks.append({'check':msg,'pass':bool(cond)})
    if not cond:print('FAIL ·',msg)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');args=ap.parse_args();repo=Path(args.repo).resolve();checks=[]
    version=(repo/'VERSION').read_text(encoding='utf-8').strip() if (repo/'VERSION').exists() else ''
    check(version==EXPECTED_VERSION,'VERSION V38.4.9 correta',checks)
    files=['docs/indices/icp_v3849_snapshot.json','docs/indices/icp-v3849.js','docs/camadas/arquivos/petrografia_geosgb_ms.geojson','docs/documentos/metodologia-icp.html','AUDITORIA_V38_4_9_ICP_RUNTIME.json','docs/indices/iod-v3848.js','docs/indices/iod_v3848_snapshot.json','docs/camadas/arquivos/afloramentos_geosgb_ms.geojson']
    for f in files:check((repo/f).exists(),f'arquivo presente · {f}',checks)
    if not all((repo/f).exists() for f in files[:5]):return 2
    snap=load_json(repo/'docs/indices/icp_v3849_snapshot.json');src=load_json(repo/'docs/camadas/arquivos/petrografia_geosgb_ms.geojson');runtime=load_json(repo/'AUDITORIA_V38_4_9_ICP_RUNTIME.json')
    meta=snap.get('metadata',{})
    check(meta.get('index')=='ICP','snapshot identifica ICP',checks)
    check(meta.get('formula')=='ICP_h = 100 × (P × U × Q)^(1/3)','fórmula ICP congelada',checks)
    check(meta.get('p_formula')=='P = sqrt(D* × O)','fórmula P congelada',checks)
    check(meta.get('microcell_m')==5000.0,'micromalha P basal 5 km',checks)
    check(meta.get('density_percentile')==95,'normalização D* por P95',checks)
    check('9 × 9' in str(meta.get('u_support','')),'suporte U basal 9 × 9 documentado',checks)
    check('Não é nota' in str(meta.get('quality_rule','')) or 'Não é' in str(meta.get('quality_rule','')),'Q explicitamente não é qualidade laboratorial',checks)
    feats=src.get('features',[]);check(len(feats)>0,'snapshot Petrografia contém registros',checks)
    keys=[(f.get('properties') or {}).get('__atlas_chave_independente') for f in feats]
    check(all(keys),'todos os registros têm chave de agrupamento independente',checks)
    check(all('__atlas_q_grupo' in (f.get('properties') or {}) for f in feats),'todos os registros têm Q de grupo documentado',checks)
    for scale,count in EXPECTED_GRID_COUNTS.items():
        rows=snap.get('grids',{}).get(scale,{})
        check(len(rows)==count,f'ICP {scale} · {count} células',checks)
        good=True;null_good=True;comp_good=True
        for row in rows.values():
            if not isinstance(row,list) or len(row)<13:good=False;break
            icp,P,U,Q,D,O,n=row[:7]
            if icp is not None and not (0<=icp<=100):good=False
            if n==0 and icp is not None:null_good=False
            for v in (P,U,Q,D,O):
                if v is not None and not (0<=v<=1):comp_good=False
        check(good,f'ICP {scale} · estrutura e faixa 0–100 válidas',checks)
        check(null_good,f'ICP {scale} · ausência de petrografia permanece null',checks)
        check(comp_good,f'ICP {scale} · componentes P U Q D O em 0–1',checks)
    app=(repo/'docs/assets/js/app.js').read_text(encoding='utf-8');idx=(repo/'docs/index.html').read_text(encoding='utf-8');sw=(repo/'docs/service-worker.js').read_text(encoding='utf-8');local=(repo/'docs/camadas/catalogo-local.js').read_text(encoding='utf-8');refs=(repo/'docs/dados/registros.js').read_text(encoding='utf-8');method=(repo/'docs/documentos/metodologia-icp.html').read_text(encoding='utf-8')
    check("renderer==='index_icp'" in app,'renderer ICP ativo',checks)
    check('buildIcpSnapshotV3849' in app,'builder ICP ativo',checks)
    check("const ICP_SCALE_LAYERS=['icp_250','icp_500','icp_1000']" in app,'exclusividade entre escalas ICP',checks)
    check("derive_type==='icp_snapshot_v3849'" in app,'derive ICP ativo',checks)
    check('./indices/icp-v3849.js?v=38.4.9' in idx,'snapshot ICP carregado pelo index',checks)
    check('metodologia-icp.html' in idx,'metodologia ICP vinculada na interface',checks)
    check('icp-v3849.js?v=38.4.9' in sw,'PWA inclui snapshot ICP',checks)
    check('petrografia_geosgb_ms.geojson' in sw,'PWA inclui snapshot petrográfico',checks)
    check('petrografia_geosgb_ms.geojson' in local,'Petrografia registrada como camada local',checks)
    for rid in REFS:check(rid in refs and rid in method,f'referência ICP disponível e citada · {rid}',checks)
    check(runtime.get('status')=='PASS','auditoria runtime PASS',checks)
    check(runtime.get('checks',{}).get('independent_scale_calculation') is True,'runtime confirma cálculo independente por escala',checks)
    check(runtime.get('checks',{}).get('q_is_metadata_completeness_not_lab_quality') is True,'runtime confirma significado de Q',checks)
    ok=all(c['pass'] for c in checks)
    out={'audit':'V38.4.9 ICP final','status':'PASS' if ok else 'FAIL','checks_total':len(checks),'checks_passed':sum(c['pass'] for c in checks),'checks':checks}
    (repo/'AUDITORIA_V38_4_9_ICP_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'AUDITORIA ICP V38.4.9 · {out["status"]} · {out["checks_passed"]}/{out["checks_total"]}')
    return 0 if ok else 3
if __name__=='__main__':raise SystemExit(main())
