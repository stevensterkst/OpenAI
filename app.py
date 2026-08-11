from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import httpx,time,json,os,re
from datetime import datetime,timezone
app=FastAPI(title="SS Second Brain",version="0.8.2")
# DATA SAFETY: chat data lives outside the repository and is never deleted by version updates.
def data_root():
    root=(Path(os.environ.get("LOCALAPPDATA",Path.home()))/"SS"/"chats") if os.name=="nt" else (Path(os.environ.get("XDG_DATA_HOME",Path.home()/".local/share"))/"SS"/"chats")
    root.mkdir(parents=True,exist_ok=True);return root
def cloud_root():
    v=os.environ.get("SS_CHAT_CLOUD_ROOT","").strip()
    if not v:return None
    p=Path(v).expanduser();p.mkdir(parents=True,exist_ok=True);return p
def safe_id(v):return (re.sub(r"[^A-Za-z0-9._-]+","_",str(v or "chat"))[:120] or "chat")
def write_chat(c):
    c=dict(c);c.setdefault("created_at",datetime.now(timezone.utc).isoformat());c["updated_at"]=datetime.now(timezone.utc).isoformat();payload=json.dumps(c,ensure_ascii=False,indent=2);targets=[data_root()/f"{safe_id(c['id'])}.json"];cr=cloud_root();targets += [cr/f"{safe_id(c['id'])}.json"] if cr else []
    for p in targets:
        p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(payload,encoding='utf-8');os.replace(tmp,p)
    return {"local":str(targets[0]),"cloud":str(targets[1]) if len(targets)>1 else None}
PROVIDERS={
"ollama":{"name":"Ollama","kind":"local","base":"http://127.0.0.1:11434"},"lmstudio":{"name":"LM Studio / Bionic","kind":"local","base":"http://127.0.0.1:1234/v1"},"jan":{"name":"Jan","kind":"local","base":"http://127.0.0.1:1337/v1"},"openrouter":{"name":"OpenRouter · ZDR","kind":"cloud-zdr","base":"https://openrouter.ai/api/v1"},"venice":{"name":"Venice AI","kind":"cloud-private","base":"https://api.venice.ai/api/v1"},"openai":{"name":"OpenAI","kind":"cloud-api","base":"https://api.openai.com/v1"},"anthropic":{"name":"Anthropic / Claude","kind":"cloud-api","base":"https://api.anthropic.com/v1"},"google":{"name":"Google Gemini","kind":"cloud-api","base":"https://generativelanguage.googleapis.com/v1beta/openai"},"xai":{"name":"xAI / Grok","kind":"cloud-api","base":"https://api.x.ai/v1"},"deepseek":{"name":"DeepSeek","kind":"cloud-api","base":"https://api.deepseek.com/v1"},"mistral":{"name":"Mistral AI","kind":"cloud-api","base":"https://api.mistral.ai/v1"},"moonshot":{"name":"Moonshot / Kimi","kind":"cloud-api","base":"https://api.moonshot.ai/v1"}}
@app.get("/",response_class=HTMLResponse)
async def home():return HTMLResponse((Path(__file__).parent/"web"/"index.html").read_text())
@app.get("/providers",response_class=HTMLResponse)
async def providers():return HTMLResponse((Path(__file__).parent/"web"/"providers.html").read_text())
@app.get("/system")
async def system():return {"service":"SS Second Brain","version":"0.8.2","status":"online","provider_count":len(PROVIDERS),"chat_persistence":{"local":str(data_root()),"cloud":str(cloud_root()) if cloud_root() else None,"deletion_policy":"NEVER"}}
@app.get("/api/providers")
async def provider_list():return {"providers":PROVIDERS}
@app.get("/api/storage")
async def storage():return {"local":str(data_root()),"cloud":str(cloud_root()) if cloud_root() else None,"never_delete":True}
@app.get("/api/chats/{chat_id}")
async def get_chat(chat_id:str):
    for p in [data_root()/f"{safe_id(chat_id)}.json"]+([cloud_root()/f"{safe_id(chat_id)}.json"] if cloud_root() else []):
        if p.exists():return json.loads(p.read_text(encoding='utf-8'))
    return JSONResponse({"ok":False,"error":"Chat not found"},404)
@app.post("/api/chats")
async def save_chat(body:dict):
    if not body.get('id') or not isinstance(body.get('messages'),list):return JSONResponse({"ok":False,"error":"id and messages required"},400)
    return {"ok":True,"saved":write_chat(body),"deletion_policy":"NEVER"}
async def req(url,method='GET',headers=None,payload=None):
    async with httpx.AsyncClient(timeout=120,follow_redirects=True) as c:
        r=await c.request(method,url,headers=headers,json=payload);r.raise_for_status();return r.json()
def boundary(pid,e):
    s=str(e)
    if isinstance(e,(httpx.ConnectError,httpx.ConnectTimeout)) or 'ConnectError' in s:return f"{PROVIDERS[pid]['name']} is unreachable. Check its API server/endpoint. SS stopped at this provider boundary and did not silently switch engines."
    if '401' in s or '403' in s:return f"{PROVIDERS[pid]['name']} rejected the credentials. Check the API key."
    if '429' in s:return f"{PROVIDERS[pid]['name']} rate-limited the request."
    return s
