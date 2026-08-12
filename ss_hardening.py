"""0.8.4 runtime hardening layer.

Additive only: it does not delete, rename, move or overwrite user data.
"""
from fastapi import JSONResponse
from app import PROVIDERS, key_for, models as core_models, chat as core_chat, route as core_route, pick_model

IDENTITY_RULES = (
    "You are being used through SS Second Brain.\n"
    "PROVENANCE RULE: never claim to be another provider, product, person, or model. "
    "If asked what model/provider you are, state only the exact provider and model supplied by SS. "
    "Do not invent infrastructure, training dates, company ownership, deployment location, or system access. "
    "If the requested fact is unavailable, say SS cannot confirm it.\n"
    "TRUTH RULE: distinguish known facts from uncertainty. Never fabricate tool use, files read, searches, "
    "connections, citations, or actions.\n"
    "SAFETY RULE: do not execute, delete, rename, move, overwrite, transmit, or purchase anything unless "
    "the SS permission layer explicitly authorizes that operation."
)

def _identity_request(messages):
    text=" ".join(str(m.get("content","")) for m in (messages or []) if m.get("role")=="user").lower()
    return any(n in text for n in ("what model are you","which model are you","what ai are you","are you using","who are you","what provider"))

def _with_identity(messages,provider,model):
    sys=IDENTITY_RULES+f"\nCURRENT SS ROUTE: provider={provider}; model={model}."
    clean=[m for m in messages if m.get("role")!="system"]
    return [{"role":"system","content":sys}]+clean

async def hardened_chat(body):
    provider,model=body.get("provider"),body.get("model")
    messages=body.get("messages") or []
    if provider not in PROVIDERS:return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    if not model:return JSONResponse({"ok":False,"error":"Model required"},400)
    if _identity_request(messages):
        return {"ok":True,"text":f"SS confirms this turn is routed to {PROVIDERS[provider]['name']} · {model}.","provider":provider,"model":model,"identity_source":"SS route metadata","latency_ms":0}
    b=dict(body);b["messages"]=_with_identity(messages,provider,model)
    return await core_chat(b)

async def model_get(provider):
    if provider not in PROVIDERS:return JSONResponse({"ok":False,"error":"Unknown provider"},404)
    return await core_models({"provider":provider})

def free_model(pid,m):
    if pid in ("ollama","jan","lmstudio"):return True
    if m.get("is_free") is True:return True
    p=m.get("pricing") or {}
    try:return float(p.get("input",1) or 1)==0 and float(p.get("output",1) or 1)==0
    except Exception:return False

def catalog_summary(pid,result):
    if isinstance(result,JSONResponse):return {"provider":pid,"ok":False,"error":"provider request failed"}
    ms=result.get("models",[]) if isinstance(result,dict) else []
    return {"provider":pid,"ok":True,"latency_ms":result.get("latency_ms"),"model_count":len(ms),"free_count":sum(free_model(pid,m) for m in ms),"models":sorted(ms,key=lambda x:str(x.get("id","")).lower())}

async def health_all(include_cloud=False):
    out=[]
    for pid in sorted(PROVIDERS,key=lambda x:PROVIDERS[x]["name"].lower()):
        p=PROVIDERS[pid]
        if p["kind"]=="cloud" and not include_cloud:
            out.append({"provider":pid,"name":p["name"],"status":"SKIPPED","reason":"Cloud health checks require explicit approval."});continue
        if p["kind"]=="cloud" and not key_for(pid):
            out.append({"provider":pid,"name":p["name"],"status":"NO_KEY"});continue
        try:
            r=await core_models({"provider":pid});s=catalog_summary(pid,r);s["name"]=p["name"];s["status"]="OK" if s.get("ok") else "ERROR";out.append(s)
        except Exception as e:out.append({"provider":pid,"name":p["name"],"status":"ERROR","error":str(e)})
    return {"ok":True,"cloud_checks_approved":include_cloud,"results":out,"no_generation_requests":True}

async def auto_safe(body):
    task=body.get("task","");messages=body.get("messages") or [{"role":"user","content":task}]
    # Identity questions are answered from SS route metadata, never guessed by an LLM.
    if _identity_request(messages):
        r=await core_route({"task":task});cands=r.get("candidates",[])
        approved=bool(body.get("cloud_approved"));cands=[p for p in cands if approved or PROVIDERS[p]["kind"]=="local"]
        if not cands:return JSONResponse({"ok":False,"error":"No eligible local provider is available for deterministic identity confirmation."},502)
        for pid in cands:
            try:
                mr=await core_models({"provider":pid})
                if isinstance(mr,dict) and mr.get("models"):
                    model=pick_model(pid,mr["models"])
                    return {"ok":True,"text":f"SS confirms this turn is routed to {PROVIDERS[pid]['name']} · {model}.","provider":pid,"model":model,"identity_source":"SS route metadata","latency_ms":0}
            except Exception:pass
        return JSONResponse({"ok":False,"error":"No eligible working provider could be verified."},502)
    b=dict(body);b["messages"]=[{"role":"system","content":IDENTITY_RULES}]+[m for m in messages if m.get("role")!="system"]
    from app import auto_chat as core_auto_chat
    return await core_auto_chat(b)

def register(app):
    @app.get('/api/models/{provider}')
    async def models_get(provider:str):return await model_get(provider)
    @app.post('/api/chat-safe')
    async def chat_safe(body:dict):return await hardened_chat(body)
    @app.post('/api/auto-chat-safe')
    async def auto_chat_safe(body:dict):return await auto_safe(body)
    @app.post('/api/health/all')
    async def health_all_route(body:dict=None):return await health_all(bool((body or {}).get('cloud_approved')))
    @app.get('/api/release')
    async def release_info():
        return {'version':'0.8.4','release_policy':'No version increment until a substantial, verified capability leap is complete and explicitly approved.','architecture':'single 8765 Brain; provider-console functionality integrated at /console','data_policy':'existing chats, memory, files and metadata are not deleted by application update','benchmarks':['Jan: tagged releases, assets/checksums, model/context management','Open WebUI: durable migrations, backups, provider flexibility and robust file/message handling','AnythingLLM: workspaces, memories, agents, filesystem skills, citations and provider/model switching','LangGraph: durable state, resumability and human-in-the-loop control','Agno: memory, context providers, approvals, tracing and auditability','LibreChat: agent skills, subagents, MCP hardening and explicit memory controls']}
    return app
