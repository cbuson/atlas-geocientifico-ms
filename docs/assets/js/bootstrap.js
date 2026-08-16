/* ITA ARANDU MS · bootstrap resiliente V38.4.37D
   A interface deve iniciar mesmo quando um GeoJSON local demora ou falha.
   Camadas são carregadas sob demanda por app.js.
*/
(async function(){
  async function loadScript(src,label){
    await new Promise((resolve,reject)=>{
      const script=document.createElement('script');
      script.src=src;
      script.async=false;
      script.onload=resolve;
      script.onerror=()=>reject(new Error(`Falha ao carregar ${label}`));
      document.body.appendChild(script);
    });
  }

  async function preloadLayer(id){
    try{
      if(window.ATLAS_DATA?.[id])return true;
      const path=window.ITA_LOCAL_LAYER_FILES?.[id];
      if(!path)return false;
      const response=await fetch(path,{cache:'default'});
      if(!response.ok)throw new Error(`HTTP ${response.status}`);
      const data=await response.json();
      window.ATLAS_DATA=window.ATLAS_DATA||{};
      window.ATLAS_DATA[id]=data;
      return true;
    }catch(error){
      console.warn(`ITA ARANDU MS · pré-carga não bloqueante falhou · ${id}`,error);
      return false;
    }
  }

  try{
    /* app.js primeiro. Ele monta Camadas, Dados e toda a navegação. */
    await loadScript('./assets/js/app.js?v=38.4.37d','app.js');
    await loadScript('./assets/js/campo-sensores.js?v=38.4.37d','campo-sensores.js');

    /* Pré-carga só depois do arranque e sem bloquear a aplicação. */
    const ids=window.ITA_LOCAL_LAYER_PRELOAD||[];
    Promise.allSettled(ids.map(preloadLayer)).then(results=>{
      const ok=results.filter(r=>r.status==='fulfilled'&&r.value===true).length;
      console.info(`ITA ARANDU MS · pré-carga local concluída · ${ok}/${ids.length}`);
    });
  }catch(error){
    console.error('ITA ARANDU MS · falha crítica de inicialização',error);
    const host=document.getElementById('map');
    if(host){
      const box=document.createElement('div');
      box.style.cssText='position:absolute;z-index:9999;left:16px;right:16px;top:16px;padding:14px;background:#fff3f3;border:1px solid #c66;border-radius:12px;color:#7a2020;font-family:system-ui';
      box.textContent='Não foi possível iniciar o motor principal do Atlas. Recarregue a página. Se o problema persistir, limpe o cache da aplicação.';
      host.appendChild(box);
    }
  }
})();
