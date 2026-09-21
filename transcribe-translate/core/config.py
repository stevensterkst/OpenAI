from __future__ import annotations
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

@dataclass
class AppConfig:
    asr_backend: str = "local"
    local_model: str = "large-v3"
    language: str = "auto"
    diarize: bool = False
    device: str = "auto"
    compute_type: str = "auto"
    text_provider: str = "ollama"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:1.7b"
    openai_model: str = "gpt-5-mini"
    target_language: str = "en"
    output_dir: str = "output"

def load_config(path: Path | None = None) -> AppConfig:
    path = path or (ROOT / "config.json")
    data: dict[str, Any] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    a, t, p = data.get("asr", {}), data.get("text", {}), data.get("paths", {})
    return AppConfig(
        asr_backend=a.get("backend", "local"),
        local_model=a.get("local_model", "large-v3"),
        language=a.get("language", "auto"),
        diarize=bool(a.get("diarize", False)),
        device=a.get("device", "auto"),
        compute_type=a.get("compute_type", "auto"),
        text_provider=t.get("provider", "ollama"),
        ollama_url=t.get("ollama_url", "http://127.0.0.1:11434"),
        ollama_model=t.get("ollama_model", "qwen3:1.7b"),
        openai_model=t.get("openai_model", "gpt-5-mini"),
        target_language=t.get("target_language", "en"),
        output_dir=p.get("output_dir", "output"),
    )

def require_openai_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Choose a local provider or configure the key.")
    return key
