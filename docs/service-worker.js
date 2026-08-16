const ITA_CACHE = 'ita-arandu-v38-4-37g-init-fix';

/* Núcleo pequeno. A instalação da PWA nunca deve depender de GeoJSON pesados. */
const ITA_CORE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './assets/css/atlas.css?v=38.4.26',
  './assets/css/design-system-v38424.css?v=38.4.26',
  './assets/js/map-fallback.js?v=38.4.26',
  './assets/js/app.js?v=38.4.37g',
  './assets/js/campo-sensores.js?v=38.4.37f',
  './dados/meta.js?v=38.4.26',
  './referencias/referencias.js?v=38.4.26',
  './camadas/catalogo-local.js?v=38.4.26'
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
