(()=>{
'use strict';
const $=id=>document.getElementById(id);
const qa=(s,r=document)=>[...r.querySelectorAll(s)];
const num=v=>{const s=String(v??'').trim().replace(',','.');if(s==='')return null;const n=Number(s);return Number.isFinite(n)?n:null};
const fmt=(v,d=2)=>Number.isFinite(v)?v.toFixed(d):'—';

function open(id){const m=$(id);if(!m)return;m.classList.add('open');m.setAttribute('aria-hidden','false');const body=m.querySelector('.ita-lab-body');if(body)body.scrollTop=0}
function close(id){const m=$(id);if(!m)return;m.classList.remove('open');m.setAttribute('aria-hidden','true')}
function tab(modal,name){if(!modal)return;qa('.ita-lab-tabs button',modal).forEach(b=>b.classList.toggle('active',b.dataset.tab===name));qa('.ita-lab-panel',modal).forEach(p=>p.classList.toggle('active',p.dataset.panel===name));if(modal.id==='granulometriaModal')granCalc();else isoUpdate()}

document.addEventListener('click',e=>{
  const a=e.target.closest('[data-tool-action]');
  if(a?.dataset.toolAction==='granulometria'){close('ferramentasModal');open('granulometriaModal');granCalc()}
  if(a?.dataset.toolAction==='isopiezas'){close('ferramentasModal');open('isopiezasModal');isoUpdate()}
  const c=e.target.closest('[data-close]');
  if(c&&['granulometriaModal','isopiezasModal'].includes(c.dataset.close))close(c.dataset.close);
  const n=e.target.closest('[data-gran-next]');if(n)tab($('granulometriaModal'),n.dataset.granNext);
});
qa('.ita-lab-tabs').forEach(nav=>nav.addEventListener('click',e=>{const b=e.target.closest('[data-tab]');if(b)tab(nav.closest('.ita-lab-modal'),b.dataset.tab)}));

/* Granulometria */
const sieves=[['4',4.75],['10',2],['20',.85],['40',.425],['60',.25],['100',.15],['200',.075],['Fundo',0]];
function addSieve(n,d,m=''){
  const tr=document.createElement('tr');
  tr.innerHTML=`<td><input class="gn" value="${n}"></td><td><input class="gd" type="number" min="0" step="0.001" value="${d}"></td><td><input class="gm" type="number" min="0" step="0.01" value="${m}"></td><td class="gr">—</td><td class="ga">—</td><td class="gp">—</td>`;
  $('granRows')?.append(tr);tr.addEventListener('input',granCalc);
}
sieves.forEach(x=>addSieve(...x));
$('granAdd')?.addEventListener('click',()=>addSieve('Nova',''));
$('granMassa')?.addEventListener('input',granCalc);

function granRowsData(){
  return qa('#granRows tr').map(tr=>({tr,d:num(tr.querySelector('.gd')?.value),m:num(tr.querySelector('.gm')?.value)}));
}
function granData(){
  const mi=num($('granMassa')?.value);
  const rows=granRowsData();
  const complete=mi!==null&&mi>0&&rows.length>0&&rows.every(r=>r.m!==null&&r.m>=0&&r.d!==null&&r.d>=0);
  let acc=0;
  const data=rows.map(r=>{
    if(complete){acc+=r.m;const retained=r.m/mi*100,ac=acc/mi*100,pass=Math.max(0,100-ac);r.tr.querySelector('.gr').textContent=fmt(retained);r.tr.querySelector('.ga').textContent=fmt(ac);r.tr.querySelector('.gp').textContent=fmt(pass);return{d:r.d,m:r.m,p:pass}}
    r.tr.querySelector('.gr').textContent='—';r.tr.querySelector('.ga').textContent='—';r.tr.querySelector('.gp').textContent='—';return{d:r.d,m:r.m,p:null};
  });
  return{mi,rows,data,complete};
}
function Dx(data,target){
  const a=data.filter(x=>x.d>0&&Number.isFinite(x.p)).sort((x,y)=>x.p-y.p);
  for(let i=1;i<a.length;i++){
    const p1=a[i-1],p2=a[i];
    if(target>=p1.p&&target<=p2.p&&p2.p!==p1.p){
      const f=(target-p1.p)/(p2.p-p1.p);
      return Math.exp(Math.log(p1.d)+f*(Math.log(p2.d)-Math.log(p1.d)));
    }
  }
  return null;
}
function granCalc(){
  const {mi,rows,data,complete}=granData();
  const entered=rows.filter(r=>r.m!==null);
  const mr=entered.reduce((s,x)=>s+x.m,0);
  const diff=complete&&mi?Math.abs(mi-mr)/mi*100:null;
  $('granMi').textContent=mi&&mi>0?fmt(mi)+' g':'—';
  $('granMr').textContent=entered.length?fmt(mr)+' g':'—';
  $('granDiff').textContent=diff===null?'—':fmt(diff)+' %';
  $('granBalance').textContent=!mi||mi<=0?'Informe uma massa inicial válida.':!complete?'Preencha todas as massas retidas. Use 0 quando a massa retida for realmente zero.':diff<=1?'Balanço dentro da tolerância de referência ≤ 1 %.':'Verifique o balanço de massa. Diferença superior a 1 %.';
  const ds=complete?[10,30,50,60].map(t=>Dx(data,t)):[null,null,null,null];
  [10,30,50,60].forEach((t,i)=>$('d'+t).textContent=ds[i]!==null?fmt(ds[i],3):'—');
  const [d10,d30,,d60]=ds,cu=d10&&d60?d60/d10:null,cc=d10&&d30&&d60?d30*d30/(d10*d60):null;
  $('granCu').textContent=cu?fmt(cu):'—';$('granCc').textContent=cc?fmt(cc):'—';
  $('granState').textContent=!complete?'Aguardando dados':d10&&d30&&d60?'Calculado':'Sem faixa suficiente';
  drawGran(complete?data:[]);
}
function drawGran(data){
  const c=$('granCanvas');if(!c)return;const x=c.getContext('2d'),W=c.width,H=c.height,p=58;x.clearRect(0,0,W,H);x.fillStyle='#fff';x.fillRect(0,0,W,H);
  x.strokeStyle='#d9e4e9';x.lineWidth=1;x.font='14px sans-serif';x.fillStyle='#526f7e';
  for(let i=0;i<=10;i++){const y=p+(H-2*p)*i/10;x.beginPath();x.moveTo(p,y);x.lineTo(W-p,y);x.stroke();x.fillText(String(100-i*10),12,y+5)}
  const pts=data.filter(a=>a.d>0&&Number.isFinite(a.p));if(pts.length<2){x.fillStyle='#607887';x.font='18px sans-serif';x.fillText('Preencha todas as massas retidas para construir a curva.',p,H/2);return}
  const logs=pts.map(a=>Math.log10(a.d)),mn=Math.min(...logs),mx=Math.max(...logs);if(mx===mn)return;
  x.strokeStyle='#075f91';x.lineWidth=4;x.beginPath();pts.sort((a,b)=>b.d-a.d).forEach((a,i)=>{const xx=p+(Math.log10(a.d)-mn)/(mx-mn)*(W-2*p),yy=H-p-a.p/100*(H-2*p);i?x.lineTo(xx,yy):x.moveTo(xx,yy)});x.stroke();
  x.fillStyle='#075f91';pts.forEach(a=>{const xx=p+(Math.log10(a.d)-mn)/(mx-mn)*(W-2*p),yy=H-p-a.p/100*(H-2*p);x.beginPath();x.arc(xx,yy,5,0,Math.PI*2);x.fill()});
  x.fillStyle='#35576a';x.font='14px sans-serif';x.fillText('Diâmetro dos grãos em escala logarítmica',W/2-120,H-12);
}
$('granExport')?.addEventListener('click',()=>{
  const rows=[['peneira','abertura_mm','massa_retida_g','percentual_passante']];
  qa('#granRows tr').forEach(tr=>rows.push([tr.querySelector('.gn').value,tr.querySelector('.gd').value,tr.querySelector('.gm').value,tr.querySelector('.gp').textContent]));
  download('granulometria.csv',rows.map(r=>r.map(csvCell).join(',')).join('\n'));
});

/* Isopiezas */
let ip=0;
function addIso(v={}){
  ip++;const tr=document.createElement('tr');
  tr.innerHTML=`<td><input class="ii" value="${v.id||'P'+ip}"></td><td><input class="ix" type="number" step="0.01" value="${v.x??''}"></td><td><input class="iy" type="number" step="0.01" value="${v.y??''}"></td><td><input class="iz" type="number" step="0.01" value="${v.z??''}"></td><td><input class="id" type="number" min="0" step="0.01" value="${v.d??''}"></td><td class="ih">—</td>`;
  $('isoRows')?.append(tr);tr.addEventListener('input',isoUpdate);
}
[{x:1250,y:3200,z:298.4,d:12.3},{x:2650,y:3150,z:296.2,d:9.8},{x:1850,y:1950,z:294.8,d:15.1},{x:3200,y:2050,z:297.1,d:10.4}].forEach(addIso);
$('isoAdd')?.addEventListener('click',()=>addIso());
function isoData(){
  return qa('#isoRows tr').map(tr=>{
    const x=num(tr.querySelector('.ix')?.value),y=num(tr.querySelector('.iy')?.value),z=num(tr.querySelector('.iz')?.value),d=num(tr.querySelector('.id')?.value);
    const valid=x!==null&&y!==null&&z!==null&&d!==null&&d>=0;const h=valid?z-d:null;
    tr.querySelector('.ih').textContent=h===null?'—':fmt(h);
    return{id:tr.querySelector('.ii')?.value||'',x,y,h,valid};
  }).filter(p=>p.valid);
}
function uniquePoints(d){const seen=new Set();return d.filter(p=>{const k=`${p.x}|${p.y}`;if(seen.has(k))return false;seen.add(k);return true})}
function cross(o,a,b){return(a.x-o.x)*(b.y-o.y)-(a.y-o.y)*(b.x-o.x)}
function convexHull(points){
  const p=uniquePoints(points).slice().sort((a,b)=>a.x-b.x||a.y-b.y);if(p.length<3)return p;
  const lo=[];for(const q of p){while(lo.length>=2&&cross(lo[lo.length-2],lo[lo.length-1],q)<=0)lo.pop();lo.push(q)}
  const hi=[];for(let i=p.length-1;i>=0;i--){const q=p[i];while(hi.length>=2&&cross(hi[hi.length-2],hi[hi.length-1],q)<=0)hi.pop();hi.push(q)}
  lo.pop();hi.pop();return lo.concat(hi);
}
function polygonArea(poly){let a=0;for(let i=0,j=poly.length-1;i<poly.length;j=i++)a+=(poly[j].x+poly[i].x)*(poly[j].y-poly[i].y);return Math.abs(a/2)}
function pointInPoly(x,y,poly){let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];const hit=((a.y>y)!==(b.y>y))&&(x<(b.x-a.x)*(y-a.y)/(b.y-a.y)+a.x);if(hit)inside=!inside}return inside}
function bounds(d){const xs=d.map(p=>p.x),ys=d.map(p=>p.y);return[Math.min(...xs),Math.max(...xs),Math.min(...ys),Math.max(...ys)]}
function idw(d,x,y){let nume=0,den=0;for(const p of d){const q=(x-p.x)**2+(y-p.y)**2;if(q<1e-12)return p.h;const w=1/q;nume+=w*p.h;den+=w}return den?nume/den:null}
function isoUpdate(){
  const d=isoData();['isoA','isoB'].forEach(id=>{const el=$(id);if(!el)return;const old=el.value;el.innerHTML=d.map((p,i)=>`<option value="${i}">${p.id}</option>`).join('');if([...el.options].some(o=>o.value===old))el.value=old});
  if(d.length>1&&$('isoB')&&!$('isoB').value)$('isoB').value='1';drawIso($('isoCanvas'),d,false);drawIso($('isoFlowCanvas'),d,true);
}
$('isoInterval')?.addEventListener('input',isoUpdate);$('isoShowPoints')?.addEventListener('change',isoUpdate);$('isoShowValues')?.addEventListener('change',isoUpdate);
$('isoCalc')?.addEventListener('click',()=>{
  const d=isoData(),a=d[num($('isoA')?.value)??0],b=d[num($('isoB')?.value)??1],v=num($('isoTarget')?.value);
  if(!a||!b||v===null||a.h===b.h){$('isoCalcOut').textContent='Dados insuficientes ou valores iguais.';return}
  const f=(v-a.h)/(b.h-a.h);if(f<0||f>1){$('isoCalcOut').textContent='O valor escolhido não está entre as cargas dos dois pontos. Não há cruzamento no segmento.';return}
  const px=a.x+f*(b.x-a.x),py=a.y+f*(b.y-a.y);$('isoCalcOut').textContent=`f = ${f.toFixed(3)} · posição interpolada X ${px.toFixed(2)} · Y ${py.toFixed(2)}`;drawInterp(a,b,{x:px,y:py},v);
});
function drawIso(c,d,flow){
  if(!c)return;const g=c.getContext('2d'),W=c.width,H=c.height,pad=62;g.clearRect(0,0,W,H);g.fillStyle='#fff';g.fillRect(0,0,W,H);
  const hull=convexHull(d);if(d.length<3||hull.length<3||polygonArea(hull)<1e-6){g.fillStyle='#607887';g.font='18px sans-serif';g.fillText('Informe ao menos 3 pontos válidos e não colineares.',pad,H/2);return}
  const [xmin,xmax,ymin,ymax]=bounds(hull);if(xmax===xmin||ymax===ymin)return;
  const nx=72,ny=48,vals=Array.from({length:ny+1},()=>Array(nx+1).fill(null));let mn=Infinity,mx=-Infinity;
  for(let j=0;j<=ny;j++)for(let i=0;i<=nx;i++){
    const X=xmin+(xmax-xmin)*i/nx,Y=ymin+(ymax-ymin)*j/ny;if(!pointInPoly(X,Y,hull)&&!hull.some(p=>Math.abs(p.x-X)<1e-9&&Math.abs(p.y-Y)<1e-9))continue;
    const z=idw(d,X,Y);vals[j][i]=z;if(z!==null){mn=Math.min(mn,z);mx=Math.max(mx,z)}
  }
  const interval=num($('isoInterval')?.value);if(interval===null||interval<=0){g.fillStyle='#b45309';g.font='18px sans-serif';g.fillText('Informe um intervalo de isopiezas maior que zero.',pad,H/2);return}
  const sx=i=>pad+i/nx*(W-2*pad),sy=j=>H-pad-j/ny*(H-2*pad);
  g.save();g.strokeStyle='#d5e4ec';g.lineWidth=1.5;g.beginPath();hull.forEach((p,k)=>{const i=(p.x-xmin)/(xmax-xmin)*nx,j=(p.y-ymin)/(ymax-ymin)*ny;k?g.lineTo(sx(i),sy(j)):g.moveTo(sx(i),sy(j))});g.closePath();g.stroke();g.restore();
  g.strokeStyle='#2d86c8';g.lineWidth=1.6;
  for(let level=Math.ceil(mn/interval)*interval;level<=mx+1e-9;level+=interval){
    for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){
      const z=[vals[j][i],vals[j][i+1],vals[j+1][i+1],vals[j+1][i]];if(z.some(v=>v===null))continue;
      const xy=[[i,j],[i+1,j],[i+1,j+1],[i,j+1]],crossings=[];
      for(let e=0;e<4;e++){const a=z[e],b=z[(e+1)%4];if(a===b)continue;if((a-level)*(b-level)<=0&&level>=Math.min(a,b)&&level<=Math.max(a,b)){const f=(level-a)/(b-a);if(f>=0&&f<=1){const A=xy[e],B=xy[(e+1)%4];crossings.push([A[0]+f*(B[0]-A[0]),A[1]+f*(B[1]-A[1])])}}}
      const uniq=[];crossings.forEach(q=>{if(!uniq.some(u=>Math.hypot(u[0]-q[0],u[1]-q[1])<1e-6))uniq.push(q)});
      const pairs=uniq.length===2?[[uniq[0],uniq[1]]]:uniq.length===4?[[uniq[0],uniq[1]],[uniq[2],uniq[3]]]:[];
      pairs.forEach(pair=>{g.beginPath();g.moveTo(sx(pair[0][0]),sy(pair[0][1]));g.lineTo(sx(pair[1][0]),sy(pair[1][1]));g.stroke()});
    }
  }
  if(flow){
    g.strokeStyle='#0b4f6c';g.fillStyle='#0b4f6c';const dx=(xmax-xmin)/nx,dy=(ymax-ymin)/ny;
    for(let j=7;j<ny;j+=10)for(let i=7;i<nx;i+=12){const X=xmin+(xmax-xmin)*i/nx,Y=ymin+(ymax-ymin)*j/ny;if(!pointInPoly(X,Y,hull))continue;const zxp=idw(d,X+dx,Y),zxm=idw(d,X-dx,Y),zyp=idw(d,X,Y+dy),zym=idw(d,X,Y-dy);if([zxp,zxm,zyp,zym].some(v=>v===null))continue;const gx=(zxp-zxm)/(2*dx),gy=(zyp-zym)/(2*dy),mag=Math.hypot(gx,gy)||1;const xx=sx(i),yy=sy(j),ux=-gx/mag,uy=-gy/mag,px=ux*24,py=-uy*24;g.beginPath();g.moveTo(xx,yy);g.lineTo(xx+px,yy+py);g.stroke();g.beginPath();g.arc(xx+px,yy+py,3,0,Math.PI*2);g.fill()}
  }
  if($('isoShowPoints')?.value!=='0'||flow){g.fillStyle='#075f91';g.font='bold 16px sans-serif';d.forEach(q=>{const i=(q.x-xmin)/(xmax-xmin)*nx,j=(q.y-ymin)/(ymax-ymin)*ny,xx=sx(i),yy=sy(j);g.beginPath();g.arc(xx,yy,6,0,Math.PI*2);g.fill();if($('isoShowValues')?.value!=='0')g.fillText(`${q.id} ${q.h.toFixed(1)}`,xx+9,yy-8)})}
  g.fillStyle='#607887';g.font='14px sans-serif';g.fillText('Pré-visualização IDW restrita ao envoltório convexo dos pontos válidos.',pad,H-18);
}
function drawInterp(a,b,q,v){const c=$('isoInterpCanvas');if(!c)return;const g=c.getContext('2d'),W=c.width,H=c.height,p=80;g.clearRect(0,0,W,H);g.strokeStyle='#456b7d';g.lineWidth=3;g.beginPath();g.moveTo(p,H/2);g.lineTo(W-p,H/2);g.stroke();const den=Math.hypot(b.x-a.x,b.y-a.y)||1,f=Math.hypot(q.x-a.x,q.y-a.y)/den,qx=p+f*(W-2*p);[[p,a.id,a.h],[W-p,b.id,b.h],[qx,'isolinha',v]].forEach((z,i)=>{g.fillStyle=i===2?'#075f91':'#173f55';g.beginPath();g.arc(z[0],H/2,9,0,Math.PI*2);g.fill();g.font='bold 18px sans-serif';g.fillText(`${z[1]} · ${Number(z[2]).toFixed(2)}`,z[0]-45,H/2-25)})}
function csvCell(v){const s=String(v??'');return /[",\n]/.test(s)?`"${s.replaceAll('"','""')}"`:s}
function download(name,text){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),500)}

granCalc();isoUpdate();
window.ITA_LAB_R10={version:'10.0',granCalc,isoUpdate};
})();
