from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime, timezone
import httpx,time,json,os,re,platform
try: import psutil
except ImportError: psutil=None
try: import keyring
except ImportError: keyring=None
VERSION='0.8.5'; APP=FastAPI(title='SS Second Brain',version=VERSION); ROOT=Path(__file__).parent; SERVICE='SS-Second-Brain'
PROVIDERS={'ollama':{'name':'Ollama','kind':'local','base':'http://127.0.0.1:11434','cap':'local','key':False},'lmstudio':{'name':'LM Studio / Bionic','kind':'local','base':'http://127.0.0.1:1234/v1','cap':'local','key':False},'jan':{'name':'Jan','kind':'local','base':'http://127.0.0.1:1337/v1','cap':'local','key':False},'openrouter':{'name':'OpenRouter · ZDR','kind':'cloud','base':'https://openrouter.ai/api/v1','cap':'gateway','key':True},'huggingface':{'name':'Hugging Face Inference','kind':'cloud','base':'https://router.huggingface.co/v1','cap':'gateway','key':True},'venice':{'name':'Venice AI','kind':'cloud','base':'https://api.venice.ai/api/v1','cap':'private','key':True},'openai':{'name':'OpenAI','kind':'cloud','base':'https://api.openai.com/v1','cap':'frontier','key':True},'anthropic':{'name':'Anthropic / Claude','kind':'cloud','base':'https://api.anthropic.com/v1','cap':'frontier','key':True},'google':{'name':'Google Gemini','kind':'cloud','base':'https://generativelanguage.googleapis.com/v1beta/openai','cap':'frontier','key':True},'xai':{'name':'xAI / Grok','kind':'cloud','base':'https://api.x.ai/v1','cap':'frontier','key':True},'deepseek':{'name':'DeepSeek','kind':'cloud','base':'https://api.deepseek.com/v1','cap':'reasoning','key':True},'mistral':{'name':'Mistral AI','kind':'cloud','base':'https://api.mistral.ai/v1','cap':'reasoning','key':True},'moonshot':{'name':'Moonshot / Kimi','kind':'cloud','base':'https://api.moonshot.ai/v1','cap':'reasoning','key':True},'zai':{'name':'Z.ai / GLM','kind':'cloud','base':'https://api.z.ai/api/paas/v4','cap':'reasoning','key':True},'qwen':{'name':'Qwen / Alibaba Model Studio','kind':'cloud','base':'https://dashscope-us.aliyuncs.com/compatible-mode/v1','cap':'reasoning','key':True},'perplexity':{'name':'Perplexity','kind':'cloud','base':'https://api.perplexity.ai/v1','cap':'research','key':True}}
CONNECTORS={'brave':{'name':'Brave Search API','kind':'search_api','status':'available','url':'https://api.search.brave.com/res/v1/web/search','key':True},'higgsfield':{'name':'Higgsfield MCP','kind':'mcp','status':'account_auth','url':'https://mcp.higgsfield.ai/mcp','key':False},'duckduckgo':{'name':'DuckDuckGo','kind':'web_search','status':'browser','url':'https://duckduckgo.com','key':False},'tor':{'name':'Tor Browser / proxy','kind':'privacy_transport','status':'manual','url':'https://www.torproject.org/download/','key':False},'huggingchat':{'name':'HuggingChat','kind':'web_ui','status':'browser','url':'https://huggingface.co/chat/','key':False},'metaai':{'name':'Meta AI','kind':'web_ui','status':'browser','url':'https://www.meta.ai/','key':False}}
OFFICIAL_SETUP={'openai':'https://platform.openai.com/api-keys','anthropic':'https://console.anthropic.com/settings/keys','google':'https://aistudio.google.com/app/apikey','xai':'https://console.x.ai/','deepseek':'https://platform.deepseek.com/api_keys','mistral':'https://console.mistral.ai/api-keys/','moonshot':'https://platform.moonshot.ai/console/api-keys','zai':'https://z.ai/manage-apikey/apikey-list','qwen':'https://bailian.console.alibabacloud.com/?tab=model#/api-key','perplexity':'https://www.perplexity.ai/settings/api','openrouter':'https://openrouter.ai/keys','huggingface':'https://huggingface.co/settings/tokens','venice':'https://venice.ai/settings/api','brave':'https://brave.com/search/api/','jan':'https://jan.ai/','lmstudio':'https://lmstudio.ai/'}
def data_root():
 base=Path(os.environ.get('LOCALAPPDATA',Path.home())) if os.name=='nt' else Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share')); p=base/'SS'/'data'
 for s in ('chats','memory','backups'):(p/s).mkdir(parents=True,exist_ok=True)
 return p
