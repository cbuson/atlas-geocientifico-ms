const ITA_CACHE = 'ita-arandu-ms-v35-beta-camadas-separadas-20260813';
const ITA_CORE = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./assets/css/atlas.css",
  "./assets/css/ajustes-v32.css",
  "./assets/css/pwa.css",
  "./assets/js/map-fallback.js",
  "./assets/js/bootstrap.js",
  "./assets/js/app.js",
  "./dados/meta.js",
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
  "./camadas/arquivos/mapa_geologico_ms.geojson"
];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(ITA_CACHE).then(cache=>cache.addAll(ITA_CORE)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('ita-arandu-ms-')&&key!==ITA_CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
  const req=event.request;
  if(req.method!=='GET')return;
  const url=new URL(req.url);
  if(url.origin!==self.location.origin)return;
  if(req.mode==='navigate'){
    event.respondWith(fetch(req).then(res=>{const copy=res.clone();caches.open(ITA_CACHE).then(cache=>cache.put('./index.html',copy));return res}).catch(()=>caches.match('./index.html')));
    return;
  }
  event.respondWith(caches.match(req).then(hit=>hit||fetch(req).then(res=>{if(res.ok&&(['script','style','image','font'].includes(req.destination)||url.pathname.includes('/camadas/arquivos/')||url.pathname.includes('/indices/'))){const copy=res.clone();caches.open(ITA_CACHE).then(cache=>cache.put(req,copy))}return res})));
});
