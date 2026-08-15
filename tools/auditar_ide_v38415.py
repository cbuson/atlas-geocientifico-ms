#!/usr/bin/env python3
from pathlib import Path
import argparse,json,math,hashlib,re,datetime
FINAL='V38.4.15-IDE-DIVERSIDADE-EVIDENCIAS-20260815'
DIMS=['IMC','IOD','ICP','IGC','IGQ','IGF','ICS']
SCALES=['250','500','1000']
SNAPS=['docs/indices/imc_v32_snapshot.json','docs/indices/iod_v3848_snapshot.json','docs/indices/icp_v3849_snapshot.json','docs/indices/igc_v38410_snapshot.json','docs/indices/igq_v38411_snapshot.json','docs/indices/igf_v38412_snapshot.json','docs/indices/ics_v38413_snapshot.json']
GRIDS=['docs/camadas/arquivos/malha_r5_250km2.geojson','docs/camadas/arquivos/malha_500km2.geojson','docs/camadas/arquivos/malha_1000km2.geojson']
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def check(rows,name,ok,detail=''):rows.append({'name':name,'pass':bool(ok),'detail':str(detail)})
def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);args=ap.parse_args();repo=Path(args.repo).resolve();rows=[]
 ver=(repo/'VERSION').read_text(encoding='utf-8-sig').strip() if (repo/'VERSION').exists() else ''
 check(rows,'version',ver==FINAL,ver)
 sp=repo/'docs/indices/ide_v38415_snapshot.json';jp=repo/'docs/indices/ide-v38415.js';rp=repo/'AUDITORIA_V38_4_15_IDE_RUNTIME.json';policy=repo/'docs/indices/politica-sintese-v384142.json'
 for p,n in [(sp,'snapshot_IDE_exists'),(jp,'js_IDE_exists'),(rp,'runtime_audit_exists'),(policy,'gate_policy_exists')]:check(rows,n,p.exists(),p.relative_to(repo) if p.exists() else 'ausente')
 if not sp.exists():raise SystemExit(2)
 snap=load(sp);meta=snap.get('metadata',{})
 check(rows,'index_IDE',meta.get('index')=='IDE',meta.get('index'))
 check(rows,'formula_fixed',meta.get('formula')=='IDE_h = 100 × exp(H_h) / 7',meta.get('formula'))
 check(rows,'null_rule_explicit','não é convertido em zero' in meta.get('null_rule','') or 'não' in meta.get('null_rule','').lower(),meta.get('null_rule'))
 check(rows,'denominator_7','7' in meta.get('denominator_rule',''),meta.get('denominator_rule'))
 check(rows,'dimensions_exact',meta.get('dimensions')==DIMS,meta.get('dimensions'))
 check(rows,'IGF_MT_not_imputed','NAO_AVALIAVEL_NO_CORTE' in meta.get('igf_cut_status',''),meta.get('igf_cut_status'))
 # Base hashes protected
 protected=snap.get('protected_base_sha256',{});protected_g=snap.get('protected_grid_sha256',{})
 for rel in SNAPS:
  p=repo/rel;check(rows,'base_exists_'+Path(rel).stem,p.exists(),rel)
  if p.exists():check(rows,'base_sha_'+Path(rel).stem,protected.get(rel)==sha(p),sha(p))
 for rel in GRIDS:
  p=repo/rel;check(rows,'grid_exists_'+Path(rel).stem,p.exists(),rel)
  if p.exists():check(rows,'grid_sha_'+Path(rel).stem,protected_g.get(rel)==sha(p),sha(p))
 audit14=load(repo/'AUDITORIA_V38_4_14_SETE_DIMENSOES.json')
 for sc in SCALES:
  grid=snap.get('grids',{}).get(sc,{});summ=snap.get('summary',{}).get(sc,{})
  total={'250':1554,'500':793,'1000':412}[sc]
  check(rows,f'{sc}_row_count',len(grid)==total,len(grid))
  vals=[];bad=0;ceiling_bad=0;nobsdist={str(k):0 for k in range(0,8)}
  for hid,r in grid.items():
   if not isinstance(r,list) or len(r)<15:bad+=1;continue
   ide,neff,H,nobs,npos,frac,mask,totalScore,*base=r
   if ide is not None:
    if not finite(ide) or ide<0 or ide>100:bad+=1
    else:vals.append(ide)
   if not isinstance(nobs,int) or nobs<0 or nobs>7:bad+=1;continue
   nobsdist[str(nobs)]+=1
   if ide is not None and ide>100*max(npos,1)/7+0.001:ceiling_bad+=1
   if abs(float(frac)-nobs/7)>1e-5:bad+=1
   obs_from_base=sum(v is not None for v in base[:7]);pos_from_base=sum(finite(v) and float(v)>0 for v in base[:7])
   if obs_from_base!=nobs or pos_from_base!=npos:bad+=1
  check(rows,f'{sc}_row_schema',bad==0,f'bad={bad}')
  check(rows,f'{sc}_effective_diversity_ceiling',ceiling_bad==0,f'bad={ceiling_bad}')
  check(rows,f'{sc}_all_cells_calculable',len(vals)==total,f'{len(vals)}/{total}')
  expected={str(k):int(v) for k,v in audit14['complete_support'][sc]['dimension_count_distribution'].items()}
  ok=all(nobsdist.get(str(k),0)==expected.get(str(k),0) for k in range(0,8))
  check(rows,f'{sc}_support_distribution_matches_v38414',ok,{'actual':nobsdist,'expected':expected})
  check(rows,f'{sc}_summary_cells',summ.get('cells')==total,summ.get('cells'))
  check(rows,f'{sc}_min_floor',summ.get('ide_min') is not None and float(summ.get('ide_min'))>=100/7-0.01,summ.get('ide_min'))
 # App integration and renderer placement
 app=(repo/'docs/assets/js/app.js').read_text(encoding='utf-8-sig')
 check(rows,'app_ide_color','const ITA_IDE_COLORS=' in app,'')
 check(rows,'app_ide_builder','async function buildIdeSnapshotV38415' in app,'')
 check(rows,'app_ide_derive',"derive_type==='ide_snapshot_v38415'" in app,'')
 check(rows,'app_ide_scale_group','IDE_SCALE_LAYERS' in app,'')
 fs0=app.find('function featureStyle(cfg,feat){');fs1=app.find('function pathGeometry',fs0);fs=app[fs0:fs1]
 check(rows,'featureStyle_ide_object_renderer',"st.renderer==='index_ide'" in fs and 'ideColor(p.ide_100)' in fs,'')
 check(rows,'featureStyle_no_ide_legend_html',"if(st.renderer==='index_ide')return `<div" not in fs,'')
 lg0=app.find('function layerLegendHtml(cfg){');lg1=app.find('function updateLegend',lg0);lg=app[lg0:lg1 if lg1>lg0 else len(app)]
 check(rows,'layerLegend_ide',"if(st.renderer==='index_ide')return" in lg,'')
 # Catalog entries
 prefix='const CATALOG=';pos=app.find(prefix)+len(prefix);cat,end=json.JSONDecoder().raw_decode(app[pos:]);by={x.get('id'):x for x in cat.get('layers',[]) if isinstance(x,dict)}
 for lid,sc in [('ide_250','250'),('ide_500','500'),('ide_1000','1000')]:
  e=by.get(lid,{});check(rows,'catalog_'+lid,e.get('status')=='incorporada' and e.get('derive_type')=='ide_snapshot_v38415' and str(e.get('ide_scale'))==sc,e)
 # Web and docs
 idx=(repo/'docs/index.html').read_text(encoding='utf-8-sig')
 check(rows,'index_loads_ide_js','ide-v38415.js' in idx,'')
 sw=(repo/'docs/service-worker.js').read_text(encoding='utf-8-sig')
 check(rows,'service_worker_cache','ita-arandu-v38-4-15-ide-diversidade-evidencias' in sw,'')
 check(rows,'methodology_exists',(repo/'docs/documentos/metodologia-ide.html').exists(),'')
 # No later composites
 check(rows,'ICG_not_materialized',not (repo/'docs/indices/icg_v38416_snapshot.json').exists(),'')
 check(rows,'VCG_not_materialized',not (repo/'docs/indices/vcg_v38417_snapshot.json').exists(),'')
 check(rows,'PIG_not_materialized',not (repo/'docs/indices/pig_v38418_snapshot.json').exists(),'')
 passed=sum(1 for r in rows if r['pass']);status='PASS' if passed==len(rows) else 'FAIL'
 out={'audit':'V38.4.15 · IDE · auditoria final','version':FINAL,'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'checks_total':len(rows),'checks_passed':passed,'checks':rows,'next_gate':'ICG permanece bloqueado até regra própria de elegibilidade e penalização por incompletude'}
 (repo/'AUDITORIA_V38_4_15_IDE_FINAL.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'AUDITORIA IDE V38.4.15 · {status} · {passed}/{len(rows)}')
 if status!='PASS':
  for r in rows:
   if not r['pass']:print('FAIL ·',r['name'],'·',r['detail'])
 return 0 if status=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
