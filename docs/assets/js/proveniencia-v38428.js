(function(){
'use strict';
const PREFIX='ita-arandu-source-mode:';
const esc=s=>String(s??'').replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[m]));
const map=()=>window.ITA_LAYER_PROVENANCE||{};
const meta=cfg=>map()[cfg?.id]||{};
function hasLocal(cfg){const m=meta(cfg);return !!(m.has_local||window.ATLAS_DATA?.[cfg?.id]||window.ITA_COMPRESSED_LAYERS?.[cfg?.id])}
function hasOnline(cfg){const m=meta(cfg);return !!(m.online_query_url||cfg?.remote_type||cfg?.status==='conectada')}
function sourceUrl(cfg){const m=meta(cfg);if(m.source_url)return m.source_url;if(cfg?.source_url)return cfg.source_url;const ids=window.ITA_LAYER_REFERENCE_LINKS?.[cfg?.id]||cfg?.reference_ids||[];return ids.map(id=>window.ITA_REFERENCE_REGISTRY?.find(r=>r.id===id)?.url).find(Boolean)||''}
function modeFor(cfg){const l=hasLocal(cfg),o=hasOnline(cfg);if(l&&o){const saved=localStorage.getItem(PREFIX+cfg.id);return saved==='online'?'online':'local'}if(l)return'local';if(o)return'online';return'auto'}
function setMode(id,mode){if(mode==='local'||mode==='online')localStorage.setItem(PREFIX+id,mode);else localStorage.removeItem(PREFIX+id);document.dispatchEvent(new CustomEvent('ita:layer-source-mode',{detail:{id,mode}}));queueDecorate()}
function capability(cfg){
 const m=meta(cfg),s=m.provenance_status||'';
 if(s==='fonte_online_instavel')return{cls:'warn',label:'ONLINE INSTÁVEL'};
 if(s==='fonte_online_atual_sem_cobertura_espacial_ms')return{cls:'warn',label:'SEM COBERTURA ATUAL'};
 if(s==='consulta_oficial_atual_zero_ms')return{cls:'online',label:'ONLINE · 0 EM MS'};
 if(m.source_type==='derivada_local')return{cls:'local',label:'LOCAL · DERIVADA'};
 if(m.source_type==='normativa_documental')return{cls:'local',label:'LOCAL · DOCUMENTAL'};
 const l=hasLocal(cfg),o=hasOnline(cfg);
 if(l&&o)return{cls:'both',label:'LOCAL + ONLINE'};
 if(l&&m.metadata_complete)return{cls:'local',label:'LOCAL'};
 if(l)return{cls:'warn',label:'LOCAL · PROVENIÊNCIA PARCIAL'};
 if(o)return{cls:'online',label:'ONLINE'};
 if(cfg?.status==='disponivel_para_captura')return{cls:'warn',label:'CAPTURA PENDENTE'};
 return{cls:'warn',label:'EM DESENVOLVIMENTO'};
}
function captureDate(cfg,data){const m=meta(cfg);return data?.atlas_metadata?.capturado_em||m.capture_date||cfg?.capture_date||cfg?.capturado_em||''}
function dateLabel(v){if(!v)return'';const raw=String(v),iso=raw.match(/^(\d{4})-(\d{2})-(\d{2})/);return iso?`${iso[3]}/${iso[2]}/${iso[1]}`:raw}
function captureDateLabel(cfg,data){return dateLabel(captureDate(cfg,data))}
function statusNote(cfg){
 const m=meta(cfg),s=m.provenance_status||'';
 if(s==='fonte_online_instavel')return'Fonte oficial localizada, mas o serviço respondeu com timeout nas consultas controladas.';
 if(s==='fonte_online_atual_sem_cobertura_espacial_ms')return'A fonte online consultada atualmente não apresenta cobertura espacial de Mato Grosso do Sul.';
 if(s==='consulta_oficial_atual_zero_ms')return'A consulta oficial controlada atual retornou zero registros para Mato Grosso do Sul.';
 if(m.source_type==='derivada_local')return'Produto derivado local. A rastreabilidade depende dos insumos, método, versão e SHA256, não de uma data de descarga externa.';if(s==='local_operacional_com_snapshot_oficial_e_online')return'A camada operacional local foi preservada. O snapshot oficial capturado em 15/08/2026 permanece separado porque o esquema bruto da fonte pode diferir do esquema normalizado usado pelo Atlas.';
 if(m.scientific_cut_relation==='snapshot_operacional_atualizado_apos_indices_precalculados')return'Snapshot operacional atualizado após o corte dos índices precalculados. Os índices fechados não foram recalculados por esta atualização.';
 if(hasLocal(cfg)&&!m.metadata_complete)return'Snapshot legado preservado. A procedência ainda não está documentalmente completa.';
 return'';
}
function cardHtml(cfg){
 const m=meta(cfg),cap=capability(cfg),mode=modeFor(cfg),url=sourceUrl(cfg),date=captureDateLabel(cfg),note=statusNote(cfg);
 let h=`<div class="ita-prov" data-prov-layer="${esc(cfg.id)}"><div class="ita-prov-badges"><span class="ita-prov-badge ${cap.cls}">${cap.label}</span>`;
 if(mode==='local'&&hasLocal(cfg))h+=`<span class="ita-prov-badge local">snapshot em uso</span>`;
 if(mode==='online'&&hasOnline(cfg))h+=`<span class="ita-prov-badge online">fonte atual em uso</span>`;
 h+='</div>';
 if(date)h+=`<div class="ita-prov-line"><span class="ita-prov-k">Captura</span><span class="ita-prov-v">${esc(date)}</span></div>`;
 if(m.local_feature_count!==null&&m.local_feature_count!==undefined)h+=`<div class="ita-prov-line"><span class="ita-prov-k">Registros locais</span><span class="ita-prov-v">${esc(m.local_feature_count)}</span></div>`;if(m.official_snapshot_capture_date)h+=`<div class="ita-prov-line"><span class="ita-prov-k">Snapshot oficial</span><span class="ita-prov-v">${esc(dateLabel(m.official_snapshot_capture_date))}${m.official_snapshot_feature_count!==null&&m.official_snapshot_feature_count!==undefined?' · '+esc(m.official_snapshot_feature_count)+' registros':''}</span></div>`;
 if(m.online_check_date)h+=`<div class="ita-prov-line"><span class="ita-prov-k">Verificação online</span><span class="ita-prov-v">${esc(dateLabel(m.online_check_date))}</span></div>`;
 if(m.snapshot_sha256)h+=`<div class="ita-prov-line"><span class="ita-prov-k">SHA256</span><span class="ita-prov-v">${esc(m.snapshot_sha256.slice(0,16))}…</span></div>`;
 if(note)h+=`<div class="ita-prov-note ${cap.cls==='warn'?'ita-prov-warn':''}">${esc(note)}</div>`;
 h+='<div class="ita-prov-actions">';
 if(hasLocal(cfg)&&hasOnline(cfg)){h+=`<button type="button" data-prov-mode="local" class="${mode==='local'?'active':''}">Usar snapshot local</button><button type="button" data-prov-mode="online" class="${mode==='online'?'active':''}">Usar fonte online</button>`}
 if(url)h+=`<a href="${esc(url)}" target="_blank" rel="noopener">Abrir fonte oficial</a>`;
 h+='</div></div>';
 return h
}
function bindCard(card,cfg){card.querySelectorAll('[data-prov-mode]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();setMode(cfg.id,b.dataset.provMode)}))}
function onlineCfg(cfg){const m=meta(cfg);if(!m.online_query_url)return cfg;return{...cfg,remote_type:m.online_remote_type||'arcgis_geojson',remote_url:m.online_query_url,remote_paged:m.online_remote_paged!==false,remote_filter_ms:m.remote_filter_ms??cfg.remote_filter_ms}}
const loading=new Map();
async function loadLocal(cfg){if(window.ATLAS_DATA?.[cfg.id])return window.ATLAS_DATA[cfg.id];if(window.ITA_COMPRESSED_LAYERS?.[cfg.id])return null;const m=meta(cfg),file=cfg.file||m.local_file;if(!file)return null;if(loading.has(cfg.id))return loading.get(cfg.id);const p=(async()=>{const u=new URL(file,document.baseURI);const r=await fetch(u.toString(),{cache:'default'});if(!r.ok)throw new Error(`Snapshot local indisponível (${r.status})`);if(/\.geojson(?:$|\?)/i.test(u.pathname)||/\.json(?:$|\?)/i.test(u.pathname)){const d=await r.json();window.ATLAS_DATA=window.ATLAS_DATA||{};window.ATLAS_DATA[cfg.id]=d;return d}await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=u.toString();s.onload=resolve;s.onerror=()=>reject(new Error('Falha ao carregar arquivo local'));document.head.appendChild(s)});return window.ATLAS_DATA?.[cfg.id]||null})();loading.set(cfg.id,p);try{return await p}finally{loading.delete(cfg.id)}}
function detailsHtml(cfg,data){const m=meta(cfg),url=sourceUrl(cfg),date=captureDateLabel(cfg,data),mode=modeFor(cfg),note=statusNote(cfg);return `<div class="ita-prov"><div class="ita-prov-badges"><span class="ita-prov-badge ${capability(cfg).cls}">${capability(cfg).label}</span>${(mode==='online'||mode==='local')?`<span class="ita-prov-badge ${mode==='online'?'online':'local'}">${mode==='online'?'consulta online':'snapshot local'}</span>`:''}</div><div class="ita-prov-line"><span class="ita-prov-k">Origem</span><span class="ita-prov-v">${esc(m.institution||cfg.source||'não informada')}</span></div>${date?`<div class="ita-prov-line"><span class="ita-prov-k">Data de captura</span><span class="ita-prov-v">${esc(date)}</span></div>`:''}${m.local_feature_count!==null&&m.local_feature_count!==undefined?`<div class="ita-prov-line"><span class="ita-prov-k">Registros locais</span><span class="ita-prov-v">${esc(m.local_feature_count)}</span></div>`:''}${m.snapshot_sha256?`<div class="ita-prov-line"><span class="ita-prov-k">SHA256</span><span class="ita-prov-v">${esc(m.snapshot_sha256)}</span></div>`:''}${note?`<div class="ita-prov-note">${esc(note)}</div>`:''}${url?`<div class="ita-prov-actions"><a href="${esc(url)}" target="_blank" rel="noopener">Abrir fonte oficial</a></div>`:''}<div class="ita-prov-note">A consulta online não altera silenciosamente resultados do corte científico.</div></div>`}
function referenceEnhance(){document.querySelectorAll('.layer-entry[id^="layer-"]').forEach(el=>{if(el.querySelector('.ita-prov-ref'))return;const id=el.id.slice(6),m=map()[id];if(!m)return;const box=document.createElement('section');box.className='ita-prov-ref';const d=dateLabel(m.capture_date),note=statusNote({id});box.innerHTML=`<h3>Proveniência e snapshot</h3><p><b>Estado</b> ${esc(capability({id,status:m.status}).label)}</p><p><b>Fonte original</b> ${esc(m.institution||m.source||'não informada')}</p>${d?`<p><b>Data de captura local</b> ${esc(d)}</p>`:''}${m.local_feature_count!==null&&m.local_feature_count!==undefined?`<p><b>Registros locais</b> ${esc(m.local_feature_count)}</p>`:''}${m.snapshot_sha256?`<p><b>SHA256 do snapshot</b> <code>${esc(m.snapshot_sha256)}</code></p>`:''}${note?`<p>${esc(note)}</p>`:''}${m.source_url?`<p><a href="${esc(m.source_url)}" target="_blank" rel="noopener">Abrir fonte oficial de origem</a></p>`:''}`;el.appendChild(box)})}

