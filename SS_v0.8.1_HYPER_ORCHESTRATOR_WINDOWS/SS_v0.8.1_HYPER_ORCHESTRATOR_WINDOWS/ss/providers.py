import os,requests
from .resources import OLLAMA,models
def providers():
    ms=[x.get("name") for x in models()];key=os.getenv("OPENROUTER_API_KEY","").strip()
    return [{"id":"ollama_local","name":"Ollama Local","available":bool(ms),"reason":"Ollama models detected." if ms else "Ollama unavailable/no models.","models":ms},
            {"id":"openrouter","name":"OpenRouter","available":bool(key),"reason":"Explicit API key configured." if key else "Not configured; no fake cloud access.","models":[os.getenv("OPENROUTER_MODEL","")] if key else []}]
def choose(kind,ram):
    installed={x.get("name") for x in models()}
    order=["qwen3:1.7b","gemma3:1b","llama3.2:1b","phi4-mini:3.8b"] if kind in ("reasoning","research","coding") else ["gemma3:1b","llama3.2:1b","qwen3:1.7b","phi4-mini:3.8b"]
    estimate={"qwen3:1.7b":1.5,"gemma3:1b":1.0,"llama3.2:1b":1.1,"phi4-mini:3.8b":3.8}
    for m in order:
        if m in installed and ram >= estimate[m]+.25:return m,estimate[m]
    return None,None
def chat(model,prompt):
    r=requests.post(OLLAMA+"/api/chat",json={"model":model,"messages":[{"role":"user","content":prompt}],"stream":False,"options":{"num_ctx":2048}},timeout=120);r.raise_for_status()
    return r.json().get("message",{}).get("content","")
