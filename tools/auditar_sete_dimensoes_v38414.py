#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, html, json, math, statistics, sys
from pathlib import Path
from datetime import datetime, timezone

EXPECTED_VERSION='V38.4.13-ICS-CONHECIMENTO-SUBSOLO-20260814'
FINAL_VERSION='V38.4.14-AUDITORIA-SETE-DIMENSOES-20260815'
SCALES=('250','500','1000')
EXPECTED_COUNTS={'250':1554,'500':793,'1000':412}
GRID_FILES={
 '250':'docs/camadas/arquivos/malha_r5_250km2.geojson',
 '500':'docs/camadas/arquivos/malha_500km2.geojson',
 '1000':'docs/camadas/arquivos/malha_1000km2.geojson',
}
INDEX_FILES={
 'IMC':'docs/indices/imc_v32_snapshot.json',
 'IOD':'docs/indices/iod_v3848_snapshot.json',
 'ICP':'docs/indices/icp_v3849_snapshot.json',
 'IGC':'docs/indices/igc_v38410_snapshot.json',
 'IGQ':'docs/indices/igq_v38411_snapshot.json',
 'IGF':'docs/indices/igf_v38412_snapshot.json',
 'ICS':'docs/indices/ics_v38413_snapshot.json',
}
INDEX_JS={
 'IMC':'docs/indices/imc-v32.js','IOD':'docs/indices/iod-v3848.js','ICP':'docs/indices/icp-v3849.js',
 'IGC':'docs/indices/igc-v38410.js','IGQ':'docs/indices/igq-v38411.js','IGF':'docs/indices/igf-v38412.js','ICS':'docs/indices/ics-v38413.js'
}
FINAL_AUDITS={
 'IOD':'AUDITORIA_V38_4_8_IOD_FINAL.json','ICP':'AUDITORIA_V38_4_9_ICP_FINAL.json',
 'IGC':'AUDITORIA_V38_4_10_IGC_FINAL.json','IGQ':'AUDITORIA_V38_4_11_IGQ_FINAL.json',
 'IGF':'AUDITORIA_V38_4_12_IGF_FINAL.json','ICS':'AUDITORIA_V38_4_13_ICS_FINAL.json'
}

def now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load(p:Path):
    with p.open('r',encoding='utf-8') as f:return json.load(f)
