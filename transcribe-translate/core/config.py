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
    word_timestamps: bool = True
    hotwords: str = ""
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    analysis_language: str = "source"
    target_language: str = "English"
    translate_transcript: bool = False
    analysis: bool = True
    search_query: str = ""
    top_terms: int = 30
    qa_question: str = ""
    qa_language: str = "English"
    diarization: bool = False
    diarization_segmentation_model: str = ""
    diarization_embedding_model: str = ""
    diarization_num_speakers: int = 0
    diarization_threshold: float = 0.5
    output_dir: str = "output"
    ytdlp_path: str = ""

def load_config(path: Path | None = None) -> AppConfig:
    path = path or (ROOT / "config.json")
    data: dict[str, Any] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    asr, text, analysis, qa, diar, paths = (
        data.get("asr", {}), data.get("text", {}), data.get("analysis", {}),
        data.get("qa", {}), data.get("diarization", {}), data.get("paths", {})
    )
    return AppConfig(
        local_model=asr.get("local_model", "small"), language=asr.get("language", "auto"),
        compute_type=asr.get("compute_type", "int8"), word_timestamps=bool(asr.get("word_timestamps", True)),
        hotwords=str(asr.get("hotwords", "")), ollama_url=text.get("ollama_url", "http://127.0.0.1:11434"),
        ollama_model=text.get("ollama_model", ""), analysis_language=str(text.get("analysis_language", "source")),
        target_language=text.get("target_language", "English"), translate_transcript=bool(text.get("translate_transcript", False)),
        analysis=bool(text.get("analysis", True)), search_query=str(analysis.get("search_query", "")),
        top_terms=int(analysis.get("top_terms", 30)), qa_question=str(qa.get("question", "")),
        qa_language=str(qa.get("language", "English")), diarization=bool(diar.get("enabled", False)),
        diarization_segmentation_model=str(diar.get("segmentation_model", "")),
        diarization_embedding_model=str(diar.get("embedding_model", "")),
        diarization_num_speakers=int(diar.get("num_speakers", 0)),
        diarization_threshold=float(diar.get("cluster_threshold", 0.5)),
        output_dir=paths.get("output_dir", "output"), ytdlp_path=paths.get("ytdlp_path", ""),
    )
