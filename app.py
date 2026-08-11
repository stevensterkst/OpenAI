from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime, timezone
import httpx, time, json, os, re, platform

try:
    import psutil
except ImportError:
    psutil = None
try:
    import keyring
except ImportError:
    keyring = None

VERSION = "0.8.4"
APP = FastAPI(title="SS Second Brain", version=VERSION)
ROOT = Path(__file__).parent
SERVICE = "SS-Second-Brain"

PROVIDERS = {
    "ollama":{"name":"Ollama","kind":"local","base":"http://127.0.0.1:11434","cap":"local","key":False},
    "lmstudio":{"name":"LM Studio / Bionic","kind":"local","base":"http://127.0.0.1:1234/v1","cap":"local","key":False},
    "jan":{"name":"Jan","kind":"local","base":"http://127.0.0.1:1337/v1","cap":"local","key":False},
    "openrouter":{"name":"OpenRouter · ZDR","kind":"cloud","base":"https://openrouter.ai/api/v1","cap":"gateway","key":True},
    "huggingface":{"name":"Hugging Face Inference","kind":"cloud","base":"https://router.huggingface.co/v1","cap":"gateway","key":True},
    "venice":{"name":"Venice AI","kind":"cloud","base":"https://api.venice.ai/api/v1","cap":"private","key":True},
    "openai":{"name":"OpenAI","kind":"cloud","base":"https://api.openai.com/v1","cap":"frontier","key":True},
    "anthropic":{"name":"Anthropic / Claude","kind":"cloud","base":"https://api.anthropic.com/v1","cap":"frontier","key":True},
    "google":{"name":"Google Gemini","kind":"cloud","base":"https://generativelanguage.googleapis.com/v1beta/openai","cap":"frontier","key":True},
    "xai":{"name":"xAI / Grok","kind":"cloud","base":"https://api.x.ai/v1","cap":"frontier","key":True},
    "deepseek":{"name":"DeepSeek","kind":"cloud","base":"https://api.deepseek.com/v1","cap":"reasoning","key":True},
    "mistral":{"name":"Mistral AI","kind":"cloud","base":"https://api.mistral.ai/v1","cap":"reasoning","key":True},
    "moonshot":{"name":"Moonshot / Kimi","kind":"cloud","base":"https://api.moonshot.ai/v1","cap":"reasoning","key":True},
    "zai":{"name":"Z.ai / GLM","kind":"cloud","base":"https://api.z.ai/api/paas/v4","cap":"reasoning","key":True},
    "qwen":{"name":"Qwen / Alibaba Model Studio","kind":"cloud","base":"https://dashscope-us.aliyuncs.com/compatible-mode/v1","cap":"reasoning","key":True},
    "perplexity":{"name":"Perplexity","kind":"cloud","base":"https://api.perplexity.ai","cap":"research","key":True},
}
CONNECTORS = {
    "brave":{"name":"Brave Search API","kind":"search_api","status":"available","url":"https://api.search.brave.com/res/v1/web/search","key":True},
    "higgsfield":{"name":"Higgsfield MCP","kind":"mcp","status":"account_auth","url":"https://mcp.higgsfield.ai/mcp","key":False,"note":"Higgsfield agent access is currently via MCP/CLI, not a normal API-key endpoint."},
    "duckduckgo":{"name":"DuckDuckGo","kind":"web_search","status":"browser","url":"https://duckduckgo.com","key":False,"note":"SS does not invent a general DuckDuckGo web-search API; this is a browser/search connector."},
    "tor":{"name":"Tor Browser / proxy","kind":"privacy_transport","status":"manual","url":"https://www.torproject.org/download/","key":False,"note":"Tor is a transport layer, not an AI API. SS reports it only when a local proxy is actually configured."},
    "huggingchat":{"name":"HuggingChat / HF Chat UI","kind":"web_ui","status":"browser","url":"https://huggingface.co/chat/","key":False,"note":"Programmatic model access is through Hugging Face Inference Providers."},
    "metaai":{"name":"Meta AI","kind":"web_ui","status":"browser","url":"https://www.meta.ai/","key":False,"note":"No public consumer Meta AI chat API is assumed; SS does not fabricate one."},
}
OFFICIAL_SETUP = {
    "openai":"https://platform.openai.com/api-keys","anthropic":"https://console.anthropic.com/settings/keys","google":"https://aistudio.google.com/app/apikey","xai":"https://console.x.ai/","deepseek":"https://platform.deepseek.com/api_keys","mistral":"https://console.mistral.ai/api-keys/","moonshot":"https://platform.moonshot.ai/console/api-keys","zai":"https://z.ai/manage-apikey/apikey-list","qwen":"https://bailian.console.alibabacloud.com/?tab=model#/api-key","perplexity":"https://www.perplexity.ai/settings/api","openrouter":"https://openrouter.ai/keys","huggingface":"https://huggingface.co/settings/tokens","venice":"https://venice.ai/settings/api","brave":"https://brave.com/search/api/","jan":"https://jan.ai/","lmstudio":"https://lmstudio.ai/"}

