const ITA_CACHE = 'ita-arandu-bussola-mobile-r6';

/* Núcleo pequeno. A instalação da PWA nunca deve depender de GeoJSON pesados. */
const ITA_CORE = [
  './assets/css/bussola-mobile-r6.css?v=6.0',
  './assets/js/bussola-mobile-r6.js?v=6.0',
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
  './assets/css/coluna-estratigrafica-v38457.css?v=38.4.57',
  './assets/js/coluna-estratigrafica-v38457.js?v=38.4.57',
  './documentos/metodologia-coluna-estratigrafica.html',
  './assets/padroes/fgdc/601.svg',
  './assets/padroes/fgdc/602.svg',
  './assets/padroes/fgdc/603.svg',
  './assets/padroes/fgdc/605.svg',
  './assets/padroes/fgdc/606.svg',
  './assets/padroes/fgdc/607.svg',
  './assets/padroes/fgdc/608.svg',
  './assets/padroes/fgdc/609.svg',
  './assets/padroes/fgdc/610.svg',
  './assets/padroes/fgdc/611.svg',
  './assets/padroes/fgdc/612.svg',
  './assets/padroes/fgdc/613.svg',
  './assets/padroes/fgdc/614.svg',
  './assets/padroes/fgdc/616.svg',
  './assets/padroes/fgdc/617.svg',
  './assets/padroes/fgdc/618.svg',
  './assets/padroes/fgdc/619.svg',
  './assets/padroes/fgdc/620.svg',
  './assets/padroes/fgdc/621.svg',
  './assets/padroes/fgdc/622.svg',
  './assets/padroes/fgdc/623.svg',
  './assets/padroes/fgdc/624.svg',
  './assets/padroes/fgdc/625.svg',
  './assets/padroes/fgdc/626.svg',
  './assets/padroes/fgdc/627.svg',
  './assets/padroes/fgdc/628.svg',
  './assets/padroes/fgdc/629.svg',
  './assets/padroes/fgdc/630.svg',
  './assets/padroes/fgdc/631.svg',
  './assets/padroes/fgdc/632.svg',
  './assets/padroes/fgdc/633.svg',
  './assets/padroes/fgdc/634.svg',
  './assets/padroes/fgdc/635.svg',
  './assets/padroes/fgdc/636.svg',
  './assets/padroes/fgdc/637.svg',
  './assets/padroes/fgdc/638.svg',
  './assets/padroes/fgdc/639.svg',
  './assets/padroes/fgdc/640.svg',
  './assets/padroes/fgdc/641.svg',
  './assets/padroes/fgdc/642.svg',
  './assets/padroes/fgdc/643.svg',
  './assets/padroes/fgdc/644.svg',
  './assets/padroes/fgdc/645.svg',
  './assets/padroes/fgdc/646.svg',
  './assets/padroes/fgdc/647.svg',
  './assets/padroes/fgdc/648.svg',
  './assets/padroes/fgdc/649.svg',
  './assets/padroes/fgdc/650.svg',
  './assets/padroes/fgdc/651.svg',
  './assets/padroes/fgdc/652.svg',
  './assets/padroes/fgdc/653.svg',
  './assets/padroes/fgdc/654.svg',
  './assets/padroes/fgdc/655.svg',
  './assets/padroes/fgdc/656.svg',
  './assets/padroes/fgdc/657.svg',
  './assets/padroes/fgdc/658.svg',
  './assets/padroes/fgdc/659.svg',
  './assets/padroes/fgdc/660.svg',
  './assets/padroes/fgdc/661.svg',
  './assets/padroes/fgdc/662.svg',
  './assets/padroes/fgdc/663.svg',
  './assets/padroes/fgdc/664.svg',
  './assets/padroes/fgdc/665.svg',
  './assets/padroes/fgdc/666.svg',
  './assets/padroes/fgdc/667.svg',
  './assets/padroes/fgdc/668.svg',
  './assets/padroes/fgdc/669.svg',
  './assets/padroes/fgdc/670.svg',
  './assets/padroes/fgdc/671.svg',
  './assets/padroes/fgdc/672.svg',
  './assets/padroes/fgdc/673.svg',
  './assets/padroes/fgdc/674.svg',
  './assets/padroes/fgdc/675.svg',
  './assets/padroes/fgdc/676.svg',
  './assets/padroes/fgdc/677.svg',
  './assets/padroes/fgdc/678.svg',
  './assets/padroes/fgdc/679.svg',
  './assets/padroes/fgdc/680.svg',
  './assets/padroes/fgdc/681.svg',
  './assets/padroes/fgdc/682.svg',
  './assets/padroes/fgdc/683.svg',
  './assets/padroes/fgdc/684.svg',
  './assets/padroes/fgdc/685.svg',
  './assets/padroes/fgdc/686.svg',
  './assets/padroes/fgdc/701.svg',
  './assets/padroes/fgdc/702.svg',
  './assets/padroes/fgdc/703.svg',
  './assets/padroes/fgdc/704.svg',
  './assets/padroes/fgdc/705.svg',
  './assets/padroes/fgdc/706.svg',
  './assets/padroes/fgdc/707.svg',
  './assets/padroes/fgdc/708.svg',
  './assets/padroes/fgdc/709.svg',
  './assets/padroes/fgdc/711.svg',
  './assets/padroes/fgdc/712.svg',
  './assets/padroes/fgdc/713.svg',
  './assets/padroes/fgdc/714.svg',
  './assets/padroes/fgdc/715.svg',
  './assets/padroes/fgdc/716.svg',
  './assets/padroes/fgdc/717.svg',
  './assets/padroes/fgdc/719.svg',
  './assets/padroes/fgdc/720.svg',
  './assets/padroes/fgdc/721.svg',
  './assets/padroes/fgdc/722.svg',
  './assets/padroes/fgdc/723.svg',
  './assets/padroes/fgdc/724.svg',
  './assets/padroes/fgdc/725.svg',
  './assets/padroes/fgdc/726.svg',
  './assets/padroes/fgdc/727.svg',
  './assets/padroes/fgdc/728.svg',
  './assets/padroes/fgdc/729.svg',
  './assets/padroes/fgdc/730.svg',
  './assets/padroes/fgdc/731.svg',
  './assets/padroes/fgdc/732.svg',
  './assets/css/bancada-governanca-v38458.css',
  './assets/js/licencas-citacao-v38458.js',
  './documentos/politica-licencas-citacao.html',
  './documentos/auditoria-bibliografica-zero-20260817.html',
  './documentos/citacoes-ferramentas-indices.json',
  './referencias/referencias.js',
  './referencias/index.html',
  './LICENSE-CONTENT.txt',
  './LICENSE-SOFTWARE.txt',
  './THIRD-PARTY-NOTICES.txt',
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

