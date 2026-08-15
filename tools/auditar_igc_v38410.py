#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
EXPECTED_VERSION='V38.4.10-IGC-CONTROLE-GEOCRONOLOGICO-20260814'
EXPECTED_GRID_COUNTS={'250':1554,'500':793,'1000':412}
REFS=['REF-002','REF-082','REF-085','REF-105','REF-108','REF-115']

def load_json(p):
    with open(p,encoding='utf-8') as f:return json.load(f)
def check(cond,msg,checks):
    checks.append({'check':msg,'pass':bool(cond)})
    if not cond:print('FAIL ·',msg)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');args=ap.parse_args();repo=Path(args.repo).resolve();checks=[]
    version=(repo/'VERSION').read_text(encoding='utf-8').strip() if (repo/'VERSION').exists() else ''
    check(version==EXPECTED_VERSION,'VERSION V38.4.10 correta',checks)
    files=['docs/indices/igc_v38410_snapshot.json','docs/indices/igc-v38410.js','docs/camadas/arquivos/geocronologia_geosgb_ms.geojson','docs/documentos/metodologia-igc.html','AUDITORIA_V38_4_10_IGC_RUNTIME.json','docs/indices/iod-v3848.js','docs/indices/iod_v3848_snapshot.json','docs/indices/icp-v3849.js','docs/indices/icp_v3849_snapshot.json','docs/camadas/arquivos/afloramentos_geosgb_ms.geojson','docs/camadas/arquivos/petrografia_geosgb_ms.geojson']
    for f in files:check((repo/f).exists(),f'arquivo presente · {f}',checks)
    if not all((repo/f).exists() for f in files[:5]):return 2
    snap=load_json(repo/'docs/indices/igc_v38410_snapshot.json');src=load_json(repo/'docs/camadas/arquivos/geocronologia_geosgb_ms.geojson');runtime=load_json(repo/'AUDITORIA_V38_4_10_IGC_RUNTIME.json');meta=snap.get('metadata',{})
    check(meta.get('index')=='IGC','snapshot identifica IGC',checks)
    check(meta.get('formula')=='IGC_h = 100 × (G × U_age × Q_age)^(1/3)','fórmula IGC congelada',checks)
    check(meta.get('g_formula')=='G = sqrt(D* × O)','fórmula G congelada',checks)
    check(meta.get('microcell_m')==5000.0,'micromalha G basal 5 km',checks)
    check(meta.get('density_percentile')==95,'normalização D* por P95',checks)
    check('9 × 9' in str(meta.get('u_support','')),'suporte U_age basal 9 × 9 documentado',checks)
    check('Não é nota' in str(meta.get('quality_rule','')) or 'não é nota' in str(meta.get('quality_rule','')).lower(),'Q_age explicitamente não é qualidade analítica',checks)
    check('método' in str(meta.get('direct_rule','')).lower() and 'idade' in str(meta.get('direct_rule','')).lower(),'regra mínima de datação direta por método + idade documentada',checks)
    check('material' in str(meta.get('quality_rule','')).lower(),'material analisado preservado como bloco de Q_age',checks)
    feats=src.get('features',[]);check(len(feats)>0,'snapshot Geocronologia contém registros diretos utilizáveis',checks)
    check(all((f.get('properties') or {}).get('__atlas_chave_independente') for f in feats),'todos os registros locais têm chave independente',checks)
    check(all('__atlas_q_age' in (f.get('properties') or {}) for f in feats),'todos os registros locais têm Q_age',checks)
    check(all((f.get('properties') or {}).get('__atlas_idade_ma') is not None for f in feats),'todos os registros locais têm idade direta selecionada',checks)
    for scale,count in EXPECTED_GRID_COUNTS.items():
        rows=snap.get('grids',{}).get(scale,{})
        check(len(rows)==count,f'IGC {scale} · {count} células',checks)
        good=True;null_good=True;comp_good=True;core_good=True
        for row in rows.values():
            if not isinstance(row,list) or len(row)<16:good=False;break
            igc,G,U,Q,D,O,n=row[:7]
            if igc is not None and not (0<=igc<=100):good=False
            if n==0 and igc is not None:null_good=False
            for v in (G,U,Q,D,O):
                if v is not None and not (0<=v<=1):comp_good=False
            if n>0 and Q is not None and Q<0.4-1e-9:core_good=False
        check(good,f'IGC {scale} · estrutura e faixa 0–100 válidas',checks)
        check(null_good,f'IGC {scale} · ausência de datação direta permanece null',checks)
        check(comp_good,f'IGC {scale} · componentes G U_age Q_age D O em 0–1',checks)
        check(core_good,f'IGC {scale} · Q_age mínimo compatível com método + idade sem imputar material',checks)
    app=(repo/'docs/assets/js/app.js').read_text(encoding='utf-8');idx=(repo/'docs/index.html').read_text(encoding='utf-8');sw=(repo/'docs/service-worker.js').read_text(encoding='utf-8');local=(repo/'docs/camadas/catalogo-local.js').read_text(encoding='utf-8');method=(repo/'docs/documentos/metodologia-igc.html').read_text(encoding='utf-8');biblio=(repo/'docs/referencias/index.html').read_text(encoding='utf-8')
    check("renderer==='index_igc'" in app,'renderer IGC ativo',checks)
    check('buildIgcSnapshotV38410' in app,'builder IGC ativo',checks)
    check("const IGC_SCALE_LAYERS=['igc_250','igc_500','igc_1000']" in app,'exclusividade entre escalas IGC',checks)
    check("derive_type==='igc_snapshot_v38410'" in app,'derive IGC ativo',checks)
    check('./indices/igc-v38410.js?v=38.4.10' in idx,'snapshot IGC carregado pelo index',checks)
    check('igc-v38410.js?v=38.4.10' in sw,'PWA inclui snapshot IGC',checks)
    check('geocronologia_geosgb_ms.geojson' in sw,'PWA inclui snapshot geocronológico',checks)
    check('metodologia-igc.html' in sw and 'metodologia-igc.html' in (repo/'docs/documentos/index.html').read_text(encoding='utf-8'),'metodologia IGC integrada',checks)
    check('geocronologia_geosgb_ms.geojson' in local,'Geocronologia registrada como camada local',checks)
    for rid in REFS:check(rid in method and rid in biblio,f'referência IGC disponível e citada · {rid}',checks)
    check(runtime.get('status')=='PASS','auditoria runtime PASS',checks)
    check(runtime.get('checks',{}).get('independent_scale_calculation') is True,'runtime confirma cálculo independente por escala',checks)
    check(runtime.get('checks',{}).get('direct_age_requires_method_and_age') is True,'runtime confirma critério de datação direta por método + idade',checks)
    check(runtime.get('checks',{}).get('missing_material_penalizes_q_age_without_being_imputed') is True,'runtime confirma ausência de material como penalização documental sem imputação',checks)
    check(runtime.get('checks',{}).get('q_age_is_documentary_completeness_not_accuracy') is True,'runtime confirma significado de Q_age',checks)
    check(runtime.get('checks',{}).get('previous_indices_not_recomputed') is True,'runtime declara preservação de IOD e ICP',checks)
    ok=all(c['pass'] for c in checks)
    out={'audit':'V38.4.10 IGC final','status':'PASS' if ok else 'FAIL','checks_total':len(checks),'checks_passed':sum(c['pass'] for c in checks),'checks':checks}
    (repo/'AUDITORIA_V38_4_10_IGC_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'AUDITORIA IGC V38.4.10 · {out["status"]} · {out["checks_passed"]}/{out["checks_total"]}')
    return 0 if ok else 3
if __name__=='__main__':raise SystemExit(main())