def data_root():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) if os.name == "nt" else Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))
    p = base / "SS" / "data"
    for sub in ("chats","memory","backups"):
        (p/sub).mkdir(parents=True, exist_ok=True)
    return p

def cloud_root():
    v=os.environ.get("SS_CHAT_CLOUD_ROOT","").strip()
    if not v:return None
    p=Path(v).expanduser();p.mkdir(parents=True,exist_ok=True);return p

def safe(v):return (re.sub(r"[^A-Za-z0-9._-]+","_",str(v or "chat"))[:140] or "chat")

def write_json_atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8");os.replace(tmp,path)

def save_chat(chat):
    chat=dict(chat);now=datetime.now(timezone.utc).isoformat();chat.setdefault("created_at",now);chat["updated_at"]=now
    targets=[data_root()/"chats"/(safe(chat["id"])+".json")];cr=cloud_root()
    if cr:targets.append(cr/(safe(chat["id"])+".json"))
    for t in targets:write_json_atomic(t,chat)
    return {"local":str(targets[0]),"cloud":str(targets[1]) if len(targets)>1 else None}

def load_chats():
    out=[]
    for p in sorted((data_root()/"chats").glob("*.json"),key=lambda x:x.stat().st_mtime,reverse=True):
        try:
            c=json.loads(p.read_text(encoding="utf-8"));out.append({"id":c.get("id",p.stem),"title":c.get("title","Untitled chat"),"updated_at":c.get("updated_at"),"provider":c.get("provider"),"model":c.get("model"),"messages":len(c.get("messages",[]))})
        except Exception:pass
    return out

def key_for(pid,supplied=None):
    if supplied:return supplied
    if keyring:
        try:return keyring.get_password(SERVICE,pid)
        except Exception:return None
    return None

async def req(url,method="GET",headers=None,payload=None,params=None):
    async with httpx.AsyncClient(timeout=120,follow_redirects=True) as c:
        r=await c.request(method,url,headers=headers,json=payload,params=params)
        try:d=r.json()
        except Exception:d={"raw":r.text}
        if r.status_code>=400:
            e=d.get("error") if isinstance(d,dict) else None
            detail=e.get("message") if isinstance(e,dict) else e
            raise RuntimeError(f"HTTP {r.status_code}: {detail or r.reason_phrase}")
        return d

def boundary(pid,exc):
    s=str(exc);name=PROVIDERS.get(pid,CONNECTORS.get(pid,{"name":pid})).get("name",pid)
    if any(x in s.lower() for x in ["connecterror","connecttimeout","connection refused","fetch failed","name or service not known"]):return f"{name} is unreachable. SS stopped at this provider boundary; it did not silently switch engines."
    if "401" in s or "403" in s:return f"{name} rejected the credential. SS did not retry with another account or spend elsewhere."
    if "429" in s:return f"{name} rate-limited the request. SS did not silently switch providers."
    return s

@APP.get("/",response_class=HTMLResponse)
async def root():return HTMLResponse((ROOT/"web"/"index.html").read_text(encoding="utf-8"))
@APP.get("/console",response_class=HTMLResponse)
@APP.get("/providers",response_class=HTMLResponse)
async def console():return HTMLResponse((ROOT/"web"/"providers.html").read_text(encoding="utf-8"))
@APP.get("/system")
async def system():return {"service":"SS Second Brain","version":VERSION,"status":"online","port":8765,"entry":"http://127.0.0.1:8765/","policy":{"auto_delete_chats":False,"silent_provider_fallback":False,"cloud_spend_without_request_approval":False},"storage":{"local":str(data_root()),"cloud":str(cloud_root()) if cloud_root() else None}}
@APP.get("/api/providers")
async def provider_list():return {"providers":PROVIDERS,"connectors":CONNECTORS,"official_setup":OFFICIAL_SETUP}
@APP.get("/api/resources")
async def resources():
    if not psutil:return {"ok":False,"error":"psutil unavailable"}
    v=psutil.virtual_memory();s=psutil.swap_memory();return {"ok":True,"ram_total_gb":round(v.total/2**30,2),"ram_available_gb":round(v.available/2**30,2),"ram_used_percent":v.percent,"swap_used_gb":round(s.used/2**30,2),"cpu_percent":psutil.cpu_percent(interval=.1),"platform":platform.platform()}
