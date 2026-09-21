from __future__ import annotations
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}
AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus", ".aac"}

def is_url(value: str) -> bool:
    try:
        return urlparse(value).scheme in {"http", "https"} and bool(urlparse(value).netloc)
    except Exception:
        return False

def find_executable(name: str) -> str | None:
    return shutil.which(name)

def run_command(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)

def ensure_ffmpeg() -> str:
    exe = find_executable("ffmpeg")
    if not exe:
        raise RuntimeError("FFmpeg was not found on PATH.")
    return exe

def download_youtube(url: str, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    template = str(destination / "%(title).180s.%(ext)s")
    commands = [
        [sys.executable, "-m", "yt_dlp", "--no-playlist", "-f", "bestvideo*+bestaudio/best", "--merge-output-format", "mp4", "-o", template, url],
        ["yt-dlp", "--no-playlist", "-f", "bestvideo*+bestaudio/best", "--merge-output-format", "mp4", "-o", template, url],
    ]
    last_error = ""
    for command in commands:
        result = run_command(command)
        if result.returncode == 0:
            files = sorted(destination.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            candidates = [p for p in files if p.is_file() and p.suffix.lower() in VIDEO_EXTS | AUDIO_EXTS]
            if candidates:
                return candidates[0]
        last_error = (result.stderr or result.stdout)[-4000:]
    raise RuntimeError(f"YouTube download failed. Last output:\n{last_error}")

def extract_audio(source: Path, destination: Path) -> Path:
    ffmpeg = ensure_ffmpeg()
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = run_command([ffmpeg, "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(destination)])
    if result.returncode != 0 or not destination.exists():
        raise RuntimeError(f"FFmpeg audio extraction failed:\n{result.stderr[-4000:]}")
    return destination

def chunk_audio(source: Path, directory: Path, seconds: int = 600) -> list[Path]:
    ffmpeg = ensure_ffmpeg()
    directory.mkdir(parents=True, exist_ok=True)
    pattern = directory / "chunk_%04d.mp3"
    result = run_command([
        ffmpeg, "-y", "-i", str(source), "-f", "segment", "-segment_time", str(seconds),
        "-reset_timestamps", "1", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "64k",
        str(pattern)
    ])
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg chunking failed:\n{result.stderr[-4000:]}")
    return sorted(directory.glob("chunk_*.mp3"))
