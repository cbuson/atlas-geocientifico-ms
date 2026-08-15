#!/usr/bin/env python3
from pathlib import Path
import argparse,re
EXPECTED='V38.4.21-PIG-PRIORIDADE-INVESTIGACAO-GEOCIENTIFICA-20260815'
FINAL='V38.4.22-AUDITORIA-ZERO-FINAL-INDICES-20260815'
TOKEN='38.4.22'

def rw(p,fn):
 p=Path(p);t=p.read_text(encoding='utf-8-sig');n=fn(t);p.write_text(n,encoding='utf-8',newline='\n')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
 cur=(repo/'VERSION').read_text(encoding='utf-8-sig').strip()
 if cur!=EXPECTED:raise RuntimeError(f'base incorreta: {cur}')
 # VERSION
 (repo/'VERSION').write_text(FINAL+'\n',encoding='utf-8',newline='\n')
 # index: synchronize visible title and all cache-busting tokens.
 def fix_index(t):
  t=re.sub(r'<title>ITA ARANDU MS · Atlas Geocientífico de Mato Grosso do Sul · V[^<]+</title>', '<title>ITA ARANDU MS · Atlas Geocientífico de Mato Grosso do Sul · V38.4.22</title>', t)
  t=re.sub(r'\?v=38\.4\.21', '?v=38.4.22', t)
  return t
 rw(repo/'docs/index.html',fix_index)
 # bootstrap query versions
 rw(repo/'docs/assets/js/bootstrap.js',lambda t:re.sub(r'\?v=38\.4\.21','?v=38.4.22',t))
 # service worker: repair legacy missing comma, synchronize cache token and include final audit report.
 def fix_sw(t):
  t=t.replace("ita-arandu-v38-4-21-pig-prioridade-investigacao","ita-arandu-v38-4-22-auditoria-zero-final-indices")
  t=re.sub(r'\?v=38\.4\.21','?v=38.4.22',t)
  t=re.sub(r'("\./documentos/changelog\.html")\s*("\./indices/ide-v38415\.js\?v=38\.4\.22")',r'\1,\n  \2',t)
  if './documentos/auditoria-zero-final-indices.html' not in t:
   t=t.replace('  "./documentos/metodologia-pig.html",','  "./documentos/metodologia-pig.html",\n  "./documentos/auditoria-zero-final-indices.html",')
  return t
 rw(repo/'docs/service-worker.js',fix_sw)
 # docs index
 def fix_docs(t):
  link='<p><a href="./auditoria-zero-final-indices.html">AUDITORIA ZERO FINAL · família de índices · V38.4.22</a></p>'
  if 'auditoria-zero-final-indices.html' not in t:t=t.replace('</body>',link+'</body>')
  return t
 rw(repo/'docs/documentos/index.html',fix_docs)
 # changelog md and html, without touching scientific snapshots.
 ch=repo/'CHANGELOG.md'
 ct=ch.read_text(encoding='utf-8-sig') if ch.exists() else ''
 note='''\n\n## V38.4.22 · 2026-08-15 · AUDITORIA ZERO FINAL DA FAMÍLIA DE ÍNDICES\n\n- Auditoria conjunta IMC, IOD, ICP, IGC, IGQ, IGF, ICS, IDE, ICG, VCG e PIG.\n- Nenhum índice científico é recalculado.\n- Corrige a sintaxe do precache PWA herdada entre changelog e IDE e sincroniza o versionamento técnico para V38.4.22.\n- A robustez do PIG em 250 km² permanece registrada como ressalva quando o cenário microgrid 5 km P95 altera mais de 25% das classes.\n- Front de Pareto permanece a saída científica primária do PIG.\n'''
 if 'V38.4.22 · 2026-08-15' not in ct:ch.write_text(ct.rstrip()+note+'\n',encoding='utf-8',newline='\n')
 hp=repo/'docs/documentos/changelog.html'
 if hp.exists():
  ht=hp.read_text(encoding='utf-8-sig')
  if 'V38.4.22' not in ht:
   sec='<section><h2>V38.4.22 · Auditoria ZERO final dos índices</h2><p>Auditoria conjunta de IMC a PIG. Nenhum snapshot científico foi recalculado. O precache PWA foi corrigido e o versionamento técnico sincronizado.</p></section>'
   ht=ht.replace('</body>',sec+'</body>');hp.write_text(ht,encoding='utf-8',newline='\n')
 print('PREPARACAO V38.4.22 · OK')
 return 0
if __name__=='__main__':raise SystemExit(main())