@APP.get("/api/storage")
async def storage():return {"local":str(data_root()),"cloud":str(cloud_root()) if cloud_root() else None,"never_delete":True,"archive":"external-to-code"}
@APP.get("/api/chats")
async def chats():return {"chats":load_chats(),"never_delete":True}
@APP.get("/api/chats/{cid}")
async def chat_get(cid:str):
    p=data_root()/"chats"/(safe(cid)+".json")
    if not p.exists():return JSONResponse({"ok":False,"error":"Chat not found"},404)
    return json.loads(p.read_text(encoding="utf-8"))
@APP.post("/api/chats")
async def chat_save(body:dict):
    if not body.get("id") or not isinstance(body.get("messages"),list):return JSONResponse({"ok":False,"error":"id and messages required"},400)
    return {"ok":True,"saved":save_chat(body),"never_delete":True}
@APP.post("/api/memory")
async def memory_save(body:dict):
    key=safe(body.get("key","memory"));p=data_root()/"memory"/(key+".json");write_json_atomic(p,body);return {"ok":True,"path":str(p)}
@APP.get("/api/memory")
async def memory_list():
    out=[]
    for p in (data_root()/"memory").glob("*.json"):
        try:out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:pass
    return {"memory":out}
@APP.get("/api/credentials/status")
async def credential_status():
    if not keyring:return {"available":False,"configured":{}}
    out={}
    for pid in list(PROVIDERS)+["brave"]:
        try:out[pid]=bool(keyring.get_password(SERVICE,pid))
        except Exception:out[pid]=False
    return {"available":True,"configured":out,"backend":"OS credential store"}
@APP.post("/api/credentials")
async def credential_save(body:dict):
    pid=body.get("provider");key=body.get("apiKey")
    if pid not in PROVIDERS and pid!="brave":return JSONResponse({"ok":False,"error":"Unknown credential target"},400)
    if not keyring:return JSONResponse({"ok":False,"error":"OS credential store unavailable"},500)
    if not key:return JSONResponse({"ok":False,"error":"API key required"},400)
    keyring.set_password(SERVICE,pid,key);return {"ok":True,"stored":"OS credential store","provider":pid}
@APP.delete("/api/credentials/{pid}")
async def credential_delete(pid:str):
    if keyring:
        try:keyring.delete_password(SERVICE,pid)
        except Exception:pass
    return {"ok":True}

@APP.post("/api/models")
async def models(body:dict):
    pid=body.get("provider");p=PROVIDERS.get(pid)
    if not p:return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    base=(body.get("base") or p["base"]).rstrip("/");key=key_for(pid,body.get("apiKey"))
    if p["key"] and not key:return JSONResponse({"ok":False,"error":f"{p['name']} API key required"},400)
    try:
        start=time.perf_counter();headers={"Authorization":f"Bearer {key}"} if key else {}
        if pid=="ollama":
            data=await req(base+"/api/tags",headers=headers);ms=[{"id":m.get("name"),"detail":m.get("details",{}).get("parameter_size","")} for m in data.get("models",[])]
        elif pid=="anthropic":
            ms=[{"id":x,"detail":"Anthropic Messages API"} for x in ["claude-opus-4-1","claude-sonnet-4-5","claude-haiku-4-5"]]
        else:
            data=await req(base+"/models",headers=headers);ms=[{"id":m.get("id"),"detail":m.get("owned_by","")} for m in data.get("data",[])]
        return {"ok":True,"models":ms,"latency_ms":round((time.perf_counter()-start)*1000)}
    except Exception as e:return JSONResponse({"ok":False,"error":boundary(pid,e)},502)
@APP.post("/api/health/provider")
async def provider_health(body:dict):return await models(body)

