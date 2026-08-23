"""Canonical SS v0.8.4 entry point for 8765.

One integrated application: Brain + provider console + workspace + optional
local coding-agent bridges. The bridges never bypass their own permission
systems and are never selected automatically by the normal router.
"""
import asyncio
import app_integrated as brain
from workspace_min import workspace, scan, extract_route, duplicates, context
from ss_policy import install_policy
from agent_bridge import AGENTS, status as agent_status, run_agent
from fastapi.responses import JSONResponse

install_policy(brain)
APP = brain.APP

for _aid, _cfg in AGENTS.items():
    brain.PROVIDERS.setdefault(_aid, {
        "name": _cfg["name"], "kind": "local_agent", "base": "local://agent",
        "cap": "coding_agent", "key": False
    })

_original_models_impl = brain.models_impl
_original_chat_provider = brain.chat_provider

async def _models_impl(body):
    pid = body.get("provider")
    if pid in AGENTS:
        s = agent_status().get(pid, {})
        if not s.get("installed"):
            return {"ok": False, "error": f"{AGENTS[pid]['name']} is not installed/on PATH."}
        models = {
            "claude_code": [{"id": "sonnet", "detail": "Claude Code alias"}, {"id": "opus", "detail": "Claude Code alias"}],
            "gemini_cli": [{"id": "default", "detail": "Gemini CLI configured model"}],
        }[pid]
        return {"ok": True, "models": models, "latency_ms": 0, "agent": s}
    return await _original_models_impl(body)

async def _chat_provider(pid, model, messages, system_extra=""):
    if pid in AGENTS:
        prompt = "\n".join(str(m.get("content", "")) for m in messages if m.get("role") in ("user", "assistant"))
        result = await asyncio.to_thread(run_agent, pid, prompt, None if model == "default" else model, None)
        return result["text"], 0
    return await _original_chat_provider(pid, model, messages, system_extra)

# app_integrated route handlers resolve these names in their module globals.
brain.__dict__["models_impl"] = _models_impl
brain.__dict__["chat_provider"] = _chat_provider

@APP.get("/api/agents")
async def agents():
    return {"agents": AGENTS, "status": agent_status(),
            "policy": "manual selection only; never automatic routing; no permission-bypass flags"}

@APP.post("/api/agents/run")
async def agents_run(body: dict):
    aid = body.get("agent")
    if aid not in AGENTS:
        return JSONResponse({"ok": False, "error": "Unknown agent"}, 400)
    try:
        result = await asyncio.to_thread(run_agent, aid, str(body.get("prompt", "")), body.get("model"), body.get("cwd"), body.get("timeout", 600))
        return result
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, 502)

_existing = {getattr(r, "path", "") for r in APP.routes}
_routes = [
    ("/workspace", workspace, ["GET"]),
    ("/api/workspace/scan", scan, ["POST"]),
    ("/api/workspace/extract", extract_route, ["POST"]),
    ("/api/workspace/duplicates", duplicates, ["POST"]),
    ("/api/workspace/context", context, ["POST"]),
]
for _path, _handler, _methods in _routes:
    if _path not in _existing:
        APP.add_api_route(_path, _handler, methods=_methods)

VERSION = "0.8.4"
assert VERSION == "0.8.4"
