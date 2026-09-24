# AGENTS.md - Project Specification & AI Coordination Hand-off
<!-- SOURCE OF TRUTH: GitHub Repository -->
<!-- Last Updated: 2026-09-23 -->

## 1. Project Identity & Architecture
*   **Project Name:** [Project Name]
*   **Core Objective:** [1-2 sentences on what this codebase does]
*   **Tech Stack:** [e.g., Next.js 15, TypeScript, Python FastAPI, PostgreSQL]
*   **Key Directories:**
    *   `/src/components`: UI Layer
    *   `/src/api`: Backend logic

## 2. Shared Development Workflow (The Multi-AI Rule)
This project utilizes a dual-engine AI strategy (OpenAI & DeepSeek). To maintain sync:
1. **GitHub is the absolute Source of Truth.** Never trust a previous chat window's assumption over the actual state of the code on GitHub.
2. Before writing code, you must read the latest commit changes or request a file export.
3. **OpenAI Focus:** Architectural design, system prompt engineering, feature planning, and structured layouts.
4. **DeepSeek Focus:** Math, performance optimization, heavy logical debugging, and deep algorithmic thinking.

## 3. Current Sprint & State of Play
*   **Active Branch:** `main` (or `dev-feature-x`)
*   **Last Successfully Merged Feature:** [e.g., Implemented Auth0 integration]
*   **Current Bottleneck / Active Task:** [e.g., DB queries are throwing connection pool timeouts]
*   **Immediate Next Action Item:** [e.g., Optimize the prisma-client connection pooling config]

## 4. Code Style & Technical Constraints
*   **Formatting:** [e.g., Prettier defaults, strict TypeScript, no `any`]
*   **Testing Protocol:** Run `npm run test` before declaring code "complete". All business logic must have unit tests.
*   **Explicit Boundaries:** Do not alter configuration files (`package.json`, `.env.example`) without explicit permission.

## SS TRANSCRIBE-TRANSLATE PROJECT OVERRIDES
- This repository is the source of truth for the Windows-native SS Transcribe-Translate application.
- The application is Python/Tkinter + faster-whisper + FFmpeg + yt-dlp + Ollama, packaged with PyInstaller.
- Before any code change, inspect the current `main` branch and preserve existing working features.
- OpenAI and DeepSeek are cooperating engineering agents; neither may treat the other agent's claims as verified until the relevant GitHub code/tests prove them.
- Every substantive feature must have a deterministic test or audit assertion where practical.
- Never silently install, update, remove, or replace unrelated software on the user's Windows PC.
- Do not claim the application is final until the source audit, Windows build audit, and an end-to-end real-media test pass.
- Record important architecture/feature changes in this file so the next agent can resume from GitHub without relying on chat history.

## CURRENT SS TRANSCRIBE-TRANSLATE STATE
- Caption parsing supports VTT, SRV3, TTML and JSON3 with regression tests.
- Acquisition is caption-first, then yt-dlp/local-media + faster-whisper fallback.
- AUTO caption selection no longer gives an unexplained preference to English; manual tracks are preferred when otherwise equivalent.
- The primary transcript is persisted immediately after acquisition/ASR and before any Ollama stage. Downstream AI failure cannot erase it.
- Local ASR uses faster-whisper BatchedInferencePipeline in bounded 180-second windows, with VAD first and a no-VAD retry when a window is empty or suspiciously under-covered.
- Local ASR now reports an explicit window coverage plan/completion and rejects invalid final timestamps.
- The selected range remains full / first N minutes / first N percent and is applied to remote captions or FFmpeg extraction.
- Browser transcript bridge and browser tab-audio capture remain explicitly unfinished; do not claim them as implemented until committed and verified.
- English summary generation is downstream of the source-language summary and has an English-language acceptance check/retry.
- The current definition of final verification remains: verify-final.ps1 + Windows EXE build + verify-local.ps1 with an explicit real media file. CI uses the source/build gate.
- IMPORTANT OPEN TEST: a real user-reported local .m4a previously produced only a ~12-second transcript segment. The repository cannot determine whether the source file itself was only ~29 seconds or whether ASR lost audio without running against that exact Windows file. Do not claim this case is solved until the exact file is re-tested and its FFmpeg duration is compared with ASR coverage/output.


## 2026-09-24 REAL TEST UPDATE
- User real test produced a 4m12s French transcript and therefore the earlier suspected short-ASR truncation is NOT reproduced in this test.
- The real failure was downstream summary quality: Ollama llama3.2:1b generated repetitive generic/template content unrelated to several sections of the transcript. Evidence is recorded in DEEPSEEK_REVIEW_2026-09-24.md.
- Output-path failure was also reproduced at the GUI level: the running EXE still showed the legacy project-local output path. Source code now migrates any project-local transcribe-translate/output path to Downloads/Transcribe-Translate, but the EXE must be rebuilt for the fix to reach the user's installation.
- Source-summary quality gate and local stronger-model fallback were added. Preferred local models are qwen3:1.7b then phi4-mini:3.8b when no explicit model is configured.
- Added summary regression tests, local-config/media .gitignore hardening, requirements forbidden-dependency audit, Windows ZIP/audit artifact packaging, and GUI overlapping-job protection.
- These source changes are NOT declared final until the rebuilt Windows EXE is run against the supplied real test and the complete final audit passes.
