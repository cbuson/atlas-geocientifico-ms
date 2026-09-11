(function(){
'use strict';

const DB_NAME='ita_arandu_campo_master_v20';
const DB_VERSION=2;
const STORE='stations';
const DRAFT_STORE='drafts';
const DRAFT_KEY='active';
const LEGACY_DB_NAME='ita_arandu_campo_v01';
const LEGACY_STORE='field_records';
const LEGACY_MIGRATION_KEY='ita_arandu_campo_legacy_migrated_v38459';
const PROFILE_KEY='ita_arandu_campo_profiles_v20';
const MODE_KEY='ita_arandu_campo_mode_v20';
const TAGS=['afloramento','contato','falha','dobra','mineralização','amostra','água','solo','caverna','fóssil','risco','geossítio'];
const ALTER_TYPES=['oxidação','silicificação','argilização','sericitização','carbonatação','cloritização','lateritização'];
const GEO_PROC=['fraturação','queda de blocos','deslizamento','erosão','instabilidade de talude','água'];
const MINERALS=['quartzo','feldspato','plagioclásio','mica','calcita','dolomita','hematita','magnetita','goethita','pirolusita','apatita','pirita','calcopirita','barita','fluorita','granada'];
const LITH={
 'Ígnea':['Granito','Granodiorito','Diorito','Gabro','Basalto','Riolito','Andesito','Dacito','Pegmatito','Dolerito','Outra ígnea'],
 'Sedimentar':['Arenito','Siltito','Argilito','Folhelho','Conglomerado','Brecha sedimentar','Calcário','Dolomito','Evaporito','Chert','Outra sedimentar'],
 'Metamórfica':['Gnaisse','Xisto','Filito','Quartzito','Mármore','Anfibolito','Migmatito','Metaconglomerado','Outra metamórfica'],
 'Sedimento inconsolidado':['Areia','Silte','Argila','Cascalho','Colúvio','Alúvio','Outro sedimento'],
 'Solo':['Latossolo','Argissolo','Neossolo','Gleissolo','Vertissolo','Solo não classificado'],
 'Não determinada':['Não determinada']
};
const PHOTO_TYPES=['vista geral','afloramento','detalhe','estrutura','amostra','mineral','paisagem','acesso','escala','documento'];
const STRUCT_TYPES=['acamamento','foliação','lineação','fratura','diaclase','falha','dobra','contato','veio','dique','outro'];
const MEASURE_TYPES=['plano','lineação','falha','fratura','acamamento','foliação','eixo de dobra','veio','outro'];
const SAMPLE_TYPES=['rocha','solo','sedimento','água','mineral','fóssil','outro'];

const S={
  db:null,
  gpsOriginal:null,
  gpsCurrent:null,
  stream:null,
  orientation:null,
  structures:[],
  measures:[],
  samples:[],
  photos:[],
  sketch:{tool:'pen',actions:[],redo:[],drawing:false,start:null,last:null},
  municipalityGeo:null,
  records:[],
  editingId:null,
  restoringDraft:false,
  draftTimer:null,
  draftSavedAt:null
};

const $=id=>document.getElementById(id);
const q=(sel,root=document)=>root.querySelector(sel);
const qa=(sel,root=document)=>[...root.querySelectorAll(sel)];
const val=id=>$(id)?.value?.trim?.()||'';
const nval=id=>{const n=Number(val(id));return Number.isFinite(n)?n:null};
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const iso=()=>new Date().toISOString();
const pad=n=>String(n).padStart(2,'0');

function localDateParts(d=new Date()){
  return {
    date:`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`,
    time:`${pad(d.getHours())}:${pad(d.getMinutes())}`
  };
}
function openDB(){
  if(S.db)return Promise.resolve(S.db);
  return new Promise((resolve,reject)=>{
    const req=indexedDB.open(DB_NAME,DB_VERSION);
    req.onupgradeneeded=()=>{
      const db=req.result;
      if(!db.objectStoreNames.contains(STORE)){
        const st=db.createObjectStore(STORE,{keyPath:'id'});
        st.createIndex('created_at','created_at',{unique:false});
        st.createIndex('station_code','station_code',{unique:true});
        st.createIndex('campaign','identity.campaign',{unique:false});
      }
      if(!db.objectStoreNames.contains(DRAFT_STORE)){
        db.createObjectStore(DRAFT_STORE,{keyPath:'id'});
      }
    };
    req.onsuccess=()=>{S.db=req.result;resolve(S.db)};
    req.onerror=()=>reject(req.error);
  });
}
async function getAll(){
  const db=await openDB();
  return await new Promise((resolve,reject)=>{
    const req=db.transaction(STORE,'readonly').objectStore(STORE).getAll();
    req.onsuccess=()=>resolve(req.result||[]);
    req.onerror=()=>reject(req.error);
  });
}
async function put(rec){
  const db=await openDB();
  return await new Promise((resolve,reject)=>{
    const tx=db.transaction(STORE,'readwrite');
    tx.objectStore(STORE).put(rec);
    tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);
  });
}
async function del(id){
  const db=await openDB();
  return await new Promise((resolve,reject)=>{
    const tx=db.transaction(STORE,'readwrite');
    tx.objectStore(STORE).delete(id);
    tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);
  });
}

