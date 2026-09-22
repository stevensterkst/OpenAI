from __future__ import annotations
from datetime import datetime
from pathlib import Path
import hashlib
import json

from .asr import FasterWhisperASR
from .config import AppConfig
from .media import extract_audio, prepare_media, is_url
from .outputs import write_outputs
from .text import OllamaTextProvider, model_advice

LANGUAGE_NAMES = {
    "ca": "Catalan", "es": "Spanish", "en": "English",
    "fr": "French", "de": "German", "it": "Italian",
    "nl": "Dutch", "pt": "Portuguese", "pl": "Polish",
    "ru": "Russian", "uk": "Ukrainian",
}

def timestamped_transcript(transcript) -> str:
    lines = []
    for segment in transcript.segments:
        start = int(segment.start)
        h, rem = divmod(start, 3600)
        m, s = divmod(rem, 60)
        lines.append(f"[{h:02d}:{m:02d}:{s:02d}] {segment.text}")
    return "\n".join(lines)

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def run_job(source: str, cfg: AppConfig, output_root: Path, progress=print) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    stem = Path(source).stem[:80] if not is_url(source) else "youtube"
    job_dir = output_root / f"{stamp}_{stem}"
    work = job_dir / "_work"
    work.mkdir(parents=True, exist_ok=True)

    progress("Preparing media...")
    media = prepare_media(source, work, cfg.ytdlp_path)
    media_hash = sha256_file(media)
    progress(f"Input SHA-256: {media_hash}")

    progress("Extracting 16 kHz mono audio...")
    audio = extract_audio(media, work / "audio.wav")

    transcript = FasterWhisperASR(
        cfg.local_model,
        cfg.language,
        cfg.compute_type,
        hotwords=cfg.hotwords,
        word_timestamps=cfg.word_timestamps,
        progress=progress,
    ).transcribe(audio)

    detected_code = transcript.language or cfg.language
    source_name = LANGUAGE_NAMES.get(detected_code, detected_code or "source language")
    progress(f"PRIMARY TRANSCRIPT COMPLETE: {source_name}")

    provider = OllamaTextProvider(cfg.ollama_url, cfg.ollama_model, progress)

    source_summary = provider.summarize_source(transcript.text, source_name)
    english_summary = provider.translate_summary_to_english(source_summary, source_name)

    analysis = ""
    if cfg.analysis:
        analysis = provider.analyze_source(timestamped_transcript(transcript), source_name)

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
        analysis,
        job_dir,
        source,
        translated=cfg.translate_transcript,
        target_language=cfg.target_language,
        analysis_created=cfg.analysis,
    )

    tier, advice = model_advice(cfg.ollama_model)
    metadata = {
        "source": source,
        "input_media_sha256": media_hash,
        "language": transcript.language,
        "asr_backend": transcript.backend,
        "asr_model": transcript.model,
        "word_timestamps": cfg.word_timestamps,
        "hotwords": cfg.hotwords,
        "text_provider": "ollama",
        "text_model": cfg.ollama_model,
        "ollama_model_advice": {"tier": tier, "note": advice},
        "source_summary": "generated from original-language transcript",
        "english_summary": "translation of source-language summary",
        "analysis": "generated from timestamped original-language transcript" if cfg.analysis else None,
        "full_transcript_translation": cfg.translate_transcript,
        "target_language": cfg.target_language if cfg.translate_transcript else None,
        "api_cost": "0: no OpenAI API calls are made by this application",
    }
    (job_dir / "job.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    progress(f"COMPLETE: {job_dir}")
    return job_dir
