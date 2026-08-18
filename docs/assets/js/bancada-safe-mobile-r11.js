(function(){
'use strict';
const qa=(s,r=document)=>Array.from(r.querySelectorAll(s));
const byId=id=>document.getElementById(id);

function normalizeCatalog(){
  qa('#ferramentasModal .ita-tool-card').forEach(card=>{
    const actions=card.querySelector('.ita-tool-actions');
    if(!actions)return;
    const open=actions.querySelector('[data-tool-action]');
    if(!open)return;
    open.textContent='Abrir';
    open.classList.add('primary');
    qa('.action-btn',actions).forEach(btn=>{ if(btn!==open) btn.remove(); });
  });
}

function normalizeScienceLabels(){
  const compass=byId('bussolaAranduModal')?.querySelector('[data-ar6-go="science"]');
  if(compass)compass.textContent='ⓘ Ajuda e Ciência';
  const level=byId('nivelAranduModal')?.querySelector('[data-level-go="science"]');
  if(level)level.textContent='ⓘ Ajuda e Ciência';
}

function resetOwnScroller(modal){
  if(!modal)return;
  let scroller=null;
  if(modal.id==='bussolaAranduModal'||modal.id==='nivelAranduModal')scroller=modal.querySelector('.ar6-body');
  else if(modal.id==='gpsEducativoModal')scroller=modal.querySelector('.modal-body');
  else scroller=modal.querySelector('.ita-lab-body');
  if(scroller)scroller.scrollTop=0;
}

function watchOpenState(){
  ['bussolaAranduModal','nivelAranduModal','gpsEducativoModal','granulometriaModal','isopiezasModal'].forEach(id=>{
    const modal=byId(id);
    if(!modal||modal.dataset.r11Watch)return;
    modal.dataset.r11Watch='1';
    new MutationObserver(()=>{
      if(modal.classList.contains('open'))requestAnimationFrame(()=>resetOwnScroller(modal));
    }).observe(modal,{attributes:true,attributeFilter:['class']});
  });
}

function refresh(){
  normalizeCatalog();
  normalizeScienceLabels();
  watchOpenState();
}

function init(){
  refresh();
  const root=byId('ferramentasModal')||document.body;
  const observer=new MutationObserver(refresh);
  observer.observe(root,{childList:true,subtree:true});
  let tries=0;
  const timer=setInterval(()=>{refresh();if(++tries>=20)clearInterval(timer)},250);
  window.ITA_BANCADA_R11={version:'11.0-safe',refresh};
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