async function getDraft(){
  const db=await openDB();
  return await new Promise((resolve,reject)=>{
    const req=db.transaction(DRAFT_STORE,'readonly').objectStore(DRAFT_STORE).get(DRAFT_KEY);
    req.onsuccess=()=>resolve(req.result||null);req.onerror=()=>reject(req.error);
  });
}
async function putDraft(draft){
  const db=await openDB();
  return await new Promise((resolve,reject)=>{
    const tx=db.transaction(DRAFT_STORE,'readwrite');
    tx.objectStore(DRAFT_STORE).put({...draft,id:DRAFT_KEY});
    tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);
  });
}
async function deleteDraft(){
  const db=await openDB();
  return await new Promise((resolve,reject)=>{
    const tx=db.transaction(DRAFT_STORE,'readwrite');
    tx.objectStore(DRAFT_STORE).delete(DRAFT_KEY);
    tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);
  });
}
function storageFailureMessage(e){
  const name=e?.name||'';
  if(name==='QuotaExceededError')return 'Armazenamento local insuficiente. Exporte um pacote ZIP antes de continuar e libere espaço no dispositivo.';
  return e?.message||String(e||'erro de armazenamento');
}
function autosaveStatus(msg,kind='ok'){
  const el=$('campoAutosaveStatus');
  if(el){el.textContent=msg;el.dataset.state=kind;}
}
function serializeForm(){
  const out={};
  qa('#campoForm input,#campoForm select,#campoForm textarea').forEach(el=>{
    if(!el.id||el.type==='file')return;
    if(el.type==='checkbox')out[el.id]={type:'checkbox',checked:!!el.checked};
    else if(el.type==='radio'){if(el.checked)out[el.id]={type:'radio',value:el.value};}
    else out[el.id]={type:'value',value:el.value};
  });
  return out;
}
function restoreForm(data={}){
  const deferred=[];
  Object.entries(data||{}).forEach(([id,o])=>{
    const el=$(id);if(!el)return;
    if(id==='campoLitologia')return deferred.push([id,o]);
    if(o?.type==='checkbox')el.checked=!!o.checked;
    else if(o?.type==='radio'){if(el.value===o.value)el.checked=true;}
    else el.value=o?.value??'';
  });
  if($('campoLitologiaGrupo'))$('campoLitologiaGrupo').dispatchEvent(new Event('change'));
  deferred.forEach(([id,o])=>{if($(id))$(id).value=o?.value??''});
}
function draftHasContent(){
  return !!(val('campoObservador')||val('campoLocalNome')||val('campoNome')||val('campoObservacao')||S.photos.length||S.samples.length||S.measures.length||S.structures.length);
}
async function saveDraft({silent=false}={}){
  if(S.restoringDraft)return;
  try{
    const draft={
      schema_version:'2.1-draft',saved_at:iso(),editing_id:S.editingId||null,mode:$('campoForm')?.closest('.ita-campo-master')?.classList.contains('advanced-mode')?'advanced':'essential',
      form:serializeForm(),gps_original:S.gpsOriginal?structuredClone(S.gpsOriginal):null,gps_current:S.gpsCurrent?structuredClone(S.gpsCurrent):null,
      orientation:S.orientation?structuredClone(S.orientation):null,structures:structuredClone(S.structures),measures:structuredClone(S.measures),samples:structuredClone(S.samples),photos:structuredClone(S.photos),sketch_actions:structuredClone(S.sketch.actions||[]),
      tags:checkedValues('campoTagsChips'),alteration_types:checkedValues('campoAlteracaoTipos'),geotechnical_processes:checkedValues('campoGeotecniaProcessos'),minerals:mineralValues()
    };
    await putDraft(draft);S.draftSavedAt=draft.saved_at;
    autosaveStatus(`Rascunho salvo localmente · ${new Date(draft.saved_at).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}`,'ok');
    if(!silent&&window.ITA_FIELD_ROBUSTNESS?.refreshStorage)window.ITA_FIELD_ROBUSTNESS.refreshStorage();
  }catch(e){autosaveStatus('Falha no rascunho · '+storageFailureMessage(e),'error');}
}
function scheduleDraft(delay=650){
  if(S.restoringDraft)return;
  clearTimeout(S.draftTimer);autosaveStatus('Alterações pendentes de salvamento…','pending');
  S.draftTimer=setTimeout(()=>saveDraft({silent:true}),delay);
}
async function restoreDraft(){
  let d=null;try{d=await getDraft()}catch(e){autosaveStatus('Não foi possível ler o rascunho local · '+storageFailureMessage(e),'error');return false}
  if(!d?.form)return false;
  S.restoringDraft=true;
  try{
    restoreForm(d.form);S.editingId=d.editing_id||null;S.gpsOriginal=d.gps_original||null;S.gpsCurrent=d.gps_current||null;S.orientation=d.orientation||null;
    S.structures=structuredClone(d.structures||[]);S.measures=structuredClone(d.measures||[]);S.samples=structuredClone(d.samples||[]);S.photos=structuredClone(d.photos||[]);S.sketch.actions=structuredClone(d.sketch_actions||[]);
    qa('#campoTagsChips input').forEach(x=>x.checked=(d.tags||[]).includes(x.value));
    qa('#campoAlteracaoTipos input').forEach(x=>x.checked=(d.alteration_types||[]).includes(x.value));
    qa('#campoGeotecniaProcessos input').forEach(x=>x.checked=(d.geotechnical_processes||[]).includes(x.value));
    qa('.ita-mineral-item').forEach(l=>{const m=(d.minerals||[]).find(x=>x.name===q('input',l).value);q('input',l).checked=!!m;q('select',l).disabled=!m;if(m)q('select',l).value=m.abundance});
    mode(d.mode||'essential');renderArrays();renderPhotos();S.sketch.redraw?.();updateLocationUI();updateCompleteness();await refreshParentOptions();
    autosaveStatus(`Estação não finalizada recuperada · ${S.photos.length} foto(s) · ${S.measures.length} medida(s) · ${S.samples.length} amostra(s).`,'recovered');
    $('campoStatus').textContent='Rascunho completo recuperado do IndexedDB, incluindo fotografias armazenadas localmente.';
    return true;
  }finally{S.restoringDraft=false;}
}
function openLegacyDB(){
  return new Promise(resolve=>{
    try{const req=indexedDB.open(LEGACY_DB_NAME);req.onsuccess=()=>resolve(req.result);req.onerror=()=>resolve(null);req.onblocked=()=>resolve(null)}catch(_){resolve(null)}
  });
}
function legacyStatus(v){
  const x=String(v||'RASCUNHO').toUpperCase();
  if(x==='REVISADA')return 'revisada';if(x==='APROVADA_PARA_ANALISE'||x==='VALIDADA')return 'validada';if(x==='REJEITADA')return 'rejeitada';if(x==='COMPLETA')return 'completa';return 'rascunho';
}
function migrateLegacyRecord(r){
  const loc=(Number.isFinite(Number(r?.location?.latitude))&&Number.isFinite(Number(r?.location?.longitude)))?{latitude:Number(r.location.latitude),longitude:Number(r.location.longitude),accuracy_m:Number(r.location.accuracy_m)||null,altitude_m:Number(r.location.altitude_m)||null,altitude_accuracy_m:null,utm:latLonToUTM(Number(r.location.latitude),Number(r.location.longitude)),source:'legacy_migration',captured_at_utc:null}:null;
  const photos=(r.photos||[]).map((p,i)=>({id:p.id||uuid(),name:p.name||`${r.station_code||'LEGACY'}_F${String(i+1).padStart(2,'0')}`,source:'legacy_migration',classification:p.category||'detalhe',description:p.caption||'',original_blob:p.blob||null,original_sha256:null,overlay_blob:null,overlay_sha256:null,georeference_status:'legacy_record',metadata:{origin:'legacy_migration',station_code:r.station_code||null}}));
  return {id:`legacy-${r.id||uuid()}`,schema_version:'2.1-migrated',project:'ITA ARANDU MS',module:'Caderno de Campo Geocientífico Digital',station_code:r.station_code||r.spot?.spot_id||`ITA-LEGACY-${Date.now()}`,created_at:r.created_at||iso(),updated_at:iso(),status:legacyStatus(r.status),identity:{campaign:r.campanha||'',observer:r.observador||'',role:'',discipline:r.disciplina||'',local_name:r.nome_ponto||'',station_name:r.nome_ponto||'',date:r.data||'',local_time:r.hora||'',utc:null,timezone:null},relations:{spot_id:r.spot?.spot_id||null,parent_station_code:r.spot?.parent_spot_id||null,profile_id:null,profile_order:null,tags:r.spot?.tags||[]},location:{current:loc,original_gps:null,manual_edited:false,municipality:r.location?.municipio||'',access:{type:'',condition:'',reference:r.location?.acesso||''},hex_250:r.location?.hex_250||'',hex_500:r.location?.hex_500||'',hex_1000:r.location?.hex_1000||''},exposure:{type:r.observation?.exposure_type||'',quality:r.observation?.exposure_quality||''},lithology:{group:r.lithology?.group||'',name:r.lithology?.name||'',facies:'',description:[r.lithology?.texture,r.lithology?.mineralogy,r.lithology?.alteration_weathering].filter(Boolean).join(' · '),confidence:''},mineralogy:{minerals:[],others:r.lithology?.mineralogy||''},alteration:{presence:'',intensity:'',types:[],description:r.lithology?.alteration_weathering||''},structures:[],measurements:(r.structures?.measurements||[]).map(x=>({id:x.id||uuid(),type:x.type||'',direction:x.azimuth??'',dip:x.dip??'',dip_direction:x.dip_direction??'',strike:'',method:x.method||'',instrument:x.instrument_source||'',precision:x.quality||'',time:''})),observation:{observed:r.observation?.text||'',interpretation:r.interpretation?.text||''},hydrogeology:{presence:'',type:'',temperature_c:null,ph:null,conductivity:null,instrument:'',note:r.interpretation?.hydrogeology||''},mineralization:{evidence:'',style:'',width_m:null,continuity:'',host_rock:'',associated_alteration:'',description:r.interpretation?.mineralization||''},geotechnics:{evaluated:!!r.interpretation?.geotechnics,weathering:'',stability:'',processes:[],note:r.interpretation?.geotechnics||''},samples:(r.samples||[]).map(x=>({id:x.id||uuid(),local_code:x.code||x.sample_code||'',type:x.material||'',depth:'',weight:x.mass||'',description:x.description||'',destination:x.purpose||'',analysis:'',responsible:r.observador||'',igsn_status:x.igsn_status||'nao_registrado',igsn_id:x.igsn_id||''})),photos,sketch:null,sensors:{device_orientation:null,note:'Registro migrado do schema 0.4; sensores preservados apenas quando disponíveis no registro legado.'},quality:{general_confidence:r.interpretation?.confidence||'',sensitivity:r.governance?.sensitivity||'local',restriction_reason:'',geoethics:{origin:'observacao_campo',access_level:'publico',authorization_status:'nao_aplicavel',authority:'',authorized_purpose:'',authorization_date:'',reuse_conditions:'',review_withdrawal_channel:'',frameworks:['ITA-GEOETHICS-1.0','CARE']},completeness_percent:null,checklist:[],review:{reviewer:'',comment:'Migrado automaticamente do schema 0.4 sem apagar o banco legado.',state:legacyStatus(r.status)}},provenance:{migration:'schema 0.4 → 2.1',legacy_id:r.id||null,legacy_db:LEGACY_DB_NAME,hash_algorithm:'SHA-256'}};
}
async function migrateLegacyOnce(){
  if(localStorage.getItem(LEGACY_MIGRATION_KEY)==='1')return {migrated:0};
  const db=await openLegacyDB();if(!db||!db.objectStoreNames.contains(LEGACY_STORE)){localStorage.setItem(LEGACY_MIGRATION_KEY,'1');return {migrated:0}}
  const rows=await new Promise(resolve=>{try{const req=db.transaction(LEGACY_STORE,'readonly').objectStore(LEGACY_STORE).getAll();req.onsuccess=()=>resolve(req.result||[]);req.onerror=()=>resolve([])}catch(_){resolve([])}});
  const current=await getAll(),codes=new Set(current.map(x=>x.station_code));let migrated=0;
  for(const r of rows){const m=migrateLegacyRecord(r);if(!codes.has(m.station_code)){try{await put(m);codes.add(m.station_code);migrated++}catch(_){}}}
  localStorage.setItem(LEGACY_MIGRATION_KEY,'1');
  if(migrated)$('campoStatus').textContent=`${migrated} registro(s) legado(s) preservado(s) no Campo Master 2.1. O banco anterior não foi apagado.`;
  return {migrated};
}
function uuid(){
  if(crypto.randomUUID)return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>{
    const r=Math.random()*16|0,v=c==='x'?r:(r&3|8);return v.toString(16);
  });
}
function stationCode(d=new Date(),seq=1){
  return `ITA-MS-${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}-${String(seq).padStart(3,'0')}`;
}
async function nextStationCode(){
  const d=val('campoData')||localDateParts().date;
  const key=d.replaceAll('-','');
  const rows=await getAll();
  let max=0;
  rows.forEach(r=>{
    const m=String(r.station_code||'').match(new RegExp(`^ITA-MS-${key}-(\\d{3})$`));
    if(m)max=Math.max(max,Number(m[1]));
  });
  return `ITA-MS-${key}-${String(max+1).padStart(3,'0')}`;
}
function latLonToUTM(lat,lon){
  if(!Number.isFinite(lat)||!Number.isFinite(lon)||lat<-80||lat>84)return null;
  const a=6378137,ecc=0.00669438,k0=.9996;
  const zone=Math.floor((lon+180)/6)+1, origin=(zone-1)*6-180+3;
  const ep=ecc/(1-ecc),lr=lat*Math.PI/180,or=origin*Math.PI/180,lor=lon*Math.PI/180;
  const N=a/Math.sqrt(1-ecc*Math.sin(lr)**2),T=Math.tan(lr)**2,C=ep*Math.cos(lr)**2,A=Math.cos(lr)*(lor-or);
  const M=a*((1-ecc/4-3*ecc**2/64-5*ecc**3/256)*lr-(3*ecc/8+3*ecc**2/32+45*ecc**3/1024)*Math.sin(2*lr)+(15*ecc**2/256+45*ecc**3/1024)*Math.sin(4*lr)-(35*ecc**3/3072)*Math.sin(6*lr));
  let e=k0*N*(A+(1-T+C)*A**3/6+(5-18*T+T*T+72*C-58*ep)*A**5/120)+500000;
  let n=k0*(M+N*Math.tan(lr)*(A*A/2+(5-T+9*C+4*C*C)*A**4/24+(61-58*T+T*T+600*C-330*ep)*A**6/720));
  const hem=lat<0?'S':'N';if(lat<0)n+=10000000;
  return {zone,hemisphere:hem,epsg:(lat<0?32700:32600)+zone,easting:e,northing:n};
}
function utmText(u){return u?`${u.zone}${u.hemisphere} · ${Math.round(u.easting)} E · ${Math.round(u.northing)} N · EPSG:${u.epsg}`:'—'}
function gpsClass(acc){if(!Number.isFinite(acc))return 'sem precisão';if(acc<=5)return 'excelente';if(acc<=10)return 'boa';if(acc<=25)return 'moderada';return 'baixa'}
function pointInRing(pt,ring){
  let inside=false;const [x,y]=pt;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++){
    const xi=ring[i][0],yi=ring[i][1],xj=ring[j][0],yj=ring[j][1];
    const hit=((yi>y)!=(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi+0.0)+xi);
    if(hit)inside=!inside;
  }
  return inside;
}
function pointInGeometry(pt,g){
  if(!g)return false;
  if(g.type==='Polygon')return g.coordinates.length&&pointInRing(pt,g.coordinates[0])&&!g.coordinates.slice(1).some(r=>pointInRing(pt,r));
  if(g.type==='MultiPolygon')return g.coordinates.some(p=>p.length&&pointInRing(pt,p[0])&&!p.slice(1).some(r=>pointInRing(pt,r)));
  return false;
}
async function municipality(lat,lon){
  try{
    if(!S.municipalityGeo){
      const r=await fetch('./camadas/arquivos/municipios_limites_base.geojson',{cache:'default'});
      if(!r.ok)throw new Error('municipios');
      S.municipalityGeo=await r.json();
    }
    for(const f of S.municipalityGeo.features||[]){
      if(pointInGeometry([lon,lat],f.geometry)){
        const p=f.properties||{};
        return p.NM_MUN||p.nm_mun||p.nome||p.NOME||p.municipio||p.MUNICIPIO||'Município identificado';
      }
    }
  }catch(_){}
  return '';
}
async function shaBlob(blob){
  if(!blob?.arrayBuffer||!crypto?.subtle)return null;
  const h=await crypto.subtle.digest('SHA-256',await blob.arrayBuffer());
  return [...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,'0')).join('');
}
function blobUrl(blob){return URL.createObjectURL(blob)}
function download(blob,name){const u=blobUrl(blob),a=document.createElement('a');a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1200)}
function canvasBlob(c,type='image/png',quality=.92){return new Promise((res,rej)=>c.toBlob(b=>b?res(b):rej(new Error('blob')),type,quality))}
async function imageFromBlob(blob){
  if(window.createImageBitmap){try{return await createImageBitmap(blob)}catch(_){}}
  return await new Promise((res,rej)=>{const i=new Image(),u=blobUrl(blob);i.onload=()=>{URL.revokeObjectURL(u);res(i)};i.onerror=rej;i.src=u});
}
function normalizeHeading(v){return Number.isFinite(v)?((v%360)+360)%360:null}

