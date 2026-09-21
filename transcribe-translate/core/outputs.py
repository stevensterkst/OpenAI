from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from .asr import Transcript

def _ts(seconds: float, comma: bool = True) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        s += 1; ms = 0
    sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"

def write_transcript(transcript: Transcript, directory: Path, stem: str = "original") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{stem}.txt").write_text(transcript.text, encoding="utf-8")
    (directory / f"{stem}.json").write_text(json.dumps({
        "text": transcript.text,
        "language": transcript.language,
        "backend": transcript.backend,
        "model": transcript.model,
        "segments": [asdict(s) for s in transcript.segments],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    if any(s.end > s.start for s in transcript.segments):
        srt, vtt = [], ["WEBVTT", ""]
        for i, s in enumerate(transcript.segments, 1):
            body = f"[{s.speaker}] {s.text}" if s.speaker else s.text
            srt.extend([str(i), f"{_ts(s.start)} --> {_ts(s.end)}", body, ""])
            vtt.extend([f"{_ts(s.start, False)} --> {_ts(s.end, False)}", body, ""])
        (directory / f"{stem}.srt").write_text("\n".join(srt), encoding="utf-8")
        (directory / f"{stem}.vtt").write_text("\n".join(vtt), encoding="utf-8")
