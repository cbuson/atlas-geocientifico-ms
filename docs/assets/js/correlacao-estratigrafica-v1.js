(()=>{
'use strict';

const STORE='ita_arandu_correlacao_estratigrafica_v1';
const COLUMN_STORE='ita_arandu_coluna_estratigrafica_v1';
const COLORS=['#1769aa','#5b9f45','#7753b6','#e19a23','#ba4f5a','#2c8c8c'];
const REF_DOC='./documentos/metodologia-correlacao-estratigrafica.html';
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];

let state={
  sections:[],
  correlations:[],
  selectedOrigin:null,
  selectedDest:null,
  alignment:{mode:'base',markerCorrelationId:null},
  tab:'correlate'
};
let map=null, mapLayer=null;

function esc(v){return String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
function uid(prefix='id'){return prefix+'_'+Date.now().toString(36)+'_'+Math.random().toString(36).slice(2,8)}
function validNum(v){return Number.isFinite(Number(v))}
function load(){
  try{
    const x=JSON.parse(localStorage.getItem(STORE)||'null');
    if(x&&Array.isArray(x.sections)&&Array.isArray(x.correlations)) state={...state,...x};
  }catch(_){}
}
function save(){localStorage.setItem(STORE,JSON.stringify(state))}
function totalThickness(sec){return (sec.levels||[]).reduce((a,b)=>a+(Number(b.thickness)||0),0)}
function gpsOf(sec){
  const g=sec.gps||{};
  const lat=Number(g.lat),lon=Number(g.lon);
  return Number.isFinite(lat)&&Number.isFinite(lon)?{lat,lon,accuracy:Number(g.accuracy),altitude:Number(g.altitude)}:null;
}
function hav(a,b){
  const R=6371,rad=x=>x*Math.PI/180;
  const dlat=rad(b.lat-a.lat),dlon=rad(b.lon-a.lon);
  const q=Math.sin(dlat/2)**2+Math.cos(rad(a.lat))*Math.cos(rad(b.lat))*Math.sin(dlon/2)**2;
  return 2*R*Math.asin(Math.sqrt(q));
}
function bearing(a,b){
  const rad=x=>x*Math.PI/180,deg=x=>x*180/Math.PI;
  const y=Math.sin(rad(b.lon-a.lon))*Math.cos(rad(b.lat));
  const x=Math.cos(rad(a.lat))*Math.sin(rad(b.lat))-Math.sin(rad(a.lat))*Math.cos(rad(b.lat))*Math.cos(rad(b.lon-a.lon));
  return (deg(Math.atan2(y,x))+360)%360;
}
function cardinal(d){
  const pts=['N','NE','E','SE','S','SW','W','NW'];
  return pts[Math.round(d/45)%8];
}
function normalizeSection(raw,nameHint){
  if(!raw||!Array.isArray(raw.levels)) throw new Error('Arquivo sem níveis estratigráficos.');
  const gps=raw.gps||{};
  return {
    id:raw.id||uid('sec'),
    project:String(raw.project||nameHint||`Seção ${state.sections.length+1}`),
    place:String(raw.place||''),
    orientation:String(raw.orientation||''),
    gps:{
      lat:validNum(gps.lat)?Number(gps.lat):null,
      lon:validNum(gps.lon)?Number(gps.lon):null,
      accuracy:validNum(gps.accuracy)?Number(gps.accuracy):null,
      altitude:validNum(gps.altitude)?Number(gps.altitude):null,
      timestamp:gps.timestamp||null
    },
    levels:raw.levels.map((l,i)=>({
      thickness:Number(l.thickness)||0,
      code:String(l.code||`Nível ${i+1}`),
      lith:String(l.lith||''),
      grain:String(l.grain||''),
      structures:String(l.structures||''),
      fossils:String(l.fossils||''),
      contactBottom:String(l.contactBottom||''),
      contactTop:String(l.contactTop||''),
      notes:String(l.notes||'')
    }))
  };
}
function addCurrent(){
  try{
    const raw=JSON.parse(localStorage.getItem(COLUMN_STORE)||'null');
    if(!raw||!Array.isArray(raw.levels)||!raw.levels.length){alert('A Coluna Estratigráfica atual não possui níveis salvos.');return}
    const sec=normalizeSection(raw);
    sec.id=uid('sec');
    state.sections.push(sec);save();renderAll();
  }catch(e){alert('Não foi possível carregar a coluna atual. '+e.message)}
}
function importFiles(files){
  [...files].forEach(file=>{
    const reader=new FileReader();
    reader.onload=()=>{
      try{
        const raw=JSON.parse(reader.result);
        if(Array.isArray(raw.sections)) raw.sections.forEach((s,i)=>state.sections.push(normalizeSection(s,`${file.name} ${i+1}`)));
        else state.sections.push(normalizeSection(raw,file.name.replace(/\.json$/i,'')));
        save();renderAll();
      }catch(e){alert(`Falha ao importar ${file.name}. ${e.message}`)}
    };
    reader.readAsText(file,'utf-8');
  });
}
function removeSection(id){
  if(!confirm('Remover esta coluna do projeto de correlação?'))return;
  state.sections=state.sections.filter(s=>s.id!==id);
  state.correlations=state.correlations.filter(c=>c.a.sectionId!==id&&c.b.sectionId!==id);
  state.selectedOrigin=null;state.selectedDest=null;save();renderAll();
}
function moveSection(id,dir){
  const i=state.sections.findIndex(s=>s.id===id),j=i+dir;
  if(i<0||j<0||j>=state.sections.length)return;
  [state.sections[i],state.sections[j]]=[state.sections[j],state.sections[i]];
  save();renderAll();
}
function modal(){
  if($('#correlacaoEstratigraficaModal'))return;
  const el=document.createElement('div');
  el.className='modal';
  el.id='correlacaoEstratigraficaModal';
  el.setAttribute('aria-hidden','true');
  el.innerHTML=`<div class="modal-box corr-modal-box">
    <div class="corr-head">
      <div><div class="corr-kicker">Bancada Digital · Estratigrafia</div><h2>Correlação Estratigráfica</h2><div class="corr-note">Comparação e correlação documentada entre seções estratigráficas.</div></div>
      <div class="corr-head-actions"><button type="button" class="corr-btn" data-corr-help>Ajuda e Ciência</button><button type="button" class="corr-btn primary" data-corr-close>×</button></div>
    </div>
    <div class="corr-tabs">
      <button class="active" data-corr-tab="correlate">Correlacionar</button>
      <button data-corr-tab="columns">Colunas</button>
      <button data-corr-tab="map">Mapa</button>
      <button data-corr-tab="data">Dados</button>
      <button data-corr-tab="help">Ajuda e Ciência</button>
    </div>
    <div class="corr-body">
      <section class="corr-pane active" data-corr-pane="correlate">
        <div id="corrSummary" class="corr-summary"></div>
        <div class="corr-mobile-columns" id="corrMobileColumns"></div>
        <div class="corr-workspace">
          <aside class="corr-side corr-side-left">
            <div class="corr-card"><h3>1. Colunas carregadas</h3><div id="corrSectionsMini"></div>
              <div class="corr-actions"><button class="corr-btn" id="corrAddCurrent">+ Coluna atual</button><button class="corr-btn" id="corrImportBtn">Importar JSON</button><input id="corrImport" type="file" accept=".json,application/json" multiple hidden></div>
            </div>
            <div class="corr-card"><h3>2. Alinhamento</h3>
              <label>Método<select id="corrAlignMode"><option value="base">Base das colunas</option><option value="top">Topo das colunas</option><option value="marker">Nível marcador</option></select></label>
              <label class="corr-marker-field">Correlação marcadora<select id="corrMarkerSelect"></select></label>
              <p class="corr-small">O alinhamento é uma decisão gráfica para comparação. Não transforma uma equivalência interpretada em equivalência temporal demonstrada.</p>
            </div>
          </aside>
          <main class="corr-center">
            <div class="corr-toolbar"><div class="corr-legend"><span><i class="high"></i> Alta confiança</span><span><i class="possible"></i> Possível</span><span><i class="marker"></i> Nível marcador</span></div><button class="corr-btn" id="corrExpand">Expandir</button></div>
            <div class="corr-canvas-wrap" id="corrCanvasWrap"><div class="corr-sections-canvas" id="corrCanvas"><svg class="corr-lines" id="corrLines" aria-hidden="true"></svg><div class="corr-section-columns" id="corrSectionColumns"></div></div></div>
            <div class="corr-fgdc-note">Padrões litológicos · FGDC-STD-013-2006 · Seção 37</div>
          </main>
          <aside class="corr-side corr-side-right">
            <div class="corr-card"><h3>3. Correlação selecionada</h3><div id="corrSelection"></div></div>
          </aside>
        </div>
        <div class="corr-mobile-lower">
          <details><summary>4. Alinhamento</summary><div id="corrMobileAlign"></div></details>
          <details><summary>5. Correlações ativas</summary><div id="corrActive"></div></details>
        </div>
      </section>

      <section class="corr-pane" data-corr-pane="columns">
        <div class="corr-page-head"><div><h3>Colunas do projeto</h3><p>Adicione a coluna atual do construtor ou importe arquivos JSON exportados pelo ITA ARANDU MS.</p></div><div class="corr-actions"><button class="corr-btn primary" id="corrAddCurrent2">+ Coluna atual</button><button class="corr-btn" id="corrImportBtn2">Importar JSON</button></div></div>
        <input id="corrImport2" type="file" accept=".json,application/json" multiple hidden>
        <div id="corrColumnsList" class="corr-columns-list"></div>
      </section>

      <section class="corr-pane" data-corr-pane="map">
        <div class="corr-page-head"><div><h3>Mapa das seções</h3><p>Localização espacial das colunas com GPS registrado. A linha entre pontos representa apenas a ordem do perfil.</p></div><button class="corr-btn" id="corrFitMap">Enquadrar pontos</button></div>
        <div id="corrMap" class="corr-map"></div>
        <div id="corrMapList" class="corr-map-list"></div>
      </section>

      <section class="corr-pane" data-corr-pane="data">
        <div class="corr-page-head"><div><h3>Dados e exportação</h3><p>O projeto conserva colunas, coordenadas, decisões de correlação, critérios e confiança.</p></div></div>
        <div class="corr-actions corr-export-actions"><button class="corr-btn" id="corrExportJSON">Exportar JSON</button><button class="corr-btn" id="corrExportCSV">Exportar correlações CSV</button><button class="corr-btn" id="corrExportSVG">Exportar painel SVG</button></div>
        <pre id="corrJSON" class="corr-json"></pre>
      </section>

      <section class="corr-pane corr-help" data-corr-pane="help">
        <div class="corr-help-intro"><b>Objetivo educativo</b><p>Comparar seções estratigráficas e registrar explicitamente por que dois níveis são interpretados como correlacionáveis. A ferramenta não demonstra equivalência temporal de forma automática.</p></div>
        <div class="corr-help-grid">
          <article><h3>O que é correlação</h3><p>A correlação estratigráfica estabelece correspondências interpretadas entre unidades ou superfícies observadas em diferentes seções. Pode utilizar relações litoestratigráficas, bioestratigráficas, cronoestratigráficas, magnetoestratigráficas, geocronológicas ou outros marcadores adequadamente documentados.</p></article>
          <article><h3>Regra fundamental</h3><p><b>Semelhança litológica não implica necessariamente equivalência temporal.</b> Mudanças laterais de fácies, diacronismo, hiatos, erosão e repetição estrutural podem produzir relações mais complexas.</p></article>
          <article><h3>Confiança</h3><p>Alta, moderada ou possível expressam a força da interpretação no projeto. Não substituem medidas quantitativas de incerteza nem validação estratigráfica independente.</p></article>
          <article><h3>Nível marcador</h3><p>Um marcador deve ser escolhido por propriedades justificáveis e rastreáveis. A linha mais espessa representa uma referência gráfica de alinhamento, não uma prova automática de sincronismo.</p></article>
          <article><h3>GPS e mapa</h3><p>As coordenadas WGS 84 permitem relacionar as seções ao território. O mapa mostra a posição das colunas e a ordem espacial do perfil. A precisão do GPS permanece parte do registro quando foi capturada na Coluna Estratigráfica.</p></article>
          <article><h3>Limitações</h3><p>A ferramenta não corrige automaticamente tectônica, mergulho aparente, deformação, espessura estratigráfica verdadeira, erosão ou idade. Essas decisões devem ser documentadas pelo usuário.</p></article>
        </div>
        <div class="corr-help-ref"><h3>Referências e normas</h3>
          <p>Murphy e Salvador (1999) · International Stratigraphic Guide · REF-241.</p>
          <p>Salvador (Ed., 1994) · International Stratigraphic Guide · REF-242.</p>
          <p>North American Commission on Stratigraphic Nomenclature (2005) · REF-243.</p>
          <p>International Chronostratigraphic Chart · REF-019. FGDC lithologic patterns · REF-233. OpenStreetMap · REF-032.</p>
          <a href="./referencias/index.html" target="_blank" rel="noopener">Abrir Biblioteca APA 7</a>
          <a href="${REF_DOC}" target="_blank" rel="noopener">Metodologia completa</a>
        </div>
        <div class="corr-cite"><h3>Como citar esta implementação</h3><p>Busón Buesa, C., &amp; Gabas, S. G. (2026). Correlação Estratigráfica · implementação educacional no ITA ARANDU MS. In <i>ITA ARANDU MS · Atlas geocientífico educativo e científico de Mato Grosso do Sul</i> [Software e atlas geocientífico]. Zenodo. https://doi.org/10.5281/zenodo.21923101</p><small>A citação refere-se à implementação, integração, interface e desenho educativo do ITA ARANDU MS. Os métodos estratigráficos subjacentes devem ser citados por suas próprias fontes.</small></div>
      </section>
    </div>
  </div>`;
  document.body.appendChild(el);
  bind();
}
function bind(){
  $('[data-corr-close]').onclick=close;
  $('[data-corr-help]').onclick=()=>tab('help');
  $$('.corr-tabs button').forEach(b=>b.onclick=()=>tab(b.dataset.corrTab));
  $('#corrAddCurrent').onclick=addCurrent;$('#corrAddCurrent2').onclick=addCurrent;
  $('#corrImportBtn').onclick=()=>$('#corrImport').click();$('#corrImportBtn2').onclick=()=>$('#corrImport2').click();
  $('#corrImport').onchange=e=>importFiles(e.target.files);$('#corrImport2').onchange=e=>importFiles(e.target.files);
  $('#corrAlignMode').onchange=e=>{state.alignment.mode=e.target.value;save();renderAll()};
  $('#corrMarkerSelect').onchange=e=>{state.alignment.markerCorrelationId=e.target.value||null;save();renderAll()};
  $('#corrExpand').onclick=()=>$('#corrCanvasWrap').classList.toggle('expanded');
  $('#corrFitMap').onclick=fitMap;
  $('#corrExportJSON').onclick=exportJSON;$('#corrExportCSV').onclick=exportCSV;$('#corrExportSVG').onclick=exportSVG;
}
function open(which='correlate'){modal();load();$('#correlacaoEstratigraficaModal').classList.add('open','is-open');$('#correlacaoEstratigraficaModal').setAttribute('aria-hidden','false');document.body.classList.add('modal-open');tab(which);renderAll()}
function close(){const m=$('#correlacaoEstratigraficaModal');if(!m)return;m.classList.remove('open','is-open');m.setAttribute('aria-hidden','true')}
function tab(t){
  state.tab=t;
  $$('.corr-tabs button').forEach(b=>b.classList.toggle('active',b.dataset.corrTab===t));
  $$('.corr-pane').forEach(p=>p.classList.toggle('active',p.dataset.corrPane===t));
  if(t==='map') setTimeout(renderMap,80);
  if(t==='data') $('#corrJSON').textContent=JSON.stringify(state,null,2);
  if(t==='correlate') requestAnimationFrame(drawLines);
}
function summary(){
  const gps=state.sections.map(gpsOf).filter(Boolean);
  let maxD=0,pair='';
  for(let i=0;i<state.sections.length;i++)for(let j=i+1;j<state.sections.length;j++){
    const a=gpsOf(state.sections[i]),b=gpsOf(state.sections[j]);if(!a||!b)continue;
    const d=hav(a,b);if(d>maxD){maxD=d;pair=`${letter(i)} ↔ ${letter(j)}`}
  }
  let profile='—';
  const first=state.sections.find(s=>gpsOf(s)),last=[...state.sections].reverse().find(s=>gpsOf(s));
  if(first&&last&&first!==last) profile=`${cardinal(bearing(gpsOf(first),gpsOf(last)))} → ${cardinal((bearing(gpsOf(first),gpsOf(last))+180)%360)}`;
  const hi=state.correlations.filter(c=>c.confidence==='alta').length,poss=state.correlations.filter(c=>c.confidence==='possivel').length,mark=state.correlations.filter(c=>c.marker).length;
  $('#corrSummary').innerHTML=`<div><b>${state.sections.length} colunas</b><span>${hi} altas · ${poss} possíveis · ${mark} marcador${mark===1?'':'es'}</span></div><div><b>Distância máx.</b><span>${maxD?`${pair} · ${maxD.toFixed(1).replace('.',',')} km`:'GPS insuficiente'}</span></div><div><b>Perfil</b><span>${profile}</span></div><button class="corr-btn" data-go-map>Ver localização das seções</button>`;
  $('[data-go-map]').onclick=()=>tab('map');
}
function letter(i){return String.fromCharCode(65+i)}
function sectionLabel(sec,i){
  const g=gpsOf(sec),alt=g&&Number.isFinite(g.altitude)?`${g.altitude.toFixed(0)} m`:'';
  return `<div class="corr-section-chip" data-sec="${esc(sec.id)}"><b><span style="background:${COLORS[i%COLORS.length]}">${letter(i)}</span>${esc(sec.project)}</b><small>${g?`${g.lat.toFixed(5)}, ${g.lon.toFixed(5)}`:'Sem GPS'} ${alt}</small></div>`;
}
function renderMini(){
  $('#corrSectionsMini').innerHTML=state.sections.length?state.sections.map((s,i)=>`<div class="corr-mini-row">${sectionLabel(s,i)}<div class="corr-mini-actions"><button data-move="${s.id}" data-dir="-1">↑</button><button data-move="${s.id}" data-dir="1">↓</button><button data-remove="${s.id}">×</button></div></div>`).join(''):'<p class="corr-empty">Nenhuma coluna carregada.</p>';
  $$('[data-remove]').forEach(b=>b.onclick=()=>removeSection(b.dataset.remove));
  $$('[data-move]').forEach(b=>b.onclick=()=>moveSection(b.dataset.move,Number(b.dataset.dir)));
}
function renderMobileColumns(){
  $('#corrMobileColumns').innerHTML=state.sections.map((s,i)=>sectionLabel(s,i)).join('');
}
function layerBg(lith){return `url('./assets/padroes/fgdc/.png'),url('./assets/padroes/fgdc/.svg')`}
function alignOffsets(){
  const n=state.sections.length, offsets=Array(n).fill(0);
  if(state.alignment.mode==='top'){
    const mx=Math.max(0,...state.sections.map(totalThickness));
    state.sections.forEach((s,i)=>offsets[i]=mx-totalThickness(s));
  }else if(state.alignment.mode==='marker'&&state.alignment.markerCorrelationId){
    const c=state.correlations.find(x=>x.id===state.alignment.markerCorrelationId);
    if(c){
      const markerDepths=Array(n).fill(null);
      [[c.a.sectionId,c.a.levelIndex],[c.b.sectionId,c.b.levelIndex]].forEach(([sid,li])=>{
        const si=state.sections.findIndex(s=>s.id===sid);
        if(si>=0){const s=state.sections[si];markerDepths[si]=(s.levels||[]).slice(0,li).reduce((a,l)=>a+(Number(l.thickness)||0),0)+(Number(s.levels[li]?.thickness)||0)/2}
      });
      const target=Math.max(...markerDepths.filter(v=>v!==null),0);
      markerDepths.forEach((d,i)=>{if(d!==null)offsets[i]=target-d});
    }
  }
  return offsets;
}
function renderCanvas(){
  const host=$('#corrSectionColumns');if(!host)return;
  if(!state.sections.length){host.innerHTML='<div class="corr-empty-canvas">Adicione pelo menos duas colunas para iniciar uma correlação.</div>';$('#corrLines').innerHTML='';return}
  const maxTotal=Math.max(1,...state.sections.map(totalThickness)),px=Math.min(5.2,520/maxTotal),offs=alignOffsets();
  host.style.setProperty('--corr-px',px+'px');
  host.innerHTML=state.sections.map((s,si)=>{
    const g=gpsOf(s),levels=s.levels||[];
    const layers=levels.map((l,li)=>`<button type="button" class="corr-layer ${isSelected(si,li)}" data-level="${si}:${li}" style="height:${Math.max(18,(Number(l.thickness)||0)*px)}px;background-image:${layerBg(l.lith)}" title="${esc(l.code)} · FGDC ${esc(l.lith)}"><span>${esc(l.code)}</span></button>`).join('');
    return `<div class="corr-section" data-section-index="${si}" style="padding-top:${Math.max(0,offs[si]*px)}px"><div class="corr-section-title"><b><i style="background:${COLORS[si%COLORS.length]}">${letter(si)}</i>${esc(s.project)}</b><small>${g?`${g.lat.toFixed(5)}, ${g.lon.toFixed(5)}`:'Sem GPS'} · ${totalThickness(s).toFixed(1).replace('.',',')} m</small></div><div class="corr-strat-column">${layers}</div></div>`;
  }).join('');
  $$('[data-level]').forEach(b=>b.onclick=()=>selectLevel(b.dataset.level));
  requestAnimationFrame(drawLines);
}
function isSelected(si,li){
  const o=state.selectedOrigin,d=state.selectedDest;
  if(o&&o.sectionIndex===si&&o.levelIndex===li)return 'selected-origin';
  if(d&&d.sectionIndex===si&&d.levelIndex===li)return 'selected-dest';
  return '';
}
function selectLevel(token){
  const [si,li]=token.split(':').map(Number);
  if(!state.selectedOrigin){state.selectedOrigin={sectionIndex:si,levelIndex:li};state.selectedDest=null}
  else if(state.selectedOrigin.sectionIndex===si){state.selectedOrigin={sectionIndex:si,levelIndex:li};state.selectedDest=null}
  else {state.selectedDest={sectionIndex:si,levelIndex:li}}
  renderCanvas();renderSelection();
}
function levelInfo(sel){
  if(!sel)return null;const s=state.sections[sel.sectionIndex],l=s?.levels?.[sel.levelIndex];return s&&l?{s,l}:null;
}
function renderSelection(){
  const box=$('#corrSelection'),a=levelInfo(state.selectedOrigin),b=levelInfo(state.selectedDest);
  if(!a){box.innerHTML='<p class="corr-empty">Selecione um nível na primeira coluna.</p>';return}
  const card=(x,sel)=>`<div class="corr-selected-level"><b>${letter(sel.sectionIndex)} · ${esc(x.s.project)} · ${esc(x.l.code)}</b><small>FGDC ${esc(x.l.lith)} · ${esc(x.l.grain||'textura não informada')} · ${Number(x.l.thickness).toFixed(2).replace('.',',')} m</small></div>`;
  box.innerHTML=`<label>Origem${card(a,state.selectedOrigin)}</label>${b?`<div class="corr-arrow">↓</div><label>Destino${card(b,state.selectedDest)}</label>`:'<p class="corr-small">Agora selecione um nível de outra coluna.</p>'}${b?`
    <label>Tipo de correlação<select id="corrType"><option value="litologica">Litológica</option><option value="bioestratigrafica">Bioestratigráfica</option><option value="cronoestratigrafica">Cronoestratigráfica</option><option value="superficie">Superfície / contato</option><option value="outro">Outro marcador</option></select></label>
    <label>Critério utilizado<textarea id="corrCriterion" maxlength="500" placeholder="Explique a evidência usada."></textarea></label>
    <div class="corr-two"><label>Confiança<select id="corrConfidence"><option value="alta">Alta</option><option value="moderada">Moderada</option><option value="possivel">Possível</option></select></label><label>Representação<select id="corrStyle"><option value="continua">Contínua</option><option value="tracejada">Tracejada</option></select></label></div>
    <label class="corr-check"><input type="checkbox" id="corrMarker"> Nível marcador</label>
    <label>Observações<textarea id="corrNotes" maxlength="500"></textarea></label>
    <button class="corr-btn primary corr-save" id="corrSave">Salvar correlação</button>`:''}`;
  if(b)$('#corrSave').onclick=saveCorrelation;
}
function saveCorrelation(){
  const a=state.selectedOrigin,b=state.selectedDest;
  if(!a||!b)return;
  const criterion=$('#corrCriterion').value.trim();
  if(!criterion){alert('Descreva o critério utilizado para a correlação.');return}
  state.correlations.push({
    id:uid('cor'),
    a:{sectionId:state.sections[a.sectionIndex].id,levelIndex:a.levelIndex},
    b:{sectionId:state.sections[b.sectionIndex].id,levelIndex:b.levelIndex},
    type:$('#corrType').value,criterion,
    confidence:$('#corrConfidence').value,style:$('#corrStyle').value,
    marker:$('#corrMarker').checked,notes:$('#corrNotes').value.trim(),createdAt:new Date().toISOString()
  });
  state.selectedOrigin=null;state.selectedDest=null;save();renderAll();
}
function removeCorrelation(id){state.correlations=state.correlations.filter(c=>c.id!==id);if(state.alignment.markerCorrelationId===id)state.alignment.markerCorrelationId=null;save();renderAll()}
function markerOptions(){
  const sel=$('#corrMarkerSelect');if(!sel)return;
  const rows=state.correlations.filter(c=>c.marker);
  sel.innerHTML='<option value="">Selecione</option>'+rows.map(c=>`<option value="${c.id}" ${state.alignment.markerCorrelationId===c.id?'selected':''}>${corName(c)}</option>`).join('');
  $('.corr-marker-field').style.display=state.alignment.mode==='marker'?'block':'none';
  $('#corrAlignMode').value=state.alignment.mode;
}
function corName(c){
  const ai=state.sections.findIndex(s=>s.id===c.a.sectionId),bi=state.sections.findIndex(s=>s.id===c.b.sectionId);
  const al=state.sections[ai]?.levels?.[c.a.levelIndex],bl=state.sections[bi]?.levels?.[c.b.levelIndex];
  return `${ai>=0?letter(ai):'?'} ${al?.code||''} ↔ ${bi>=0?letter(bi):'?'} ${bl?.code||''}`;
}
function renderActive(){
  const html=state.correlations.length?state.correlations.map(c=>`<div class="corr-active-row"><div><b>${esc(corName(c))}</b><small>${esc(c.type)} · ${esc(c.confidence)}${c.marker?' · marcador':''}</small></div><button data-del-cor="${c.id}">×</button></div>`).join(''):'<p class="corr-empty">Nenhuma correlação salva.</p>';
  $('#corrActive').innerHTML=html;
  $$('[data-del-cor]').forEach(b=>b.onclick=()=>removeCorrelation(b.dataset.delCor));
}
function drawLines(){
  const svg=$('#corrLines'),canvas=$('#corrCanvas');if(!svg||!canvas)return;
  const cr=canvas.getBoundingClientRect();svg.setAttribute('viewBox',`0 0 ${cr.width} ${cr.height}`);svg.setAttribute('width',cr.width);svg.setAttribute('height',cr.height);
  let out='';
  state.correlations.forEach(c=>{
    const ai=state.sections.findIndex(s=>s.id===c.a.sectionId),bi=state.sections.findIndex(s=>s.id===c.b.sectionId);
    if(ai<0||bi<0)return;
    const ae=$(`[data-section-index="${ai}"] [data-level="${ai}:${c.a.levelIndex}"]`),be=$(`[data-section-index="${bi}"] [data-level="${bi}:${c.b.levelIndex}"]`);
    if(!ae||!be)return;
    const ar=ae.getBoundingClientRect(),br=be.getBoundingClientRect();
    const x1=ar.right-cr.left,x2=br.left-cr.left,y1=ar.top+ar.height/2-cr.top,y2=br.top+br.height/2-cr.top;
    const cls=c.marker?'marker':(c.confidence==='possivel'||c.style==='tracejada'?'possible':'high');
    out+=`<line class="${cls}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"></line>`;
  });
  svg.innerHTML=out;
}
function renderColumnsPage(){
  $('#corrColumnsList').innerHTML=state.sections.length?state.sections.map((s,i)=>{
    const g=gpsOf(s);
    return `<article class="corr-column-card"><div class="corr-column-letter" style="background:${COLORS[i%COLORS.length]}">${letter(i)}</div><div><h3>${esc(s.project)}</h3><p>${esc(s.place||'Local não informado')}</p><small>${g?`WGS 84 · ${g.lat.toFixed(6)}, ${g.lon.toFixed(6)}${Number.isFinite(g.accuracy)?` · ±${Math.round(g.accuracy)} m`:''}`:'GPS não registrado'} · ${s.levels.length} níveis · ${totalThickness(s).toFixed(2).replace('.',',')} m</small></div><div class="corr-column-actions"><button data-move="${s.id}" data-dir="-1">↑</button><button data-move="${s.id}" data-dir="1">↓</button><button data-remove="${s.id}">Remover</button></div></article>`;
  }).join(''):'<p class="corr-empty">Nenhuma coluna carregada.</p>';
  $$('[data-remove]').forEach(b=>b.onclick=()=>removeSection(b.dataset.remove));
  $$('[data-move]').forEach(b=>b.onclick=()=>moveSection(b.dataset.move,Number(b.dataset.dir)));
}
function renderMap(){
  const list=$('#corrMapList'),pts=state.sections.map((s,i)=>({s,i,g:gpsOf(s)})).filter(x=>x.g);
  list.innerHTML=pts.length?pts.map(x=>`<div class="corr-map-row"><b><i style="background:${COLORS[x.i%COLORS.length]}">${letter(x.i)}</i>${esc(x.s.project)}</b><span>${x.g.lat.toFixed(6)}, ${x.g.lon.toFixed(6)}${Number.isFinite(x.g.accuracy)?` · ±${Math.round(x.g.accuracy)} m`:''}</span></div>`).join(''):'<p class="corr-empty">Nenhuma coluna possui GPS registrado.</p>';
  if(typeof L==='undefined'){ $('#corrMap').innerHTML='<div class="corr-map-fallback">Leaflet não está disponível nesta execução. As coordenadas continuam listadas abaixo.</div>';return}
  if(!map){
    map=L.map('corrMap',{zoomControl:true});
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
  }
  if(mapLayer){mapLayer.clearLayers()} else {mapLayer=L.layerGroup().addTo(map)}
  pts.forEach(x=>{
    const icon=L.divIcon({className:'corr-map-marker',html:`<span style="background:${COLORS[x.i%COLORS.length]}">${letter(x.i)}</span>`,iconSize:[28,28],iconAnchor:[14,14]});
    L.marker([x.g.lat,x.g.lon],{icon}).bindPopup(`<b>${esc(x.s.project)}</b><br>${x.g.lat.toFixed(6)}, ${x.g.lon.toFixed(6)}<br>${x.s.levels.length} níveis · ${totalThickness(x.s).toFixed(2)} m`).addTo(mapLayer);
  });
  if(pts.length>1)L.polyline(pts.map(x=>[x.g.lat,x.g.lon]),{weight:2,dashArray:'5,5',opacity:.75}).addTo(mapLayer);
  fitMap();
  setTimeout(()=>map.invalidateSize(),80);
}
function fitMap(){
  if(!map)return;
  const pts=state.sections.map(gpsOf).filter(Boolean);if(!pts.length){map.setView([-20.5,-54.6],5);return}
  map.fitBounds(pts.map(g=>[g.lat,g.lon]),{padding:[24,24],maxZoom:14});
}
function renderMobileAlign(){
  const box=$('#corrMobileAlign');if(!box)return;
  const marks=state.correlations.filter(c=>c.marker);
  box.innerHTML=`<label>Método<select id="corrMobileAlignMode"><option value="base">Base das colunas</option><option value="top">Topo das colunas</option><option value="marker">Nível marcador</option></select></label>${state.alignment.mode==='marker'?`<label>Marcador<select id="corrMobileMarker"><option value="">Selecione</option>${marks.map(c=>`<option value="${c.id}" ${state.alignment.markerCorrelationId===c.id?'selected':''}>${esc(corName(c))}</option>`).join('')}</select></label>`:''}`;
  $('#corrMobileAlignMode').value=state.alignment.mode;$('#corrMobileAlignMode').onchange=e=>{state.alignment.mode=e.target.value;save();renderAll()};
  if($('#corrMobileMarker'))$('#corrMobileMarker').onchange=e=>{state.alignment.markerCorrelationId=e.target.value||null;save();renderAll()};
}
function renderAll(){
  if(!$('#correlacaoEstratigraficaModal'))return;
  summary();renderMini();renderMobileColumns();renderCanvas();renderSelection();markerOptions();renderActive();renderColumnsPage();renderMobileAlign();
  if(state.tab==='data')$('#corrJSON').textContent=JSON.stringify(state,null,2);
  if(state.tab==='map')renderMap();
}
function download(name,type,text){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1200)}
function exportJSON(){download('correlacao_estratigrafica.json','application/json',JSON.stringify(state,null,2))}
function exportCSV(){
  const h=['id','origem_coluna','origem_nivel','destino_coluna','destino_nivel','tipo','criterio','confianca','representacao','nivel_marcador','observacoes'];
  const rows=state.correlations.map(c=>{
    const as=state.sections.find(s=>s.id===c.a.sectionId),bs=state.sections.find(s=>s.id===c.b.sectionId);
    return [c.id,as?.project||'',as?.levels?.[c.a.levelIndex]?.code||'',bs?.project||'',bs?.levels?.[c.b.levelIndex]?.code||'',c.type,c.criterion,c.confidence,c.style,c.marker?'sim':'nao',c.notes||''];
  });
  const q=v=>'"'+String(v??'').replaceAll('"','""')+'"';
  download('correlacoes.csv','text/csv;charset=utf-8','\ufeff'+[h,...rows].map(r=>r.map(q).join(';')).join('\n'));
}
function exportSVG(){
  const W=Math.max(760,state.sections.length*170+180),H=760,top=110,bottom=680,maxT=Math.max(1,...state.sections.map(totalThickness)),scale=(bottom-top)/maxT;
  const colW=72,gap=(W-160)/(Math.max(1,state.sections.length)),xs=state.sections.map((s,i)=>80+i*gap+gap/2-colW/2);
  let defs='',layers='',lines='';
  const used=[...new Set(state.sections.flatMap(s=>s.levels.map(l=>l.lith)))];
  used.forEach(c=>{defs+=`<pattern id="p${c}" patternUnits="userSpaceOnUse" width="50" height="50"><image href="./assets/padroes/fgdc/${c}.svg" width="50" height="50"/></pattern>`});
  state.sections.forEach((s,si)=>{let y=bottom;layers+=`<text x="${xs[si]+colW/2}" y="82" text-anchor="middle" font-size="13" font-weight="700">${esc(letter(si)+' · '+s.project)}</text>`;s.levels.forEach((l,li)=>{const h=Math.max(4,(Number(l.thickness)||0)*scale);y-=h;layers+=`<rect id="s${si}l${li}" x="${xs[si]}" y="${y}" width="${colW}" height="${h}" fill="url(#p${l.lith})" stroke="#34566a"/>`;});});
  state.correlations.forEach(c=>{
    const ai=state.sections.findIndex(s=>s.id===c.a.sectionId),bi=state.sections.findIndex(s=>s.id===c.b.sectionId);if(ai<0||bi<0)return;
    const mid=(s,li)=>bottom-(s.levels.slice(0,li).reduce((a,l)=>a+(Number(l.thickness)||0),0)+(Number(s.levels[li]?.thickness)||0)/2)*scale;
    const y1=mid(state.sections[ai],c.a.levelIndex),y2=mid(state.sections[bi],c.b.levelIndex);
    const stroke=c.marker?'#0063c7':'#174f78',dash=(c.confidence==='possivel'||c.style==='tracejada')?'6 5':'',width=c.marker?3:1.7;
    lines+=`<line x1="${xs[ai]+colW}" y1="${y1}" x2="${xs[bi]}" y2="${y2}" stroke="${stroke}" stroke-width="${width}" ${dash?`stroke-dasharray="${dash}"`:''}/>`;
  });
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>${defs}</defs><rect width="100%" height="100%" fill="white"/><text x="${W/2}" y="30" text-anchor="middle" font-size="22" font-weight="700">Correlação Estratigráfica</text><text x="${W/2}" y="50" text-anchor="middle" font-size="11">ITA ARANDU MS · DOI 10.5281/zenodo.21923101</text>${layers}${lines}</svg>`;
  download('correlacao_estratigrafica.svg','image/svg+xml',svg);
}
load();
document.addEventListener('click',e=>{
  const a=e.target.closest('[data-tool-action="correlacaoEstratigrafica"]');if(a){e.preventDefault();open('correlate')}
  const h=e.target.closest('[data-tool-action="correlacaoAjuda"]');if(h){e.preventDefault();open('help')}
});
window.addEventListener('resize',()=>{if(state.tab==='correlate')requestAnimationFrame(drawLines);if(map)setTimeout(()=>map.invalidateSize(),100)});
window.ITA_CORRELACAO_ESTRATIGRAFICA={open,state};
})();
