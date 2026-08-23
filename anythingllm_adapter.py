"""SS AnythingLLM adapter for v0.8.4 — documented API only.

Consults official AnythingLLM OpenAPI specification.
Implements SS → AnythingLLM → configured provider/model chain.
SS remains orchestrator/Brain; AnythingLLM is AI/knowledge substrate.

OFFICIAL AnythingLLM API endpoints (verified against current spec):
- GET /api/v1/system/status
- GET /api/v1/workspaces
- GET /api/v1/workspace/{slug}/settings
- POST /api/v1/workspace/{slug}/chat

CRITICAL: The workspace has a CONFIGURED provider and model.
SS does NOT discover/invent models. SS queries the workspace config,
then sends messages. AnythingLLM enforces the configured model.

Response schema per official spec:
  POST /api/v1/workspace/{slug}/chat returns:
  {
    "textResponse": "...",      ← Actual generated text
    "close": false,
    "error": null
  }
"""
import os
import json
import time
import httpx
from typing import Dict, Optional, List
from pathlib import Path


class AnythingLLMAdapter:
    """Verified AnythingLLM integration using official documented API only."""

    SERVICE = "SS-Second-Brain"
    DEFAULT_BASE = "http://127.0.0.1:3001"  # Official default port

    def __init__(self):
        self.base_url = None
        self.api_key = None
        self.workspace_slug = None
        self.workspace_name = None
        self.workspace_config = None  # Store actual workspace settings
        self.last_error = None

    def discover_endpoint(self) -> Dict:
        """Discover AnythingLLM endpoint from environment or default.
        
        Returns: {"ok": bool, "endpoint": str, "source": str}
        """
        # 1. Check environment variable
        env_base = os.environ.get("ANYTHINGLLM_BASE", "").strip()
        if env_base:
            self.base_url = env_base.rstrip("/")
            return {"ok": True, "endpoint": self.base_url, "source": "environment"}

        # 2. Default local
        self.base_url = self.DEFAULT_BASE
        return {"ok": True, "endpoint": self.base_url, "source": "default"}

    async def ping(self) -> Dict:
        """Verify AnythingLLM is reachable (GET /api/v1/system/status).
        
        Returns: {"ok": bool, "status": str, "version": str, ...}
        """
        if not self.base_url:
            self.discover_endpoint()

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/api/v1/system/status")
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "ok": True,
                        "endpoint": self.base_url,
                        "status": "online",
                        "version": data.get("version", "unknown"),
                        "response": data
                    }
                return {
                    "ok": False,
                    "status": "error",
                    "http_code": r.status_code,
                    "response": r.text[:200]
                }
        except httpx.ConnectError as e:
            self.last_error = f"Connection refused: {str(e)}"
            return {
                "ok": False,
                "status": "unreachable",
                "endpoint": self.base_url,
                "error": self.last_error
            }
        except Exception as e:
            self.last_error = str(e)
            return {"ok": False, "status": "error", "error": self.last_error}

    async def list_workspaces(self) -> Dict:
        """List available workspaces (GET /api/v1/workspaces).
        
        Requires: API key (stored in keyring)
        Returns: {"ok": bool, "workspaces": [...], "count": int}
        """
        if not self.base_url:
            self.discover_endpoint()

        # Retrieve API key from OS credential store
        try:
            import keyring
            self.api_key = keyring.get_password(self.SERVICE, "anythingllm")
        except Exception:
            self.api_key = None

        if not self.api_key:
            return {
                "ok": False,
                "error": "AnythingLLM API key not configured in OS credential store.",
                "fix": "Set with: keyring.set_password('SS-Second-Brain', 'anythingllm', '<api-key>')"
            }

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self.base_url}/api/v1/workspaces", headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    workspaces = data.get("workspaces", [])
                    return {
                        "ok": True,
                        "workspaces": workspaces,
                        "count": len(workspaces)
                    }
                return {
                    "ok": False,
                    "http_code": r.status_code,
                    "error": r.text[:200]
                }
        except Exception as e:
            self.last_error = str(e)
            return {"ok": False, "error": self.last_error}

    async def select_workspace(self, slug: str = None, name: str = None) -> Dict:
        """Select a workspace by slug or name.
        
        If neither provided, uses the first available.
        Returns: {"ok": bool, "workspace": {...}, ...}
        """
        ws_result = await self.list_workspaces()
        if not ws_result.get("ok"):
            return ws_result

        workspaces = ws_result.get("workspaces", [])
        if not workspaces:
            return {"ok": False, "error": "No workspaces configured in AnythingLLM"}

        # Find workspace by slug or name
        selected = None
        if slug:
            selected = next((ws for ws in workspaces if ws.get("slug") == slug), None)
        elif name:
            selected = next((ws for ws in workspaces if ws.get("name") == name), None)
        else:
            selected = workspaces[0]  # Default to first

        if not selected:
            return {
                "ok": False,
                "error": f"Workspace not found",
                "available": [ws.get("slug") or ws.get("name") for ws in workspaces]
            }

        self.workspace_slug = selected.get("slug")
        self.workspace_name = selected.get("name")
        return {"ok": True, "workspace": selected}

    async def workspace_config(self) -> Dict:
        """Get workspace configuration including LLM provider and model.
        
        AnythingLLM workspace has a CONFIGURED chatProvider and chatModel.
        SS reports these; does NOT invent or override them.
        
        Returns: {"ok": bool, "llm_provider": str, "llm_model": str, ...}
        """
        if not self.workspace_slug:
            return {"ok": False, "error": "Workspace not selected"}

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{self.base_url}/api/v1/workspace/{self.workspace_slug}/settings",
                    headers=headers
                )
                if r.status_code == 200:
                    data = r.json()
                    # Store actual workspace configuration
                    self.workspace_config = data
                    
                    # Extract provider and model from workspace config
                    # Per AnythingLLM spec, these are at workspace level
                    provider = data.get("chatProvider") or data.get("llmProvider") or "unknown"
                    model = data.get("chatModel") or data.get("llmModel") or "unknown"
                    
                    return {
                        "ok": True,
                        "llm_provider": provider,
                        "llm_model": model,
                        "configured": True,
                        "config": data
                    }
                return {"ok": False, "http_code": r.status_code, "error": r.text[:200]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def chat_inference(self, messages: List[Dict]) -> Dict:
        """Execute documented workspace chat (POST /api/v1/workspace/{slug}/chat).
        
        CRITICAL: Uses ACTUAL AnythingLLM response schema.
        Per official spec, response contains 'textResponse', not 'response' or 'text'.
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": str}

        Returns: {"ok": bool, "text": str, "latency_ms": int, "model": str, ...}
        """
        if not self.workspace_slug:
            return {"ok": False, "error": "Workspace not selected"}

        # Extract user message (last user message in thread)
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return {"ok": False, "error": "No user message in thread"}

        # Payload per official AnythingLLM API spec
        payload = {
            "message": user_message,
            "mode": "chat"
        }

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            start = time.perf_counter()

            async with httpx.AsyncClient(timeout=300) as client:
                r = await client.post(
                    f"{self.base_url}/api/v1/workspace/{self.workspace_slug}/chat",
                    json=payload,
                    headers=headers
                )
                latency_ms = round((time.perf_counter() - start) * 1000)

                if r.status_code == 200:
                    data = r.json()
                    # OFFICIAL SCHEMA: textResponse is the generated text
                    text = data.get("textResponse", "")
                    error = data.get("error")

                    if error:
                        return {
                            "ok": False,
                            "error": f"AnythingLLM returned error: {error}",
                            "latency_ms": latency_ms
                        }

                    if not text:
                        return {
                            "ok": False,
                            "error": "Empty textResponse from AnythingLLM",
                            "latency_ms": latency_ms,
                            "raw_keys": list(data.keys())
                        }

                    # Get configured model from workspace config
                    model = (self.workspace_config or {}).get("chatModel") or "unknown"

                    return {
                        "ok": True,
                        "text": text,
                        "model": model,
                        "workspace": self.workspace_slug,
                        "latency_ms": latency_ms,
                        "chain": "SS → AnythingLLM → configured provider → configured model",
                        "response_schema": "textResponse (official)"
                    }
                return {
                    "ok": False,
                    "http_code": r.status_code,
                    "error": r.text[:200],
                    "latency_ms": latency_ms
                }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def full_health_check(self) -> Dict:
        """Complete end-to-end health check.
        
        Verifies:
        1. Endpoint reachability
        2. API key validity
        3. Workspace availability
        4. Configured provider/model
        5. ACTUAL inference with real response
        
        Returns: {"ok": bool, "ready": bool, "final_status": str, ...}
        """
        checks = {}

        # 1. Endpoint reachability
        checks["endpoint"] = await self.ping()
        if not checks["endpoint"].get("ok"):
            return {
                "ok": False,
                "checks": checks,
                "final_status": "BLOCKED",
                "blocker": "AnythingLLM endpoint unreachable"
            }

        # 2. Workspace selection
        ws_check = await self.select_workspace()
        checks["workspace"] = ws_check
        if not ws_check.get("ok"):
            return {
                "ok": False,
                "checks": checks,
                "final_status": "BLOCKED",
                "blocker": f"Workspace selection failed: {ws_check.get('error')}"
            }

        # 3. Get actual workspace config (provider/model)
        config_check = await self.workspace_config()
        checks["config"] = config_check
        if not config_check.get("ok"):
            return {
                "ok": False,
                "checks": checks,
                "final_status": "BLOCKED",
                "blocker": f"Workspace config fetch failed: {config_check.get('error')}"
            }

        # 4. Test real inference
        test_messages = [{"role": "user", "content": "What is 2+2?"}]
        inference_check = await self.chat_inference(test_messages)
        checks["inference"] = inference_check

        if not inference_check.get("ok"):
            return {
                "ok": False,
                "checks": checks,
                "final_status": "BLOCKED",
                "blocker": f"Real inference failed: {inference_check.get('error')}"
            }

        # If actual inference succeeded with real text
        if inference_check.get("text") and len(inference_check.get("text", "")) > 0:
            return {
                "ok": True,
                "checks": checks,
                "ready": True,
                "final_status": "READY",
                "endpoint": self.base_url,
                "workspace": self.workspace_name or self.workspace_slug,
                "provider": config_check.get("llm_provider"),
                "model": config_check.get("llm_model"),
                "inference_latency_ms": inference_check.get("latency_ms")
            }
        else:
            return {
                "ok": False,
                "checks": checks,
                "final_status": "BLOCKED",
                "blocker": "Inference produced no actual text"
            }


# Export for use in ss_entry.py
adapter = AnythingLLMAdapter()