@app.post('/api/models')
async def models(b:dict):
    pid=b.get('provider');p=PROVIDERS.get(pid)
    if not p:return JSONResponse({'ok':False,'error':'Unknown provider'},400)
    key=b.get('apiKey');base=(b.get('base') or p['base']).rstrip('/')
    if p['kind'].startswith('cloud') and not key:return JSONResponse({'ok':False,'error':'API key required'},400)
    try:
        h={'Authorization':f'Bearer {key}'} if key else {};t=time.perf_counter()
        if pid=='ollama':
            d=await req(base+'/api/tags',headers=h);ms=[{'id':x['name'],'size':x.get('size'),'parameter_size':x.get('details',{}).get('parameter_size','')} for x in d.get('models',[])]
        elif pid=='anthropic':ms=[{'id':x,'owner':'Anthropic'} for x in ['claude-sonnet-4-5','claude-opus-4-1','claude-haiku-4-5']]
        else:
            d=await req(base+'/models',headers=h);ms=[{'id':x['id'],'owner':x.get('owned_by','')} for x in d.get('data',[])]
        return {'ok':True,'models':ms,'latency_ms':round((time.perf_counter()-t)*1000)}
    except Exception as e:return JSONResponse({'ok':False,'error':boundary(pid,e)},502)
@app.post('/api/health/provider')
async def health(b:dict):
    d=await models(b)
    return d if isinstance(d,JSONResponse) else {'ok':True,'provider':b.get('provider'),'status':'READY','model_count':len(d['models']),'latency_ms':d['latency_ms']}
@app.post('/api/route')
async def route(b:dict):
    t=(b.get('task') or '').lower();c=list(PROVIDERS)
    if any(x in t for x in ('private','confidential','local','offline')):c=['ollama','lmstudio','jan','venice','openrouter']
    elif any(x in t for x in ('research','current','web','search','latest')):c=['openrouter','google','openai','xai','venice','mistral','ollama']
    elif any(x in t for x in ('uncensored','unrestricted','creative','roleplay')):c=['venice','ollama','lmstudio','jan','openrouter','deepseek','moonshot']
    elif any(x in t for x in ('code','program','debug','software')):c=['deepseek','openai','anthropic','mistral','ollama']
    return {'ok':True,'task':b.get('task',''),'candidates':c,'policy':'transparent heuristic; availability, privacy and model fit must be checked before execution'}
@app.post('/api/chat')
async def chat(b:dict):
    pid=b.get('provider');p=PROVIDERS.get(pid)
    if not p:return JSONResponse({'ok':False,'error':'Unknown provider'},400)
    key=b.get('apiKey');model=b.get('model');base=(b.get('base') or p['base']).rstrip('/');messages=b.get('messages',[]);temp=b.get('temperature',.7)
    if not model:return JSONResponse({'ok':False,'error':'Model required'},400)
    if p['kind'].startswith('cloud') and not key:return JSONResponse({'ok':False,'error':'API key required'},400)
    try:
        t=time.perf_counter()
        if pid=='anthropic':
            h={'x-api-key':key,'anthropic-version':'2023-06-01','Content-Type':'application/json'};sys=[];msgs=[]
            for m in messages:(sys.append(m.get('content','')) if m.get('role')=='system' else msgs.append({'role':m.get('role','user'),'content':m.get('content','')}))
            q={'model':model,'max_tokens':4096,'temperature':temp,'messages':msgs};q['system']='\n'.join(sys) if sys else None;q={k:v for k,v in q.items() if v is not None};d=await req(base+'/messages','POST',h,q);text=''.join(x.get('text','') for x in d.get('content',[]) if x.get('type')=='text');used=d.get('model',model)
        elif pid=='ollama':
            d=await req(base+'/api/chat','POST',{'Authorization':f'Bearer {key}'} if key else {},{'model':model,'messages':messages,'stream':False,'options':{'temperature':temp}});text=d.get('message',{}).get('content','');used=d.get('model',model)
        else:
            h={'Authorization':f'Bearer {key}'} if key else {};extra={'provider':{'zdr':True,'data_collection':'deny','allow_fallbacks':True}} if pid=='openrouter' and b.get('zdr',True) else {};d=await req(base+'/chat/completions','POST',h,{'model':model,'messages':messages,'temperature':temp,**extra});text=d.get('choices',[{}])[0].get('message',{}).get('content','');used=d.get('model',model)
        out={'ok':True,'text':text,'provider':pid,'model':used,'usage':d.get('usage'),'latency_ms':round((time.perf_counter()-t)*1000)}
        if b.get('chat_id'):out['persistence']=write_chat({'id':b['chat_id'],'provider':pid,'model':used,'messages':messages+[{'role':'assistant','content':text}]})
        return out
    except Exception as e:return JSONResponse({'ok':False,'error':boundary(pid,e),'provider':pid},502)
