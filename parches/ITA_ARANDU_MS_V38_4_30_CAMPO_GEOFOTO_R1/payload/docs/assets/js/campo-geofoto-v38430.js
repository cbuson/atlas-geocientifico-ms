(function(){
'use strict';

const ITA_GEOFOTO_VERSION='1.0';
const state={
  stream:null,
  gps:null,
  orientation:null,
  orientationListening:false,
  cameraPhotos:[],
  previewUrls:[],
  lastStationCode:null
};

const $=id=>document.getElementById(id);
const val=id=>$(id)?.value?.trim?.()||'';
const num=id=>{
  const v=Number(val(id));
  return Number.isFinite(v)?v:null;
};
const nowIso=()=>new Date().toISOString();
const pad=n=>String(n).padStart(2,'0');
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

function localStamp(d=new Date()){
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
function gpsQuality(acc){
  if(!Number.isFinite(acc))return 'sem precisão';
  if(acc<=5)return 'excelente';
  if(acc<=10)return 'boa';
  if(acc<=25)return 'moderada';
  return 'baixa';
}
function deg(v){
  return Number.isFinite(v)?((v%360)+360)%360:null;
}
function bearingLabel(o){
  if(!o)return '—';
  if(Number.isFinite(o.bearing_deg)){
    return `${o.bearing_deg.toFixed(0)}°${o.absolute?'':' rel.'}`;
  }
  return '—';
}
function haversine(lat1,lon1,lat2,lon2){
  const R=6371008.8,rad=Math.PI/180;
  const p1=lat1*rad,p2=lat2*rad,dp=(lat2-lat1)*rad,dl=(lon2-lon1)*rad;
  const a=Math.sin(dp/2)**2+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;
  return 2*R*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}

/* WGS84 latitude/longitude to UTM, dynamic zone */
function latLonToUTM(lat,lon){
  if(!Number.isFinite(lat)||!Number.isFinite(lon)||lat<-80||lat>84)return null;
  const a=6378137.0;
  const eccSquared=0.00669438;
  const k0=0.9996;
  const zone=Math.floor((lon+180)/6)+1;
  const longOrigin=(zone-1)*6-180+3;
  const eccPrimeSquared=eccSquared/(1-eccSquared);
  const latRad=lat*Math.PI/180;
  const longRad=lon*Math.PI/180;
  const longOriginRad=longOrigin*Math.PI/180;
  const N=a/Math.sqrt(1-eccSquared*Math.sin(latRad)**2);
  const T=Math.tan(latRad)**2;
  const C=eccPrimeSquared*Math.cos(latRad)**2;
  const A=Math.cos(latRad)*(longRad-longOriginRad);
  const M=a*((1-eccSquared/4-3*eccSquared**2/64-5*eccSquared**3/256)*latRad
    -(3*eccSquared/8+3*eccSquared**2/32+45*eccSquared**3/1024)*Math.sin(2*latRad)
    +(15*eccSquared**2/256+45*eccSquared**3/1024)*Math.sin(4*latRad)
    -(35*eccSquared**3/3072)*Math.sin(6*latRad));
  let easting=k0*N*(A+(1-T+C)*A**3/6+(5-18*T+T**2+72*C-58*eccPrimeSquared)*A**5/120)+500000;
  let northing=k0*(M+N*Math.tan(latRad)*(A**2/2+(5-T+9*C+4*C**2)*A**4/24+(61-58*T+T**2+600*C-330*eccPrimeSquared)*A**6/720));
  const hemisphere=lat<0?'S':'N';
  if(lat<0)northing+=10000000;
  const epsg=(lat<0?32700:32600)+zone;
  return {zone,hemisphere,epsg,easting,northing};
}
function utmText(u){
  return u?`${u.zone}${u.hemisphere} · ${Math.round(u.easting)} E · ${Math.round(u.northing)} N · EPSG:${u.epsg}`:'—';
}

async function sha256Blob(blob){
  if(!blob?.arrayBuffer||!crypto?.subtle)return null;
  const buf=await blob.arrayBuffer();
  const h=await crypto.subtle.digest('SHA-256',buf);
  return [...new Uint8Array(h)].map(x=>x.toString(16).padStart(2,'0')).join('');
}
function downloadBlob(blob,name){
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;
  a.download=name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1500);
}
function canvasBlob(canvas,type='image/jpeg',quality=.9){
  return new Promise((resolve,reject)=>{
    canvas.toBlob(b=>b?resolve(b):reject(new Error('Não foi possível gerar a imagem.')),type,quality);
  });
}
async function imageFromBlob(blob){
  if('createImageBitmap' in window){
    try{return await createImageBitmap(blob)}catch(_){}
  }
  return await new Promise((resolve,reject)=>{
    const img=new Image();
    const url=URL.createObjectURL(blob);
    img.onload=()=>{URL.revokeObjectURL(url);resolve(img)};
    img.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('Imagem inválida'))};
    img.src=url;
  });
}
function fitCanvasSize(w,h,maxSide=1920){
  const s=Math.min(1,maxSide/Math.max(w,h));
  return {w:Math.max(1,Math.round(w*s)),h:Math.max(1,Math.round(h*s))};
}

function currentFormPosition(source='form'){
  const latitude=num('campoLat'),longitude=num('campoLon');
  if(latitude==null||longitude==null)return null;
  const utm=latLonToUTM(latitude,longitude);
  return {
    latitude,longitude,
    accuracy_m:num('campoPrecisao'),
    altitude_m:num('campoAltitude'),
    altitude_accuracy_m:num('campoAltitudeAccuracyV1'),
    heading_deg:null,
    speed_m_s:null,
    source,
    captured_at_utc:val('campoGpsTimestampV1')||null,
    utm
  };
}

