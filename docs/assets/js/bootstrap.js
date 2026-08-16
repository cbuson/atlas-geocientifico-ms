(function(){
  'use strict';

  async function loadLayer(id){
    const path=window.ITA_LOCAL_LAYER_FILES?.[id];
    if(!path || window.ATLAS_DATA?.[id])return window.ATLAS_DATA?.[id]||null;
    try{
      const response=await fetch(path,{cache:'default'});
      if(!response.ok)throw new Error(`HTTP ${response.status}`);
      const data=await response.json();
      window.ATLAS_DATA=window.ATLAS_DATA||{};
      window.ATLAS_DATA[id]=data;
      return data;
    }catch(error){
      console.warn(`ITA ARANDU MS · pré-carga opcional falhou · ${id}`,error);
      return null;
    }
  }

  function warmLocalLayers(){
    const ids=window.ITA_LOCAL_LAYER_PRELOAD||[];
    // A interface e o catálogo já foram inicializados por app.js.
    // Esta etapa é apenas aquecimento de cache e nunca bloqueia Camadas ou Dados.
    Promise.allSettled(ids.map(loadLayer)).then(results=>{
      const failed=results.filter(r=>r.status==='rejected').length;
      if(failed)console.warn(`ITA ARANDU MS · ${failed} pré-cargas opcionais não concluídas`);
    });
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',()=>setTimeout(warmLocalLayers,0),{once:true});
  }else{
    setTimeout(warmLocalLayers,0);
  }
})();
