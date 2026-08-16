(function(){
'use strict';
const $=id=>document.getElementById(id);
function syncGeoethics(){
 const sens=$('campoSensibilidade')?.value||'';
 const access=$('campoGeoNivelAcesso'),consent=$('campoGeoConsentimento'),warn=$('campoGeoeticaAviso');
 if(!access||!warn)return;
 const restricted=sens==='restrita'||['restrita','nao_publicar','generalizada'].includes(access.value);
 warn.textContent=restricted
  ? 'Registro com restrição. Coordenadas, fotografias e conteúdo devem ser revistos antes de qualquer divulgação. A disponibilidade técnica do dado não constitui autorização de publicação.'
  : 'Avalie origem, autoridade, finalidade, sensibilidade e condições de reutilização antes de compartilhar.';
 if(consent&&access.value==='nao_publicar')consent.value='nao_autorizado';
}
function wire(){['campoSensibilidade','campoGeoNivelAcesso','campoGeoConsentimento'].forEach(id=>$(id)?.addEventListener('change',syncGeoethics));syncGeoethics()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
window.ITA_GEOETICA_CARE={version:'1.0',syncGeoethics};
})();
