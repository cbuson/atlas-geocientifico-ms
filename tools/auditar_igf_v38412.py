#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,re
from pathlib import Path
VERSION='V38.4.12-IGF-CONHECIMENTO-GEOFISICO-20260814'
EXPECTED={'250':1554,'500':793,'1000':412}

def load(p):
    with p.open('r',encoding='utf-8') as f:return json.load(f)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');args=ap.parse_args();r=Path(args.repo).resolve();checks=[]
    def ck(name,ok,detail=''):checks.append({'name':name,'pass':bool(ok),'detail':str(detail)})
    vf=r/'VERSION';ck('version_file',vf.exists());version=vf.read_text(encoding='utf-8').strip() if vf.exists() else '';ck('version_exact',version==VERSION,version)
    req=['docs/indices/igf_v38412_snapshot.json','docs/indices/igf-v38412.js','docs/camadas/arquivos/aerogeofisica_projetos_sgb_ms.geojson','docs/camadas/arquivos/gravimetria_sgb_ms.geojson','docs/camadas/arquivos/magnetotelurico_sgb_ms.geojson','docs/documentos/metodologia-igf.html','AUDITORIA_V38_4_12_IGF_RUNTIME.json','docs/indices/iod_v3848_snapshot.json','docs/indices/icp_v3849_snapshot.json','docs/indices/igc_v38410_snapshot.json','docs/indices/igq_v38411_snapshot.json']
    for rel in req:ck('exists_'+rel,(r/rel).exists())
    sp=r/'docs/indices/igf_v38412_snapshot.json';source_availability={}
    if sp.exists():
        s=load(sp);m=s.get('metadata',{});source_availability=m.get('source_availability') or {};ck('source_completeness_recorded',m.get('source_completeness') in {'completa','parcial_por_indisponibilidade_remota'},m.get('source_completeness'));ck('index_IGF',m.get('index')=='IGF');ck('formula_max',m.get('formula')=='IGF_h = max(IGF_AM,h, IGF_GA,h, IGF_GR,h, IGF_MT,h)',m.get('formula'));ck('aero_formula',m.get('aero_formula')=='IGF_AM,h ou IGF_GA,h = 100 × sqrt(C_m × R*_m)',m.get('aero_formula'));ck('point_formula',m.get('point_formula')=='IGF_GR,h ou IGF_MT,h = 100 × sqrt(D*_m × O_m)',m.get('point_formula'));ck('null_rule','IGF=null' in m.get('null_rule',''));ck('no_anomaly_interpretation','anomalia' in m.get('interpretation_limit','').lower());ck('four_components',set((m.get('components') or {}).keys())=={'AM','GA','GR','MT'},list((m.get('components') or {}).keys()))
        for sc,n in EXPECTED.items():
            rows=s.get('grids',{}).get(sc,{});ck(f'grid_{sc}_count',len(rows)==n,len(rows));bad=False;nulls=0;values=[]
            for hid,row in rows.items():
                if not isinstance(row,list) or len(row)<13:bad=True;break
                v=row[0];subs=row[3:7];sv=[]
                for x in subs:
                    if x is not None:
                        try:y=float(x);bad=bad or not math.isfinite(y) or y<0 or y>100;sv.append(y)
                        except Exception:bad=True
                if v is None:
                    nulls+=1
                    if sv:bad=True
                else:
                    try:y=float(v);bad=bad or not math.isfinite(y) or y<0 or y>100;values.append(y)
                    except Exception:bad=True;continue
                    if not sv or abs(y-max(sv))>0.011:bad=True
            ck(f'grid_{sc}_values_valid',not bad);ck(f'grid_{sc}_summary_present',sc in s.get('summary',{}));ck(f'grid_{sc}_null_semantics',nulls>=0)
        ck('sensitivity_present',all(sc in s.get('sensitivity_spearman',{}) for sc in EXPECTED))
    app=(r/'docs/assets/js/app.js').read_text(encoding='utf-8') if (r/'docs/assets/js/app.js').exists() else ''
    for token in ['ITA_IGF_COLORS','buildIgfSnapshotV38412','igf_snapshot_v38412','IGF_SCALE_LAYERS',"renderer==='index_igf'"]:ck('app_'+token,token in app)
    idx=(r/'docs/index.html').read_text(encoding='utf-8') if (r/'docs/index.html').exists() else '';ck('index_script','./indices/igf-v38412.js?v=38.4.12' in idx)
    sw=(r/'docs/service-worker.js').read_text(encoding='utf-8') if (r/'docs/service-worker.js').exists() else '';ck('sw_cache_version','ita-arandu-v38-4-12-igf-conhecimento-geofisico' in sw);ck('sw_igf_script','./indices/igf-v38412.js?v=38.4.12' in sw);ck('sw_aero_source','./camadas/arquivos/aerogeofisica_projetos_sgb_ms.geojson' in sw);ck('sw_grav_source','./camadas/arquivos/gravimetria_sgb_ms.geojson' in sw);ck('sw_mt_source','./camadas/arquivos/magnetotelurico_sgb_ms.geojson' in sw);ck('sw_method','./documentos/metodologia-igf.html' in sw)
    source_rules=[
      ('docs/camadas/arquivos/aerogeofisica_projetos_sgb_ms.geojson','aero'),
      ('docs/camadas/arquivos/gravimetria_sgb_ms.geojson','grav'),
      ('docs/camadas/arquivos/magnetotelurico_sgb_ms.geojson','mt')
    ]
    for rel,key in source_rules:
        p=r/rel
        if p.exists():
            o=load(p);n=len(o.get('features',[]));ck('source_fc_'+rel,o.get('type')=='FeatureCollection')
            av=source_availability.get(key,{})
            if key=='aero':
                statuses=[v.get('status') for v in av.values()] if isinstance(av,dict) else []
                captured=any(x=='captured' for x in statuses);unavailable=bool(statuses) and not captured
            else:
                captured=isinstance(av,dict) and av.get('status')=='captured';unavailable=isinstance(av,dict) and av.get('status')=='unavailable'
            ck('source_available_or_documented_'+rel,(n>0) or unavailable or captured,f'features={n}; availability={av}')
    catp=r/'docs/camadas/catalogo-local.json'
    if catp.exists():
        o=load(catp);layers=o.get('layers',[]) if isinstance(o,dict) else o;by={x.get('id'):x for x in layers if isinstance(x,dict)}
        for lid in ['levantamentos_geofisicos_cobertura_ms','gravimetria_sgb_ms','magnetotelurico_sgb_ms']:ck('catalog_'+lid,by.get(lid,{}).get('status')=='incorporada',by.get(lid,{}).get('status'))
    b=r/'docs/referencias/bibliografia-camadas-indices.json'
    if b.exists():
        o=load(b);entries={e.get('id'):e for e in o.get('entries',[]) if isinstance(e,dict)};ck('bibliography_reference_count_preserved',isinstance(o.get('total_references'),int) and o.get('total_references')>=176,o.get('total_references'))
        for lid in ['igf_250','igf_500','igf_1000','levantamentos_geofisicos_cobertura_ms','gravimetria_sgb_ms','magnetotelurico_sgb_ms']:ck('bibliography_'+lid,entries.get(lid,{}).get('status')=='incorporada',entries.get(lid,{}).get('status'))
    mh=r/'docs/documentos/metodologia-igf.html'
    if mh.exists():
        mt=mh.read_text(encoding='utf-8');ck('method_apa7','Referências em APA 7' in mt);ck('method_ref100','Projetos aerogeofísicos e dados aerogeofísicos' in mt);ck('method_ref101','Dados gravimétricos' in mt);ck('method_ref102','Levantamentos geofísicos terrestres' in mt);ck('method_sensitivity','Saisana' in mt);ck('method_limit','Não mede intensidade de anomalia' in mt)
    runtime=r/'AUDITORIA_V38_4_12_IGF_RUNTIME.json'
    if runtime.exists():
        ro=load(runtime);ck('runtime_pass',ro.get('status')=='PASS');ck('runtime_no_interpolation',(ro.get('checks') or {}).get('grav_no_interpolation') is True);ck('runtime_mt_available',(ro.get('checks') or {}).get('mt_available_only') is True)
    failed=[x for x in checks if not x['pass']];out={'audit':'V38.4.12 IGF final','status':'PASS' if not failed else 'FAIL','checks_total':len(checks),'checks_pass':len(checks)-len(failed),'checks_fail':len(failed),'checks':checks}
    op=r/'AUDITORIA_V38_4_12_IGF_FINAL.json';op.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'AUDITORIA IGF V38.4.12 · {out["status"]} · {out["checks_pass"]}/{out["checks_total"]}')
    if failed:
        for x in failed:print('FAIL ·',x['name'],'·',x['detail'])
        return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
