from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import httpx, time

app = FastAPI(title="SS Second Brain", version="0.8.1")

PROVIDERS = {
    "ollama": {"name":"Ollama", "kind":"local", "base":"http://127.0.0.1:11434", "priority":1},
    "lmstudio": {"name":"LM Studio / Bionic", "kind":"local", "base":"http://127.0.0.1:1234/v1", "priority":2},
    "jan": {"name":"Jan", "kind":"local", "base":"http://127.0.0.1:1337/v1", "priority":3},
    "openrouter": {"name":"OpenRouter", "kind":"cloud-zdr", "base":"https://openrouter.ai/api/v1", "priority":4},
    "venice": {"name":"Venice AI", "kind":"cloud-private", "base":"https://api.venice.ai/api/v1", "priority":5},
}

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse((Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8"))

@app.get("/providers", response_class=HTMLResponse)
async def providers():
    return HTMLResponse((Path(__file__).parent / "web" / "providers.html").read_text(encoding="utf-8"))

@app.get("/system")
async def system():
    return {"service":"SS Second Brain","version":"0.8.1","status":"online","provider_count":len(PROVIDERS),"architecture":"local-first provider-independent orchestrator"}

@app.get("/api/providers")
async def provider_list():
    return {"providers":PROVIDERS}

async def request_json(url, method="GET", headers=None, payload=None):
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as c:
        r = await c.request(method, url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()

def boundary(pid, exc):
    text=str(exc)
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)) or "ConnectError" in text:
        return f"{PROVIDERS[pid]['name']} is unreachable at its configured endpoint. Start its local API server or correct the endpoint. SS stopped at the provider boundary; it did not silently substitute another engine."
    if "401" in text or "403" in text:
        return f"{PROVIDERS[pid]['name']} rejected the credentials. Check the API key; SS did not store it server-side."
    if "429" in text:
        return f"{PROVIDERS[pid]['name']} rate-limited the request."
    return text

@app.post("/api/models")
async def models(body: dict):
    pid=body.get("provider"); p=PROVIDERS.get(pid)
    if not p: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    base=(body.get("base") or p["base"]).rstrip("/"); key=body.get("apiKey")
    if pid in {"openrouter","venice"} and not key: return JSONResponse({"ok":False,"error":"API key required"},400)
    try:
        h={"Authorization":f"Bearer {key}"} if key else {}
        started=time.perf_counter()
        if pid=="ollama":
            d=await request_json(base+"/api/tags",headers=h)
            ms=[{"id":x["name"],"size":x.get("size"),"parameter_size":x.get("details",{}).get("parameter_size","")} for x in d.get("models",[])]
        else:
            d=await request_json(base+"/models",headers=h); ms=[{"id":x["id"],"owner":x.get("owned_by","")} for x in d.get("data",[])]
        return {"ok":True,"models":ms,"latency_ms":round((time.perf_counter()-started)*1000)}
    except Exception as e:
        return JSONResponse({"ok":False,"error":boundary(pid,e)},502)

@app.post("/api/health/provider")
async def provider_health(body: dict):
    pid=body.get("provider")
    if pid not in PROVIDERS: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    d=await models(body)
    if isinstance(d, JSONResponse): return d
    return {"ok":True,"provider":pid,"status":"READY","model_count":len(d.get("models",[])),"latency_ms":d.get("latency_ms")}

@app.post("/api/route")
async def route(body: dict):
    task=(body.get("task") or "").lower()
    candidates=list(PROVIDERS)
    if any(x in task for x in ("uncensored","unrestricted","creative","roleplay")):
        candidates=["venice","ollama","lmstudio","jan","openrouter"]
    elif any(x in task for x in ("research","current","web","search","latest")):
        candidates=["openrouter","venice","lmstudio","ollama","jan"]
    elif any(x in task for x in ("private","confidential","local","offline")):
        candidates=["ollama","lmstudio","jan","venice","openrouter"]
    return {"ok":True,"task":body.get("task",""),"candidates":candidates,"policy":"transparent heuristic v0.8.1; availability and model fit must be checked before execution"}

@app.post("/api/chat")
async def chat(body: dict):
    pid=body.get("provider"); p=PROVIDERS.get(pid)
    if not p: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    base=(body.get("base") or p["base"]).rstrip("/"); key=body.get("apiKey"); model=body.get("model")
    if not model: return JSONResponse({"ok":False,"error":"Model required"},400)
    h={"Authorization":f"Bearer {key}"} if key else {}
    try:
        started=time.perf_counter()
        if pid=="ollama":
            d=await request_json(base+"/api/chat","POST",h,{"model":model,"messages":body.get("messages",[]),"stream":False,"options":{"temperature":body.get("temperature",0.7)}})
            return {"ok":True,"text":d.get("message",{}).get("content",""),"provider":pid,"model":model,"latency_ms":round((time.perf_counter()-started)*1000)}
        extra={}
        if pid=="openrouter" and body.get("zdr",True):
            extra["provider"]={"zdr":True,"data_collection":"deny","allow_fallbacks":True}
        d=await request_json(base+"/chat/completions","POST",h,{"model":model,"messages":body.get("messages",[]),"temperature":body.get("temperature",0.7),**extra})
        return {"ok":True,"text":d.get("choices",[{}])[0].get("message",{}).get("content","") ,"provider":pid,"model":d.get("model",model),"usage":d.get("usage"),"latency_ms":round((time.perf_counter()-started)*1000)}
    except Exception as e:
        return JSONResponse({"ok":False,"error":boundary(pid,e),"provider":pid},502)
