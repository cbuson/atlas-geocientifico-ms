
from pathlib import Path
import argparse,json,hashlib

FINAL="V38.4.37B-CONTADOR-VISITAS-SEPARADO-1.0-20260815"

def read(p):
    return Path(p).read_text(encoding="utf-8-sig")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    ap.add_argument("--catalog-sha",required=True)
    ap.add_argument("--manifest-sha",required=True)
    a=ap.parse_args()

    repo=Path(a.repo)
    checks=[]

    def ck(name,ok,detail=""):
        checks.append({"name":name,"pass":bool(ok),"detail":str(detail)})

    ck("version",read(repo/"VERSION").strip()==FINAL)

    index=read(repo/"docs/index.html")
    ck("tracker_preserved",'data-goatcounter="https://ita-arandu.goatcounter.com/count"' in index)
    ck("reader_removed",'contador-visitas-v38437a.js?v=38.4.37a' not in index)
    ck("visitas_link",'class="ita-visitas-link"' in index)
    ck("visitas_page",(repo/"docs/visitas/index.html").exists())

    if (repo/"docs/visitas/index.html").exists():
        v=read(repo/"docs/visitas/index.html")
        for token in ["Visitas do Atlas","visitas acumuladas","visitas hoje","últimos 7 dias","mês atual"]:
            ck("page_"+token,token in v,token)

    catalog=repo/"docs/camadas/catalogo-local.json"
    manifest=repo/"docs/camadas/snapshots-manifest.json"
    ck("catalog_unchanged",hashlib.sha256(catalog.read_bytes()).hexdigest()==a.catalog_sha)
    ck("manifest_unchanged",hashlib.sha256(manifest.read_bytes()).hexdigest()==a.manifest_sha)

    ok=all(x["pass"] for x in checks)
    result={
        "audit":"V38.4.37B contador separado",
        "status":"PASS" if ok else "FAIL",
        "passed":sum(x["pass"] for x in checks),
        "total":len(checks),
        "checks":checks
    }
    (repo/"AUDITORIA_V38_4_37B_CONTADOR_SEPARADO.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8"
    )
    print(json.dumps({
        "status":result["status"],
        "passed":result["passed"],
        "total":result["total"]
    },ensure_ascii=False,indent=2))
    if not ok:
        raise SystemExit(2)

if __name__=="__main__":
    main()
