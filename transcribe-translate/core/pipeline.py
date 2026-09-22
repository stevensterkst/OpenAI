from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json

from .asr import FasterWhisperASR
from .config import AppConfig
from .media import extract_audio, prepare_media, is_url
from .outputs import write_outputs
from .text import OllamaTextProvider, model_advice

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

    source_name = LANGUAGE_NAMES.get(
        transcript.language or cfg.language,
        transcript.language or "source language",
    )
    progress(f"PRIMARY TRANSCRIPT COMPLETE: {source_name}")

    provider = OllamaTextProvider(cfg.ollama_url, cfg.ollama_model, progress)

    # PRIMARY summary: original-language transcript -> original-language summary.
    source_summary = provider.summarize_source(transcript.text, source_name)

    # English summary is ONLY a translation of the primary source summary.
    english_summary = provider.translate_summary_to_english(source_summary, source_name)

    # Optional full transcript translation; independent of the summaries.
    translation = ""
    if cfg.translate_transcript:
        translation = provider.translate(
            transcript.text, cfg.target_language, purpose="transcript"
        )

    write_outputs(
        transcript,
        translation,
        source_summary,
        english_summary,
        job_dir,
        source,
        translated=cfg.translate_transcript,
        target_language=cfg.target_language,
    )

    tier, advice = model_advice(cfg.ollama_model)
    metadata = {
        "source": source,
        "language": transcript.language,
        "asr_backend": transcript.backend,
        "asr_model": transcript.model,
        "text_provider": "ollama",
        "text_model": cfg.ollama_model,
        "ollama_model_advice": {"tier": tier, "note": advice},
        "source_summary": "generated from original-language transcript",
        "english_summary": "translation of source-language summary",
        "full_transcript_translation": cfg.translate_transcript,
        "target_language": cfg.target_language if cfg.translate_transcript else None,
        "api_cost": "0: no OpenAI API calls are made by this application",
    }
    (job_dir / "job.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    progress(f"COMPLETE: {job_dir}")
    return job_dir
