const ITA_CACHE = 'ita-arandu-v38-4-5-ux-campo02-sensores';
const ITA_CORE = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./assets/css/atlas.css",
  "./assets/css/ajustes-v32.css",
  "./assets/css/pwa.css",
  "./assets/css/aprender.css",
  "./assets/css/educacao-metodologia.css",
  "./assets/css/campo-sensores.css",
  "./assets/js/map-fallback.js",
  "./assets/js/bootstrap.js",
  "./assets/js/app.js",
  "./assets/js/campo-sensores.js",
  "./dados/meta.js",
  "./dados/geometria-computacional/registry.js",
  "./referencias/referencias.js",
  "./dados/registros.js",
  "./indices/imc-v32.js",
  "./camadas/catalogo-local.js",
  "./camadas/catalogo-local.json",
  "./camadas/index.html",
  "./documentos/index.html",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./camadas/arquivos/limite_ms_ibge_2025.geojson",
  "./camadas/arquivos/malha_r5_250km2.geojson",
  "./camadas/arquivos/malha_500km2.geojson",
  "./camadas/arquivos/malha_1000km2.geojson",
  "./camadas/arquivos/mapa_geologico_ms.geojson",
  "./referencias/index.html",
  "./referencias/bibliografia-camadas-indices.json",
  "./referencias/README.md",
  "./assets/css/dados-dashboard.css",
  "./analytics/config.js",
  "./icons/favicon-32.png",
  "./documentos/metodologia-educativa.html",
  "./documentos/fundamentos-evidencias-rastreabilidade.html",
  "./documentos/fundamentos-incerteza-inferencia.html",
  "./documentos/fundamentos-indices-produtos-derivados.html",
  "./documentos/metodologia-pag-etr.html",
  "./documentos/geoetica-governanca-dados.html",
  "./camadas/arquivos/localidades_indigenas_ibge.geojson",
  "./camadas/arquivos/localidades_quilombolas_ibge.geojson",
  "./camadas/arquivos/pag_etr_250km2.geojson",
  "./camadas/arquivos/pag_etr_500km2.geojson",
  "./camadas/arquivos/pag_etr_1000km2.geojson",
  "./camadas/arquivos/pag_etr_evidencia_m2_feixe_morros.geojson",
  "./camadas/arquivos/pag_etr_evidencia_m4_fosforitos.geojson",
  "./camadas/arquivos/pag_etr_pontos_fosforo.geojson",
  "./documentos/metodologia-geografia-territorio.html",
  "./documentos/metodologia-cartografia-geologica.html",
  "./documentos/metodologia-caderneta-campo.html",
  "./documentos/fontes.html",
  "./documentos/auditoria.html",
  "./documentos/changelog.html"];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(ITA_CACHE).then(cache=>cache.addAll(ITA_CORE)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('ita-arandu-')&&key!==ITA_CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
  const req=event.request;
  if(req.method!=='GET')return;
  const url=new URL(req.url);
  if(url.origin!==self.location.origin)return;
  if(req.mode==='navigate'){
    const scopePath=new URL(self.registration.scope).pathname.replace(/\/?$/,'/');
    const isAppShell=url.pathname===scopePath||url.pathname===scopePath+'index.html';
    event.respondWith(fetch(req).then(res=>{
      if(res.ok){const copy=res.clone();caches.open(ITA_CACHE).then(cache=>cache.put(req,copy));}
      return res;
    }).catch(async()=>{
      const hit=await caches.match(req);
      if(hit)return hit;
      if(isAppShell)return caches.match('./index.html');
      return new Response('Documento indisponível offline.',{status:503,headers:{'Content-Type':'text/plain; charset=utf-8'}});
    }));
    return;
  }
  event.respondWith(caches.match(req).then(hit=>hit||fetch(req).then(res=>{if(res.ok&&(['script','style','image','font'].includes(req.destination)||url.pathname.includes('/camadas/arquivos/')||url.pathname.includes('/indices/')||url.pathname.includes('/dados/geometria-computacional/'))){const copy=res.clone();caches.open(ITA_CACHE).then(cache=>cache.put(req,copy))}return res})));
});
