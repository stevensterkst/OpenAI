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