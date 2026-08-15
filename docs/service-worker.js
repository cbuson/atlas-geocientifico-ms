const ITA_CACHE = 'ita-arandu-v38-4-24-design-system-tipografia';
const ITA_CORE = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./assets/css/atlas.css?v=38.4.24",
  "./assets/css/ajustes-v32.css?v=38.4.24",
  "./assets/css/pwa.css?v=38.4.24",
  "./assets/css/aprender.css?v=38.4.24",
  "./assets/css/educacao-metodologia.css?v=38.4.24",
  "./assets/css/campo-sensores.css?v=38.4.24",
  "./assets/css/design-system-v38424.css?v=38.4.24",
  "./assets/css/dados-dashboard.css?v=38.4.24",
  "./assets/js/map-fallback.js?v=38.4.24",
  "./assets/js/bootstrap.js?v=38.4.24",
  "./assets/js/app.js?v=38.4.24",
  "./assets/js/campo-sensores.js?v=38.4.24",
  "./dados/meta.js?v=38.4.24",
  "./dados/geometria-computacional/registry.js?v=38.4.24",
  "./referencias/referencias.js?v=38.4.24",
  "./dados/registros.js?v=38.4.24",
  "./indices/imc-v32.js?v=38.4.24",
  "./indices/iod-v3848.js?v=38.4.24",
  "./indices/icp-v3849.js?v=38.4.24",
  "./indices/igc-v38410.js?v=38.4.24",
  "./indices/igq-v38411.js?v=38.4.24",
  "./documentos/metodologia-igf.html",
  "./camadas/arquivos/magnetotelurico_sgb_ms.geojson",
  "./camadas/arquivos/gravimetria_sgb_ms.geojson",
  "./camadas/arquivos/aerogeofisica_projetos_sgb_ms.geojson",
  "./indices/igf-v38412.js?v=38.4.24",
  "./documentos/metodologia-ics.html",
  "./camadas/arquivos/rimas_pocos_monitoramento_ms.geojson",
  "./camadas/arquivos/siagas_pocos_ms.geojson",
  "./indices/ics-v38413.js?v=38.4.24",
  "./camadas/catalogo-local.js?v=38.4.24",
  "./analytics/config.js?v=38.4.24",
  "./camadas/catalogo-local.json",
  "./camadas/index.html",
  "./documentos/index.html",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/favicon-32.png",
  "./camadas/arquivos/limite_ms_ibge_2025.geojson",
  "./camadas/arquivos/malha_r5_250km2.geojson",
  "./camadas/arquivos/malha_500km2.geojson",
  "./camadas/arquivos/malha_1000km2.geojson",
  "./camadas/arquivos/mapa_geologico_ms.geojson",
  "./camadas/arquivos/afloramentos_geosgb_ms.geojson",
  "./camadas/arquivos/petrografia_geosgb_ms.geojson",
  "./camadas/arquivos/geocronologia_geosgb_ms.geojson",
  "./camadas/arquivos/geoquimica_amostras_sgb_ms.geojson",
  "./referencias/index.html",
  "./referencias/bibliografia-camadas-indices.json",
  "./referencias/README.md",
  "./documentos/metodologia-educativa.html",
  "./documentos/fundamentos-evidencias-rastreabilidade.html",
  "./documentos/fundamentos-incerteza-inferencia.html",
  "./documentos/fundamentos-indices-produtos-derivados.html",
  "./documentos/metodologia-iod.html",
  "./documentos/metodologia-icp.html",
  "./documentos/metodologia-igc.html",
  "./documentos/metodologia-igq.html",
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
  "./documentos/changelog.html",
  "./documentos/design-system-v38424.html",
  "./indices/ide-v38415.js?v=38.4.24",
  "./documentos/metodologia-ide.html",
  "./indices/politica-sintese-v384142.json",
  "./indices/icg-v38417.js?v=38.4.24",
  "./documentos/metodologia-icg.html",
  "./indices/politica-icg-v38416.json",
  "./indices/vcg-v38419.js?v=38.4.24",
  "./documentos/metodologia-vcg.html",
  "./indices/politica-vcg-v38418.json",
  "./indices/pig-v38421.js?v=38.4.24",
  "./documentos/metodologia-pig.html",
  "./documentos/auditoria-zero-final-indices.html",
  "./indices/politica-pig-v38420.json",
];

self.addEventListener('install', event => {
  event.waitUntil((async()=>{
    const cache=await caches.open(ITA_CACHE);
    await Promise.all(ITA_CORE.map(async url=>{
      const req=new Request(url,{cache:'reload'});
      const res=await fetch(req);
      if(!res.ok)throw new Error(`Falha no precache ${url} · HTTP ${res.status}`);
      await cache.put(req,res.clone());
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(key=>key.startsWith('ita-arandu-')&&key!==ITA_CACHE).map(key=>caches.delete(key)));
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
      const cache=await caches.open(ITA_CACHE);await cache.put(req,res.clone());
    }
    return res;
  })());
});