function updateLocationUi(position){
  if(!position)return;
  state.gps=position;
  if(Number.isFinite(position.latitude))$('campoLat').value=position.latitude.toFixed(7);
  if(Number.isFinite(position.longitude))$('campoLon').value=position.longitude.toFixed(7);
  if(Number.isFinite(position.accuracy_m))$('campoPrecisao').value=position.accuracy_m.toFixed(1);
  if(Number.isFinite(position.altitude_m))$('campoAltitude').value=position.altitude_m.toFixed(1);
  if($('campoAltitudeAccuracyV1'))$('campoAltitudeAccuracyV1').value=Number.isFinite(position.altitude_accuracy_m)?position.altitude_accuracy_m.toFixed(1):'';
  if($('campoGpsSourceV1'))$('campoGpsSourceV1').value=position.source||'';
  if($('campoGpsTimestampV1'))$('campoGpsTimestampV1').value=position.captured_at_utc||'';
  if($('campoUtmV1'))$('campoUtmV1').value=utmText(position.utm);
  const q=$('campoGpsQualityV1');
  if(q)q.textContent=`${gpsQuality(position.accuracy_m)}${Number.isFinite(position.accuracy_m)?` · ±${position.accuracy_m.toFixed(1)} m`:''}`;
  try{
    if(typeof itaSetGpsPosition==='function'){
      itaSetGpsPosition(position.latitude,position.longitude,position.accuracy_m||20,{center:false});
    }
  }catch(_){}
  try{
    if(typeof itaIdentifyGrids==='function')itaIdentifyGrids();
  }catch(_){}
  updateLivePlate();
}

async function getFreshPosition(updateForm=true){
  if(!navigator.geolocation)throw new Error('Geolocalização não disponível neste navegador.');
  return await new Promise((resolve,reject)=>{
    navigator.geolocation.getCurrentPosition(pos=>{
      const c=pos.coords;
      const p={
        latitude:c.latitude,
        longitude:c.longitude,
        accuracy_m:Number.isFinite(c.accuracy)?c.accuracy:null,
        altitude_m:Number.isFinite(c.altitude)?c.altitude:null,
        altitude_accuracy_m:Number.isFinite(c.altitudeAccuracy)?c.altitudeAccuracy:null,
        heading_deg:Number.isFinite(c.heading)?deg(c.heading):null,
        speed_m_s:Number.isFinite(c.speed)?c.speed:null,
        source:'device_geolocation',
        captured_at_utc:new Date(pos.timestamp||Date.now()).toISOString(),
        utm:latLonToUTM(c.latitude,c.longitude)
      };
      if(updateForm)updateLocationUi(p);
      resolve(p);
    },reject,{enableHighAccuracy:true,timeout:15000,maximumAge:0});
  });
}

async function enhancedGps(){
  const s=$('campoGpsStatus');
  if(s)s.textContent='Solicitando posição de alta precisão ao dispositivo.';
  try{
    const p=await getFreshPosition(true);
    if(s)s.textContent=`Posição capturada · ${gpsQuality(p.accuracy_m)}${Number.isFinite(p.accuracy_m)?` · ±${p.accuracy_m.toFixed(1)} m`:''}. Confira antes de salvar.`;
  }catch(e){
    if(s)s.textContent='GPS não disponível · '+(e.message||String(e))+' · use coordenadas manuais ou o centro do mapa.';
  }
}

function onOrientation(e){
  let bearing=null,source='deviceorientation_relative',absolute=!!e.absolute,accuracy=null;
  if(Number.isFinite(e.webkitCompassHeading)){
    bearing=deg(e.webkitCompassHeading);
    source='webkit_compass_heading';
    absolute=true;
    accuracy=Number.isFinite(e.webkitCompassAccuracy)?e.webkitCompassAccuracy:null;
  }else if(Number.isFinite(e.alpha)){
    bearing=deg(360-e.alpha);
    source=absolute?'deviceorientation_absolute':'deviceorientation_relative';
  }
  state.orientation={
    bearing_deg:bearing,
    absolute,
    source,
    compass_accuracy_deg:accuracy,
    alpha_deg:Number.isFinite(e.alpha)?e.alpha:null,
    beta_deg:Number.isFinite(e.beta)?e.beta:null,
    gamma_deg:Number.isFinite(e.gamma)?e.gamma:null,
    captured_at_utc:nowIso()
  };
  renderSensorState();
  updateLivePlate();
}
async function requestOrientation(){
  const s=$('campoSensorStatusV1');
  try{
    if(typeof DeviceOrientationEvent==='undefined'){
      throw new Error('Orientação do dispositivo não disponível.');
    }
    if(typeof DeviceOrientationEvent.requestPermission==='function'){
      const p=await DeviceOrientationEvent.requestPermission(true);
      if(p!=='granted')throw new Error('Permissão de orientação não concedida.');
    }
    if(!state.orientationListening){
      window.addEventListener('deviceorientationabsolute',onOrientation,true);
      window.addEventListener('deviceorientation',onOrientation,true);
      state.orientationListening=true;
    }
    if(s)s.textContent='Bússola e orientação ativadas. O rumo só é tratado como absoluto quando o navegador assim o informa.';
  }catch(e){
    if(s)s.textContent=e.message||String(e);
  }
}
function renderSensorState(){
  const o=state.orientation;
  const heading=$('campoHeadingV1');
  if(heading)heading.value=bearingLabel(o);
  const pitch=$('campoPitchV1');
  if(pitch)pitch.value=o&&Number.isFinite(o.beta_deg)?`${o.beta_deg.toFixed(1)}°`:'';
  const roll=$('campoRollV1');
  if(roll)roll.value=o&&Number.isFinite(o.gamma_deg)?`${o.gamma_deg.toFixed(1)}°`:'';
}

async function nextStationCode(){
  const d=val('campoData')||new Date().toISOString().slice(0,10);
  const ymd=d.replaceAll('-','');
  let max=0,count=0;
  try{
    if(typeof itaGetRecords==='function'){
      const rows=await itaGetRecords();
      for(const r of rows){
        if(r.data===d)count++;
        const code=r.station_code||r.field_station?.code||'';
        const m=String(code).match(new RegExp(`^ITA-MS-${ymd}-(\\d{{3}})$`));
        if(m)max=Math.max(max,Number(m[1]));
      }
    }
  }catch(_){}
  const n=Math.max(max,count)+1;
  return `ITA-MS-${ymd}-${String(n).padStart(3,'0')}`;
}
async function ensureStationCode(force=false){
  const input=$('campoStationCodeV1');
  if(!input)return null;
  if(!force&&input.value)return input.value;
  const code=await nextStationCode();
  input.value=code;
  state.lastStationCode=code;
  updateLivePlate();
  return code;
}
async function generateSampleCode(){
  const station=await ensureStationCode();
  const sample=$('campoSampleLocal');
  if(sample&&!sample.value)sample.value=`${station}-A01`;
}

