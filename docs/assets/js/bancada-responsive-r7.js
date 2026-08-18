(function(){
'use strict';
const qa=(s,r=document)=>Array.from(r.querySelectorAll(s));

function normalizeHubActions(){
  const modal=document.getElementById('ferramentasModal');
  if(!modal)return;
  qa('.ita-tool-card',modal).forEach(card=>{
    const action=card.querySelector('.ita-tool-actions [data-tool-action]');
    if(!action)return;
    action.classList.add('primary');
    action.removeAttribute('hidden');
    action.style.removeProperty('display');
    action.setAttribute('aria-label',`Abrir ${card.querySelector('h4')?.textContent?.trim()||'ferramenta'}`);
  });
}

function normalizeToolTabs(){
  qa('#estereogramaAranduModal .re-tabs button,#roseModal .ita-rose-tabs button').forEach(btn=>{
    btn.style.removeProperty('width');
    btn.style.removeProperty('min-width');
    btn.setAttribute('title',btn.textContent.trim());
  });
}

function markR7(){
  document.documentElement.dataset.bancadaResponsive='r7';
}

function run(){normalizeHubActions();normalizeToolTabs();markR7();}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true}); else run();

/* Alguns modais são injetados depois do DOMContentLoaded. Reaplica somente ajustes seguros. */
const observer=new MutationObserver(muts=>{
  let relevant=false;
  for(const m of muts){
    for(const n of m.addedNodes){
      if(n.nodeType===1 && (n.matches?.('#ferramentasModal,#estereogramaAranduModal,#roseModal') || n.querySelector?.('#ferramentasModal,#estereogramaAranduModal,#roseModal'))){relevant=true;break;}
    }
    if(relevant)break;
  }
  if(relevant)run();
});
observer.observe(document.documentElement,{childList:true,subtree:true});
})();
