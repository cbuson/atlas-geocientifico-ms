(function(){
'use strict';
const $=id=>document.getElementById(id);
const S={stream:null,blob:null,cameras:[]};
function status(s){if($('macroGeoStatus'))$('macroGeoStatus').textContent=s}
function stop(){
 if(S.stream){window.ITA_CAMERA_CORE?.stop(S.stream);S.stream=null}
 if($('macroGeoVideo'))$('macroGeoVideo').srcObject=null;
}
async function fillDevices(){
 try{
  S.cameras=await window.ITA_CAMERA_CORE.cameras();
  const sel=$('macroGeoDevice');
  const old=sel.value;
  sel.innerHTML='<option value="">traseira preferencial</option>'+
   S.cameras.map((d,i)=>`<option value="${d.deviceId}">${(d.label||('câmera '+(i+1))).replace(/[<>]/g,'')}</option>`).join('');
  if([...sel.options].some(o=>o.value===old))sel.value=old;
 }catch{}
}
async function configureCapabilities(){
 const cap=window.ITA_CAMERA_CORE.capabilities(S.stream);
 const zoom=$('macroGeoZoom'),help=$('macroGeoZoomHelp');
 if(cap.zoom && Number.isFinite(cap.zoom.min) && Number.isFinite(cap.zoom.max)){
  zoom.min=cap.zoom.min;zoom.max=cap.zoom.max;zoom.step=cap.zoom.step||0.1;
  const track=S.stream.getVideoTracks()[0];
  const current=track.getSettings?.().zoom||cap.zoom.min;
  zoom.value=current;zoom.disabled=false;
  help.textContent=`Zoom suportado pelo dispositivo · ${cap.zoom.min}× a ${cap.zoom.max}×`;
 }else{
  zoom.disabled=true;zoom.min=1;zoom.max=1;zoom.value=1;
  help.textContent='Controle de zoom não exposto pelo navegador. A imagem continua operacional sem zoom programático.';
 }
 // Prefer continuous focus when exposed.
 if(Array.isArray(cap.focusMode) && cap.focusMode.includes('continuous')){
  try{await window.ITA_CAMERA_CORE.apply(S.stream,{focusMode:'continuous'})}catch{}
 }
}
async function start(){
 try{
  stop();
  status('Solicitando câmera…');
  S.stream=await window.ITA_CAMERA_CORE.open({deviceId:$('macroGeoDevice').value||'',facingMode:'environment'});
  const v=$('macroGeoVideo');v.srcObject=S.stream;await v.play();
  await fillDevices();await configureCapabilities();
  const settings=S.stream.getVideoTracks()[0]?.getSettings?.()||{};
  $('macroGeoPlate').textContent=`MacroGeo · ${settings.width||'—'}×${settings.height||'—'} · ${settings.facingMode||'câmera ativa'}`;
  status('Câmera ativa. Aproxime sem perder foco e mantenha o telefone estável.');
 }catch(e){
  status('Câmera indisponível · '+(window.ITA_CAMERA_CORE?.describeError(e)||e.message));
 }
}
async function setZoom(){
 if(!S.stream||$('macroGeoZoom').disabled)return;
 try{await window.ITA_CAMERA_CORE.apply(S.stream,{zoom:Number($('macroGeoZoom').value)})}
 catch(e){status('O dispositivo recusou o zoom programático. A câmera continua ativa.')}
}
async function capture(){
 try{
  const v=$('macroGeoVideo');
  if(!v?.srcObject||!v.videoWidth)throw new Error('Ative a câmera antes de fotografar');
  const c=$('macroGeoCanvas'),max=2200,scale=Math.min(1,max/Math.max(v.videoWidth,v.videoHeight));
  c.width=Math.round(v.videoWidth*scale);c.height=Math.round(v.videoHeight*scale);
  const x=c.getContext('2d');x.drawImage(v,0,0,c.width,c.height);
  const note=$('macroGeoNote').value.trim(),bar=$('macroGeoScale').value.trim();
  if(note||bar){
   const h=Math.max(90,Math.round(c.height*.14)),fs=Math.max(18,Math.round(c.width/48));
   x.fillStyle='rgba(3,24,36,.84)';x.fillRect(0,c.height-h,c.width,h);
   x.fillStyle='#fff';x.font=`700 ${fs}px system-ui`;
   x.fillText('ITA ARANDU MS · MacroGeo',fs*.65,c.height-h+fs*1.25);
   x.font=`500 ${Math.round(fs*.72)}px system-ui`;
   const text=[bar?`escala informada · ${bar}`:'',note].filter(Boolean).join(' · ');
   x.fillText(text.slice(0,120),fs*.65,c.height-h+fs*2.45);
  }
  S.blob=await new Promise((resolve,reject)=>c.toBlob(b=>b?resolve(b):reject(new Error('Falha ao gerar JPEG')),'image/jpeg',.92));
  $('macroGeoResult').hidden=false;
  window.ITA_MACROGEO_LAST={blob:S.blob,captured_at_utc:new Date().toISOString(),scale_note:bar||null,annotation:note||null};
  status('Captura pronta. Escala e anotação são declarações do usuário, não medidas automáticas.');
 }catch(e){status(e.message)}
}
function download(){
 if(!S.blob)return;
 const a=document.createElement('a');a.href=URL.createObjectURL(S.blob);
 a.download=`ITA_ARANDU_MACROGEO_${new Date().toISOString().replace(/[:.]/g,'-')}.jpg`;
 a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1500);
}
function wire(){
 $('macroGeoStart')?.addEventListener('click',start);
 $('macroGeoCapture')?.addEventListener('click',capture);
 $('macroGeoStop')?.addEventListener('click',stop);
 $('macroGeoDevice')?.addEventListener('change',()=>{if(S.stream)start()});
 $('macroGeoZoom')?.addEventListener('input',setZoom);
 $('macroGeoDownload')?.addEventListener('click',download);
 $('macroGeoClear')?.addEventListener('click',()=>{$('macroGeoResult').hidden=true;S.blob=null});
 document.querySelectorAll('[data-close="macroGeoModal"]').forEach(b=>b.addEventListener('click',stop));
 window.addEventListener('pagehide',stop);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
window.ITA_MACROGEO={version:'1.0',start,stop,capture};
})();