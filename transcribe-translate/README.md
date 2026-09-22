# SS Transcribe-Translate

Windows-native, local-first transcription, summarisation, translation and source-grounded analysis.

## Product order — this is intentional

The **source-language transcript is the primary product**.

The **source-language summary is also a primary/basic feature** and is generated directly from that original-language transcript.

The **English summary is NOT an independent summary**. It is only a translation of the source-language summary.

A **full transcript translation is optional**, independent of the summaries, and can target any language supported by the selected Ollama model.

The source-grounded meeting/evidence analysis is an additional layer downstream of the original transcript. It must never replace or rewrite the primary source transcript.

## Pipeline

1. Local media file or YouTube URL
2. Existing FFmpeg extracts 16 kHz mono audio
3. faster-whisper + CTranslate2 performs local speech-to-text
4. Original-language transcript is saved with segment timestamps
5. Source-language summary is generated directly from the source transcript
6. English summary is translated from the source-language summary
7. Source-grounded analysis optionally extracts topics/timeline, people mentioned, proposals, decisions, votes, questions/objections, action items, evidence, procedural/governance flags, contradictions and knowledge-management tags
8. Full transcript translation is optionally performed into the user's target language

## Local/free boundary

The application runtime makes **no OpenAI API calls and requires no paid API token**.

OpenAI remains part of the wider SS development/knowledge-management ecosystem and may be used outside this application for coding, SDK work, orchestration or SS-brain functions. That is deliberately separate from this application's runtime.

The app's transcription is local via faster-whisper/CTranslate2. Text summarisation, analysis and optional translation are local via Ollama.

## Ollama model selection

The GUI calls Ollama's local `/api/tags` endpoint and exposes **every model currently installed**, rather than hard-coding Qwen or another model.

The currently known PC models are:

- `llama3.2:1b` — fast/lightweight
- `gemma3:1b` — fast/lightweight
- `qwen3:1.7b` — balanced multilingual/speed option
- `phi4-mini:3.8b` — stronger starting choice for careful translation/analysis, with slower CPU generation

The GUI gives a recommendation but never silently changes the user's selection. The recommendation is a heuristic, not a benchmark claim.

## Outputs

Primary outputs:

- `original.txt` — complete source-language transcript
- `original.json` — transcript + segment timestamps
- `original.srt` — timestamped source transcript
- `original.vtt` — timestamped source transcript
- `source_summary.md` — source-language summary
- `english_summary.md` — English translation of the source summary

Additional output when analysis is enabled:

- `analysis.md` — source-grounded analysis including timeline, topics, decisions, proposals, votes, action items, evidence matrix, procedural/governance review points, contradictions and knowledge-management tags

Additional output when full translation is enabled:

- `translation.txt` — complete source transcript translated to the selected target language

Metadata:

- `job.json` — model, language, provenance and zero-paid-API assertion
- `output_manifest.json` — produced outputs

## Evidence rules

The analysis layer is deliberately conservative:

- It uses only the original-language transcript.
- It does not claim speaker diarization unless the transcript itself supports speaker identification.
- It does not invent votes, motives, legal conclusions, dates, amounts or decisions.
- It distinguishes explicit transcript facts from analytical flags and reports insufficient evidence when necessary.

## Existing FFmpeg / standalone yt-dlp

The application does not install, replace or modify the user's existing FFmpeg or standalone yt-dlp.

For YouTube input, configure `paths.ytdlp_path` if the existing standalone executable is not on PATH.

## Obsolete Whisper/Torch cleanup

The application itself requires neither WhisperX nor Torch.

Do **not** run the cleanup blindly: first run the read-only audit supplied in the working instructions and verify package ownership and disk usage. The cleanup script is intentionally restricted to obsolete `openai-whisper` and `torch`; it does not touch Python, FFmpeg, standalone yt-dlp, Hugging Face cache, or SS project files.

## Verification

Repository inspection verifies the architecture and source-first data flow.

Verification status after the 2026-09-22 audit:
- Architecture/source-code checks: implemented.
- Ollama local endpoint and all four installed models: verified on this PC.
- faster-whisper + CTranslate2 imports: verified on this PC.
- Existing FFmpeg executable: verified on this PC.
- A real end-to-end run was attempted, but the automatically selected 4.54-second browser-extension cache MP4 produced zero transcript segments; the old verifier incorrectly continued into Ollama stages and only failed when it found an empty SRT.
- The verifier is now strict: it requires an explicit user-selected recording, treats zero ASR segments as a hard failure, and checks transcript text/segments before declaring success.
- The ASR now retries once with VAD disabled when the normal VAD pass produces zero segments.
- The application's FFmpeg discovery now also searches the existing C:\Program Files\FFmpeg* installation when FFmpeg is not on PATH.
- Obsolete Whisper/Torch cleanup is no longer automatic in finish-local.ps1.
- Speaker diarization remains optional and is NOT claimed as verified: sherpa-onnx and compatible local ONNX speaker models were not present in the audited PC state.

No code inspection can honestly substitute for the final real run on a genuine recording containing speech.
