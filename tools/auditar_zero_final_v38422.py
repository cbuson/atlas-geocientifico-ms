#!/usr/bin/env python3
from pathlib import Path
import argparse,json,math,statistics,datetime,hashlib,csv,re,html,sys
EXPECTED='V38.4.22-AUDITORIA-ZERO-FINAL-INDICES-20260815'
SCALES=['250','500','1000']
GRID_FILES={'250':'docs/camadas/arquivos/malha_r5_250km2.geojson','500':'docs/camadas/arquivos/malha_500km2.geojson','1000':'docs/camadas/arquivos/malha_1000km2.geojson'}
SNAPS={
 'IMC':'docs/indices/imc_v32_snapshot.json','IOD':'docs/indices/iod_v3848_snapshot.json','ICP':'docs/indices/icp_v3849_snapshot.json','IGC':'docs/indices/igc_v38410_snapshot.json','IGQ':'docs/indices/igq_v38411_snapshot.json','IGF':'docs/indices/igf_v38412_snapshot.json','ICS':'docs/indices/ics_v38413_snapshot.json','IDE':'docs/indices/ide_v38415_snapshot.json','ICG':'docs/indices/icg_v38417_snapshot.json','VCG':'docs/indices/vcg_v38419_snapshot.json','PIG':'docs/indices/pig_v38421_snapshot.json'}
BASE=['IMC','IOD','ICP','IGC','IGQ','IGF','ICS']
POLICIES=['docs/indices/politica-sintese-v384142.json','docs/indices/politica-icg-v38416.json','docs/indices/politica-vcg-v38418.json','docs/indices/politica-pig-v38420.json']
PROTECTED=list(SNAPS.values())+POLICIES+list(GRID_FILES.values())+['docs/camadas/arquivos/mapa_geologico_ms.geojson','AUDITORIA_V38_4_21_PIG_FINAL.json']

def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))
def num(v):
 if finite(v):return float(v)
 return None
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def approx(a,b,t=0.02):return a is not None and b is not None and abs(float(a)-float(b))<=t

def ids_grid(repo,sc):
 fc=load(repo/GRID_FILES[sc]);ids=[]
 for f in fc.get('features',[]):
  p=f.get('properties') or {};hid=str(p.get('hex_id') or '')
  if hid:ids.append(hid)
 return ids

def score_maps(data,name):
 out={}
 for sc in SCALES:
  if name=='IMC':
   scores=((data.get('grids') or {}).get(sc) or {}).get('scores') or {}
   out[sc]={k:num((v or {}).get('imc_100')) for k,v in scores.items()}
  else:
   g=(data.get('grids') or {}).get(sc) or {}
   out[sc]={k:(num(v[0]) if isinstance(v,list) and v else None) for k,v in g.items()}
 return out

def recalc_ide(vals):
 obs=[v for v in vals if v is not None]
 pos=[v for v in obs if v>0]
 if not obs or not pos:return None
 s=sum(pos);h=0.0
 for v in pos:
  p=v/s;h-=p*math.log(p)
 return 100*math.exp(h)/7

def recalc_icg(vals):
 obs=[v/100 for v in vals if v is not None]
 n=len(obs)
 if n<2:return None
 mu=sum(obs)/n
 var=sum((x-mu)**2 for x in obs)/n
 m=0.0 if mu<=0 else max(0.0,mu-var/mu)
 return 100*(n/7)*m

def recalc_vcg(vals):
 measured=0.0;missing=0
 for v in vals:
  if v is None:missing+=1
  else:measured+=(1-v/100)**2
 return 100*math.sqrt((measured+missing)/7)

