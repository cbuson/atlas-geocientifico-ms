(function(){
'use strict';
const $=id=>document.getElementById(id);
function open(id){const m=$(id);if(!m)return;m.classList.add('open');m.setAttribute('aria-hidden','false')}
/* Rota direta. Evita depender do botão oculto intermediário. */
document.addEventListener('click',function(e){
 const b=e.target.closest('[data-tool-action]'); if(!b)return;
 const a=b.dataset.toolAction;
 if(a==='bussola'||a==='nivel'){
   e.preventDefault();e.stopImmediatePropagation();
   $('ferramentasModal')?.classList.remove('open');
   open(a==='bussola'?'bussolaAranduModal':'nivelAranduModal');
 }
},true);
/* Corrige permissão de orientação em navegadores que expõem requestPermission sem argumentos. */
window.ITA_SENSOR_PERMISSION=async function(){
 if(typeof DeviceOrientationEvent==='undefined')throw new Error('Sensor de orientação não disponível neste navegador');
 if(typeof DeviceOrientationEvent.requestPermission==='function'){
   const p=await DeviceOrientationEvent.requestPermission();
   if(p!=='granted')throw new Error('Permissão de movimento e orientação não concedida');
 }
 return true;
};
})();