async function startCamera(){
  const status=$('campoCameraStatusV1');
  try{
    if(!window.isSecureContext)throw new Error('A câmera web requer HTTPS ou contexto seguro.');
    if(!navigator.mediaDevices?.getUserMedia)throw new Error('A câmera web não está disponível neste navegador.');
    stopCamera();
    state.stream=await navigator.mediaDevices.getUserMedia({
      video:{
        facingMode:{ideal:'environment'},
        width:{ideal:1920},
        height:{ideal:1080}
      },
      audio:false
    });
    const video=$('campoCameraVideoV1');
    video.srcObject=state.stream;
    await video.play();
    if(status)status.textContent='Câmera ativa. A imagem original sem placa será preservada junto com a cópia cartográfica.';
    try{await getFreshPosition(true)}catch(_){}
    updateLivePlate();
  }catch(e){
    if(status)status.textContent='Câmera indisponível · '+(e.message||String(e));
  }
}
function stopCamera(){
  if(state.stream){
    state.stream.getTracks().forEach(t=>t.stop());
    state.stream=null;
  }
  const video=$('campoCameraVideoV1');
  if(video)video.srcObject=null;
}
function orientationSnapshot(){
  return state.orientation?{...state.orientation}:null;
}
function photoMetaBase(position,origin){
  return {
    station_code:val('campoStationCodeV1')||null,
    spot_id:val('campoSpotId')||null,
    sample_code:val('campoSampleLocal')||null,
    origin,
    location:position?{...position}:null,
    orientation:orientationSnapshot(),
    recorded_at_utc:nowIso()
  };
}
function updateLivePlate(){
  const box=$('campoCameraLivePlateV1');
  if(!box)return;
  const p=state.gps||currentFormPosition('form_current');
  const station=val('campoStationCodeV1')||'estação não definida';
  const utm=p?.utm?utmText(p.utm):'UTM —';
  const alt=Number.isFinite(p?.altitude_m)?`${p.altitude_m.toFixed(0)} m`:'alt —';
  const acc=Number.isFinite(p?.accuracy_m)?`±${p.accuracy_m.toFixed(0)} m`:'precisão —';
  const heading=bearingLabel(state.orientation);
  box.innerHTML=`<strong>ITA ARANDU MS · ${esc(station)}</strong><span>${esc(utm)}</span><span>${esc(alt)} · GPS ${esc(acc)} · rumo ${esc(heading)}</span>`;
}

async function captureFrameBlob(){
  const video=$('campoCameraVideoV1');
  if(!video?.srcObject||!video.videoWidth)throw new Error('Ative a câmera antes de fotografar.');
  const sz=fitCanvasSize(video.videoWidth,video.videoHeight,1920);
  const canvas=document.createElement('canvas');
  canvas.width=sz.w;canvas.height=sz.h;
  const ctx=canvas.getContext('2d',{alpha:false});
  ctx.drawImage(video,0,0,sz.w,sz.h);
  return await canvasBlob(canvas,'image/jpeg',.9);
}
async function makeOverlayBlob(original,meta,label='captura'){
  const img=await imageFromBlob(original);
  const w=img.width||img.videoWidth,h=img.height||img.videoHeight;
  const canvas=document.createElement('canvas');
  canvas.width=w;canvas.height=h;
  const ctx=canvas.getContext('2d',{alpha:false});
  ctx.drawImage(img,0,0,w,h);

  const band=Math.max(118,Math.min(230,Math.round(h*.18)));
  const font=Math.max(18,Math.min(34,Math.round(w/48)));
  ctx.fillStyle='rgba(4,22,32,.84)';
  ctx.fillRect(0,h-band,w,band);
  ctx.fillStyle='#fff';
  ctx.font=`700 ${font}px system-ui, sans-serif`;
  const station=meta.station_code||'ITA ARANDU MS';
  ctx.fillText(`ITA ARANDU MS · ${station}`,Math.round(font*.7),h-band+font*1.25);

  ctx.font=`500 ${Math.round(font*.78)}px system-ui, sans-serif`;
  const p=meta.location;
  const u=p?.utm?utmText(p.utm):'UTM —';
  const alt=Number.isFinite(p?.altitude_m)?`${p.altitude_m.toFixed(0)} m`:'alt —';
  const acc=Number.isFinite(p?.accuracy_m)?`±${p.accuracy_m.toFixed(0)} m`:'precisão —';
  const o=meta.orientation;
  const br=bearingLabel(o);
  const y1=h-band+font*2.45;
  ctx.fillText(u,Math.round(font*.7),y1);
  ctx.fillText(`${alt} · GPS ${acc} · rumo ${br}`,Math.round(font*.7),y1+font*1.05);
  const last=`${label} · ${localStamp()}${meta.sample_code?' · '+meta.sample_code:''}`;
  ctx.fillText(last,Math.round(font*.7),y1+font*2.1);
  return await canvasBlob(canvas,'image/jpeg',.9);
}

async function captureGeoPhoto(){
  const status=$('campoCameraStatusV1');
  try{
    await ensureStationCode();
    const original=await captureFrameBlob();
    let p=null;
    try{p=await getFreshPosition(true)}catch(_){p=state.gps||currentFormPosition('form_current')}
    const meta=photoMetaBase(p,'web_camera');
    meta.georeference_status=p?.source==='device_geolocation'?'simultaneous_device_geolocation':'station_position_fallback';
    meta.capture_note='Captura PWA. Metadados científicos estruturados são primários. O aplicativo não declara escrita EXIF GPS no JPEG.';
    const originalSha=await sha256Blob(original);
    const overlay=await makeOverlayBlob(original,meta,'captura web');
    const overlaySha=await sha256Blob(overlay);
    const n=state.cameraPhotos.length+1;
    const station=meta.station_code||'ITA-MS';
    state.cameraPhotos.push({
      id:`C${n}`,
      name:`${station}_F${String(n).padStart(2,'0')}.jpg`,
      type:'image/jpeg',
      size:original.size,
      source:'web_camera',
      original_blob:original,
      overlay_blob:overlay,
      original_sha256:originalSha,
      overlay_sha256:overlaySha,
      ...meta
    });
    renderPhotoPreview();
    if(status)status.textContent=`Fotografia ${n} capturada · original sem placa + cópia cartográfica · SHA256 calculado.`;
  }catch(e){
    if(status)status.textContent='Não foi possível fotografar · '+(e.message||String(e));
  }
}

