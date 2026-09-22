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
    # Bound the decoded WAV passed to faster-whisper. Long recordings can otherwise
    # trigger multi-GB NumPy STFT allocations before inference starts.
    # Keep each decode request comfortably below the RAM ceiling of the Windows PC.
    CHUNK_SECONDS = 20

    def __init__(self, model: str, language: str, compute_type: str,
                 hotwords: str = "", word_timestamps: bool = True,
                 progress: Progress = print):
        self.model_name = model
        self.language = language
        self.compute_type = compute_type
        self.hotwords = hotwords.strip()
        self.word_timestamps = word_timestamps
        self.progress = progress

    def _run(self, model, audio, language, vad_filter):
        kwargs = {
            "language": language, "beam_size": 3, "batch_size": 1,
            "vad_filter": vad_filter, "condition_on_previous_text": False,
            "word_timestamps": self.word_timestamps,
        }
        if self.hotwords:
            kwargs["hotwords"] = self.hotwords
        return model.transcribe(str(audio), **kwargs)

    def _collect(self, model, audio, language):
        segments, info = self._run(model, audio, language, True)
        collected = []
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue
            words = None
            if self.word_timestamps and getattr(segment, "words", None):
                words = [Word(float(w.start), float(w.end), str(w.word),
                    float(w.probability) if getattr(w, "probability", None) is not None else None)
                    for w in segment.words]
            collected.append(Segment(float(segment.start), float(segment.end), text, words=words))
        if not collected:
            self.progress("No speech survived VAD in this chunk; retrying without VAD.")
            segments, info = self._run(model, audio, language, False)
            for segment in segments:
                text = segment.text.strip()
                if not text:
                    continue
                words = None
                if self.word_timestamps and getattr(segment, "words", None):
                    words = [Word(float(w.start), float(w.end), str(w.word),
                        float(w.probability) if getattr(w, "probability", None) is not None else None)
                        for w in segment.words]
                collected.append(Segment(float(segment.start), float(segment.end), text, words=words))
        return collected, info

    def transcribe(self, audio: Path) -> Transcript:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("faster-whisper is not installed; Torch/WhisperX are not required.") from exc

        import wave
        import numpy as np
        language = None if self.language == "auto" else self.language
        self.progress(f"Local transcription: faster-whisper model={self.model_name}, device=cpu, compute={self.compute_type}")
        if self.hotwords:
            self.progress(f"Vocabulary bias enabled: {self.hotwords}")

        with wave.open(str(audio), "rb") as wf:
            channels, width, rate, frames = wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()
            duration = frames / float(rate or 1)
            if (channels, width, rate) != (1, 2, 16000):
                raise RuntimeError(f"Internal audio format is {rate} Hz, {channels} channel(s), {width*8}-bit; expected 16000 Hz mono 16-bit PCM WAV.")
            self.progress(f"Audio duration: {duration/60:.1f} minutes")
            model = WhisperModel(self.model_name, device="cpu", compute_type=self.compute_type)

            chunk_frames = self.CHUNK_SECONDS * rate
            ranges = [(start, min(frames, start + chunk_frames)) for start in range(0, frames, chunk_frames)]
            if len(ranges) > 1:
                self.progress(f"Long-recording safety: {len(ranges)} sequential {self.CHUNK_SECONDS//60}-minute chunks; memory is bounded.")

            all_segments = []
            detected_language = None
            with __import__("contextlib").nullcontext():
                for i, (start, end) in enumerate(ranges, 1):
                    offset = start / float(rate)
                    wf.setpos(start)
                    raw = wf.readframes(end - start)
                    # Decode directly from the bounded NumPy chunk. This guarantees
                    # faster-whisper receives at most CHUNK_SECONDS of audio per request.
                    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                    self.progress(f"Transcribing chunk {i}/{len(ranges)} ({offset/60:.1f} min)…")
                    collected, info = self._collect(model, samples, language if language else detected_language)
                    if detected_language is None:
                        detected_language = getattr(info, "language", None) or language
                    for s in collected:
                        s.start += offset; s.end += offset
                        if s.words:
                            for w in s.words:
                                w.start += offset; w.end += offset
                        all_segments.append(s)

        if not all_segments:
            raise RuntimeError("Local transcription produced zero speech segments. No downstream AI stage was run.")
        return Transcript(
            text="\n".join(s.text for s in all_segments),
            segments=all_segments, language=detected_language,
            backend="faster-whisper", model=self.model_name,
        )

def transcript_dict(transcript: Transcript) -> dict:
    return {
        "text": transcript.text, "language": transcript.language,
        "backend": transcript.backend, "model": transcript.model,
        "segments": [asdict(s) for s in transcript.segments],
    }
