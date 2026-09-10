const ITA_CACHE = 'ita-arandu-v38458c-geoquimica';

/* Núcleo pequeno. A instalação da PWA nunca deve depender de GeoJSON pesados. */
const ITA_CORE = [
  "./assets/css/bancada-normalizacao-r9.css?v=9.0",
  "./assets/js/bancada-normalizacao-r9.js?v=9.0",
  "./assets/css/laboratorio-sed-hidro-r8.css?v=1.0.0",
  "./assets/js/laboratorio-sed-hidro-r8.js?v=1.0.0",
  "./documentos/metodologia-analise-granulometrica.html",
  "./documentos/metodologia-interpolacao-isopiezas.html",
  "./assets/css/bussola-mobile-r6.css?v=6.0",
  "./assets/js/bussola-mobile-r6.js?v=6.0",
  "./assets/css/diagrama-rosas-v38454.css?v=38.4.54",
  "./assets/js/diagrama-rosas-v38454.js?v=38.4.54",
  "./documentos/metodologia-diagrama-rosas.html",
  "./assets/css/ondas-sismicas-v38453.css?v=38.4.58B",
  "./assets/js/ondas-sismicas-v38453.js?v=38.4.58B",
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
  "./index.html",
  "./manifest.webmanifest",
  "./assets/css/ternario-usda-v38446.css?v=38.4.46e",
  "./assets/js/ternario-usda-v38446f.js?v=38.4.46e",
  "./documentos/metodologia-ternario-usda.html",
  "./assets/css/atlas.css?v=38.4.26",
  "./assets/css/design-system-v38424.css?v=38.4.26",
  "./assets/js/map-fallback.js?v=38.4.26",
  "./assets/js/app.js?v=38.4.58C",
  "./assets/js/campo-sensores.js?v=38.4.37f",
  "./dados/meta.js?v=38.4.58C",
  "./referencias/referencias.js?v=38.4.26",
  "./camadas/catalogo-local.js?v=38.4.45",
  "./assets/css/coluna-estratigrafica-v38457.css?v=38.4.57",
  "./assets/js/coluna-estratigrafica-v38457.js?v=38.4.57",
  "./documentos/metodologia-coluna-estratigrafica.html",
  "./assets/padroes/fgdc/601.svg",
  "./assets/padroes/fgdc/602.svg",
  "./assets/padroes/fgdc/603.svg",
  "./assets/padroes/fgdc/605.svg",
  "./assets/padroes/fgdc/606.svg",
  "./assets/padroes/fgdc/607.svg",
  "./assets/padroes/fgdc/608.svg",
  "./assets/padroes/fgdc/609.svg",
  "./assets/padroes/fgdc/610.svg",
  "./assets/padroes/fgdc/611.svg",
  "./assets/padroes/fgdc/612.svg",
  "./assets/padroes/fgdc/613.svg",
  "./assets/padroes/fgdc/614.svg",
  "./assets/padroes/fgdc/616.svg",
  "./assets/padroes/fgdc/617.svg",
  "./assets/padroes/fgdc/618.svg",
  "./assets/padroes/fgdc/619.svg",
  "./assets/padroes/fgdc/620.svg",
  "./assets/padroes/fgdc/621.svg",
  "./assets/padroes/fgdc/622.svg",
  "./assets/padroes/fgdc/623.svg",
  "./assets/padroes/fgdc/624.svg",
  "./assets/padroes/fgdc/625.svg",
  "./assets/padroes/fgdc/626.svg",
  "./assets/padroes/fgdc/627.svg",
  "./assets/padroes/fgdc/628.svg",
  "./assets/padroes/fgdc/629.svg",
  "./assets/padroes/fgdc/630.svg",
  "./assets/padroes/fgdc/631.svg",
  "./assets/padroes/fgdc/632.svg",
  "./assets/padroes/fgdc/633.svg",
  "./assets/padroes/fgdc/634.svg",
  "./assets/padroes/fgdc/635.svg",
  "./assets/padroes/fgdc/636.svg",
  "./assets/padroes/fgdc/637.svg",
  "./assets/padroes/fgdc/638.svg",
  "./assets/padroes/fgdc/639.svg",
  "./assets/padroes/fgdc/640.svg",
  "./assets/padroes/fgdc/641.svg",
  "./assets/padroes/fgdc/642.svg",
  "./assets/padroes/fgdc/643.svg",
  "./assets/padroes/fgdc/644.svg",
  "./assets/padroes/fgdc/645.svg",
  "./assets/padroes/fgdc/646.svg",
  "./assets/padroes/fgdc/647.svg",
  "./assets/padroes/fgdc/648.svg",
  "./assets/padroes/fgdc/649.svg",
  "./assets/padroes/fgdc/650.svg",
  "./assets/padroes/fgdc/651.svg",
  "./assets/padroes/fgdc/652.svg",
  "./assets/padroes/fgdc/653.svg",
  "./assets/padroes/fgdc/654.svg",
  "./assets/padroes/fgdc/655.svg",
  "./assets/padroes/fgdc/656.svg",
  "./assets/padroes/fgdc/657.svg",
  "./assets/padroes/fgdc/658.svg",
  "./assets/padroes/fgdc/659.svg",
  "./assets/padroes/fgdc/660.svg",
  "./assets/padroes/fgdc/661.svg",
  "./assets/padroes/fgdc/662.svg",
  "./assets/padroes/fgdc/663.svg",
  "./assets/padroes/fgdc/664.svg",
  "./assets/padroes/fgdc/665.svg",
  "./assets/padroes/fgdc/666.svg",
  "./assets/padroes/fgdc/667.svg",
  "./assets/padroes/fgdc/668.svg",
  "./assets/padroes/fgdc/669.svg",
  "./assets/padroes/fgdc/670.svg",
  "./assets/padroes/fgdc/671.svg",
  "./assets/padroes/fgdc/672.svg",
  "./assets/padroes/fgdc/673.svg",
  "./assets/padroes/fgdc/674.svg",
  "./assets/padroes/fgdc/675.svg",
  "./assets/padroes/fgdc/676.svg",
  "./assets/padroes/fgdc/677.svg",
  "./assets/padroes/fgdc/678.svg",
  "./assets/padroes/fgdc/679.svg",
  "./assets/padroes/fgdc/680.svg",
  "./assets/padroes/fgdc/681.svg",
  "./assets/padroes/fgdc/682.svg",
  "./assets/padroes/fgdc/683.svg",
  "./assets/padroes/fgdc/684.svg",
  "./assets/padroes/fgdc/685.svg",
  "./assets/padroes/fgdc/686.svg",
  "./assets/padroes/fgdc/701.svg",
  "./assets/padroes/fgdc/702.svg",
  "./assets/padroes/fgdc/703.svg",
  "./assets/padroes/fgdc/704.svg",
  "./assets/padroes/fgdc/705.svg",
  "./assets/padroes/fgdc/706.svg",
  "./assets/padroes/fgdc/707.svg",
  "./assets/padroes/fgdc/708.svg",
  "./assets/padroes/fgdc/709.svg",
  "./assets/padroes/fgdc/711.svg",
  "./assets/padroes/fgdc/712.svg",
  "./assets/padroes/fgdc/713.svg",
  "./assets/padroes/fgdc/714.svg",
  "./assets/padroes/fgdc/715.svg",
  "./assets/padroes/fgdc/716.svg",
  "./assets/padroes/fgdc/717.svg",
  "./assets/padroes/fgdc/719.svg",
  "./assets/padroes/fgdc/720.svg",
  "./assets/padroes/fgdc/721.svg",
  "./assets/padroes/fgdc/722.svg",
  "./assets/padroes/fgdc/723.svg",
  "./assets/padroes/fgdc/724.svg",
  "./assets/padroes/fgdc/725.svg",
  "./assets/padroes/fgdc/726.svg",
  "./assets/padroes/fgdc/727.svg",
  "./assets/padroes/fgdc/728.svg",
  "./assets/padroes/fgdc/729.svg",
  "./assets/padroes/fgdc/730.svg",
  "./assets/padroes/fgdc/731.svg",
  "./assets/padroes/fgdc/732.svg",
  "./assets/css/bancada-governanca-v38458.css",
  "./assets/js/licencas-citacao-v38458.js",
  "./documentos/politica-licencas-citacao.html",
  "./documentos/auditoria-bibliografica-zero-20260817.html",
  "./documentos/citacoes-ferramentas-indices.json",
  "./referencias/referencias.js",
  "./referencias/index.html",
  "./LICENSE-CONTENT.txt",
  "./LICENSE-SOFTWARE.txt",
  "./THIRD-PARTY-NOTICES.txt",
  "./dados/geometria-computacional/registry.js?v=38.4.26",
  "./dados/registros.js?v=38.4.26",
  "./indices/imc-v32.js?v=38.4.26",
  "./indices/iod-v3848.js?v=38.4.26",
  "./indices/icp-v3849.js?v=38.4.26",
  "./indices/igc-v38410.js?v=38.4.26",
  "./indices/igq-v38411.js?v=38.4.26",
  "./indices/igf-v38412.js?v=38.4.26",
  "./indices/ics-v38413.js?v=38.4.26",
  "./indices/ide-v38415.js?v=38.4.26",
  "./indices/icg-v38417.js?v=38.4.26",
  "./indices/vcg-v38419.js?v=38.4.26",
  "./indices/pig-v38421.js?v=38.4.26",
  "./camadas/proveniencia-snapshots.js?v=38.4.28",
  "./assets/js/proveniencia-v38428.js?v=38.4.40b",
  "./assets/js/campo-master-v38431.js?v=38.4.31",
  "./assets/js/campo-ux-v38432.js?v=38.4.32",
  "./assets/js/clinometro-visual-v38433.js?v=38.4.33r2",
  "./assets/js/geoetica-care-v38434.js?v=38.4.34",
  "./assets/js/ferramentas-hub-v38435.js?v=38.4.40a",
  "./assets/js/bussola-nivel-v38436.js?v=38.4.36",
  "./assets/js/bussola-arandu-r4.js?v=1.0.0",
  "./assets/js/estereograma-calculadora-v38437.js?v=38.4.37",
  "./assets/js/magnetometro-mapa-v38451.js?v=38.4.52",
  "./assets/js/rede-estereografica-v38455.js?v=38.4.55",
  "./assets/js/licencas-citacao-v38458.js?v=38.4.58",
  "./assets/js/correlacao-estratigrafica-v1.js?v=1.0.0",
  "./assets/js/geocamera-field-data-r1.js?v=1.0.0",
  "./assets/js/bussola-norte-r5.js?v=1.0.0",
  "./assets/js/bussola-mobile-r6.js?v=6.1",
  "./assets/js/bussola-profissional-r14.js?v=15.0",
  "./assets/css/ajustes-v32.css?v=38.4.26",
  "./icons/icon-192.png",
  "./icons/favicon-32.png",
  "./assets/css/pwa.css?v=38.4.26",
  "./assets/css/dados-dashboard.css?v=38.4.26",
  "./assets/css/aprender.css?v=38.4.26",
  "./assets/css/educacao-metodologia.css?v=38.4.26",
  "./assets/css/campo-sensores.css?v=38.4.26",
  "./assets/css/ux-master-v38426.css?v=38.4.26",
  "./assets/css/proveniencia-v38428.css?v=38.4.28",
  "./assets/css/mobile-map-toolbar-v38429.css?v=38.4.29",
  "./assets/css/campo-master-v38431.css?v=38.4.31",
  "./assets/css/campo-ux-v38432.css?v=38.4.32",
  "./assets/css/clinometro-visual-v38433.css?v=38.4.33r2",
  "./assets/css/geoetica-care-v38434.css?v=38.4.34",
  "./assets/css/ferramentas-hub-v38435.css?v=38.4.35",
  "./assets/css/bussola-nivel-v38436.css?v=38.4.36",
  "./assets/css/estereograma-calculadora-v38437.css?v=38.4.37",
  "./assets/css/magnetometro-mapa-v38451.css?v=38.4.51",
  "./assets/css/bancada-governanca-v38458.css?v=38.4.58",
  "./assets/css/correlacao-estratigrafica-v1.css?v=1.0.0",
  "./assets/css/mobile-polish-bancada-r1.css?v=1.0.0",
  "./assets/css/geocamera-field-data-r1.css?v=1.0.0",
  "./assets/css/bussola-norte-r5.css?v=1.0.0",
  "./assets/css/bussola-profissional-r14.css?v=15.0",
  "./assets/css/bussola-arandu-r4.css?v=1.0.0",
  "./assets/css/rede-estereografica-v38455.css?v=38.4.55",
  "./",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
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


