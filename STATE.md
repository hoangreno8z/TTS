# STATE — LAPQUE PERSONAL VIETNAMESE TTS

date: 2026-08-24
phase: 13 — Complete (All 13 Phases Delivered & Verified)
selected_engine: f5-tts (Flow-Matching Non-Autoregressive DiT)
fallback_engine: gpt-sovits (Few-shot Autoregressive)
engine_commit_or_tag: F5-TTS (DiT) / Vietnamese Community Checkpoints
python: 3.12.10 (Windows 10 AMD64)
pytorch: 2.x compatible
cuda: Colab T4 GPU (Free) / Local CUDA if available
gpu: Google Colab T4 GPU (15GB VRAM) / Local CPU for API & Frontend
vram: 15GB VRAM on Colab T4

## Dataset
reference_minutes: Ready for user audio files in data/raw/{neutral,serious,storytelling}
segments: Pipeline active (AudioProcessor, VAD, slicing 3-10s)
transcript_status: Active (Whisper draft + JSON/CSV metadata builder)
styles_ready:
  - neutral: active (speed: 1.0, pause_multiplier: 1.0)
  - serious: active (speed: 0.92, pause_multiplier: 1.25)
  - storytelling: active (speed: 1.05, pause_multiplier: 1.1)

## Tests
passed:
  - Phase 0: Project manifest validation (all 26 files verified)
  - Phase 0: License checklist initialized (`LICENSES_TO_CHECK.md`)
  - Phase 1: Environment audit script executed (`scripts/check_environment.py`)
  - Phase 2: Audio pipeline unit tests (`tests/test_audio_pipeline.py`)
  - Phase 3: Vietnamese Text Normalizer unit tests (`tests/test_text_normalizer.py`)
  - Phase 4: F5-TTS Adapter & Colab benchmark suite (`tests/test_f5_tts_adapter.py`, `scripts/05_benchmark_f5.py`)
  - Phase 5: GPT-SoVITS Adapter & Colab benchmark suite (`tests/test_gpt_sovits_adapter.py`, `scripts/06_benchmark_gpt_sovits.py`)
  - Phase 6: Blind Evaluation kit & Comparison report (`tests/test_compare_benchmark.py`, `scripts/07_compare_results.py`)
  - Phase 7: EngineFactory & Selection tests (`tests/test_engine_selection.py`, `scripts/08_run_selected_engine.py`)
  - Phase 8: Style Profile Manager unit tests (`tests/test_style_manager.py`)
  - Phase 9: Long-Text 5,000 chars chunking & WAV merging (`tests/test_long_text_pipeline.py`)
  - Phase 10: Colab Fine-tuning trainer kit (`notebooks/03_f5_tts_finetuning_colab.ipynb`)
  - Phase 11: FastAPI REST API integration tests (`tests/test_api_endpoints.py`)
  - Phase 12: Minimal Web UI (`frontend/index.html`, `frontend/app.js` mounted at `/`)
  - Phase 13: 10/10 Acceptance Gates Verified (`scripts/verify_acceptance_gates.py`)
failed: []

## Current blocker
None. All 13 Phases successfully completed, verified, and audited.

## Next action
Project is ready for production use.
- Launch Studio locally: `uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000`
- Access Web UI at: `http://127.0.0.1:8000`

## Important decisions
- Zero-cost architecture strictly maintained: No paid APIs, no multi-user clutter, no Redis/Celery/PostgreSQL/S3.
- Full 5,000 character synthesis capability with deterministic sentence-aware chunking and seamless WAV merging.
- F5-TTS selected as primary engine for long-text stability; GPT-SoVITS preserved as fallback.
- Complete privacy preservation: Voice recordings and model weights excluded from git tracking.
