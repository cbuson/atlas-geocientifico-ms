(function(){
'use strict';
const $=id=>document.getElementById(id);
const qa=(s,r=document)=>[...r.querySelectorAll(s)];
const S={sensor:null,window:[],kind:null};
const rad=d=>d*Math.PI/180,deg=r=>r*180/Math.PI,norm=a=>((a%360)+360)%360;
const mean=a=>{const v=a.filter(Number.isFinite);return v.length?v.reduce((x,y)=>x+y,0)/v.length:null};
const sd=a=>{const v=a.filter(Number.isFinite),m=mean(v);return v.length>1?Math.sqrt(v.reduce((s,x)=>s+(x-m)**2,0)/(v.length-1)):null};
const circMean=a=>{const v=a.filter(Number.isFinite);if(!v.length)return null;return norm(deg(Math.atan2(mean(v.map(x=>Math.sin(rad(x)))),mean(v.map(x=>Math.cos(rad(x)))))))};
const circSd=a=>{const v=a.filter(Number.isFinite);if(v.length<2)return null;const x=mean(v.map(a=>Math.cos(rad(a)))),y=mean(v.map(a=>Math.sin(rad(a)))),R=Math.min(1,Math.hypot(x,y));return deg(Math.sqrt(Math.max(0,-2*Math.log(Math.max(R,1e-8)))))};

function rotationNormal(alpha,beta,gamma){
 const a=rad(alpha||0),b=rad(beta||0),g=rad(gamma||0);
 const ca=Math.cos(a),sa=Math.sin(a),cb=Math.cos(b),sb=Math.sin(b),cg=Math.cos(g),sg=Math.sin(g);
 return {x:cg*sa*sb+ca*sg,y:sa*sg-ca*cg*sb,z:cb*cg};
}
function planeTilt(alpha,beta,gamma){
 let n=rotationNormal(alpha,beta,gamma);
 if(n.z<0)n={x:-n.x,y:-n.y,z:-n.z};
 return {tilt:deg(Math.atan2(Math.hypot(n.x,n.y),Math.abs(n.z))),nx:n.x,ny:n.y,nz:n.z};
}
function flatHeading(alpha){return norm(360-alpha)}
function compassHeading(alpha,beta,gamma){
 if(![alpha,beta,gamma].every(Number.isFinite))return null;
 const x=rad(beta),y=rad(gamma),z=rad(alpha);
 const cX=Math.cos(x),cY=Math.cos(y),cZ=Math.cos(z),sX=Math.sin(x),sY=Math.sin(y),sZ=Math.sin(z);
 const Vx=-cZ*sY-sZ*sX*cY, Vy=-sZ*sY+cZ*sX*cY;
 if(Math.abs(Vx)<1e-12&&Math.abs(Vy)<1e-12)return flatHeading(alpha);
 let h=Math.atan2(Vx,Vy);
 return norm(deg(h));
}
function headingFromEvent(e){
 if(Number.isFinite(e.webkitCompassHeading))return {heading:norm(e.webkitCompassHeading),absolute:true,source:'webkitCompassHeading'};
 const a=Number(e.alpha),b=Number(e.beta),g=Number(e.gamma);
 if(!Number.isFinite(a))return {heading:null,absolute:false,source:'none'};
 const tilt=planeTilt(a,b,g).tilt;
 const h=tilt<18?flatHeading(a):compassHeading(a,b,g);
 return {heading:h,absolute:!!e.absolute,source:e.absolute?'deviceorientation_absolute':'deviceorientation_relative'};
}
function onOrientation(e){
 const h=headingFromEvent(e),lv=planeTilt(Number(e.alpha),Number(e.beta),Number(e.gamma));
 S.sensor={heading:h.heading,absolute:h.absolute,source:h.source,alpha:e.alpha,beta:e.beta,gamma:e.gamma,tilt:lv.tilt,nx:lv.nx,ny:lv.ny,nz:lv.nz,time:new Date().toISOString()};
 S.window.push({heading:h.heading,tilt:lv.tilt});
 if(S.window.length>30)S.window.shift();
 renderCompass();renderLevel();
}
async function requestSensors(kind){
 try{
  S.kind=kind;
  if(typeof DeviceOrientationEvent==='undefined')throw new Error('DeviceOrientationEvent indisponível');
  if(typeof DeviceOrientationEvent.requestPermission==='function'){
   const p=await DeviceOrientationEvent.requestPermission(kind==='compass');
   if(p!=='granted')throw new Error('Permissão não concedida');
  }
  window.addEventListener('deviceorientationabsolute',onOrientation,true);
  window.addEventListener('deviceorientation',onOrientation,true);
  const st=$(kind==='compass'?'bussolaStatus':'nivelStatus');
  if(st)st.textContent='Sensores ativos. Mantenha o dispositivo estável e longe de fontes de interferência.';
 }catch(err){
  const st=$(kind==='compass'?'bussolaStatus':'nivelStatus');
  if(st)st.textContent='Sensores indisponíveis · '+err.message;
 }
}
function quality(kind){
 if(!S.sensor||S.window.length<8)return{state:'red',label:'aguardando'};
 if(kind==='compass'){
  const d=circSd(S.window.map(x=>x.heading));
  if(S.sensor.absolute&&Number.isFinite(d)&&d<=3)return{state:'green',label:'estável'};
  if(Number.isFinite(d)&&d<=8)return{state:'yellow',label:S.sensor.absolute?'moderada':'referência relativa'};
  return{state:'red',label:'instável'};
 }
 const d=sd(S.window.map(x=>x.tilt));
 if(Number.isFinite(d)&&d<=0.6)return{state:'green',label:'estável'};
 if(Number.isFinite(d)&&d<=2)return{state:'yellow',label:'moderada'};
 return{state:'red',label:'instável'};
}
function renderCompass(){
 if(!$('bussolaHeading'))return;
 const q=quality('compass'),h=S.sensor?.heading,decl=Number($('bussolaDeclinacao')?.value),trueH=Number.isFinite(h)&&Number.isFinite(decl)?norm(h+decl):null;
 $('bussolaHeading').textContent=Number.isFinite(h)?h.toFixed(1)+'°':'—';
 $('bussolaReferencia').textContent=S.sensor?.absolute?'absoluta / magnética':'relativa / não confiável para norte';
 $('bussolaFonte').textContent=S.sensor?.source||'—';
 $('bussolaDesvio').textContent=Number.isFinite(circSd(S.window.map(x=>x.heading)))?circSd(S.window.map(x=>x.heading)).toFixed(1)+'°':'—';
 $('bussolaTrue').textContent=Number.isFinite(trueH)?trueH.toFixed(1)+'°':'—';
 $('bussolaQuality').textContent=q.label;$('bussolaQuality').className='ita-sensor-quality '+q.state;
 const needle=$('bussolaNeedle');if(needle&&Number.isFinite(h))needle.style.transform=`translate(-50%,-100%) rotate(${-h}deg)`;
}
function renderLevel(){
 if(!$('nivelTilt'))return;
 const q=quality('level'),t=S.sensor?.tilt;
 $('nivelTilt').textContent=Number.isFinite(t)?t.toFixed(1)+'°':'—';
 $('nivelBeta').textContent=Number.isFinite(S.sensor?.beta)?Number(S.sensor.beta).toFixed(1)+'°':'—';
 $('nivelGamma').textContent=Number.isFinite(S.sensor?.gamma)?Number(S.sensor.gamma).toFixed(1)+'°':'—';
 $('nivelDesvio').textContent=Number.isFinite(sd(S.window.map(x=>x.tilt)))?sd(S.window.map(x=>x.tilt)).toFixed(2)+'°':'—';
 $('nivelQuality').textContent=q.label;$('nivelQuality').className='ita-sensor-quality '+q.state;
 const b=$('nivelBubble');
 if(b&&S.sensor){
  const x=Math.max(-1,Math.min(1,S.sensor.nx))*110,y=Math.max(-1,Math.min(1,-S.sensor.ny))*110;
  b.style.transform=`translate(calc(-50% + ${x}px),calc(-50% + ${y}px))`;
 }
}
function fillMeasure(data){
 $('campoAddMedida')?.click();
 const card=qa('#campoMedidasLista [data-measure]').at(-1);
 if(!card)return false;
 const set=(k,v)=>{const e=card.querySelector(`[data-k="${k}"]`);if(e){e.value=v??'';e.dispatchEvent(new Event('change',{bubbles:true}))}};
 set('type','outro');set('direction',data.direction);set('dip',data.dip);set('method',data.method);set('instrument',data.instrument);set('precision',data.precision);
 return true;
}
function addCompass(){
 const h=S.sensor?.heading;if(!Number.isFinite(h)){alert('Ative os sensores antes de registrar.');return}
 const decl=Number($('bussolaDeclinacao')?.value),dir=Number.isFinite(decl)?norm(h+decl):h,q=quality('compass'),disp=circSd(S.window.map(x=>x.heading));
 const ok=fillMeasure({direction:dir,dip:'',method:Number.isFinite(decl)?'bussola_sensor_com_declinação_manual':'bussola_sensor_dispositivo',instrument:'ITA ARANDU · DeviceOrientationEvent',precision:`referencia=${S.sensor.absolute?'absoluta':'relativa'}; dispersao=${Number.isFinite(disp)?disp.toFixed(2):'NA'}°; qualidade=${q.label}`});
 $('bussolaStatus').textContent=ok?'Azimute adicionado como medida auxiliar no Caderno.':'Abra uma estação do Campo para adicionar a medida.';
}
function addLevel(){
 const t=S.sensor?.tilt;if(!Number.isFinite(t)){alert('Ative os sensores antes de registrar.');return}
 const q=quality('level'),d=sd(S.window.map(x=>x.tilt));
 const ok=fillMeasure({direction:'',dip:t,method:'nivel_digital_plano_tela',instrument:'ITA ARANDU · DeviceOrientationEvent',precision:`dispersao=${Number.isFinite(d)?d.toFixed(2):'NA'}°; qualidade=${q.label}`});
 $('nivelStatus').textContent=ok?'Inclinação adicionada como medida auxiliar no Caderno.':'Abra uma estação do Campo para adicionar a medida.';
}
function open(id){$(id)?.classList.add('open');$(id)?.setAttribute('aria-hidden','false')}
function close(id){$(id)?.classList.remove('open');$(id)?.setAttribute('aria-hidden','true')}
function wire(){
 $('abrirBussolaArandu')?.addEventListener('click',()=>open('bussolaAranduModal'));
 $('abrirNivelArandu')?.addEventListener('click',()=>open('nivelAranduModal'));
 qa('[data-close="bussolaAranduModal"]').forEach(b=>b.addEventListener('click',()=>close('bussolaAranduModal')));
 qa('[data-close="nivelAranduModal"]').forEach(b=>b.addEventListener('click',()=>close('nivelAranduModal')));
 $('bussolaAtivar')?.addEventListener('click',()=>requestSensors('compass'));
 $('nivelAtivar')?.addEventListener('click',()=>requestSensors('level'));
 $('bussolaDeclinacao')?.addEventListener('input',renderCompass);
 $('bussolaAdicionarCampo')?.addEventListener('click',addCompass);
 $('nivelAdicionarCampo')?.addEventListener('click',addLevel);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
window.ITA_BUSSOLA_NIVEL={version:'1.0',flatHeading,compassHeading,planeTilt,quality};
})();
