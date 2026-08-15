
from pathlib import Path
import argparse,json,hashlib,subprocess,shutil,re

FINAL="V38.4.33-CLINOMETRO-VISUAL-ARANDU-1.0-R2-20260815"
FINGERPRINTS=[
 "10.1016/j.cageo.2013.07.014",
 "10.1016/j.jsg.2017.02.015",
 "10.1016/j.jsg.2017.07.011",
 "10.1016/j.cageo.2019.104393",
 "https://www.w3.org/TR/orientation-event/"
]

def read(p):
    return Path(p).read_text(encoding="utf-8-sig")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    ap.add_argument("--catalog-sha")
    ap.add_argument("--manifest-sha")
    ap.add_argument("--master-sha")
    ap.add_argument("--ux-sha")
    a=ap.parse_args()

    r=Path(a.repo)
    checks=[]
    def ck(name,ok,detail=""):
        checks.append({"name":name,"pass":bool(ok),"detail":str(detail)})

    ck("version",read(r/"VERSION").strip()==FINAL,read(r/"VERSION").strip())

    idx=read(r/"docs/index.html")
    for token in [
        'id="abrirClinometroArandu"',
        'id="clinometroAranduModal"',
        'clinometro-visual-v38433.js?v=38.4.33r2',
        'clinometro-visual-v38433.css?v=38.4.33r2',
        'Metodologia + APA 7',
        'V38.4.33</title>'
    ]:
        ck("index_"+token,token in idx,token)

    js=r/"docs/assets/js/clinometro-visual-v38433.js"
    doc=r/"docs/documentos/metodologia-clinometro-visual-arandu.html"
    bib=r/"docs/referencias/index.html"
    side=r/"docs/documentos/clinometro-visual-referencias.json"

    ck("js_file",js.exists(),js)
    ck("methodology_file",doc.exists(),doc)
    ck("bibliography_file",bib.exists(),bib)
    ck("reference_sidecar",side.exists(),side)

    if js.exists():
        t=read(js)
        for token in [
            "devicePlane","Rz","Rx","Ry","circMean","circSd",
            "sensor_contato_dispositivo","estimativa_visual_assistida",
            "visual_camera_assisted_estimate","methodology_id"
        ]:
            ck("js_"+token,token in t,token)
        node=shutil.which("node")
        if node:
            p=subprocess.run([node,"--check",str(js)],capture_output=True,text=True)
            ck("node_syntax",p.returncode==0,p.stderr.strip())

    if doc.exists():
        t=read(doc)
        for token in [
            "R = Rz(α) · Rx(β) · Ry(γ)",
            "Referências · APA 7",
            "IDs no registro mestre",
            "Lee, S.","Novakova, L.","Allmendinger, R. W.",
            "Wang, J.","World Wide Web Consortium."
        ]:
            ck("methodology_"+token,token in t,token)

    if bib.exists():
        t=read(bib)
        ids=[int(x) for x in re.findall(r'id=["\']ref-(\d+)["\']',t,re.I)]
        unique=set(ids)
        ck("bib_unique_ids",len(ids)==len(unique),f"{len(ids)} entries / {len(unique)} unique")
        ck("bib_instrumentos",'id="instrumentos-campo"' in t)
        ck("bib_nav",'href="#instrumentos-campo"' in t)
        for fp in FINGERPRINTS:
            ck("bib_semantic_"+fp,fp.lower() in t.lower(),fp)
        m=re.search(r'(\d+)\s+referências no registro mestre',t)
        shown=int(m.group(1)) if m else -1
        ck("bib_dynamic_count",shown==len(unique),f"shown={shown} unique={len(unique)}")

    if side.exists():
        s=json.loads(read(side))
        refs=s.get("references",[])
        ck("sidecar_five_refs",len(refs)==5,len(refs))
        ck("sidecar_actual_ids",all(re.fullmatch(r"REF-\d+",x.get("ref_id","")) for x in refs))

    for expected,rel,name in [
        (a.catalog_sha,"docs/camadas/catalogo-local.json","catalog"),
        (a.manifest_sha,"docs/camadas/snapshots-manifest.json","manifest"),
        (a.master_sha,"docs/assets/js/campo-master-v38431.js","campo_master"),
        (a.ux_sha,"docs/assets/js/campo-ux-v38432.js","campo_ux")
    ]:
        if expected:
            p=r/rel
            h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
            ck(name+"_unchanged",h==expected,h)

    ok=all(x["pass"] for x in checks)
    out={
        "audit":"V38.4.33 Clinometro Visual ARANDU R2 adaptativo",
        "status":"PASS" if ok else "FAIL",
        "passed":sum(x["pass"] for x in checks),
        "total":len(checks),
        "checks":checks
    }
    (r/"AUDITORIA_V38_4_33_CLINOMETRO_R2.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps({"status":out["status"],"passed":out["passed"],"total":out["total"]},ensure_ascii=False,indent=2))
    if not ok:
        raise SystemExit(2)

if __name__=="__main__":
    main()
