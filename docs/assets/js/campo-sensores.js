/* ITA ARANDU MS · UX-CAMPO-02 · Instrumentos do dispositivo · 2026-08-14
   As leituras são auxiliares e preservam procedência instrumental.
   A matriz Z-X'-Y'' segue Device Orientation and Motion do W3C.
*/
(function(){
  'use strict';

  const RAD=Math.PI/180;
  const DEG=180/Math.PI;
  const OFFSET_KEY='ita_arandu_sensor_offset_deg';
  const state={
    active:false,
    orientation:{alpha:null,beta:null,gamma:null,absolute:false,matrix:null,heading:null,heading_raw:null,heading_source:'',webkit_heading:null,webkit_accuracy:null,timestamp:null},
    motion:{acceleration:null,acceleration_including_gravity:null,rotation_rate:null,interval:null,timestamp:null},
    generic:{gravity:null,gyro:null,absoluteOrientation:null},
    recent:[],
    permission:{orientation:'desconhecida',motion:'desconhecida'},
    lastAbsoluteAt:0
  };

  function finite(v){return Number.isFinite(Number(v))?Number(v):null}
  function norm360(v){const n=Number(v);return Number.isFinite(n)?((n%360)+360)%360:null}
  function clamp(v,a,b){return Math.max(a,Math.min(b,v))}
  function fmt(v,d=1){return Number.isFinite(Number(v))?Number(v).toFixed(d):'—'}
  function nowIso(){return new Date().toISOString()}
  function el(id){return document.getElementById(id)}
  function offset(){const input=finite(el('campoSensorOffset')?.value);return input??0}
  function adjusted(v){return v==null?null:norm360(v+offset())}
  function vecNorm(v){const n=Math.hypot(v[0],v[1],v[2]);return n?[v[0]/n,v[1]/n,v[2]/n]:[0,0,0]}
  function transform(m,v){return [m[0]*v[0]+m[1]*v[1]+m[2]*v[2],m[3]*v[0]+m[4]*v[1]+m[5]*v[2],m[6]*v[0]+m[7]*v[1]+m[8]*v[2]]}
  function azimuth(v){const h=Math.hypot(v[0],v[1]);return h<1e-6?null:norm360(Math.atan2(v[0],v[1])*DEG)}

  function rotationMatrix(alpha,beta,gamma){
    const x=(finite(beta)??0)*RAD;
    const y=(finite(gamma)??0)*RAD;
    const z=(finite(alpha)??0)*RAD;
    const cX=Math.cos(x),cY=Math.cos(y),cZ=Math.cos(z);
    const sX=Math.sin(x),sY=Math.sin(y),sZ=Math.sin(z);
    return [
      cZ*cY-sZ*sX*sY, -cX*sZ, cY*sZ*sX+cZ*sY,
      cY*sZ+cZ*sX*sY, cZ*cX, sZ*sY-cZ*cY*sX,
      -cX*sY, sX, cX*cY
    ];
  }

  function planeFromRotation(m){
    let n=vecNorm(transform(m,[0,0,1]));
    if(n[2]<0)n=n.map(v=>-v);
    const dip=Math.acos(clamp(n[2],0,1))*DEG;
    let dipDirection=null;
    let strike=null;
    if(dip>0.25&&dip<89.75){
      const down=[0,0,-1];
      const dot=down[0]*n[0]+down[1]*n[1]+down[2]*n[2];
      const tangent=[down[0]-dot*n[0],down[1]-dot*n[1],down[2]-dot*n[2]];
      dipDirection=azimuth(tangent);
      strike=dipDirection==null?null:norm360(dipDirection-90);
    }else if(dip>=89.75){
      const normalAz=azimuth(n);
      strike=normalAz==null?null:norm360(normalAz-90);
    }
    return {dip,strike,dip_direction:dipDirection,normal:n,matrix:m};
  }

  function planeFromMatrix(alpha,beta,gamma){return planeFromRotation(rotationMatrix(alpha,beta,gamma))}

  function lineationFromRotation(m){
    let v=vecNorm(transform(m,[0,1,0]));
    if(v[2]>0)v=v.map(x=>-x);
    const horizontal=Math.hypot(v[0],v[1]);
    return {trend:azimuth(v),plunge:Math.atan2(Math.max(0,-v[2]),horizontal)*DEG,vector:v,matrix:m};
  }

  function lineationFromMatrix(alpha,beta,gamma){return lineationFromRotation(rotationMatrix(alpha,beta,gamma))}

  function dipFromGravity(g){
    if(!g)return null;
    const x=finite(g.x),y=finite(g.y),z=finite(g.z);
    if(x==null||y==null||z==null)return null;
    const mag=Math.hypot(x,y,z);
    if(mag<1e-6)return null;
    return Math.acos(clamp(Math.abs(z)/mag,0,1))*DEG;
  }

  function lineationPlungeFromGravity(g){
    if(!g)return null;
    const x=finite(g.x),y=finite(g.y),z=finite(g.z);
    if(x==null||y==null||z==null)return null;
    const mag=Math.hypot(x,y,z);
    if(mag<1e-6)return null;
    return Math.asin(clamp(Math.abs(y)/mag,0,1))*DEG;
  }

  function headingFromTopAxis(){
    const o=state.orientation;
    if(o.absolute){
      const m=o.matrix||(o.alpha!=null&&o.beta!=null&&o.gamma!=null?rotationMatrix(o.alpha,o.beta,o.gamma):null);
      if(m){const h=azimuth(transform(m,[0,1,0]));if(h!=null)return adjusted(h)}
    }
    if(o.webkit_heading!=null)return adjusted(o.webkit_heading);
    return null;
  }

  function motionMagnitude(){
    const g=state.motion.acceleration_including_gravity;
    if(!g)return null;
    const x=finite(g.x),y=finite(g.y),z=finite(g.z);
    return x==null||y==null||z==null?null:Math.hypot(x,y,z);
  }

  function rotationMagnitude(){
    const r=state.motion.rotation_rate;
    if(!r)return null;
    const a=finite(r.alpha)??0,b=finite(r.beta)??0,c=finite(r.gamma)??0;
    return Math.hypot(a,b,c);
  }

  function currentDip(){
    const o=state.orientation;
    if(o.absolute){const m=o.matrix||(o.alpha!=null&&o.beta!=null&&o.gamma!=null?rotationMatrix(o.alpha,o.beta,o.gamma):null);if(m)return planeFromRotation(m).dip;}
    return dipFromGravity(state.motion.acceleration_including_gravity);
  }

  function levelXY(){
    const g=state.motion.acceleration_including_gravity;
    if(!g)return {x:null,y:null};
    const x=finite(g.x),y=finite(g.y),z=finite(g.z);
    if(x==null||y==null||z==null)return {x:null,y:null};
    return {x:Math.atan2(x,Math.hypot(y,z))*DEG,y:Math.atan2(y,Math.hypot(x,z))*DEG};
  }

  function circularSpread(values){
    const vals=values.filter(Number.isFinite);
    if(vals.length<2)return null;
    const sx=vals.reduce((s,v)=>s+Math.sin(v*RAD),0)/vals.length;
    const cx=vals.reduce((s,v)=>s+Math.cos(v*RAD),0)/vals.length;
    const mean=norm360(Math.atan2(sx,cx)*DEG);
    return Math.max(...vals.map(v=>Math.abs((((v-mean)+540)%360)-180)));
  }

  function std(values){
    const vals=values.filter(Number.isFinite);
    if(vals.length<2)return null;
    const mean=vals.reduce((a,b)=>a+b,0)/vals.length;
    return Math.sqrt(vals.reduce((s,v)=>s+(v-mean)**2,0)/vals.length);
  }

  function stability(){
    const cutoff=Date.now()-1800;
    const rows=state.recent.filter(r=>r.t>=cutoff);
    const rot=rotationMagnitude();
    const g=motionMagnitude();
    const dipStd=std(rows.map(r=>r.dip));
    const headSpread=circularSpread(rows.map(r=>r.heading));
    let score=0;
    if(rows.length>=6)score++;
    if(rot!=null&&rot<3.5)score++;
    if(g!=null&&g>8.3&&g<11.3)score++;
    if(dipStd!=null&&dipStd<1.8)score++;
    if(headSpread==null||headSpread<5)score++;
    const stable=score>=4;
    const quality=score>=5?'boa':score>=3?'moderada':'baixa';
    return {stable,quality,score,rows:rows.length,rotation_mag:rot,gravity_mag:g,dip_std_deg:dipStd,heading_spread_deg:headSpread};
  }

  function snapshot(){
    const o=state.orientation,m=state.motion,s=stability();
    return {
      active:state.active,
      captured_at:nowIso(),
      secure_context:window.isSecureContext===true,
      manual_heading_offset_deg:offset(),
      permission:{...state.permission},
      orientation:{alpha:o.alpha,beta:o.beta,gamma:o.gamma,absolute:o.absolute,rotation_matrix:o.matrix?[...o.matrix]:null,heading_deg:headingFromTopAxis(),heading_source:o.heading_source,webkit_compass_accuracy_deg:o.webkit_accuracy},
      motion:{acceleration:m.acceleration?{...m.acceleration}:null,acceleration_including_gravity:m.acceleration_including_gravity?{...m.acceleration_including_gravity}:null,rotation_rate:m.rotation_rate?{...m.rotation_rate}:null,interval_ms:m.interval},
      stability:s,
      screen_orientation_deg:finite(window.screen?.orientation?.angle)??finite(window.orientation)??0,
      note:'Leitura auxiliar do sensor do dispositivo. Não substitui verificação de campo quando a precisão da campanha exigir instrumento geológico dedicado.'
    };
  }
  window.ITA_FIELD_SENSOR_SNAPSHOT=snapshot;
  window.ITA_FIELD_SENSOR_MATH={rotationMatrix,planeFromRotation,planeFromMatrix,lineationFromRotation,lineationFromMatrix,dipFromGravity,lineationPlungeFromGravity,norm360};

  function setStatus(msg,kind=''){
    const box=el('campoSensorStatus');
    if(box){box.textContent=msg;box.dataset.kind=kind}
  }

  function updateStatePill(){
    const p=el('campoSensorState');if(!p)return;
    p.className='sensor-state '+(state.active?'on':'off');
    p.textContent=state.active?'ativos':'desativados';
  }

  function updateHud(){
    const hud=el('sensorHud');if(!hud)return;
    const h=headingFromTopAxis();
    const show=state.active&&h!=null;
    hud.classList.toggle('hidden',!show);
    hud.setAttribute('aria-hidden',show?'false':'true');
    if(show)hud.textContent=`N ${Math.round(h)}°`;
  }

  function updateDashboard(){
    updateStatePill();
    const h=headingFromTopAxis();
    const dip=currentDip();
    const xy=levelXY();
    const gm=motionMagnitude();
    const rm=rotationMagnitude();
    const st=stability();
    if(el('campoSensorHeading'))el('campoSensorHeading').textContent=h==null?'—':`${fmt(h,1)}°`;
    if(el('campoSensorHeadingSource'))el('campoSensorHeadingSource').textContent=state.orientation.heading_source||'orientação absoluta ainda não disponível';
    if(el('campoSensorDip'))el('campoSensorDip').textContent=dip==null?'—':`${fmt(dip,1)}°`;
    if(el('campoSensorLevel'))el('campoSensorLevel').textContent=dip==null?'—':dip<1.5?'nivelado':`${fmt(dip,1)}°`;
    if(el('campoSensorLevelXY'))el('campoSensorLevelXY').textContent=`X ${xy.x==null?'—':fmt(xy.x,1)+'°'} · Y ${xy.y==null?'—':fmt(xy.y,1)+'°'}`;
    if(el('campoSensorAccel'))el('campoSensorAccel').textContent=gm==null?'—':fmt(gm,2);
    if(el('campoSensorRotation'))el('campoSensorRotation').textContent=rm==null?'—':fmt(rm,1);
    if(el('campoSensorStability'))el('campoSensorStability').textContent=st.stable?'estável':'aguarde';
    if(el('campoSensorQuality'))el('campoSensorQuality').textContent=`qualidade operacional ${st.quality}`;
    updateHud();
  }

  function addRecent(){
    state.recent.push({t:Date.now(),dip:currentDip(),heading:headingFromTopAxis()});
    if(state.recent.length>80)state.recent.splice(0,state.recent.length-80);
  }

  function orientationSource(e,forcedAbsolute){
    const wh=finite(e.webkitCompassHeading);
    const absolute=forcedAbsolute||e.absolute===true;
    if(wh!=null)return {absolute,heading:wh,source:absolute?'webkitCompassHeading + orientação absoluta':'webkitCompassHeading',accuracy:finite(e.webkitCompassAccuracy)};
    return {absolute,heading:null,source:absolute?'orientação absoluta W3C':'orientação relativa',accuracy:null};
  }

  function onOrientation(e,forcedAbsolute=false){
    const src=orientationSource(e,forcedAbsolute);
    if(!src.absolute&&state.lastAbsoluteAt&&Date.now()-state.lastAbsoluteAt<1200&&src.heading==null)return;
    state.orientation.alpha=finite(e.alpha);
    state.orientation.beta=finite(e.beta);
    state.orientation.gamma=finite(e.gamma);
    state.orientation.absolute=src.absolute;
    state.orientation.matrix=src.absolute&&state.orientation.alpha!=null&&state.orientation.beta!=null&&state.orientation.gamma!=null?rotationMatrix(state.orientation.alpha,state.orientation.beta,state.orientation.gamma):null;
    state.orientation.webkit_heading=src.heading;
    state.orientation.webkit_accuracy=src.accuracy;
    state.orientation.heading_source=src.source;
    state.orientation.timestamp=nowIso();
    if(src.absolute)state.lastAbsoluteAt=Date.now();
    addRecent();
    updateDashboard();
  }

  function copyMotionVector(v){
    if(!v)return null;
    return {x:finite(v.x),y:finite(v.y),z:finite(v.z)};
  }
  function copyRotation(v){
    if(!v)return null;
    return {alpha:finite(v.alpha),beta:finite(v.beta),gamma:finite(v.gamma)};
  }
  function onMotion(e){
    state.motion.acceleration=copyMotionVector(e.acceleration);
    state.motion.acceleration_including_gravity=copyMotionVector(e.accelerationIncludingGravity);
    state.motion.rotation_rate=copyRotation(e.rotationRate);
    state.motion.interval=finite(e.interval);
    state.motion.timestamp=nowIso();
    addRecent();
    updateDashboard();
  }

  async function askPermission(ctor,arg){
    if(!ctor||typeof ctor.requestPermission!=='function')return 'não exigida';
    try{return await ctor.requestPermission(arg)}catch(first){
      try{return await ctor.requestPermission()}catch(second){throw second}
    }
  }

  function startGenericFallbacks(){
    try{
      if(typeof window.AbsoluteOrientationSensor==='function'){
        const ao=new AbsoluteOrientationSensor({frequency:20,referenceFrame:'device'});
        ao.addEventListener('reading',()=>{
          try{
            const raw=new Float64Array(16);ao.populateMatrix(raw);
            state.orientation.matrix=[raw[0],raw[4],raw[8],raw[1],raw[5],raw[9],raw[2],raw[6],raw[10]];
            state.orientation.absolute=true;
            state.orientation.heading_source='AbsoluteOrientationSensor W3C';
            state.orientation.timestamp=nowIso();
            state.lastAbsoluteAt=Date.now();
            addRecent();updateDashboard();
          }catch(_){ }
        });
        ao.addEventListener('error',()=>{});ao.start();state.generic.absoluteOrientation=ao;
      }
    }catch(_){ }
    try{
      if(typeof window.GravitySensor==='function'){
        const g=new GravitySensor({frequency:20,referenceFrame:'device'});
        g.addEventListener('reading',()=>{
          state.motion.acceleration_including_gravity={x:finite(g.x),y:finite(g.y),z:finite(g.z)};
          state.motion.timestamp=nowIso();addRecent();updateDashboard();
        });
        g.addEventListener('error',()=>{});g.start();state.generic.gravity=g;
      }
    }catch(_){ }
    try{
      if(typeof window.Gyroscope==='function'){
        const gy=new Gyroscope({frequency:20,referenceFrame:'device'});
        gy.addEventListener('reading',()=>{
          state.motion.rotation_rate={alpha:finite(gy.x)==null?null:gy.x*DEG,beta:finite(gy.y)==null?null:gy.y*DEG,gamma:finite(gy.z)==null?null:gy.z*DEG};
          state.motion.timestamp=nowIso();updateDashboard();
        });
        gy.addEventListener('error',()=>{});gy.start();state.generic.gyro=gy;
      }
    }catch(_){ }
  }

  function onOrientationAbsolute(e){onOrientation(e,true)}
  function onOrientationRelative(e){onOrientation(e,false)}

  function attachListeners(){
    window.addEventListener('deviceorientationabsolute',onOrientationAbsolute);
    window.addEventListener('deviceorientation',onOrientationRelative);
    window.addEventListener('devicemotion',onMotion);
    startGenericFallbacks();
  }

  async function activate(){
    if(state.active){setStatus('Os instrumentos já estão ativos.');return}
    if(window.isSecureContext!==true){
      setStatus('Os sensores exigem contexto seguro. Abra o Atlas pelo GitHub Pages em HTTPS ou por localhost.','error');
      return;
    }
    setStatus('Solicitando autorização do dispositivo.');
    try{
      const O=window.DeviceOrientationEvent;
      const M=window.DeviceMotionEvent;
      const op=await askPermission(O,true);
      const mp=await askPermission(M);
      state.permission.orientation=op;
      state.permission.motion=mp;
      const oDenied=String(op).toLowerCase()==='denied';
      const mDenied=String(mp).toLowerCase()==='denied';
      if(oDenied&&mDenied){setStatus('A autorização para orientação e movimento foi negada. As medidas manuais continuam disponíveis.','error');return}
      state.active=true;
      attachListeners();
      updateDashboard();
      setStatus('Instrumentos ativos. Mantenha o aparelho longe de objetos metálicos e aguarde a indicação de estabilidade antes de capturar.','ok');
    }catch(e){
      setStatus('Não foi possível ativar os sensores neste navegador. As medidas manuais continuam disponíveis. '+(e?.message||''),'error');
    }
  }

  function stop(){
    if(!state.active){setStatus('Os instrumentos já estão desativados.');return}
    window.removeEventListener('deviceorientationabsolute',onOrientationAbsolute);
    window.removeEventListener('deviceorientation',onOrientationRelative);
    window.removeEventListener('devicemotion',onMotion);
    try{state.generic.absoluteOrientation?.stop()}catch(_){ }
    try{state.generic.gravity?.stop()}catch(_){ }
    try{state.generic.gyro?.stop()}catch(_){ }
    state.generic.absoluteOrientation=null;state.generic.gravity=null;state.generic.gyro=null;
    state.active=false;
    updateDashboard();
    setStatus('Sensores desativados. As leituras já capturadas permanecem nas medidas da estação.');
  }

  function verifyCalibration(){
    if(!state.active){setStatus('Ative os instrumentos antes de verificar a leitura.');return}
    const acc=state.orientation.webkit_accuracy;
    const extra=acc!=null&&acc>=0?` O dispositivo informa precisão de bússola de aproximadamente ±${fmt(acc,0)}°.`:'';
    setStatus('Mova o aparelho lentamente em forma de oito, afaste-o de metal, veículos e ímãs e compare o rumo com uma bússola confiável. O navegador não permite forçar a calibração do magnetômetro.'+extra);
  }

  function measureQuality(){
    const st=stability();
    if(!state.orientation.absolute)return st.stable?'moderada':'baixa';
    return st.quality;
  }

  function baseSensorMeasure(type){
    return {
      code:itaCampoMeasureCode(campoMeasures.length),
      type,
      azimuth:'',dip:'',dip_direction:'',trend:'',plunge:'',
      method:'sensores do dispositivo',
      quality:measureQuality(),
      note:'',
      instrument_source:'smartphone_sensor',
      captured_at:nowIso(),
      sensor_snapshot:snapshot()
    };
  }

  function pushMeasure(m){
    campoMeasures.push(m);
    itaCampoRenderMeasures();
    itaCampoScheduleDraft();
    const box=el('campoMedidasLista');
    box?.lastElementChild?.scrollIntoView({behavior:'smooth',block:'nearest'});
  }

  function capturePlane(){
    if(!state.active){setStatus('Ative os instrumentos antes de medir um plano.');return}
    const o=state.orientation;
    const st=stability();
    let dip=dipFromGravity(state.motion.acceleration_including_gravity);
    let strike=null,dipDir=null;
    let note='Tela apoiada paralelamente ao plano.';
    const absMatrix=o.absolute?(o.matrix||(o.alpha!=null&&o.beta!=null&&o.gamma!=null?rotationMatrix(o.alpha,o.beta,o.gamma):null)):null;
    if(absMatrix){
      const p=planeFromRotation(absMatrix);
      dip=p.dip;strike=p.strike;dipDir=p.dip_direction;
      if(p.dip>=89.75)note+=' Plano subvertical. A direção de mergulho é geometricamente ambígua e não foi preenchida.';
      if(p.dip<=0.25)note+=' Plano praticamente horizontal. A direção de mergulho não foi preenchida.';
    }else{
      note+=' Orientação absoluta indisponível. O mergulho foi estimado pela gravidade e o azimute não foi preenchido.';
    }
    if(dip==null){setStatus('Ainda não há leitura suficiente do clinômetro. Mantenha o aparelho imóvel e tente novamente.','error');return}
    const m=baseSensorMeasure('Plano');
    m.azimuth=strike==null?'':fmt(adjusted(strike),1);
    m.dip=fmt(dip,1);
    m.dip_direction=dipDir==null?'':fmt(adjusted(dipDir),1);
    m.note=note;
    m.sensor_snapshot.stability=st;
    pushMeasure(m);
    setStatus(`Plano capturado. Mergulho ${fmt(dip,1)}°${dipDir==null?'':` e direção ${fmt(adjusted(dipDir),1)}°`}. Confira a medida antes de salvar.`,'ok');
  }

  function captureLineation(){
    if(!state.active){setStatus('Ative os instrumentos antes de medir uma lineação.');return}
    const o=state.orientation;
    let trend=null,plunge=lineationPlungeFromGravity(state.motion.acceleration_including_gravity);
    let note='Bordo superior físico do aparelho alinhado à lineação.';
    const absMatrix=o.absolute?(o.matrix||(o.alpha!=null&&o.beta!=null&&o.gamma!=null?rotationMatrix(o.alpha,o.beta,o.gamma):null)):null;
    if(absMatrix){
      const l=lineationFromRotation(absMatrix);
      trend=l.trend;plunge=l.plunge;
    }else note+=' Orientação absoluta indisponível. O plunge foi estimado pela gravidade e o trend não foi preenchido.';
    if(plunge==null){setStatus('Ainda não há leitura suficiente para a lineação. Mantenha o aparelho imóvel e tente novamente.','error');return}
    const m=baseSensorMeasure('Lineação');
    m.trend=trend==null?'':fmt(adjusted(trend),1);
    m.plunge=fmt(plunge,1);
    m.note=note;
    pushMeasure(m);
    setStatus(`Lineação capturada. Plunge ${fmt(plunge,1)}°${trend==null?'':` e trend ${fmt(adjusted(trend),1)}°`}. Confira a medida antes de salvar.`,'ok');
  }

  function captureAzimuth(){
    if(!state.active){setStatus('Ative os instrumentos antes de capturar um azimute.');return}
    const h=headingFromTopAxis();
    if(h==null){setStatus('A orientação absoluta não está disponível. O Atlas não preencherá um azimute relativo como se fosse rumo geográfico.','error');return}
    const m=baseSensorMeasure('Outro');
    m.azimuth=fmt(h,1);
    m.note='Azimute do bordo superior físico do aparelho capturado pelos sensores.';
    pushMeasure(m);
    setStatus(`Azimute ${fmt(h,1)}° capturado e adicionado às medidas.`,'ok');
  }

  function enhanceMeasureCards(){
    document.querySelectorAll('#campoMedidasLista [data-measure]').forEach(card=>{
      const i=Number(card.dataset.measure);
      const m=campoMeasures[i];
      if(!m?.instrument_source||card.querySelector('.sensor-provenance'))return;
      const snap=m.sensor_snapshot||{};
      const p=document.createElement('div');
      p.className='sensor-provenance';
      const abs=snap.orientation?.absolute?'orientação absoluta':'orientação sem referência absoluta';
      const when=m.captured_at?new Date(m.captured_at).toLocaleString('pt-BR'):'sem horário';
      p.innerHTML=`<b>Procedência instrumental</b><span>sensor do dispositivo · ${abs} · ${itaEsc(when)} · qualidade ${itaEsc(m.quality||'não avaliada')}</span>`;
      card.querySelector('.campo-object-title')?.insertAdjacentElement('afterend',p);
    });
  }

  if(typeof itaCampoRenderMeasures==='function'){
    const originalRender=itaCampoRenderMeasures;
    itaCampoRenderMeasures=function(){originalRender();enhanceMeasureCards()};
    enhanceMeasureCards();
  }

  function init(){
    const stored=finite(localStorage.getItem(OFFSET_KEY));
    if(stored!=null&&el('campoSensorOffset'))el('campoSensorOffset').value=stored;
    el('campoSensoresAtivar')?.addEventListener('click',activate);
    el('campoSensoresParar')?.addEventListener('click',stop);
    el('campoSensoresVerificar')?.addEventListener('click',verifyCalibration);
    el('campoMedirPlano')?.addEventListener('click',capturePlane);
    el('campoMedirLineacao')?.addEventListener('click',captureLineation);
    el('campoCapturarAzimute')?.addEventListener('click',captureAzimuth);
    el('campoSensorOffset')?.addEventListener('change',e=>{
      const v=finite(e.target.value)??0;
      e.target.value=String(clamp(v,-180,180));
      localStorage.setItem(OFFSET_KEY,e.target.value);
      updateDashboard();
      itaCampoScheduleDraft?.();
    });
    updateDashboard();
  }

  init();
})();
