from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

@dataclass
class Segment:
    start: float
    end: float
    text: str

@dataclass
class Transcript:
    text: str
    segments: list[Segment]
    language: str | None
    backend: str
    model: str

Progress = Callable[[str], None]

class FasterWhisperASR:
    def __init__(self, model: str, language: str, compute_type: str, progress: Progress = print):
        self.model_name = model
        self.language = language
        self.compute_type = compute_type
        self.progress = progress

    def transcribe(self, audio: Path) -> Transcript:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. The current free architecture requires "
                "faster-whisper + CTranslate2; WhisperX and Torch are not required."
            ) from exc

        language = None if self.language == "auto" else self.language
        self.progress(
            f"Local transcription: faster-whisper model={self.model_name}, "
            f"device=cpu, compute={self.compute_type}"
        )
        model = WhisperModel(self.model_name, device="cpu", compute_type=self.compute_type)
        segments, info = model.transcribe(
            str(audio),
            language=language,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=True,
        )
        collected: list[Segment] = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                collected.append(Segment(float(segment.start), float(segment.end), text))

        detected = getattr(info, "language", None) or language
        text = "\n".join(s.text for s in collected)
        return Transcript(
            text=text,
            segments=collected,
            language=detected,
            backend="faster-whisper",
            model=self.model_name,
        )

def transcript_dict(transcript: Transcript) -> dict:
    return {
        "text": transcript.text,
        "language": transcript.language,
        "backend": transcript.backend,
        "model": transcript.model,
        "segments": [asdict(s) for s in transcript.segments],
    }
