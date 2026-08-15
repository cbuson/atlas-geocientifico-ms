#!/usr/bin/env python3
from pathlib import Path
import argparse,json,math,datetime,hashlib
FINAL='V38.4.21-PIG-PRIORIDADE-INVESTIGACAO-GEOCIENTIFICA-20260815';SCALES=['250','500','1000']
GRIDS={'250':'docs/camadas/arquivos/malha_r5_250km2.geojson','500':'docs/camadas/arquivos/malha_500km2.geojson','1000':'docs/camadas/arquivos/malha_1000km2.geojson'}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def dominates(a,b):return a[0]>=b[0] and a[1]>=b[1] and (a[0]>b[0] or a[1]>b[1])
def class_pig(v):
 if v<20:return 'muito baixa'
 if v<40:return 'baixa'
 if v<60:return 'média'
 if v<80:return 'alta'
 return 'muito alta'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve();checks=[]
 def ck(n,o,d=''):checks.append({'name':n,'pass':bool(o),'detail':str(d)})
 ck('version',(repo/'VERSION').read_text(encoding='utf-8-sig').strip()==FINAL)
 snap=load(repo/'docs/indices/pig_v38421_snapshot.json');gate=load(repo/'AUDITORIA_V38_4_20_GATE_PIG_FINAL.json');pol=load(repo/'docs/indices/politica-pig-v38420.json')
 ck('snapshot_version',(snap.get('metadata') or {}).get('version')==FINAL);ck('gate_pass',gate.get('status')=='PASS');ck('policy_pass',pol.get('status')=='PASS');meta=snap.get('metadata') or {};ck('primary_front',meta.get('primary_output')=='pareto_front');ck('not_cardinal','nao e escala cardinal' in meta.get('pig_100_rule','').lower());ck('not_favorability','nao favorabilidade' in meta.get('interpretation_limit','').lower())
 for rel,h in (snap.get('protected_input_sha256') or {}).items():ck('hash_'+rel,sha(repo/rel)==h,rel)
 for sc in SCALES:
  ids=[str((f.get('properties') or {}).get('hex_id') or '') for f in load(repo/GRIDS[sc]).get('features',[])];g=(snap.get('grids') or {}).get(sc,{});sm=(snap.get('summary') or {}).get(sc,{});sen=(snap.get('sensitivity') or {}).get(sc,{})
  ck(sc+'_alignment',set(g)==set(ids),f'{len(g)}/{len(ids)}');bad=schema=0;pts=[];fronts={};ties={}
  for hid,r in g.items():
   if not isinstance(r,list) or len(r)!=18:schema+=1;continue
   pig,front,fmax,vcg,cgeo,frontsize,neff,tr,ns,nu,overlap,classe,frontsize2,med,doc,nobs,dom,sec=r
   if pig is None:
    if front is not None or cgeo is not None:bad+=1
    continue
   if not all(finite(x) for x in [pig,vcg,cgeo]) or not (0<=pig<=100 and 0<=vcg<=100 and 0<=cgeo<=100):bad+=1;continue
   if not isinstance(front,int) or not isinstance(fmax,int) or front<1 or fmax<front:bad+=1;continue
   expected=100.0 if fmax<=1 else 100.0*(1.0-(front-1)/(fmax-1))
   if abs(pig-expected)>0.011 or classe!=class_pig(pig) or frontsize!=frontsize2:bad+=1
   pts.append((hid,vcg,cgeo,front));fronts[front]=fronts.get(front,0)+1;ties.setdefault((round(vcg,8),round(cgeo,8)),set()).add(front)
  ck(sc+'_schema',schema==0,'bad='+str(schema));ck(sc+'_rows_valid',bad==0,'bad='+str(bad));ck(sc+'_summary_eligible',sm.get('eligible_cells')==len(pts),f"{sm.get('eligible_cells')}/{len(pts)}");ck(sc+'_front_count',sm.get('pareto_fronts')==(max(fronts) if fronts else 0));ck(sc+'_front1_count',sm.get('front_1_cells')==fronts.get(1,0));ck(sc+'_ties',all(len(v)==1 for v in ties.values()))
  # independent Pareto properties: every dominator has a lower front; every front > 1 has a dominator in immediately previous front.
  dom_bad=prev_bad=0
  for i,pi in enumerate(pts):
   has_prev=pi[3]==1
   for j,pj in enumerate(pts):
    if i==j:continue
    if dominates((pj[1],pj[2]),(pi[1],pi[2])):
     if pj[3]>=pi[3]:dom_bad+=1
     if pj[3]==pi[3]-1:has_prev=True
   if not has_prev:prev_bad+=1
  ck(sc+'_dominance_order',dom_bad==0,'bad='+str(dom_bad));ck(sc+'_front_predecessor',prev_bad==0,'bad='+str(prev_bad))
  for nm in ['baseline_2_5_P95','microgrid_1_25_P95','microgrid_5_P95','normalizacao_P90','normalizacao_P99']:ck(sc+'_sens_'+nm,nm in sen)
  for nm in ['microgrid_1_25_P95','microgrid_5_P95','normalizacao_P90','normalizacao_P99']:
   x=sen.get(nm,{});rho=x.get('spearman_cgeo');ck(sc+'_rho_'+nm,rho is None or -1<=float(rho)<=1,rho);j=x.get('front1_jaccard');ck(sc+'_jaccard_'+nm,j is not None and 0<=float(j)<=1,j)
 app=(repo/'docs/assets/js/app.js').read_text(encoding='utf-8-sig');ck('app_colors','const ITA_PIG_COLORS=' in app);ck('app_builder','async function buildPigSnapshotV38421' in app);ck('app_derive',"derive_type==='pig_snapshot_v38421'" in app);ck('app_scale_group','PIG_SCALE_LAYERS' in app)
 fs0=app.find('function featureStyle(cfg,feat){');fs1=app.find('function pathGeometry',fs0);fs=app[fs0:fs1];ck('renderer',"st.renderer==='index_pig'" in fs and 'pigColor(p.pig_100)' in fs);ck('renderer_not_legend',"if(st.renderer==='index_pig')return `<div" not in fs)
 lg0=app.find('function layerLegendHtml(cfg){');lg1=app.find('function updateLegend',lg0);lg=app[lg0:lg1 if lg1>lg0 else len(app)];ck('legend',"if(st.renderer==='index_pig')return" in lg)
 prefix='const CATALOG=';pos=app.find(prefix)+len(prefix);cat,end=json.JSONDecoder().raw_decode(app[pos:]);by={x.get('id'):x for x in cat.get('layers',[]) if isinstance(x,dict)}
 for lid,sc in [('pig_250','250'),('pig_500','500'),('pig_1000','1000')]:
  e=by.get(lid,{});ck('catalog_'+lid,e.get('status')=='incorporada' and e.get('derive_type')=='pig_snapshot_v38421' and str(e.get('pig_scale'))==sc,e)
 idx=(repo/'docs/index.html').read_text(encoding='utf-8-sig');ck('index_script','pig-v38421.js' in idx);sw=(repo/'docs/service-worker.js').read_text(encoding='utf-8-sig');ck('cache','ita-arandu-v38-4-21-pig-prioridade-investigacao' in sw);ck('methodology',(repo/'docs/documentos/metodologia-pig.html').exists())
 passed=sum(c['pass'] for c in checks);status='PASS' if passed==len(checks) else 'FAIL';out={'audit':'V38.4.21 PIG auditoria final','version':FINAL,'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'checks_total':len(checks),'checks_passed':passed,'checks':checks,'robustness_warnings':snap.get('robustness_warnings',[]),'next_step':'AUDITORIA ZERO final da familia de indices antes do fechamento cientifico do bloco'};(repo/'AUDITORIA_V38_4_21_PIG_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print(f'AUDITORIA PIG V38.4.21 - {status} - {passed}/{len(checks)}')
 if snap.get('robustness_warnings'):print('AVISOS DE ROBUSTEZ - '+json.dumps(snap['robustness_warnings'],ensure_ascii=False))
 if status!='PASS':
  for c in checks:
   if not c['pass']:print('FAIL -',c['name'],'-',c['detail'])
 return 0 if status=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
