from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pathlib import Path
from datetime import datetime, timezone
import httpx, time, json, os, re, socket, platform, shutil

try:
    import psutil
except ImportError:
    psutil = None

try:
    import keyring
except ImportError:
    keyring = None

VERSION = "0.8.3"
APP = FastAPI(title="SS Second Brain", version=VERSION)
ROOT = Path(__file__).parent

# Persistent user data is deliberately outside the repository. Application updates must never replace it.
def data_root():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) if os.name == "nt" else Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))
    p = base / "SS" / "chats"
    p.mkdir(parents=True, exist_ok=True)
    return p

def cloud_root():
    value = os.environ.get("SS_CHAT_CLOUD_ROOT", "").strip()
    if not value:
        return None
    p = Path(value).expanduser(); p.mkdir(parents=True, exist_ok=True); return p

def safe_id(value):
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "chat"))[:120] or "chat")

def write_chat(chat):
    chat = dict(chat)
    chat.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    chat["updated_at"] = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(chat, ensure_ascii=False, indent=2)
    targets = [data_root() / f"{safe_id(chat['id'])}.json"]
    cr = cloud_root()
    if cr: targets.append(cr / f"{safe_id(chat['id'])}.json")
    for target in targets:
        tmp = target.with_suffix(".tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, target)
    return {"local": str(targets[0]), "cloud": str(targets[1]) if len(targets) > 1 else None}

# Provider registry. kind=local means SS never requires a cloud key; cloud providers require credentials.
PROVIDERS = {
    "ollama": {"name":"Ollama", "kind":"local", "base":"http://127.0.0.1:11434", "cap":"local"},
    "lmstudio": {"name":"LM Studio / Bionic", "kind":"local", "base":"http://127.0.0.1:1234/v1", "cap":"local"},
    "jan": {"name":"Jan", "kind":"local", "base":"http://127.0.0.1:1337/v1", "cap":"local"},
    "openrouter": {"name":"OpenRouter · ZDR", "kind":"cloud-zdr", "base":"https://openrouter.ai/api/v1", "cap":"gateway"},
    "huggingface": {"name":"Hugging Face Inference Providers", "kind":"cloud-gateway", "base":"https://router.huggingface.co/v1", "cap":"gateway"},
    "venice": {"name":"Venice AI", "kind":"cloud-private", "base":"https://api.venice.ai/api/v1", "cap":"private"},
    "openai": {"name":"OpenAI", "kind":"cloud-api", "base":"https://api.openai.com/v1", "cap":"frontier"},
    "anthropic": {"name":"Anthropic / Claude", "kind":"cloud-api", "base":"https://api.anthropic.com/v1", "cap":"frontier"},
    "google": {"name":"Google Gemini", "kind":"cloud-api", "base":"https://generativelanguage.googleapis.com/v1beta/openai", "cap":"frontier"},
    "xai": {"name":"xAI / Grok", "kind":"cloud-api", "base":"https://api.x.ai/v1", "cap":"frontier"},
    "deepseek": {"name":"DeepSeek", "kind":"cloud-api", "base":"https://api.deepseek.com/v1", "cap":"reasoning"},
    "mistral": {"name":"Mistral AI", "kind":"cloud-api", "base":"https://api.mistral.ai/v1", "cap":"reasoning"},
    "moonshot": {"name":"Moonshot / Kimi", "kind":"cloud-api", "base":"https://api.moonshot.ai/v1", "cap":"reasoning"},
    "zai": {"name":"Z.ai / GLM", "kind":"cloud-api", "base":"https://api.z.ai/api/paas/v4", "cap":"reasoning"},
    "qwen": {"name":"Qwen / Alibaba Model Studio", "kind":"cloud-api", "base":"https://dashscope-us.aliyuncs.com/compatible-mode/v1", "cap":"reasoning", "note":"US default; regional WorkspaceId endpoint can be entered manually"},
    "perplexity": {"name":"Perplexity", "kind":"cloud-research", "base":"https://api.perplexity.ai", "cap":"research"},
}
SEARCH_PROVIDERS = {
    "brave": {"name":"Brave Search", "base":"https://api.search.brave.com/res/v1/web/search", "auth":"X-Subscription-Token"},
}
KEY_SERVICE = "SS-Second-Brain"

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse((ROOT/"web"/"index.html").read_text(encoding="utf-8"))

@app.get("/providers", response_class=HTMLResponse)
@app.get("/console", response_class=HTMLResponse)
async def providers():
    return HTMLResponse((ROOT/"web"/"providers.html").read_text(encoding="utf-8"))

@app.get("/web/persistence.js", response_class=PlainTextResponse)
async def persistence():
    return PlainTextResponse((ROOT/"web"/"persistence.js").read_text(encoding="utf-8"), media_type="text/javascript")

@app.get("/system")
async def system():
    return {"service":"SS Second Brain", "version":VERSION, "status":"online", "port":8765,
            "provider_count":len(PROVIDERS), "search_provider_count":len(SEARCH_PROVIDERS),
            "chat_persistence":{"local":str(data_root()),"cloud":str(cloud_root()) if cloud_root() else None,"deletion_policy":"NEVER"},
            "single_entrypoint":"http://127.0.0.1:8765/"}

@app.get("/api/providers")
async def provider_list():
    return {"providers":PROVIDERS, "search_providers":SEARCH_PROVIDERS}

@app.get("/api/storage")
async def storage():
    return {"local":str(data_root()),"cloud":str(cloud_root()) if cloud_root() else None,"never_delete":True}

@app.get("/api/resources")
async def resources():
    if psutil:
        vm=psutil.virtual_memory(); swap=psutil.swap_memory()
        return {"ok":True,"ram_total_gb":round(vm.total/2**30,2),"ram_available_gb":round(vm.available/2**30,2),"ram_used_percent":vm.percent,
                "swap_used_gb":round(swap.used/2**30,2),"cpu_percent":psutil.cpu_percent(interval=0.15),
                "platform":platform.platform()}
    return {"ok":False,"error":"psutil not installed"}

@app.get("/api/chats/{chat_id}")
async def get_chat(chat_id:str):
    for p in [data_root()/f"{safe_id(chat_id)}.json"] + ([cloud_root()/f"{safe_id(chat_id)}.json"] if cloud_root() else []):
        if p.exists(): return json.loads(p.read_text(encoding="utf-8"))
    return JSONResponse({"ok":False,"error":"Chat not found"},404)

@app.post("/api/chats")
async def save_chat(body:dict):
    if not body.get("id") or not isinstance(body.get("messages"),list):
        return JSONResponse({"ok":False,"error":"id and messages required"},400)
    return {"ok":True,"saved":write_chat(body),"deletion_policy":"NEVER"}

@app.get("/api/credentials/status")
async def credential_status():
    if not keyring: return {"available":False,"backend":"browser-only","warning":"keyring package unavailable"}
    out={}
    for pid in list(PROVIDERS)+list(SEARCH_PROVIDERS):
        try: out[pid]=bool(keyring.get_password(KEY_SERVICE,pid))
        except Exception: out[pid]=False
    return {"available":True,"backend":"OS credential store","configured":out}

@app.post("/api/credentials")
async def credential_save(body:dict):
    pid=body.get("provider"); key=body.get("apiKey","")
    if pid not in PROVIDERS and pid not in SEARCH_PROVIDERS: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    if not keyring: return JSONResponse({"ok":False,"error":"OS credential store unavailable; install keyring dependency"},500)
    if not key: return JSONResponse({"ok":False,"error":"API key required"},400)
    keyring.set_password(KEY_SERVICE,pid,key)
    return {"ok":True,"provider":pid,"stored":"OS credential store"}

@app.delete("/api/credentials/{pid}")
async def credential_delete(pid:str):
    if not keyring: return JSONResponse({"ok":False,"error":"OS credential store unavailable"},500)
    try: keyring.delete_password(KEY_SERVICE,pid)
    except Exception: pass
    return {"ok":True,"provider":pid}

def get_key(pid, supplied=None):
    if supplied: return supplied
    if keyring:
        try: return keyring.get_password(KEY_SERVICE,pid)
        except Exception: return None
    return None

async def req(url, method="GET", headers=None, payload=None, params=None):
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        response=await client.request(method,url,headers=headers,json=payload,params=params)
        response.raise_for_status()
        return response.json()

def boundary(pid, exc):
    text=str(exc)
    if isinstance(exc,(httpx.ConnectError,httpx.ConnectTimeout)) or "ConnectError" in text:
        return f"{PROVIDERS.get(pid,SEARCH_PROVIDERS.get(pid,{ 'name':pid }))['name']} is unreachable. SS stopped at this provider boundary and did not silently switch engines."
    if "401" in text or "403" in text: return f"{PROVIDERS.get(pid,SEARCH_PROVIDERS.get(pid,{ 'name':pid }))['name']} rejected the credentials."
    if "429" in text: return f"{PROVIDERS.get(pid,SEARCH_PROVIDERS.get(pid,{ 'name':pid }))['name']} rate-limited the request."
    return text

@app.post("/api/models")
async def models(body:dict):
    pid=body.get("provider"); p=PROVIDERS.get(pid)
    if not p: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    key=get_key(pid,body.get("apiKey")); base=(body.get("base") or p["base"]).rstrip("/")
    if p["kind"].startswith("cloud") and not key: return JSONResponse({"ok":False,"error":"API key required"},400)
    try:
        headers={"Authorization":f"Bearer {key}"} if key else {}; start=time.perf_counter()
        if pid=="anthropic":
            # Anthropic does not expose the same public /models endpoint; keep a documented model catalogue.
            ms=[{"id":"claude-opus-4-1","owner":"Anthropic"},{"id":"claude-sonnet-4-5","owner":"Anthropic"},{"id":"claude-haiku-4-5","owner":"Anthropic"}]
        else:
            data=await req(base+"/models",headers=headers)
            ms=[{"id":m.get("id"),"owner":m.get("owned_by","")} for m in data.get("data",[])]
        return {"ok":True,"models":ms,"latency_ms":round((time.perf_counter()-start)*1000)}
    except Exception as exc:
        return JSONResponse({"ok":False,"error":boundary(pid,exc)},502)

@app.post("/api/health/provider")
async def provider_health(body:dict):
    return await models(body)

@app.post("/api/search")
async def search(body:dict):
    pid=body.get("provider","brave"); q=(body.get("query") or "").strip()
    if pid!="brave" or not q: return JSONResponse({"ok":False,"error":"Brave search and query required"},400)
    key=get_key("brave",body.get("apiKey"))
    if not key: return JSONResponse({"ok":False,"error":"Brave API key required"},400)
    try:
        data=await req(SEARCH_PROVIDERS["brave"]["base"],headers={"X-Subscription-Token":key,"Accept":"application/json"},params={"q":q,"count":int(body.get("count",10))})
        return {"ok":True,"provider":"brave","results":data.get("web",{}).get("results",[]),"query":q}
    except Exception as exc: return JSONResponse({"ok":False,"error":boundary("brave",exc)},502)

@app.post("/api/route")
async def route(body:dict):
    task=(body.get("task") or "").lower()
    local=["ollama","lmstudio","jan"]; candidates=list(PROVIDERS)
    privacy=any(x in task for x in ("private","confidential","sensitive","local only","offline"))
    research=any(x in task for x in ("research","current","latest","web","search","today","news"))
    hard=any(x in task for x in ("complex","deep reasoning","hard","prove","derive","architecture","legal analysis","long document"))
    coding=any(x in task for x in ("code","program","debug","software","github"))
    if privacy: candidates=local+["venice","openrouter","huggingface"]
    elif research: candidates=["perplexity","brave","openrouter","google","openai","xai","huggingface"]
    elif coding: candidates=["deepseek","anthropic","openai","zai","qwen","mistral"]+local
    elif hard: candidates=["anthropic","openai","google","deepseek","zai","qwen","huggingface"]+local
    else: candidates=["ollama","jan","lmstudio","huggingface","openrouter","venice","openai"]
    return {"ok":True,"task":body.get("task",""),"privacy":privacy,"research":research,"high_complexity":hard,
            "candidates":list(dict.fromkeys(candidates)),
            "policy":"SS v0.8.3 routing is resource/privacy/capability-aware policy scaffolding; it never silently falls back across a privacy boundary."}

@app.post("/api/chat")
async def chat(body:dict):
    pid=body.get("provider"); p=PROVIDERS.get(pid)
    if not p: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    key=get_key(pid,body.get("apiKey")); model=body.get("model"); base=(body.get("base") or p["base"]).rstrip("/")
    messages=body.get("messages",[]); temperature=body.get("temperature",0.7)
    if not model: return JSONResponse({"ok":False,"error":"Model required"},400)
    if p["kind"].startswith("cloud") and not key: return JSONResponse({"ok":False,"error":"API key required"},400)
    try:
        start=time.perf_counter(); used=model
        if pid=="anthropic":
            headers={"x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"}
            system=[]; msgs=[]
            for msg in messages:
                if msg.get("role")=="system": system.append(msg.get("content",""))
                else: msgs.append({"role":msg.get("role","user"),"content":msg.get("content","")})
            payload={"model":model,"max_tokens":4096,"temperature":temperature,"messages":msgs}
            if system: payload["system"]="\n".join(system)
            data=await req(base+"/messages","POST",headers,payload)
            text="".join(x.get("text","") for x in data.get("content",[]) if x.get("type")=="text"); used=data.get("model",model)
        elif pid=="ollama":
            data=await req(base+"/api/chat","POST",{"Content-Type":"application/json"},{"model":model,"messages":messages,"stream":False,"options":{"temperature":temperature}})
            text=data.get("message",{}).get("content",""); used=data.get("model",model)
        else:
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}
            extra={}
            if pid=="openrouter" and body.get("zdr",True): extra["provider"]={"zdr":True,"data_collection":"deny","allow_fallbacks":True}
            data=await req(base+"/chat/completions","POST",headers,{"model":model,"messages":messages,"temperature":temperature,**extra})
            text=data.get("choices",[{}])[0].get("message",{}).get("content",""); used=data.get("model",model)
        out={"ok":True,"text":text,"provider":pid,"model":used,"usage":data.get("usage"),"latency_ms":round((time.perf_counter()-start)*1000)}
        if body.get("chat_id"):
            out["persistence"]=write_chat({"id":body["chat_id"],"provider":pid,"model":used,"messages":messages+[{"role":"assistant","content":text}]})
        return out
    except Exception as exc:
        return JSONResponse({"ok":False,"error":boundary(pid,exc),"provider":pid},502)
