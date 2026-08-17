(function(){
'use strict';
const $=id=>document.getElementById(id);
const qa=(s,r=document)=>Array.from(r.querySelectorAll(s));
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const TERNARY_KNOWLEDGE={
 title:'Diagrama Ternário · Areia · Silte · Argila',
 purpose:'Representar uma composição de areia, silte e argila e identificar a classe textural correspondente no triângulo USDA.',
 importance:'Diagramas ternários permitem compreender relações composicionais entre três componentes. O triângulo textural é uma aplicação clássica em solos e sedimentos finos.',
 use:['Informe as porcentagens de areia, silte e argila.','Confirme que a soma corresponde a 100 %.','Use Normalizar apenas quando os três valores forem proporções válidas que precisam ser reescaladas.','Observe o ponto e a classe correspondente.','Use Mover o ponto para explorar didaticamente como a composição altera a classificação.'],
 measures:'A ferramenta não mede granulometria. Ela representa e classifica percentuais fornecidos pelo usuário.',
 interpret:'Cada ponto interno corresponde a uma composição cuja soma é 100 %. A proximidade de um vértice indica maior participação relativa daquele componente.',
 limits:'O resultado depende integralmente da qualidade dos percentuais informados. Fragmentos maiores que 2 mm devem ser registrados separadamente. A ferramenta não substitui análise granulométrica de laboratório.',
 quality:'A qualidade depende da procedência dos percentuais. O resultado deve registrar se os valores vieram de laboratório, estimativa de campo, exercício didático ou outra fonte.',
 method:'Classificação pelas 12 classes básicas do triângulo textural USDA. A normalização apenas reescala valores proporcionais para totalizar 100 %.',
 example:'Insira 60 % de areia, 25 % de silte e 15 % de argila. Depois mova o ponto lentamente em direção ao vértice Argila e observe as mudanças de classe.',
 refs:['REF-206','REF-207','REF-208']
};

function knowledgeHTML(k){
 const refs=(k.refs||[]).map(r=>`<a href="./referencias/index.html#ref-${r.replace('REF-','')}" target="_blank" rel="noopener">${esc(r)}</a>`).join('');
 return `<div class="ita-tool-knowledge-inner"><div class="ita-tool-knowledge-top"><h3>Ajuda e Ciência</h3><button type="button" class="ita-tool-back" data-ita48-knowledge-back>← Voltar à ferramenta</button></div><div class="ita-tool-knowledge-grid">
 <section class="ita-tool-knowledge-section"><h4>Para que serve</h4><p>${esc(k.purpose)}</p></section>
 <section class="ita-tool-knowledge-section"><h4>Por que é importante nas Geociências</h4><p>${esc(k.importance)}</p></section>
 <section class="ita-tool-knowledge-section"><h4>Como usar</h4><ol>${k.use.map(x=>`<li>${esc(x)}</li>`).join('')}</ol></section>
 <section class="ita-tool-knowledge-section"><h4>O que está sendo medido ou calculado</h4><p>${esc(k.measures)}</p></section>
 <section class="ita-tool-knowledge-section"><h4>Como interpretar</h4><p>${esc(k.interpret)}</p></section>
 <section class="ita-tool-knowledge-section warning"><h4>Limitações</h4><p>${esc(k.limits)}</p></section>
 <section class="ita-tool-knowledge-section"><h4>Qualidade da medição ou do dado</h4><p>${esc(k.quality)}</p></section>
 <section class="ita-tool-knowledge-section"><h4>Método</h4><p>${esc(k.method)}</p></section>
 <section class="ita-tool-knowledge-section"><h4>Experimente</h4><p>${esc(k.example)}</p></section>
 <section class="ita-tool-knowledge-section ita-tool-knowledge-refs"><h4>Referências científicas</h4><p>As referências utilizadas também integram a Biblioteca Bibliográfica do ITA ARANDU MS.</p><div>${refs}</div><p><a class="ita-tool-library-link" href="./referencias/index.html" target="_blank" rel="noopener">Ver referências completas na Biblioteca</a></p></section>
 </div></div>`;
}

function standardizeTernary(){
 const modal=$('ternarioModal');
 const box=modal?.querySelector('.modal-box');
 if(!box)return;
 box.classList.add('ita48-tool-modal');
 if(!box.querySelector('.ita48-ternario-head')){
   const head=document.createElement('div');
   head.className='modal-head ita48-ternario-head';
   head.innerHTML=`<div><div class="kicker">BANCADA DIGITAL · MATERIAIS GEOLÓGICOS</div><h2>Diagrama Ternário</h2><span class="ita-tool-subtitle">Areia · Silte · Argila · classificação textural USDA</span></div><div class="ita-tool-head-actions"><button type="button" class="ita-tool-back" data-ita48-ternary-back>← Bancada</button><button type="button" class="ita-tool-knowledge-btn" data-ita48-ternary-knowledge>Ajuda e Ciência</button></div>`;
   box.insertBefore(head,box.firstChild);
 }
 let panel=box.querySelector(':scope > .ita48-ternary-knowledge');
 if(!panel){panel=document.createElement('section');panel.className='ita-tool-knowledge ita48-ternary-knowledge';panel.innerHTML=knowledgeHTML(TERNARY_KNOWLEDGE);box.appendChild(panel)}
 // As subviews antigas permanecem no DOM apenas para compatibilidade do motor, mas não participam da navegação 48.
 modal.classList.remove('is-subview');
 const old=$('ternarioSubview');if(old){old.hidden=true;old.setAttribute('aria-hidden','true')}
}

function normalizeToolShells(){
 qa('#clinometroAranduModal,#bussolaAranduModal,#nivelAranduModal,#estereogramaAranduModal,#calculadoraEstruturalModal,#macroGeoModal,#geocameraModal,#saidaCampoModal').forEach(m=>m.querySelector('.modal-box')?.classList.add('ita48-tool-modal'));
 standardizeTernary();
}

function hubKnowledge(){
 const modal=$('ferramentasModal');const box=modal?.querySelector('.modal-box');if(!box)return;
 const old=modal.querySelector('.ita-tools-principle a');
 if(old){old.removeAttribute('target');old.removeAttribute('href');old.setAttribute('role','button');old.dataset.ita48HubScience='1';old.textContent='Ajuda e Ciência'}
 if(box.querySelector(':scope > .ita48-hub-knowledge'))return;
 const panel=document.createElement('section');panel.className='ita48-hub-knowledge';panel.innerHTML=`<div class="ita48-hub-knowledge-inner"><div class="ita48-hub-knowledge-top"><h3>Bancada Digital · Ajuda e Ciência</h3><button class="ita48-standard-btn" type="button" data-ita48-hub-back>← Voltar às ferramentas</button></div><div class="ita48-hub-knowledge-grid">
 <section><h4>Para que serve</h4><p>A Bancada Digital reúne ferramentas geocientíficas educativas para observar, medir, calcular, representar e experimentar conceitos estudados em Geologia utilizando recursos disponíveis no navegador e no dispositivo.</p></section>
 <section><h4>Por que é importante nas Geociências</h4><p>A aprendizagem de campo e de laboratório depende de compreender o que uma medida representa, como foi obtida, quais são seus limites e como ela se relaciona com uma interpretação geológica. A Bancada foi organizada para tornar essa sequência explícita.</p></section>
 <section><h4>Como usar</h4><ol><li>Escolha uma família temática.</li><li>Abra uma ferramenta.</li><li>Leia a instrução operacional antes de medir ou calcular.</li><li>Use Ajuda e Ciência para compreender método, limites e bibliografia.</li><li>Registre somente resultados cuja origem e qualidade possam ser explicadas.</li></ol></section>
 <section><h4>Regra científica comum</h4><p>Cada ferramenta deve informar para que serve, importância geocientífica, modo de uso, grandeza medida ou calculada, interpretação, limitações, qualidade, método, exemplo didático e referências científicas.</p></section>
 <section><h4>Limitações dos celulares</h4><p>Sensores, câmeras e GNSS variam entre aparelhos e navegadores. Uma leitura estável não é sinônimo de calibração metrológica. O celular é um recurso educativo e de apoio, não um substituto automático de equipamento científico profissional.</p></section>
 <section><h4>Bibliografia</h4><p>As referências específicas aparecem dentro de cada ferramenta e são centralizadas em APA 7 na Biblioteca Bibliográfica do ITA ARANDU MS.</p><p><a class="ita48-standard-btn primary" href="./referencias/index.html" target="_blank" rel="noopener">Abrir Biblioteca Bibliográfica</a></p></section>
 </div></div>`;box.appendChild(panel);
}

function placeSaidaToolbar(){
 const modal=$('saidaCampoModal');const wrap=modal?.querySelector('.ita-saida-mapwrap');if(!wrap)return;
 let tools=$('saidaMinhaLocalizacao')?.closest('.ita-saida-map-tools');
 if(!tools){
   tools=document.createElement('div');tools.className='ita-saida-map-tools';
   tools.innerHTML=`<button class="action-btn primary" id="saidaMinhaLocalizacao" type="button">◎ Minha localização</button><button class="action-btn" id="saidaCentralizarPontos" type="button">⌖ Pontos registrados</button><button class="action-btn" id="saidaEnquadrarMS" type="button">▣ Enquadrar MS</button><span class="ita-saida-location-status" id="saidaLocationStatus">Localização ainda não solicitada.</span>`;
 }
 wrap.parentNode.insertBefore(tools,wrap);
 if(!$('saidaEnquadrarMS')){const b=document.createElement('button');b.className='action-btn';b.id='saidaEnquadrarMS';b.type='button';b.textContent='▣ Enquadrar MS';tools.insertBefore(b,$('saidaLocationStatus'))}
 const st=$('saidaLocationStatus');
 $('saidaMinhaLocalizacao').onclick=()=>{
   if(st)st.textContent='Obtendo localização…';
   if(!navigator.geolocation){if(st)st.textContent='Geolocalização indisponível neste navegador.';return}
   navigator.geolocation.getCurrentPosition(p=>{
     const map=window.ITA_SAIDA_CAMPO?.state?.map;const ll=[p.coords.latitude,p.coords.longitude];
     if(map&&window.L){
       if(window.__itaSaidaYou)try{map.removeLayer(window.__itaSaidaYou)}catch(_){ }
       window.__itaSaidaYou=L.circleMarker(ll,{radius:9,weight:3,color:'#b51f1f',fillColor:'#ffd23f',fillOpacity:.95}).addTo(map).bindPopup('Minha localização');
       map.setView(ll,16);setTimeout(()=>map.invalidateSize(),50);
       if(st)st.textContent=`Minha localização · precisão ±${Math.round(p.coords.accuracy||0)} m`;
     }else if(st)st.textContent='Mapa ainda não inicializado.';
   },e=>{if(st)st.textContent='Não foi possível obter a localização · '+e.message},{enableHighAccuracy:true,timeout:15000,maximumAge:0});
 };
 $('saidaCentralizarPontos').onclick=()=>{
   const state=window.ITA_SAIDA_CAMPO?.state,map=state?.map,markers=state?.markers;if(!map)return;
   const ls=markers?.getLayers?.()||[];if(ls.length&&window.L){try{map.fitBounds(L.featureGroup(ls).getBounds().pad(.18),{maxZoom:15})}catch(_){}}else map.setView([-20.45,-54.62],6);setTimeout(()=>map.invalidateSize(),50);
 };
 $('saidaEnquadrarMS').onclick=()=>{const map=window.ITA_SAIDA_CAMPO?.state?.map;if(map){map.setView([-20.45,-54.62],6);setTimeout(()=>map.invalidateSize(),50)}};
}

function keepSaidaMapSane(){
 const m=$('saidaCampoModal');if(!m)return;
 const obs=new MutationObserver(()=>{
   if(!m.classList.contains('open'))return;
   const state=window.ITA_SAIDA_CAMPO?.state;if(!state?.map)return;
   setTimeout(()=>{state.map.invalidateSize();const pts=state.saida?.points||[];if(!pts.length&&state.map.getZoom()<5)state.map.setView([-20.45,-54.62],6)},80);
 });obs.observe(m,{attributes:true,attributeFilter:['class']});
}

function clickRouter(e){
 const t=e.target instanceof Element?e.target.closest('button,a'):null;if(!t)return;
 if(t.matches('[data-ita48-hub-science]')){e.preventDefault();$('ferramentasModal')?.classList.add('ita48-hub-knowledge-open');return}
 if(t.matches('[data-ita48-hub-back]')){e.preventDefault();$('ferramentasModal')?.classList.remove('ita48-hub-knowledge-open');return}
 if(t.matches('[data-ita48-ternary-knowledge]')){e.preventDefault();const box=$('ternarioModal')?.querySelector('.modal-box');box?.classList.add('ita-knowledge-open');return}
 if(t.matches('[data-ita48-knowledge-back]')){e.preventDefault();t.closest('.modal-box')?.classList.remove('ita-knowledge-open');return}
 if(t.matches('[data-ita48-ternary-back]')){e.preventDefault();const m=$('ternarioModal');m?.classList.remove('open','is-subview');m?.setAttribute('aria-hidden','true');const h=$('ferramentasModal');h?.classList.add('open');h?.setAttribute('aria-hidden','false');return}
}

function updateVersion(){
 document.title=document.title.replace(/V38\.4\.47|V38\.4\.46F|V38\.4\.46E/g,'V38.4.48');
 const badge=qa('.brand-badge').find(x=>/^V38\.4\./.test(x.textContent.trim()));if(badge)badge.textContent='V38.4.48';
}

function init(){
 normalizeToolShells();hubKnowledge();placeSaidaToolbar();keepSaidaMapSane();updateVersion();document.addEventListener('click',clickRouter,true);
 // Reaplica após eventuais modais gerados tardiamente por outros módulos.
 setTimeout(()=>{normalizeToolShells();placeSaidaToolbar()},250);
 window.ITA_BANCADA_SYSTEM={version:'2.0',normalize:normalizeToolShells};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
