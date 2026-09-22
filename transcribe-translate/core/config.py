from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

@dataclass
class AppConfig:
    local_model: str = "small"
    language: str = "auto"
    compute_type: str = "int8"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    target_language: str = "English"
    translate_transcript: bool = False
    output_dir: str = "output"
    ytdlp_path: str = ""

def load_config(path: Path | None = None) -> AppConfig:
    path = path or (ROOT / "config.json")
    data: dict[str, Any] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    asr = data.get("asr", {})
    text = data.get("text", {})
    paths = data.get("paths", {})
    return AppConfig(
        local_model=asr.get("local_model", "small"),
        language=asr.get("language", "auto"),
        compute_type=asr.get("compute_type", "int8"),
        ollama_url=text.get("ollama_url", "http://127.0.0.1:11434"),
        ollama_model=text.get("ollama_model", ""),
        target_language=text.get("target_language", "English"),
        translate_transcript=bool(text.get("translate_transcript", False)),
        output_dir=paths.get("output_dir", "output"),
        ytdlp_path=paths.get("ytdlp_path", ""),
    )
