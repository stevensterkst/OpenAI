# Transcribe-Translate for Windows

A native Windows 11 desktop application for **video/audio transcription, translation and bilingual summarisation**. It accepts local media and YouTube URLs, keeps processing local by default, and exposes cloud providers explicitly rather than silently uploading media.

## Current implementation

- GUI: Python/Tkinter.
- Media: local audio/video files or YouTube URLs.
- YouTube download: yt-dlp, invoked through Python module or executable.
- Local ASR: WhisperX, with selectable Whisper model and optional speaker diarization.
- Cloud ASR: OpenAI Audio Transcriptions API, including `gpt-4o-transcribe`, `gpt-4o-mini-transcribe` and `gpt-4o-transcribe-diarize`.
- Translation/summarisation: modular OpenAI or local Ollama text provider.
- Output: original transcript TXT/JSON, SRT/VTT when timestamps are available, English translation TXT, bilingual summary TXT/MD, and a job metadata JSON.
- No API keys are committed.
- No WSL or Docker is required.

## Windows 11 prerequisites

- Windows 11 64-bit.
- Python 3.10–3.13. WhisperX currently documents Python 3.10–3.13.
- FFmpeg on PATH.
- Internet only for first-time package/model downloads, YouTube downloads, or explicitly selected cloud providers.
- For local WhisperX: sufficient RAM/CPU; an NVIDIA CUDA GPU is strongly preferable. AMD integrated graphics are not treated as CUDA devices.
- For speaker diarization: a Hugging Face account/token and access to the diarization model(s) used by the installed WhisperX version.

WhisperX installation and diarization requirements are documented upstream:
https://github.com/m-bain/whisperX

yt-dlp Windows installation:
https://github.com/yt-dlp/yt-dlp/wiki/Installation

## Installation

From the repository root:

    cd transcribe-translate
    setup.bat

The setup script creates `.venv`, installs the application dependencies and checks FFmpeg/Python. It does not install WSL or Docker.

For NVIDIA CUDA, the setup script deliberately does not guess a CUDA/PyTorch wheel: run the PyTorch command appropriate to the installed NVIDIA driver from the official PyTorch selector, then rerun setup if necessary.

## Configuration

Copy:

    config.example.json

to:

    config.json

API keys should normally be supplied through Windows environment variables:

    OPENAI_API_KEY
    HF_TOKEN

The application also accepts these values from `.env` if present. `.env` is ignored by Git.

Important defaults:

- local ASR is the default;
- source language is auto-detected unless selected;
- translation target defaults to English;
- local Ollama is the default text provider when available;
- OpenAI is available as an explicit alternative;
- local media stays local unless a cloud provider is selected.

## Launch

Double-click:

    run.bat

or run:

    powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1

The GUI lets you choose:

1. local file or YouTube URL;
2. source language (Auto/Catalan/Spanish/English/etc.);
3. ASR backend (Local WhisperX/OpenAI);
4. Whisper model for local ASR;
5. diarization;
6. translation/summarisation provider;
7. target language;
8. output directory.

## Local ASR model choices

The WhisperX backend uses these model names:

- `tiny`
- `base`
- `small`
- `medium`
- `large-v2`
- `large-v3`
- `large-v3-turbo`

For high-quality Catalan meeting transcription, `large-v3` is the quality-first choice; `large-v3-turbo` is a practical faster alternative where supported. The application does not pretend that a CPU-only Windows machine has GPU acceleration.

Model files are downloaded/cached by Hugging Face/WhisperX on first use. Exact disk/RAM/VRAM requirements vary by backend, batch size and installed model version; the GUI reports provider errors rather than inventing capacity estimates.

## Cloud ASR

The OpenAI backend sends media chunks to:

    https://api.openai.com/v1/audio/transcriptions

Current documented models include `gpt-4o-transcribe`, `gpt-4o-mini-transcribe` and `gpt-4o-transcribe-diarize`.

Cloud ASR is explicit because it sends the audio to the provider. The application never falls back to cloud silently.

## Output

A job creates a timestamped directory such as:

    output\2026-09-21_204100_filename\

Typical files:

- `original.txt`
- `original.json`
- `original.srt` (when timestamps exist)
- `original.vtt` (when timestamps exist)
- `english.txt`
- `summary.md`
- `bilingual-summary.md`
- `job.json`

The original transcript is preserved separately from translations and summaries.

## Testing

Repository-level tests validate configuration, output formatting and provider-independent pipeline behaviour.

**Verified before release:** repository structure, Python syntax, internal imports used by the test suite, launcher path references and configuration consistency.

**Not yet verified here:** a complete WhisperX model inference on your Windows machine, because the ChatGPT execution environment does not have your Windows WhisperX installation/GPU. Cloud API calls are also not made during repository tests.

## Troubleshooting

### "FFmpeg not found"
Install FFmpeg and restart PowerShell so PATH is refreshed.

### WhisperX import/model error
Run:

    .venv\Scripts\python.exe -c "import whisperx; print('WhisperX OK')"

Then run:

    powershell -ExecutionPolicy Bypass -File .\scripts\diagnose.ps1

### Diarization authentication error
Set `HF_TOKEN` and accept the model access terms required by your installed WhisperX release.

### Local processing is too slow
Use `small`, `medium` or `large-v3-turbo`, or select OpenAI cloud ASR explicitly.

### YouTube download fails
Update yt-dlp and confirm the URL is publicly accessible. Some videos require authentication or are unavailable to yt-dlp.

## Privacy

The application is local-first. Choosing Local WhisperX means the media is processed on the machine. Choosing OpenAI ASR or OpenAI text processing necessarily sends the relevant content to OpenAI. Ollama processing stays on the local Ollama server.

## Architecture

The UI does not contain provider-specific transcription logic.

    GUI
      |
      +-- media.py
      |
      +-- pipeline.py
             |
             +-- ASR provider
             |     +-- WhisperX local
             |     +-- OpenAI cloud
             |
             +-- Text provider
                   +-- Ollama local
                   +-- OpenAI cloud
             |
             +-- outputs.py

Provider interfaces are deliberately small so additional ASR or translation providers can be added without rewriting the GUI.
