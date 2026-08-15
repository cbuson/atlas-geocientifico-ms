(function(){
'use strict';

const $=id=>document.getElementById(id);
const qa=(sel,root=document)=>[...root.querySelectorAll(sel)];

function visibleFieldsets(){
  return qa('#campoForm > fieldset.ita-campo-section').filter(fs=>{
    const style=getComputedStyle(fs);
    return style.display!=='none';
  });
}

function updateNav(){
  const visible=visibleFieldsets();
  visible.forEach((fs,i)=>{
    const prev=fs.querySelector('[data-ita-section-prev]');
    const next=fs.querySelector('[data-ita-section-next]');
    if(prev)prev.disabled=i===0;
    if(next)next.disabled=i===visible.length-1;
  });
}

function openSection(fs,scroll=true){
  if(!fs)return;
  fs.classList.add('is-open');
  const btn=fs.querySelector('.ita-section-toggle');
  if(btn)btn.setAttribute('aria-expanded','true');
  if(scroll&&matchMedia('(max-width:760px)').matches){
    requestAnimationFrame(()=>fs.scrollIntoView({behavior:'smooth',block:'start'}));
  }
}

function closeSection(fs){
  if(!fs)return;
  fs.classList.remove('is-open');
  const btn=fs.querySelector('.ita-section-toggle');
  if(btn)btn.setAttribute('aria-expanded','false');
}

function goRelative(fs,delta){
  const visible=visibleFieldsets();
  const i=visible.indexOf(fs);
  const target=visible[i+delta];
  if(!target)return;
  closeSection(fs);
  openSection(target,true);
}

function buildAccordion(){
  const form=$('campoForm');
  if(!form||form.dataset.itaUxAccordion==='1')return;
  form.dataset.itaUxAccordion='1';

  const sections=qa(':scope > fieldset.field-box',form);
  sections.forEach((fs,index)=>{
    fs.classList.add('ita-campo-section');
    fs.dataset.itaSectionIndex=String(index);

    const legend=fs.querySelector(':scope > legend');
    if(!legend)return;
    const title=legend.textContent.trim();
    const kind=fs.classList.contains('advanced')?'especialista':'essencial';

    const body=document.createElement('div');
    body.className='ita-section-body';

    [...fs.childNodes].forEach(node=>{
      if(node!==legend)body.appendChild(node);
    });

    const toggle=document.createElement('button');
    toggle.type='button';
    toggle.className='ita-section-toggle';
    toggle.setAttribute('aria-expanded',index===0?'true':'false');
    toggle.innerHTML=`<span class="ita-section-title">${title}</span><span class="ita-section-kind ${kind==='essencial'?'essential':''}">${kind}</span><span class="ita-section-chevron" aria-hidden="true">⌄</span>`;
    legend.textContent='';
    legend.appendChild(toggle);

    const nav=document.createElement('div');
    nav.className='ita-section-nav';
    nav.innerHTML='<button type="button" class="action-btn" data-ita-section-prev>← Anterior</button><button type="button" class="action-btn primary" data-ita-section-next>Próximo →</button><select class="field-select ita-campo-jump" aria-label="Ir para outra seção"></select>';
    body.appendChild(nav);
    fs.appendChild(body);

    toggle.addEventListener('click',()=>{
      if(!matchMedia('(max-width:760px)').matches)return;
      const open=fs.classList.contains('is-open');
      if(open)closeSection(fs);
      else{
        visibleFieldsets().forEach(other=>{if(other!==fs)closeSection(other)});
        openSection(fs,false);
      }
    });

    nav.querySelector('[data-ita-section-prev]').addEventListener('click',()=>goRelative(fs,-1));
    nav.querySelector('[data-ita-section-next]').addEventListener('click',()=>goRelative(fs,1));
  });

  const first=sections[0];
  if(first)first.classList.add('is-open');

  refreshJumpMenus();

  const campoRoot=form.closest('.ita-campo-master');
  if(campoRoot){
    new MutationObserver(()=>{
      refreshJumpMenus();
      updateNav();
      const visible=visibleFieldsets();
      if(matchMedia('(max-width:760px)').matches&&!visible.some(x=>x.classList.contains('is-open'))&&visible[0]){
        openSection(visible[0],false);
      }
    }).observe(campoRoot,{attributes:true,attributeFilter:['class']});
  }

  updateNav();
}

function refreshJumpMenus(){
  const visible=visibleFieldsets();
  qa('.ita-campo-jump').forEach(select=>{
    const fs=select.closest('.ita-campo-section');
    const current=visible.indexOf(fs);
    select.innerHTML=visible.map((x,i)=>{
      const title=x.querySelector('.ita-section-title')?.textContent||`Seção ${i+1}`;
      return `<option value="${i}" ${i===current?'selected':''}>${title}</option>`;
    }).join('');
    select.onchange=()=>{
      const target=visibleFieldsets()[Number(select.value)];
      if(target&&target!==fs){
        closeSection(fs);
        openSection(target,true);
      }
    };
  });
}

function improveCompletionText(){
  const pct=$('campoCompletudeText');
  const checklist=$('campoChecklist');
  if(!pct||!checklist)return;

  let busy=false;
  const sync=()=>{
    if(busy)return;
    busy=true;
    const base=(pct.textContent.match(/\d+%/)||['0%'])[0];
    const txt=checklist.textContent.trim();
    let extra='';
    const m=txt.match(/^Faltam?\s+(.+?)\.?$/i);
    if(m){
      const missing=m[1].replace(/\.$/,'').split(',').map(x=>x.trim()).filter(Boolean);
      if(missing.length===1)extra=` · falta ${missing[0]}`;
      else if(missing.length>1)extra=` · falta ${missing[0]} +${missing.length-1}`;
    }else if(/completo/i.test(txt)){
      extra=' · essencial completo';
    }
    const wanted=base+extra;
    if(pct.textContent!==wanted)pct.textContent=wanted;
    busy=false;
  };

  new MutationObserver(()=>requestAnimationFrame(sync)).observe(pct,{childList:true,characterData:true,subtree:true});
  new MutationObserver(()=>requestAnimationFrame(sync)).observe(checklist,{childList:true,characterData:true,subtree:true});
  sync();
}

function updateModeLabels(){
  const essential=$('campoModoEssencial');
  const advanced=$('campoModoAvancado');
  if(essential){
    essential.textContent='Estudante · Essencial';
    essential.title='Fluxo simplificado para ensino e registro rápido';
  }
  if(advanced){
    advanced.textContent='Especialista · Avançado';
    advanced.title='Exibe todos os módulos científicos do caderno';
  }
}

function openRelevantSectionFromChecklist(){
  const status=$('campoChecklist');
  if(!status)return;
  status.addEventListener('click',()=>{
    if(!matchMedia('(max-width:760px)').matches)return;
    const txt=status.textContent.toLowerCase();
    const map=[
      ['posição','3 · Localização'],
      ['exposição','4 · Exposição'],
      ['litologia','4 · Exposição'],
      ['observação','7 · Observação'],
      ['foto','12 · Fotografias'],
      ['sensibilidade','14 · Qualidade'],
      ['identificação','1 · Identificação']
    ];
    const hit=map.find(([key])=>txt.includes(key));
    if(!hit)return;
    const fs=qa('.ita-campo-section').find(x=>(x.querySelector('.ita-section-title')?.textContent||'').includes(hit[1]));
    if(fs){
      visibleFieldsets().forEach(x=>closeSection(x));
      openSection(fs,true);
    }
  });
  status.title='No celular, toque para ir a um dos blocos essenciais pendentes.';
}

function install(){
  updateModeLabels();
  buildAccordion();
  improveCompletionText();
  openRelevantSectionFromChecklist();

  const mq=matchMedia('(max-width:760px)');
  const react=()=>{
    if(!mq.matches){
      qa('.ita-campo-section').forEach(fs=>fs.classList.add('is-open'));
    }else{
      const visible=visibleFieldsets();
      visible.forEach((fs,i)=>fs.classList.toggle('is-open',i===0));
      qa('.ita-section-toggle').forEach(btn=>btn.setAttribute('aria-expanded',btn.closest('.ita-campo-section')?.classList.contains('is-open')?'true':'false'));
    }
    updateNav();
  };
  if(mq.addEventListener)mq.addEventListener('change',react);
  react();
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
else install();

window.ITA_CAMPO_UX_38432={openSection,visibleFieldsets};
})();
