# Transcribe-Translate for Windows

A Windows 11 desktop application for audio/video transcription, translation and bilingual summarisation.

## First-time installation

Open **Command Prompt (cmd.exe)**, not PowerShell, and run:

    cd OpenAI\transcribe-translate
    setup.bat

If your repository is somewhere else, cd to that actual directory first.

The setup script creates the virtual environment, installs Python dependencies, creates config.json and .env from their example files, and checks FFmpeg.

If FFmpeg is missing, setup tells you how to install it with Windows Package Manager:

    winget install --id Gyan.FFmpeg.Shared -e

After installing FFmpeg, close the terminal, open a new Command Prompt, and run setup.bat again.

## Start

From the same transcribe-translate directory:

    run.bat

Do not run python app.py from an arbitrary directory; use the supplied launcher.

## Configuration

setup.bat automatically creates config.json and .env.

Edit .env only if you use a cloud provider or Hugging Face diarization:

    OPENAI_API_KEY=...
    HF_TOKEN=...

These local files are Git-ignored.

## Current functionality

- local audio/video input;
- YouTube URL input through yt-dlp;
- local WhisperX transcription;
- automatic or selected source language;
- Whisper model selection including large-v3;
- optional speaker diarization;
- OpenAI cloud ASR as an explicit alternative;
- local Ollama translation/summarisation;
- OpenAI translation/summarisation;
- original transcript TXT/JSON;
- timestamped SRT/VTT where available;
- target-language translation;
- bilingual summary;
- job metadata;
- local-first processing with no silent cloud fallback.

## Local ASR

WhisperX is the local ASR engine. large-v3 is the quality-first choice for the Catalan meeting use case; smaller models reduce resource requirements.

WhisperX documents CUDA 12.8 for NVIDIA acceleration on Windows and CPU int8 operation. Exact performance depends on your hardware and installed PyTorch/CUDA stack.

Upstream WhisperX:
https://github.com/m-bain/whisperX

## Diarization

WhisperX speaker diarization requires the documented Hugging Face authentication/access arrangement. Set HF_TOKEN in .env after obtaining the appropriate Hugging Face access.

Diarization generates labels such as SPEAKER_00; it does not automatically know participants' names.

## Cloud providers

OpenAI ASR is explicit and uses:

    https://api.openai.com/v1/audio/transcriptions

The application does not silently upload local media.

Ollama defaults to:

    http://127.0.0.1:11434

The example Ollama model is qwen3:1.7b; change it in config.json if another local model is installed.

## Outputs

Jobs are placed under:

    output\<timestamp>_<source>\

Expected files include:

    original.txt
    original.json
    original.srt
    original.vtt
    en.txt
    summary.md
    bilingual-summary.md
    job.json

## Update

From the project directory:

    update.bat

This performs git pull --ff-only and refreshes Python dependencies.

## Diagnostics

From the project directory:

    powershell -ExecutionPolicy Bypass -File .\scripts\diagnose.ps1

This reports Python, FFmpeg, the virtual environment, WhisperX/Torch import status and CUDA availability without exposing secret values.

## Testing status

Verified from the GitHub repository:
- project structure and referenced files;
- Windows launcher paths;
- virtual-environment paths;
- configuration names;
- provider separation;
- Git-ignored local secrets/output;
- setup handling of missing FFmpeg.

Not yet verified on the Windows machine:
- dependency installation;
- WhisperX inference;
- GPU/CUDA acceleration;
- diarization;
- Ollama;
- OpenAI;
- YouTube retrieval.

These are not represented as successful until actually run.
