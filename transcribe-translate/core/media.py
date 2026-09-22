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
    for root in [os.environ.get("ProgramFiles", r"C:\Program Files")]:
        for candidate in Path(root).glob("FFmpeg*/bin/ffmpeg.exe"):
            if candidate.is_file():
                return str(candidate)
    raise RuntimeError(
        "FFmpeg was not found on PATH or under C:\\Program Files\\FFmpeg*\\bin. "
        "The application does not install or replace FFmpeg."
    )

def find_ytdlp(configured: str = "") -> str:
    candidates = []

    def add(value: str | Path):
        if not value:
            return
        p = Path(os.path.expandvars(os.path.expanduser(str(value))))
        if p not in candidates:
            candidates.append(p)

    add(configured)
    add(os.environ.get("YTDLP_PATH", ""))
    add(Path(__file__).resolve().parents[1] / "tools" / "yt-dlp.exe")

    found = shutil.which("yt-dlp.exe") or shutil.which("yt-dlp")
    if found:
        add(found)

    # Common locations for a manually downloaded standalone Windows yt-dlp.exe.
    home = Path.home()
    local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    roaming = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    common = [
        home / "Downloads" / "yt-dlp.exe",
        home / "Desktop" / "yt-dlp.exe",
        home / "Documents" / "yt-dlp.exe",
        local / "yt-dlp.exe",
        local / "Programs" / "yt-dlp" / "yt-dlp.exe",
        local / "Programs" / "yt-dlp.exe",
        roaming / "yt-dlp" / "yt-dlp.exe",
    ]
    for p in common:
        add(p)

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())

    raise FileNotFoundError(
        "yt-dlp.exe was not found automatically. Select your existing standalone "
        "yt-dlp.exe with the Browse button in the YouTube input section. "
        "This application will not install, replace, update, or modify yt-dlp."
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
        [ffmpeg, "-y", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", str(destination)],
        check=True,
    )
    if not destination.is_file() or destination.stat().st_size <= 44:
        raise RuntimeError("FFmpeg produced no usable audio track.")
    return destination
