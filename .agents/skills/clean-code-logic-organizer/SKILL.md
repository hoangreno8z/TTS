---
name: clean-code-logic-organizer
description: >-
  Codebase architecture, systematic organization, and clean code standards.
  Activate when creating files, refactoring directories, designing data structures,
  writing API endpoints, or separating concerns.
---

# Clean Code Logic Organizer Standard

Structures the codebase into a predictable, maintainable, and clean modular hierarchy.

## 1. Directory Structure Rules
```text
├── backend/
│   └── app/
│       ├── audio/          # Core DSP, Neural Engines (RVC, VITS, ONNX, World)
│       ├── routers/        # Fast, clean API routes
│       ├── services/       # Business logic (Synthesizer, VoiceManager, Denoise)
│       └── models/         # Pydantic schemas & state models
├── frontend/
│   ├── index.html          # Clean semantic DOM
│   ├── css/                # Token-based styles (tokens, layout, components)
│   ├── js/
│   │   ├── api/            # Network client & endpoint bindings
│   │   ├── audio/          # WebAudio player, recorder, waveform canvas
│   │   ├── ui/             # Modals, drawers, toast notifications
│   │   └── app.js          # Master controller & state orchestration
```

## 2. Code Quality Rules
- Single Responsibility Principle (SRP): Each function should do ONE thing cleanly in under 50 lines.
- Deterministic Naming: Functions start with action verbs (`handlePlayAudio`, `initWaveformCanvas`, `fetchVoiceStyles`).
- Explicit Error Handling: Never use empty `catch {}` blocks. Always return structured JSON responses with explicit error codes.
