(function(){
'use strict';
const $=id=>document.getElementById(id),qa=(s,r=document)=>[...r.querySelectorAll(s)];
const rad=d=>d*Math.PI/180,deg=r=>r*180/Math.PI,norm=a=>((a%360)+360)%360;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const S={planes:[],showPlanes:true,showPoles:true};

function poleFromPlane(dipdir,dip){
 return {trend:norm(dipdir+180),plunge:90-dip};
}
function planeFromPole(trend,plunge){
 return {dipdir:norm(trend+180),dip:90-plunge};
}
function equalAreaPoint(trend,plunge,R=180,cx=200,cy=200){
 const colat=90-plunge;
 const rho=Math.SQRT2*Math.sin(rad(colat)/2);
 return {x:cx+R*rho*Math.sin(rad(trend)),y:cy-R*rho*Math.cos(rad(trend))};
}
function lowerGreatCircle(dipdir,dip){
 const strike=norm(dipdir-90),D=rad(dipdir),St=rad(strike),di=rad(dip);
 const s=[Math.sin(St),Math.cos(St),0];
 const d=[Math.cos(di)*Math.sin(D),Math.cos(di)*Math.cos(D),-Math.sin(di)];
 const pts=[];
 for(let i=0;i<=180;i+=2){
  const th=rad(i),v=[Math.cos(th)*s[0]+Math.sin(th)*d[0],Math.cos(th)*s[1]+Math.sin(th)*d[1],Math.sin(th)*d[2]];
  const trend=norm(deg(Math.atan2(v[0],v[1]))),plunge=deg(Math.asin(clamp(-v[2],-1,1)));
  pts.push(equalAreaPoint(trend,plunge));
 }
 return pts;
}
function meanPole(planes){
 if(!planes.length)return null;
 let x=0,y=0,z=0,n=0;
 planes.forEach(p=>{
  const po=poleFromPlane(p.dipdir,p.dip),T=rad(po.trend),P=rad(po.plunge);
  x+=Math.cos(P)*Math.sin(T);y+=Math.cos(P)*Math.cos(T);z+=Math.sin(P);n++;
 });
 const L=Math.hypot(x,y,z);if(!L)return null;
 const R=L/n;x/=L;y/=L;z/=L;
 const trend=norm(deg(Math.atan2(x,y))),plunge=deg(Math.asin(clamp(z,-1,1)));
 return {...planeFromPole(trend,plunge),pole_trend:trend,pole_plunge:plunge,vector_strength:R};
}
function svgEl(tag,attrs={}){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));return e}
function renderNet(){
 const svg=$('estereoSvg');if(!svg)return;svg.innerHTML='';
 const cx=200,cy=200,R=180;
 svg.appendChild(svgEl('circle',{cx,cy,r:R,fill:'#fff',stroke:'#57798a','stroke-width':'1.5'}));
 for(let a=0;a<360;a+=10){
  const t=rad(a),r1=a%30===0?R-8:R-4,r2=R;
  svg.appendChild(svgEl('line',{x1:cx+r1*Math.sin(t),y1:cy-r1*Math.cos(t),x2:cx+r2*Math.sin(t),y2:cy-r2*Math.cos(t),stroke:'#9eb4bf','stroke-width':a%30===0?'1':'0.6'}));
 }
 ['N','E','S','W'].forEach((txt,i)=>{
  const pos=[[200,15],[384,204],[200,394],[16,204]][i],te=svgEl('text',{x:pos[0],y:pos[1],'text-anchor':'middle','font-size':'11',fill:'#355c70','font-weight':'700'});te.textContent=txt;svg.appendChild(te)
 });
 if(S.showPlanes)S.planes.forEach(p=>{
  const pts=lowerGreatCircle(p.dipdir,p.dip),path=svgEl('path',{d:pts.map((q,i)=>(i?'L':'M')+q.x.toFixed(2)+' '+q.y.toFixed(2)).join(' '),fill:'none',stroke:'#54798c','stroke-width':'1.1','stroke-opacity':'.75'});svg.appendChild(path)
 });
 if(S.showPoles)S.planes.forEach(p=>{
  const po=poleFromPlane(p.dipdir,p.dip),q=equalAreaPoint(po.trend,po.plunge);
  svg.appendChild(svgEl('circle',{cx:q.x,cy:q.y,r:3.2,fill:'#183f55'}))
 });
 const m=meanPole(S.planes);
 if(m){
  const q=equalAreaPoint(m.pole_trend,m.pole_plunge);
  svg.appendChild(svgEl('circle',{cx:q.x,cy:q.y,r:6,fill:'none',stroke:'#111','stroke-width':'2'}));
 }
 renderStats(m);
}
function renderStats(m){
 $('estereoN').textContent=S.planes.length;
 $('estereoMeanDip').textContent=m?m.dip.toFixed(1)+'°':'—';
 $('estereoMeanDir').textContent=m?m.dipdir.toFixed(1)+'°':'—';
 $('estereoR').textContent=m?m.vector_strength.toFixed(3):'—';
 const box=$('estereoLista');
 box.innerHTML=S.planes.length?S.planes.map((p,i)=>`<div class="ita-struct-row"><b>#${i+1}</b><span>${p.dipdir.toFixed(1)}° dir</span><span>${p.dip.toFixed(1)}° dip</span><button type="button" class="ita-mini-danger" data-estereo-rm="${p.id}">×</button></div>`).join(''):'<div class="empty">Nenhuma medida carregada.</div>';
 qa('[data-estereo-rm]',box).forEach(b=>b.onclick=()=>{S.planes=S.planes.filter(x=>x.id!==b.dataset.estereoRm);renderNet()});
}
function addPlane(dipdir,dip,source='manual'){
 dipdir=Number(dipdir);dip=Number(dip);
 if(!Number.isFinite(dipdir)||!Number.isFinite(dip)||dip<0||dip>90)return false;
 S.planes.push({id:crypto.randomUUID?.()||String(Date.now()+Math.random()),dipdir:norm(dipdir),dip,source});
 renderNet();return true;
}
function importCampo(){
 const arr=window.ITA_CAMPO_MASTER?.state?.measures||[];
 let n=0;arr.forEach(m=>{const dd=Number(m.dip_direction??m.direction),d=Number(m.dip);if(Number.isFinite(dd)&&Number.isFinite(d)&&d>=0&&d<=90){addPlane(dd,d,'campo');n++}});
 $('estereoStatus').textContent=n?`${n} medidas válidas importadas do Caderno.`:'Nenhuma medida com dip e dip direction foi encontrada no Caderno.';
}
function downloadSvg(){
 const svg=$('estereoSvg');if(!svg)return;
 const blob=new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='ITA_ARANDU_estereograma.svg';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}
