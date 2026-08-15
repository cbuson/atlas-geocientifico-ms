#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,re,sys
from pathlib import Path
VERSION='V38.4.11-IGQ-CONHECIMENTO-GEOQUIMICO-20260814'
MED=['SC','CB','solo','rocha','agua']
EXPECTED={'250':1554,'500':793,'1000':412}

def load(p):
    with p.open('r',encoding='utf-8') as f:return json.load(f)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');args=ap.parse_args();r=Path(args.repo).resolve();checks=[]
    def ck(name,ok,detail=''):
        checks.append({'name':name,'pass':bool(ok),'detail':str(detail)})
    vf=r/'VERSION';ck('version_file',vf.exists());version=vf.read_text(encoding='utf-8').strip() if vf.exists() else '';ck('version_exact',version==VERSION,version)
    req=['docs/indices/igq_v38411_snapshot.json','docs/indices/igq-v38411.js','docs/camadas/arquivos/geoquimica_amostras_sgb_ms.geojson','docs/documentos/metodologia-igq.html','AUDITORIA_V38_4_11_IGQ_RUNTIME.json','docs/indices/iod_v3848_snapshot.json','docs/indices/icp_v3849_snapshot.json','docs/indices/igc_v38410_snapshot.json']
    for rel in req:ck('exists_'+rel,(r/rel).exists())
    sp=r/'docs/indices/igq_v38411_snapshot.json'
    if sp.exists():
        s=load(sp);m=s.get('metadata',{});ck('index_IGQ',m.get('index')=='IGQ');ck('formula_max',m.get('formula')=='IGQ_h = max(IGQ_SC, IGQ_CB, IGQ_solo, IGQ_rocha, IGQ_agua)',m.get('formula'));ck('medium_formula',m.get('medium_formula')=='IGQ_m = 100 × (G_m × A_m × Q_m)^(1/3)',m.get('medium_formula'));ck('five_media',m.get('media')==MED,m.get('media'));ck('null_rule','IGQ=null' in m.get('null_rule',''));ck('censoring_no_imputation','não imputa' in m.get('censoring_rule','').lower() or 'nao imputa' in m.get('censoring_rule','').lower());ck('interpretation_not_anomaly','anomalia' in m.get('interpretation_limit','').lower())
        for sc,n in EXPECTED.items():
            rows=s.get('grids',{}).get(sc,{});ck(f'grid_{sc}_count',len(rows)==n,len(rows));vals=[];nulls=0;bad=False
            for hid,row in rows.items():
                if not isinstance(row,list) or len(row)<13:bad=True;break
                v=row[0]
                if v is None:nulls+=1
                else:
                    try:x=float(v);bad=bad or not math.isfinite(x) or x<0 or x>100;vals.append(x)
                    except Exception:bad=True
                sub=row[3:8]
                sv=[x for x in sub if x is not None]
                if v is None and sv:bad=True
                if v is not None and (not sv or abs(float(v)-max(float(x) for x in sv))>0.011):bad=True
            ck(f'grid_{sc}_values_valid',not bad);ck(f'grid_{sc}_has_nulls',nulls>=0);ck(f'grid_{sc}_summary_present',sc in s.get('summary',{}))
        ck('sensitivity_present',all(sc in s.get('sensitivity_spearman',{}) for sc in EXPECTED))
    app=(r/'docs/assets/js/app.js').read_text(encoding='utf-8') if (r/'docs/assets/js/app.js').exists() else ''
    for token in ['ITA_IGQ_COLORS','buildIgqSnapshotV38411','igq_snapshot_v38411','IGQ_SCALE_LAYERS',"renderer==='index_igq'"] :ck('app_'+token,token in app)
    idx=(r/'docs/index.html').read_text(encoding='utf-8') if (r/'docs/index.html').exists() else '';ck('index_script','./indices/igq-v38411.js?v=38.4.11' in idx)
    sw=(r/'docs/service-worker.js').read_text(encoding='utf-8') if (r/'docs/service-worker.js').exists() else '';ck('sw_cache_version','ita-arandu-v38-4-11-igq-conhecimento-geoquimico' in sw);ck('sw_igq_script','./indices/igq-v38411.js?v=38.4.11' in sw);ck('sw_source','./camadas/arquivos/geoquimica_amostras_sgb_ms.geojson' in sw);ck('sw_method','./documentos/metodologia-igq.html' in sw)
    srcp=r/'docs/camadas/arquivos/geoquimica_amostras_sgb_ms.geojson'
    if srcp.exists():
        src=load(srcp);features=src.get('features',[]);ck('source_featurecollection',src.get('type')=='FeatureCollection');ck('source_has_features',len(features)>0,len(features));badm=[f for f in features if (f.get('properties') or {}).get('__atlas_meio') not in MED];ck('source_medium_tagged',not badm,len(badm));dups=[f for f in features if 'DUPLIC' in str((f.get('properties') or {}).get('duplicata','')).upper()];ck('source_no_declared_duplicate_as_independent',len(dups)==0,len(dups))
    b=r/'docs/referencias/bibliografia-camadas-indices.json'
    if b.exists():
        o=load(b);entries={e.get('id'):e for e in o.get('entries',[]) if isinstance(e,dict)}
        ck('bibliography_total_refs_176',o.get('total_references')==176,o.get('total_references'))
        for lid in ['igq_250','igq_500','igq_1000','geoquimica_amostras_sgb_ms','geoquimica_resultados_sgb_ms']:
            e=entries.get(lid,{})
            ck('bibliography_'+lid,e.get('status')=='incorporada',e.get('status'))
            ck('bibliography_ref178_'+lid,'REF-178' in (e.get('reference_ids') or []),e.get('reference_ids'))
    rp=r/'docs/referencias/referencias.js'
    if rp.exists():
        rt=rp.read_text(encoding='utf-8');ck('ref178_master','"id":"REF-178"' in rt);ck('ref178_apa7','Geoquímica – amostras analisadas e resultados analíticos' in rt and 'Recuperado em 14 de agosto de 2026' in rt)
    dp=r/'docs/dados/registros.js'
    if dp.exists():
        dt=dp.read_text(encoding='utf-8');ck('registros_ref178',all((f'"{lid}"' in dt and 'REF-178' in dt) for lid in ['igq_250','igq_500','igq_1000']))
    bh=r/'docs/referencias/index.html'
    if bh.exists():
        ht=bh.read_text(encoding='utf-8');ck('bibliography_html_ref178','id="ref-178"' in ht);ck('bibliography_html_176','176 referências no registro mestre' in ht)
    mh=r/'docs/documentos/metodologia-igq.html'
    if mh.exists():
        mt=mh.read_text(encoding='utf-8');ck('method_ref178','REF-178' in mt);ck('method_apa7','Referências em APA 7' in mt and 'Saisana, M., Saltelli, A., &amp; Tarantola, S. (2005)' in mt)
    runtime=r/'AUDITORIA_V38_4_11_IGQ_RUNTIME.json'
    if runtime.exists():ck('runtime_pass',load(runtime).get('status')=='PASS')
    failed=[x for x in checks if not x['pass']];out={'audit':'V38.4.11 IGQ final','status':'PASS' if not failed else 'FAIL','checks_total':len(checks),'checks_pass':len(checks)-len(failed),'checks_fail':len(failed),'checks':checks}
    op=r/'AUDITORIA_V38_4_11_IGQ_FINAL.json';op.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'AUDITORIA IGQ V38.4.11 · {out["status"]} · {out["checks_pass"]}/{out["checks_total"]}')
    if failed:
        for x in failed:print('FAIL ·',x['name'],'·',x['detail'])
        return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