function renderPickers(){
  $('campoTagsChips').innerHTML=TAGS.map(x=>`<label><input type="checkbox" value="${esc(x)}">${esc(x)}</label>`).join('');
  $('campoAlteracaoTipos').innerHTML=ALTER_TYPES.map(x=>`<label><input type="checkbox" value="${esc(x)}">${esc(x)}</label>`).join('');
  $('campoGeotecniaProcessos').innerHTML=GEO_PROC.map(x=>`<label><input type="checkbox" value="${esc(x)}">${esc(x)}</label>`).join('');
  $('campoMineraisPicker').innerHTML=MINERALS.map(x=>`<label class="ita-mineral-item"><input type="checkbox" value="${esc(x)}"><span>${esc(x)}</span><select disabled><option>principal</option><option>secundário</option><option>traço</option><option>possível</option></select></label>`).join('');
  qa('#campoMineraisPicker input').forEach(c=>c.addEventListener('change',()=>{q('select',c.closest('label')).disabled=!c.checked;updateCompleteness()}));
}
function checkedValues(root){return qa('input[type="checkbox"]:checked',$(root)).map(x=>x.value)}
function mineralValues(){
  return qa('.ita-mineral-item',$('campoMineraisPicker')).filter(x=>q('input',x).checked).map(x=>({name:q('input',x).value,abundance:q('select',x).value}));
}
function setupLithology(){
  $('campoLitologiaGrupo').addEventListener('change',()=>{
    const group=val('campoLitologiaGrupo'),list=LITH[group]||[];
    $('campoLitologia').innerHTML='<option value="">Selecionar</option>'+list.map(x=>`<option>${esc(x)}</option>`).join('');
    updateCompleteness();
  });
}
function mode(mode){
  $('campoForm').closest('.ita-campo-master').classList.toggle('advanced-mode',mode==='advanced');
  $('campoModoEssencial').classList.toggle('active',mode!=='advanced');
  $('campoModoAvancado').classList.toggle('active',mode==='advanced');
  localStorage.setItem(MODE_KEY,mode);
}
function loadProfiles(){
  let p={campaigns:[],observers:[]};try{p=JSON.parse(localStorage.getItem(PROFILE_KEY)||'{}')}catch(_){}
  $('campoCampanhasLista').innerHTML=(p.campaigns||[]).map(x=>`<option value="${esc(x)}">`).join('');
  $('campoObservadoresLista').innerHTML=(p.observers||[]).map(x=>`<option value="${esc(x)}">`).join('');
}
function saveProfiles(){
  let p={campaigns:[],observers:[]};try{p=JSON.parse(localStorage.getItem(PROFILE_KEY)||'{}')}catch(_){}
  const c=val('campoCampanha'),o=val('campoObservador');
  if(c&&!p.campaigns.includes(c))p.campaigns.push(c);
  if(o&&!p.observers.includes(o))p.observers.push(o);
  localStorage.setItem(PROFILE_KEY,JSON.stringify(p));loadProfiles();
  $('campoStatus').textContent='Campanha e observador guardados neste navegador.';
}
async function newStation({clearDraft=true,confirmDiscard=false}={}){
  if(confirmDiscard&&draftHasContent()&&!confirm('Há alterações locais nesta estação. Criar uma nova estação e descartar o rascunho atual?'))return;
  if(clearDraft){try{await deleteDraft()}catch(_){}}
  S.editingId=null;S.gpsOriginal=null;S.gpsCurrent=null;S.structures=[];S.measures=[];S.samples=[];S.photos=[];
  stopCamera();clearSketch();
  $('campoForm').reset();
  const t=localDateParts();$('campoData').value=t.date;$('campoHora').value=t.time;$('campoUtc').value=iso();
  $('campoStationCode').value=await nextStationCode();$('campoSpotId').value=`ITA-SPOT-${Date.now().toString(36).toUpperCase()}`;
  $('campoEstadoFicha').value='rascunho';$('campoEstadoResumo').value='rascunho';
  $('campoLat').readOnly=$('campoLon').readOnly=true;
  renderArrays();renderPhotos();await refreshParentOptions();updateLocationUI();updateCompleteness();
  autosaveStatus('Nova estação preparada · salvamento automático ativo.','ok');
}
async function refreshParentOptions(){
  S.records=await getAll();
  $('campoParentSpot').innerHTML='<option value="">Sem estação pai</option>'+S.records.map(r=>`<option value="${esc(r.station_code)}">${esc(r.station_code)} · ${esc(r.identity?.station_name||r.identity?.local_name||'')}</option>`).join('');
}
function currentLocation(){
  const lat=nval('campoLat'),lon=nval('campoLon');if(lat==null||lon==null)return null;
  return {latitude:lat,longitude:lon,accuracy_m:nval('campoPrecisao'),altitude_m:nval('campoAltitude'),altitude_accuracy_m:nval('campoPrecisaoVertical'),utm:latLonToUTM(lat,lon),source:val('campoGpsFonte')||'form',captured_at_utc:val('campoGpsHora')||null};
}
async function setLocation(p,{setOriginal=false}={}){
  if(!p)return;
  p.utm=p.utm||latLonToUTM(p.latitude,p.longitude);
  S.gpsCurrent={...p};
  if(setOriginal)S.gpsOriginal={...p};
  $('campoLat').value=Number(p.latitude).toFixed(7);$('campoLon').value=Number(p.longitude).toFixed(7);
  $('campoPrecisao').value=Number.isFinite(p.accuracy_m)?p.accuracy_m.toFixed(1):'';
  $('campoAltitude').value=Number.isFinite(p.altitude_m)?p.altitude_m.toFixed(1):'';
  $('campoPrecisaoVertical').value=Number.isFinite(p.altitude_accuracy_m)?p.altitude_accuracy_m.toFixed(1):'';
  $('campoUtm').value=utmText(p.utm);$('campoGpsFonte').value=p.source||'';$('campoGpsHora').value=p.captured_at_utc||'';
  const mun=await municipality(p.latitude,p.longitude);if(mun)$('campoMunicipio').value=mun;
  updateLocationUI();
  try{if(typeof itaSetGpsPosition==='function')itaSetGpsPosition(p.latitude,p.longitude,p.accuracy_m||20,{center:false})}catch(_){}
  try{if(typeof itaIdentifyGrids==='function')itaIdentifyGrids()}catch(_){}
}
function updateLocationUI(){
  const p=currentLocation();$('campoGpsQualidade').textContent=p?`${gpsClass(p.accuracy_m)}${Number.isFinite(p.accuracy_m)?` · ±${p.accuracy_m.toFixed(1)} m`:''}`:'GPS ainda não medido';
  $('campoUtmResumo').textContent=p?.utm?utmText(p.utm):'UTM —';$('campoMunicipioAuto').textContent=val('campoMunicipio')||'Município —';
  updateCameraPlate();updateCompleteness();scheduleDraft();
}
async function captureGps(){
  if(!navigator.geolocation){$('campoGpsStatus').textContent='Geolocalização indisponível.';return}
  $('campoGpsStatus').textContent='Capturando posição de alta precisão.';
  navigator.geolocation.getCurrentPosition(async pos=>{
    const c=pos.coords,p={latitude:c.latitude,longitude:c.longitude,accuracy_m:Number.isFinite(c.accuracy)?c.accuracy:null,altitude_m:Number.isFinite(c.altitude)?c.altitude:null,altitude_accuracy_m:Number.isFinite(c.altitudeAccuracy)?c.altitudeAccuracy:null,heading_deg:Number.isFinite(c.heading)?c.heading:null,speed_m_s:Number.isFinite(c.speed)?c.speed:null,source:'device_geolocation',captured_at_utc:new Date(pos.timestamp||Date.now()).toISOString()};
    await setLocation(p,{setOriginal:true});$('campoGpsStatus').textContent=`GPS original preservado · ${gpsClass(p.accuracy_m)}${p.accuracy_m?` · ±${p.accuracy_m.toFixed(1)} m`:''}.`;
  },e=>$('campoGpsStatus').textContent='GPS indisponível · '+(e.message||String(e)),{enableHighAccuracy:true,timeout:15000,maximumAge:0});
}
function editPosition(){
  $('campoLat').readOnly=$('campoLon').readOnly=false;$('campoGpsFonte').value='manual_edit';
  $('campoGpsStatus').textContent='Edição manual ativada. A posição GPS original continuará preservada separadamente.';
}
async function restoreGps(){if(S.gpsOriginal){$('campoLat').readOnly=$('campoLon').readOnly=true;await setLocation(S.gpsOriginal);$('campoGpsFonte').value='device_geolocation_restored'}}
function addStructure(data={}){
  S.structures.push({id:uuid(),type:data.type||'',description:data.description||'',confidence:data.confidence||'Média'});renderStructures();scheduleDraft();
}
function addMeasure(data={}){
  S.measures.push({id:uuid(),type:data.type||'',direction:data.direction??'',dip:data.dip??'',dip_direction:data.dip_direction??'',strike:data.strike??'',method:data.method||'',instrument:data.instrument||'',precision:data.precision||'',time:data.time||localDateParts().time});renderMeasures();scheduleDraft();
}
async function addSample(data={}){
  const n=S.samples.length+1,code=data.local_code||`${val('campoStationCode')||'ITA-MS'}-A${String(n).padStart(2,'0')}`;
  S.samples.push({id:uuid(),local_code:code,type:data.type||'',depth:data.depth??'',weight:data.weight??'',description:data.description||'',destination:data.destination||'',analysis:data.analysis||'',responsible:data.responsible||val('campoObservador'),igsn_status:data.igsn_status||'nao_registrado',igsn_id:data.igsn_id||''});renderSamples();scheduleDraft();
}
function renderStructures(){
  $('campoEstruturasLista').innerHTML=S.structures.length?S.structures.map((x,i)=>`<div class="ita-array-card" data-struct="${x.id}"><div class="ita-array-card-head"><b>Estrutura ${i+1}</b><button type="button" class="ita-mini-danger" data-rm-struct="${x.id}">Remover</button></div><div class="field-grid three"><label><span class="field-label">Tipo</span><select class="field-select" data-k="type">${STRUCT_TYPES.map(v=>`<option ${v===x.type?'selected':''}>${esc(v)}</option>`).join('')}</select></label><label><span class="field-label">Confiança</span><select class="field-select" data-k="confidence">${['Alta','Média','Baixa'].map(v=>`<option ${v===x.confidence?'selected':''}>${v}</option>`).join('')}</select></label><label class="field-full"><span class="field-label">Descrição</span><input class="field-input" data-k="description" value="${esc(x.description)}"></label></div></div>`).join(''):'<div class="empty">Nenhuma estrutura estruturada.</div>';
  qa('[data-struct]').forEach(c=>qa('[data-k]',c).forEach(e=>e.addEventListener('change',()=>{const x=S.structures.find(v=>v.id===c.dataset.struct);if(x){x[e.dataset.k]=e.value;scheduleDraft()}})));
  qa('[data-rm-struct]').forEach(b=>b.onclick=()=>{S.structures=S.structures.filter(x=>x.id!==b.dataset.rmStruct);renderStructures();scheduleDraft()});
}
function renderMeasures(){
  $('campoMedidasLista').innerHTML=S.measures.length?S.measures.map((x,i)=>`<div class="ita-array-card" data-measure="${x.id}"><div class="ita-array-card-head"><b>Medida ${i+1}</b><button type="button" class="ita-mini-danger" data-rm-measure="${x.id}">Remover</button></div><div class="field-grid three"><label><span class="field-label">Tipo</span><select class="field-select" data-k="type">${MEASURE_TYPES.map(v=>`<option ${v===x.type?'selected':''}>${esc(v)}</option>`).join('')}</select></label><label><span class="field-label">Direção / azimute</span><input class="field-input" type="number" min="0" max="360" data-k="direction" value="${esc(x.direction)}"></label><label><span class="field-label">Mergulho</span><input class="field-input" type="number" min="0" max="90" data-k="dip" value="${esc(x.dip)}"></label><label><span class="field-label">Sentido do mergulho</span><input class="field-input" type="number" min="0" max="360" data-k="dip_direction" value="${esc(x.dip_direction)}"></label><label><span class="field-label">Rumo</span><input class="field-input" type="number" min="0" max="360" data-k="strike" value="${esc(x.strike)}"></label><label><span class="field-label">Hora</span><input class="field-input" type="time" data-k="time" value="${esc(x.time)}"></label><label><span class="field-label">Método</span><input class="field-input" data-k="method" value="${esc(x.method)}"></label><label><span class="field-label">Instrumento</span><input class="field-input" data-k="instrument" value="${esc(x.instrument)}"></label><label><span class="field-label">Precisão estimada</span><input class="field-input" data-k="precision" value="${esc(x.precision)}"></label></div></div>`).join(''):'<div class="empty">Nenhuma medida registrada.</div>';
  qa('[data-measure]').forEach(c=>qa('[data-k]',c).forEach(e=>e.addEventListener('change',()=>{const x=S.measures.find(v=>v.id===c.dataset.measure);if(x){x[e.dataset.k]=e.value;scheduleDraft()}})));
  qa('[data-rm-measure]').forEach(b=>b.onclick=()=>{S.measures=S.measures.filter(x=>x.id!==b.dataset.rmMeasure);renderMeasures();scheduleDraft()});
}
function renderSamples(){
  $('campoAmostrasLista').innerHTML=S.samples.length?S.samples.map((x,i)=>`<div class="ita-array-card" data-sample="${x.id}"><div class="ita-array-card-head"><b>${esc(x.local_code)}</b><button type="button" class="ita-mini-danger" data-rm-sample="${x.id}">Remover</button></div><div class="field-grid three"><label><span class="field-label">Código local</span><input class="field-input" data-k="local_code" value="${esc(x.local_code)}"></label><label><span class="field-label">Tipo</span><select class="field-select" data-k="type"><option value="">Selecionar</option>${SAMPLE_TYPES.map(v=>`<option ${v===x.type?'selected':''}>${esc(v)}</option>`).join('')}</select></label><label><span class="field-label">Profundidade m</span><input class="field-input" type="number" step="any" data-k="depth" value="${esc(x.depth)}"></label><label><span class="field-label">Peso aproximado g</span><input class="field-input" type="number" step="any" data-k="weight" value="${esc(x.weight)}"></label><label><span class="field-label">Destino</span><input class="field-input" data-k="destination" value="${esc(x.destination)}"></label><label><span class="field-label">Análise prevista</span><input class="field-input" data-k="analysis" value="${esc(x.analysis)}"></label><label><span class="field-label">Responsável</span><input class="field-input" data-k="responsible" value="${esc(x.responsible)}"></label><label><span class="field-label">Estado IGSN</span><select class="field-select" data-k="igsn_status"><option value="nao_registrado" ${x.igsn_status==='nao_registrado'?'selected':''}>Não registrado</option><option value="solicitado" ${x.igsn_status==='solicitado'?'selected':''}>Solicitado</option><option value="registrado" ${x.igsn_status==='registrado'?'selected':''}>Registrado</option></select></label><label><span class="field-label">IGSN real</span><input class="field-input" data-k="igsn_id" value="${esc(x.igsn_id)}"></label><label class="field-full"><span class="field-label">Descrição</span><textarea class="field-textarea" data-k="description">${esc(x.description)}</textarea></label></div></div>`).join(''):'<div class="empty">Nenhuma amostra adicionada.</div>';
  qa('[data-sample]').forEach(c=>qa('[data-k]',c).forEach(e=>e.addEventListener('change',()=>{const x=S.samples.find(v=>v.id===c.dataset.sample);if(x){x[e.dataset.k]=e.value;scheduleDraft()}})));
  qa('[data-rm-sample]').forEach(b=>b.onclick=()=>{S.samples=S.samples.filter(x=>x.id!==b.dataset.rmSample);renderSamples();scheduleDraft()});
}
function renderArrays(){renderStructures();renderMeasures();renderSamples()}

