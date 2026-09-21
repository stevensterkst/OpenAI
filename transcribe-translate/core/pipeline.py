from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json
import shutil
from typing import Callable

from .asr import LocalWhisperX, OpenAIASR, Transcript
from .config import AppConfig
from .media import chunk_audio, download_youtube, extract_audio, is_url
from .outputs import write_transcript
from .translate import OllamaTextProvider, OpenAITextProvider

Progress = Callable[[str], None]

def run_job(source: str, cfg: AppConfig, output_root: Path, progress: Progress = print) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    job_dir = output_root / f"{stamp}_{Path(source).stem[:80] if not is_url(source) else 'youtube'}"
    job_dir.mkdir(parents=True, exist_ok=True)
    work = job_dir / "_work"
    work.mkdir()

    if is_url(source):
        progress("Downloading YouTube media with yt-dlp...")
        media = download_youtube(source, work)
    else:
        media = Path(source).expanduser().resolve()
        if not media.exists():
            raise FileNotFoundError(media)
        shutil.copy2(media, work / media.name)
        media = work / media.name

    progress("Extracting 16 kHz mono audio...")
    audio = extract_audio(media, work / "audio.wav")

    if cfg.asr_backend == "local":
        transcript = LocalWhisperX(cfg.local_model, cfg.language, cfg.diarize, cfg.device, cfg.compute_type, progress).transcribe(audio)
    elif cfg.asr_backend == "openai":
        chunks = chunk_audio(audio, work / "chunks")
        transcript = OpenAIASR(cfg.openai_model if hasattr(cfg, "openai_model") else "gpt-4o-transcribe", cfg.language, cfg.diarize, progress).transcribe_chunks(chunks)
    else:
        raise ValueError(f"Unsupported ASR backend: {cfg.asr_backend}")

    write_transcript(transcript, job_dir, "original")

    provider = OllamaTextProvider(cfg.ollama_url, cfg.ollama_model, progress) if cfg.text_provider == "ollama" else OpenAITextProvider(cfg.openai_model, progress)
    progress(f"Translating to {cfg.target_language}...")
    translation = provider.translate(transcript.text, cfg.target_language)
    (job_dir / "english.txt").write_text(translation, encoding="utf-8")

    progress("Creating summaries...")
    original_summary = provider.summarize(transcript.text, cfg.language if cfg.language != "auto" else "the source language")
    translated_summary = provider.summarize(translation, cfg.target_language)
    (job_dir / "bilingual-summary.md").write_text(
        f"# Original-language summary\n\n{original_summary}\n\n# English summary\n\n{translated_summary}\n",
        encoding="utf-8"
    )
    (job_dir / "summary.md").write_text(translated_summary + "\n", encoding="utf-8")

    metadata = {
        "source": source,
        "media": str(media),
        "asr_backend": transcript.backend,
        "asr_model": transcript.model,
        "language": transcript.language,
        "text_provider": cfg.text_provider,
        "target_language": cfg.target_language,
    }
    (job_dir / "job.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    progress(f"COMPLETE: {job_dir}")
    return job_dir
