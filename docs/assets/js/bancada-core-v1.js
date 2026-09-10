(()=>{
  'use strict';

  const VERSION='39.1.0';
  const GROUP_LABELS={
    estrutura:'Geologia estrutural',
    materiais:'Materiais geológicos',
    documentacao:'Documentação de campo',
    posicionamento:'Posicionamento',
    hidro:'Hidrogeologia',
    tempo:'Tempo geológico',
    geofisica:'Geofísica experimental'
  };
  const registry=[
    {id:'clinometro',title:'Clinômetro Visual ARANDU',group:'estrutura',modal:'clinometroAranduModal',method:'metodologia-clinometro-visual-arandu.html'},
    {id:'bussola',title:'Bússola geológica',group:'estrutura',modal:'bussolaAranduModal',method:'metodologia-bussola-geologica.html'},
    {id:'nivel',title:'Nível digital',group:'estrutura',modal:'nivelAranduModal',method:'metodologia-nivel-digital.html'},
    {id:'rede-estereografica',title:'Rede Estereográfica',group:'estrutura',modal:'estereogramaAranduModal',method:'metodologia-rede-estereografica.html'},
    {id:'calculadora-estrutural',title:'Calculadora estrutural',group:'estrutura',modal:'calculadoraEstruturalModal',method:'metodologia-calculadora-estrutural.html'},
    {id:'rosas',title:'Diagrama de Rosas',group:'estrutura',modal:'roseModal',method:'metodologia-diagrama-rosas.html'},
    {id:'ternario-usda',title:'Diagramas Ternários',group:'materiais',modal:'ternarioModal',method:'metodologia-ternario-usda.html'},
    {id:'granulometria',title:'Análise Granulométrica',group:'materiais',modal:'granulometriaModal',method:'metodologia-analise-granulometrica.html'},
    {id:'macrogeo',title:'MacroGeo',group:'documentacao',modal:'macroGeoModal',method:'metodologia-macrogeo.html'},
    {id:'geocamera',title:'GeoCâmera ARANDU',group:'documentacao',modal:'geocameraModal',method:'metodologia-ferramentas-geocientificas.html'},
    {id:'saida-campo',title:'Saída de Campo ARANDU',group:'documentacao',modal:'saidaCampoModal',method:'metodologia-saida-campo.html'},
    {id:'gps',title:'GPS · UTM · Waypoint',group:'posicionamento',modal:'gpsEducativoModal',method:'metodologia-cartografia-geologica.html'},
    {id:'isopiezas',title:'Interpolação gráfica · Isopiezas',group:'hidro',modal:'isopiezasModal',method:'metodologia-interpolacao-isopiezas.html'},
    {id:'tempo-geologico',title:'Colunas estratigráficas',group:'tempo',modal:'tempoModal',method:'metodologia-coluna-estratigrafica.html'},
    {id:'tempo-profundo',title:'Tempo Profundo',group:'tempo',modal:'paleoModal',method:'metodologia-ferramentas-geocientificas.html'},
    {id:'coluna-construtor',title:'Coluna Estratigráfica · Construtor',group:'tempo',modal:'colunaEstratigraficaModal',method:'metodologia-coluna-estratigrafica.html'},
    {id:'correlacao',title:'Correlação Estratigráfica · Multiponto',group:'tempo',modal:'correlacaoEstratigraficaModal',method:'metodologia-correlacao-estratigrafica.html'},
    {id:'magnetometro-amostras',title:'Magnetômetro · Amostras',group:'geofisica',modal:'magAmostrasModal',method:'metodologia-magnetometro-amostras.html'},
    {id:'magnetometro-mapa',title:'Magnetômetro · Mapa',group:'geofisica',modal:'magMapaModal',method:'metodologia-magnetometro-mapa.html'},
    {id:'ondas-sismicas',title:'Ondas sísmicas · Acelerômetro',group:'geofisica',modal:'ondasSismicasModal',method:'metodologia-ondas-sismicas-acelerometro.html'}
  ];

  const byModal=new Map(registry.map(item=>[item.modal,item]));
  let lastTrigger=null;
  let activeModal=null;
  let observerBusy=false;

  function visible(modal){
    if(!modal)return false;
    return modal.classList.contains('open')||modal.classList.contains('show')||modal.getAttribute('aria-hidden')==='false';
  }

  function focusables(root){
    return [...root.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')]
      .filter(el=>!el.hidden&&el.getClientRects().length);
  }

  function announce(text){
    let live=document.getElementById('itaBdLive');
    if(!live){
      live=document.createElement('div');
      live.id='itaBdLive';
      live.className='ita-bd-sr-status';
      live.setAttribute('aria-live','polite');
      document.body.appendChild(live);
    }
    live.textContent='';
    requestAnimationFrame(()=>{live.textContent=text});
  }

  function normalizeModal(modal,item){
    if(!modal||modal.dataset.itaBdReady==='true')return;
    modal.dataset.itaBdReady='true';
    modal.dataset.itaToolId=item.id;
    modal.dataset.itaToolGroup=item.group;
    modal.classList.add('ita-bancada-tool');
    modal.setAttribute('role','dialog');
    modal.setAttribute('aria-modal','true');
    if(!modal.hasAttribute('aria-hidden'))modal.setAttribute('aria-hidden','true');
    const title=modal.querySelector('h1,h2,h3');
    if(title){
      if(!title.id)title.id=`itaBdTitle-${item.id}`;
      modal.setAttribute('aria-labelledby',title.id);
    }else{
      modal.setAttribute('aria-label',item.title);
    }
    const box=modal.querySelector('.modal-box')||modal;
    box.classList.add('ita-bd-box');
    if(!box.hasAttribute('tabindex'))box.tabIndex=-1;
    const head=box.querySelector('.ita48-ternario-head,.modal-head,.ita-lab-head,.ce-head,.corr-head,.ita-ternario-header');
    if(head){
      head.classList.add('ita-bd-head');
      const titleBlock=head.querySelector(':scope > div:first-child')||head;
      let kicker=titleBlock.querySelector('.kicker,.corr-kicker,.ce-kicker');
      if(!kicker){
        kicker=document.createElement('div');
        kicker.className='kicker';
        titleBlock.prepend(kicker);
      }
      kicker.textContent=`BANCADA DIGITAL · ${GROUP_LABELS[item.group]||item.group}`;
      let actions=head.querySelector('.ita-tool-head-actions,.ita-lab-head-actions,.ita49-head-actions,.ce-head-actions,.corr-actions,.ita-bd-head-actions');
      const close=head.querySelector('.close-modal')||head.querySelector('[data-ce-close],[data-corr-close],[id$="Close"],[data-close]');
      if(!actions){
        actions=document.createElement('div');
        actions.className='ita-bd-head-actions';
        if(close)actions.appendChild(close);
        head.appendChild(actions);
      }else actions.classList.add('ita-bd-head-actions');
      let back=actions.querySelector('.ita-tool-back,[data-ita-bd-back]')||[...actions.querySelectorAll('button,a')].find(node=>/bancada/i.test(node.textContent||'')&&!node.classList.contains('close-modal'));
      if(!back){
        back=document.createElement('button');
        back.type='button';
        back.className='ita-tool-back';
        back.dataset.itaBdBack='true';
        back.textContent='Voltar à Bancada';
        actions.prepend(back);
      }
      if(close){
        close.classList.add('ita-bd-close');
        if(!close.getAttribute('aria-label'))close.setAttribute('aria-label',`Fechar ${item.title}`);
      }
      if(back.dataset.itaBdBound!=='true'){
        back.dataset.itaBdBound='true';
        back.addEventListener('click',event=>{
          event.preventDefault();
          event.stopPropagation();
          modal.classList.remove('open','show');
          modal.setAttribute('aria-hidden','true');
          const hub=document.getElementById('ferramentasModal');
          if(hub){
            hub.classList.add('open');
            hub.setAttribute('aria-hidden','false');
          }
        });
      }
    }
    const body=box.querySelector('.modal-body,.ita-lab-body,.ce-body,.corr-body,.ita-ternario-body');
    if(body)body.classList.add('ita-bd-body');
    box.querySelectorAll('.ita-calc-tabs,.ita-lab-tabs,.mm-tabs,.ita-seis-tabs,.ita-saida-tabs,.ita-rose-tabs,.ita-mag-tabs,.ita-ternario-tabs,.ce-tabs,.corr-tabs').forEach(node=>node.classList.add('ita-bd-tabs'));
  }

  function normalizeHub(){
    const hub=document.getElementById('ferramentasModal');
    if(!hub)return;
    hub.classList.add('ita-bancada-hub');
    hub.setAttribute('role','dialog');
    hub.setAttribute('aria-modal','true');
    const box=hub.querySelector('.modal-box');
    const head=box?.querySelector('.modal-head');
    const body=box?.querySelector('.modal-body');
    box?.classList.add('ita-bd-hub-box');
    head?.classList.add('ita-bd-hub-head');
    body?.classList.add('ita-bd-hub-body');
    const titleBlock=head?.querySelector(':scope > div:first-child');
    if(titleBlock&&!titleBlock.querySelector('.ita-bd-hub-badge')){
      const badge=document.createElement('span');
      badge.className='ita-bd-hub-badge';
      badge.textContent='SISTEMA COMUM V39.1';
      titleBlock.appendChild(badge);
    }
    const close=head?.querySelector('.close-modal');
    if(close){
      close.classList.add('ita-bd-close');
      if(!close.getAttribute('aria-label'))close.setAttribute('aria-label','Fechar Bancada Digital');
    }
    hub.querySelectorAll('.ita-tools-section').forEach(node=>node.classList.add('ita-bd-section'));
    hub.querySelectorAll('.ita-tool-card').forEach(card=>{
      card.classList.add('ita-bd-card');
      const actions=card.querySelector('.ita-tool-actions');
      actions?.querySelectorAll('button,a').forEach((action,index)=>{
        action.classList.add(index===0?'ita-bd-primary':'ita-bd-secondary');
      });
    });
  }

  function normalizeCard(item){
    const cards=[...document.querySelectorAll('.ita-tool-card')];
    const card=cards.find(node=>{
      const title=node.querySelector('h4')?.textContent?.trim()||'';
      return title===item.title||title.startsWith(item.title);
    });
    if(!card)return;
    card.dataset.itaToolId=item.id;
    card.dataset.itaToolGroup=item.group;
    card.dataset.itaMethod=item.method;
  }

  function scan(){
    normalizeHub();
    registry.forEach(item=>{
      normalizeCard(item);
      normalizeModal(document.getElementById(item.modal),item);
    });
  }

  function modalOpened(modal,item){
    activeModal=modal;
    document.body.classList.add('ita-bd-modal-open');
    modal.setAttribute('aria-hidden','false');
    const first=focusables(modal)[0]||modal.querySelector('.modal-box')||modal;
    requestAnimationFrame(()=>first.focus({preventScroll:true}));
    announce(`${item.title} aberta`);
  }

  function modalClosed(modal,item){
    modal.setAttribute('aria-hidden','true');
    if(activeModal===modal)activeModal=null;
    if(![...document.querySelectorAll('.ita-bancada-tool')].some(visible))document.body.classList.remove('ita-bd-modal-open');
    if(lastTrigger?.isConnected)requestAnimationFrame(()=>lastTrigger.focus({preventScroll:true}));
    announce(`${item.title} fechada`);
  }

  function observeModal(modal,item){
    if(modal.dataset.itaBdObserved==='true')return;
    modal.dataset.itaBdObserved='true';
    let wasOpen=visible(modal);
    const observer=new MutationObserver(()=>{
      const isOpen=visible(modal);
      if(isOpen===wasOpen)return;
      wasOpen=isOpen;
      if(isOpen)modalOpened(modal,item);
      else modalClosed(modal,item);
    });
    observer.observe(modal,{attributes:true,attributeFilter:['class','aria-hidden','hidden']});
  }

  function activateObservers(){
    registry.forEach(item=>{
      const modal=document.getElementById(item.modal);
      if(modal){normalizeModal(modal,item);observeModal(modal,item)}
    });
  }

  function closeActive(){
    if(!activeModal)return;
    const close=activeModal.querySelector('[data-close],[data-ce-close],[data-corr-close],.close-modal,[id$="Close"]');
    if(close)close.click();
    else{
      activeModal.classList.remove('open','show');
      activeModal.setAttribute('aria-hidden','true');
    }
  }

  function trapFocus(event){
    if(event.key!=='Tab'||!activeModal)return;
    const list=focusables(activeModal);
    if(!list.length){event.preventDefault();return}
    const first=list[0],last=list[list.length-1];
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
  }

  function audit(){
    return registry.map(item=>{
      const card=document.querySelector(`.ita-tool-card[data-ita-tool-id="${item.id}"]`);
      const modal=document.getElementById(item.modal);
      return {id:item.id,title:item.title,group:item.group,card:Boolean(card),modal:Boolean(modal),method:item.method};
    });
  }

  function register(item){
    const required=['id','title','group','modal','method'];
    const missing=required.filter(key=>!String(item?.[key]||'').trim());
    if(missing.length)throw new Error(`Bancada Digital · registro incompleto · ${missing.join(', ')}`);
    const existing=registry.find(tool=>tool.id===item.id||tool.modal===item.modal);
    if(existing)return existing;
    const normalized={
      id:String(item.id).trim(),
      title:String(item.title).trim(),
      group:String(item.group).trim(),
      modal:String(item.modal).trim(),
      method:String(item.method).trim()
    };
    registry.push(normalized);
    byModal.set(normalized.modal,normalized);
    scan();
    activateObservers();
    return normalized;
  }

  document.addEventListener('pointerdown',event=>{
    const trigger=event.target.closest('button,a,[data-tool-action]');
    if(trigger&&!trigger.closest('.ita-bancada-tool'))lastTrigger=trigger;
  },true);

  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&activeModal){event.preventDefault();closeActive();return}
    trapFocus(event);
  },true);

  document.addEventListener('DOMContentLoaded',()=>{
    document.title=document.title.replace(/V\d+(?:\.\d+){1,3}[A-Za-z-]*/i,`V${VERSION}`);
    document.querySelectorAll('.ita-version-badge').forEach(node=>{node.textContent=`V${VERSION}`});
    scan();
    activateObservers();
    const bodyObserver=new MutationObserver(()=>{
      if(observerBusy)return;
      observerBusy=true;
      requestAnimationFrame(()=>{scan();activateObservers();observerBusy=false});
    });
    bodyObserver.observe(document.body,{childList:true,subtree:true});
  });

  window.ITA_BANCADA={
    version:VERSION,
    get registry(){return registry.map(item=>Object.freeze({...item}))},
    register,
    scan,
    audit
  };
})();
