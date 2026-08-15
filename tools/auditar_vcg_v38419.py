#!/usr/bin/env python3
from pathlib import Path
import argparse,json,math,datetime,hashlib
FINAL='V38.4.19-VCG-VAZIOS-CONHECIMENTO-GEOCIENTIFICO-20260815';SCALES=['250','500','1000']
GRIDS={'250':'docs/camadas/arquivos/malha_r5_250km2.geojson','500':'docs/camadas/arquivos/malha_500km2.geojson','1000':'docs/camadas/arquivos/malha_1000km2.geojson'}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve();rows=[]
 def ck(n,o,d=''):rows.append({'name':n,'pass':bool(o),'detail':d})
 ck('version',(repo/'VERSION').read_text(encoding='utf-8-sig').strip()==FINAL)
 snap=load(repo/'docs/indices/vcg_v38419_snapshot.json');gate=load(repo/'AUDITORIA_V38_4_18_GATE_VCG_FINAL.json');pol=load(repo/'docs/indices/politica-vcg-v38418.json')
 ck('snapshot_version',(snap.get('metadata') or {}).get('version')==FINAL);ck('gate_pass',gate.get('status')=='PASS');ck('policy_pass',pol.get('status')=='PASS')
 meta=snap.get('metadata') or {};ck('null_semantics','null permanece null' in meta.get('null_rule','').lower());ck('not_icg_complement','100' in meta.get('not_icg_complement','') and 'ICG' in meta.get('not_icg_complement',''))
 for rel,h in (snap.get('protected_input_sha256') or {}).items():ck('hash_'+rel,sha(repo/rel)==h,rel)
 for rel,h in (snap.get('protected_grid_sha256') or {}).items():ck('gridhash_'+rel,sha(repo/rel)==h,rel)
 for sc in SCALES:
  ids=[str((f.get('properties') or {}).get('hex_id') or '') for f in load(repo/GRIDS[sc]).get('features',[])];g=(snap.get('grids') or {}).get(sc) or {};sm=(snap.get('summary') or {}).get(sc) or {};se=(snap.get('sensitivity') or {}).get(sc) or {}
  ck(sc+'_alignment',set(g)==set(ids),f'{len(g)}/{len(ids)}');bad=schema=decomp=0;vals=[]
  for hid,r in g.items():
   if not isinstance(r,list) or len(r)!=19:schema+=1;continue
   vcg,med,doc,nobs,nmiss,mask,profile,conf,dom,sec,ide,icg,*base=r
   if nobs+nmiss!=7 or sum(v is not None for v in base)!=nobs:bad+=1
   if not all(finite(x) for x in [vcg,med,doc]) or not (0<=vcg<=100 and 0<=med<=100 and 0<=doc<=100):bad+=1
   if abs(vcg*vcg-med*med-doc*doc)>0.25:decomp+=1
   vals.append(vcg)
  ck(sc+'_schema',schema==0,f'bad={schema}');ck(sc+'_counts',bad==0,f'bad={bad}');ck(sc+'_decomposition',decomp==0,f'bad={decomp}');ck(sc+'_summary_cells',sm.get('cells')==len(ids));ck(sc+'_numeric_all',len(vals)==len(ids));ck(sc+'_sens_075','lambda_0_75' in se);ck(sc+'_sens_05','lambda_0_5' in se)
  for k in ['lambda_0_75','lambda_0_5']:
   rho=(se.get(k) or {}).get('rho_vs_baseline');ck(sc+'_rho_'+k,rho is not None and -1<=float(rho)<=1,rho)
 app=(repo/'docs/assets/js/app.js').read_text(encoding='utf-8-sig');ck('app_color','const ITA_VCG_COLORS=' in app);ck('app_builder','async function buildVcgSnapshotV38419' in app);ck('app_derive',"derive_type==='vcg_snapshot_v38419'" in app);ck('app_scale_group','VCG_SCALE_LAYERS' in app)
 fs0=app.find('function featureStyle(cfg,feat){');fs1=app.find('function pathGeometry',fs0);fs=app[fs0:fs1];ck('renderer',"st.renderer==='index_vcg'" in fs and 'vcgColor(p.vcg_100)' in fs);ck('renderer_not_legend',"if(st.renderer==='index_vcg')return `<div" not in fs)
 lg0=app.find('function layerLegendHtml(cfg){');lg1=app.find('function updateLegend',lg0);lg=app[lg0:lg1 if lg1>lg0 else len(app)];ck('legend',"if(st.renderer==='index_vcg')return" in lg)
 prefix='const CATALOG=';pos=app.find(prefix)+len(prefix);cat,end=json.JSONDecoder().raw_decode(app[pos:]);by={x.get('id'):x for x in cat.get('layers',[]) if isinstance(x,dict)}
 for lid,sc in [('vazios_250','250'),('vazios_500','500'),('vazios_1000','1000')]:
  e=by.get(lid,{});ck('catalog_'+lid,e.get('status')=='incorporada' and e.get('derive_type')=='vcg_snapshot_v38419' and str(e.get('vcg_scale'))==sc,e)
 idx=(repo/'docs/index.html').read_text(encoding='utf-8-sig');ck('index_script','vcg-v38419.js' in idx);sw=(repo/'docs/service-worker.js').read_text(encoding='utf-8-sig');ck('cache','ita-arandu-v38-4-19-vcg-vazios-conhecimento' in sw);ck('methodology',(repo/'docs/documentos/metodologia-vcg.html').exists());ck('PIG_still_not_materialized',not (repo/'docs/indices/pig_v38420_snapshot.json').exists())
 passed=sum(r['pass'] for r in rows);status='PASS' if passed==len(rows) else 'FAIL';out={'audit':'V38.4.19 · VCG · auditoria final','version':FINAL,'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'checks_total':len(rows),'checks_passed':passed,'checks':rows,'next_gate':'PIG permanece bloqueado até definição própria de complexidade geológica e dominância de Pareto'};(repo/'AUDITORIA_V38_4_19_VCG_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'AUDITORIA VCG V38.4.19 - {status} - {passed}/{len(rows)}')
 if status!='PASS':
  for r in rows:
   if not r['pass']:print('FAIL -',r['name'],'-',r['detail'])
 return 0 if status=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