function onOrientation(e){
  let bearing=null,absolute=!!e.absolute,source='relative';
  if(Number.isFinite(e.webkitCompassHeading)){bearing=normalizeHeading(e.webkitCompassHeading);absolute=true;source='webkitCompassHeading'}
  else if(Number.isFinite(e.alpha)){bearing=normalizeHeading(360-e.alpha);source=absolute?'absolute':'relative'}
  S.orientation={bearing_deg:bearing,absolute,source,alpha:Number.isFinite(e.alpha)?e.alpha:null,beta:Number.isFinite(e.beta)?e.beta:null,gamma:Number.isFinite(e.gamma)?e.gamma:null,captured_at_utc:iso()};
  $('campoHeading').value=Number.isFinite(bearing)?`${bearing.toFixed(0)}°${absolute?'':' rel.'}`:'';
  $('campoPitch').value=Number.isFinite(S.orientation.beta)?`${S.orientation.beta.toFixed(1)}°`:'';
  $('campoRoll').value=Number.isFinite(S.orientation.gamma)?`${S.orientation.gamma.toFixed(1)}°`:'';
  updateCameraPlate();
}
async function startSensors(){
  try{
    if(typeof DeviceOrientationEvent==='undefined')throw new Error('Orientação não disponível');
    if(typeof DeviceOrientationEvent.requestPermission==='function'){
      const p=await DeviceOrientationEvent.requestPermission(true);if(p!=='granted')throw new Error('Permissão não concedida')
    }
    window.addEventListener('deviceorientationabsolute',onOrientation,true);window.addEventListener('deviceorientation',onOrientation,true);
    $('campoStatus').textContent='Bússola auxiliar ativada.';
  }catch(e){$('campoStatus').textContent='Bússola indisponível · '+e.message}
}
async function startCamera(){
  try{
    stopCamera();
    if(window.ITA_CAMERA_CORE){
      S.stream=await window.ITA_CAMERA_CORE.open({facingMode:'environment'});
    }else{
      if(!window.isSecureContext)throw new Error('A câmera requer HTTPS');
      S.stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
    }
    $('campoCameraVideo').srcObject=S.stream;
    await $('campoCameraVideo').play();
    updateCameraPlate();
    $('campoStatus').textContent='Câmera ativa.';
  }catch(e){
    const msg=window.ITA_CAMERA_CORE?.describeError?.(e)||e.message;
    $('campoStatus').textContent='Câmera indisponível · '+msg;
  }
}
function stopCamera(){if(S.stream){S.stream.getTracks().forEach(t=>t.stop());S.stream=null}if($('campoCameraVideo'))$('campoCameraVideo').srcObject=null}
function updateCameraPlate(){
  const p=currentLocation(),o=S.orientation,st=val('campoStationCode')||'estação';
  $('campoCameraPlate').innerHTML=`<strong>ITA ARANDU MS · ${esc(st)}</strong><span>${esc(p?.utm?utmText(p.utm):'UTM —')} · ${p?.accuracy_m?`±${p.accuracy_m.toFixed(0)} m`:'precisão —'} · rumo ${Number.isFinite(o?.bearing_deg)?o.bearing_deg.toFixed(0)+'°':'—'}</span>`;
}
async function captureVideoBlob(){
  const v=$('campoCameraVideo');if(!v?.srcObject||!v.videoWidth)throw new Error('Ative a câmera');
  const scale=Math.min(1,1920/Math.max(v.videoWidth,v.videoHeight)),c=document.createElement('canvas');
  c.width=Math.round(v.videoWidth*scale);c.height=Math.round(v.videoHeight*scale);c.getContext('2d').drawImage(v,0,0,c.width,c.height);
  return await canvasBlob(c,'image/jpeg',.9);
}
async function overlayPhoto(blob,meta){
  const img=await imageFromBlob(blob),c=document.createElement('canvas');c.width=img.width;c.height=img.height;
  const x=c.getContext('2d');x.drawImage(img,0,0);const band=Math.max(115,Math.round(c.height*.18)),fs=Math.max(18,Math.round(c.width/50));
  x.fillStyle='rgba(4,22,32,.86)';x.fillRect(0,c.height-band,c.width,band);x.fillStyle='#fff';x.font=`700 ${fs}px system-ui`;
  x.fillText(`ITA ARANDU MS · ${meta.station_code}`,fs*.7,c.height-band+fs*1.25);x.font=`500 ${Math.round(fs*.76)}px system-ui`;
  x.fillText(meta.location?.utm?utmText(meta.location.utm):'UTM —',fs*.7,c.height-band+fs*2.4);
  x.fillText(`GPS ${meta.location?.accuracy_m?`±${meta.location.accuracy_m.toFixed(0)} m`:'—'} · rumo ${Number.isFinite(meta.orientation?.bearing_deg)?meta.orientation.bearing_deg.toFixed(0)+'°':'—'} · ${new Date().toLocaleString()}`,fs*.7,c.height-band+fs*3.45);
  return await canvasBlob(c,'image/jpeg',.9);
}
async function capturePhoto(){
  try{
    const original=await captureVideoBlob(),loc=currentLocation(),meta={station_code:val('campoStationCode'),location:loc,orientation:S.orientation?{...S.orientation}:null,captured_at_utc:iso(),origin:'web_camera'};
    const photo={id:uuid(),name:`${meta.station_code}_F${String(S.photos.length+1).padStart(2,'0')}.jpg`,source:'web_camera',classification:'vista geral',description:'',original_blob:original,original_sha256:await shaBlob(original),overlay_blob:null,overlay_sha256:null,georeference_status:loc?'station_simultaneous':'without_position',metadata:meta};
    if($('campoOverlay').checked){photo.overlay_blob=await overlayPhoto(original,meta);photo.overlay_sha256=await shaBlob(photo.overlay_blob)}
    S.photos.push(photo);renderPhotos();scheduleDraft(100);$('campoStatus').textContent='Foto capturada com original preservado, SHA256 e rascunho local persistente.';
  }catch(e){$('campoStatus').textContent='Falha na foto · '+e.message}
}
async function exifGps(file){
  try{
    const buf=await file.arrayBuffer(),dv=new DataView(buf);if(dv.byteLength<4||dv.getUint16(0,false)!==0xFFD8)return null;
    const ascii=(o,n)=>{let s='';for(let i=0;i<n;i++){const c=dv.getUint8(o+i);if(!c)break;s+=String.fromCharCode(c)}return s};
    let off=2;
    while(off+4<dv.byteLength){
      if(dv.getUint8(off)!==0xFF){off++;continue}const marker=dv.getUint8(off+1);off+=2;if(marker===0xDA||marker===0xD9)break;
      const len=dv.getUint16(off,false);if(marker===0xE1&&ascii(off+2,6)==='Exif'){
        const t=off+8,little=dv.getUint16(t,false)===0x4949,u16=o=>dv.getUint16(o,little),u32=o=>dv.getUint32(o,little),first=t+u32(t+4);
        const entries=ifd=>{const m=new Map(),n=u16(ifd);for(let i=0;i<n;i++){const e=ifd+2+i*12,tag=u16(e),type=u16(e+2),count=u32(e+4),size=({1:1,2:1,3:2,4:4,5:8,7:1,9:4,10:8}[type]||1)*count,pos=size<=4?e+8:t+u32(e+8);m.set(tag,{type,count,pos})}return m};
        const value=(e,i=0)=>{if(!e)return null;const p=e.pos;if(e.type===2)return ascii(p,e.count);if(e.type===3)return u16(p+i*2);if(e.type===4)return u32(p+i*4);if(e.type===5){const q=p+i*8,d=u32(q+4);return d?u32(q)/d:null}return null};
        const ifd=entries(first),gp=value(ifd.get(0x8825));if(!Number.isFinite(gp))return null;const g=entries(t+gp),rat3=e=>[value(e,0),value(e,1),value(e,2)];
        const dms=(a,ref)=>{if(!a.every(Number.isFinite))return null;let x=a[0]+a[1]/60+a[2]/3600;if(ref==='S'||ref==='W')x=-x;return x};
        const lat=dms(rat3(g.get(2)),value(g.get(1))),lon=dms(rat3(g.get(4)),value(g.get(3))),ar=value(g.get(6)),altRef=value(g.get(5));
        return {latitude:lat,longitude:lon,altitude_m:Number.isFinite(ar)?(altRef===1?-ar:ar):null,image_direction_deg:value(g.get(17))};
      }off+=len;
    }
  }catch(_){}
  return null;
}
async function importPhotos(files){
  for(const file of files){
    const ex=await exifGps(file),station=currentLocation();let loc=null,status='not_georeferenced';
    if(Number.isFinite(ex?.latitude)&&Number.isFinite(ex?.longitude)){loc={latitude:ex.latitude,longitude:ex.longitude,altitude_m:ex.altitude_m,accuracy_m:null,utm:latLonToUTM(ex.latitude,ex.longitude),source:'embedded_exif'};status='embedded_exif_original'}
    else if($('campoAssociateGallery').checked&&station){loc={...station,source:'station_position_attributed_later',attributed_at_utc:iso()};status='attributed_later'}
    const p={id:uuid(),name:file.name,source:'gallery_import',classification:'detalhe',description:'',original_blob:file,original_sha256:await shaBlob(file),overlay_blob:null,overlay_sha256:null,georeference_status:status,metadata:{station_code:val('campoStationCode'),location:loc,orientation:null,captured_at_utc:null,origin:'gallery_import',exif:ex}};
    if($('campoOverlay').checked){try{p.overlay_blob=await overlayPhoto(file,p.metadata);p.overlay_sha256=await shaBlob(p.overlay_blob)}catch(_){}}
    S.photos.push(p);scheduleDraft(100);
  }renderPhotos();
}
function renderPhotos(){
  const box=$('campoFotoPreview');if(!box)return;box.innerHTML='';
  S.photos.forEach((p,i)=>{
    const d=document.createElement('article');d.className='ita-photo-card';const url=blobUrl(p.overlay_blob||p.original_blob);
    d.innerHTML=`<img src="${url}" alt="${esc(p.name)}"><b>${esc(p.name)}</b><small>${esc(p.source)} · ${esc(p.georeference_status)} · SHA ${esc((p.original_sha256||'').slice(0,10))}</small><select class="field-select">${PHOTO_TYPES.map(x=>`<option ${x===p.classification?'selected':''}>${x}</option>`).join('')}</select><input class="field-input" placeholder="Descrição da foto" value="${esc(p.description)}"><div class="ita-photo-card-actions"><button type="button" class="action-btn">Original</button><button type="button" class="ita-mini-danger">Remover</button></div>`;
    const [sel,desc]=[q('select',d),q('input',d)];sel.onchange=()=>p.classification=sel.value;desc.onchange=()=>p.description=desc.value;
    const [down,rm]=qa('button',d);down.onclick=()=>download(p.original_blob,p.name);rm.onclick=()=>{URL.revokeObjectURL(url);S.photos.splice(i,1);renderPhotos();scheduleDraft()};
    box.appendChild(d);
  });
  if(!S.photos.length)box.innerHTML='<div class="empty">Nenhuma fotografia.</div>';
}