function clearPreviewUrls(){
  state.previewUrls.forEach(u=>URL.revokeObjectURL(u));
  state.previewUrls=[];
}
function galleryFiles(){
  try{
    if(typeof campoSelectedFiles!=='undefined')return [...campoSelectedFiles];
  }catch(_){}
  return [...($('campoFotos')?.files||[])];
}
function addPreviewUrl(blob){
  const u=URL.createObjectURL(blob);
  state.previewUrls.push(u);
  return u;
}
function renderPhotoPreview(){
  const box=$('campoFotoPreview');
  if(!box)return;
  clearPreviewUrls();
  const gallery=galleryFiles();
  const cards=[];

  state.cameraPhotos.forEach((p,i)=>{
    const src=addPreviewUrl(p.overlay_blob||p.original_blob);
    const acc=Number.isFinite(p.location?.accuracy_m)?`±${p.location.accuracy_m.toFixed(1)} m`:'sem precisão';
    cards.push(`<article class="ita-photo-card" data-camera-photo="${i}">
      <img src="${src}" alt="${esc(p.name)}">
      <b>${esc(p.name)}</b>
      <small>câmera web · ${esc(acc)} · ${esc(p.location?.utm?utmText(p.location.utm):'sem UTM')}</small>
      <div class="ita-photo-card-actions">
        <button type="button" class="ita-photo-mini-btn" data-photo-download-original="${i}">Original</button>
        <button type="button" class="ita-photo-mini-btn" data-photo-download-overlay="${i}">Com placa</button>
        <button type="button" class="ita-photo-mini-btn danger" data-photo-remove="${i}">Remover</button>
      </div>
    </article>`);
  });

  gallery.forEach((f,i)=>{
    const src=addPreviewUrl(f);
    cards.push(`<article class="ita-photo-card">
      <img src="${src}" alt="${esc(f.name)}">
      <b>${esc(f.name)}</b>
      <small>galeria · EXIF será verificado ao salvar · posição da estação só será atribuída se você autorizar</small>
    </article>`);
  });

  box.classList.add('ita-photo-grid');
  box.innerHTML=cards.length?cards.join(''):'<div class="empty">Nenhuma fotografia selecionada.</div>';

  box.querySelectorAll('[data-photo-download-original]').forEach(b=>{
    b.addEventListener('click',()=>{
      const p=state.cameraPhotos[Number(b.dataset.photoDownloadOriginal)];
      if(p)downloadBlob(p.original_blob,p.name.replace(/\.jpg$/i,'_ORIGINAL.jpg'));
    });
  });
  box.querySelectorAll('[data-photo-download-overlay]').forEach(b=>{
    b.addEventListener('click',()=>{
      const p=state.cameraPhotos[Number(b.dataset.photoDownloadOverlay)];
      if(p)downloadBlob(p.overlay_blob,p.name.replace(/\.jpg$/i,'_PLACA.jpg'));
    });
  });
  box.querySelectorAll('[data-photo-remove]').forEach(b=>{
    b.addEventListener('click',()=>{
      state.cameraPhotos.splice(Number(b.dataset.photoRemove),1);
      renderPhotoPreview();
    });
  });
}

/* Minimal JPEG EXIF reader for original GPS metadata on imported photos */
function ascii(dv,offset,count){
  let s='';
  for(let i=0;i<count;i++){
    const c=dv.getUint8(offset+i);
    if(c===0)break;
    s+=String.fromCharCode(c);
  }
  return s;
}
async function readExifGps(file){
  try{
    const buf=await file.arrayBuffer();
    const dv=new DataView(buf);
    if(dv.byteLength<4||dv.getUint16(0,false)!==0xFFD8)return null;
    let off=2;
    while(off+4<dv.byteLength){
      if(dv.getUint8(off)!==0xFF){off++;continue}
      const marker=dv.getUint8(off+1);
      off+=2;
      if(marker===0xD9||marker===0xDA)break;
      const len=dv.getUint16(off,false);
      if(marker===0xE1&&len>=8){
        const seg=off+2;
        if(ascii(dv,seg,6)==='Exif'){
          return parseExifTiff(dv,seg+6);
        }
      }
      off+=len;
    }
  }catch(_){}
  return null;
}
function parseExifTiff(dv,tiff){
  const little=dv.getUint16(tiff,false)===0x4949;
  const u16=o=>dv.getUint16(o,little);
  const u32=o=>dv.getUint32(o,little);
  const typeSize={1:1,2:1,3:2,4:4,5:8,7:1,9:4,10:8};
  const first=tiff+u32(tiff+4);

  function entries(ifd){
    const n=u16(ifd),out=new Map();
    for(let i=0;i<n;i++){
      const e=ifd+2+i*12;
      const tag=u16(e),type=u16(e+2),count=u32(e+4),bytes=(typeSize[type]||1)*count;
      const pos=bytes<=4?e+8:tiff+u32(e+8);
      out.set(tag,{tag,type,count,pos});
    }
    return out;
  }
  function value(ent,index=0){
    if(!ent)return null;
    const p=ent.pos;
    if(ent.type===1)return dv.getUint8(p+index);
    if(ent.type===2)return ascii(dv,p,ent.count);
    if(ent.type===3)return u16(p+index*2);
    if(ent.type===4)return u32(p+index*4);
    if(ent.type===5){
      const q=p+index*8,den=u32(q+4);
      return den?u32(q)/den:null;
    }
    if(ent.type===9)return dv.getInt32(p+index*4,little);
    if(ent.type===10){
      const q=p+index*8,den=dv.getInt32(q+4,little);
      return den?dv.getInt32(q,little)/den:null;
    }
    return null;
  }
  function rational3(ent){
    return [value(ent,0),value(ent,1),value(ent,2)];
  }
  function dms(v,ref){
    if(!v.every(Number.isFinite))return null;
    let x=v[0]+v[1]/60+v[2]/3600;
    if(ref==='S'||ref==='W')x=-x;
    return x;
  }

  const ifd0=entries(first);
  let dateTimeOriginal=null;
  const exifPtr=value(ifd0.get(0x8769));
  if(Number.isFinite(exifPtr)){
    const exif=entries(tiff+exifPtr);
    dateTimeOriginal=value(exif.get(0x9003))||value(exif.get(0x9004))||null;
  }

  const gpsPtr=value(ifd0.get(0x8825));
  if(!Number.isFinite(gpsPtr)){
    return dateTimeOriginal?{datetime_original:dateTimeOriginal}:null;
  }
  const gps=entries(tiff+gpsPtr);
  const lat=dms(rational3(gps.get(0x0002)),value(gps.get(0x0001)));
  const lon=dms(rational3(gps.get(0x0004)),value(gps.get(0x0003)));
  const altRaw=value(gps.get(0x0006));
  const altRef=value(gps.get(0x0005));
  const altitude=Number.isFinite(altRaw)?(altRef===1?-altRaw:altRaw):null;
  const direction=value(gps.get(0x0011));
  const directionRef=value(gps.get(0x0010));
  const dateStamp=value(gps.get(0x001D))||null;

  return {
    latitude:Number.isFinite(lat)?lat:null,
    longitude:Number.isFinite(lon)?lon:null,
    altitude_m:altitude,
    image_direction_deg:Number.isFinite(direction)?deg(direction):null,
    image_direction_ref:directionRef||null,
    datetime_original:dateTimeOriginal,
    gps_date_stamp:dateStamp
  };
}

