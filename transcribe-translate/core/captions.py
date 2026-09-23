from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

import requests


def _clean_caption_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _parse_vtt(text: str) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    blocks = re.split(r"\n\s*\n", text.replace("\r", ""))
    for block in blocks:
        lines = [x.strip("\ufeff") for x in block.split("\n") if x.strip()]
        timing = next((x for x in lines if "-->" in x), None)
        if not timing:
            continue
        left, right = [x.strip().split()[0] for x in timing.split("-->", 1)]
        def ts(x: str) -> float:
            p = x.replace(",", ".").split(":")
            if len(p) == 3:
                return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
            return int(p[0]) * 60 + float(p[1])
        body = " ".join(_clean_caption_text(x) for x in lines[lines.index(timing)+1:])
        body = re.sub(r"\s+", " ", body).strip()
        if body:
            cues.append({"start": ts(left), "end": ts(right), "text": body})
    return cues


def _choose_track(info: dict, requested_language: str) -> tuple[str, dict] | None:
    requested = (requested_language or "auto").lower().strip()
    tracks: list[tuple[str, dict, int]] = []
    for source_name, mapping in (
        ("manual", info.get("subtitles") or {}),
        ("automatic", info.get("automatic_captions") or {}),
    ):
        for lang, entries in mapping.items():
            if not entries:
                continue
            score = 0
            ll = lang.lower()
            if requested != "auto":
                if ll == requested:
                    score += 100
                elif ll.startswith(requested + "-") or ll.startswith(requested):
                    score += 80
            if source_name == "manual":
                score += 20
            if ll.startswith("en"):
                score += 5
            for entry in entries:
                if entry.get("url") and entry.get("ext") in ("vtt", "srv3", "ttml", "json3"):
                    tracks.append((lang, entry, score))
    if not tracks:
        return None
    tracks.sort(key=lambda x: x[2], reverse=True)
    return tracks[0][0], tracks[0][1]


def scrape_transcript(source: str, requested_language: str = "auto", progress=print):
    """Return a Transcript-like object from remote captions without downloading media.

    This is deliberately a first-stage optimisation. It is not a claim that every
    URL has captions: when no usable subtitle track exists, the caller must fall
    back to actual audio transcription.
    """
    if not source.lower().startswith(("http://", "https://")):
        return None
    try:
        import yt_dlp
        from .asr import Segment, Transcript
        progress("Caption-first probe: checking remote transcript/caption tracks before downloading media...")
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "extract_flat": False,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(source, download=False)
        chosen = _choose_track(info, requested_language)
        if not chosen:
            progress("No usable remote caption track found; falling back to local audio transcription.")
            return None
        lang, track = chosen
        response = requests.get(track["url"], timeout=60)
        response.raise_for_status()
        cues = _parse_vtt(response.text)
        if not cues:
            progress("Caption track was found but contained no usable cues; falling back to audio transcription.")
            return None
        segments = [Segment(float(c["start"]), float(c["end"]), c["text"]) for c in cues]
        # Deduplicate repeated rolling captions common in WebVTT/ASR tracks.
        dedup = []
        last = None
        for seg in segments:
            if seg.text != last:
                dedup.append(seg)
                last = seg.text
        text = "\n".join(s.text for s in dedup)
        progress(f"REMOTE TRANSCRIPT USED: {lang} captions; media download and Whisper were skipped.")
        return Transcript(
            text=text,
            segments=dedup,
            language=lang,
            backend="remote-captions",
            model=track.get("ext", "caption"),
        )
    except Exception as exc:
        progress(f"Caption-first probe unavailable ({exc}); falling back to local audio transcription.")
        return None
