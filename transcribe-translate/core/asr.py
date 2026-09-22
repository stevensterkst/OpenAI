from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

@dataclass
class Word:
    start: float
    end: float
    word: str
    probability: float | None = None

@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word] | None = None

@dataclass
class Transcript:
    text: str
    segments: list[Segment]
    language: str | None
    backend: str
    model: str

Progress = Callable[[str], None]

class FasterWhisperASR:
    def __init__(
        self,
        model: str,
        language: str,
        compute_type: str,
        hotwords: str = "",
        word_timestamps: bool = True,
        progress: Progress = print,
    ):
        self.model_name = model
        self.language = language
        self.compute_type = compute_type
        self.hotwords = hotwords.strip()
        self.word_timestamps = word_timestamps
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
        if self.hotwords:
            self.progress(f"Vocabulary bias enabled: {self.hotwords}")

        model = WhisperModel(self.model_name, device="cpu", compute_type=self.compute_type)
        kwargs = {
            "language": language,
            "beam_size": 5,
            "vad_filter": True,
            "condition_on_previous_text": True,
            "word_timestamps": self.word_timestamps,
        }
        if self.hotwords:
            kwargs["hotwords"] = self.hotwords

        segments, info = model.transcribe(str(audio), **kwargs)
        collected: list[Segment] = []

        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue

            words = None
            if self.word_timestamps and getattr(segment, "words", None):
                words = []
                for word in segment.words:
                    words.append(
                        Word(
                            start=float(word.start),
                            end=float(word.end),
                            word=str(word.word),
                            probability=(
                                float(word.probability)
                                if getattr(word, "probability", None) is not None
                                else None
                            ),
                        )
                    )

            collected.append(
                Segment(
                    start=float(segment.start),
                    end=float(segment.end),
                    text=text,
                    words=words,
                )
            )

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
