(function(){
'use strict';
const EXP_CACHE='ita-arandu-expedition-v38459';
const EXP_KEY='ita_arandu_expedition_v38459';
const FILES=[
  './camadas/arquivos/limite_ms_ibge_2025.geojson',
  './camadas/arquivos/municipios_limites_base.geojson',
  './camadas/arquivos/mapa_geologico_ms.geojson',
  './camadas/arquivos/malha_r5_250km2.geojson',
  './camadas/arquivos/malha_500km2.geojson',
  './camadas/arquivos/malha_1000km2.geojson',
  './camadas/arquivos/rodovias_estaduais_base.geojson',
  './camadas/arquivos/rodovias_federais_base.geojson',
  './documentos/protocolo-campo-master.html',
  './documentos/metodologia-saida-campo.html'
];
const OPTIONAL_REMOTE=[
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'
];
const $=id=>document.getElementById(id);
function bytes(n){if(!Number.isFinite(n))return '—';const u=['B','KB','MB','GB'];let i=0,x=n;while(x>=1024&&i<u.length-1){x/=1024;i++}return `${x.toFixed(i?1:0)} ${u[i]}`}
async function estimate(){
  const el=$('campoStorageStatus'),bar=$('campoStorageBar');
  if(!navigator.storage?.estimate){if(el)el.textContent='Este navegador não expõe estimativa de armazenamento.';return null}
  try{const e=await navigator.storage.estimate(),usage=e.usage||0,quota=e.quota||0,pct=quota?usage/quota*100:null,persisted=navigator.storage.persisted?await navigator.storage.persisted():null;
    if(el)el.textContent=`${bytes(usage)} usados de ${bytes(quota)}${Number.isFinite(pct)?` · ${pct.toFixed(1)}%`:''}${persisted===true?' · persistente':persisted===false?' · persistência não garantida':''}`;
    if(bar&&Number.isFinite(pct)){bar.style.width=Math.min(100,pct)+'%';bar.dataset.level=pct>=90?'critical':pct>=80?'high':pct>=60?'warn':'ok'}
    const warn=$('campoStorageWarning');if(warn){warn.textContent=pct>=90?'Armazenamento quase esgotado. Exporte um ZIP e libere espaço antes de registrar novas fotos.':pct>=80?'Espaço local elevado. Faça uma cópia de segurança antes da saída de campo.':''}
    return {usage,quota,pct,persisted};
  }catch(e){if(el)el.textContent='Não foi possível estimar o armazenamento · '+e.message;return null}
}
async function requestPersist(){
  const st=$('campoStorageStatus');if(!navigator.storage?.persist){if(st)st.textContent='Persistência de armazenamento não suportada neste navegador.';return}
  try{const ok=await navigator.storage.persist();if(st)st.textContent=ok?'Armazenamento persistente concedido pelo navegador.':'O navegador não concedeu persistência; mantenha cópias ZIP regulares.';await estimate()}catch(e){if(st)st.textContent='Não foi possível solicitar persistência · '+e.message}
}
function expStatus(msg,state=''){const e=$('campoExpeditionStatus');if(e){e.textContent=msg;e.dataset.state=state}}
async function verify(){
  if(!('caches'in window)){expStatus('Cache Storage não disponível neste navegador.','error');return false}
  const cache=await caches.open(EXP_CACHE);let ok=0;for(const u of FILES){if(await cache.match(new Request(new URL(u,location.href).href)))ok++}
  const ready=ok===FILES.length;const meta={version:'V38.4.59',ready,files_ok:ok,files_total:FILES.length,verified_at:new Date().toISOString()};localStorage.setItem(EXP_KEY,JSON.stringify(meta));
  expStatus(ready?`Pronto para campo offline ✓ · ${ok}/${FILES.length} recursos verificados.`:`Pacote incompleto · ${ok}/${FILES.length} recursos disponíveis.`,ready?'ready':'warn');
  return ready;
}
async function prepare(){
  if(!('caches'in window)){expStatus('Cache Storage não disponível neste navegador.','error');return}
  const btn=$('campoExpeditionPrepare'),progress=$('campoExpeditionProgress');if(btn)btn.disabled=true;expStatus('Preparando pacote Essencial de Campo…','pending');
  const cache=await caches.open(EXP_CACHE);let ok=0,failed=[];
  for(let i=0;i<FILES.length;i++){
    const u=FILES[i];try{const absolute=new URL(u,location.href).href,req=new Request(absolute,{cache:'reload',mode:absolute.startsWith(location.origin)?'same-origin':'cors'}),res=await fetch(req);if(!res.ok)throw new Error(`HTTP ${res.status}`);await cache.put(req,res.clone());ok++}catch(e){failed.push(`${u}: ${e.message}`)}
    if(progress){progress.max=FILES.length;progress.value=i+1}expStatus(`Baixando pacote offline · ${i+1}/${FILES.length}`,'pending');
  }
  let optionalOk=0;
  for(const u of OPTIONAL_REMOTE){try{const req=new Request(u,{cache:'reload',mode:'cors'}),res=await fetch(req);if(res.ok){await cache.put(req,res.clone());optionalOk++}}catch(_){}}
  if(btn)btn.disabled=false;await estimate();const ready=await verify();
  if(ready&&optionalOk<OPTIONAL_REMOTE.length)expStatus(`Pronto para campo offline ✓ · ${ok}/${FILES.length} recursos locais verificados. Base Leaflet externa: cache opcional ${optionalOk}/${OPTIONAL_REMOTE.length}.`,'ready');
  if(!ready&&failed.length)expStatus(`Pacote parcial · ${ok}/${FILES.length}. ${failed[0]}`,'warn');
}
async function removePackage(){if(!('caches'in window))return;await caches.delete(EXP_CACHE);localStorage.removeItem(EXP_KEY);const p=$('campoExpeditionProgress');if(p)p.value=0;expStatus('Pacote offline removido deste dispositivo.','');await estimate()}
async function refresh(){await estimate();try{await verify()}catch(_){}}
function wire(){
  $('campoStoragePersist')?.addEventListener('click',requestPersist);$('campoExpeditionPrepare')?.addEventListener('click',prepare);$('campoExpeditionVerify')?.addEventListener('click',verify);$('campoExpeditionRemove')?.addEventListener('click',removePackage);
  window.addEventListener('online',()=>{const e=$('campoNetworkStatus');if(e)e.textContent='Rede disponível'});window.addEventListener('offline',()=>{const e=$('campoNetworkStatus');if(e)e.textContent='Sem rede · usando recursos locais'});
  const e=$('campoNetworkStatus');if(e)e.textContent=navigator.onLine?'Rede disponível':'Sem rede · usando recursos locais';refresh();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
window.ITA_FIELD_ROBUSTNESS={version:'V38.4.59',files:FILES,optionalRemote:OPTIONAL_REMOTE,refreshStorage:estimate,verifyExpedition:verify,prepareExpedition:prepare};
})();
