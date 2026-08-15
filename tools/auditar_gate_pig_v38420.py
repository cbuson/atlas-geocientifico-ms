#!/usr/bin/env python3
from pathlib import Path
import argparse,json,hashlib,sys
EXPECTED='V38.4.20-GATE-PIG-20260815'
PROTECTED=[
 'docs/indices/imc_v32_snapshot.json','docs/indices/iod_v3848_snapshot.json','docs/indices/icp_v3849_snapshot.json','docs/indices/igc_v38410_snapshot.json','docs/indices/igq_v38411_snapshot.json','docs/indices/igf_v38412_snapshot.json','docs/indices/ics_v38413_snapshot.json','docs/indices/ide_v38415_snapshot.json','docs/indices/icg_v38417_snapshot.json','docs/indices/vcg_v38419_snapshot.json',
 'docs/camadas/arquivos/malha_r5_250km2.geojson','docs/camadas/arquivos/malha_500km2.geojson','docs/camadas/arquivos/malha_1000km2.geojson','docs/camadas/arquivos/mapa_geologico_ms.geojson']
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--before',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
 raw_before=load(a.before)
 before={str(k).replace('\\\\','/').replace('\\','/'):str(v).lower() for k,v in raw_before.items()}
 checks=[]
 def ck(name,ok,detail=''):checks.append({'name':name,'pass':bool(ok),'detail':detail})
 ck('version',(repo/'VERSION').read_text(encoding='utf-8-sig').strip()==EXPECTED)
 policy=load(repo/'docs/indices/politica-pig-v38420.json');runtime=load(repo/'AUDITORIA_V38_4_20_GATE_PIG_RUNTIME.json')
 ck('policy_pass',policy.get('status')=='PASS');ck('runtime_pass',runtime.get('status')=='PASS')
 ck('pareto_no_weighted_sum','soma ponderada' in json.dumps(policy,ensure_ascii=False).lower() and policy.get('pareto',{}).get('dominance'))
 ck('pig_not_materialized',not (repo/'docs/indices/pig_v38421_snapshot.json').exists())
 ck('independence','Nao usa IOD' in policy.get('independence','') or 'Não usa IOD' in policy.get('independence',''))
 ck('complexity_formula',policy.get('complexity_baseline',{}).get('formula')=='C_geo = 100 * sqrt(D* * T*).')
 ck('display_ordinal','ordinal' in policy.get('pareto',{}).get('display_100',''))
 ck('references',set(['REF-002','REF-004','REF-082','REF-105','REF-115','REF-116']).issubset(set(policy.get('references',[]))))
 for sc in ['250','500','1000']:
  d=policy.get('diagnostic',{}).get(sc,{})
  ck('diag_'+sc,d.get('cells',0)>0 and d.get('vcg_complete_for_grid') is True)
  ck('vcg_complete_'+sc,d.get('vcg_numeric_cells')==d.get('cells'),str(d.get('vcg_numeric_cells'))+'/'+str(d.get('cells')))
  s=policy.get('sensitivity_diagnostic',{}).get(sc,{})
  ck('sensitivity_'+sc,s.get('status')=='OBRIGATORIA_NA_V38.4.21' and s.get('microgrids_km')==[1.25,2.5,5.0] and s.get('normalization_percentiles')==[90,95,99])
 for rel in PROTECTED:
  p=repo/rel;ck('exists_'+rel,p.exists())
  if p.exists():ck('sha_'+rel,sha(p)==before.get(rel),sha(p))
 status='PASS' if all(c['pass'] for c in checks) else 'FAIL'
 out={'audit':'V38.4.20 Gate PIG final','status':status,'version':EXPECTED,'checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks)}
 (repo/'AUDITORIA_V38_4_20_GATE_PIG_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(f"AUDITORIA GATE PIG V38.4.20 · {status} · {out['passed']}/{out['total']}")
 if status!='PASS':
  for c in checks:
   if not c['pass']:print('FAIL',c['name'],c['detail'])
  return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
