(function(){
'use strict';
const $=id=>document.getElementById(id);
const norm=a=>((a%360)+360)%360;
const dirs=['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
const dir=h=>Number.isFinite(h)?dirs[Math.round(norm(h)/22.5)%16]:'—';
const parseAngle=t=>{const n=parseFloat(String(t||'').replace(',','.'));return Number.isFinite(n)?n:null};
function decl(){const e=$('bussolaDeclinacao');if(!e||String(e.value||'').trim()==='')return null;const n=Number(e.value);return Number.isFinite(n)?n:null}
function fmtDecl(d){if(!Number.isFinite(d))return '—';if(Math.abs(d)<0.05)return '0,0°';return `${Math.abs(d).toFixed(1).replace('.',',')}° ${d>0?'E':'W'}`}
function enhance(){
 const modal=$('bussolaAranduModal');if(!modal||modal.dataset.r5)return;
 modal.dataset.r5='1';
 const body=modal.querySelector('.modal-body');if(!body)return;
 const status=body.querySelector('.ita-r4-status')||body.querySelector('.ita-sensor-note');
 const html=`<section class="ita-r5-north" aria-label="Referência magnética e geográfica">
   <div class="ita-r5-title"><div><small>REFERÊNCIA DO NORTE</small><b>Magnético × geográfico</b></div><button type="button" class="ita-r5-help" id="r5NorthHelp">Por quê?</button></div>
   <div class="ita-r5-north-grid">
     <div class="ita-r5-north-card magnetic"><small>Norte magnético</small><strong id="r5MagHeading">—</strong><span id="r5MagDir">leitura do sensor</span></div>
     <div class="ita-r5-decl-card"><small>Declinação</small><strong id="r5Decl">—</strong><span>Leste + · Oeste −</span></div>
     <div class="ita-r5-north-card true"><small>Norte geográfico</small><strong id="r5TrueHeading">—</strong><span id="r5TrueDir">requer declinação</span></div>
   </div>
   <div class="ita-r5-formula"><span>Azimute geográfico</span><b>Azimute magnético + declinação</b></div>
   <div class="ita-r5-reference-switch" role="group" aria-label="Referência destacada"><button type="button" class="active" data-r5-ref="mag">Magnético</button><button type="button" data-r5-ref="true">Geográfico</button></div>
   <div class="ita-r5-decl-entry"><label><span>Declinação local °</span><input id="r5DeclInput" inputmode="decimal" type="number" step="0.1" placeholder="Ex. -18,4"></label><button type="button" id="r5NOAA">Consultar NOAA</button></div>
   <div class="ita-r5-education" id="r5Education"><b>Importante</b> A bússola do telefone fornece a referência magnética quando o dispositivo oferece orientação absoluta. O norte geográfico só é mostrado quando existe uma declinação informada. ITA ARANDU não inventa essa correção.</div>
 </section>`;
 if(status)status.insertAdjacentHTML('afterend',html);else body.insertAdjacentHTML('afterbegin',html);
 const dial=modal.querySelector('.ita-compass-dial');
 if(dial){dial.classList.add('ita-r5-dial');dial.insertAdjacentHTML('beforeend','<div class="ita-r5-true-needle" id="r5TrueNeedle" aria-hidden="true"><span>Ng</span></div><div class="ita-r5-decl-arc" id="r5DeclArc" aria-hidden="true"></div>')}
 const old=$('bussolaDeclinacao');if(old){old.closest('label')?.classList.add('ita-r5-original-decl');old.addEventListener('input',()=>{const x=$('r5DeclInput');if(x&&x.value!==old.value)x.value=old.value;sync()})}
 const input=$('r5DeclInput');if(input){input.value=old?.value||'';input.addEventListener('input',()=>{if(old){old.value=input.value;old.dispatchEvent(new Event('input',{bubbles:true}))}sync()})}
 document.querySelectorAll('[data-r5-ref]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-r5-ref]').forEach(x=>x.classList.toggle('active',x===b));modal.dataset.northRef=b.dataset.r5Ref;sync()}));
 $('r5NorthHelp')?.addEventListener('click',()=>{const box=$('r5Education');box?.classList.toggle('open')});
 $('r5NOAA')?.addEventListener('click',()=>window.open('https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml','_blank','noopener'));
 sync();setInterval(sync,250);
}
function sync(){
 const modal=$('bussolaAranduModal');if(!modal)return;
 const mag=parseAngle($('bussolaHeading')?.textContent),d=decl(),trueH=Number.isFinite(mag)&&Number.isFinite(d)?norm(mag+d):null;
 if($('r5MagHeading'))$('r5MagHeading').textContent=Number.isFinite(mag)?mag.toFixed(1)+'°':'—';
 if($('r5MagDir'))$('r5MagDir').textContent=Number.isFinite(mag)?dir(mag)+' · sensor':'leitura do sensor';
 if($('r5Decl'))$('r5Decl').textContent=fmtDecl(d);
 if($('r5TrueHeading'))$('r5TrueHeading').textContent=Number.isFinite(trueH)?trueH.toFixed(1)+'°':'—';
 if($('r5TrueDir'))$('r5TrueDir').textContent=Number.isFinite(trueH)?dir(trueH)+' · corrigido':'requer declinação';
 const needle=$('r5TrueNeedle');if(needle){needle.hidden=!Number.isFinite(trueH);if(Number.isFinite(trueH))needle.style.transform=`translate(-50%,-100%) rotate(${-trueH}deg)`}
 const arc=$('r5DeclArc');if(arc){arc.hidden=!Number.isFinite(d);arc.dataset.sign=Number.isFinite(d)?(d>=0?'E':'W'):'';arc.title=Number.isFinite(d)?`Declinação ${fmtDecl(d)}`:''}
 const chosen=modal.dataset.northRef||'mag';modal.classList.toggle('ita-r5-show-true',chosen==='true'&&Number.isFinite(trueH));
 const ref=$('r4Ref');if(ref)ref.textContent=chosen==='true'?(Number.isFinite(trueH)?'Geográfica · corrigida':'Geográfica · sem correção'):'Magnética · sensor';
}
function start(){let tries=0;const timer=setInterval(()=>{tries++;enhance();if($('bussolaAranduModal')?.dataset.r5||tries>40)clearInterval(timer)},100)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
