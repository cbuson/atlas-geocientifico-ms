#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
VERSION='V38.4.13-ICS-CONHECIMENTO-SUBSOLO-20260814';EXPECTED={'250':1554,'500':793,'1000':412}
def load(p):
    with p.open('r',encoding='utf-8') as f:return json.load(f)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');args=ap.parse_args();r=Path(args.repo).resolve();checks=[]
    def ck(name,ok,detail=''):checks.append({'name':name,'pass':bool(ok),'detail':str(detail)})
    vf=r/'VERSION';ck('version_file',vf.exists());v=vf.read_text(encoding='utf-8').strip() if vf.exists() else '';ck('version_exact',v==VERSION,v)
    req=['docs/indices/ics_v38413_snapshot.json','docs/indices/ics-v38413.js','docs/camadas/arquivos/siagas_pocos_ms.geojson','docs/camadas/arquivos/rimas_pocos_monitoramento_ms.geojson','docs/documentos/metodologia-ics.html','AUDITORIA_V38_4_13_ICS_RUNTIME.json','docs/indices/iod_v3848_snapshot.json','docs/indices/icp_v3849_snapshot.json','docs/indices/igc_v38410_snapshot.json','docs/indices/igq_v38411_snapshot.json','docs/indices/igf_v38412_snapshot.json']
    for rel in req:ck('exists_'+rel,(r/rel).exists())
    sp=r/'docs/indices/ics_v38413_snapshot.json'
    if sp.exists():
        s=load(sp);m=s.get('metadata',{});ck('index_ICS',m.get('index')=='ICS');ck('formula',m.get('formula')=='ICS_h = 100 × (M* × B × Q_log)^(1/3)',m.get('formula'));ck('null_rule','ICS=null' in m.get('null_rule',''));ck('qlog_guardrail','0,75' in m.get('qlog_guardrail',''));ck('not_productivity','produtividade' in m.get('interpretation_limit','').lower())
        for sc,n in EXPECTED.items():
            rows=s.get('grids',{}).get(sc,{});ck(f'grid_{sc}_count',len(rows)==n,len(rows));bad=False
            for hid,row in rows.items():
                if not isinstance(row,list) or len(row)<12:bad=True;break
                val,M,B,Q,nw,meters,dens,occ,sup,profiles,rimas,mean=row
                for x in [M,B,Q]:
                    if x is not None and (not math.isfinite(float(x)) or float(x)<0 or float(x)>1):bad=True
                if val is None:
                    if nw!=0 and meters>0 and Q and B:bad=True
                else:
                    y=float(val);bad=bad or not math.isfinite(y) or y<0 or y>100 or nw<=0 or meters<=0
            ck(f'grid_{sc}_values_valid',not bad);ck(f'grid_{sc}_summary_present',sc in s.get('summary',{}));ck(f'grid_{sc}_normalization_present',sc in s.get('normalization',{}))
        ck('sensitivity_present',all(sc in s.get('sensitivity_spearman',{}) for sc in EXPECTED))
    app=(r/'docs/assets/js/app.js').read_text(encoding='utf-8') if (r/'docs/assets/js/app.js').exists() else ''
    for token in ['ITA_ICS_COLORS','buildIcsSnapshotV38413','ics_snapshot_v38413','ICS_SCALE_LAYERS',"renderer==='index_ics'"]:ck('app_'+token,token in app)
    idx=(r/'docs/index.html').read_text(encoding='utf-8') if (r/'docs/index.html').exists() else '';ck('index_script','./indices/ics-v38413.js?v=38.4.13' in idx)
    sw=(r/'docs/service-worker.js').read_text(encoding='utf-8') if (r/'docs/service-worker.js').exists() else '';ck('sw_cache','ita-arandu-v38-4-13-ics-conhecimento-subsolo' in sw);ck('sw_script','./indices/ics-v38413.js?v=38.4.13' in sw);ck('sw_siagas','./camadas/arquivos/siagas_pocos_ms.geojson' in sw);ck('sw_rimas','./camadas/arquivos/rimas_pocos_monitoramento_ms.geojson' in sw);ck('sw_method','./documentos/metodologia-ics.html' in sw)
    p=r/'docs/camadas/arquivos/siagas_pocos_ms.geojson'
    if p.exists():o=load(p);ck('siagas_fc',o.get('type')=='FeatureCollection');ck('siagas_nonempty',len(o.get('features',[]))>0,len(o.get('features',[])))
    p=r/'docs/camadas/arquivos/rimas_pocos_monitoramento_ms.geojson'
    if p.exists():o=load(p);ck('rimas_fc',o.get('type')=='FeatureCollection');ck('rimas_zero_allowed',len(o.get('features',[]))>=0,len(o.get('features',[])))
    catp=r/'docs/camadas/catalogo-local.json'
    if catp.exists():
        arr=load(catp);by={x.get('id'):x for x in arr if isinstance(x,dict)};ck('local_siagas',by.get('siagas_pocos_ms',{}).get('status')=='incorporada');ck('local_rimas',by.get('rimas_pocos_monitoramento_ms',{}).get('status')=='incorporada')
    mh=r/'docs/documentos/metodologia-ics.html'
    if mh.exists():
        mt=mh.read_text(encoding='utf-8');ck('method_apa7','Referências em APA 7' in mt);ck('method_siagas','SIAGAS' in mt);ck('method_rimas','RIMAS' in mt);ck('method_yin','Yin' in mt);ck('method_guardrail','0,75' in mt);ck('method_rimas_not_log','não é considerada automaticamente um log litológico' in mt.lower());ck('method_litoteca_guardrail','não é imputada' in mt.lower() or 'não são imputados' in mt.lower())
    runtime=r/'AUDITORIA_V38_4_13_ICS_RUNTIME.json'
    if runtime.exists():ro=load(runtime);ck('runtime_pass',ro.get('status')=='PASS');ck('runtime_qlog_guardrail',(ro.get('checks') or {}).get('qlog_profile_ceiling_guardrail') is True);ck('runtime_rimas_not_log',(ro.get('checks') or {}).get('rimas_relation_not_equal_log') is True);ck('runtime_previous',(ro.get('checks') or {}).get('previous_indices_not_recomputed') is True)
    failed=[x for x in checks if not x['pass']];out={'audit':'V38.4.13 ICS final','status':'PASS' if not failed else 'FAIL','checks_total':len(checks),'checks_pass':len(checks)-len(failed),'checks_fail':len(failed),'checks':checks};(r/'AUDITORIA_V38_4_13_ICS_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'AUDITORIA ICS V38.4.13 · {out["status"]} · {out["checks_pass"]}/{out["checks_total"]}')
    if failed:
        for x in failed:print('FAIL ·',x['name'],'·',x['detail'])
        return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
