from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json

from .asr import FasterWhisperASR
from .config import AppConfig
from .media import extract_audio, prepare_media, is_url
from .outputs import write_outputs
from .text import OllamaTextProvider

LANGUAGE_NAMES = {
    "ca": "Catalan", "es": "Spanish", "en": "English",
    "fr": "French", "de": "German", "it": "Italian",
}

def run_job(source: str, cfg: AppConfig, output_root: Path, progress=print) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    job_dir = output_root / f"{stamp}_{Path(source).stem[:80] if not is_url(source) else 'youtube'}"
    work = job_dir / "_work"
    work.mkdir(parents=True, exist_ok=True)

    progress("Preparing media...")
    media = prepare_media(source, work, cfg.ytdlp_path)
    progress("Extracting 16 kHz mono audio...")
    audio = extract_audio(media, work / "audio.wav")

    transcript = FasterWhisperASR(
        cfg.local_model, cfg.language, cfg.compute_type, progress
    ).transcribe(audio)

    source_name = LANGUAGE_NAMES.get(transcript.language or cfg.language, transcript.language or "source language")
    target_name = LANGUAGE_NAMES.get(cfg.target_language, cfg.target_language)

    progress(f"Transcript complete: detected language={source_name}")
    provider = OllamaTextProvider(cfg.ollama_url, cfg.ollama_model, progress)
    translation = provider.translate(transcript.text, target_name)
    source_summary = provider.summarize(transcript.text, source_name)
    english_summary = provider.summarize(translation, target_name)

    write_outputs(
        transcript, translation, source_summary, english_summary, job_dir, source
    )
    metadata = {
        "source": source,
        "language": transcript.language,
        "asr_backend": transcript.backend,
        "asr_model": transcript.model,
        "text_provider": "ollama",
        "text_model": cfg.ollama_model,
        "target_language": cfg.target_language,
        "api_cost": "0: no OpenAI API calls are made",
    }
    (job_dir / "job.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    progress(f"COMPLETE: {job_dir}")
    return job_dir