function smallestStrikeAngle(section,strike){
 let d=Math.abs(norm(section)-norm(strike));if(d>180)d=360-d;if(d>90)d=180-d;return d;
}
function apparentDip(trueDip,strike,sectionAz){
 const theta=smallestStrikeAngle(sectionAz,strike);
 return deg(Math.atan(Math.tan(rad(trueDip))*Math.sin(rad(theta))));
}
function trueDip(apparent,strike,sectionAz){
 const theta=smallestStrikeAngle(sectionAz,strike),s=Math.sin(rad(theta));
 if(Math.abs(s)<1e-10)return null;
 return deg(Math.atan(Math.tan(rad(apparent))/s));
}
function normalFromPlane(dipdir,dip){
 const po=poleFromPlane(dipdir,dip),T=rad(po.trend),P=rad(po.plunge);
 return [Math.cos(P)*Math.sin(T),Math.cos(P)*Math.cos(T),Math.sin(P)];
}
function intersectionPlanes(dd1,d1,dd2,d2){
 const a=normalFromPlane(dd1,d1),b=normalFromPlane(dd2,d2);
 let v=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
 let L=Math.hypot(...v);if(L<1e-10)return null;v=v.map(x=>x/L);
 if(v[2]<0)v=v.map(x=>-x);
 return {trend:norm(deg(Math.atan2(v[0],v[1]))),plunge:deg(Math.asin(clamp(v[2],-1,1)))};
}
function calc(){
 const mode=qa('.ita-calc-tabs button').find(b=>b.classList.contains('active'))?.dataset.calcMode||'convert';
 const out=$('calcResult');
 if(mode==='convert'){
  const dd=Number($('calcDipDir').value),st=Number($('calcStrike').value);
  if(Number.isFinite(dd)){out.innerHTML=`<b>${norm(dd-90).toFixed(1)}°</b><br>Strike RHR calculado a partir de dip direction ${norm(dd).toFixed(1)}°.`}
  else if(Number.isFinite(st)){out.innerHTML=`<b>${norm(st+90).toFixed(1)}°</b><br>Dip direction calculado a partir de strike RHR ${norm(st).toFixed(1)}°.`}
  else out.textContent='Informe dip direction ou strike RHR.';
 }
 if(mode==='apparent'){
  const td=Number($('calcTrueDip').value),st=Number($('calcAppStrike').value),sec=Number($('calcSectionAz').value),ap=Number($('calcAppDip').value);
  if(Number.isFinite(td)&&Number.isFinite(st)&&Number.isFinite(sec)){const v=apparentDip(td,st,sec);out.innerHTML=`<b>${v.toFixed(2)}°</b><br>Mergulho aparente.`}
  else if(Number.isFinite(ap)&&Number.isFinite(st)&&Number.isFinite(sec)){const v=trueDip(ap,st,sec);out.innerHTML=v==null?'Geometria indeterminada quando a seção é paralela ao strike.':`<b>${v.toFixed(2)}°</b><br>Mergulho verdadeiro calculado.`}
  else out.textContent='Informe strike e azimute da seção, mais o mergulho verdadeiro ou aparente.';
 }
 if(mode==='intersection'){
  const vals=['calcDD1','calcD1','calcDD2','calcD2'].map(id=>Number($(id).value));
  if(vals.every(Number.isFinite)){const v=intersectionPlanes(...vals);out.innerHTML=v?`<b>${v.trend.toFixed(1)}° / ${v.plunge.toFixed(1)}°</b><br>Trend / plunge da linha de interseção.`:'Planos paralelos ou numericamente indistinguíveis.'}
  else out.textContent='Informe dip direction e dip dos dois planos.';
 }
}
function open(id){$(id)?.classList.add('open');$(id)?.setAttribute('aria-hidden','false')}
function close(id){$(id)?.classList.remove('open');$(id)?.setAttribute('aria-hidden','true')}
function wire(){
 $('abrirEstereogramaArandu')?.addEventListener('click',()=>{open('estereogramaAranduModal');renderNet()});
 $('abrirCalculadoraEstrutural')?.addEventListener('click',()=>open('calculadoraEstruturalModal'));
 qa('[data-close="estereogramaAranduModal"]').forEach(b=>b.onclick=()=>close('estereogramaAranduModal'));
 qa('[data-close="calculadoraEstruturalModal"]').forEach(b=>b.onclick=()=>close('calculadoraEstruturalModal'));
 $('estereoAdd')?.addEventListener('click',()=>{if(!addPlane($('estereoDipDir').value,$('estereoDip').value))$('estereoStatus').textContent='Dip direction deve ser numérico e dip deve estar entre 0° e 90°.'});
 $('estereoImportCampo')?.addEventListener('click',importCampo);
 $('estereoClear')?.addEventListener('click',()=>{S.planes=[];renderNet()});
 $('estereoSvgDownload')?.addEventListener('click',downloadSvg);
 $('estereoShowPlanes')?.addEventListener('change',e=>{S.showPlanes=e.target.checked;renderNet()});
 $('estereoShowPoles')?.addEventListener('change',e=>{S.showPoles=e.target.checked;renderNet()});
 qa('.ita-calc-tabs button').forEach(b=>b.onclick=()=>{qa('.ita-calc-tabs button').forEach(x=>x.classList.toggle('active',x===b));qa('.ita-calc-pane').forEach(p=>p.classList.toggle('active',p.dataset.calcPane===b.dataset.calcMode));$('calcResult').textContent='Preencha os campos e calcule.'});
 $('calcRun')?.addEventListener('click',calc);
 $('campoAbrirEstereograma')?.addEventListener('click',()=>$('abrirEstereogramaArandu')?.click());
 $('campoAbrirCalculadora')?.addEventListener('click',()=>$('abrirCalculadoraEstrutural')?.click());
 renderNet();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
window.ITA_ESTRUTURAL={version:'1.0',poleFromPlane,planeFromPole,equalAreaPoint,lowerGreatCircle,meanPole,apparentDip,trueDip,intersectionPlanes,state:S};
})();