async function processGalleryFile(file,index){
  const originalSha=await sha256Blob(file);
  const exif=await readExifGps(file);
  let p=null,status='not_georeferenced',source='none',distance=null;

  if(Number.isFinite(exif?.latitude)&&Number.isFinite(exif?.longitude)){
    p={
      latitude:exif.latitude,
      longitude:exif.longitude,
      accuracy_m:null,
      altitude_m:Number.isFinite(exif.altitude_m)?exif.altitude_m:null,
      altitude_accuracy_m:null,
      heading_deg:Number.isFinite(exif.image_direction_deg)?exif.image_direction_deg:null,
      speed_m_s:null,
      source:'embedded_exif',
      captured_at_utc:null,
      captured_at_original:exif.datetime_original||null,
      utm:latLonToUTM(exif.latitude,exif.longitude)
    };
    status='embedded_exif_original';
    source='embedded_exif';
    const station=currentFormPosition('station_form');
    if(station)distance=haversine(p.latitude,p.longitude,station.latitude,station.longitude);
  }else if($('campoAssociateGalleryV1')?.checked){
    p=state.gps||currentFormPosition('station_position_attributed_later');
    if(p){
      p={...p,source:'station_position_attributed_later',georeference_attributed_at_utc:nowIso()};
      status='attributed_later';
      source='station_record';
    }
  }

  const meta=photoMetaBase(p,'gallery_import');
  meta.georeference_status=status;
  meta.exif=exif;
  meta.exif_read_status=exif?'read':'not_found_or_unsupported';
  meta.distance_to_station_m=Number.isFinite(distance)?distance:null;
  meta.georeference_source=source;
  meta.capture_note=status==='attributed_later'
    ?'A posição foi atribuída posteriormente a partir da estação. Não representa necessariamente a posição original de captura.'
    :'A posição EXIF, quando presente, é preservada como metadado original da fotografia.';

  let overlay=null,overlaySha=null;
  if($('campoOverlayV1')?.checked){
    try{
      overlay=await makeOverlayBlob(file,meta,status==='attributed_later'?'posição atribuída posteriormente':'foto importada');
      overlaySha=await sha256Blob(overlay);
    }catch(_){}
  }

  return {
    id:`G${index+1}`,
    name:file.name,
    type:file.type||'image/jpeg',
    size:file.size,
    source:'gallery_import',
    original_blob:file,
    overlay_blob:overlay,
    original_sha256:originalSha,
    overlay_sha256:overlaySha,
    ...meta
  };
}

function locationForRecord(){
  const p=state.gps||currentFormPosition(val('campoGpsSourceV1')||'form');
  if(!p)return null;
  return {
    latitude:p.latitude,
    longitude:p.longitude,
    accuracy_m:p.accuracy_m,
    altitude_m:p.altitude_m,
    altitude_accuracy_m:p.altitude_accuracy_m,
    speed_m_s:p.speed_m_s,
    gps_heading_deg:p.heading_deg,
    source:p.source,
    captured_at_utc:p.captured_at_utc,
    municipio:val('campoMunicipio'),
    acesso:val('campoAcesso'),
    hex_250:val('campoHex250'),
    hex_500:val('campoHex500'),
    hex_1000:val('campoHex1000'),
    utm:p.utm
  };
}

