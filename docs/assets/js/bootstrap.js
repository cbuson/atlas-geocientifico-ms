(async function(){
  async function loadLayer(id){
    const path=window.ITA_LOCAL_LAYER_FILES?.[id];
    if(!path)return null;
    const response=await fetch(path,{cache:"default"});
    if(!response.ok)throw new Error(`Falha ao carregar camada local ${id} · HTTP ${response.status}`);
    const data=await response.json();
    window.ATLAS_DATA[id]=data;
    return data;
  }
  const ids=window.ITA_LOCAL_LAYER_PRELOAD||[];
  await Promise.all(ids.map(id=>window.ATLAS_DATA[id]?Promise.resolve(window.ATLAS_DATA[id]):loadLayer(id)));
  async function loadScript(src,label){
    await new Promise((resolve,reject)=>{
      const script=document.createElement("script");
      script.src=src;
      script.async=false;
      script.onload=resolve;
      script.onerror=()=>reject(new Error(`Falha ao carregar ${label}`));
      document.body.appendChild(script);
    });
  }
  await loadScript("./assets/js/app.js?v=38.4.24","app.js");
  await loadScript("./assets/js/campo-sensores.js?v=38.4.24","campo-sensores.js");
})().catch(error=>{
  console.error("ITA ARANDU MS · falha no bootstrap",error);
  const host=document.getElementById("map");
  if(host){
    const box=document.createElement("div");
    box.style.cssText="position:absolute;z-index:9999;left:16px;right:16px;top:16px;padding:14px;background:#fff3f3;border:1px solid #c66;border-radius:12px;color:#7a2020;font-family:system-ui";
    box.textContent="Não foi possível carregar os arquivos locais do Atlas. Abra a aplicação pelo GitHub Pages ou por um servidor web.";
    host.appendChild(box);
  }
});