let decorateQueued=false;
function decorateCards(){
 decorateQueued=false;
 document.querySelectorAll('[data-card]').forEach(card=>{
  const id=card.getAttribute('data-card');
  const m=map()[id];
  if(!m)return;
  const cfg={id,name:m.name,source:m.source,source_url:m.source_url};
  const cap=capability(cfg),mode=modeFor(cfg);
  const sig=[cap.label,mode,m.capture_date,m.local_feature_count,m.online_status,m.provenance_status].join('|');
  const old=[...card.querySelectorAll('.ita-prov')].find(x=>x.dataset.provLayer===id);
  if(old?.dataset.provSig===sig)return;
  if(old)old.remove();
  card.insertAdjacentHTML('beforeend',cardHtml(cfg));
  const box=[...card.querySelectorAll('.ita-prov')].find(x=>x.dataset.provLayer===id);
  if(box){box.dataset.provSig=sig;bindCard(box,cfg)}
 });
}
function queueDecorate(){
 if(decorateQueued)return;
 decorateQueued=true;
 requestAnimationFrame(decorateCards);
}
function installCardObserver(){
 if(window.__ITA_PROV_CARD_OBSERVER__)return;
 window.__ITA_PROV_CARD_OBSERVER__=true;
 queueDecorate();
 const obs=new MutationObserver(queueDecorate);
 obs.observe(document.documentElement,{childList:true,subtree:true});
}

window.ITA_PROVENIENCIA={meta,hasLocal,hasOnline,sourceUrl,modeFor,setMode,cardHtml,bindCard,onlineCfg,loadLocal,detailsHtml,referenceEnhance,captureDateLabel,capability};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{referenceEnhance();installCardObserver()});else{referenceEnhance();installCardObserver()}
})();