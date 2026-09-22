# SS Transcribe-Translate

Windows-native, local-first transcription and analysis utility.

## Core design — source first

The **original-language transcript is the primary product**.

The pipeline is:

1. Local media file or YouTube URL
2. FFmpeg extracts 16 kHz mono audio
3. **faster-whisper + CTranslate2** performs local speech-to-text
4. The **source-language summary is generated directly from the source-language transcript**
5. The **English summary is only a translation of that source-language summary**
6. Full transcript translation is an **optional extra**, into any language selected by the user
7. Ollama provides the local text/translation model; the GUI discovers all models currently installed on the user's Ollama instance

There is deliberately **no paid OpenAI API call in this application**. The SS project may use OpenAI separately for coding, orchestration, knowledge-management or other approved SS-brain work; that does not make this Transcribe-Translate runtime dependent on paid OpenAI transcription.

## Local runtime

- Windows
- Python + faster-whisper
- CTranslate2
- FFmpeg executable for audio extraction
- standalone yt-dlp.exe for YouTube input
- Ollama for summaries and optional translation

**WhisperX and Torch are not required by this application.**

## Ollama model selection

The GUI queries Ollama's local /api/tags endpoint and exposes every installed model instead of hard-coding one model.

The current PC has been using these local models:

- llama3.2:1b — fast/lightweight
- gemma3:1b — fast/lightweight
- qwen3:1.7b — balanced multilingual/speed option
- phi4-mini:3.8b — slower, but the strongest of these known choices for careful text work

The application displays a recommendation, but the user retains the choice. The recommendation is a speed/precision trade-off, not a hidden model switch.

## Primary outputs

Every completed job writes:

- original.txt — complete source-language transcript
- original.json — structured transcript + segment timestamps
- original.srt — timestamped source transcript
- original.vtt — timestamped source transcript
- source_summary.md — comprehensive summary in the source language
- english_summary.md — English translation of the source-language summary
- job.json — processing metadata and explicit zero-API declaration
- output_manifest.json — files produced

When optional full transcript translation is enabled:

- translation.txt — complete translation into the selected target language

## Important separation

The full source transcript is **not** translated merely to make the source summary.

The source summary is produced first from the original-language transcript.

The English summary is then translated from that source summary.

A full transcript translation is an independent optional operation.

## YouTube and FFmpeg

The application does not install, replace or modify the user's existing FFmpeg or standalone yt-dlp.exe.

For YouTube input, set paths.ytdlp_path in config.json if the existing standalone executable is not on PATH.

## Start

Run run.bat.

The GUI discovers the installed Ollama models and lets the user choose the text model.

## Verification status

Repository-level verification confirms the source-first architecture and absence of an OpenAI API call in the application code.

A real Windows end-to-end run still has to be executed on the user's machine with an actual recording. That is the only honest way to prove transcription accuracy, Ollama availability, model speed and the final output files on this particular PC.