function sketch(){
  const c=$('campoSketch'),ctx=c.getContext('2d');ctx.lineCap='round';ctx.lineJoin='round';
  function pos(e){const r=c.getBoundingClientRect(),p=e.touches?e.touches[0]:e;return{x:(p.clientX-r.left)*c.width/r.width,y:(p.clientY-r.top)*c.height/r.height}}
  function redraw(){ctx.clearRect(0,0,c.width,c.height);ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height);ctx.strokeStyle='#123f57';ctx.fillStyle='#123f57';ctx.lineWidth=3;ctx.font='28px system-ui';
    for(const a of S.sketch.actions){
      if(a.tool==='pen'){ctx.beginPath();a.points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.stroke()}
      if(a.tool==='arrow'){ctx.beginPath();ctx.moveTo(a.a.x,a.a.y);ctx.lineTo(a.b.x,a.b.y);ctx.stroke();const ang=Math.atan2(a.b.y-a.a.y,a.b.x-a.a.x),l=22;ctx.beginPath();ctx.moveTo(a.b.x,a.b.y);ctx.lineTo(a.b.x-l*Math.cos(ang-.5),a.b.y-l*Math.sin(ang-.5));ctx.moveTo(a.b.x,a.b.y);ctx.lineTo(a.b.x-l*Math.cos(ang+.5),a.b.y-l*Math.sin(ang+.5));ctx.stroke()}
      if(a.tool==='text')ctx.fillText(a.text,a.p.x,a.p.y);
    }}
  c.addEventListener('pointerdown',e=>{c.setPointerCapture(e.pointerId);const p=pos(e);S.sketch.drawing=true;S.sketch.start=p;S.sketch.last=p;if(S.sketch.tool==='pen')S.sketch.actions.push({tool:'pen',points:[p]})});
  c.addEventListener('pointermove',e=>{if(!S.sketch.drawing)return;const p=pos(e);if(S.sketch.tool==='pen'){S.sketch.actions.at(-1).points.push(p);redraw()}S.sketch.last=p});
  c.addEventListener('pointerup',e=>{if(!S.sketch.drawing)return;const p=pos(e);if(S.sketch.tool==='arrow')S.sketch.actions.push({tool:'arrow',a:S.sketch.start,b:p});if(S.sketch.tool==='text'){const text=prompt('Texto do croquis');if(text)S.sketch.actions.push({tool:'text',p,text})}S.sketch.drawing=false;redraw();scheduleDraft()});
  qa('[data-sketch-tool]').forEach(b=>b.onclick=()=>S.sketch.tool=b.dataset.sketchTool);
  $('campoSketchUndo').onclick=()=>{S.sketch.actions.pop();redraw();scheduleDraft()};$('campoSketchClear').onclick=()=>{if(confirm('Limpar o croquis?')){S.sketch.actions=[];redraw();scheduleDraft()}};redraw();S.sketch.redraw=redraw;
}
function clearSketch(){S.sketch.actions=[];if(S.sketch.redraw)S.sketch.redraw()}
async function sketchAttachment(){
  if(!S.sketch.actions.length)return null;const blob=await canvasBlob($('campoSketch'),'image/png');return {name:`${val('campoStationCode')}_CROQUIS.png`,blob,sha256:await shaBlob(blob),actions:structuredClone(S.sketch.actions)}
}