def dump(p:Path,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def finite(v):
    try:
        x=float(v);return x if math.isfinite(x) else None
    except Exception:return None
def pct(vals,p):
    a=sorted(float(x) for x in vals if finite(x) is not None)
    if not a:return None
    if len(a)==1:return a[0]
    pos=(len(a)-1)*p/100.0;lo=math.floor(pos);hi=math.ceil(pos)
    return a[lo] if lo==hi else a[lo]+(a[hi]-a[lo])*(pos-lo)
def med_abs_diff(a,b):
    d=[abs(x-y) for x,y in zip(a,b)]
    return statistics.median(d) if d else None
def rankdata(a):
    order=sorted(range(len(a)),key=lambda i:(a[i],i));r=[0.0]*len(a);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and a[order[j]]==a[order[i]]:j+=1
        rr=(i+j-1)/2+1
        for k in range(i,j):r[order[k]]=rr
        i=j
    return r
def pearson(a,b):
    n=len(a)
    if n<2:return None
    ma=sum(a)/n;mb=sum(b)/n
    da=[x-ma for x in a];db=[y-mb for y in b]
    va=sum(x*x for x in da);vb=sum(y*y for y in db)
    if va<=0 or vb<=0:return None
    return sum(x*y for x,y in zip(da,db))/math.sqrt(va*vb)
def spearman(a,b):
    return pearson(rankdata(a),rankdata(b)) if len(a)>=2 else None
def stats(vals,total):
    a=[float(x) for x in vals if finite(x) is not None]
    if not a:return {'n':0,'nulls':total,'coverage':0.0,'min':None,'p05':None,'median':None,'mean':None,'p95':None,'max':None,'sd':None,'n_unique':0,'pct_100':0.0}
    return {'n':len(a),'nulls':total-len(a),'coverage':round(len(a)/total,6),'min':round(min(a),4),'p05':round(pct(a,5),4),'median':round(statistics.median(a),4),'mean':round(statistics.fmean(a),4),'p95':round(pct(a,95),4),'max':round(max(a),4),'sd':round(statistics.pstdev(a),4),'n_unique':len(set(round(x,6) for x in a)),'pct_100':round(sum(abs(x-100)<1e-9 for x in a)/len(a),6)}
def is_border(v):
    s=str(v or '').strip().lower()
    return s in {'sim','yes','true','1','s'}
def recursive_numbers(obj):
    out=[]
    if isinstance(obj,dict):
        for v in obj.values():out.extend(recursive_numbers(v))
    elif isinstance(obj,list):
        for v in obj:out.extend(recursive_numbers(v))
    elif isinstance(obj,(int,float)) and math.isfinite(float(obj)) and -1.000001<=float(obj)<=1.000001:
        out.append(float(obj))
    return out

def extract_values(index,snap,scale):
    if index=='IMC':
        scores=((snap.get('grids') or {}).get(scale) or {}).get('scores') or {}
        out={}
        for hid,row in scores.items():
            if isinstance(row,dict):v=row.get('imc_100')
            else:v=row
            out[str(hid)]=finite(v)
        return out
    rows=(snap.get('grids') or {}).get(scale) or {}
    out={}
    for hid,row in rows.items():
        v=row[0] if isinstance(row,list) and row else None
        out[str(hid)]=finite(v)
    return out

def make_html(report):
    def esc(x):return html.escape(str(x))
    status=report['status'];gate=report['synthesis_gate']['status']
    rows=[]
    for sc in SCALES:
        for idx in INDEX_FILES:
            s=report['distributions'][sc][idx]
            rows.append(f"<tr><td>{sc}</td><td>{idx}</td><td>{s['n']}</td><td>{s['nulls']}</td><td>{100*s['coverage']:.1f}%</td><td>{esc(s['median'])}</td><td>{esc(s['mean'])}</td><td>{esc(s['min'])}</td><td>{esc(s['max'])}</td></tr>")
    cor=[]
    for sc in SCALES:
        for r in report['correlations'][sc]:
            rho='' if r['rho'] is None else f"{r['rho']:.3f}"
            cor.append(f"<tr><td>{sc}</td><td>{esc(r['a'])}</td><td>{esc(r['b'])}</td><td>{r['n_overlap']}</td><td>{rho}</td><td>{100*r['support_jaccard']:.1f}%</td><td>{100*r['exact_equal_fraction']:.1f}%</td></tr>")
    bord=[]
    for sc in SCALES:
        for idx,b in report['border_effects'][sc].items():
            bord.append(f"<tr><td>{sc}</td><td>{idx}</td><td>{100*b['coverage_border']:.1f}%</td><td>{100*b['coverage_interior']:.1f}%</td><td>{100*b['coverage_delta']:+.1f} pp</td><td>{esc(b['median_border'])}</td><td>{esc(b['median_interior'])}</td></tr>")
    warn=''.join(f'<li>{esc(x)}</li>' for x in report['warnings']) or '<li>Nenhum aviso científico automático.</li>'
    block=''.join(f'<li>{esc(x)}</li>' for x in report['synthesis_gate']['blockers']) or '<li>Nenhum bloqueador.</li>'
    cond=''.join(f'<li>{esc(x)}</li>' for x in report['synthesis_gate']['conditions']) or '<li>Nenhuma condição adicional.</li>'
    overlap=''.join(f"<tr><td>{sc}</td><td>{report['complete_support'][sc]['n_all_7']}</td><td>{100*report['complete_support'][sc]['fraction_all_7']:.2f}%</td><td>{esc(report['complete_support'][sc]['dimension_count_distribution'])}</td></tr>" for sc in SCALES)
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ITA ARANDU MS · Auditoria das sete dimensões</title><style>body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:1220px;margin:auto;padding:24px;line-height:1.48;color:#1f2937}}h1,h2{{line-height:1.15}}.badge{{display:inline-block;padding:4px 10px;border-radius:999px;background:#eee;font-weight:700}}table{{border-collapse:collapse;width:100%;font-size:.9rem;margin:12px 0 24px}}th,td{{border:1px solid #d1d5db;padding:6px 8px;text-align:left}}th{{background:#f3f4f6;position:sticky;top:0}}.scroll{{overflow:auto}}code{{background:#f3f4f6;padding:2px 4px;border-radius:4px}}.note{{padding:12px;border-left:4px solid #6b7280;background:#f9fafb}}li{{margin:.3rem 0}}</style></head><body><h1>Auditoria conjunta das sete dimensões base</h1><p><span class="badge">Auditoria técnica {esc(status)}</span> <span class="badge">Gate de síntese {esc(gate)}</span></p><p>Versão {esc(report['version'])}. Corte auditado sem recalcular IMC, IOD, ICP, IGC, IGQ, IGF ou ICS.</p><div class="note"><b>Regra central</b> · valores <code>null</code> permanecem ausência de evidência documentada na dimensão base. Esta auditoria não os transforma em zero e não calcula IDE, ICG, VCG ou PIG.</div><h2>Distribuições</h2><div class="scroll"><table><thead><tr><th>km²</th><th>Índice</th><th>n</th><th>null</th><th>cobertura</th><th>mediana</th><th>média</th><th>mín</th><th>máx</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div><h2>Sobreposição das sete dimensões</h2><table><thead><tr><th>km²</th><th>células com 7/7</th><th>%</th><th>distribuição n dimensões observadas</th></tr></thead><tbody>{overlap}</tbody></table><h2>Correlação e redundância</h2><div class="scroll"><table><thead><tr><th>km²</th><th>A</th><th>B</th><th>n comum</th><th>Spearman ρ</th><th>Jaccard suporte</th><th>valores exatamente iguais</th></tr></thead><tbody>{''.join(cor)}</tbody></table></div><h2>Efeito de borda</h2><div class="scroll"><table><thead><tr><th>km²</th><th>Índice</th><th>cobertura borda</th><th>cobertura interior</th><th>diferença</th><th>mediana borda</th><th>mediana interior</th></tr></thead><tbody>{''.join(bord)}</tbody></table></div><h2>Avisos</h2><ul>{warn}</ul><h2>Bloqueadores para síntese</h2><ul>{block}</ul><h2>Condições para os índices de síntese</h2><ul>{cond}</ul><h2>Critérios automáticos</h2><p>São bloqueadores a ausência ou desalinhamento de snapshots, valores fora de 0–100, dimensão sem observações numéricas, auditoria base final em FAIL, duplicação praticamente exata entre dimensões, sensibilidade severamente instável e fonte geofísica explicitamente parcial por indisponibilidade remota. Correlações elevadas, efeitos de borda, saturação e baixa sobreposição completa são documentados como avisos salvo evidência de erro estrutural.</p><h2>Referências metodológicas</h2><p>Saisana, M., Saltelli, A., &amp; Tarantola, S. (2005). Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators. <i>Journal of the Royal Statistical Society: Series A</i>, 168(2), 307–323. https://doi.org/10.1111/j.1467-985X.2005.00350.x</p><p>Spearman, C. (1904). The proof and measurement of association between two things. <i>The American Journal of Psychology</i>, 15(1), 72–101. https://doi.org/10.2307/1412159</p><p>Stevens, D. L., Jr., &amp; Olsen, A. R. (2004). Spatially balanced sampling of natural resources. <i>Journal of the American Statistical Association</i>, 99(465), 262–278. https://doi.org/10.1198/016214504000000250</p><p>ITA ARANDU MS. Protocolo dos índices multiescalares de conhecimento geocientífico. Documento de trabalho, 2026.</p></body></html>'''

def append_docs(repo:Path,report):
    readme=repo/'README.md'
    if readme.exists():
        t=readme.read_text(encoding='utf-8')
        marker='V38.4.14 · Auditoria conjunta das sete dimensões base'
        if marker not in t:
            t=t.rstrip()+f"\n\n## {marker}\n\nAuditoria multiescalar de IMC, IOD, ICP, IGC, IGQ, IGF e ICS. Gate de síntese: **{report['synthesis_gate']['status']}**. Nenhum índice base foi recalculado. Relatório em `docs/documentos/auditoria-sete-dimensoes.html`.\n"
            readme.write_text(t,encoding='utf-8',newline='\n')
    ch=repo/'CHANGELOG.md'
    if ch.exists():
        t=ch.read_text(encoding='utf-8')
        marker='V38.4.14 · Auditoria das sete dimensões'
        if marker not in t:
            t=t.rstrip()+f"\n\n## {marker}\n\n- Auditoria conjunta de IMC, IOD, ICP, IGC, IGQ, IGF e ICS nas três escalas.\n- Verificação de alinhamento espacial, faixas, nulls, distribuições, correlações, redundância, sensibilidade e bordas.\n- Gate de síntese: {report['synthesis_gate']['status']}.\n- Nenhum índice base recalculado.\n"
            ch.write_text(t,encoding='utf-8',newline='\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');ap.add_argument('--self-test',action='store_true');args=ap.parse_args()
    if args.self_test:
        a=[1,2,3,4,5];b=[10,20,30,40,50];c=[5,4,3,2,1]
        assert abs(spearman(a,b)-1)<1e-12 and abs(spearman(a,c)+1)<1e-12
        assert pct([1,2,3,4,5],50)==3
        print('SELF TEST V38.4.14 · PASS');return 0
    repo=Path(args.repo).resolve();technical=[];warnings=[];blockers=[];conditions=[]
    def check(name,ok,detail=''):
        technical.append({'name':name,'pass':bool(ok),'detail':str(detail)})
        if not ok:print('FAIL ·',name,'·',detail)
    vf=repo/'VERSION';check('version_file',vf.exists())
    ver=vf.read_text(encoding='utf-8').strip() if vf.exists() else ''
    check('version_origin',ver==EXPECTED_VERSION,ver)
    snapshots={};hashes={}
    for idx,rel in INDEX_FILES.items():
        p=repo/rel;check(f'snapshot_{idx}_exists',p.exists(),rel)
        if p.exists():snapshots[idx]=load(p);hashes[rel]=sha256(p)
    for idx,rel in INDEX_JS.items():
        p=repo/rel;check(f'js_{idx}_exists',p.exists(),rel)
        if p.exists():hashes[rel]=sha256(p)
    grids={};grid_ids={};border={}
    for sc,rel in GRID_FILES.items():
        p=repo/rel;check(f'grid_{sc}_exists',p.exists(),rel)
        if not p.exists():continue
        g=load(p);fs=g.get('features') or [];check(f'grid_{sc}_count',len(fs)==EXPECTED_COUNTS[sc],len(fs));ids=[];bd={}
        for f in fs:
            pr=f.get('properties') or {};hid=str(pr.get('hex_id') or '')
            if hid:ids.append(hid);bd[hid]=is_border(pr.get('celula_borda_estadual'))
        check(f'grid_{sc}_ids_unique',len(ids)==len(set(ids))==EXPECTED_COUNTS[sc],len(set(ids)))
        grids[sc]=g;grid_ids[sc]=set(ids);border[sc]=bd;hashes[rel]=sha256(p)
    if not all(i in snapshots for i in INDEX_FILES) or not all(sc in grid_ids for sc in SCALES):
        return 3
    values={sc:{} for sc in SCALES};distributions={sc:{} for sc in SCALES}
    for sc in SCALES:
        canonical=grid_ids[sc]
        for idx,snap in snapshots.items():
            m=extract_values(idx,snap,sc);values[sc][idx]=m
            check(f'{idx}_{sc}_id_alignment',set(m)==canonical,f'{len(m)} vs {len(canonical)}')
            bad=[(hid,v) for hid,v in m.items() if v is not None and not (0<=v<=100)]
            check(f'{idx}_{sc}_range_0_100',not bad,bad[:3])
            n=sum(v is not None for v in m.values());check(f'{idx}_{sc}_numeric_positive',n>0,n)
            distributions[sc][idx]=stats(m.values(),len(canonical))
            if distributions[sc][idx]['pct_100']>0.25:warnings.append(f'{idx} {sc} km² apresenta {100*distributions[sc][idx]["pct_100"]:.1f}% dos valores numéricos saturados em 100.')
            if distributions[sc][idx]['n_unique']<=2 and n>=30:warnings.append(f'{idx} {sc} km² apresenta apenas {distributions[sc][idx]["n_unique"]} valores distintos entre {n} células numéricas.')
    # auditorias finais das dimensões materializadas
    base_audits={}
    for idx,rel in FINAL_AUDITS.items():
        p=repo/rel;check(f'final_audit_{idx}_exists',p.exists(),rel)
        if p.exists():
            o=load(p);base_audits[idx]={'status':o.get('status'),'checks_total':o.get('checks_total'),'checks_passed':o.get('checks_passed')}
            check(f'final_audit_{idx}_pass',o.get('status')=='PASS',o.get('status'))
    # salvaguardas documentais
    pending=snapshots['IMC'].get('pending_exact_footprints') or []
    if pending:warnings.append(f'IMC mantém {len(pending)} footprints detalhados conhecidos ainda pendentes de geometria exata. O snapshot permanece conservador e não os imputa.')
    igc_n=(snapshots['IGC'].get('metadata') or {}).get('independent_direct_samples')
    if isinstance(igc_n,(int,float)) and igc_n<10:warnings.append(f'IGC baseia-se em apenas {int(igc_n)} amostras geocronológicas diretas independentes no corte atual. A baixa cobertura deve permanecer explícita.')
    igf_meta=snapshots['IGF'].get('metadata') or {};igf_comp=igf_meta.get('source_completeness')
    if igf_comp and igf_comp!='completa':blockers.append(f'IGF foi materializado com fonte geofísica parcial ({igf_comp}). Antes dos índices de síntese é necessário completar ou congelar documentalmente a indisponibilidade do módulo remoto.')
    # sensibilidade
    sensitivity={}
    for idx,snap in snapshots.items():
        obj=snap.get('sensitivity_spearman',snap.get('sensitivity'))
        nums=recursive_numbers(obj) if obj is not None else []
        nums=[x for x in nums if -1<=x<=1]
        if nums:
            mn=min(nums);sensitivity[idx]={'n_scenarios':len(nums),'min_rho':round(mn,6),'median_rho':round(statistics.median(nums),6),'max_rho':round(max(nums),6)}
            if mn<0.5:blockers.append(f'{idx} apresenta cenário de sensibilidade com Spearman ρ={mn:.3f}, abaixo do limiar crítico 0,50.')
            elif mn<0.7:warnings.append(f'{idx} apresenta sensibilidade relevante em pelo menos um cenário, com ρ mínimo {mn:.3f}.')
        else:sensitivity[idx]={'n_scenarios':0,'min_rho':None,'median_rho':None,'max_rho':None}
    # correlações e redundância
    correlations={sc:[] for sc in SCALES}
    idxs=list(INDEX_FILES)
    for sc in SCALES:
        for i,a in enumerate(idxs):
            for b in idxs[i+1:]:
                ma,mb=values[sc][a],values[sc][b];ids=sorted(grid_ids[sc]);xa=[];xb=[]
                sa={h for h in ids if ma.get(h) is not None};sb={h for h in ids if mb.get(h) is not None};inter=sa&sb;union=sa|sb
                for h in sorted(inter):xa.append(ma[h]);xb.append(mb[h])
                rho=spearman(xa,xb) if len(xa)>=3 else None
                eq=sum(abs(x-y)<1e-9 for x,y in zip(xa,xb))/len(xa) if xa else 0.0
                mad=med_abs_diff(xa,xb)
                rec={'a':a,'b':b,'n_overlap':len(xa),'rho':None if rho is None else round(rho,6),'support_jaccard':round(len(inter)/len(union),6) if union else 1.0,'exact_equal_fraction':round(eq,6),'median_abs_diff':None if mad is None else round(mad,6)}
                correlations[sc].append(rec)
                if len(xa)>=30 and eq>=0.995:blockers.append(f'{a} e {b} em {sc} km² apresentam valores praticamente idênticos em {100*eq:.1f}% de {len(xa)} células comuns, sugerindo duplicação indevida.')
                elif rho is not None and len(xa)>=30 and abs(rho)>=0.95:warnings.append(f'{a} e {b} em {sc} km² têm correlação de Spearman elevada (ρ={rho:.3f}, n={len(xa)}). Revisar redundância antes de síntese.')
    # efeito de borda
    border_effects={sc:{} for sc in SCALES}
    for sc in SCALES:
        ids=grid_ids[sc];bids={h for h in ids if border[sc].get(h)};iids=ids-bids
        for idx in idxs:
            m=values[sc][idx];bv=[m[h] for h in bids if m.get(h) is not None];iv=[m[h] for h in iids if m.get(h) is not None]
            cb=len(bv)/len(bids) if bids else 0;ci=len(iv)/len(iids) if iids else 0;mb=statistics.median(bv) if bv else None;mi=statistics.median(iv) if iv else None
            rec={'n_border':len(bids),'n_interior':len(iids),'numeric_border':len(bv),'numeric_interior':len(iv),'coverage_border':round(cb,6),'coverage_interior':round(ci,6),'coverage_delta':round(cb-ci,6),'median_border':None if mb is None else round(mb,4),'median_interior':None if mi is None else round(mi,4)}
            border_effects[sc][idx]=rec
            if abs(cb-ci)>=0.25:warnings.append(f'{idx} {sc} km² mostra diferença de cobertura borda/interior de {100*(cb-ci):+.1f} pontos percentuais.')
            if mb is not None and mi is not None and abs(mb-mi)>=25:warnings.append(f'{idx} {sc} km² mostra diferença de mediana borda/interior de {mb-mi:+.1f} pontos.')
    # suporte completo e número de dimensões observadas
    complete_support={}
    for sc in SCALES:
        dist={str(k):0 for k in range(8)};all7=0
        for h in grid_ids[sc]:
            k=sum(values[sc][idx].get(h) is not None for idx in idxs);dist[str(k)]+=1
            if k==7:all7+=1
        frac=all7/EXPECTED_COUNTS[sc]
        complete_support[sc]={'n_all_7':all7,'fraction_all_7':round(frac,6),'dimension_count_distribution':dist}
        if frac<0.10:warnings.append(f'Apenas {100*frac:.2f}% das células de {sc} km² têm valores numéricos simultâneos nas sete dimensões. IDE/ICG não devem usar complete-case silencioso.')
    if any(distributions[sc][idx]['nulls']>0 for sc in SCALES for idx in idxs):
        conditions.append('A próxima etapa deve congelar uma política explícita para null. Nenhum null das dimensões base pode ser convertido automaticamente em zero sem regra metodológica específica do índice de síntese.')
    conditions.append('IDE e ICG devem declarar regra de elegibilidade mínima e número de dimensões efetivamente observadas por célula; complete-case não pode ser adotado silenciosamente.')
    conditions.append('VCG pode representar ausência de conhecimento documentado somente mediante regra explícita que preserve a distinção entre lacuna de evidência e ausência geológica.')
    conditions.append('PIG permanece bloqueado até VCG certificado e definição independente da complexidade geológica e do algoritmo de Pareto.')
    # drift entre escalas, apenas aviso
    scale_drift={}
    for idx in idxs:
        scale_drift[idx]={sc:{'coverage':distributions[sc][idx]['coverage'],'median':distributions[sc][idx]['median']} for sc in SCALES}
        covs=[distributions[sc][idx]['coverage'] for sc in SCALES];meds=[distributions[sc][idx]['median'] for sc in SCALES if distributions[sc][idx]['median'] is not None]
        if covs and max(covs)-min(covs)>0.40:warnings.append(f'{idx} apresenta variação de cobertura superior a 40 pontos percentuais entre escalas.')
        if meds and max(meds)-min(meds)>35:warnings.append(f'{idx} apresenta variação de mediana superior a 35 pontos entre escalas. Confirmar efeito de escala antes da síntese.')
    tech_ok=all(c['pass'] for c in technical)
    if not tech_ok:blockers.insert(0,'Falha técnica ou de integridade em uma ou mais dimensões base.')
    # deduplicar mensagens preservando ordem
    warnings=list(dict.fromkeys(warnings));blockers=list(dict.fromkeys(blockers));conditions=list(dict.fromkeys(conditions))
    gate='PASS' if tech_ok and not blockers else 'BLOCKED'
    report={'audit':'V38.4.14 · Auditoria conjunta das sete dimensões base','version':FINAL_VERSION,'origin_version':EXPECTED_VERSION,'generated_at':now_iso(),'status':'PASS' if tech_ok else 'FAIL','synthesis_gate':{'status':gate,'blockers':blockers,'conditions':conditions},'dimensions':idxs,'scales_km2':list(SCALES),'technical_checks':technical,'base_final_audits':base_audits,'distributions':distributions,'complete_support':complete_support,'correlations':correlations,'border_effects':border_effects,'sensitivity':sensitivity,'scale_drift':scale_drift,'warnings':warnings,'protected_sha256_before':hashes,'methodological_guards':{'no_base_recalculation':True,'null_not_zero':True,'no_synthesis_index_calculated':True,'correlation_is_diagnostic_not_weighting':True,'edge_effect_is_diagnostic_not_correction':True}}
    out=repo/'AUDITORIA_V38_4_14_SETE_DIMENSOES.json';dump(out,report)
    dump(repo/'docs/dados/auditoria_sete_dimensoes_v38414.json',report)
    # CSV resumos
    rp=repo/'AUDITORIA_V38_4_14_RESUMO.csv';rp.parent.mkdir(parents=True,exist_ok=True)
    with rp.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['escala_km2','indice','n','nulls','coverage','min','p05','median','mean','p95','max','sd','n_unique','pct_100'])
        for sc in SCALES:
            for idx in idxs:
                s=distributions[sc][idx];w.writerow([sc,idx]+[s[k] for k in ['n','nulls','coverage','min','p05','median','mean','p95','max','sd','n_unique','pct_100']])
    cp=repo/'AUDITORIA_V38_4_14_CORRELACOES.csv'
    with cp.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['escala_km2','a','b','n_overlap','rho','support_jaccard','exact_equal_fraction','median_abs_diff']);w.writeheader()
        for sc in SCALES:
            for r in correlations[sc]:w.writerow({'escala_km2':sc,**r})
    hp=repo/'docs/documentos/auditoria-sete-dimensoes.html';hp.parent.mkdir(parents=True,exist_ok=True);hp.write_text(make_html(report),encoding='utf-8',newline='\n')
    if tech_ok:
        append_docs(repo,report);vf.write_text(FINAL_VERSION+'\n',encoding='utf-8',newline='\n')
    print(f'AUDITORIA CONJUNTA V38.4.14 · {report["status"]}')
    print(f'GATE DE SÍNTESE · {gate}')
    for sc in SCALES:
        cs=complete_support[sc];print(f'{sc} km² · células 7/7 = {cs["n_all_7"]}/{EXPECTED_COUNTS[sc]} ({100*cs["fraction_all_7"]:.2f}%)')
    if blockers:
        print('BLOQUEADORES ·')
        for x in blockers:print('  -',x)
    if warnings:print(f'AVISOS · {len(warnings)} · consultar relatório HTML/JSON')
    print('Relatório ·',out)
    return 0 if tech_ok else 3
if __name__=='__main__':raise SystemExit(main())
