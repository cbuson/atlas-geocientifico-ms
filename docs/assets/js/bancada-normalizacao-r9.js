(function(){
'use strict';
const qa=(s,r=document)=>Array.from(r.querySelectorAll(s));
const $=id=>document.getElementById(id);

function normalizeCatalog(){
  qa('#ferramentasModal .ita-tool-card').forEach(card=>{
    const actions=card.querySelector('.ita-tool-actions');
    if(!actions)return;
    const open=actions.querySelector('[data-tool-action]');
    if(!open)return;
    open.textContent='Abrir';
    open.classList.add('primary');
    qa('.action-btn',actions).forEach(a=>{if(a!==open)a.remove()});
  });
}

function normalizeInstrumentLabels(){
  const compassScience=$('bussolaAranduModal')?.querySelector('[data-ar6-go="science"]');
  if(compassScience)compassScience.textContent='ⓘ Ajuda e Ciência';
  const levelScience=$('nivelAranduModal')?.querySelector('[data-level-go="science"]');
  if(levelScience)levelScience.textContent='ⓘ Ajuda e Ciência';
  const ternHelp=$('itaTernarioAjuda');
  const ternScience=$('itaTernarioCiencia');
  if(ternHelp){ternHelp.innerHTML='ⓘ <span>Ajuda e Ciência</span>'}
  if(ternScience)ternScience.style.display='none';
}

function resetScrollOnOpen(){
  const ids=['bussolaAranduModal','nivelAranduModal','gpsEducativoModal'];
  ids.forEach(id=>{
    const modal=$(id);if(!modal)return;
    const obs=new MutationObserver(()=>{
      if(!modal.classList.contains('open'))return;
      const scroller=modal.querySelector(id==='gpsEducativoModal'?'.modal-body':'.ar6-body');
      if(scroller)scroller.scrollTop=0;
    });
    obs.observe(modal,{attributes:true,attributeFilter:['class']});
  });
}

function protectTouchScroll(){
  qa('#bussolaAranduModal .ar6-body,#nivelAranduModal .ar6-body,#gpsEducativoModal .modal-body,#gpsEducativoModal .ita49-help-panel').forEach(el=>{
    el.addEventListener('touchmove',()=>{}, {passive:true});
  });
}

function init(){
  normalizeCatalog();
  normalizeInstrumentLabels();
  resetScrollOnOpen();
  protectTouchScroll();
  /* alguns módulos constroem o catálogo/modal depois do DOMContentLoaded */
  let n=0;const timer=setInterval(()=>{
    normalizeCatalog();normalizeInstrumentLabels();protectTouchScroll();
    if(++n>30)clearInterval(timer);
  },200);
  window.ITA_BANCADA_R9={version:'9.0',normalizeCatalog};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
