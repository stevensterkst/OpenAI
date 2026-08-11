from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import httpx

app = FastAPI(title="SS Second Brain", version="0.8.0")

PROVIDERS = {
    "ollama": {"name":"Ollama", "kind":"local", "base":"http://127.0.0.1:11434"},
    "lmstudio": {"name":"LM Studio / Bionic", "kind":"local", "base":"http://127.0.0.1:1234/v1"},
    "jan": {"name":"Jan", "kind":"local", "base":"http://127.0.0.1:1337/v1"},
    "openrouter": {"name":"OpenRouter", "kind":"cloud-zdr", "base":"https://openrouter.ai/api/v1"},
    "venice": {"name":"Venice AI", "kind":"cloud-private", "base":"https://api.venice.ai/api/v1"},
}

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse((Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8"))

@app.get("/providers", response_class=HTMLResponse)
async def providers():
    return HTMLResponse((Path(__file__).parent / "web" / "providers.html").read_text(encoding="utf-8"))

@app.get("/system")
async def system():
    return {"service":"SS Second Brain","version":"0.8.0","status":"online","provider_count":len(PROVIDERS)}

@app.get("/api/providers")
async def provider_list():
    return {"providers":PROVIDERS}

async def request_json(url, method="GET", headers=None, payload=None):
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.request(method, url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()

@app.post("/api/models")
async def models(body: dict):
    pid=body.get("provider"); p=PROVIDERS.get(pid)
    if not p: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    base=(body.get("base") or p["base"]).rstrip("/")
    key=body.get("apiKey")
    if pid in {"openrouter","venice"} and not key: return JSONResponse({"ok":False,"error":"API key required"},400)
    try:
        h={"Authorization":f"Bearer {key}"} if key else {}
        if pid=="ollama":
            d=await request_json(base+"/api/tags",headers=h); ms=[{"id":x["name"]} for x in d.get("models",[])]
        else:
            d=await request_json(base+"/models",headers=h); ms=[{"id":x["id"]} for x in d.get("data",[])]
        return {"ok":True,"models":ms}
    except Exception as e:
        return JSONResponse({"ok":False,"error":str(e)},502)

@app.post("/api/chat")
async def chat(body: dict):
    pid=body.get("provider"); p=PROVIDERS.get(pid)
    if not p: return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    base=(body.get("base") or p["base"]).rstrip("/"); key=body.get("apiKey"); model=body.get("model")
    if not model: return JSONResponse({"ok":False,"error":"Model required"},400)
    h={"Authorization":f"Bearer {key}"} if key else {}
    try:
        if pid=="ollama":
            d=await request_json(base+"/api/chat","POST",h,{"model":model,"messages":body.get("messages",[]),"stream":False,"options":{"temperature":body.get("temperature",0.7)}})
            return {"ok":True,"text":d.get("message",{}).get("content","")}
        extra={}
        if pid=="openrouter" and body.get("zdr",True):
            extra["provider"]={"zdr":True,"data_collection":"deny","allow_fallbacks":True}
        d=await request_json(base+"/chat/completions","POST",h,{"model":model,"messages":body.get("messages",[]),"temperature":body.get("temperature",0.7),**extra})
        return {"ok":True,"text":d.get("choices",[{}])[0].get("message",{}).get("content","")}
    except Exception as e:
        return JSONResponse({"ok":False,"error":str(e)},502)
