/* SS permanent chat archive guard. Loaded after the provider console. */
(function(){
  const KEY='ss-permanent-chat-ids-v1';
  const map=JSON.parse(localStorage.getItem(KEY)||'{}');
  let current=map._default || ('chat-'+Date.now()+'-'+Math.random().toString(36).slice(2));
  function providerId(){try{return document.querySelector('.prov.active')?.id?.replace(/^p-/,'')||'default'}catch{return'default'}}
  function idFor(p){if(!map[p]) map[p]='chat-'+p+'-'+Date.now()+'-'+Math.random().toString(36).slice(2);return map[p]}
  current=idFor(providerId());
  function persist(){localStorage.setItem(KEY,JSON.stringify(map))}
  window.addEventListener('click',function(e){
    const b=e.target.closest('button'); if(!b)return;
    const t=(b.textContent||'').trim().toLowerCase();
    if(t==='new chat'){
      const p=providerId(); map[p]='chat-'+p+'-'+Date.now()+'-'+Math.random().toString(36).slice(2); current=map[p]; persist();
    } else if(b.classList.contains('prov')) { setTimeout(()=>{current=idFor(providerId());persist()},0); }
  },true);
  const originalFetch=window.fetch;
  window.fetch=async function(input,init){
    const response=await originalFetch(input,init);
    try{
      const url=typeof input==='string'?input:(input&&input.url)||'';
      if(url.endsWith('/api/chat') && init && init.body && response.ok){
        const request=JSON.parse(init.body); const copy=await response.clone().json();
        if(copy && copy.ok && request.messages){
          fetch('/api/chats',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:current,provider:request.provider,model:copy.model||request.model,messages:[...request.messages,{role:'assistant',content:copy.text||''}]})}).catch(()=>{});
        }
      }
    }catch(_e){}
    return response;
  };
  window.SSChatArchive={status:()=>fetch('/api/storage').then(r=>r.json()),newChat:()=>{const p=providerId();map[p]='chat-'+p+'-'+Date.now()+'-'+Math.random().toString(36).slice(2);current=map[p];persist();}};
})();
