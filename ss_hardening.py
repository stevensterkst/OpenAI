"""0.8.4 runtime hardening layer.

Keeps the existing Brain implementation intact while adding deterministic
identity, model-route compatibility, provider health boundaries and safer
conversation context. This layer is intentionally additive: it does not
change the persisted chat archive or delete/rename any user data.
"""
from fastapi import JSONResponse
from app import PROVIDERS, CONNECTORS, OFFICIAL_SETUP, key_for, models as core_models, chat as core_chat

IDENTITY_RULES = (
    "You are being used through SS Second Brain.\n"
    "PROVENANCE RULE: never claim to be another provider, product, person, or model. "
    "If asked what model/provider you are, state only the exact provider and model supplied by SS. "
    "Do not invent infrastructure, training dates, company ownership, deployment location, or system access. "
    "If the requested fact is not available, say that SS cannot confirm it.\n"
    "TRUTH RULE: distinguish known facts from uncertainty. Never fabricate tool use, files read, searches, "
    "connections, citations, or actions.\n"
    "SAFETY RULE: do not execute, delete, rename, move, overwrite, transmit, or purchase anything unless "
    "the SS permission layer explicitly authorizes that operation."
)

def _identity_request(messages):
    if not messages:
        return False
    text = " ".join(str(m.get("content", "")) for m in messages if m.get("role") == "user").lower()
    needles = ("what model are you", "which model are you", "what ai are you", "are you using", "who are you", "what provider")
    return any(n in text for n in needles)

def _with_identity(messages, provider, model):
    sys = IDENTITY_RULES + f"\nCURRENT SS ROUTE: provider={provider}; model={model}."
    clean = [m for m in messages if m.get("role") != "system"]
    return [{"role":"system","content":sys}] + clean

async def hardened_chat(body):
    provider = body.get("provider")
    model = body.get("model")
    messages = body.get("messages") or []
    if provider not in PROVIDERS:
        return JSONResponse({"ok":False,"error":"Unknown provider"},400)
    if not model:
        return JSONResponse({"ok":False,"error":"Model required"},400)
    # Deterministic answer for identity questions: do not let a model invent provenance.
    if _identity_request(messages):
        return {"ok":True,"text":f"SS confirms this turn is routed to {PROVIDERS[provider]['name']} · {model}.","provider":provider,"model":model,"identity_source":"SS route metadata","latency_ms":0}
    b=dict(body)
    b["messages"]=_with_identity(messages,provider,model)
    return await core_chat(b)

async def model_get(provider):
    if provider not in PROVIDERS:
        return JSONResponse({"ok":False,"error":"Unknown provider"},404)
    return await core_models({"provider":provider})

def catalog_summary(pid, result):
    if isinstance(result, JSONResponse):
        return {"provider":pid,"ok":False,"error":"provider request failed"}
    models=result.get("models",[]) if isinstance(result,dict) else []
    def free(m):
        if pid in ("ollama","jan","lmstudio"): return True
        if m.get("is_free") is True:return True
        p=m.get("pricing") or {}
        try:return float(p.get("input",1) or 1)==0 and float(p.get("output",1) or 1)==0
        except Exception:return False
    return {"provider":pid,"ok":True,"latency_ms":result.get("latency_ms"),"model_count":len(models),"free_count":sum(free(m) for m in models),"models":sorted(models,key=lambda x:str(x.get("id","")).lower())}

async def health_all(include_cloud=False):
    out=[]
    for pid in sorted(PROVIDERS,key=lambda x:PROVIDERS[x]["name"].lower()):
        p=PROVIDERS[pid]
        if p["kind"]=="cloud" and not include_cloud:
            out.append({"provider":pid,"name":p["name"],"status":"SKIPPED","reason":"Cloud health checks require explicit approval."})
            continue
        if p["kind"]=="cloud" and not key_for(pid):
            out.append({"provider":pid,"name":p["name"],"status":"NO_KEY"})
            continue
        try:
            r=await core_models({"provider":pid})
            s=catalog_summary(pid,r)
            s["name"]=p["name"]
            s["status"]="OK" if s.get("ok") else "ERROR"
            out.append(s)
        except Exception as e:
            out.append({"provider":pid,"name":p["name"],"status":"ERROR","error":str(e)})
    return {"ok":True,"cloud_checks_approved":include_cloud,"results":out,"no_generation_requests":True}

def register(app):
    @app.get('/api/models/{provider}')
    async def models_get(provider:str):
        # Compatibility route for the original Brain UI. The canonical POST endpoint remains unchanged.
        return await model_get(provider)

    @app.post('/api/chat-safe')
    async def chat_safe(body:dict):
        return await hardened_chat(body)

    @app.post('/api/health/all')
    async def health_all_route(body:dict=None):
        body=body or {}
        return await health_all(bool(body.get('cloud_approved')))

    @app.get('/api/release')
    async def release_info():
        return {
            'version':'0.8.4',
            'release_policy':'No version increment until a substantial, verified capability leap is complete and explicitly approved.',
            'architecture':'single 8765 Brain; provider console functionality integrated at /console',
            'data_policy':'existing chats, memory, files and metadata are not deleted by application update',
            'release_inspiration':[
                'Jan: explicit tagged releases, release assets/checksums and model/context management',
                'Open WebUI: migrations/backups, durable file/message handling and provider flexibility',
                'AnythingLLM: workspaces, memories, agents, filesystem skills, citations and provider/model switching',
                'LangGraph: durable state, resumability and human-in-the-loop control',
                'Agno: memory, context providers, human approval, tracing and auditability',
                'LibreChat: agent skills, subagents, MCP hardening and explicit memory controls'
            ]
        }
    return app
