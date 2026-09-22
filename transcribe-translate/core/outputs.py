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
        s += 1
        ms = 0
    sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"

def write_outputs(
    transcript: Transcript,
    translation: str,
    source_summary: str,
    english_summary: str,
    analysis: str,
    directory: Path,
    source: str,
    translated: bool = False,
    target_language: str = "",
    analysis_created: bool = False,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)

    (directory / "original.txt").write_text(transcript.text + "\n", encoding="utf-8")
    (directory / "source_summary.md").write_text(
        f"# Source-language summary ({transcript.language or 'detected language'})\n\n{source_summary}\n",
        encoding="utf-8",
    )
    (directory / "english_summary.md").write_text(
        "# English summary (translation of source-language summary)\n\n"
        f"{english_summary}\n",
        encoding="utf-8",
    )

    if analysis_created:
        (directory / "analysis.md").write_text(
            "# Source-grounded meeting / evidence analysis\n\n"
            f"{analysis}\n",
            encoding="utf-8",
        )

    if translated:
        (directory / "translation.txt").write_text(
            translation + "\n", encoding="utf-8"
        )

    payload = {
        "source": source,
        "language": transcript.language,
        "backend": transcript.backend,
        "model": transcript.model,
        "segments": [asdict(s) for s in transcript.segments],
    }
    (directory / "original.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if any(s.end > s.start for s in transcript.segments):
        srt: list[str] = []
        vtt: list[str] = ["WEBVTT", ""]
        for i, segment in enumerate(transcript.segments, 1):
            body = segment.text
            srt.extend([str(i), f"{_ts(segment.start)} --> {_ts(segment.end)}", body, ""])
            vtt.extend([f"{_ts(segment.start, False)} --> {_ts(segment.end, False)}", body, ""])
        (directory / "original.srt").write_text("\n".join(srt), encoding="utf-8")
        (directory / "original.vtt").write_text("\n".join(vtt), encoding="utf-8")

    manifest = {
        "translation_created": translated,
        "translation_target": target_language if translated else None,
        "analysis_created": analysis_created,
        "primary_outputs": [
            "original.txt", "original.json", "original.srt", "original.vtt",
            "source_summary.md", "english_summary.md"
        ],
        "analysis_outputs": ["analysis.md"] if analysis_created else [],
    }
    (directory / "output_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
