---
name: audio-web-app-engineer
description: >-
  Specialized skill for engineering audio studio web applications, speech synthesis,
  voice cloning workflows, Web Audio API, and audio DSP processing.
  Activate when working on audio pipelines, waveform cutters, denoisers, or TTS engines.
---

# Audio Web App Engineer Standard

Provides comprehensive workflows for building production-grade audio applications in the browser and backend.

## 1. Web Audio API Best Practices
- Auto-Unlock AudioContext: Mobile browsers (Safari/Chrome) mute AudioContext until a user gesture occurs. Always resume AudioContext on first touch/click.
- Sample Rate Consistency: Always resample and normalize to consistent studio sample rates (22050Hz, 24000Hz, or 44100Hz).
- Peak Normalization: Always normalize generated waveforms to -1.0 dBFS to prevent clipping distortion.

## 2. Studio Waveform Cutter & Denoiser Mechanics
- Sub-pixel Canvas Waveform: Render high-DPI waveform peaks with zero aliasing.
- Interactive Trim Range: Ensure dragging start/end handles has a minimum 0.2s duration guard.
- Direct Export: Support instant WAV download and direct transfer to reference audio storage.
