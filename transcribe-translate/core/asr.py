from __future__ import annotations
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

import requests

from .config import require_openai_key

@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = None

@dataclass
class Transcript:
    text: str
    segments: list[Segment]
    language: str | None
    backend: str
    model: str

Progress = Callable[[str], None]

class LocalWhisperX:
    def __init__(self, model: str, language: str, diarize: bool, device: str, compute_type: str, progress: Progress = print):
        self.model = model
        self.language = language
        self.diarize = diarize
        self.device = device
        self.compute_type = compute_type
        self.progress = progress

    def transcribe(self, audio_path: Path) -> Transcript:
        try:
            import torch
            import whisperx
        except ImportError as exc:
            raise RuntimeError("WhisperX is not installed. Run setup.bat.") from exc

        device = self.device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = self.compute_type
        if compute == "auto":
            compute = "float16" if device == "cuda" else "int8"

        self.progress(f"Local WhisperX: model={self.model}, device={device}, compute={compute}")
        audio = whisperx.load_audio(str(audio_path))
        model = whisperx.load_model(self.model, device=device, compute_type=compute)
        language = None if self.language == "auto" else self.language
        result = model.transcribe(audio, language=language, batch_size=4 if device == "cpu" else 16)

        detected = result.get("language") or language
        segments = [
            Segment(float(s.get("start", 0)), float(s.get("end", 0)), str(s.get("text", "")).strip(), s.get("speaker"))
            for s in result.get("segments", []) if str(s.get("text", "")).strip()
        ]

        if self.diarize:
            token = os.getenv("HF_TOKEN", "").strip()
            if not token:
                raise RuntimeError("HF_TOKEN is required for local speaker diarization.")
            try:
                from whisperx.diarize import DiarizationPipeline
            except ImportError as exc:
                raise RuntimeError("Installed WhisperX does not expose its diarization module.") from exc

            self.progress("Running WhisperX speaker diarization...")
            diarizer = DiarizationPipeline(token=token, device=device)
            diarize_segments = diarizer(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            segments = [
                Segment(float(s.get("start", 0)), float(s.get("end", 0)), str(s.get("text", "")).strip(), s.get("speaker"))
                for s in result.get("segments", []) if str(s.get("text", "")).strip()
            ]

        text = "\n".join((f"[{s.speaker}] {s.text}" if s.speaker else s.text) for s in segments)
        return Transcript(text=text, segments=segments, language=detected, backend="local-whisperx", model=self.model)

class OpenAIASR:
    def __init__(self, model: str, language: str, diarize: bool, progress: Progress = print):
        self.model = "gpt-4o-transcribe-diarize" if diarize else model
        self.language = language
        self.diarize = diarize
        self.progress = progress

    def transcribe_chunks(self, chunks: list[Path], chunk_seconds: int = 600) -> Transcript:
        key = require_openai_key()
        all_segments: list[Segment] = []
        plain_text: list[str] = []
        for index, chunk in enumerate(chunks, 1):
            self.progress(f"OpenAI ASR: chunk {index}/{len(chunks)}")
            data = {"model": self.model, "response_format": "diarized_json" if self.diarize else "json"}
            if self.diarize:
                data["chunking_strategy"] = "auto"
            if self.language != "auto":
                data["language"] = self.language
            with chunk.open("rb") as fh:
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {key}"},
                    data=data,
                    files={"file": (chunk.name, fh, "audio/mpeg")},
                    timeout=3600,
                )
            if response.status_code >= 400:
                raise RuntimeError(f"OpenAI transcription failed ({response.status_code}): {response.text[:4000]}")
            payload = response.json()
            if self.diarize:
                raw_segments = payload.get("segments", []) or payload.get("speaker_segments", [])
                for s in raw_segments:
                    text = str(s.get("text", "")).strip()
                    if not text:
                        continue
                    all_segments.append(Segment(
                        float(s.get("start", 0)) + (index - 1) * chunk_seconds,
                        float(s.get("end", 0)) + (index - 1) * chunk_seconds,
                        text,
                        s.get("speaker"),
                    ))
            else:
                plain_text.append(str(payload.get("text", "")).strip())
        if self.diarize:
            text = "\n".join(f"[{s.speaker}] {s.text}" if s.speaker else s.text for s in all_segments)
            return Transcript(text=text, segments=all_segments, language=None if self.language == "auto" else self.language, backend="openai", model=self.model)
        text = "\n".join(x for x in plain_text if x)
        return Transcript(text=text, segments=[Segment(0, 0, text)] if text else [], language=None if self.language == "auto" else self.language, backend="openai", model=self.model)
