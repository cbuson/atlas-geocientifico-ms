(function(){
'use strict';
function stop(stream){if(stream)stream.getTracks().forEach(t=>{try{t.stop()}catch{}})}
function describeError(e){
 const n=e?.name||'Error';
 const map={
  NotAllowedError:'permissão de câmera negada',
  NotFoundError:'nenhuma câmera compatível encontrada',
  NotReadableError:'câmera ocupada ou indisponível para o navegador',
  OverconstrainedError:'restrições solicitadas não são compatíveis com esta câmera',
  SecurityError:'acesso à câmera bloqueado pelo contexto de segurança',
  AbortError:'captura interrompida pelo dispositivo'
 };
 return (map[n]||e?.message||n)+(e?.constraint?` · ${e.constraint}`:'');
}
async function open(opts={}){
 if(!window.isSecureContext)throw Object.assign(new Error('A câmera requer HTTPS ou localhost'),{name:'SecurityError'});
 if(!navigator.mediaDevices?.getUserMedia)throw new Error('MediaDevices/getUserMedia indisponível');
 const attempts=[];
 if(opts.deviceId)attempts.push({video:{deviceId:{exact:opts.deviceId}},audio:false});
 attempts.push({video:{facingMode:{ideal:opts.facingMode||'environment'},width:{ideal:1920},height:{ideal:1080}},audio:false});
 attempts.push({video:{facingMode:{ideal:opts.facingMode||'environment'}},audio:false});
 attempts.push({video:true,audio:false});
 let last;
 for(const c of attempts){
  try{return await navigator.mediaDevices.getUserMedia(c)}
  catch(e){last=e}
 }
 throw last||new Error('Não foi possível iniciar a câmera');
}
async function cameras(){
 if(!navigator.mediaDevices?.enumerateDevices)return [];
 const ds=await navigator.mediaDevices.enumerateDevices();
 return ds.filter(d=>d.kind==='videoinput');
}
function capabilities(stream){
 const track=stream?.getVideoTracks?.()[0];
 if(!track)return {};
 try{return track.getCapabilities?.()||{}}catch{return {}}
}
async function apply(stream,constraints){
 const track=stream?.getVideoTracks?.()[0];
 if(!track?.applyConstraints)return false;
 await track.applyConstraints({advanced:[constraints]});
 return true;
}
window.ITA_CAMERA_CORE={version:'1.0',open,stop,cameras,capabilities,apply,describeError};
})();