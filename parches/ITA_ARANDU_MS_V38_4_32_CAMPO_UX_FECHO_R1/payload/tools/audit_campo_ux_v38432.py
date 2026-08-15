
from pathlib import Path
import argparse,json,hashlib,subprocess,shutil,re

FINAL="V38.4.32-CAMPO-UX-FECHO-20260815"

def read(p): return Path(p).read_text(encoding="utf-8-sig")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    ap.add_argument("--catalog-sha")
    ap.add_argument("--manifest-sha")
    ap.add_argument("--master-js-sha")
    a=ap.parse_args()
    r=Path(a.repo).resolve()
    checks=[]
    def ck(name,ok,detail=""):checks.append({"name":name,"pass":bool(ok),"detail":str(detail)})

    ck("version",read(r/"VERSION").strip()==FINAL,read(r/"VERSION").strip())
    idx=read(r/"docs/index.html")

    ck("title_version","V38.4.32</title>" in idx)
    ck("visible_version_badge",'<span class="ita-version-badge">V38.4.32</span>' in idx)
    ck("caderno_functional",'<h3>Meu caderno</h3><span class="aprender-status functional">funcional</span>' in idx)
    ck("caderno_partial_removed",'<h3>Meu caderno</h3><span class="aprender-status partial">parcial</span>' not in idx)
    ck("ux_css_loaded","campo-ux-v38432.css?v=38.4.32" in idx)
    ck("ux_js_loaded","campo-ux-v38432.js?v=38.4.32" in idx)

    js=r/"docs/assets/js/campo-ux-v38432.js"
    css=r/"docs/assets/css/campo-ux-v38432.css"
    ck("ux_js_file",js.exists(),js)
    ck("ux_css_file",css.exists(),css)

    if js.exists():
        t=read(js)
        for token in [
          "Estudante · Essencial","Especialista · Avançado",
          "ita-section-body","data-ita-section-prev","data-ita-section-next",
          "improveCompletionText","openRelevantSectionFromChecklist",
          "max-width:760px"
        ]:
            ck("js_"+token,token in t,token)
        node=shutil.which("node")
        if node:
            p=subprocess.run([node,"--check",str(js)],capture_output=True,text=True)
            ck("node_syntax",p.returncode==0,p.stderr.strip())

    if css.exists():
        t=read(css)
        for token in [".ita-section-toggle",".ita-section-nav",".ita-campo-section.is-open","@media(max-width:760px)"]:
            ck("css_"+token,token in t,token)

    if a.catalog_sha:
        p=r/"docs/camadas/catalogo-local.json"
        h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
        ck("catalog_unchanged",h==a.catalog_sha,h)

    if a.manifest_sha:
        p=r/"docs/camadas/snapshots-manifest.json"
        h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
        ck("manifest_unchanged",h==a.manifest_sha,h)

    if a.master_js_sha:
        p=r/"docs/assets/js/campo-master-v38431.js"
        h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
        ck("campo_master_engine_unchanged",h==a.master_js_sha,h)

    ok=all(x["pass"] for x in checks)
    out={
      "audit":"V38.4.32 fechamento UX do Campo",
      "status":"PASS" if ok else "FAIL",
      "passed":sum(x["pass"] for x in checks),
      "total":len(checks),
      "checks":checks
    }
    (r/"AUDITORIA_V38_4_32_CAMPO_UX.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"passed":out["passed"],"total":out["total"]},ensure_ascii=False,indent=2))
    if not ok: raise SystemExit(2)

if __name__=="__main__": main()
