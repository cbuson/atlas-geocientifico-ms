(function(){
 if(window.L){window.ITA_MAP_ENGINE='leaflet';return;}
 window.ITA_MAP_ENGINE='fallback';
 const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
 const normLL=v=>Array.isArray(v)?{lat:Number(v[0]),lng:Number(v[1])}:{lat:Number(v?.lat),lng:Number(v?.lng??v?.lon)};
 const merc=(lat,lon,z)=>{lat=clamp(Number(lat),-85.05112878,85.05112878);const scale=256*Math.pow(2,z),x=(Number(lon)+180)/360*scale,s=Math.sin(lat*Math.PI/180),y=(.5-Math.log((1+s)/(1-s))/(4*Math.PI))*scale;return{x,y,scale}};
 const inv=(x,y,z)=>{const scale=256*Math.pow(2,z),lng=x/scale*360-180,n=Math.PI-2*Math.PI*y/scale,lat=180/Math.PI*Math.atan(.5*(Math.exp(n)-Math.exp(-n)));return{lat,lng}};
 class FMap{
  constructor(id,o={}){this.el=document.getElementById(id);this.o=o;this.zoom=5;this.center={lat:-20.5,lng:-54.6};this.layers=new Set();this.handlers={};this.el?.addEventListener('click',e=>{const r=this.el.getBoundingClientRect(),ll=this.containerPointToLatLng([e.clientX-r.left,e.clientY-r.top]);this.fire('click',{latlng:ll})});}
  _size(){const r=this.el?.getBoundingClientRect?.()||{width:1000,height:700};return{w:Math.max(1,r.width||1000),h:Math.max(1,r.height||700)}}
  hasLayer(l){return this.layers.has(l)} addLayer(l){this.layers.add(l);l._map=this;return this} removeLayer(l){this.layers.delete(l);return this}
  on(es,fn){String(es).split(/\s+/).forEach(e=>(this.handlers[e]??=[]).push(fn));return this} fire(e,d={}){(this.handlers[e]||[]).forEach(fn=>{try{fn(d)}catch(_){}});return this}
  getZoom(){return this.zoom} getCenter(){return{...this.center}}
  setView(ll,z=this.zoom){this.center=normLL(ll);this.zoom=clamp(Number(z)||this.zoom,this.o.minZoom??2,this.o.maxZoom??19);this.fire('move');this.fire('zoom');return this}
  zoomIn(){return this.setView(this.center,this.zoom+1)} zoomOut(){return this.setView(this.center,this.zoom-1)}
  latLngToContainerPoint(ll){ll=normLL(ll);const s=this._size(),p=merc(ll.lat,ll.lng,this.zoom),c=merc(this.center.lat,this.center.lng,this.zoom);let dx=p.x-c.x;const world=p.scale;if(dx>world/2)dx-=world;if(dx<-world/2)dx+=world;return{x:s.w/2+dx,y:s.h/2+(p.y-c.y)}}
  containerPointToLatLng(pt){const s=this._size(),c=merc(this.center.lat,this.center.lng,this.zoom);return inv(c.x+(Number(pt[0]??pt.x)-s.w/2),c.y+(Number(pt[1]??pt.y)-s.h/2),this.zoom)}
  fitBounds(b){const sw=normLL(b._sw||b[0]||[-26.0,-58.0]),ne=normLL(b._ne||b[1]||[-17.0,-50.5]);this.center={lat:(sw.lat+ne.lat)/2,lng:(sw.lng+ne.lng)/2};const size=this._size();let chosen=this.o.minZoom??4;for(let z=this.o.maxZoom??19;z>=(this.o.minZoom??4);z--){const a=merc(sw.lat,sw.lng,z),q=merc(ne.lat,ne.lng,z);const ww=Math.abs(q.x-a.x),hh=Math.abs(a.y-q.y);if(ww<=size.w*.9&&hh<=size.h*.9){chosen=z;break}}this.zoom=chosen;this.fire('move');this.fire('zoom');return this}
  invalidateSize(){this.fire('resize');return this}
 }
 const simpleLayer=()=>({addTo(m){m.addLayer(this);return this}});
 window.L={
  map:(id,o)=>new FMap(id,o),
  tileLayer:(url,o)=>Object.assign(simpleLayer(),{url,o}),
  layerGroup:arr=>Object.assign(simpleLayer(),{layers:arr||[]}),
  latLngBounds:(sw,ne)=>({_sw:normLL(sw),_ne:normLL(ne)}),
  circle:(ll,o)=>Object.assign(simpleLayer(),{ll:normLL(ll),o}),
  circleMarker:(ll,o)=>Object.assign(simpleLayer(),{ll:normLL(ll),o})
 };
})();
