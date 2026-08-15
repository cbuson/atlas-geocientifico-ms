
from pathlib import Path
import argparse,json,hashlib,subprocess,shutil
FINAL="V38.4.33-CLINOMETRO-VISUAL-ARANDU-1.0-20260815"
def read(p):return Path(p).read_text(encoding="utf-8-sig")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo",required=True);ap.add_argument("--catalog-sha");ap.add_argument("--manifest-sha");ap.add_argument("--master-sha");a=ap.parse_args()
    r=Path(a.repo);checks=[]
    def ck(n,c,d=""):checks.append({"name":n,"pass":bool(c),"detail":str(d)})
    ck("version",read(r/"VERSION").strip()==FINAL,read(r/"VERSION").strip())
    idx=read(r/"docs/index.html")
    for token in ['id="abrirClinometroArandu"','id="clinometroAranduModal"','clinometro-visual-v38433.js?v=38.4.33','clinometro-visual-v38433.css?v=38.4.33','Metodologia + APA 7','V38.4.33</title>']:ck("index_"+token,token in idx,token)
    js=r/"docs/assets/js/clinometro-visual-v38433.js";doc=r/"docs/documentos/metodologia-clinometro-visual-arandu.html";bib=r/"docs/referencias/index.html"
    ck("js",js.exists());ck("doc",doc.exists());ck("bib",bib.exists())
    if js.exists():
        t=read(js)
        for token in ["devicePlane","Rz","Rx","Ry","circMean","circSd","sensor_contato_dispositivo","estimativa_visual_assistida","visual_camera_assisted_estimate","methodology_id"]:ck("js_"+token,token in t,token)
        node=shutil.which("node")
        if node:
            p=subprocess.run([node,"--check",str(js)],capture_output=True,text=True);ck("node_syntax",p.returncode==0,p.stderr.strip())
    if doc.exists():
        t=read(doc)
        for token in ["R = Rz(α) · Rx(β) · Ry(γ)","Referências · APA 7","Lee, S.","Novakova, L.","Allmendinger, R. W.","Wang, J.","World Wide Web Consortium."]:ck("doc_"+token,token in t,token)
    if bib.exists():
        t=read(bib)
        for rid in range(174,179):ck("bib_ref_"+str(rid),f'id="ref-{rid}"' in t)
        ck("bib_count","176 referências no registro mestre" in t);ck("bib_instrumentos",'id="instrumentos-campo"' in t)
    for expected,rel,name in [(a.catalog_sha,"docs/camadas/catalogo-local.json","catalog"),(a.manifest_sha,"docs/camadas/snapshots-manifest.json","manifest"),(a.master_sha,"docs/assets/js/campo-master-v38431.js","master")]:
        if expected:
            p=r/rel;h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "";ck(name+"_unchanged",h==expected,h)
    ok=all(x["pass"] for x in checks)
    out={"audit":"V38.4.33 Clinometro Visual ARANDU","status":"PASS" if ok else "FAIL","passed":sum(x["pass"] for x in checks),"total":len(checks),"checks":checks}
    (r/"AUDITORIA_V38_4_33_CLINOMETRO.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"passed":out["passed"],"total":out["total"]},ensure_ascii=False,indent=2))
    if not ok:raise SystemExit(2)
if __name__=="__main__":main()
