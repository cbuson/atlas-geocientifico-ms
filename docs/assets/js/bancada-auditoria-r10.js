(function(){
'use strict';
const qa=(s,r=document)=>Array.from(r.querySelectorAll(s));
const $=id=>document.getElementById(id);
function normalizeCatalog(){
  qa('#ferramentasModal .ita-tool-card').forEach(card=>{
    const actions=card.querySelector('.ita-tool-actions');if(!actions)return;
    const open=actions.querySelector('[data-tool-action]');if(!open)return;
    /* Em catálogo, uma única ação. A ajuda científica vive dentro da ferramenta. */
    open.textContent='Abrir';open.classList.add('primary');
    qa('.action-btn',actions).forEach(a=>{if(a!==open)a.remove()});
  });
}
function normalizeLabels(){
  const compass=$('bussolaAranduModal')?.querySelector('[data-ar6-go="science"]');if(compass)compass.textContent='ⓘ Ajuda e Ciência';
  const level=$('nivelAranduModal')?.querySelector('[data-level-go="science"]');if(level)level.textContent='ⓘ Ajuda e Ciência';
  const ternHelp=$('itaTernarioAjuda');const ternScience=$('itaTernarioCiencia');if(ternHelp)ternHelp.innerHTML='ⓘ <span>Ajuda e Ciência</span>';if(ternScience)ternScience.style.display='none';
}
function resetScroll(modal,selector){if(!modal)return;const scroller=modal.querySelector(selector);if(scroller)scroller.scrollTop=0}
function installOpenObservers(){
  [['bussolaAranduModal','.ar6-body'],['nivelAranduModal','.ar6-body'],['gpsEducativoModal','.modal-body'],['granulometriaModal','.ita-lab-body'],['isopiezasModal','.ita-lab-body']].forEach(([id,sel])=>{
    const modal=$(id);if(!modal)return;new MutationObserver(()=>{if(modal.classList.contains('open'))resetScroll(modal,sel)}).observe(modal,{attributes:true,attributeFilter:['class']});
  });
}
function init(){normalizeCatalog();normalizeLabels();installOpenObservers();const root=$('ferramentasModal');if(root)new MutationObserver(()=>{normalizeCatalog();normalizeLabels()}).observe(root,{childList:true,subtree:true});window.ITA_BANCADA_R10={version:'10.0',normalizeCatalog}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
