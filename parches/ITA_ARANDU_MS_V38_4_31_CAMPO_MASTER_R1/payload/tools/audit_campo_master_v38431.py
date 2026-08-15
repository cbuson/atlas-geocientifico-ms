
from pathlib import Path
import argparse,json,hashlib,subprocess,shutil,re
FINAL="V38.4.31-CAMPO-MASTER-2.0-20260815"
def read(p):return Path(p).read_text(encoding="utf-8-sig")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--repo",required=True);ap.add_argument("--catalog-sha");ap.add_argument("--manifest-sha");a=ap.parse_args()
    r=Path(a.repo).resolve();checks=[]
    def ck(n,c,d=""):checks.append({"name":n,"pass":bool(c),"detail":str(d)})
    ck("version",read(r/"VERSION").strip()==FINAL,read(r/"VERSION").strip())
    idx=read(r/"docs/index.html")
    ck("single_campo_modal",idx.count('id="campoModal"')==1,idx.count('id="campoModal"'))
    ck("master_js_loaded","campo-master-v38431.js?v=38.4.31" in idx)
    ck("master_css_loaded","campo-master-v38431.css?v=38.4.31" in idx)
    ck("old_geofoto_not_loaded","campo-geofoto-v38430.js" not in idx)
    for token in ["campoModoEssencial","campoModoAvancado","campoAddMedida","campoAddAmostra","campoSketch","campoExportarPacote","campoMineraisPicker","campoEstadoFicha"]:
        ck("html_"+token,token in idx,token)
    js=r/"docs/assets/js/campo-master-v38431.js"
    ck("js_file",js.exists(),js)
    if js.exists():
        t=read(js)
        for token in ["ita_arandu_campo_master_v20","original_gps","latLonToUTM","municipios_limites_base.geojson","embedded_exif_original","attributed_later","makeZip","measurements","mineralization","geotechnics","sensitivity"]:
            ck("js_"+token,token in t,token)
        node=shutil.which("node")
        if node:
            p=subprocess.run([node,"--check",str(js)],capture_output=True,text=True)
            ck("node_syntax",p.returncode==0,p.stderr.strip())
    if a.catalog_sha:
        p=r/"docs/camadas/catalogo-local.json";h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "";ck("catalog_unchanged",h==a.catalog_sha,h)
    if a.manifest_sha:
        p=r/"docs/camadas/snapshots-manifest.json";h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "";ck("manifest_unchanged",h==a.manifest_sha,h)
    ok=all(x["pass"] for x in checks)
    out={"audit":"V38.4.31 Campo Master 2.0","status":"PASS" if ok else "FAIL","passed":sum(x["pass"] for x in checks),"total":len(checks),"checks":checks}
    (r/"AUDITORIA_V38_4_31_CAMPO_MASTER.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"passed":out["passed"],"total":out["total"]},ensure_ascii=False,indent=2))
    if not ok:raise SystemExit(2)
if __name__=="__main__":main()
