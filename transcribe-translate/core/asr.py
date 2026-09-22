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
    speaker: str | None = None

@dataclass
class Transcript:
    text: str
    segments: list[Segment]
    language: str | None
    backend: str
    model: str

Progress = Callable[[str], None]

class FasterWhisperASR:
    def __init__(self, model: str, language: str, compute_type: str,
                 hotwords: str = "", word_timestamps: bool = True,
                 progress: Progress = print):
        self.model_name = model
        self.language = language
        self.compute_type = compute_type
        self.hotwords = hotwords.strip()
        self.word_timestamps = word_timestamps
        self.progress = progress

    def _run(self, model, audio: Path, language, vad_filter: bool):
        kwargs = {
            "language": language, "beam_size": 5, "vad_filter": vad_filter,
            "condition_on_previous_text": True, "word_timestamps": self.word_timestamps,
        }
        if self.hotwords:
            kwargs["hotwords"] = self.hotwords
        return model.transcribe(str(audio), **kwargs)

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

        # First pass uses VAD for normal recordings. A zero-segment result is not
        # accepted as a valid transcript: retry once without VAD because very short,
        # quiet, compressed or unusual recordings can be rejected by the VAD stage.
        segments, info = self._run(model, audio, language, vad_filter=True)
        collected: list[Segment] = []
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            words = None
            if self.word_timestamps and getattr(segment, "words", None):
                words = [
                    Word(float(w.start), float(w.end), str(w.word),
                         float(w.probability) if getattr(w, "probability", None) is not None else None)
                    for w in segment.words
                ]
            collected.append(Segment(float(segment.start), float(segment.end), text, words=words))

        if not collected:
            self.progress("No speech segments survived VAD; retrying transcription with VAD disabled.")
            segments, info = self._run(model, audio, language, vad_filter=False)
            for segment in segments:
                text = segment.text.strip()
                if not text:
                    continue
                words = None
                if self.word_timestamps and getattr(segment, "words", None):
                    words = [
                        Word(float(w.start), float(w.end), str(w.word),
                             float(w.probability) if getattr(w, "probability", None) is not None else None)
                        for w in segment.words
                    ]
                collected.append(Segment(float(segment.start), float(segment.end), text, words=words))

        detected = getattr(info, "language", None) or language
        if not collected:
            raise RuntimeError(
                "Local transcription produced zero speech segments after both normal VAD "
                "and the no-VAD retry. No summary or translation was generated because the "
                "source transcript is empty. Check the recording/audio track or choose another test file."
            )

        return Transcript(
            text="\n".join(s.text for s in collected), segments=collected,
            language=detected, backend="faster-whisper", model=self.model_name,
        )

def transcript_dict(transcript: Transcript) -> dict:
    return {
        "text": transcript.text, "language": transcript.language,
        "backend": transcript.backend, "model": transcript.model,
        "segments": [asdict(s) for s in transcript.segments],
    }