function completeness(){
  const checks=[
    ['identificação',!!val('campoStationCode')&&!!val('campoObservador')],
    ['posição',nval('campoLat')!=null&&nval('campoLon')!=null],
    ['exposição',!!val('campoExposicao')],
    ['litologia',!!val('campoLitologiaGrupo')&&!!val('campoLitologia')],
    ['observação',val('campoObservacao').length>=10],
    ['foto geral',S.photos.some(p=>p.classification==='vista geral')],
    ['qualidade GPS',nval('campoPrecisao')!=null],
    ['sensibilidade',!!val('campoSensibilidade')]
  ];
  return checks;
}
function updateCompleteness(){
  const c=completeness(),done=c.filter(x=>x[1]).length,pct=Math.round(done/c.length*100);
  $('campoCompletudeText').textContent=`${pct}% completa`;$('campoCompletudeBar').style.width=pct+'%';
  $('campoFinalCheck').innerHTML=c.map(x=>`<span class="ita-check-item ${x[1]?'ok':'warn'}">${x[1]?'✓':'○'} ${esc(x[0])}</span>`).join('');
  const missing=c.filter(x=>!x[1]).map(x=>x[0]);$('campoChecklist').textContent=missing.length?`Faltam ${missing.join(', ')}.`:'Checklist essencial completo.';
  return {pct,checks:c,missing};
}
function tags(){return [...checkedValues('campoTagsChips'),...val('campoTagsOutras').split(',').map(x=>x.trim()).filter(Boolean)]}
function sensitivePublicLocation(loc,sensitivity){
  if(!loc)return null;if(sensitivity!=='restrita')return {latitude:loc.latitude,longitude:loc.longitude,precision:'exact'};
  return {latitude:Math.round(loc.latitude*10)/10,longitude:Math.round(loc.longitude*10)/10,precision:'degraded_0.1_degree'};
}
async function buildRecord(){
  const comp=updateCompleteness(),loc=currentLocation(),sk=await sketchAttachment(),state=val('campoEstadoFicha');
  if(state==='validada'&&comp.pct<100)throw new Error('Uma ficha validada precisa completar o checklist essencial.');
  for(const s of S.samples){if(s.igsn_status==='registrado'&&!s.igsn_id)throw new Error(`Amostra ${s.local_code} marcada como IGSN registrado sem identificador.`)}
  return {
    id:S.editingId||uuid(),schema_version:'2.0',project:'ITA ARANDU MS',module:'Caderno de Campo Geocientífico Digital',station_code:val('campoStationCode'),created_at:S.editingId?(S.records.find(r=>r.id===S.editingId)?.created_at||iso()):iso(),updated_at:iso(),status:state,
    identity:{campaign:val('campoCampanha'),observer:val('campoObservador'),role:val('campoFuncao'),discipline:val('campoDisciplina'),local_name:val('campoLocalNome'),station_name:val('campoNome'),date:val('campoData'),local_time:val('campoHora'),utc:val('campoUtc'),timezone:Intl.DateTimeFormat().resolvedOptions().timeZone||null},
    relations:{spot_id:val('campoSpotId'),parent_station_code:val('campoParentSpot')||null,profile_id:val('campoPerfil')||null,profile_order:nval('campoPerfilOrdem'),tags:tags()},
    location:{current:loc,original_gps:S.gpsOriginal?{...S.gpsOriginal}:null,manual_edited:val('campoGpsFonte')==='manual_edit',municipality:val('campoMunicipio'),access:{type:val('campoAcessoTipo'),condition:val('campoAcessoCondicao'),reference:val('campoAcesso')},hex_250:val('campoHex250'),hex_500:val('campoHex500'),hex_1000:val('campoHex1000')},
    exposure:{type:val('campoExposicao'),quality:val('campoExposicaoQualidade')},
    lithology:{group:val('campoLitologiaGrupo'),name:val('campoLitologia'),facies:val('campoFacies'),description:val('campoLitologiaDescricao'),confidence:val('campoLitologiaConfianca')},
    mineralogy:{minerals:mineralValues(),others:val('campoMineraisOutros')},
    alteration:{presence:val('campoAlteracaoPresenca'),intensity:val('campoAlteracaoIntensidade'),types:checkedValues('campoAlteracaoTipos'),description:val('campoAlteracao')},
    structures:S.structures.map(x=>({...x})),measurements:S.measures.map(x=>({...x})),
    observation:{observed:val('campoObservacao'),interpretation:val('campoInterpretacao')},
    hydrogeology:{presence:val('campoHidroPresenca'),type:val('campoHidroTipo'),temperature_c:nval('campoHidroTemperatura'),ph:nval('campoHidroPh'),conductivity:nval('campoHidroCond'),instrument:val('campoHidroInstrumento'),note:val('campoHidro')},
    mineralization:{evidence:val('campoMineralizacaoPresenca'),style:val('campoMineralizacaoTipo'),width_m:nval('campoMineralizacaoLargura'),continuity:val('campoMineralizacaoContinuidade'),host_rock:val('campoMineralizacaoHospedeira'),associated_alteration:val('campoMineralizacaoAlteracao'),description:val('campoMineralizacao')},
    geotechnics:{evaluated:val('campoGeotecniaAvaliada')==='Sim',weathering:val('campoGeotecniaIntemperismo'),stability:val('campoGeotecniaEstabilidade'),processes:checkedValues('campoGeotecniaProcessos'),note:val('campoGeotecnia')},
    samples:S.samples.map(x=>({...x})),
    photos:S.photos.map(p=>({...p})),
    sketch:sk,
    sensors:{device_orientation:S.orientation?{...S.orientation}:null,note:'Orientação do dispositivo é auxiliar e não constitui medida estrutural automaticamente.'},
    quality:{general_confidence:val('campoConfianca'),sensitivity:val('campoSensibilidade'),restriction_reason:val('campoSensibilidadeMotivo'),geoethics:{origin:val('campoGeoOrigem'),access_level:val('campoGeoNivelAcesso'),authorization_status:val('campoGeoConsentimento'),authority:val('campoGeoAutoridade'),authorized_purpose:val('campoGeoFinalidade'),authorization_date:val('campoGeoAutorizacaoData'),reuse_conditions:val('campoGeoReutilizacao'),review_withdrawal_channel:val('campoGeoRetirada'),frameworks:['ITA-GEOETHICS-1.0','CARE']},completeness_percent:comp.pct,checklist:comp.checks.map(([name,ok])=>({name,ok})),review:{reviewer:val('campoRevisor'),comment:val('campoRevisaoComentario'),state}},
    provenance:{coordinate_policy:'original GPS preserved separately from manual edits',photo_policy:'original file preserved; imported EXIF distinguished from later attribution',hash_algorithm:'SHA-256'}
  };
}
async function save(){
  try{$('campoStatus').textContent='Validando e salvando estação.';const rec=await buildRecord();await put(rec);await deleteDraft();$('campoStatus').textContent=`${rec.station_code} salva · ${rec.samples.length} amostra(s) · ${rec.photos.length} foto(s).`;autosaveStatus('Estação salva no IndexedDB · rascunho limpo.','ok');await renderRecords();await newStation({clearDraft:false})}
  catch(e){$('campoStatus').textContent='Não foi possível salvar · '+storageFailureMessage(e);autosaveStatus('Salvamento interrompido · '+storageFailureMessage(e),'error')}
}
function cleanBlobFields(rec){
  const clone=structuredClone(rec);
  clone.photos=(clone.photos||[]).map(p=>{delete p.original_blob;delete p.overlay_blob;return p});
  if(clone.sketch)delete clone.sketch.blob;return clone;
}
async function renderRecords(){
  S.records=(await getAll()).sort((a,b)=>String(b.updated_at).localeCompare(String(a.updated_at)));await refreshParentOptions();
  const term=val('campoBuscaRegistros').toLowerCase(),filter=val('campoFiltroEstado');
  const rows=S.records.filter(r=>{
    if(filter&&r.status!==filter)return false;
    if(!term)return true;
    const hay=[r.station_code,r.identity?.station_name,r.identity?.local_name,r.lithology?.name,...(r.samples||[]).map(s=>s.local_code)].join(' ').toLowerCase();return hay.includes(term);
  });
  $('campoRegistros').innerHTML=rows.length?rows.map(r=>`<div class="ita-record-master" data-rec="${r.id}"><div><b>${esc(r.station_code)} · ${esc(r.identity?.station_name||r.identity?.local_name||'estação')}</b><small>${esc(r.status)} · ${esc(r.identity?.campaign||'sem campanha')} · ${esc(r.lithology?.name||'litologia não informada')} · ${r.photos?.length||0} foto(s) · ${r.samples?.length||0} amostra(s) · ${r.quality?.completeness_percent||0}%</small></div><div class="ita-record-actions"><button class="action-btn" data-edit="${r.id}">Editar</button><button class="action-btn" data-dup="${r.id}">Duplicar</button><button class="ita-mini-danger" data-del="${r.id}">Excluir</button></div></div>`).join(''):'<div class="empty">Nenhuma estação encontrada.</div>';
  qa('[data-del]').forEach(b=>b.onclick=async()=>{if(confirm('Excluir esta estação local?')){await del(b.dataset.del);await renderRecords()}});
  qa('[data-edit]').forEach(b=>b.onclick=()=>loadRecord(S.records.find(r=>r.id===b.dataset.edit)));
  qa('[data-dup]').forEach(b=>b.onclick=()=>duplicateRecord(S.records.find(r=>r.id===b.dataset.dup)));
}
async function duplicateRecord(r){if(!r)return;await loadRecord(r);S.editingId=null;$('campoStationCode').value=await nextStationCode();$('campoSpotId').value=`ITA-SPOT-${Date.now().toString(36).toUpperCase()}`;$('campoEstadoFicha').value='rascunho';updateCompleteness();scheduleDraft(100)}
async function loadRecord(r){
  if(!r)return;S.editingId=r.id;S.gpsOriginal=r.location?.original_gps||null;S.gpsCurrent=r.location?.current||null;S.structures=structuredClone(r.structures||[]);S.measures=structuredClone(r.measurements||[]);S.samples=structuredClone(r.samples||[]);S.photos=structuredClone(r.photos||[]);
  const set=(id,v)=>{if($(id))$(id).value=v??''};
  set('campoStationCode',r.station_code);set('campoSpotId',r.relations?.spot_id);set('campoCampanha',r.identity?.campaign);set('campoObservador',r.identity?.observer);set('campoFuncao',r.identity?.role);set('campoDisciplina',r.identity?.discipline);set('campoLocalNome',r.identity?.local_name);set('campoNome',r.identity?.station_name);set('campoData',r.identity?.date);set('campoHora',r.identity?.local_time);set('campoUtc',r.identity?.utc);
  set('campoParentSpot',r.relations?.parent_station_code);set('campoPerfil',r.relations?.profile_id);set('campoPerfilOrdem',r.relations?.profile_order);
  qa('#campoTagsChips input').forEach(x=>x.checked=(r.relations?.tags||[]).includes(x.value));set('campoTagsOutras',(r.relations?.tags||[]).filter(x=>!TAGS.includes(x)).join(', '));
  if(r.location?.current)await setLocation(r.location.current);set('campoMunicipio',r.location?.municipality);set('campoAcessoTipo',r.location?.access?.type);set('campoAcessoCondicao',r.location?.access?.condition);set('campoAcesso',r.location?.access?.reference);set('campoHex250',r.location?.hex_250);set('campoHex500',r.location?.hex_500);set('campoHex1000',r.location?.hex_1000);
  set('campoExposicao',r.exposure?.type);set('campoExposicaoQualidade',r.exposure?.quality);set('campoLitologiaGrupo',r.lithology?.group);$('campoLitologiaGrupo').dispatchEvent(new Event('change'));set('campoLitologia',r.lithology?.name);set('campoFacies',r.lithology?.facies);set('campoLitologiaDescricao',r.lithology?.description);set('campoLitologiaConfianca',r.lithology?.confidence);
  qa('.ita-mineral-item').forEach(l=>{const m=(r.mineralogy?.minerals||[]).find(x=>x.name===q('input',l).value);q('input',l).checked=!!m;q('select',l).disabled=!m;if(m)q('select',l).value=m.abundance});set('campoMineraisOutros',r.mineralogy?.others);
  set('campoAlteracaoPresenca',r.alteration?.presence);set('campoAlteracaoIntensidade',r.alteration?.intensity);qa('#campoAlteracaoTipos input').forEach(x=>x.checked=(r.alteration?.types||[]).includes(x.value));set('campoAlteracao',r.alteration?.description);
  set('campoObservacao',r.observation?.observed);set('campoInterpretacao',r.observation?.interpretation);
  set('campoHidroPresenca',r.hydrogeology?.presence);set('campoHidroTipo',r.hydrogeology?.type);set('campoHidroTemperatura',r.hydrogeology?.temperature_c);set('campoHidroPh',r.hydrogeology?.ph);set('campoHidroCond',r.hydrogeology?.conductivity);set('campoHidroInstrumento',r.hydrogeology?.instrument);set('campoHidro',r.hydrogeology?.note);
  set('campoMineralizacaoPresenca',r.mineralization?.evidence);set('campoMineralizacaoTipo',r.mineralization?.style);set('campoMineralizacaoLargura',r.mineralization?.width_m);set('campoMineralizacaoContinuidade',r.mineralization?.continuity);set('campoMineralizacaoHospedeira',r.mineralization?.host_rock);set('campoMineralizacaoAlteracao',r.mineralization?.associated_alteration);set('campoMineralizacao',r.mineralization?.description);
  set('campoGeotecniaAvaliada',r.geotechnics?.evaluated?'Sim':'Não');set('campoGeotecniaIntemperismo',r.geotechnics?.weathering);set('campoGeotecniaEstabilidade',r.geotechnics?.stability);qa('#campoGeotecniaProcessos input').forEach(x=>x.checked=(r.geotechnics?.processes||[]).includes(x.value));set('campoGeotecnia',r.geotechnics?.note);
  set('campoConfianca',r.quality?.general_confidence);set('campoSensibilidade',r.quality?.sensitivity);set('campoSensibilidadeMotivo',r.quality?.restriction_reason);set('campoGeoOrigem',r.quality?.geoethics?.origin);set('campoGeoNivelAcesso',r.quality?.geoethics?.access_level);set('campoGeoConsentimento',r.quality?.geoethics?.authorization_status);set('campoGeoAutoridade',r.quality?.geoethics?.authority);set('campoGeoFinalidade',r.quality?.geoethics?.authorized_purpose);set('campoGeoAutorizacaoData',r.quality?.geoethics?.authorization_date);set('campoGeoReutilizacao',r.quality?.geoethics?.reuse_conditions);set('campoGeoRetirada',r.quality?.geoethics?.review_withdrawal_channel);set('campoRevisor',r.quality?.review?.reviewer);set('campoRevisaoComentario',r.quality?.review?.comment);set('campoEstadoFicha',r.status);set('campoEstadoResumo',r.status);
  if(r.sketch?.actions){S.sketch.actions=structuredClone(r.sketch.actions);S.sketch.redraw?.()}
  renderArrays();renderPhotos();updateCompleteness();$('campoForm').scrollIntoView({behavior:'smooth',block:'start'});scheduleDraft(100);
}
function geojson(rows,publicMode=false){
  return {type:'FeatureCollection',name:'ITA_ARANDU_CAMPO',features:rows.filter(r=>r.location?.current).map(r=>{
    const sensitivity=r.quality?.sensitivity,loc=publicMode?sensitivePublicLocation(r.location.current,sensitivity):r.location.current;
    return {type:'Feature',geometry:loc?{type:'Point',coordinates:[loc.longitude,loc.latitude]}:null,properties:{station_code:r.station_code,status:r.status,local:r.identity?.local_name,station:r.identity?.station_name,campaign:r.identity?.campaign,date:r.identity?.date,municipality:r.location?.municipality,lithology:r.lithology?.name,lithology_group:r.lithology?.group,observation:r.observation?.observed,interpretation:r.observation?.interpretation,samples:(r.samples||[]).map(s=>s.local_code).join('|'),photos:(r.photos||[]).length,sensitivity,coordinate_precision:loc?.precision||'exact'}};
  })};
}
function kml(rows,publicMode=false){
  const xe=s=>String(s??'').replace(/[<>&'"]/g,m=>({'<':'&lt;','>':'&gt;','&':'&amp;',"'":'&apos;','"':'&quot;'}[m]));
  const marks=rows.filter(r=>r.location?.current).map(r=>{const loc=publicMode?sensitivePublicLocation(r.location.current,r.quality?.sensitivity):r.location.current;if(!loc)return'';return `<Placemark><name>${xe(r.station_code)}</name><description>${xe(`${r.identity?.station_name||''}\n${r.lithology?.name||''}\n${r.observation?.observed||''}`)}</description><Point><coordinates>${loc.longitude},${loc.latitude},${r.location.current.altitude_m||0}</coordinates></Point></Placemark>`}).join('');
  return `<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>ITA ARANDU Campo</name>${marks}</Document></kml>`;
}
async function exportJson(){const rows=await getAll(),clean=rows.map(cleanBlobFields);download(new Blob([JSON.stringify({schema_version:'2.0',project:'ITA ARANDU MS',exported_at:iso(),records:clean},null,2)],{type:'application/json'}),`ITA_ARANDU_CAMPO_${localDateParts().date}.json`)}
async function exportGeo(){const rows=await getAll();download(new Blob([JSON.stringify(geojson(rows,false),null,2)],{type:'application/geo+json'}),`ITA_ARANDU_CAMPO_${localDateParts().date}.geojson`)}
async function exportKml(){const rows=await getAll();download(new Blob([kml(rows,false)],{type:'application/vnd.google-earth.kml+xml'}),`ITA_ARANDU_CAMPO_${localDateParts().date}.kml`)}

/* Minimal uncompressed ZIP writer for complete local package */
function crc32(bytes){
  let c=0xffffffff;for(const b of bytes){c^=b;for(let k=0;k<8;k++)c=(c>>>1)^((c&1)?0xedb88320:0)}return (c^0xffffffff)>>>0;
}
function u16(n){return new Uint8Array([n&255,(n>>>8)&255])}
function u32(n){return new Uint8Array([n&255,(n>>>8)&255,(n>>>16)&255,(n>>>24)&255])}
function concat(parts){const n=parts.reduce((a,b)=>a+b.length,0),o=new Uint8Array(n);let p=0;for(const b of parts){o.set(b,p);p+=b.length}return o}
async function makeZip(files){
  const te=new TextEncoder(),locals=[],centrals=[];let offset=0;
  for(const f of files){
    const name=te.encode(f.name),data=new Uint8Array(await f.blob.arrayBuffer()),crc=crc32(data);
    const local=concat([u32(0x04034b50),u16(20),u16(0),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),name,data]);
    locals.push(local);
    const central=concat([u32(0x02014b50),u16(20),u16(20),u16(0),u16(0),u16(0),u16(0),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),u16(0),u16(0),u16(0),u32(0),u32(offset),name]);
    centrals.push(central);offset+=local.length;
  }
  const cd=concat(centrals),body=concat(locals),end=concat([u32(0x06054b50),u16(0),u16(0),u16(files.length),u16(files.length),u32(cd.length),u32(body.length),u16(0)]);
  return new Blob([body,cd,end],{type:'application/zip'});
}
async function exportPackage(){
  const rows=await getAll(),clean=rows.map(cleanBlobFields),files=[];
  files.push({name:'manifest.json',blob:new Blob([JSON.stringify({project:'ITA ARANDU MS',schema_version:'2.0',exported_at:iso(),records:clean},null,2)],{type:'application/json'})});
  files.push({name:'stations.geojson',blob:new Blob([JSON.stringify(geojson(rows,false),null,2)],{type:'application/geo+json'})});
  files.push({name:'stations.kml',blob:new Blob([kml(rows,false)],{type:'application/vnd.google-earth.kml+xml'})});
  for(const r of rows){
    for(const p of r.photos||[]){
      if(p.original_blob)files.push({name:`photos/${r.station_code}/original/${p.name}`,blob:p.original_blob});
      if(p.overlay_blob)files.push({name:`photos/${r.station_code}/overlay/${p.name.replace(/\.(jpe?g|png)$/i,'_PLACA.jpg')}`,blob:p.overlay_blob});
    }
    if(r.sketch?.blob)files.push({name:`sketches/${r.station_code}_CROQUIS.png`,blob:r.sketch.blob});
  }
  $('campoStatus').textContent=`Gerando pacote ZIP com ${files.length} arquivo(s).`;
  download(await makeZip(files),`ITA_ARANDU_CAMPO_PACOTE_${localDateParts().date}.zip`);
}
async function wire(){
  renderPickers();setupLithology();loadProfiles();mode(localStorage.getItem(MODE_KEY)||'essential');sketch();
  await migrateLegacyOnce();
  $('campoModoEssencial').onclick=()=>{mode('essential');scheduleDraft()};$('campoModoAvancado').onclick=()=>{mode('advanced');scheduleDraft()};$('campoSalvarPerfil').onclick=saveProfiles;
  $('campoGps').onclick=captureGps;$('campoEditarPosicao').onclick=editPosition;$('campoRestaurarGps').onclick=restoreGps;
  $('campoCentroMapa').onclick=async()=>{try{const c=leafletMap.getCenter();await setLocation({latitude:c.lat,longitude:c.lng,accuracy_m:null,altitude_m:null,altitude_accuracy_m:null,source:'map_center',captured_at_utc:iso()})}catch(e){$('campoStatus').textContent='Centro do mapa indisponível'}};
  $('campoAddEstrutura').onclick=()=>addStructure();$('campoAddMedida').onclick=()=>addMeasure();$('campoAddAmostra').onclick=()=>addSample();
  $('campoCameraStart').onclick=startCamera;$('campoCameraCapture').onclick=capturePhoto;$('campoCameraStop').onclick=stopCamera;$('campoSensorStart').onclick=startSensors;$('campoFotos').onchange=async e=>{await importPhotos([...e.target.files]);e.target.value='';scheduleDraft(100)};
  $('campoSalvar').onclick=save;$('campoNovo').onclick=()=>newStation({clearDraft:true,confirmDiscard:true});$('campoNovaEstacao').onclick=()=>newStation({clearDraft:true,confirmDiscard:true});$('campoExportar').onclick=exportJson;$('campoExportarGeoJSON').onclick=exportGeo;$('campoExportarKML').onclick=exportKml;$('campoExportarPacote').onclick=exportPackage;
  $('campoBuscaRegistros').oninput=renderRecords;$('campoFiltroEstado').onchange=renderRecords;$('campoEstadoFicha').onchange=()=>{$('campoEstadoResumo').value=val('campoEstadoFicha');updateCompleteness();scheduleDraft()};
  qa('#campoForm input,#campoForm select,#campoForm textarea').forEach(e=>{e.addEventListener('input',()=>{if(e.type!=='file')scheduleDraft()});e.addEventListener('change',()=>{if(['campoLat','campoLon'].includes(e.id)){const p=currentLocation();if(p)setLocation({...p,source:'manual_edit'})}updateCompleteness();scheduleDraft()})});
  qa('[data-close="campoModal"]').forEach(b=>b.addEventListener('click',()=>{stopCamera();saveDraft({silent:true})}));
  window.addEventListener('pagehide',()=>{stopCamera();saveDraft({silent:true})});document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveDraft({silent:true})});
  document.querySelectorAll('[data-modal="campoModal"]').forEach(b=>b.addEventListener('click',()=>setTimeout(()=>{renderRecords();updateCompleteness()},0)));
  const recovered=await restoreDraft();if(!recovered)await newStation({clearDraft:false});await renderRecords();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
window.ITA_CAMPO_MASTER={version:'2.1',release:'V38.4.59',state:S,getAll,getDraft,saveDraft,deleteDraft,newStation,renderRecords,latLonToUTM,geojson,kml};
})();
