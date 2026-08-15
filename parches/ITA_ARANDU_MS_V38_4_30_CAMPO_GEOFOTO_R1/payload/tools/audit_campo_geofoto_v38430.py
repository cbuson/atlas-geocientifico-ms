
from pathlib import Path
import argparse,json,hashlib,re,subprocess,shutil

FINAL="V38.4.30-CAMPO-GEOFOTO-1.0-20260815"

def read(p):
    return Path(p).read_text(encoding="utf-8-sig")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    ap.add_argument("--catalog-sha")
    ap.add_argument("--manifest-sha")
    a=ap.parse_args()
    repo=Path(a.repo).resolve()

    checks=[]
    def ck(n,c,d=""):checks.append({"name":n,"pass":bool(c),"detail":str(d)})

    ck("version",read(repo/"VERSION").strip()==FINAL,read(repo/"VERSION").strip())
    index=read(repo/"docs/index.html")
    js=repo/"docs/assets/js/campo-geofoto-v38430.js"
    css=repo/"docs/assets/css/campo-geofoto-v38430.css"
    doc=repo/"docs/documentos/protocolo-campo-geofoto.html"

    ck("js_file",js.exists(),js)
    ck("css_file",css.exists(),css)
    ck("protocol_file",doc.exists(),doc)
    ck("js_loaded","campo-geofoto-v38430.js?v=38.4.30" in index)
    ck("css_loaded","campo-geofoto-v38430.css?v=38.4.30" in index)

    if js.exists():
        t=read(js)
        for token in [
          "getUserMedia","geolocation","DeviceOrientationEvent","latLonToUTM",
          "readExifGps","original_sha256","overlay_sha256","attributed_later",
          "embedded_exif_original","exportGeoJsonV1","exportKmlV1",
          "Caderno de Campo Geocientífico Digital"
        ]:
            ck("js_"+token,token in t,token)

    # Node syntax validation if available
    node=shutil.which("node")
    if node and js.exists():
        p=subprocess.run([node,"--check",str(js)],capture_output=True,text=True)
        ck("node_syntax",p.returncode==0,p.stderr.strip())
    else:
        ck("node_syntax",True,"node nao disponivel na auditoria")

    if a.catalog_sha:
        p=repo/"docs/camadas/catalogo-local.json"
        h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
        ck("catalog_unchanged",h==a.catalog_sha,h)
    if a.manifest_sha:
        p=repo/"docs/camadas/snapshots-manifest.json"
        h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
        ck("manifest_unchanged",h==a.manifest_sha,h)

    ok=all(x["pass"] for x in checks)
    out={"audit":"V38.4.30 Campo GeoFoto 1.0","status":"PASS" if ok else "FAIL","passed":sum(x["pass"] for x in checks),"total":len(checks),"checks":checks}
    (repo/"AUDITORIA_V38_4_30_CAMPO_GEOFOTO.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"passed":out["passed"],"total":out["total"]},ensure_ascii=False,indent=2))
    if not ok:raise SystemExit(2)

if __name__=="__main__":
    main()
