"""Optional local coding-agent bridge for SS v0.8.4.

This does not store credentials. It only invokes fixed, user-installed CLIs that
are already authenticated on the local machine. SS never uses dangerous
permission-bypass flags automatically.
"""
from __future__ import annotations
import json, os, shutil, subprocess
from typing import Dict

AGENTS = {
    "claude_code": {"name": "Claude Code", "command": "claude", "mode": "print"},
    "gemini_cli": {"name": "Gemini CLI", "command": "gemini", "mode": "print"},
}

def status() -> Dict[str, dict]:
    out = {}
    for aid, cfg in AGENTS.items():
        exe = shutil.which(cfg["command"])
        out[aid] = {"name": cfg["name"], "installed": bool(exe), "executable": exe}
    return out

def run_agent(agent: str, prompt: str, model: str | None = None, cwd: str | None = None,
              timeout: int = 600) -> dict:
    if agent not in AGENTS:
        raise ValueError("Unknown local coding agent")
    if not prompt.strip():
        raise ValueError("Prompt required")
    cfg = AGENTS[agent]
    exe = shutil.which(cfg["command"])
    if not exe:
        raise RuntimeError(f"{cfg['name']} is not installed or is not on PATH")
    args = [exe]
    if agent == "claude_code":
        args += ["-p", "--output-format", "json", "--permission-mode", "plan"]
        if model: args += ["--model", model]
    elif agent == "gemini_cli":
        args += ["-p", prompt]
        if model: args += ["--model", model]
    if agent != "gemini_cli":
        args += [prompt]
    workdir = cwd or os.getcwd()
    if not os.path.isdir(workdir):
        raise ValueError("Requested agent working directory does not exist")
    p = subprocess.run(args, cwd=workdir, capture_output=True, text=True,
                       timeout=max(30, min(int(timeout), 1800)), shell=False)
    raw = (p.stdout or "").strip()
    if p.returncode:
        err = (p.stderr or raw or "agent exited with an error").strip()
        raise RuntimeError(err[-4000:])
    text = raw
    if agent == "claude_code":
        try:
            obj = json.loads(raw)
            text = obj.get("result") or obj.get("content") or raw
        except Exception:
            pass
    return {"ok": True, "agent": agent, "name": cfg["name"], "text": text,
            "working_directory": os.path.abspath(workdir)}
