# Transcribe-Translate for Windows

A native Windows 11 application for local/cloud audio-video transcription, translation and bilingual summarisation.

## Current implementation
- Tkinter desktop GUI.
- Local media and YouTube URLs via yt-dlp.
- Local ASR via WhisperX; selectable Whisper model; optional speaker diarization.
- Cloud ASR via OpenAI audio transcription endpoint.
- Translation/summarisation via local Ollama or OpenAI.
- Original transcript JSON/TXT plus SRT/VTT when timestamps exist.
- Target-language translation plus bilingual summaries.
- No WSL or Docker.
- No API keys committed.

## Windows prerequisites
- Windows 11 64-bit.
- Python 3.10-3.13.
- FFmpeg on PATH.
- Internet for package/model downloads, YouTube retrieval, or selected cloud providers.

WhisperX documents Windows CUDA 12.8 for NVIDIA acceleration and CPU int8 operation. GPU availability is detected at runtime; the application does not claim CUDA when it is unavailable.

Upstream WhisperX: https://github.com/m-bain/whisperX

## Install
From the repository root:

    cd transcribe-translate
    setup.bat

The setup script creates .venv, installs requirements, and checks Python and FFmpeg. It does not install WSL or Docker.

## Configuration
Copy config.example.json to config.json.
Copy .env.example to .env and set credentials only for providers you use:

    OPENAI_API_KEY=...
    HF_TOKEN=...

config.json and .env are Git-ignored.

Defaults are local WhisperX ASR, automatic source-language detection, English target translation, and local Ollama text processing.

## Launch
Double-click run.bat, or run:

    powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1

The GUI supports local file/YouTube URL, source language, local/OpenAI ASR, Whisper model, diarization, Ollama/OpenAI text provider, target language, and output directory.

## Local ASR
Available UI models: tiny, base, small, medium, large-v2, large-v3.
For high-quality Catalan meeting transcription, large-v3 is the quality-first local choice. Smaller models reduce compute and memory requirements.
Model files are cached by WhisperX/Hugging Face. Exact memory use depends on model, batch size and backend.

## Diarization
WhisperX documents a Hugging Face read token and access to its pyannote diarization model. Set HF_TOKEN in .env. Output labels are SPEAKER_00 etc.; names are not inferred.

## Cloud ASR
Audio is sent only when OpenAI ASR is explicitly selected:

    https://api.openai.com/v1/audio/transcriptions

The current OpenAI model catalogue lists GPT-4o Transcribe, GPT-4o Mini Transcribe and newer GPT-Transcribe models. This implementation currently uses gpt-4o-transcribe in core/asr.py so that the provider choice is isolated from the GUI.

Cloud ASR is never a silent fallback.

## Translation and summarisation
Ollama default endpoint: http://127.0.0.1:11434
Ollama example model: qwen3:1.7b
OpenAI example text model: gpt-5.6-luna.

## Outputs
Each job is written below output with a timestamped job directory.
- original.txt: original transcript
- original.json: structured transcript and timestamps
- original.srt / original.vtt: timestamped subtitles when available
- en.txt (or selected target code).txt: translation
- summary.md: target-language summary
- bilingual-summary.md: original-language summary followed by target-language summary
- job.json: source/provider/model metadata

## Privacy
Local WhisperX keeps media on the Windows machine. Local Ollama keeps text on the local Ollama server. Selecting OpenAI ASR uploads audio to OpenAI. Selecting OpenAI text processing uploads transcript text. There is no silent cloud fallback.

## Architecture
GUI -> media -> pipeline -> ASR provider -> transcript -> text provider -> outputs.
ASR and text providers are isolated from the GUI so additional providers can be added without rewriting the application.

## Testing status
Verified from repository contents: project structure, project-relative launcher/setup/update paths, configuration consistency, provider separation, and absence of hardcoded API keys.
Not verified in this ChatGPT execution environment: full WhisperX inference, Windows dependency installation, CUDA acceleration, diarization, real OpenAI/Ollama calls, and real YouTube download. Those require execution on Windows and are not claimed as successful tests.

## References
- WhisperX: https://github.com/m-bain/whisperX
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- OpenAI models: https://platform.openai.com/docs/models