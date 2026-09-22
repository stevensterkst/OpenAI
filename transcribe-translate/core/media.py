from __future__ import annotations
from pathlib import Path
import os
import shutil
import subprocess
from urllib.parse import urlparse

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".mp3", ".m4a", ".wav", ".flac", ".ogg"}

def is_url(source: str) -> bool:
    try:
        return urlparse(source).scheme in {"http", "https"}
    except Exception:
        return False

def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise RuntimeError("FFmpeg was not found on PATH. Your existing FFmpeg installation must be on PATH.")

def find_ytdlp(configured: str = "") -> str:
    candidates = []
    if configured:
        candidates.append(Path(os.path.expandvars(os.path.expanduser(configured))))
    candidates.append(Path(__file__).resolve().parents[1] / "tools" / "yt-dlp.exe")
    path = shutil.which("yt-dlp")
    if path:
        candidates.append(Path(path))
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError(
        "yt-dlp.exe was not found. For YouTube input, set paths.ytdlp_path in config.json "
        "to your existing standalone yt-dlp.exe. It is not installed or changed by this app."
    )

def prepare_media(source: str, work: Path, ytdlp_path: str = "") -> Path:
    work.mkdir(parents=True, exist_ok=True)
    if is_url(source):
        ytdlp = find_ytdlp(ytdlp_path)
        output = work / "%(title).180s.%(ext)s"
        subprocess.run(
            [ytdlp, "--no-playlist", "-f", "bestvideo*+bestaudio/best",
             "--merge-output-format", "mp4", "-o", str(output), source],
            check=True,
        )
        media = next((p for p in sorted(work.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
                      if p.is_file() and p.suffix.lower() in VIDEO_EXTS), None)
        if not media:
            raise RuntimeError("yt-dlp completed but no supported media file was produced.")
        return media

    media = Path(source).expanduser().resolve()
    if not media.is_file():
        raise FileNotFoundError(media)
    destination = work / media.name
    shutil.copy2(media, destination)
    return destination

def extract_audio(media: Path, destination: Path) -> Path:
    ffmpeg = find_ffmpeg()
    subprocess.run(
        [ffmpeg, "-y", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(destination)],
        check=True,
    )
    return destination
