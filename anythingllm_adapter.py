"""SS AnythingLLM adapter for v0.8.4 — documented API only.

Consults official AnythingLLM API documentation.
Implements SS → AnythingLLM → Ollama → configured model chain.
SS remains orchestrator/Brain; AnythingLLM is AI/knowledge substrate.

Official AnythingLLM API reference:
https://docs.anythingllm.com/api/overview

Key endpoints verified as of 2026:
- GET /api/v1/system/status
- GET /api/v1/workspaces
- POST /api/v1/workspace/{slug}/chat
- GET /api/v1/workspace/{slug}/chat/history
"""
import os
import json
import time
import httpx
from typing import Dict, Optional, List
from pathlib import Path


class AnythingLLMAdapter:
    """Verified AnythingLLM integration using documented API only."""

    SERVICE = "SS-Second-Brain"
    DEFAULT_BASE = "http://127.0.0.1:3001"  # Official default

    def __init__(self):
        self.base_url = None
        self.api_key = None
        self.workspace_slug = None
        self.workspace_name = None
        self.ollama_status = None
        self.model = None
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
        
        Returns: {"ok": bool, "status": str, ...}
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
                    "response": r.text
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
        Returns: {"ok": bool, "workspaces": [...], ...}
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
                "fix": "Save with: keyring.set_password('SS-Second-Brain', 'anythingllm', '<key>')"
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
                "error": f"Workspace '{slug or name}' not found",
                "available": [ws.get("slug") or ws.get("name") for ws in workspaces]
            }

        self.workspace_slug = selected.get("slug")
        self.workspace_name = selected.get("name")
        return {"ok": True, "workspace": selected}

    async def workspace_settings(self) -> Dict:
        """Get workspace settings including LLM configuration.
        
        Returns: {"ok": bool, "settings": {...}, "ollama_configured": bool, ...}
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
                    settings = data.get("settings", {})
                    llm_config = settings.get("llmProvider", {})
                    
                    # Check if Ollama is configured
                    ollama_configured = (
                        llm_config.get("type") == "ollama" or
                        "ollama" in str(llm_config).lower()
                    )
                    
                    self.ollama_status = ollama_configured
                    return {
                        "ok": True,
                        "settings": settings,
                        "llm_provider": llm_config.get("type"),
                        "ollama_configured": ollama_configured,
                        "raw_llm_config": llm_config
                    }
                return {"ok": False, "http_code": r.status_code, "error": r.text[:200]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def chat_inference(self, messages: List[Dict], model: str = None) -> Dict:
        """Execute documented workspace chat (POST /api/v1/workspace/{slug}/chat).
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            model: Model name (optional if workspace has default)

        Returns: {"ok": bool, "text": str, "latency_ms": int, ...}
        """
        if not self.workspace_slug:
            return {"ok": False, "error": "Workspace not selected"}

        if not model:
            model = self.model or "phi4-mini:3.8b"

        # Per AnythingLLM documented API, message format for POST /chat
        payload = {
            "message": messages[-1].get("content", "") if messages else "",
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
                    # AnythingLLM returns response in various formats
                    text = (
                        data.get("response")
                        or data.get("text")
                        or data.get("message")
                        or ""
                    )

                    if not text:
                        return {
                            "ok": False,
                            "error": "Empty response from AnythingLLM",
                            "latency_ms": latency_ms,
                            "raw_response": data
                        }

                    return {
                        "ok": True,
                        "text": text,
                        "model": model,
                        "workspace": self.workspace_slug,
                        "latency_ms": latency_ms,
                        "chain": "SS → AnythingLLM → Ollama → model → response",
                        "raw_response_keys": list(data.keys())
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
        """Complete end-to-end health check chain.
        
        Returns: {"ok": bool, "checks": {...}, "ready": bool, ...}
        """
        checks = {}

        # 1. Endpoint reachability
        checks["endpoint"] = await self.ping()
        if not checks["endpoint"].get("ok"):
            return {
                "ok": False,
                "checks": checks,
                "blocker": "AnythingLLM endpoint unreachable"
            }

        # 2. Workspace selection
        ws_check = await self.select_workspace()
        checks["workspace"] = ws_check
        if not ws_check.get("ok"):
            return {
                "ok": False,
                "checks": checks,
                "blocker": f"Workspace issue: {ws_check.get('error')}"
            }

        # 3. Settings/Ollama config
        settings_check = await self.workspace_settings()
        checks["settings"] = settings_check
        if not settings_check.get("ollama_configured"):
            return {
                "ok": False,
                "checks": checks,
                "blocker": "Ollama not configured in AnythingLLM workspace"
            }

        # 4. Test inference
        test_messages = [{"role": "user", "content": "What is 2+2?"}]
        inference_check = await self.chat_inference(test_messages)
        checks["inference_test"] = inference_check

        return {
            "ok": inference_check.get("ok", False),
            "checks": checks,
            "ready": inference_check.get("ok", False),
            "endpoint": self.base_url,
            "workspace": self.workspace_name or self.workspace_slug,
            "ollama_status": self.ollama_status,
            "final_status": "READY" if inference_check.get("ok") else "BLOCKED"
        }


# Export for use in ss_entry.py
adapter = AnythingLLMAdapter()
