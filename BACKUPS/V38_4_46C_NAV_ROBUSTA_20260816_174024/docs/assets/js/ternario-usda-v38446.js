
(function(){
'use strict';
const $=id=>document.getElementById(id);
const PT={sand:'Areia',loamySand:'Areia franca',sandyLoam:'Franco-arenosa',loam:'Franca',siltLoam:'Franco-siltosa',silt:'Silte',sandyClayLoam:'Franco-argilo-arenosa',clayLoam:'Franco-argilosa',siltyClayLoam:'Franco-argilo-siltosa',sandyClay:'Argila arenosa',siltyClay:'Argila siltosa',clay:'Argila'};
const EN={sand:'Sand',loamySand:'Loamy sand',sandyLoam:'Sandy loam',loam:'Loam',siltLoam:'Silt loam',silt:'Silt',sandyClayLoam:'Sandy clay loam',clayLoam:'Clay loam',siltyClayLoam:'Silty clay loam',sandyClay:'Sandy clay',siltyClay:'Silty clay',clay:'Clay'};
const DESC={sand:'Predomínio muito elevado de areia.',loamySand:'Material dominado por areia, com pequena contribuição das frações mais finas.',sandyLoam:'Textura franca com forte participação de areia.',loam:'Mistura relativamente equilibrada das três frações.',siltLoam:'Textura franca com participação elevada de silte.',silt:'Predomínio muito elevado de silte.',sandyClayLoam:'Material franco-argiloso com participação elevada de areia.',clayLoam:'Material franco com teor importante de argila.',siltyClayLoam:'Material franco-argiloso com participação elevada de silte.',sandyClay:'Material argiloso com forte participação de areia.',siltyClay:'Material argiloso com forte participação de silte.',clay:'Predomínio de argila dentro dos limites da classificação USDA.'};
const COLORS={sand:'#f5d987',loamySand:'#f0cf84',sandyLoam:'#eed19a',loam:'#ead7ad',siltLoam:'#d1dfb7',silt:'#b8d9ae',sandyClayLoam:'#e2c899',clayLoam:'#d8c8b0',siltyClayLoam:'#b9d4c0',sandyClay:'#d8bdad',siltyClay:'#b9cde0',clay:'#9fb9dd'};
const LABELS=[['sand',90,5,5],['loamySand',78,17,5],['sandyLoam',62,28,10],['loam',40,40,20],['siltLoam',20,65,15],['silt',8,88,4],['sandyClayLoam',55,10,35],['clayLoam',32,28,40],['siltyClayLoam',10,50,40],['sandyClay',55,5,40],['siltyClay',8,45,47],['clay',20,20,60]];
let mode='values',drag=false,background=null;
function validNums(a,b,c){return [a,b,c].every(Number.isFinite)&&[a,b,c].every(v=>v>=0&&v<=100)}
function classify(sand,silt,clay){
 const eps=1e-8;
 if(!validNums(sand,silt,clay)||Math.abs(sand+silt+clay-100)>0.05)return null;
 if(silt+1.5*clay < 15-eps)return 'sand';
 if(silt+1.5*clay >=15-eps && silt+2*clay <30-eps)return 'loamySand';
 if((clay>=7-eps&&clay<20-eps&&sand>52&&silt+2*clay>=30-eps)||(clay<7-eps&&silt<50-eps&&silt+2*clay>=30-eps))return 'sandyLoam';
 if(clay>=7-eps&&clay<27-eps&&silt>=28-eps&&silt<50-eps&&sand<=52+eps)return 'loam';
 if(silt>=80-eps&&clay<12-eps)return 'silt';
 if((silt>=50-eps&&clay>=12-eps&&clay<27-eps)||(silt>=50-eps&&silt<80-eps&&clay<12-eps))return 'siltLoam';
 if(clay>=20-eps&&clay<35-eps&&silt<28-eps&&sand>45)return 'sandyClayLoam';
 if(clay>=27-eps&&clay<40-eps&&sand>20&&sand<=45+eps)return 'clayLoam';
 if(clay>=27-eps&&clay<40-eps&&sand<=20+eps)return 'siltyClayLoam';
 if(clay>=35-eps&&sand>45)return 'sandyClay';
 if(clay>=40-eps&&silt>=40-eps)return 'siltyClay';
 if(clay>=40-eps&&sand<=45+eps&&silt<40-eps)return 'clay';
 return null;
}
function vals(){return [parseFloat($('ternarioSand')?.value),parseFloat($('ternarioSilt')?.value),parseFloat($('ternarioClay')?.value)]}
function fmt(v){return Number.isFinite(v)?(Math.round(v*10)/10).toLocaleString('pt-BR',{maximumFractionDigits:1})+' %':'—'}
function bary(sand,silt,clay,w,h){const T={x:w*.5,y:h*.08},L={x:w*.09,y:h*.86},R={x:w*.91,y:h*.86};return{x:(sand*T.x+silt*L.x+clay*R.x)/100,y:(sand*T.y+silt*L.y+clay*R.y)/100,T,L,R}}
function inv(x,y,w,h){const p=bary(100,0,0,w,h),T=p.T,L=p.L,R=p.R;const den=(L.y-R.y)*(T.x-R.x)+(R.x-L.x)*(T.y-R.y);let a=((L.y-R.y)*(x-R.x)+(R.x-L.x)*(y-R.y))/den;let b=((R.y-T.y)*(x-R.x)+(T.x-R.x)*(y-R.y))/den;let c=1-a-b;if(a<0||b<0||c<0)return null;return [a*100,b*100,c*100]}
function makeBackground(){const c=$('ternarioCanvas');if(!c)return;const w=c.width,h=c.height;const off=document.createElement('canvas');off.width=w;off.height=h;const ctx=off.getContext('2d');ctx.clearRect(0,0,w,h);const img=ctx.createImageData(w,h),d=img.data;for(let y=0;y<h;y+=2){for(let x=0;x<w;x+=2){const v=inv(x,y,w,h);if(!v)continue;const key=classify(v[0],v[1],v[2]);if(!key)continue;const hex=COLORS[key],rgb=[parseInt(hex.slice(1,3),16),parseInt(hex.slice(3,5),16),parseInt(hex.slice(5,7),16)];for(let yy=0;yy<2;yy++)for(let xx=0;xx<2;xx++){const X=x+xx,Y=y+yy;if(X>=w||Y>=h)continue;const i=(Y*w+X)*4;d[i]=rgb[0];d[i+1]=rgb[1];d[i+2]=rgb[2];d[i+3]=220;}}}ctx.putImageData(img,0,0);background=off}
function line(ctx,a,b){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()}
function draw(){const c=$('ternarioCanvas');if(!c)return;if(!background)makeBackground();const ctx=c.getContext('2d'),w=c.width,h=c.height;ctx.clearRect(0,0,w,h);ctx.drawImage(background,0,0);const base=bary(100,0,0,w,h),{T,L,R}=base;ctx.save();ctx.strokeStyle='#26343d';ctx.lineWidth=2.2;ctx.beginPath();ctx.moveTo(T.x,T.y);ctx.lineTo(L.x,L.y);ctx.lineTo(R.x,R.y);ctx.closePath();ctx.stroke();ctx.lineWidth=.8;ctx.strokeStyle='rgba(45,65,75,.24)';for(let p=10;p<100;p+=10){let a=bary(p,100-p,0,w,h),b=bary(p,0,100-p,w,h);line(ctx,a,b);a=bary(100-p,p,0,w,h);b=bary(0,p,100-p,w,h);line(ctx,a,b);a=bary(100-p,0,p,w,h);b=bary(0,100-p,p,w,h);line(ctx,a,b)}ctx.fillStyle='#c68d16';ctx.font='700 18px system-ui';ctx.textAlign='center';ctx.fillText('AREIA',T.x,T.y-22);ctx.fillStyle='#4f8f4b';ctx.textAlign='right';ctx.fillText('SILTE',L.x-10,L.y+30);ctx.fillStyle='#2c65a6';ctx.textAlign='left';ctx.fillText('ARGILA',R.x+10,R.y+30);ctx.font='600 11px system-ui';ctx.fillStyle='#304653';ctx.textAlign='center';for(let p=20;p<=80;p+=20){const a=bary(p,100-p,0,w,h);ctx.fillText(String(p),a.x-18,a.y+4);const b=bary(100-p,0,p,w,h);ctx.fillText(String(p),b.x+18,b.y+4);const cc=bary(0,100-p,p,w,h);ctx.fillText(String(p),cc.x,cc.y+18)}ctx.font='700 10px system-ui';ctx.fillStyle='rgba(32,53,64,.85)';LABELS.forEach(([key,s,si,cl])=>{const p=bary(s,si,cl,w,h);const label=PT[key].replace('Franco-','Franco-\n').replace('Argila ','Argila\n');const lines=label.split('\n');lines.forEach((t,i)=>ctx.fillText(t,p.x,p.y+i*12))});const [s,si,cl]=vals();if(validNums(s,si,cl)&&Math.abs(s+si+cl-100)<=.05){const p=bary(s,si,cl,w,h);ctx.beginPath();ctx.setLineDash([7,7]);ctx.strokeStyle='rgba(217,53,46,.55)';ctx.lineWidth=1.5;line(ctx,p,{x:p.x,y:L.y});ctx.setLineDash([]);ctx.shadowColor='rgba(0,0,0,.2)';ctx.shadowBlur=7;ctx.beginPath();ctx.arc(p.x,p.y,9,0,Math.PI*2);ctx.fillStyle='#ed221d';ctx.fill();ctx.lineWidth=3;ctx.strokeStyle='#fff';ctx.stroke();ctx.shadowBlur=0}ctx.restore()}
function update(){const [s,si,cl]=vals(),sum=s+si+cl;const ok=validNums(s,si,cl)&&Math.abs(sum-100)<=.05;$('ternarioSum').textContent=Number.isFinite(sum)?fmt(sum):'—';$('ternarioSum')?.parentElement.classList.toggle('is-error',!ok);$('ternarioValidation').textContent=!validNums(s,si,cl)?'Informe valores entre 0 e 100.':Math.abs(sum-100)>.05?'A soma deve ser 100 %. Use Normalizar apenas se os valores forem proporcionais.':'';const key=ok?classify(s,si,cl):null;$('resultSand').textContent=ok?fmt(s):'—';$('resultSilt').textContent=ok?fmt(si):'—';$('resultClay').textContent=ok?fmt(cl):'—';$('resultPoint').textContent=ok?`(${(Math.round(s*10)/10).toLocaleString('pt-BR')}, ${(Math.round(si*10)/10).toLocaleString('pt-BR')}, ${(Math.round(cl*10)/10).toLocaleString('pt-BR')})`:'—';$('ternarioClassPt').textContent=key?PT[key]:'—';$('ternarioClassEn').textContent=key?EN[key]:'—';$('ternarioClassDesc').textContent=key?DESC[key]:'Informe uma composição válida para classificar a amostra.';draw();if(key){window.ITA_TERNARIO_LAST={tool:'ternario_usda',version:'1.0',sample:$('ternarioSample')?.value||'',sand:s,silt:si,clay:cl,class_key:key,class_usda:EN[key],class_pt:PT[key],method:'USDA textural triangle',reference_ids:['REF-206','REF-207','REF-208'],created_at:new Date().toISOString()};window.dispatchEvent(new CustomEvent('ita:tool:result',{detail:window.ITA_TERNARIO_LAST}))}}
function normalize(){let [s,si,cl]=vals(),sum=s+si+cl;if(!validNums(s,si,cl)||sum<=0)return;[s,si,cl]=[s,si,cl].map(v=>v*100/sum);$('ternarioSand').value=s.toFixed(1);$('ternarioSilt').value=si.toFixed(1);$('ternarioClay').value=cl.toFixed(1);update()}
function clear(){['ternarioSand','ternarioSilt','ternarioClay'].forEach(id=>$(id).value='');update()}
function setMode(m){mode=m;document.querySelectorAll('[data-ternario-mode]').forEach(b=>b.classList.toggle('is-active',b.dataset.ternarioMode===m));$('ternarioModeBadge').textContent=m==='point'?'MOVER O PONTO':'INSERIR VALORES';$('ternarioHint').textContent=m==='point'?'Toque ou arraste o ponto vermelho dentro do triângulo.':'O ponto vermelho representa a composição informada.'}
function pointer(e){if(mode!=='point')return;const c=$('ternarioCanvas'),r=c.getBoundingClientRect(),x=(e.clientX-r.left)*c.width/r.width,y=(e.clientY-r.top)*c.height/r.height,v=inv(x,y,c.width,c.height);if(!v)return;$('ternarioSand').value=v[0].toFixed(1);$('ternarioSilt').value=v[1].toFixed(1);$('ternarioClay').value=(100-v[0]-v[1]).toFixed(1);const sum=+$('ternarioSand').value + +$('ternarioSilt').value + +$('ternarioClay').value;if(Math.abs(sum-100)>.01)$('ternarioClay').value=(+$('ternarioClay').value+(100-sum)).toFixed(1);update()}
function open(){document.getElementById('ferramentasModal')?.classList.remove('open');const m=$('ternarioModal');m?.classList.add('open');m?.setAttribute('aria-hidden','false');m?.classList.remove('is-subview');const sub=$('ternarioSubview');if(sub){sub.hidden=true;sub.setAttribute('aria-hidden','true')}setTimeout(()=>{background=null;draw();update()},40)}
function showSubview(kind){
 const modal=$('ternarioModal'),sub=$('ternarioSubview'),helpView=$('ternarioHelpView'),scienceView=$('ternarioScienceView'),title=$('ternarioSubviewTitle');
 if(!modal||!sub)return;
 const isScience=kind==='science';
 helpView?.toggleAttribute('hidden',isScience);
 scienceView?.toggleAttribute('hidden',!isScience);
 if(title)title.textContent=isScience?'Ciência e método':'Ajuda';
 sub.hidden=false;sub.setAttribute('aria-hidden','false');modal.classList.add('is-subview');
 sub.querySelector('.ita-ternario-subview-scroll')?.scrollTo({top:0,behavior:'instant'});
}
function returnToDiagram(){
 const modal=$('ternarioModal'),sub=$('ternarioSubview');
 if(!modal||!sub)return false;
 const active=modal.classList.contains('is-subview');
 if(!active)return false;
 modal.classList.remove('is-subview');sub.hidden=true;sub.setAttribute('aria-hidden','true');
 setTimeout(()=>{draw();update()},20);
 return true;
}
function help(){showSubview('help')}
function science(){showSubview('science')}
function close(id){const m=$(id);m?.classList.remove('open');m?.setAttribute('aria-hidden','true')}
function wire(){['ternarioSand','ternarioSilt','ternarioClay','ternarioSample'].forEach(id=>$(id)?.addEventListener('input',update));$('ternarioNormalize')?.addEventListener('click',normalize);$('ternarioClear')?.addEventListener('click',clear);document.querySelectorAll('[data-ternario-mode]').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.ternarioMode)));document.querySelectorAll('[data-ternario-help]').forEach(b=>b.addEventListener('click',help));document.querySelectorAll('[data-ternario-science]').forEach(b=>b.addEventListener('click',science));document.querySelectorAll('[data-ternario-return]').forEach(b=>b.addEventListener('click',returnToDiagram));document.querySelectorAll('[data-ternario-open-science]').forEach(b=>b.addEventListener('click',()=>showSubview('science')));document.querySelectorAll('[data-close="ternarioModal"]').forEach(b=>b.addEventListener('click',()=>{if(returnToDiagram())return;close('ternarioModal');document.getElementById('ferramentasModal')?.classList.add('open')}));document.querySelectorAll('[data-close="ternarioHelpModal"]').forEach(b=>b.addEventListener('click',()=>close('ternarioHelpModal')));const c=$('ternarioCanvas');c?.addEventListener('pointerdown',e=>{drag=true;c.setPointerCapture?.(e.pointerId);pointer(e)});c?.addEventListener('pointermove',e=>{if(drag)pointer(e)});['pointerup','pointercancel','pointerleave'].forEach(ev=>c?.addEventListener(ev,()=>drag=false));window.addEventListener('resize',()=>draw())}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
window.ITA_TERNARIO={version:'1.0.2',open,help,science,returnToDiagram,classify,update};
})();