@APP.post("/api/chat")
async def chat(body:dict):
    pid=body.get("provider");p=PROVIDERS.get(pid)
    if not p:return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    if p["kind"]=="cloud" and not body.get("cloud_approved"):return JSONResponse({"ok":False,"error":"Cloud request not approved for this turn. Enable 'Approve cloud for this request'."},403)
    key=key_for(pid,body.get("apiKey"));base=(body.get("base") or p["base"]).rstrip("/");model=body.get("model");messages=body.get("messages") or []
    if not model:return JSONResponse({"ok":False,"error":"Model required"},400)
    if p["key"] and not key:return JSONResponse({"ok":False,"error":f"{p['name']} API key required"},400)
    try:
        start=time.perf_counter()
        if pid=="anthropic":
            headers={"x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"};sys=[];msgs=[]
            for m in messages:
                if m.get("role")=="system":sys.append(m.get("content",""))
                else:msgs.append({"role":m.get("role","user"),"content":m.get("content","")})
            payload={"model":model,"max_tokens":8192,"messages":msgs,"temperature":body.get("temperature",.7)}
            if sys:payload["system"]="\n".join(sys)
            data=await req(base+"/messages","POST",headers,payload);text="".join(x.get("text","") for x in data.get("content",[]) if x.get("type")=="text");used=data.get("model",model)
        elif pid=="ollama":
            data=await req(base+"/api/chat","POST",{"Content-Type":"application/json"},{"model":model,"messages":messages,"stream":False,"options":{"temperature":body.get("temperature",.7),"num_ctx":body.get("num_ctx",4096)}});text=data.get("message",{}).get("content","");used=data.get("model",model)
        else:
            extra={}
            if pid=="openrouter" and body.get("zdr",True):extra["provider"]={"zdr":True,"data_collection":"deny","allow_fallbacks":bool(body.get("allow_fallbacks",False))}
            data=await req(base+"/chat/completions","POST",{"Authorization":f"Bearer {key}","Content-Type":"application/json"},{"model":model,"messages":messages,"temperature":body.get("temperature",.7),**extra});text=data.get("choices",[{}])[0].get("message",{}).get("content","");used=data.get("model",model)
        if body.get("chat_id"):
            save_chat({"id":body["chat_id"],"title":body.get("title") or (messages[0].get("content","")[:80] if messages else "SS chat"),"provider":pid,"model":used,"messages":messages+[ {"role":"assistant","content":text,"model":used} ]})
        return {"ok":True,"text":text,"provider":pid,"model":used,"usage":data.get("usage"),"latency_ms":round((time.perf_counter()-start)*1000)}
    except Exception as e:return JSONResponse({"ok":False,"error":boundary(pid,e)},502)

@APP.post("/api/search")
async def search(body:dict):
    q=(body.get("query") or "").strip();key=key_for("brave",body.get("apiKey"))
    if not q:return JSONResponse({"ok":False,"error":"Query required"},400)
    if not key:return JSONResponse({"ok":False,"error":"Brave Search API key required"},400)
    try:
        data=await req("https://api.search.brave.com/res/v1/web/search",headers={"X-Subscription-Token":key,"Accept":"application/json"},params={"q":q,"count":int(body.get("count",8))});return {"ok":True,"results":data.get("web",{}).get("results",[])}
    except Exception as e:return JSONResponse({"ok":False,"error":str(e)},502)

@APP.post("/api/route")
async def route(body:dict):
    t=(body.get("task") or "").lower();privacy=any(x in t for x in ["private","confidential","sensitive","local only","offline"]);research=any(x in t for x in ["latest","current","research","web","news","today"]);hard=any(x in t for x in ["complex","deep reasoning","prove","derive","architecture","legal analysis","long document"]);coding=any(x in t for x in ["code","debug","program","software","github"])
    if privacy:order=["ollama","jan","lmstudio","openrouter","huggingface","venice"]
    elif research:order=["perplexity","openrouter","google","huggingface","brave"]
    elif coding:order=["deepseek","anthropic","openai","zai","qwen","lmstudio","jan"]
    elif hard:order=["openai","anthropic","google","deepseek","zai","qwen","openrouter","lmstudio","jan"]
    else:order=["ollama","jan","lmstudio","huggingface","openrouter","venice","openai"]
    return {"ok":True,"candidates":order,"privacy":privacy,"research":research,"complex":hard,"coding":coding,"policy":"Capability × privacy × compute × availability. No silent cross-boundary fallback."}