def cloud_root():
 v=os.environ.get('SS_CHAT_CLOUD_ROOT','').strip()
 if not v:return None
 p=Path(v).expanduser();p.mkdir(parents=True,exist_ok=True);return p
def safe(v):return (re.sub(r'[^A-Za-z0-9._-]+','_',str(v or 'chat'))[:140] or 'chat')
def atomic(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(t,p)
def save_chat(c):
 c=dict(c);now=datetime.now(timezone.utc).isoformat();c.setdefault('created_at',now);c['updated_at']=now;ts=[data_root()/'chats'/(safe(c['id'])+'.json')];cr=cloud_root()
 if cr:ts.append(cr/(safe(c['id'])+'.json'))
 for p in ts:atomic(p,c)
 return {'local':str(ts[0]),'cloud':str(ts[1]) if len(ts)>1 else None}
def load_chats():
 out=[]
 for p in sorted((data_root()/'chats').glob('*.json'),key=lambda x:x.stat().st_mtime,reverse=True):
  try:
   c=json.loads(p.read_text(encoding='utf-8'));out.append({'id':c.get('id',p.stem),'title':c.get('title','Untitled chat'),'updated_at':c.get('updated_at'),'provider':c.get('provider'),'model':c.get('model'),'messages':len(c.get('messages',[]))})
  except Exception:pass
 return out
def key_for(pid,supplied=None):
 if supplied:return supplied
 if keyring:
  try:return keyring.get_password(SERVICE,pid)
  except Exception:return None
 return None
async def req(url,method='GET',headers=None,payload=None,params=None):
 async with httpx.AsyncClient(timeout=120,follow_redirects=True) as c:
  r=await c.request(method,url,headers=headers,json=payload,params=params)
  try:d=r.json()
  except Exception:d={'raw':r.text}
  if r.status_code>=400:
   e=d.get('error') if isinstance(d,dict) else None;detail=e.get('message') if isinstance(e,dict) else e;raise RuntimeError(f'HTTP {r.status_code}: {detail or r.reason_phrase}')
  return d
def boundary(pid,e):
 s=str(e);name=PROVIDERS.get(pid,{'name':pid})['name']
 if any(x in s.lower() for x in ('connecterror','connecttimeout','connection refused','name or service not known')):return f'{name} is unreachable. SS stopped at this boundary; no silent provider switch.'
 if '401' in s or '403' in s:return f'{name} rejected the credential/permission. SS did not retry with another account.'
 if '429' in s:return f'{name} rate-limited the request. SS did not silently spend elsewhere.'
 return s
@APP.get('/',response_class=HTMLResponse)
async def root():return HTMLResponse((ROOT/'web'/'index.html').read_text(encoding='utf-8'))
@APP.get('/console',response_class=HTMLResponse)
@APP.get('/providers',response_class=HTMLResponse)
async def console():return HTMLResponse((ROOT/'web'/'providers.html').read_text(encoding='utf-8'))
@APP.get('/system')
async def system():return {'service':'SS Second Brain','version':VERSION,'status':'online','port':8765,'entry':'http://127.0.0.1:8765/','policy':{'auto_delete_chats':False,'silent_provider_fallback':False,'cloud_spend_without_request_approval':False},'storage':{'local':str(data_root()),'cloud':str(cloud_root()) if cloud_root() else None}}
@APP.get('/api/providers')
async def provider_list():return {'providers':PROVIDERS,'connectors':CONNECTORS,'official_setup':OFFICIAL_SETUP,'version':VERSION}
@APP.get('/api/resources')
async def resources():
 if not psutil:return {'ok':False,'error':'psutil unavailable'}
 v=psutil.virtual_memory();s=psutil.swap_memory();return {'ok':True,'ram_total_gb':round(v.total/2**30,2),'ram_available_gb':round(v.available/2**30,2),'ram_used_percent':v.percent,'swap_used_gb':round(s.used/2**30,2),'cpu_percent':psutil.cpu_percent(interval=.1),'platform':platform.platform()}
@APP.get('/api/storage')
async def storage():return {'local':str(data_root()),'cloud':str(cloud_root()) if cloud_root() else None,'never_delete':True,'archive':'external-to-code'}
@APP.get('/api/chats')
async def chats():return {'chats':load_chats(),'never_delete':True}
@APP.get('/api/chats/{cid}')
async def chat_get(cid:str):
 p=data_root()/'chats'/(safe(cid)+'.json')
 if not p.exists():return JSONResponse({'ok':False,'error':'Chat not found'},404)
 return json.loads(p.read_text(encoding='utf-8'))
@APP.post('/api/chats')
async def chat_save(body:dict):
 if not body.get('id') or not isinstance(body.get('messages'),list):return JSONResponse({'ok':False,'error':'id and messages required'},400)
 return {'ok':True,'saved':save_chat(body),'never_delete':True}
@APP.post('/api/memory')
async def memory_save(body:dict):p=data_root()/'memory'/(safe(body.get('key','memory'))+'.json');atomic(p,body);return {'ok':True,'path':str(p)}
@APP.get('/api/memory')
async def memory_list():
 out=[]
 for p in (data_root()/'memory').glob('*.json'):
  try:out.append(json.loads(p.read_text(encoding='utf-8')))
  except Exception:pass
 return {'memory':out}
@APP.get('/api/credentials/status')
async def credential_status():
 if not keyring:return {'available':False,'configured':{}}
 out={}
 for pid in list(PROVIDERS)+['brave']:
  try:out[pid]=bool(keyring.get_password(SERVICE,pid))
  except Exception:out[pid]=False
 return {'available':True,'configured':out,'backend':'OS credential store'}
@APP.post('/api/credentials')
async def credential_save(body:dict):
 pid=body.get('provider');k=body.get('apiKey')
 if pid not in PROVIDERS and pid!='brave':return JSONResponse({'ok':False,'error':'Unknown credential target'},400)
 if not keyring:return JSONResponse({'ok':False,'error':'OS credential store unavailable'},500)
 if not k:return JSONResponse({'ok':False,'error':'API key required'},400)
 keyring.set_password(SERVICE,pid,k);return {'ok':True,'stored':'OS credential store','provider':pid}
@APP.delete('/api/credentials/{pid}')
async def credential_delete(pid:str):
 if keyring:
  try:keyring.delete_password(SERVICE,pid)
  except Exception:pass
 return {'ok':True}
def model_meta(m):return {'id':m.get('id'),'detail':m.get('owned_by',''),'pricing':m.get('pricing'),'is_free':m.get('is_free',False),'context_length':m.get('context_length')} if isinstance(m,dict) else {}
def hf_free(m):
 if m.get('is_free') is True:return True
 ps=m.get('providers') or m.get('inference_providers') or []
 if isinstance(ps,dict):ps=list(ps.values())
 for p in ps if isinstance(ps,list) else []:
  if isinstance(p,dict) and p.get('is_free') is True:return True
  pr=p.get('pricing') if isinstance(p,dict) else None
  if isinstance(pr,dict) and float(pr.get('input',1) or 1)==0 and float(pr.get('output',1) or 1)==0:return True
 return False
@APP.post('/api/models')
async def models(body:dict):
 pid=body.get('provider');p=PROVIDERS.get(pid)
 if not p:return JSONResponse({'ok':False,'error':'Unknown provider'},400)
 base=(body.get('base') or p['base']).rstrip('/');k=key_for(pid,body.get('apiKey'))
 if p['key'] and not k:return JSONResponse({'ok':False,'error':f'{p["name"]} API key required'},400)
 try:
  start=time.perf_counter();h={'Authorization':f'Bearer {k}'} if k else {}
  if pid=='ollama':d=await req(base+'/api/tags',headers=h);ms=[{'id':m.get('name'),'detail':m.get('details',{}).get('parameter_size',''),'is_free':True} for m in d.get('models',[])]
  elif pid=='anthropic':ms=[{'id':x,'detail':'Anthropic Messages API'} for x in ['claude-opus-4-1','claude-sonnet-4-5','claude-haiku-4-5']]
  else:d=await req(base+'/models',headers=h);ms=[model_meta(m) for m in d.get('data',[])]
  ms=sorted([x for x in ms if x.get('id')],key=lambda x:x['id'].lower());return {'ok':True,'models':ms,'latency_ms':round((time.perf_counter()-start)*1000)}
 except Exception as e:return JSONResponse({'ok':False,'error':boundary(pid,e)},502)
@APP.post('/api/huggingface/catalog')
async def hf_catalog(body:dict):
 k=key_for('huggingface',body.get('apiKey'))
 if not k:return JSONResponse({'ok':False,'error':'Hugging Face inference token required'},400)
 try:
  d=await req('https://router.huggingface.co/v1/models',headers={'Authorization':f'Bearer {k}'})
  allm=sorted([model_meta(x) for x in d.get('data',[]) if x.get('id')],key=lambda x:x['id'].lower());free=sorted([m for m in allm if hf_free(m)],key=lambda x:x['id'].lower())
  starter_ids=['Qwen/Qwen3-8B','google/gemma-3-4b-it','meta-llama/Llama-3.1-8B-Instruct','meta-llama/Llama-3.2-3B-Instruct','openai/gpt-oss-20b','openai/gpt-oss-120b','deepseek-ai/DeepSeek-R1','deepseek-ai/DeepSeek-V3-0324','Qwen/Qwen2.5-7B-Instruct','mistralai/Mistral-7B-Instruct-v0.3'];starters=sorted([m for m in allm if m['id'] in starter_ids],key=lambda x:x['id'].lower())
  return {'ok':True,'free_now':free,'free_credit_starters':starters,'all':allm,'free_now_count':len(free),'monthly_free_credit_note':'HF currently documents $0.10/month for free users; this is a credit allowance, not a promise of permanently free models.'}
 except Exception as e:return JSONResponse({'ok':False,'error':boundary('huggingface',e)},502)
@APP.post('/api/health/provider')
async def provider_health(body:dict):return await models(body)
def classify(task):
 s=(task or '').lower();return {'privacy':any(x in s for x in ('private','confidential','local file','personal','sensitive','secret','my documents','offline')),'research':any(x in s for x in ('research','latest','web search','sources','news','look up','current')),'coding':any(x in s for x in ('code','program','debug','github','python','javascript','typescript','api')),'high_complexity':any(x in s for x in ('deep','complex','architecture','reason','analyse','analyze','legal','scientific','compare','design')) or len(s)>900}
@APP.post('/api/route')
async def route(body:dict):
 c=classify(body.get('task',''))
 if c['privacy']:a=['ollama','jan','lmstudio','venice','openrouter','huggingface']
 elif c['research']:a=['perplexity','openrouter','huggingface','deepseek','google','openai']
 elif c['coding']:a=['anthropic','openai','deepseek','qwen','openrouter','huggingface','ollama','jan']
 elif c['high_complexity']:a=['openai','anthropic','google','deepseek','openrouter','huggingface','ollama','jan']
 else:a=['ollama','jan','lmstudio','openrouter','huggingface','deepseek','google','openai']
 a=[p for p in a if PROVIDERS[p]['kind']=='local' or key_for(p)];return {'privacy':c['privacy'],'research':c['research'],'coding':c['coding'],'high_complexity':c['high_complexity'],'candidates':a,'policy':'Privacy prefers local. Cloud requires explicit approval. SS never crosses a failed privacy boundary silently.'}
def pick_model(pid,ms):
 names=[m.get('id') for m in ms if m.get('id')];prefs={'ollama':['qwen3','gemma3','llama3.2','phi4-mini'],'jan':['qwen','gemma','llama'],'lmstudio':['qwen','gemma','llama'],'deepseek':['DeepSeek-V3','DeepSeek-R1'],'anthropic':['claude-sonnet','claude-opus','claude-haiku'],'openai':['gpt-5','gpt-4.1','gpt-4o'],'google':['gemini-2.5-pro','gemini-2.5-flash','gemini-3'],'xai':['grok-4','grok-3'],'qwen':['qwen3','qwen2.5'],'zai':['glm-5','glm-4.5'],'mistral':['mistral-large','mistral-small'],'moonshot':['kimi'],'venice':['llama','qwen','deepseek'],'openrouter':['openai/gpt-5','anthropic/claude','google/gemini','deepseek'],'huggingface':['openai/gpt-oss-120b','deepseek-ai/DeepSeek-V3-0324','Qwen/Qwen3-8B']}.get(pid,[])
 for pref in prefs:
  for n in names:
   if pref.lower() in n.lower():return n
 return sorted(names,key=str.lower)[0] if names else None
@APP.post('/api/auto-chat')
async def auto_chat(body:dict):
 task=body.get('task','');messages=body.get('messages') or [{'role':'user','content':task}];approved=bool(body.get('cloud_approved'));r=await route({'task':task});attempts=[]
 for pid in r['candidates']:
  if PROVIDERS[pid]['kind']=='cloud' and not approved:continue
  try:
   mr=await models({'provider':pid})
   if not mr.get('ok') or not mr.get('models'):continue
   result=await chat({'provider':pid,'model':pick_model(pid,mr['models']),'messages':messages,'cloud_approved':approved,'zdr':pid=='openrouter'})
   if isinstance(result,JSONResponse):continue
   return result
  except Exception as e:attempts.append({'provider':pid,'error':boundary(pid,e)})
 return JSONResponse({'ok':False,'error':'No eligible working provider under the current privacy/cloud policy.','attempts':attempts,'candidates':r['candidates']},502)
@APP.post('/api/chat')
async def chat(body:dict):
 pid=body.get('provider');p=PROVIDERS.get(pid)
 if not p:return JSONResponse({'ok':False,'error':'Unknown provider'},400)
 if p['kind']=='cloud' and not body.get('cloud_approved'):return JSONResponse({'ok':False,'error':'Cloud request not approved for this turn. Enable cloud approval.'},403)
 k=key_for(pid,body.get('apiKey'));base=(body.get('base') or p['base']).rstrip('/');model=body.get('model');messages=body.get('messages') or []
 if not model:return JSONResponse({'ok':False,'error':'Model required'},400)
 if p['key'] and not k:return JSONResponse({'ok':False,'error':f'{p["name"]} API key required'},400)
 try:
  start=time.perf_counter()
  if pid=='anthropic':
   h={'x-api-key':k,'anthropic-version':'2023-06-01','content-type':'application/json'};sys='';mm=[]
   for m in messages:
    if m.get('role')=='system':sys+=str(m.get('content',''))+'\n'
    else:mm.append({'role':m.get('role'),'content':m.get('content','')})
   pl={'model':model,'max_tokens':2048,'messages':mm};pl['system']=sys if sys else pl.get('system');d=await req(base+'/messages','POST',h,pl);text=''.join(x.get('text','') for x in d.get('content',[]) if isinstance(x,dict))
  else:
   h={'Authorization':f'Bearer {k}','Content-Type':'application/json'} if k else {'Content-Type':'application/json'};pl={'model':model,'messages':messages,'temperature':body.get('temperature',.7),'stream':False}
   if pid=='openrouter' and body.get('zdr'):pl['provider']={'data_collection':'deny'}
   d=await req(base+'/chat/completions','POST',h,pl);text=((d.get('choices') or [{}])[0].get('message') or {}).get('content','')
  result={'ok':True,'text':text,'provider':pid,'model':model,'latency_ms':round((time.perf_counter()-start)*1000)};cid=body.get('chat_id')
  if cid:save_chat({'id':cid,'title':body.get('title') or (str(messages[0].get('content',''))[:70] if messages else 'SS chat'),'provider':pid,'model':model,'messages':list(messages)+[{'role':'assistant','content':text}]})
  return result
 except Exception as e:return JSONResponse({'ok':False,'error':boundary(pid,e)},502)
@APP.post('/api/search')
async def search(body:dict):
 k=key_for('brave',body.get('apiKey'));q=body.get('query','').strip()
 if not k:return JSONResponse({'ok':False,'error':'Brave Search API key required'},400)
 try:
  d=await req('https://api.search.brave.com/res/v1/web/search',headers={'X-Subscription-Token':k,'Accept':'application/json'},params={'q':q,'count':10});return {'ok':True,'results':[{'title':x.get('title'),'url':x.get('url'),'description':x.get('description')} for x in d.get('web',{}).get('results',[])]}
 except Exception as e:return JSONResponse({'ok':False,'error':boundary('brave',e)},502)
if __name__=='__main__':
 import uvicorn;uvicorn.run(APP,host='127.0.0.1',port=8765)
