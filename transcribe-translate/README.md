# SS Transcribe-Translate

Windows-native transcription utility.

## No WhisperX / no Torch / no pip

The obsolete Python/WhisperX implementation has been removed. This project does not install or require a Python virtual environment, WhisperX, Torch, pip packages, or Hugging Face diarization.

The runtime is:
- PowerShell (built into Windows)
- FFmpeg executable for audio extraction
- standalone yt-dlp.exe for YouTube input
- OpenAI Audio Transcriptions API for speech-to-text
- Ollama may be used later for local translation/summarisation

OpenAI currently documents `gpt-4o-transcribe-diarize` for speaker-labelled transcription and `chunking_strategy=auto` for inputs longer than 30 seconds. citeturn0search1

## Start

Run `run.bat` from this folder. It accepts a local media path or a YouTube URL.

Set `OPENAI_API_KEY` in `.env` or in the Windows environment.

## Required external executables

- FFmpeg must be installed and on PATH.
- For YouTube URLs only, `tools\\yt-dlp.exe` is used as a standalone executable. It is **not** a Python package and does not require Python.

Windows Python itself is not touched by this project.

## Current status

The old dependency stack is removed from GitHub. The native launcher now performs media preparation and OpenAI transcription. Translation, meeting analysis, voting/evidence extraction and polished output generation are the next application layer; they are not falsely represented as already complete.
