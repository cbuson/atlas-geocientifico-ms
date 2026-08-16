
from pathlib import Path
import argparse,json,hashlib,subprocess,shutil,re
FINAL="V38.4.37A-CONTADOR-VISITAS-1.0-20260815"
def read(p):return Path(p).read_text(encoding="utf-8-sig")
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--repo",required=True);ap.add_argument("--catalog-sha");ap.add_argument("--manifest-sha");ap.add_argument("--master-sha");ap.add_argument("--struct-sha");a=ap.parse_args()
 r=Path(a.repo);checks=[]
 def ck(n,c,d=""):checks.append({"name":n,"pass":bool(c),"detail":str(d)})
 ck("version",read(r/"VERSION").strip()==FINAL,read(r/"VERSION").strip())
 idx=read(r/"docs/index.html")
 for tok in ['data-goatcounter=','count.v5.js','contador-visitas-v38437a.js?v=38.4.37a','V38.4.37A']:ck("index_"+tok,tok in idx,tok)
 js=r/"docs/assets/js/contador-visitas-v38437a.js";ck("js_exists",js.exists())
 if js.exists():
  t=read(js)
  for tok in ["counter/TOTAL.json","visitas acumuladas","visitas hoje","últimos 7 dias","mês atual","credentials:'omit'"]:ck("js_"+tok,tok in t,tok)
  ck("no_token","Bearer " not in t and "api/v0" not in t)
  node=shutil.which("node")
  if node:
   p=subprocess.run([node,"--check",str(js)],capture_output=True,text=True);ck("node",p.returncode==0,p.stderr.strip())
 for rel in ["docs/documentos/metodologia-contador-visitas.html","docs/documentos/contador-visitas-referencias.json"]:ck("file_"+rel,(r/rel).exists(),rel)
 bib=read(r/"docs/referencias/index.html");ck("bib_goatcounter","goatcounter.com/help/visitor-counter" in bib.lower())
 ids=[int(x) for x in re.findall(r'id=["\']ref-(\d+)["\']',bib,re.I)];ck("bib_unique",len(ids)==len(set(ids)),f"{len(ids)}/{len(set(ids))}")
 for expected,rel,name in [(a.catalog_sha,"docs/camadas/catalogo-local.json","catalog"),(a.manifest_sha,"docs/camadas/snapshots-manifest.json","manifest"),(a.master_sha,"docs/assets/js/campo-master-v38431.js","master"),(a.struct_sha,"docs/assets/js/estereograma-calculadora-v38437.js","struct")]:
  if expected:
   p=r/rel;h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "";ck(name+"_unchanged",h==expected,h)
 ok=all(x["pass"] for x in checks);out={"audit":"V38.4.37A Contador de visitas","status":"PASS" if ok else "FAIL","passed":sum(x["pass"] for x in checks),"total":len(checks),"checks":checks}
 (r/"AUDITORIA_V38_4_37A_CONTADOR_VISITAS.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":out["status"],"passed":out["passed"],"total":out["total"]},ensure_ascii=False,indent=2))
 if not ok:raise SystemExit(2)
if __name__=="__main__":main()
