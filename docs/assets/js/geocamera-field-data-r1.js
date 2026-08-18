(()=>{
'use strict';

const $=id=>document.getElementById(id);
const STATE={
  gps:null,
  heading:null,
  headingSource:null,
  tilt:null,
  orientationActive:false,
  lastBlob:null,
  lastMeta:null,
  lastObjectUrl:null,
  lastUpdate:0
};

const norm360=n=>((Number(n)%360)+360)%360;
const card=d=>{
  const pts=['N','NE','E','SE','S','SW','W','NW'];
  return pts[Math.round(norm360(d)/45)%8];
};
const fnum=(n,d=5)=>Number.isFinite(Number(n))?Number(n).toFixed(d):'—';
const fmtAlt=n=>Number.isFinite(Number(n))?`${Math.round(Number(n))} m`:'—';
const fmtAcc=n=>Number.isFinite(Number(n))?`±${Math.round(Number(n))} m`:'—';
const fmtHeading=n=>Number.isFinite(Number(n))?`${Math.round(norm360(n))}° ${card(n)}`:'—';
const fmtTilt=n=>Number.isFinite(Number(n))?`${Number(n)>=0?'+':''}${Math.round(Number(n))}°`:'—';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function getModal(){return $('geocameraModal')}
function getView(){return getModal()?.querySelector('.ita-geocamera-view')}
function getVideo(){return $('geoCameraVideo')}

function ensureUI(){
  const modal=getModal(),view=getView();
  if(!modal||!view||view.dataset.geoFieldR1==='1')return;
  view.dataset.geoFieldR1='1';

  view.insertAdjacentHTML('beforeend',`
    <div class="geo-field-brand" aria-hidden="true">
      <div class="geo-field-hex"><span>i</span></div>
      <div class="geo-field-brand-copy"><b>ITA ARANDU MS</b><small>Atlas geocientífico de Mato Grosso do Sul</small></div>
      <img src="./assets/img/ms-outline-ibge.svg" alt="" class="geo-field-ms">
    </div>
    <div class="geo-field-gps" id="geoFieldGpsBadge"><span></span>GPS</div>
    <div class="geo-field-strip" id="geoFieldStrip">
      <div><b id="geoFieldLat">—</b><small>Lat</small></div>
      <div><b id="geoFieldLon">—</b><small>Long</small></div>
      <div><b id="geoFieldAcc">—</b><small>Prec.</small></div>
      <div><b id="geoFieldAlt">—</b><small>Alt.</small></div>
      <div><b id="geoFieldHeading">—</b><small>Rumbo</small></div>
      <div><b id="geoFieldTilt">—</b><small>Inclinação</small></div>
      <div><b id="geoFieldTime">—</b><small>Data · hora</small></div>
    </div>`);

  const oldHud=view.querySelector('.ita-geocamera-hud');
  if(oldHud) oldHud.hidden=true;

  const video=getVideo();
  if(video){
    video.addEventListener('loadedmetadata',()=>{
      if(video.videoWidth&&video.videoHeight){
        view.style.setProperty('--geo-camera-ratio',`${video.videoWidth} / ${video.videoHeight}`);
      }
    });
  }
  updateUI();
}

function updateUI(){
  ensureUI();
  const g=STATE.gps||{};
  if($('geoFieldLat')) $('geoFieldLat').textContent=Number.isFinite(g.lat)?g.lat.toFixed(5):'—';
  if($('geoFieldLon')) $('geoFieldLon').textContent=Number.isFinite(g.lon)?g.lon.toFixed(5):'—';
  if($('geoFieldAcc')) $('geoFieldAcc').textContent=fmtAcc(g.accuracy);
  if($('geoFieldAlt')) $('geoFieldAlt').textContent=fmtAlt(g.altitude);
  if($('geoFieldHeading')) $('geoFieldHeading').textContent=fmtHeading(STATE.heading);
  if($('geoFieldTilt')) $('geoFieldTilt').textContent=fmtTilt(STATE.tilt);
  const now=new Date();
  if($('geoFieldTime')) $('geoFieldTime').textContent=now.toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit',year:'numeric'})+' '+now.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
  const badge=$('geoFieldGpsBadge');
  if(badge) badge.classList.toggle('active',!!(Number.isFinite(g.lat)&&Number.isFinite(g.lon)));
}

function captureGps(){
  if(!navigator.geolocation)return Promise.reject(new Error('Geolocalização indisponível.'));
  return new Promise((resolve,reject)=>{
    navigator.geolocation.getCurrentPosition(p=>{
      STATE.gps={
        lat:p.coords.latitude,
        lon:p.coords.longitude,
        accuracy:Number.isFinite(p.coords.accuracy)?p.coords.accuracy:null,
        altitude:Number.isFinite(p.coords.altitude)?p.coords.altitude:null,
        altitudeAccuracy:Number.isFinite(p.coords.altitudeAccuracy)?p.coords.altitudeAccuracy:null,
        timestamp:p.timestamp||Date.now()
      };
      updateUI();
      resolve(STATE.gps);
    },reject,{enableHighAccuracy:true,timeout:15000,maximumAge:0});
  });
}

function orientationHandler(e){
  const now=performance.now();
  if(now-STATE.lastUpdate<120)return;
  STATE.lastUpdate=now;

  let h=null,src=null;
  if(Number.isFinite(e.webkitCompassHeading)){
    h=norm360(e.webkitCompassHeading);src='webkitCompassHeading';
  }else if(Number.isFinite(e.alpha)){
    h=norm360(360-e.alpha);src=e.absolute?'deviceorientationabsolute':'deviceorientation';
  }
  if(Number.isFinite(h)){STATE.heading=h;STATE.headingSource=src}

  if(Number.isFinite(e.beta)){
    let t=Number(e.beta)-90;
    while(t>180)t-=360;
    while(t<-180)t+=360;
    if(t>90)t=180-t;
    if(t<-90)t=-180-t;
    STATE.tilt=Math.max(-90,Math.min(90,t));
  }
  updateUI();
}

async function enableOrientation(){
  if(STATE.orientationActive)return true;
  try{
    if(typeof DeviceOrientationEvent!=='undefined' && typeof DeviceOrientationEvent.requestPermission==='function'){
      const p=await DeviceOrientationEvent.requestPermission();
      if(p!=='granted')throw new Error('Permissão de orientação não concedida.');
    }
    window.addEventListener('deviceorientationabsolute',orientationHandler,true);
    window.addEventListener('deviceorientation',orientationHandler,true);
    STATE.orientationActive=true;
    return true;
  }catch(e){
    console.warn('GeoCâmera orientação',e);
    return false;
  }
}

function drawHex(ctx,cx,cy,r){
  ctx.beginPath();
  for(let i=0;i<6;i++){
    const a=Math.PI/3*i-Math.PI/6;
    const x=cx+r*Math.cos(a),y=cy+r*Math.sin(a);
    if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
  }
  ctx.closePath();
}

async function drawBrand(ctx,w,h){
  const scale=Math.max(1,w/1200);
  const pad=20*scale;
  const boxW=Math.min(w*.43,420*scale), boxH=74*scale;
  ctx.save();
  ctx.fillStyle='rgba(3,24,36,.63)';
  roundRect(ctx,pad,pad,boxW,boxH,11*scale);ctx.fill();

  const cx=pad+38*scale,cy=pad+boxH/2,r=26*scale;
  drawHex(ctx,cx,cy,r);ctx.fillStyle='#073b63';ctx.fill();ctx.lineWidth=2*scale;ctx.strokeStyle='#fff';ctx.stroke();
  ctx.fillStyle='#fff';ctx.font=`700 ${40*scale}px Georgia,serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('i',cx,cy+1*scale);

  ctx.textAlign='left';ctx.textBaseline='alphabetic';
  ctx.font=`700 ${17*scale}px Arial,sans-serif`;ctx.fillText('ITA ARANDU MS',pad+74*scale,pad+30*scale);
  ctx.font=`400 ${11*scale}px Arial,sans-serif`;ctx.fillText('Atlas geocientífico de Mato Grosso do Sul',pad+74*scale,pad+50*scale);

  try{
    const img=await loadImage('./assets/img/ms-outline-ibge.svg');
    ctx.globalAlpha=.9;
    ctx.drawImage(img,pad+boxW-58*scale,pad+11*scale,46*scale,52*scale);
  }catch(_){}
  ctx.restore();
}

function roundRect(ctx,x,y,w,h,r){
  const rr=Math.min(r,w/2,h/2);
  ctx.beginPath();ctx.moveTo(x+rr,y);ctx.arcTo(x+w,y,x+w,y+h,rr);ctx.arcTo(x+w,y+h,x,y+h,rr);ctx.arcTo(x,y+h,x,y,rr);ctx.arcTo(x,y,x+w,y,rr);ctx.closePath();
}
function loadImage(src){
  return new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=rej;i.src=src});
}
function fitText(ctx,text,maxW,start){
  let size=start;
  while(size>10 && ctx.measureText(text).width>maxW){size-=1;ctx.font=ctx.font.replace(/\d+(?:\.\d+)?px/,`${size}px`)}
  return size;
}

async function makeAnnotatedBlob(){
  const video=getVideo();
  if(!video?.srcObject||!video.videoWidth)throw new Error('Ative a câmera antes de fotografar.');

  try{await captureGps()}catch(_){}
  await enableOrientation();

  // R2 · preserva a resolução integral entregue pelo stream da câmera.
  // Não reduz mais a imagem a 2400 px.
  const w=video.videoWidth,h=video.videoHeight;
  const c=document.createElement('canvas');c.width=w;c.height=h;
  const ctx=c.getContext('2d',{alpha:false});
  ctx.drawImage(video,0,0,w,h);

  await drawBrand(ctx,w,h);

  const S=Math.max(1,w/1200);
  // Faixa mais fina, legível e muito transparente.
  const stripH=Math.max(78*S,Math.min(h*.105,116*S));
  const x=18*S,y=h-stripH-18*S,boxW=w-36*S;
  ctx.fillStyle='rgba(5,21,29,.34)';
  roundRect(ctx,x,y,boxW,stripH,13*S);ctx.fill();

  const g=STATE.gps||{};
  const values=[
    [Number.isFinite(g.lat)?g.lat.toFixed(5):'—','Lat'],
    [Number.isFinite(g.lon)?g.lon.toFixed(5):'—','Long'],
    [fmtAcc(g.accuracy),'Prec.'],
    [fmtAlt(g.altitude),'Alt.'],
    [fmtHeading(STATE.heading),'Rumbo'],
    [fmtTilt(STATE.tilt),'Inclinação'],
    [new Date().toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit',year:'numeric'})+' '+new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'}),'Data · hora']
  ];
  const colW=boxW/values.length;
  values.forEach(([v,l],i)=>{
    const cx=x+i*colW;
    if(i){ctx.strokeStyle='rgba(255,255,255,.42)';ctx.lineWidth=1*S;ctx.beginPath();ctx.moveTo(cx,y+15*S);ctx.lineTo(cx,y+stripH-15*S);ctx.stroke()}
    ctx.fillStyle='#fff';ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.font=`700 ${19*S}px Arial,sans-serif`;
    fitText(ctx,String(v),colW-12*S,19*S);
    ctx.fillText(String(v),cx+colW/2,y+stripH*.42);
    ctx.fillStyle='rgba(255,255,255,.96)';ctx.font=`600 ${13*S}px Arial,sans-serif`;
    ctx.fillText(l,cx+colW/2,y+stripH*.70);
  });

  const blob=await new Promise((res,rej)=>c.toBlob(b=>b?res(b):rej(new Error('Falha ao gerar JPEG.')),'image/jpeg',.98));
  STATE.lastBlob=blob;
  STATE.lastMeta={
    captured_at_utc:new Date().toISOString(),
    type:$('geoCameraTipo')?.value||null,
    station:$('geoCameraEstacao')?.value.trim()||null,
    sample:$('geoCameraAmostra')?.value.trim()||null,
    note:$('geoCameraNota')?.value.trim()||null,
    gps:STATE.gps,
    heading_deg:Number.isFinite(STATE.heading)?STATE.heading:null,
    heading_cardinal:Number.isFinite(STATE.heading)?card(STATE.heading):null,
    heading_source:STATE.headingSource,
    camera_tilt_estimated_deg:Number.isFinite(STATE.tilt)?STATE.tilt:null,
    orientation_note:'Rumo e inclinação dependem dos sensores disponíveis no dispositivo e devem ser tratados como leituras de campo assistidas.'
  };
  window.ITA_GEOCAMERA_LAST={...STATE.lastMeta,blob};
  return blob;
}

async function enhancedCapture(ev){
  const btn=ev.target.closest?.('#geoCameraCapture');
  if(!btn)return;
  ev.preventDefault();ev.stopImmediatePropagation();
  try{
    const status=$('geoCameraStatus');if(status)status.textContent='Capturando imagem e dados de campo…';
    const blob=await makeAnnotatedBlob();
    const meta=$('geoCameraMeta');
    if(meta)meta.textContent=[
      STATE.lastMeta.type?`tipo ${STATE.lastMeta.type}`:'',
      STATE.lastMeta.gps?`GPS ${STATE.lastMeta.gps.lat.toFixed(6)}, ${STATE.lastMeta.gps.lon.toFixed(6)}`:'GPS não capturado',
      Number.isFinite(STATE.heading)?`rumo ${fmtHeading(STATE.heading)}`:'rumo não disponível',
      Number.isFinite(STATE.tilt)?`inclinação ${fmtTilt(STATE.tilt)}`:'inclinação não disponível'
    ].filter(Boolean).join(' · ');
    if($('geoCameraResult'))$('geoCameraResult').hidden=false;
    if(status)status.textContent='Captura georreferenciada pronta para revisão.';
    previewCaptured(blob);
  }catch(e){
    if($('geoCameraStatus'))$('geoCameraStatus').textContent=e.message;
  }
}

function previewCaptured(blob){
  const view=getView(),canvas=$('geoCameraCanvas'),video=getVideo();
  if(!view||!canvas)return;
  if(STATE.lastObjectUrl)URL.revokeObjectURL(STATE.lastObjectUrl);
  STATE.lastObjectUrl=URL.createObjectURL(blob);
  const img=new Image();
  img.onload=()=>{
    canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;
    canvas.getContext('2d').drawImage(img,0,0);
    canvas.hidden=false;
    if(video)video.style.visibility='hidden';
    view.style.setProperty('--geo-camera-ratio',`${img.naturalWidth} / ${img.naturalHeight}`);
  };
  img.src=STATE.lastObjectUrl;
}

function enhancedDownload(ev){
  const btn=ev.target.closest?.('#geoCameraDownload');
  if(!btn||!STATE.lastBlob)return;
  ev.preventDefault();ev.stopImmediatePropagation();
  const a=document.createElement('a');
  a.href=URL.createObjectURL(STATE.lastBlob);
  a.download=`ITA_ARANDU_GEOCAMERA_${new Date().toISOString().replace(/[:.]/g,'-')}.jpg`;
  a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1500);

  const metaBlob=new Blob([JSON.stringify(STATE.lastMeta,null,2)],{type:'application/json'});
  const m=document.createElement('a');m.href=URL.createObjectURL(metaBlob);
  m.download=a.download.replace(/\.jpg$/i,'.json');m.click();setTimeout(()=>URL.revokeObjectURL(m.href),1500);
}

function clearPreview(ev){
  const btn=ev.target.closest?.('#geoCameraClear');
  if(!btn)return;
  const canvas=$('geoCameraCanvas'),video=getVideo();
  if(canvas)canvas.hidden=true;
  if(video)video.style.visibility='visible';
  STATE.lastBlob=null;STATE.lastMeta=null;
}

async function locateIntercept(ev){
  const btn=ev.target.closest?.('#geoCameraLocate');
  if(!btn)return;
  try{await captureGps()}catch(_){}
  await enableOrientation();
}
async function startIntercept(ev){
  const btn=ev.target.closest?.('#geoCameraStart');
  if(!btn)return;
  setTimeout(()=>{captureGps().catch(()=>{});enableOrientation();},300);
}

document.addEventListener('click',enhancedCapture,true);
document.addEventListener('click',enhancedDownload,true);
document.addEventListener('click',clearPreview,true);
document.addEventListener('click',locateIntercept,true);
document.addEventListener('click',startIntercept,true);

const obs=new MutationObserver(()=>ensureUI());
obs.observe(document.documentElement,{childList:true,subtree:true});
document.addEventListener('DOMContentLoaded',ensureUI);
setInterval(()=>{if(getModal()?.classList.contains('open'))updateUI()},1000);

window.ITA_GEOCAMERA_FIELD_R1={state:STATE,captureGps,enableOrientation};
})();
