"""SS Second Brain v0.8.4 integrated runtime.

Single 8765 application: Brain + provider console + workspace.
The legacy 8766 provider-console source remains in the repository; this runtime
absorbs its provider/setup/history functions rather than running a second Brain.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime, timezone
import json, os, re, time, platform
import httpx
try:
    import psutil
except ImportError:
    psutil = None
try:
    import keyring
except ImportError:
    keyring = None

import app as legacy
from workspace_min import router as workspace_router

VERSION = "0.8.4"
APP = FastAPI(title="SS Second Brain", version=VERSION)
ROOT = Path(__file__).parent
SERVICE = "SS-Second-Brain"
PROVIDERS = legacy.PROVIDERS
CONNECTORS = legacy.CONNECTORS
OFFICIAL_SETUP = legacy.OFFICIAL_SETUP

# ---------- persistence ----------
def data_root():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) if os.name == "nt" else Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))
    p = base / "SS" / "data"
    for s in ("chats", "memory", "backups", "audit", "workspaces"):
        (p / s).mkdir(parents=True, exist_ok=True)
    return p

def cloud_root():
    v = os.environ.get("SS_CHAT_CLOUD_ROOT", "").strip()
    if not v:
        return None
    p = Path(v).expanduser(); p.mkdir(parents=True, exist_ok=True)
    return p

def safe(v):
    return (re.sub(r"[^A-Za-z0-9._-]+", "_", str(v or "chat"))[:140] or "chat")

def atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)

def save_chat(chat):
    c = dict(chat); now = datetime.now(timezone.utc).isoformat()
    c.setdefault("created_at", now); c["updated_at"] = now
    targets = [data_root()/"chats"/(safe(c["id"])+".json")]
    cr = cloud_root()
    if cr: targets.append(cr/(safe(c["id"])+".json"))
    for p in targets: atomic(p, c)
    return {"local": str(targets[0]), "cloud": str(targets[1]) if len(targets) > 1 else None}

def load_chats():
    out=[]
    for p in sorted((data_root()/"chats").glob("*.json"), key=lambda x:x.stat().st_mtime, reverse=True):
        try:
            c=json.loads(p.read_text(encoding="utf-8")); out.append({"id":c.get("id",p.stem),"title":c.get("title","Untitled chat"),"updated_at":c.get("updated_at"),"provider":c.get("provider"),"model":c.get("model"),"messages":len(c.get("messages",[]))})
        except Exception: pass
    return out

def save_audit(event):
    p=data_root()/"audit"/(datetime.now().strftime("%Y-%m-%d")+".jsonl")
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f: f.write(json.dumps({"ts":datetime.now(timezone.utc).isoformat(),**event},ensure_ascii=False)+"\n")

def key_for(pid, supplied=None):
    if supplied: return supplied
    if keyring:
        try: return keyring.get_password(SERVICE,pid)
        except Exception: return None
    return None

# ---------- provider transport ----------
async def request_json(url, method="GET", headers=None, payload=None):
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        r = await client.request(method, url, headers=headers, json=payload)
        try: d = r.json()
        except Exception: d = {"raw": r.text}
        if r.status_code >= 400:
            e=d.get("error") if isinstance(d,dict) else None
            detail=e.get("message") if isinstance(e,dict) else e
            raise RuntimeError(f"HTTP {r.status_code}: {detail or r.reason_phrase}")
        return d

def boundary(pid, exc):
    s=str(exc); name=PROVIDERS.get(pid, {"name":pid})["name"]
    lo=s.lower()
    if any(x in lo for x in ("connecterror","connecttimeout","connection refused","name or service not known")):
        return f"{name} is unreachable. SS stopped at this boundary; no silent provider switch."
    if "401" in s or "403" in s: return f"{name} rejected the credential/permission. SS did not retry with another account."
    if "429" in s: return f"{name} rate-limited the request. SS did not silently spend elsewhere."
    return s

def model_meta(m):
    if not isinstance(m,dict): return {}
    return {"id":m.get("id"),"detail":m.get("owned_by","") or m.get("description","")[:160],"pricing":m.get("pricing"),"is_free":m.get("is_free",False),"context_length":m.get("context_length")}

def is_free(m, pid):
    if pid in ("ollama","jan","lmstudio"): return True
    if m.get("is_free") is True: return True
    p=m.get("pricing") or {}
    try: return float(p.get("input",1) or 1)==0 and float(p.get("output",1) or 1)==0
    except Exception: return False

def identity_answer(pid, model):
    p=PROVIDERS.get(pid,{"name":pid,"kind":"unknown"})
    if pid=="ollama": location="Ollama local runtime on this machine"
    elif pid in ("jan","lmstudio"): location=f"{p['name']} local API on this machine"
    else: location=f"{p['name']} cloud API"
    return (f"SS is currently routing this chat to **{p['name']} / {model}**.\n\n"
            f"Provider: {p['name']}\nModel: {model}\nExecution: {location}\n"
            f"SS will not let the model invent or override this provenance.\n\n"
            "If you ask which engine answered, SS reports the actual selected route rather than asking the model to identify itself.")

def looks_like_identity(text):
    s=(text or "").lower()
    return bool(re.search(r"\b(who are you|what are you|which model|what model|are you phi|are you gpt|are you ollama|what engine|what provider|who is answering|what ai)\b",s))

async def chat_provider(pid, model, messages, system_extra=""):
    p=PROVIDERS[pid]; key=key_for(pid)
    if p["key"] and not key: raise RuntimeError(f"{p['name']} API key is not configured in SS Setup Center.")
    system=("You are an AI model operating INSIDE SS Second Brain. SS is the authoritative source for provider/model identity, routing, permissions, cost approval and provenance. Never claim to be SS, ChatGPT, Microsoft, OpenAI, Ollama, or another provider unless the supplied route metadata says so. Never invent infrastructure, training dates, account ownership, previous chats, or system access. If asked about your identity, describe only the route metadata supplied by SS. Never claim to have memory of another session unless it is present in the supplied messages.\n"+system_extra).strip()
    msgs=[{"role":"system","content":system}]+[m for m in messages if m.get("role") in ("user","assistant")]
    start=time.perf_counter()
    if pid=="ollama":
        d=await request_json(p["base"]+"/api/chat",method="POST",payload={"model":model,"messages":msgs,"stream":False,"options":{"temperature":0.2}})
        text=((d.get("message") or {}).get("content") or "").strip()
    else:
        base=p["base"].rstrip("/")
        headers={"Authorization":f"Bearer {key}"} if key else {}
        if pid=="openrouter":
            headers.update({"HTTP-Referer":"http://127.0.0.1:8765","X-Title":"SS Second Brain"})
        if pid=="anthropic":
            headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"}
            body={"model":model,"max_tokens":4096,"temperature":0.2,"system":system,"messages":[m for m in messages if m.get("role") in ("user","assistant")]}
            d=await request_json(base+"/messages",method="POST",headers=headers,payload=body)
            text="".join(x.get("text","") for x in d.get("content",[]) if isinstance(x,dict)).strip()
        else:
            d=await request_json(base+"/chat/completions",method="POST",headers=headers,payload={"model":model,"messages":msgs,"temperature":0.2})
            text=(((d.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not text: raise RuntimeError(f"{p['name']} returned an empty response.")
    return text, round((time.perf_counter()-start)*1000)

# ---------- UI / status ----------
@APP.get("/",response_class=HTMLResponse)
@APP.get("/console",response_class=HTMLResponse)
@APP.get("/providers",response_class=HTMLResponse)
async def home():
    return HTMLResponse((ROOT/"web"/"providers.html").read_text(encoding="utf-8"))

@APP.get("/system")
async def system():
    return {"service":"SS Second Brain","version":VERSION,"status":"online","port":8765,"entry":"http://127.0.0.1:8765/","policy":{"auto_delete_chats":False,"silent_provider_fallback":False,"cloud_spend_without_request_approval":False,"destructive_files":False},"storage":{"local":str(data_root()),"cloud":str(cloud_root()) if cloud_root() else None}}

@APP.get("/api/providers")
async def provider_list(): return {"providers":PROVIDERS,"connectors":CONNECTORS,"official_setup":OFFICIAL_SETUP,"version":VERSION}

@APP.get("/api/resources")
async def resources():
    if not psutil: return {"ok":False,"error":"psutil unavailable"}
    v=psutil.virtual_memory(); s=psutil.swap_memory()
    return {"ok":True,"ram_total_gb":round(v.total/2**30,2),"ram_available_gb":round(v.available/2**30,2),"ram_used_percent":v.percent,"swap_used_gb":round(s.used/2**30,2),"cpu_percent":psutil.cpu_percent(interval=.1),"platform":platform.platform()}

@APP.get("/api/storage")
async def storage(): return {"local":str(data_root()),"cloud":str(cloud_root()) if cloud_root() else None,"never_delete":True,"archive":"external-to-code"}

@APP.get("/api/credentials/status")
async def credential_status():
    if not keyring: return {"available":False,"configured":{},"error":"keyring package unavailable"}
    out={}
    for pid in list(PROVIDERS)+["brave"]:
        try: out[pid]=bool(keyring.get_password(SERVICE,pid))
        except Exception: out[pid]=False
    return {"available":True,"configured":out,"backend":"Windows OS credential store" if os.name=="nt" else "OS credential store"}

@APP.post("/api/credentials")
async def credential_save(body:dict):
    pid=body.get("provider"); k=body.get("apiKey")
    if pid not in PROVIDERS and pid!="brave": return JSONResponse({"ok":False,"error":"Unknown credential target"},400)
    if not keyring: return JSONResponse({"ok":False,"error":"OS credential store unavailable"},500)
    if not k: return JSONResponse({"ok":False,"error":"API key/token required"},400)
    keyring.set_password(SERVICE,pid,k); save_audit({"event":"credential_saved","provider":pid})
    return {"ok":True,"stored":"OS credential store","provider":pid}

@APP.delete("/api/credentials/{pid}")
async def credential_delete(pid:str):
    if keyring:
        try:keyring.delete_password(SERVICE,pid)
        except Exception:pass
    save_audit({"event":"credential_deleted","provider":pid})
    return {"ok":True}

@APP.get("/api/chats")
async def chats(): return {"chats":load_chats(),"never_delete":True}

@APP.get("/api/chats/{cid}")
async def chat_get(cid:str):
    p=data_root()/"chats"/(safe(cid)+".json")
    if not p.exists(): return JSONResponse({"ok":False,"error":"Chat not found"},404)
    return json.loads(p.read_text(encoding="utf-8"))

@APP.post("/api/chats")
async def chat_save(body:dict):
    if not body.get("id") or not isinstance(body.get("messages"),list): return JSONResponse({"ok":False,"error":"id and messages required"},400)
    return {"ok":True,"saved":save_chat(body),"never_delete":True}

@APP.get("/api/memory")
async def memory_list():
    out=[]
    for p in (data_root()/"memory").glob("*.json"):
        try:out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:pass
    return {"memory":out}

@APP.post("/api/memory")
async def memory_save(body:dict):
    p=data_root()/"memory"/(safe(body.get("key","memory"))+".json"); atomic(p,body); return {"ok":True,"path":str(p)}

@APP.get("/api/models")
async def models_get(provider:str, apiKey:str="", base:str=""):
    return await models_post({"provider":provider,"apiKey":apiKey,"base":base})

@APP.post("/api/models")
async def models_post(body:dict):
    pid=body.get("provider"); p=PROVIDERS.get(pid)
    if not p: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    base=(body.get("base") or p["base"]).rstrip("/"); key=key_for(pid,body.get("apiKey"))
    if p["key"] and not key: return JSONResponse({"ok":False,"error":f"{p['name']} API key required — use Setup Center on this page."},400)
    try:
        start=time.perf_counter(); headers={"Authorization":f"Bearer {key}"} if key else {}
        if pid=="ollama":
            d=await request_json(base+"/api/tags",headers=headers); ms=[{"id":m.get("name"),"detail":m.get("details",{}).get("parameter_size",""),"is_free":True} for m in d.get("models",[])]
        elif pid=="anthropic":
            ms=[{"id":x,"detail":"Anthropic Messages API"} for x in ["claude-opus-4-1","claude-sonnet-4-5","claude-haiku-4-5"]]
        else:
            d=await request_json(base+"/models",headers=headers); ms=[model_meta(m) for m in d.get("data",[])]
        ms=sorted([m for m in ms if m.get("id")],key=lambda x:x["id"].lower())
        return {"ok":True,"models":ms,"latency_ms":round((time.perf_counter()-start)*1000)}
    except Exception as e: return JSONResponse({"ok":False,"error":boundary(pid,e)},502)

@APP.post("/api/health/provider")
async def provider_health(body:dict): return await models_post(body)

@APP.post("/api/chat")
async def chat(body:dict):
    pid=body.get("provider"); model=body.get("model"); messages=body.get("messages") or []
    if pid not in PROVIDERS: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    if not model: return JSONResponse({"ok":False,"error":"No model selected"},400)
    if PROVIDERS[pid]["key"] and not body.get("cloud_approved"):
        return JSONResponse({"ok":False,"error":"Cloud request requires explicit approval for this request."},403)
    user_text=""
    for m in reversed(messages):
        if m.get("role")=="user": user_text=str(m.get("content","")); break
    if looks_like_identity(user_text):
        text=identity_answer(pid,model); latency=0
    else:
        try:
            text,latency=await chat_provider(pid,model,messages)
        except Exception as e:
            return JSONResponse({"ok":False,"error":boundary(pid,e)},502)
    cid=body.get("chat_id") or safe(datetime.now().isoformat())
    archive_messages=list(messages)+[{"role":"assistant","content":text}]
    save_chat({"id":cid,"title":user_text[:80] or "SS chat","provider":pid,"model":model,"messages":archive_messages})
    save_audit({"event":"chat","provider":pid,"model":model,"chat_id":cid})
    return {"ok":True,"text":text,"provider":pid,"model":model,"latency_ms":latency,"chat_id":cid,"provenance":{"provider":PROVIDERS[pid]["name"],"model":model,"ss_version":VERSION}}

def classify(task):
    s=(task or "").lower()
    return {"privacy":any(x in s for x in ("private","confidential","local file","personal","sensitive","secret","my documents","offline")),"research":any(x in s for x in ("research","latest","web search","sources","news","look up","current")),"coding":any(x in s for x in ("code","program","debug","github","python","javascript","typescript","api")),"high_complexity":any(x in s for x in ("deep","complex","architecture","reason","analyse","analyze","legal","scientific","compare","design")) or len(s)>900}

@APP.post("/api/route")
async def route(body:dict):
    c=classify(body.get("task","")); candidates=[]
    if c["privacy"]: candidates += ["ollama","jan","lmstudio","venice","openrouter"]
    elif c["research"]: candidates += ["perplexity","openrouter","google","qwen"]
    elif c["coding"]: candidates += ["openrouter","deepseek","qwen","anthropic","ollama"]
    elif c["high_complexity"]: candidates += ["openrouter","anthropic","google","deepseek","qwen"]
    else: candidates += ["ollama","openrouter","qwen","google"]
    candidates += [x for x in PROVIDERS if x not in candidates]
    return {**c,"candidates":candidates,"policy":"SS selects only after capability/resource/credential checks; cloud requires explicit approval."}

@APP.post("/api/auto-chat")
async def auto_chat(body:dict):
    task=str(body.get("task","")).strip()
    if not task:return JSONResponse({"ok":False,"error":"Task required"},400)
    r=await route({"task":task}); candidates=r["candidates"]; approved=bool(body.get("cloud_approved")); msgs=body.get("messages") or [{"role":"user","content":task}]
    last_error=None
    for pid in candidates:
        p=PROVIDERS[pid]
        if p["key"] and not approved: continue
        key=key_for(pid)
        if p["key"] and not key: continue
        try:
            # Do not switch after an actual request has started. Only unavailable/unconfigured candidates are skipped.
            models=await models_post({"provider":pid})
            if not models.get("ok") or not models.get("models"): continue
            ms=models["models"]
            chosen=next((m["id"] for m in ms if not is_free(m,pid)),ms[0]["id"])
            text,latency=await chat_provider(pid,chosen,msgs)
            cid=body.get("chat_id") or safe(datetime.now().isoformat())
            save_chat({"id":cid,"title":task[:80],"provider":pid,"model":chosen,"messages":list(msgs)+[{"role":"assistant","content":text}]})
            save_audit({"event":"auto_chat","provider":pid,"model":chosen,"chat_id":cid})
            return {"ok":True,"text":text,"provider":pid,"model":chosen,"latency_ms":latency,"chat_id":cid,"candidates":candidates}
        except Exception as e: last_error=boundary(pid,e); continue
    return JSONResponse({"ok":False,"error":last_error or "No eligible provider/model: configure a local engine or explicitly approve/configure a cloud provider."},503)

# File intelligence is read-only and lives on the same 8765 process.
APP.include_router(workspace_router)
