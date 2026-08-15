
from pathlib import Path
import argparse,json,re,hashlib

FINAL='V38.4.29-MOBILE-MAP-TOOLS-INTEGRADOS-20260815'

def read(p):
    return Path(p).read_text(encoding='utf-8-sig')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True)
    ap.add_argument('--catalog-json-sha',required=False)
    ap.add_argument('--manifest-sha',required=False)
    a=ap.parse_args()
    repo=Path(a.repo).resolve()

    checks=[]
    def ck(name,ok,detail=''):
        checks.append({'name':name,'pass':bool(ok),'detail':str(detail)})

    ck('version',read(repo/'VERSION').strip()==FINAL,read(repo/'VERSION').strip())
    index=read(repo/'docs/index.html')
    app=read(repo/'docs/assets/js/app.js')
    cssp=repo/'docs/assets/css/mobile-map-toolbar-v38429.css'
    ck('css_file',cssp.exists(),cssp)
    ck('css_loaded','mobile-map-toolbar-v38429.css?v=38.4.29' in index)
    ck('old_floating_group_removed',not bool(re.search(r'<div class=["\']mobile-map-tools["\']',index,re.I)))
    ck('base_unique',index.count('id="mobileBaseBtn"')==1,index.count('id="mobileBaseBtn"'))
    ck('legend_unique',index.count('id="mobileLegendBtn"')==1,index.count('id="mobileLegendBtn"'))
    ck('base_integrated',bool(re.search(r'<div class=["\']map-toolbar["\'][\s\S]*?id=["\']mobileBaseBtn["\']',index,re.I)))
    ck('legend_integrated',bool(re.search(r'<div class=["\']map-toolbar["\'][\s\S]*?id=["\']mobileLegendBtn["\']',index,re.I)))
    ck('ms_outline','ita-ms-outline' in index)
    ck('legend_icon','aria-label="Abrir legenda cartografica"' in index)
    ck('reset_icon','id="resetView"' in index and 'ita-map-tool-icon' in index)
    ck('state_sync','V38.4.29 mobile map toolbar integrated' in app)
    css=read(cssp) if cssp.exists() else ''
    ck('mobile_integrated_rule','.mobile-integrated-tool' in css)
    ck('panels_left','.basemap-panel' in css and 'left:8px!important' in css)
    ck('narrow_phone_rule','@media(max-width:340px)' in css)

    if a.catalog_json_sha:
        p=repo/'docs/camadas/catalogo-local.json'
        h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ''
        ck('catalog_json_unchanged',h==a.catalog_json_sha,h)

    if a.manifest_sha:
        p=repo/'docs/camadas/snapshots-manifest.json'
        h=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ''
        ck('snapshot_manifest_unchanged',h==a.manifest_sha,h)

    ok=all(x['pass'] for x in checks)
    out={'audit':'V38.4.29 mobile map toolbar','status':'PASS' if ok else 'FAIL','passed':sum(x['pass'] for x in checks),'total':len(checks),'checks':checks}
    (repo/'AUDITORIA_V38_4_29_MOBILE_MAP_TOOLBAR.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],'passed':out['passed'],'total':out['total']},ensure_ascii=False,indent=2))
    if not ok:
        raise SystemExit(2)

if __name__=='__main__':
    main()
