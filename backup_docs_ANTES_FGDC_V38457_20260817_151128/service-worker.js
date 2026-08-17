const ITA_CACHE = 'ita-arandu-v38-4-56-coluna-estratigrafica';

/* Núcleo pequeno. A instalação da PWA nunca deve depender de GeoJSON pesados. */
const ITA_CORE = [
  "./assets/css/diagrama-rosas-v38454.css?v=38.4.54",
  "./assets/js/diagrama-rosas-v38454.js?v=38.4.54",
  "./documentos/metodologia-diagrama-rosas.html",
  "./assets/css/ondas-sismicas-v38453.css?v=38.4.53",
  "./assets/js/ondas-sismicas-v38453.js?v=38.4.53",
  "./documentos/metodologia-ondas-sismicas-acelerometro.html",
  "./assets/css/magnetometro-amostras-v38450.css?v=38.4.50",
  "./assets/js/magnetometro-amostras-v38450.js?v=38.4.52",
  "./documentos/metodologia-magnetometro-amostras.html",
  "./assets/css/bancada-educativa-v38449.css?v=38.4.49",
  "./assets/js/bancada-educativa-v38449.js?v=38.4.49",
  "./assets/css/bancada-system-v38448.css?v=38.4.48",
  "./assets/js/bancada-system-v38448.js?v=38.4.48",
  "./documentos/metodologia-saida-campo.html",
  "./assets/css/saida-campo-v38440.css?v=38.4.40",
  "./assets/js/saida-campo-v38440.js?v=38.4.40a",
  "./documentos/metodologia-macrogeo.html",
  "./assets/css/macrogeo-v38439.css?v=38.4.39",
  "./assets/js/macrogeo-v38439.js?v=38.4.39",
  "./assets/js/camera-core-v38439.js?v=38.4.39",
  "./assets/css/bancada-harmonizada-v38447.css?v=38.4.47",
  "./assets/js/bancada-harmonizada-v38447.js?v=38.4.47",
  './',
  './index.html',
  './manifest.webmanifest',
  './assets/css/ternario-usda-v38446.css?v=38.4.46e',
  './assets/js/ternario-usda-v38446f.js?v=38.4.46e',
  './documentos/metodologia-ternario-usda.html',
  './assets/css/atlas.css?v=38.4.26',
  './assets/css/design-system-v38424.css?v=38.4.26',
  './assets/js/map-fallback.js?v=38.4.26',
  './assets/js/app.js?v=38.4.45',
  './assets/js/campo-sensores.js?v=38.4.37f',
  './dados/meta.js?v=38.4.26',
  './referencias/referencias.js?v=38.4.26',
  './camadas/catalogo-local.js?v=38.4.45',
  './assets/css/coluna-estratigrafica-v38456.css?v=38.4.56',
  './assets/js/coluna-estratigrafica-v38456.js?v=38.4.56',
  './documentos/metodologia-coluna-estratigrafica.html',
  './assets/padroes/fgdc/601.svg',
  './assets/padroes/fgdc/603.svg',
  './assets/padroes/fgdc/607.svg',
  './assets/padroes/fgdc/609.svg',
  './assets/padroes/fgdc/616.svg',
  './assets/padroes/fgdc/620.svg',
  './assets/padroes/fgdc/627.svg',
  './assets/padroes/fgdc/642.svg',
  './assets/padroes/fgdc/658.svg',
  './assets/padroes/fgdc/667.svg',
  './assets/padroes/fgdc/702.svg',
  './assets/padroes/fgdc/705.svg',
  './assets/padroes/fgdc/708.svg',
  './assets/padroes/fgdc/711.svg',
  './assets/padroes/fgdc/717.svg'
];

self.addEventListener('install', event => {
  event.waitUntil((async()=>{
    const cache=await caches.open(ITA_CACHE);
    const results=await Promise.allSettled(ITA_CORE.map(async url=>{
      const req=new Request(url,{cache:'reload'});
      const res=await fetch(req);
      if(!res.ok)throw new Error(`HTTP ${res.status} · ${url}`);
      await cache.put(req,res.clone());
    }));
    const failed=results.filter(r=>r.status==='rejected');
    if(failed.length)console.warn('ITA ARANDU MS · precache parcial',failed);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(k=>k.startsWith('ita-arandu-')&&k!==ITA_CACHE).map(k=>caches.delete(k)));
    await self.clients.claim();
  })());
});

function isCritical(url){
  return url.pathname.endsWith('/index.html') ||
    url.pathname.endsWith('/manifest.webmanifest') ||
    url.pathname.includes('/assets/css/') ||
    url.pathname.includes('/assets/js/') ||
    url.pathname.endsWith('/dados/meta.js') ||
    url.pathname.endsWith('/dados/registros.js') ||
    url.pathname.includes('/dados/geometria-computacional/') ||
    url.pathname.includes('/referencias/referencias.js') ||
    url.pathname.includes('/indices/') ||
    url.pathname.endsWith('/camadas/catalogo-local.js') ||
    url.pathname.endsWith('/analytics/config.js');
}

async function networkFirst(req){
  const cache=await caches.open(ITA_CACHE);
  try{
    const res=await fetch(req,{cache:'no-store'});
    if(res.ok)await cache.put(req,res.clone());
    return res;
  }catch(err){
    const hit=await cache.match(req);
    if(hit)return hit;
    throw err;
  }
}

self.addEventListener('fetch', event => {
  const req=event.request;
  if(req.method!=='GET')return;
  const url=new URL(req.url);
  if(url.origin!==self.location.origin)return;

  if(req.mode==='navigate'){
    event.respondWith((async()=>{
      try{
        const res=await fetch(req,{cache:'no-store'});
        if(res.ok){const cache=await caches.open(ITA_CACHE);await cache.put(req,res.clone());}
        return res;
      }catch(_){
        const hit=await caches.match(req);
        if(hit)return hit;
        const shell=await caches.match('./index.html');
        if(shell)return shell;
        return new Response('Documento indisponível offline.',{status:503,headers:{'Content-Type':'text/plain; charset=utf-8'}});
      }
    })());
    return;
  }

  if(isCritical(url)){
    event.respondWith(networkFirst(req));
    return;
  }

  event.respondWith((async()=>{
    const hit=await caches.match(req);
    if(hit)return hit;
    const res=await fetch(req);
    if(res.ok&&(req.destination==='image'||req.destination==='font'||url.pathname.includes('/camadas/arquivos/'))){
      const cache=await caches.open(ITA_CACHE);
      await cache.put(req,res.clone());
    }
    return res;
  })());
});