async function saveFieldV1(){
  const status=$('campoStatus');
  try{
    const lat=num('campoLat'),lon=num('campoLon');
    if((val('campoLat')&&lat==null)||(val('campoLon')&&lon==null))throw new Error('Coordenadas inválidas');
    if(lat!=null&&lon!=null){
      try{if(typeof itaIdentifyGrids==='function')itaIdentifyGrids()}catch(_){}
      if(!state.gps)state.gps=currentFormPosition(val('campoGpsSourceV1')||'form');
    }

    const igsn=val('campoIGSN'),igsnStatus=val('campoIGSNStatus');
    if(igsnStatus==='registrado'&&!igsn)throw new Error('Informe o IGSN antes de marcar como registrado.');

    const stationCode=await ensureStationCode();
    const spotId=val('campoSpotId')||(typeof itaSpotId==='function'?itaSpotId():`ITA-SPOT-${Date.now()}`);
    if(status)status.textContent='Preparando fotografias, EXIF e hashes SHA256.';

    const imported=[];
    const files=galleryFiles();
    for(let i=0;i<files.length;i++){
      if(status)status.textContent=`Processando fotografia importada ${i+1} de ${files.length}.`;
      imported.push(await processGalleryFile(files[i],i));
    }
    const photos=[...state.cameraPhotos.map(p=>({...p,spot_id:spotId,station_code:stationCode})),...imported.map(p=>({...p,spot_id:spotId,station_code:stationCode}))];

    const location=locationForRecord();
    const rec={
      id:typeof itaId==='function'?itaId():`ITA-CAMPO-${Date.now()}`,
      schema_version:'1.0',
      project:'ITA ARANDU MS',
      module:'Caderno de Campo Geocientífico Digital',
      status:'capturada_local',
      created_at:nowIso(),
      station_code:stationCode,
      campanha:val('campoCampanha'),
      observador:val('campoObservador'),
      disciplina:val('campoDisciplina'),
      nome_ponto:val('campoNome'),
      data:val('campoData'),
      hora:val('campoHora'),
      spot:{
        spot_id:spotId,
        parent_spot_id:val('campoParentSpot')||null,
        geometry_type:'Point',
        tags:typeof itaTags==='function'?itaTags():val('campoTags').split(',').map(x=>x.trim()).filter(Boolean),
        geometry:location?{type:'Point',coordinates:[location.longitude,location.latitude]}:null
      },
      location,
      sensors:{
        device_orientation:orientationSnapshot(),
        note:'Orientação do dispositivo não substitui medida estrutural com instrumento e método documentados.'
      },
      geology:{
        exposicao:val('campoExposicao'),
        litologia:val('campoLitologia'),
        mineralogia:val('campoMineralogia'),
        alteracao:val('campoAlteracao'),
        estruturas:val('campoEstruturas'),
        medidas_estruturais:val('campoMedidas'),
        observacao:val('campoObservacao'),
        interpretacao:val('campoInterpretacao'),
        hidrogeologia:val('campoHidro'),
        mineralizacao:val('campoMineralizacao'),
        geotecnia:val('campoGeotecnia'),
        amostras:val('campoAmostras')
      },
      samples:{
        notes:val('campoAmostras'),
        primary:{
          local_code:val('campoSampleLocal')||null,
          igsn_id:igsn||null,
          igsn_status:igsnStatus||'nao_registrado'
        }
      },
      quality:{
        confianca:val('campoConfianca'),
        sensibilidade:val('campoSensibilidade'),
        validation:'nao_revisada',
        gps_quality:gpsQuality(location?.accuracy_m)
      },
      photo_provenance:{
        metadata_model:'structured_sidecar_primary',
        exif_policy:'read_original_exif_when_available_on_import',
        exif_write_status:'not_claimed_by_web_app',
        gallery_position_policy:'never attribute station position unless explicitly enabled',
        originals_preserved_without_visual_plate:true,
        overlay_copies_optional:true
      },
      photos
    };

    if(typeof itaOpenFieldDB!=='function')throw new Error('Banco local do módulo Campo não disponível.');
    const db=await itaOpenFieldDB();
    await new Promise((resolve,reject)=>{
      const tx=db.transaction(ITA_FIELD_STORE,'readwrite');
      tx.objectStore(ITA_FIELD_STORE).put(rec);
      tx.oncomplete=resolve;
      tx.onerror=()=>reject(tx.error);
    });

    if(status)status.textContent=`Estação ${stationCode} salva localmente · ${photos.length} fotografia(s) · metadados estruturados e hashes preservados.`;
    stopCamera();
    state.cameraPhotos=[];
    state.gps=null;
    clearPreviewUrls();
    try{if(typeof itaRenderFieldRecords==='function')await itaRenderFieldRecords()}catch(_){}
    try{if(typeof itaNewField==='function')itaNewField(false)}catch(_){}
    setTimeout(async()=>{resetExtras();await ensureStationCode(true)},0);
  }catch(e){
    if(status)status.textContent='Não foi possível salvar · '+(e.message||String(e));
  }
}

