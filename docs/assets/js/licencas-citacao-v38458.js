
(()=>{'use strict';
const DOI='10.5281/zenodo.21923101';
const DOIURL='https://doi.org/10.5281/zenodo.21923101';
const ZENODO='https://zenodo.org/records/21923101';
const projectCitation='Busón Buesa, C., & Gabas, S. G. (2026). ITA ARANDU MS · Atlas geocientífico educativo e científico de Mato Grosso do Sul [Software e atlas geocientífico]. Zenodo. https://doi.org/10.5281/zenodo.21923101';
const components={
clinometroAranduModal:'Clinômetro Visual ARANDU',bussolaAranduModal:'Bússola geológica',nivelAranduModal:'Nível digital',
estereogramaAranduModal:'Rede/Estereograma estrutural',calculadoraEstruturalModal:'Calculadora estrutural',roseModal:'Diagrama de Rosas · Direções',
ternarioModal:'Diagrama Ternário · USDA',macroGeoModal:'MacroGeo',saidaCampoModal:'Saída de campo',gpsEducativoModal:'GPS educativo',
geocameraModal:'GeoCâmera',magAmostrasModal:'Magnetômetro · Amostras',magMapaModal:'Magnetômetro · Mapa',
ondasSismicasModal:'Ondas sísmicas · Acelerômetro',colunaEstratigraficaModal:'Coluna Estratigráfica'
};
function citeFor(name){return `Busón Buesa, C., & Gabas, S. G. (2026). ${name} · implementação educacional no ITA ARANDU MS. In ITA ARANDU MS · Atlas geocientífico educativo e científico de Mato Grosso do Sul [Software e atlas geocientífico]. Zenodo. ${DOIURL}`;}
function ensureModal(){
 if(document.getElementById('licencasCitacaoModal'))return;
 const m=document.createElement('div');m.className='modal ita-license-modal';m.id='licencasCitacaoModal';m.setAttribute('aria-hidden','true');
 m.innerHTML=`<div class="modal-box ita-governance-box"><div class="modal-head"><div><div class="kicker">AUTORIA · LICENÇAS · CITAÇÃO</div><h2>Licenças e como citar</h2></div><button type="button" class="close-modal" data-license-close aria-label="Fechar">×</button></div><div class="modal-body">
 <div class="ita-license-hero"><b>Reutilização permitida com atribuição e sem uso comercial</b><p>O ITA ARANDU MS separa conteúdo autoral, código original e materiais de terceiros. A licença do projeto nunca altera os direitos das fontes cartográficas, científicas ou tecnológicas incorporadas.</p></div>
 <div class="ita-license-grid">
  <article><span>CONTEÚDO ORIGINAL</span><h3>CC BY-NC-SA 4.0</h3><p>Textos, metodologias, índices, materiais educativos e documentação originais. Reutilização não comercial com atribuição, indicação de alterações e compartilhamento pela mesma licença.</p><a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="noopener">Licença oficial</a></article>
  <article><span>SOFTWARE ORIGINAL</span><h3>PolyForm Noncommercial 1.0.0</h3><p>Código criado especificamente para o ITA ARANDU MS. Licença de software de uso não comercial. Não é apresentada como licença open source OSI.</p><a href="https://polyformproject.org/licenses/noncommercial/1.0.0/" target="_blank" rel="noopener">Licença oficial</a></article>
  <article><span>CONTEÚDO DE TERCEIROS</span><h3>Direitos da fonte original</h3><p>Mapas, bases, imagens, padrões, bibliotecas e serviços externos conservam autoria, licença, atribuição e termos próprios. Consulte a ficha e a Biblioteca APA 7.</p></article>
 </div>
 <section class="ita-citation-box"><div><span>CITAÇÃO DO PROJETO</span><b>${projectCitation}</b></div><div class="ita-license-actions"><a href="${ZENODO}" target="_blank" rel="noopener">Zenodo</a><a href="${DOIURL}" target="_blank" rel="noopener">DOI</a><a href="./documentos/politica-licencas-citacao.html" target="_blank" rel="noopener">Política completa</a></div></section>
 <section id="itaComponentCitation" class="ita-component-citation" hidden><span>COMO CITAR ESTE COMPONENTE</span><b id="itaComponentCitationText"></b><p>A citação identifica a implementação e a integração no ITA ARANDU MS. O método geocientífico subjacente deve ser citado também pelas referências indicadas em Ajuda e Ciência.</p></section>
 <div class="ita-license-refline">Bibliografia de suporte · REF-237 · REF-238 · REF-239 · REF-240</div>
 </div></div>`;
 document.body.appendChild(m);
 m.querySelector('[data-license-close]').onclick=()=>closeModal();
 m.addEventListener('click',e=>{if(e.target===m)closeModal()});
}
function openModal(component){
 ensureModal();const m=document.getElementById('licencasCitacaoModal');
 const box=m.querySelector('#itaComponentCitation'), txt=m.querySelector('#itaComponentCitationText');
 if(component){box.hidden=false;txt.textContent=citeFor(component)}else{box.hidden=true;txt.textContent=''}
 m.classList.add('open','is-open');m.setAttribute('aria-hidden','false');document.body.classList.add('modal-open');
}
function closeModal(){const m=document.getElementById('licencasCitacaoModal');if(!m)return;m.classList.remove('open','is-open');m.setAttribute('aria-hidden','true')}
function addHelpCard(){
 const grid=document.querySelector('#ajudaModal .docs-grid');if(!grid||grid.querySelector('[data-license-policy]'))return;
 const b=document.createElement('button');b.type='button';b.className='doc-card';b.dataset.licensePolicy='1';
 b.innerHTML='<b>Licenças · autoria · como citar</b><span>Uso não comercial, atribuição, licenças do conteúdo e do software, direitos de terceiros e citação de ferramentas e índices.</span>';
 b.onclick=()=>openModal();grid.appendChild(b);
}
function addHubButton(){
 const p=document.querySelector('#ferramentasModal .ita-tools-principle');if(!p||p.querySelector('[data-license-policy]'))return;
 const b=document.createElement('button');b.type='button';b.className='action-btn';b.dataset.licensePolicy='1';b.textContent='Licenças e citação';b.onclick=()=>openModal();p.appendChild(b);
}
function addStrips(){
 Object.entries(components).forEach(([id,name])=>{
   const modal=document.getElementById(id);if(!modal||modal.querySelector('.ita-citation-strip'))return;
   const body=modal.querySelector('.modal-body,.ce-body,.mag-body,.ondas-body')||modal.querySelector('.modal-box');if(!body)return;
   const s=document.createElement('div');s.className='ita-citation-strip';
   s.innerHTML=`<div><b>Como citar esta implementação</b><span>ITA ARANDU MS · DOI ${DOI}</span></div><button type="button">Citação e licenças</button>`;
   s.querySelector('button').onclick=()=>openModal(name);body.appendChild(s);
 });
}
function normalizeTools(){
 const ids=['clinometroAranduModal','bussolaAranduModal','nivelAranduModal','estereogramaAranduModal','calculadoraEstruturalModal','roseModal','ternarioModal','macroGeoModal','saidaCampoModal','gpsEducativoModal','geocameraModal','magAmostrasModal','magMapaModal','ondasSismicasModal','colunaEstratigraficaModal'];
 ids.forEach(id=>document.getElementById(id)?.classList.add('ita-bancada-standard-modal'));
}
function run(){ensureModal();addHelpCard();addHubButton();addStrips();normalizeTools()}
document.addEventListener('DOMContentLoaded',run);
new MutationObserver(()=>{addHelpCard();addHubButton();addStrips();normalizeTools()}).observe(document.documentElement,{childList:true,subtree:true});
window.ITA_LICENSES={open:openModal,projectCitation,doi:DOI};
})();
