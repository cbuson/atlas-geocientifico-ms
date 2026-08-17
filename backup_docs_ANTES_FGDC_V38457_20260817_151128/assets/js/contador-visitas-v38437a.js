(function(){
'use strict';

const CFG = Object.freeze({
  provider: 'GoatCounter',
  code: 'ita-arandu',
  counterBase: 'https://ita-arandu.goatcounter.com/counter/TOTAL.json',
  cacheMs: 15 * 60 * 1000,
  publicCounterCacheNote: 'O contador público do provedor pode manter cache por até quatro horas.'
});

const $all = (s,r=document)=>[...r.querySelectorAll(s)];
const norm = s => (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
const pad=n=>String(n).padStart(2,'0');
const isoLocal=d=>`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;

function ranges(){
  const now=new Date();
  const today=isoLocal(now);
  const d7=new Date(now); d7.setDate(d7.getDate()-6);
  const month=new Date(now.getFullYear(),now.getMonth(),1);
  return {
    total:null,
    today,
    seven:isoLocal(d7),
    month:isoLocal(month)
  };
}

async function fetchCount(start){
  const url = new URL(CFG.counterBase);
  if(start) url.searchParams.set('start',start);
  const r = await fetch(url.toString(),{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'});
  if(!r.ok) throw new Error(`HTTP ${r.status}`);
  const data=await r.json();
  if(!data || typeof data.count!=='string') throw new Error('Resposta sem campo count');
  return data.count;
}

function findUsageBox(){
  return $all('section,div,article').find(el=>{
    const t=norm(el.textContent);
    return t.includes('uso publico do atlas') &&
           t.includes('visitas acumuladas') &&
           t.includes('ultimos 7 dias') &&
           t.length < 3000;
  }) || null;
}

function findLabel(root,label){
  const target=norm(label);
  return $all('*',root).find(el=>norm(el.textContent)===target) || null;
}

function findCard(labelEl){
  let el=labelEl?.parentElement;
  while(el && el!==document.body){
    const t=norm(el.textContent);
    if(t.includes(norm(labelEl.textContent)) && el.querySelectorAll('*').length<=20){
      const val=$all('*',el).find(x=>{
        const tx=norm(x.textContent);
        return tx==='—' || /^[\d.\s,]+$/.test(tx);
      });
      if(val && val!==labelEl) return {card:el,value:val};
    }
    el=el.parentElement;
  }
  return null;
}

function setMetric(root,label,value){
  const lab=findLabel(root,label);
  const hit=findCard(lab);
  if(hit?.value){
    hit.value.textContent=value;
    hit.value.setAttribute('data-goatcounter-value','true');
    return true;
  }
  return false;
}

function replaceText(root,fromContains,newText){
  const target=norm(fromContains);
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  const nodes=[];
  while(walker.nextNode()) nodes.push(walker.currentNode);
  const n=nodes.find(x=>norm(x.nodeValue).includes(target));
  if(n){ n.nodeValue=newText; return true }
  return false;
}

function updateStatus(root,ok,msg){
  const candidates=$all('*',root).filter(el=>{
    const t=norm(el.textContent);
    return t==='monitoramento nao configurado' ||
           t.includes('monitoramento ativo') ||
           t.includes('monitoramento indisponivel');
  });
  const pill=candidates[0];
  if(pill){
    pill.textContent=ok?'monitoramento ativo · GoatCounter':'monitoramento indisponível';
    pill.setAttribute('title',msg||'');
  }
  replaceText(
    root,
    'o contador global ainda nao foi ativado',
    ok
      ? 'Contador de visitas ativo. Os valores são agregados e não representam pessoas identificadas.'
      : 'O contador de visitas está configurado, mas o serviço estatístico não respondeu nesta consulta.'
  );
  replaceText(
    root,
    'a camada estatistica foi preparada para um servico sem cookies',
    'Contagem agregada por GoatCounter, sem cookies. '+CFG.publicCounterCacheNote
  );
}

function cacheKey(){return 'ita_arandu_visitas_goatcounter_v1'}
function readCache(){
  try{
    const d=JSON.parse(sessionStorage.getItem(cacheKey())||'null');
    return d && Date.now()-d.at<CFG.cacheMs ? d : null;
  }catch{return null}
}
function writeCache(v){
  try{sessionStorage.setItem(cacheKey(),JSON.stringify({at:Date.now(),...v}))}catch{}
}

async function load(){
  const root=findUsageBox();
  if(!root) return;
  let values=readCache();
  try{
    if(!values){
      const r=ranges();
      const [total,today,seven,month]=await Promise.all([
        fetchCount(r.total),
        fetchCount(r.today),
        fetchCount(r.seven),
        fetchCount(r.month)
      ]);
      values={total,today,seven,month};
      writeCache(values);
    }
    setMetric(root,'visitas acumuladas',values.total);
    setMetric(root,'visitas hoje',values.today);
    setMetric(root,'últimos 7 dias',values.seven);
    setMetric(root,'mês atual',values.month);
    updateStatus(root,true,'Contador público GoatCounter ativo');
  }catch(err){
    console.warn('ITA ARANDU · contador de visitas',err);
    updateStatus(root,false,String(err?.message||err));
  }
}

function wire(){
  load();
  const obs=new MutationObserver(()=>{
    const root=findUsageBox();
    if(root && !root.querySelector('[data-goatcounter-value="true"]')) load();
  });
  obs.observe(document.body,{childList:true,subtree:true});
  setTimeout(()=>obs.disconnect(),30000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});
else wire();

window.ITA_VISITAS={
  version:'1.0',
  provider:CFG.provider,
  reload:load
};
})();