function cleanRecordForExport(r){
  return {
    ...r,
    photos:(r.photos||[]).map(p=>{
      const {original_blob,overlay_blob,...meta}=p;
      return meta;
    })
  };
}
async function exportJsonV1(){
  const status=$('campoStatus');
  try{
    const rows=typeof itaGetRecords==='function'?await itaGetRecords():[];
    const payload={
      project:'ITA ARANDU MS',
      module:'Caderno de Campo Geocientífico Digital',
      schema_version:'1.0',
      exported_at:nowIso(),
      crs_coordinates:'WGS84 geographic with derived dynamic UTM',
      note:'Fotografias binárias permanecem no IndexedDB local. O JSON exporta metadados, proveniência e SHA256.',
      records:rows.map(cleanRecordForExport)
    };
    downloadBlob(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),`ITA_ARANDU_CAMPO_${new Date().toISOString().slice(0,10)}.json`);
    if(status)status.textContent=`Exportadas ${rows.length} ficha(s) em JSON com metadados fotográficos e SHA256.`;
  }catch(e){
    if(status)status.textContent='Falha ao exportar JSON · '+(e.message||String(e));
  }
}
async function exportGeoJsonV1(){
  const status=$('campoStatus');
  try{
    const rows=typeof itaGetRecords==='function'?await itaGetRecords():[];
    const fc={
      type:'FeatureCollection',
      name:'ITA_ARANDU_CAMPO',
      features:rows.filter(r=>r.spot?.geometry).map(r=>({
        type:'Feature',
        geometry:r.spot.geometry,
        properties:{
          station_code:r.station_code||null,
          spot_id:r.spot?.spot_id||null,
          nome_ponto:r.nome_ponto||null,
          campanha:r.campanha||null,
          observador:r.observador||null,
          data:r.data||null,
          hora:r.hora||null,
          accuracy_m:r.location?.accuracy_m??null,
          altitude_m:r.location?.altitude_m??null,
          utm:r.location?.utm?utmText(r.location.utm):null,
          litologia:r.geology?.litologia||null,
          observacao:r.geology?.observacao||null,
          interpretacao:r.geology?.interpretacao||null,
          sample_code:r.samples?.primary?.local_code||null,
          photos:(r.photos||[]).length,
          photo_sha256:(r.photos||[]).map(p=>p.original_sha256).filter(Boolean).join('|')
        }
      }))
    };
    downloadBlob(new Blob([JSON.stringify(fc,null,2)],{type:'application/geo+json'}),`ITA_ARANDU_CAMPO_${new Date().toISOString().slice(0,10)}.geojson`);
    if(status)status.textContent=`Exportadas ${fc.features.length} estação(ões) em GeoJSON.`;
  }catch(e){
    if(status)status.textContent='Falha ao exportar GeoJSON · '+(e.message||String(e));
  }
}
function xmlEsc(s){
  return String(s??'').replace(/[<>&'"]/g,m=>({'<':'&lt;','>':'&gt;','&':'&amp;',"'":'&apos;','"':'&quot;'}[m]));
}
async function exportKmlV1(){
  const status=$('campoStatus');
  try{
    const rows=typeof itaGetRecords==='function'?await itaGetRecords():[];
    const marks=rows.filter(r=>r.spot?.geometry?.type==='Point').map(r=>{
      const [lon,lat]=r.spot.geometry.coordinates;
      const name=r.station_code||r.nome_ponto||r.spot?.spot_id||'Estação';
      const desc=[
        r.nome_ponto,
        r.geology?.litologia&&`Litologia: ${r.geology.litologia}`,
        r.samples?.primary?.local_code&&`Amostra: ${r.samples.primary.local_code}`,
        r.location?.accuracy_m!=null&&`Precisão GPS: ±${r.location.accuracy_m} m`,
        r.location?.utm&&`UTM: ${utmText(r.location.utm)}`,
        `Fotos: ${(r.photos||[]).length}`
      ].filter(Boolean).join('\n');
      return `<Placemark><name>${xmlEsc(name)}</name><description>${xmlEsc(desc)}</description><Point><coordinates>${lon},${lat},${r.location?.altitude_m??0}</coordinates></Point></Placemark>`;
    }).join('');
    const kml=`<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>ITA ARANDU Campo</name>${marks}</Document></kml>`;
    downloadBlob(new Blob([kml],{type:'application/vnd.google-earth.kml+xml'}),`ITA_ARANDU_CAMPO_${new Date().toISOString().slice(0,10)}.kml`);
    if(status)status.textContent='KML gerado para uso em SIG ou Google Earth.';
  }catch(e){
    if(status)status.textContent='Falha ao exportar KML · '+(e.message||String(e));
  }
}

function resetExtras(){
  stopCamera();
  state.cameraPhotos=[];
  state.gps=null;
  if($('campoStationCodeV1'))$('campoStationCodeV1').value='';
  ['campoUtmV1','campoGpsSourceV1','campoGpsTimestampV1','campoAltitudeAccuracyV1','campoHeadingV1','campoPitchV1','campoRollV1'].forEach(id=>{if($(id))$(id).value=''});
  if($('campoGpsQualityV1'))$('campoGpsQualityV1').textContent='sem medição';
  if($('campoCameraStatusV1'))$('campoCameraStatusV1').textContent='Câmera ainda não ativada.';
  renderPhotoPreview();
}

function augmentFieldUi(){
  const modal=$('campoModal');
  if(!modal||$('campoGeoCameraFieldsetV1'))return false;

  const kicker=modal.querySelector('.modal-head .kicker');
  if(kicker)kicker.textContent='ITA ARANDU Campo · caderno geocientífico digital';
  const h2=modal.querySelector('.modal-head h2');
  if(h2)h2.textContent='Estação geológica de campo';

  const form=$('campoForm');
  if(!form)return false;

  const firstField=form.querySelector('fieldset.field-box');
  if(firstField){
    const station=document.createElement('div');
    station.className='ita-field-provenance';
    station.innerHTML=`
      <div class="ita-station-row">
        <label><span class="field-label">Código da estação</span><input class="field-input" id="campoStationCodeV1" readonly></label>
        <button type="button" class="action-btn" id="campoStationNewV1">Gerar código</button>
      </div>
      <div class="field-help">O código identifica a estação no caderno local. O Spot ID continua preservado para compatibilidade com a estrutura já existente.</div>`;
    firstField.appendChild(station);
  }

  const gpsStatus=$('campoGpsStatus');
  const locField=gpsStatus?.closest('fieldset');
  if(locField){
    const prov=document.createElement('div');
    prov.className='ita-field-provenance';
    prov.innerHTML=`
      <div class="ita-field-provenance-grid">
        <label class="ita-field-chip"><b>UTM WGS84</b><input class="field-input" id="campoUtmV1" readonly></label>
        <label class="ita-field-chip"><b>Fonte da posição</b><input class="field-input" id="campoGpsSourceV1" readonly></label>
        <label class="ita-field-chip"><b>UTC da medição</b><input class="field-input" id="campoGpsTimestampV1" readonly></label>
        <label class="ita-field-chip"><b>Precisão vertical m</b><input class="field-input" id="campoAltitudeAccuracyV1" readonly></label>
        <label class="ita-field-chip"><b>Rumo da foto</b><input class="field-input ita-sensor-reading" id="campoHeadingV1" readonly></label>
        <span class="ita-field-chip"><b>Qualidade GPS</b><span id="campoGpsQualityV1">sem medição</span></span>
      </div>`;
    locField.appendChild(prov);
  }

  const sample=$('campoSampleLocal');
  if(sample){
    const label=sample.closest('label');
    const btn=document.createElement('button');
    btn.type='button';btn.id='campoGerarAmostraV1';btn.className='action-btn';
    btn.textContent='Gerar a partir da estação';
    label?.appendChild(btn);
  }

  const photoInput=$('campoFotos');
  const photoField=photoInput?.closest('fieldset');
  if(photoField){
    const legend=photoField.querySelector('legend');
    if(legend)legend.textContent='Fotografias importadas';
    const lab=photoInput.closest('label')?.querySelector('.field-label');
    if(lab)lab.textContent='Galeria ou câmera do sistema';
    const help=photoField.querySelector('.field-help');
    if(help)help.textContent='Fotos importadas mantêm seus arquivos originais. Se houver GPS EXIF, ele será lido ao salvar. A posição da estação só será atribuída posteriormente se você marcar essa opção.';

    const camera=document.createElement('fieldset');
    camera.className='field-box';
    camera.id='campoGeoCameraFieldsetV1';
    camera.innerHTML=`
      <legend>Câmera geocientífica</legend>
      <div class="ita-geocamera">
        <div class="ita-camera-stage">
          <video id="campoCameraVideoV1" class="ita-camera-video" playsinline autoplay muted></video>
          <div class="ita-camera-liveplate" id="campoCameraLivePlateV1"><strong>ITA ARANDU MS</strong><span>Ative GPS e câmera para iniciar.</span></div>
        </div>
        <div class="ita-camera-controls">
          <button type="button" class="action-btn primary" id="campoCameraStartV1">Ativar câmera</button>
          <button type="button" class="action-btn primary" id="campoCameraCaptureV1">Fotografar</button>
          <button type="button" class="action-btn" id="campoCameraStopV1">Parar câmera</button>
          <button type="button" class="action-btn" id="campoSensorStartV1">Ativar bússola</button>
          <button type="button" class="action-btn" id="campoGpsRefreshV1">Atualizar GPS</button>
        </div>
        <div class="ita-camera-status">
          <span class="ita-field-chip"><b>Rumo</b><span id="campoHeadingChipV1">—</span></span>
          <span class="ita-field-chip"><b>Inclinação</b><span id="campoPitchChipV1">—</span></span>
          <span class="ita-field-chip"><b>Rolagem</b><span id="campoRollChipV1">—</span></span>
          <span class="ita-field-chip"><b>Armazenamento</b><span id="campoStorageV1">local</span></span>
        </div>
        <label><input type="checkbox" id="campoOverlayV1" checked> gerar também uma cópia cartográfica com placa visível</label>
        <label><input type="checkbox" id="campoAssociateGalleryV1"> atribuir a posição desta estação às fotos importadas que não tenham GPS EXIF</label>
        <div class="ita-camera-note warn">A posição atribuída posteriormente nunca será registrada como posição original da fotografia. O original permanece sem placa. A PWA guarda metadados científicos estruturados e não declara escrita de GPS EXIF no JPEG capturado.</div>
        <div class="ita-camera-note" id="campoCameraStatusV1">Câmera ainda não ativada.</div>
        <div class="ita-camera-note" id="campoSensorStatusV1">Bússola ainda não ativada. O rumo do dispositivo é auxiliar e não substitui medida estrutural com método documentado.</div>
      </div>`;
    photoField.parentNode.insertBefore(camera,photoField);
  }

  const actions=$('campoSalvar')?.closest('.field-actions');
  if(actions&&!$('campoExportarGeoJSONV1')){
    const extra=document.createElement('div');
    extra.className='ita-export-extra';
    extra.innerHTML=`
      <button type="button" class="action-btn" id="campoExportarGeoJSONV1">Exportar GeoJSON</button>
      <button type="button" class="action-btn" id="campoExportarKMLV1">Exportar KML</button>
      <a class="action-btn" href="./documentos/protocolo-campo-geofoto.html" target="_blank" rel="noopener">Protocolo GeoFoto</a>`;
    actions.insertAdjacentElement('afterend',extra);
  }

  return true;
}

function replaceButtonHandler(id,handler){
  const old=$(id);
  if(!old)return null;
  const neo=old.cloneNode(true);
  old.replaceWith(neo);
  neo.addEventListener('click',handler);
  return neo;
}

async function storageEstimate(){
  const el=$('campoStorageV1');
  if(!el)return;
  try{
    const e=await navigator.storage?.estimate?.();
    if(e&&Number.isFinite(e.usage)&&Number.isFinite(e.quota)){
      el.textContent=`${(e.usage/1048576).toFixed(0)} / ${(e.quota/1048576).toFixed(0)} MB`;
    }else el.textContent='local';
  }catch(_){el.textContent='local'}
}
function renderSensorChips(){
  const o=state.orientation;
  if($('campoHeadingChipV1'))$('campoHeadingChipV1').textContent=bearingLabel(o);
  if($('campoPitchChipV1'))$('campoPitchChipV1').textContent=o&&Number.isFinite(o.beta_deg)?`${o.beta_deg.toFixed(1)}°`:'—';
  if($('campoRollChipV1'))$('campoRollChipV1').textContent=o&&Number.isFinite(o.gamma_deg)?`${o.gamma_deg.toFixed(1)}°`:'—';
}
const oldRenderSensor=renderSensorState;
renderSensorState=function(){
  oldRenderSensor();
  renderSensorChips();
};

function wire(){
  if(!augmentFieldUi())return;

  replaceButtonHandler('campoGps',enhancedGps);
  replaceButtonHandler('campoSalvar',saveFieldV1);
  replaceButtonHandler('campoExportar',exportJsonV1);

  $('campoStationNewV1')?.addEventListener('click',()=>ensureStationCode(true));
  $('campoGerarAmostraV1')?.addEventListener('click',generateSampleCode);
  $('campoCameraStartV1')?.addEventListener('click',startCamera);
  $('campoCameraCaptureV1')?.addEventListener('click',captureGeoPhoto);
  $('campoCameraStopV1')?.addEventListener('click',stopCamera);
  $('campoSensorStartV1')?.addEventListener('click',requestOrientation);
  $('campoGpsRefreshV1')?.addEventListener('click',enhancedGps);
  $('campoExportarGeoJSONV1')?.addEventListener('click',exportGeoJsonV1);
  $('campoExportarKMLV1')?.addEventListener('click',exportKmlV1);

  $('campoFotos')?.addEventListener('change',()=>setTimeout(renderPhotoPreview,0));
  ['campoLat','campoLon','campoAltitude','campoPrecisao'].forEach(id=>{
    $(id)?.addEventListener('change',()=>{
      const p=currentFormPosition('manual_or_form');
      if(p)updateLocationUi(p);
    });
  });

  $('campoCentroMapa')?.addEventListener('click',()=>{
    setTimeout(()=>{
      const p=currentFormPosition('map_center');
      if(p)updateLocationUi(p);
    },0);
  });

  $('campoNovo')?.addEventListener('click',()=>{
    setTimeout(async()=>{resetExtras();await ensureStationCode(true)},0);
  });

  document.querySelectorAll('[data-modal="campoModal"]').forEach(b=>{
    b.addEventListener('click',()=>setTimeout(async()=>{
      await ensureStationCode();
      const p=currentFormPosition(val('campoGpsSourceV1')||'form');
      if(p)updateLocationUi(p);
      await storageEstimate();
      renderPhotoPreview();
    },0));
  });

  document.querySelectorAll('[data-close="campoModal"]').forEach(b=>b.addEventListener('click',stopCamera));
  window.addEventListener('pagehide',stopCamera);

  ensureStationCode();
  storageEstimate();
  renderPhotoPreview();
  updateLivePlate();
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',wire,{once:true});
}else{
  wire();
}

window.ITA_CAMPO_GEOFOTO={
  version:ITA_GEOFOTO_VERSION,
  state,
  latLonToUTM,
  readExifGps,
  exportGeoJsonV1,
  exportKmlV1
};
})();