def pareto_fronts(points):
 # Deterministic non-dominated sorting, same semantics as PIG gate.
 n=len(points);remaining=set(range(n));front=[None]*n;f=1
 while remaining:
  cur=[]
  for i in sorted(remaining):
   _,vi,ci=points[i];dom=False
   for j in remaining:
    if j==i:continue
    _,vj,cj=points[j]
    if vj>=vi and cj>=ci and (vj>vi or cj>ci):dom=True;break
   if not dom:cur.append(i)
  if not cur:break
  for i in cur:front[i]=f;remaining.remove(i)
  f+=1
 return front

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--before',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
 raw_before=load(a.before);before={str(k).replace('\\','/'):str(v).lower() for k,v in raw_before.items()}
 checks=[];warnings=[];metrics={};rows_csv=[]
 def ck(name,ok,detail='',severity='FAIL'):
  checks.append({'name':name,'pass':bool(ok),'detail':str(detail),'severity':severity})
 def warn(code,msg):warnings.append({'code':code,'message':msg})
 ck('version_final',(repo/'VERSION').read_text(encoding='utf-8-sig').strip()==EXPECTED,(repo/'VERSION').read_text(encoding='utf-8-sig').strip())
 # Protected hashes unchanged from prepatch state
 for rel in PROTECTED:
  p=repo/rel;expected=before.get(rel.replace('\\','/'))
  ok=p.exists() and expected is not None and sha(p).lower()==expected
  ck('sha_'+rel.replace('/','_'),ok,rel)
 # Required files
 for rel in list(SNAPS.values())+POLICIES+list(GRID_FILES.values())+['docs/assets/js/app.js','docs/assets/js/bootstrap.js','docs/service-worker.js','docs/index.html','docs/referencias/bibliografia-camadas-indices.json']:
  ck('exists_'+rel.replace('/','_'),(repo/rel).exists(),rel)
 # Version and PWA synchronization + known syntax regression
 idx=(repo/'docs/index.html').read_text(encoding='utf-8-sig')
 boot=(repo/'docs/assets/js/bootstrap.js').read_text(encoding='utf-8-sig')
 sw=(repo/'docs/service-worker.js').read_text(encoding='utf-8-sig')
 app=(repo/'docs/assets/js/app.js').read_text(encoding='utf-8-sig')
 ck('index_title_v38422','V38.4.22</title>' in idx)
 ck('index_cache_tokens_v38422','?v=38.4.21' not in idx and '?v=38.4.22' in idx)
 ck('bootstrap_cache_tokens_v38422','?v=38.4.21' not in boot and '?v=38.4.22' in boot)
 ck('service_worker_cache_v38422','ita-arandu-v38-4-22-auditoria-zero-final-indices' in sw)
 ck('service_worker_missing_comma_fixed','./documentos/changelog.html"\n  "./indices/ide' not in sw)
 ck('service_worker_final_report_precache','./documentos/auditoria-zero-final-indices.html' in sw)
 # Snapshots and grid alignment
 data={k:load(repo/v) for k,v in SNAPS.items()}
 ids={sc:ids_grid(repo,sc) for sc in SCALES}
 maps={k:score_maps(v,k) for k,v in data.items()}
 expected_counts={'250':1554,'500':793,'1000':412}
 for sc in SCALES:
  ck(f'grid_{sc}_count',len(ids[sc])==expected_counts[sc],f'{len(ids[sc])}/{expected_counts[sc]}')
  ck(f'grid_{sc}_unique',len(ids[sc])==len(set(ids[sc])),f'{len(set(ids[sc]))} unique')
  for name in SNAPS:
   m=maps[name][sc];ck(f'{name}_{sc}_alignment',set(m)==set(ids[sc]),f'{len(m)}/{len(ids[sc])}')
   bad=[v for v in m.values() if v is not None and not (0<=v<=100)]
   ck(f'{name}_{sc}_range',not bad,f'bad={len(bad)}')
 # Snapshot metadata semantics
 ck('IDE_formula','IDE_h = 100' in str((data['IDE'].get('metadata') or {}).get('formula','')))
 ck('IDE_null_rule','null' in str((data['IDE'].get('metadata') or {}).get('null_rule','')).lower())
 ck('ICG_formula','n_obs/7' in str((data['ICG'].get('metadata') or {}).get('formula','')))
 ck('ICG_eligibility','n_obs >= 2' in str((data['ICG'].get('metadata') or {}).get('eligibility','')))
 ck('VCG_not_100_minus_ICG','100 − ICG' in str((data['VCG'].get('metadata') or {}).get('not_icg_complement','')) or '100 - ICG' in str((data['VCG'].get('metadata') or {}).get('not_icg_complement','')))
 ck('PIG_primary_front',(data['PIG'].get('metadata') or {}).get('primary_output')=='pareto_front')
 ck('PIG_not_cardinal','nao e escala cardinal' in str((data['PIG'].get('metadata') or {}).get('pig_100_rule','')).lower() or 'não é escala cardinal' in str((data['PIG'].get('metadata') or {}).get('pig_100_rule','')).lower())
 ck('PIG_not_favorability','favorabilidade mineral' in str((data['PIG'].get('metadata') or {}).get('interpretation_limit','')).lower())
 # Exact recomputation of composite indices from the seven certified bases.
 for sc in SCALES:
  ide_bad=icg_bad=vcg_bad=0;elig_icg=0
  for hid in ids[sc]:
   vals=[maps[b][sc].get(hid) for b in BASE]
   ie=recalc_ide(vals);isv=maps['IDE'][sc].get(hid)
   if (ie is None)!=(isv is None) or (ie is not None and not approx(ie,isv,0.03)):ide_bad+=1
   cg=recalc_icg(vals);icgsv=maps['ICG'][sc].get(hid)
   if cg is not None:elig_icg+=1
   if (cg is None)!=(icgsv is None) or (cg is not None and not approx(cg,icgsv,0.03)):icg_bad+=1
   vg=recalc_vcg(vals);vsv=maps['VCG'][sc].get(hid)
   if vsv is None or not approx(vg,vsv,0.03):vcg_bad+=1
  ck(f'IDE_{sc}_recompute',ide_bad==0,f'bad={ide_bad}')
  ck(f'ICG_{sc}_recompute',icg_bad==0,f'bad={icg_bad}; eligible={elig_icg}')
  ck(f'VCG_{sc}_recompute',vcg_bad==0,f'bad={vcg_bad}')
 # PIG: objectives must reproduce stored Pareto fronts and ordinal display.
 pig=data['PIG'];pgr=pig.get('grids') or {}
 for sc in SCALES:
  pts=[];stored={}
  for hid,r in (pgr.get(sc) or {}).items():
   if not isinstance(r,list) or len(r)<5:continue
   pig100=num(r[0]);front=r[1] if isinstance(r[1],int) else None;fmax=r[2] if isinstance(r[2],int) else None;v=num(r[3]);c=num(r[4])
   if v is not None and c is not None:
    pts.append((hid,v,c));stored[hid]=(front,fmax,pig100)
  calc=pareto_fronts(pts);bad_front=bad_ord=0
  fmax_calc=max([x for x in calc if x is not None],default=0)
  for (hid,v,c),fr in zip(pts,calc):
   sf,sfm,sp=stored[hid]
   if sf!=fr or sfm!=fmax_calc:bad_front+=1
   expected=100.0 if fmax_calc<=1 else 100*(1-(fr-1)/(fmax_calc-1))
   if sp is None or not approx(sp,expected,0.03):bad_ord+=1
  ck(f'PIG_{sc}_pareto_recompute',bad_front==0,f'bad={bad_front}; fronts={fmax_calc}')
  ck(f'PIG_{sc}_ordinal_recompute',bad_ord==0,f'bad={bad_ord}')
  metrics[sc]={'cells':len(ids[sc]),'pig_eligible':len(pts),'pareto_fronts':fmax_calc,'front1':sum(1 for x in calc if x==1),'icg_numeric':sum(v is not None for v in maps['ICG'][sc].values()),'vcg_numeric':sum(v is not None for v in maps['VCG'][sc].values())}
 # PIG upstream final audit and robustness warnings.
 pa=load(repo/'AUDITORIA_V38_4_21_PIG_FINAL.json')
 ck('PIG_audit_103_103',pa.get('status')=='PASS' and pa.get('checks_passed')==pa.get('checks_total') and pa.get('checks_total',0)>=100,f"{pa.get('checks_passed')}/{pa.get('checks_total')}")
 for w in pa.get('robustness_warnings') or []:warn('PIG_SENSIBILIDADE',str(w))
 # IGF cut incompleteness is acceptable only if explicitly frozen in synthesis policy.
 igf_comp=str((data['IGF'].get('metadata') or {}).get('source_completeness','')).lower()
 pol=load(repo/'docs/indices/politica-sintese-v384142.json')
 mt=((pol.get('igf_cut_policy') or {}).get('mt_module'))
 if igf_comp and igf_comp!='completa':
  ck('IGF_partial_documented',mt=='NAO_AVALIAVEL_NO_CORTE',f'source_completeness={igf_comp}; mt={mt}')
  if mt=='NAO_AVALIAVEL_NO_CORTE':warn('IGF_MT_CORTE','IGF foi materializado com fonte parcial; MT permanece NAO_AVALIAVEL_NO_CORTE e nao recebe zero nem imputacao.')
 # Bibliographic registry and index families.
 bib=load(repo/'docs/referencias/bibliografia-camadas-indices.json');fams=bib.get('index_families') or {}
 for name in SNAPS:
  ck('bibliografia_'+name,name in fams,name)
 ck('bibliografia_APA7',str(bib.get('citation_standard','')).upper().replace(' ','')=='APA7',bib.get('citation_standard'))
 # Frontend renderer and layer IDs for all indices.
 id_alias={'IMC':'imc','IOD':'iod','ICP':'icp','IGC':'igc','IGQ':'igq','IGF':'igf','ICS':'ics','IDE':'ide','ICG':'icg','VCG':'vcg','PIG':'pig'}
 for name,prefix in id_alias.items():
  ck('renderer_'+name,("index_"+prefix) in app,name)
  # Layer IDs are dynamically embedded in CATALOG inside app.js.
  ok=all(('"id":"%s_%s"'%(prefix,sc)) in app or (name=='VCG' and ('"id":"vazios_%s"'%sc) in app) for sc in SCALES)
  ck('catalog_layers_'+name,ok,name)
 # Final status. Warnings do not erase PASS, but produce explicit PASS_COM_RESSALVAS.
 failures=[x for x in checks if not x['pass'] and x.get('severity')!='WARN']
 status='FAIL' if failures else ('PASS_COM_RESSALVAS' if warnings else 'PASS')
 result={'audit':'V38.4.22 · AUDITORIA ZERO FINAL · família de índices','version':EXPECTED,'generated_at':now(),'status':status,'checks_total':len(checks),'checks_passed':sum(x['pass'] for x in checks),'checks_failed':len(failures),'warnings':warnings,'metrics':metrics,'checks':checks,'scientific_chain':['IMC','IOD','ICP','IGC','IGQ','IGF','ICS','IDE','ICG','VCG','PIG'],'interpretation':{'PIG':'pareto_front é a saída científica primária; PIG_100 é ordinal e não cardinal','VCG':'lacuna documental não equivale a ausência geológica','null':'null nunca é convertido automaticamente em zero','closure':'nenhum snapshot científico foi recalculado na V38.4.22'}}
 (repo/'AUDITORIA_ZERO_FINAL_V38_4_22.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 # CSV summary
 with open(repo/'AUDITORIA_ZERO_FINAL_V38_4_22_RESUMO.csv','w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter=';');w.writerow(['escala_km2','celulas','icg_numerico','vcg_numerico','pig_elegivel','fronts_pareto','front1'])
  for sc in SCALES:
   m=metrics[sc];w.writerow([sc,m['cells'],m['icg_numeric'],m['vcg_numeric'],m['pig_eligible'],m['pareto_fronts'],m['front1']])
 # Matrix of index coverage
 with open(repo/'AUDITORIA_ZERO_FINAL_V38_4_22_MATRIZ_INDICES.csv','w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter=';');w.writerow(['indice']+SCALES)
  for name in SNAPS:w.writerow([name]+[sum(v is not None for v in maps[name][sc].values()) for sc in SCALES])
 # Public HTML report
 def esc(x):return html.escape(str(x))
 warnhtml=''.join(f'<li><b>{esc(w["code"])}</b> · {esc(w["message"])}</li>' for w in warnings) or '<li>Nenhuma ressalva adicional.</li>'
 failhtml=''.join(f'<li>{esc(x["name"])} · {esc(x["detail"])}</li>' for x in failures) or '<li>Nenhuma falha científica ou técnica bloqueante.</li>'
 table=''.join(f'<tr><td>{sc}</td><td>{metrics[sc]["cells"]}</td><td>{metrics[sc]["icg_numeric"]}</td><td>{metrics[sc]["vcg_numeric"]}</td><td>{metrics[sc]["pig_eligible"]}</td><td>{metrics[sc]["pareto_fronts"]}</td><td>{metrics[sc]["front1"]}</td></tr>' for sc in SCALES)
 page=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Auditoria ZERO final · ITA ARANDU MS</title><style>body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:1000px;margin:auto;padding:28px;color:#24323d;line-height:1.5}}h1,h2{{color:#073b63}}.status{{font-size:1.15rem;font-weight:800;padding:12px;border:1px solid #ccd9df;border-radius:10px;background:#f4f8fa}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d6e0e5;padding:8px;text-align:right}}th:first-child,td:first-child{{text-align:left}}code{{background:#eef3f6;padding:2px 5px;border-radius:5px}}.warn{{background:#fff8df;border-left:4px solid #d39b00;padding:12px}}.ok{{background:#edf8f0;border-left:4px solid #2a8a4b;padding:12px}}</style></head><body><p><a href="../index.html">← ITA ARANDU MS</a></p><h1>AUDITORIA ZERO FINAL · família de índices</h1><p class="status">Estado · {esc(status)} · {sum(x['pass'] for x in checks)}/{len(checks)} controles aprovados</p><p>Versão auditada · <code>{EXPECTED}</code></p><p>Sequência científica · IMC · IOD · ICP · IGC · IGQ · IGF · ICS · IDE · ICG · VCG · PIG.</p><h2>Resultados estruturais</h2><table><thead><tr><th>Escala km²</th><th>Células</th><th>ICG numérico</th><th>VCG numérico</th><th>PIG elegível</th><th>Fronts</th><th>Front 1</th></tr></thead><tbody>{table}</tbody></table><h2>Ressalvas científicas</h2><div class="warn"><ul>{warnhtml}</ul></div><h2>Falhas bloqueantes</h2><div class="ok"><ul>{failhtml}</ul></div><h2>Regras preservadas</h2><ul><li><code>null</code> não é convertido automaticamente em zero.</li><li>VCG distingue déficit medido de lacuna documental e não é <code>100 − ICG</code>.</li><li>Front de Pareto é a saída científica primária do PIG.</li><li><code>PIG_100</code> é apenas uma transformação ordinal de simbologia.</li><li>PIG indica prioridade relativa de investigação, não favorabilidade mineral.</li><li>Nenhum snapshot científico foi recalculado pela V38.4.22.</li></ul><h2>Arquivos de auditoria</h2><p><code>AUDITORIA_ZERO_FINAL_V38_4_22.json</code><br><code>AUDITORIA_ZERO_FINAL_V38_4_22_RESUMO.csv</code><br><code>AUDITORIA_ZERO_FINAL_V38_4_22_MATRIZ_INDICES.csv</code></p></body></html>'''
 out=repo/'docs/documentos/auditoria-zero-final-indices.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(page,encoding='utf-8',newline='\n')
 print(f'AUDITORIA ZERO FINAL V38.4.22 · {status} · {sum(x["pass"] for x in checks)}/{len(checks)}')
 for w in warnings:print('RESSALVA ·',w['code'],'·',w['message'])
 if failures:
  for x in failures[:30]:print('FAIL',x['name'],x['detail'])
  return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
