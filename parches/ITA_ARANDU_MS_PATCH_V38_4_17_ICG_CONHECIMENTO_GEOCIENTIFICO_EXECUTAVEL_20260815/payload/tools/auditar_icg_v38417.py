#!/usr/bin/env python3
from pathlib import Path
import argparse,json,math,datetime,hashlib
FINAL='V38.4.17-ICG-CONHECIMENTO-GEOCIENTIFICO-20260815'
SCALES=['250','500','1000'];POLICY='docs/indices/politica-icg-v38416.json'
GRIDS={'250':'docs/camadas/arquivos/malha_r5_250km2.geojson','500':'docs/camadas/arquivos/malha_500km2.geojson','1000':'docs/camadas/arquivos/malha_1000km2.geojson'}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def check(rows,name,ok,detail=''):rows.append({'name':name,'pass':bool(ok),'detail':detail})
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve();rows=[]
 check(rows,'version',(repo/'VERSION').read_text(encoding='utf-8-sig').strip()==FINAL,'')
 snap=load(repo/'docs/indices/icg_v38417_snapshot.json');policy=load(repo/POLICY);gate=load(repo/'AUDITORIA_V38_4_16_GATE_ICG_FINAL.json')
 check(rows,'snapshot_version',(snap.get('metadata') or {}).get('version')==FINAL,'');check(rows,'gate_pass',gate.get('status')=='PASS','');check(rows,'policy_pass',policy.get('status')=='PASS','');check(rows,'eligibility_policy',(snap.get('metadata') or {}).get('eligibility')=='n_obs >= 2','');check(rows,'ide_outside_formula','IDE é indicador companheiro' in (snap.get('metadata') or {}).get('ide_rule',''),'')
 for rel,h in (snap.get('protected_base_sha256') or {}).items():check(rows,'hash_'+rel,sha(repo/rel)==h,rel)
 for rel,h in (snap.get('protected_grid_sha256') or {}).items():check(rows,'gridhash_'+rel,sha(repo/rel)==h,rel)
 for sc in SCALES:
  grid=load(repo/GRIDS[sc]);ids=[str((f.get('properties') or {}).get('hex_id') or '') for f in grid.get('features',[])];g=(snap.get('grids') or {}).get(sc) or {};sm=(snap.get('summary') or {}).get(sc) or {};sens=(snap.get('sensitivity') or {}).get(sc) or {};check(rows,sc+'_grid_alignment',set(g)==set(ids),f'{len(g)}/{len(ids)}')
  bad=capbad=nullbad=schemabad=eligible=0;vals=[]
  for hid,r in g.items():
   if not isinstance(r,list) or len(r)!=15:schemabad+=1;continue
   icg,m100,mu,var,nobs,frac,mask,ide,*base=r;obs=sum(v is not None for v in base)
   if obs!=nobs:bad+=1
   if nobs<2:
    if icg is not None:nullbad+=1
   else:
    eligible+=1
    if not finite(icg) or float(icg)<-1e-9 or float(icg)>100+1e-9:bad+=1
    else:
     vals.append(float(icg));cap=100*nobs/7
     if float(icg)>cap+0.011:capbad+=1
    if not finite(mu) or not finite(var) or not finite(m100):bad+=1
  check(rows,sc+'_row_schema',schemabad==0,f'bad={schemabad}');check(rows,sc+'_nobs_matches_base',bad==0,f'bad={bad}');check(rows,sc+'_null_for_nobs_lt2',nullbad==0,f'bad={nullbad}');check(rows,sc+'_theoretical_cap',capbad==0,f'bad={capbad}')
  exp=int(((policy.get('diagnostic_current_cut') or {}).get(sc) or {}).get('cells_eligible_n_obs_ge_2',-1));check(rows,sc+'_eligible_matches_gate',eligible==exp,f'{eligible}/{exp}');check(rows,sc+'_summary_count',sm.get('cells_with_icg')==eligible,f"{sm.get('cells_with_icg')}/{eligible}");check(rows,sc+'_has_numeric_values',len(vals)>0,len(vals))
  for key in ['alpha_0_5','alpha_1','alpha_2']:check(rows,sc+'_sensitivity_'+key,key in sens,sens.get(key))
  for key in ['alpha_0_5','alpha_2']:
   rho=(sens.get(key) or {}).get('rho_vs_baseline');check(rows,sc+'_rho_'+key,rho is not None and -1<=float(rho)<=1,rho)
 app=(repo/'docs/assets/js/app.js').read_text(encoding='utf-8-sig');check(rows,'app_color','const ITA_ICG_COLORS=' in app,'');check(rows,'app_builder','async function buildIcgSnapshotV38417' in app,'');check(rows,'app_derive',"derive_type==='icg_snapshot_v38417'" in app,'');check(rows,'app_scale_group','ICG_SCALE_LAYERS' in app,'')
 fs0=app.find('function featureStyle(cfg,feat){');fs1=app.find('function pathGeometry',fs0);fs=app[fs0:fs1];check(rows,'featureStyle_icg',"st.renderer==='index_icg'" in fs and 'icgColor(p.icg_100)' in fs,'');check(rows,'featureStyle_no_legend_html',"if(st.renderer==='index_icg')return `<div" not in fs,'')
 lg0=app.find('function layerLegendHtml(cfg){');lg1=app.find('function updateLegend',lg0);lg=app[lg0:lg1 if lg1>lg0 else len(app)];check(rows,'legend_icg',"if(st.renderer==='index_icg')return" in lg,'')
 prefix='const CATALOG=';pos=app.find(prefix)+len(prefix);cat,end=json.JSONDecoder().raw_decode(app[pos:]);by={x.get('id'):x for x in cat.get('layers',[]) if isinstance(x,dict)}
 for lid,sc in [('icg_250','250'),('icg_500','500'),('icg_1000','1000')]:
  e=by.get(lid,{});check(rows,'catalog_'+lid,e.get('status')=='incorporada' and e.get('derive_type')=='icg_snapshot_v38417' and str(e.get('icg_scale'))==sc,e)
 idx=(repo/'docs/index.html').read_text(encoding='utf-8-sig');check(rows,'index_loads_icg','icg-v38417.js' in idx,'');sw=(repo/'docs/service-worker.js').read_text(encoding='utf-8-sig');check(rows,'service_worker_cache','ita-arandu-v38-4-17-icg-conhecimento-geocientifico' in sw,'');check(rows,'methodology_exists',(repo/'docs/documentos/metodologia-icg.html').exists(),'');check(rows,'VCG_not_materialized',not (repo/'docs/indices/vcg_v38418_snapshot.json').exists(),'');check(rows,'PIG_not_materialized',not (repo/'docs/indices/pig_v38419_snapshot.json').exists(),'')
 passed=sum(1 for r in rows if r['pass']);status='PASS' if passed==len(rows) else 'FAIL';out={'audit':'V38.4.17 · ICG · auditoria final','version':FINAL,'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'checks_total':len(rows),'checks_passed':passed,'checks':rows,'next_gate':'VCG permanece bloqueado até política própria de vazios de conhecimento'};(repo/'AUDITORIA_V38_4_17_ICG_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'AUDITORIA ICG V38.4.17 · {status} · {passed}/{len(rows)}')
 if status!='PASS':
  for r in rows:
   if not r['pass']:print('FAIL ·',r['name'],'·',r['detail'])
 return 0 if status=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
