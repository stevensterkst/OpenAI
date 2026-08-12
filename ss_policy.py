"""SS v0.8.4 policy layer.

Keeps routing decisions deterministic and separate from provider adapters. It uses
measured system RAM only; integrated/shared GPU memory is deliberately not used
as additional RAM capacity.
"""
from datetime import datetime, timezone
from pathlib import Path
import os, re

try:
    import psutil
except ImportError:
    psutil = None


def resources():
    if not psutil:
        return {"available_gb": None, "total_gb": None, "used_percent": None}
    v = psutil.virtual_memory()
    return {
        "available_gb": round(v.available / 2**30, 2),
        "total_gb": round(v.total / 2**30, 2),
        "used_percent": v.percent,
    }


def classify(task):
    s = str(task or "").lower()
    return {
        "privacy": any(x in s for x in ("private", "confidential", "local file", "personal", "sensitive", "secret", "my documents", "offline")),
        "research": any(x in s for x in ("research", "latest", "web search", "sources", "news", "look up", "current")),
        "coding": any(x in s for x in ("code", "program", "debug", "github", "python", "javascript", "typescript", "api")),
        "high_complexity": any(x in s for x in ("deep", "complex", "architecture", "reason", "analyse", "analyze", "legal", "scientific", "compare", "design")) or len(s) > 900,
    }


def local_capacity_ok(pid, available_gb, model=None):
    """Conservative gate; this is a routing heuristic, not a model-memory guarantee."""
    if pid not in ("ollama", "jan", "lmstudio"):
        return True
    if available_gb is None:
        return False
    if available_gb < 1.75:
        return False
    if not model:
        return True
    m = str(model).lower()
    match = re.search(r"(?:^|[^0-9])([0-9]+(?:\.[0-9]+)?)b(?:[^0-9]|$)", m)
    if not match:
        return available_gb >= 2.0
    params = float(match.group(1))
    required = 1.5 if params <= 1.2 else 2.0 if params <= 2.0 else 3.5 if params <= 4.0 else 6.0 if params <= 8.0 else 10.0
    return available_gb >= required


def _model_params(model):
    s = str(model.get("id", "")) + " " + str(model.get("detail", ""))
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)b", s.lower())
    return float(m.group(1)) if m else 999.0


def pick_model(provider, models, available_gb):
    candidates = [m for m in models if m.get("id")]
    if provider in ("ollama", "jan", "lmstudio"):
        candidates = [m for m in candidates if local_capacity_ok(provider, available_gb, m.get("id"))]
        candidates.sort(key=lambda m: (_model_params(m), str(m.get("id")).lower()))
        return candidates[0] if candidates else None
    # For cloud providers, prefer explicitly free models when available; otherwise
    # the provider catalogue order is not treated as a quality claim.
    free = [m for m in candidates if m.get("is_free") is True]
    return sorted(free or candidates, key=lambda m: str(m.get("id")).lower())[0] if (free or candidates) else None


async def route(body, brain):
    c = classify(body.get("task", ""))
    r = resources()
    available = r["available_gb"]
    local_ok = available is not None and available >= 1.75
    if c["privacy"]:
        preferred = ["ollama", "jan", "lmstudio", "venice", "openrouter", "huggingface"]
    elif c["research"]:
        preferred = ["perplexity", "openrouter", "google", "deepseek", "huggingface"]
    elif c["coding"]:
        preferred = ["ollama", "openrouter", "anthropic", "openai", "deepseek", "qwen"]
    elif c["high_complexity"]:
        preferred = ["openrouter", "anthropic", "openai", "google", "deepseek", "qwen"]
    else:
        preferred = ["ollama", "jan", "lmstudio", "openrouter", "huggingface", "deepseek", "google", "openai"]
    candidates = []
    for pid in preferred:
        p = brain.PROVIDERS.get(pid)
        if not p:
            continue
        if p["kind"] == "local" and not local_ok:
            continue
        if p["kind"] == "cloud" and not brain.key_for(pid):
            continue
        candidates.append(pid)
    return {
        **c,
        "candidates": candidates,
        "resource": r,
        "local_gate": {"allowed": local_ok, "minimum_available_ram_gb": 1.75, "basis": "conservative measured-RAM heuristic; shared GPU memory is not added"},
        "policy": "Local is preferred where capability and measured RAM permit it. Cloud requires explicit approval. SS never silently crosses a failed privacy boundary.",
    }


async def auto_chat(body, brain):
    task = str(body.get("task", "")).strip()
    if not task:
        from fastapi.responses import JSONResponse
        return JSONResponse({"ok": False, "error": "Task required"}, 400)
    approved = bool(body.get("cloud_approved"))
    messages = body.get("messages") or [{"role": "user", "content": task}]
    r = await route({"task": task}, brain)
    last = []
    available = r["resource"]["available_gb"]
    for pid in r["candidates"]:
        p = brain.PROVIDERS[pid]
        if p["kind"] == "cloud" and not approved:
            continue
        try:
            d = await brain.models_impl({"provider": pid})
            if not d.get("ok") or not d.get("models"):
                continue
            chosen = pick_model(pid, d["models"], available)
            if not chosen:
                last.append({"provider": pid, "reason": "No model passed the current conservative local resource gate."})
                continue
            text, latency = await brain.chat_provider(pid, chosen["id"], messages)
            cid = body.get("chat_id") or re.sub(r"[^A-Za-z0-9._-]+", "_", datetime.now(timezone.utc).isoformat())
            brain.save_chat({"id": cid, "title": task[:80], "provider": pid, "model": chosen["id"], "messages": list(messages) + [{"role": "assistant", "content": text}]})
            brain.save_audit({"event": "auto_chat", "provider": pid, "model": chosen["id"], "chat_id": cid})
            return {"ok": True, "text": text, "provider": pid, "model": chosen["id"], "latency_ms": latency, "chat_id": cid, "candidates": r["candidates"], "resource": r["resource"]}
        except Exception as e:
            last.append({"provider": pid, "error": brain.boundary(pid, e)})
    from fastapi.responses import JSONResponse
    return JSONResponse({"ok": False, "error": "No eligible provider/model under the current privacy, credential, approval and resource policy.", "attempts": last, "resource": r["resource"], "candidates": r["candidates"]}, 503)


def install_policy(brain):
    brain.route = lambda body: route(body, brain)
    brain.auto_chat = lambda body: auto_chat(body, brain)
    app = brain.APP
    app.router.routes[:] = [r for r in app.router.routes if getattr(r, "path", "") not in ("/api/route", "/api/auto-chat")]
    app.add_api_route("/api/route", brain.route, methods=["POST"])
    app.add_api_route("/api/auto-chat", brain.auto_chat, methods=["POST"])
