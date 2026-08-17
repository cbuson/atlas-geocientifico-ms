(function(){
'use strict';
const $=id=>document.getElementById(id),qa=(s,r=document)=>[...r.querySelectorAll(s)];
const norm=s=>(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
function byText(ps){const p=ps.map(norm);return qa('button,a').find(el=>!el.closest('#ferramentasModal')&&p.some(x=>norm(el.textContent).includes(x))&&el.offsetParent!==null)||qa('button,a').find(el=>!el.closest('#ferramentasModal')&&p.some(x=>norm(el.textContent).includes(x)))}
function modal(ids){for(const id of ids){const e=$(id);if(e){e.classList.add('open');e.setAttribute('aria-hidden','false');return true}}return false}
function closeHub(){const e=$('ferramentasModal');if(e){e.classList.remove('open');e.setAttribute('aria-hidden','true')}}
function openHub(){const e=$('ferramentasModal');if(e){e.classList.add('open');e.setAttribute('aria-hidden','false')}}
function openCampo(){closeHub();const b=byText(['abrir campo','campo']);if(b){b.click();return true}return modal(['campoModal'])}
function openSection(words){if(!openCampo())return;setTimeout(()=>{const fs=qa('#campoForm fieldset').find(x=>words.some(w=>norm(x.querySelector('legend,.ita-section-title')?.textContent).includes(norm(w))));if(fs){if(window.ITA_CAMPO_UX?.openSection)window.ITA_CAMPO_UX.openSection(fs,true);else{fs.classList.add('is-open');fs.scrollIntoView({behavior:'smooth',block:'start'})}}},180)}
function clino(){closeHub();const b=$('abrirClinometroArandu');if(b)b.click();else if(!modal(['clinometroAranduModal']))alert('Clinômetro não localizado nesta versão.')}
function geocamera(){openSection(['fotografias','geofoto'])}
function columns(){closeHub();const b=byText(['abrir tempo geologico','colunas geologicas','tempo geologico']);if(b)b.click();else if(!modal(['tempoGeologicoModal','tempoModal','geologicTimeModal']))alert('Colunas estratigráficas não localizadas nesta versão.')}
function deep(){closeHub();const b=byText(['abrir tempo profundo','onde estava este lugar','reconstruir paleoposicao']);if(b)b.click();else if(!modal(['tempoProfundoModal','paleoposicaoModal','deepTimeModal']))alert('Tempo Profundo não localizado nesta versão.')}
function planned(name){$('ferramentasStatus').textContent=name+' está no catálogo da bancada digital, mas ainda não é apresentada como ferramenta operacional.'}
const A={clinometro:clino,geocamera:geocamera,colunas:columns,tempo:deep,gps:()=>openSection(['localizacao','localização']),amostras:()=>openSection(['amostras']),nivel:()=>document.getElementById('abrirNivelArandu')?.click(),bussola:()=>document.getElementById('abrirBussolaArandu')?.click(),estereograma:()=>document.getElementById('abrirEstereogramaArandu')?.click(),calculadora:()=>document.getElementById('abrirCalculadoraEstrutural')?.click(),macrogeo:()=>{closeHub();modal(['macroGeoModal'])},saidacampo:()=>{closeHub();modal(['saidaCampoModal']);setTimeout(()=>window.dispatchEvent(new CustomEvent('ita:saida:open')),0)}};
function filter(){const q=norm($('ferramentasBusca')?.value);let n=0;qa('.ita-tool-card').forEach(c=>{const ok=!q||norm(c.dataset.search+' '+c.textContent).includes(q);c.style.display=ok?'':'none';if(ok)n++});qa('.ita-tools-section').forEach(s=>s.style.display=qa('.ita-tool-card',s).some(c=>c.style.display!=='none')?'':'none');$('ferramentasVazio').style.display=n?'none':'block'}
function wire(){$('abrirFerramentas')?.addEventListener('click',openHub);qa('[data-close="ferramentasModal"]').forEach(b=>b.addEventListener('click',closeHub));qa('[data-tool-action]').forEach(b=>b.addEventListener('click',()=>A[b.dataset.toolAction]?.()))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
window.ITA_FERRAMENTAS={version:'1.0',open:openHub,close:closeHub,actions:A};
})();
