# Feature2 coordinator proposal — preserve 120-member Functions ZIP gate (2026-10-29)

**This document proposes a fix; it does not change the shared packager or authorize deployment.**

Read source `scripts/deploy/package.py` on Feature2 PR #551: `source_files()` currently sweeps every `*.py` from `azure-functions/campaign-api`, `video-engine`, `poster-engine`, and `ai-agents/src/ai_agents`; it also adds the generated root `function_app.py`, `requirements.txt`, `host.json`, and three immutable `bin/` files. The shared `verify_zip()` correctly rejects duplicate names and any ZIP with **more than 120 members**, before processing rollback and poison-trigger checks. Four existing protected preflight tests now fail with `Duplicate or excessive ZIP members`. Do **not** raise 120, remove security checks, split archive without review, or skip release tests.

## Read-only source evidence

- Existing Feature2 branch `ai-agents/src/ai_agents`: **35 Python files**; it contains both deployed retailer trend/plan paths and offline/reviewer/CPU voice tools.
- Existing `function_app.py` provides actual Feature2 GET/POST route entrypoints for trends, drafts and prompt improvements, optional Foundry AI behind a disabled-by-default flag, and a daily trend collection trigger. These must remain fully functional and import complete.
- No live Speech/Feature7 private WAV route is currently registered in that Functions entrypoint. Source-only F2 `feature2_kokoro_local.py`, `feature2_voice_quality.py`, `feature2_voiceover_upload.py`, `feature2_sentence_retake.py`, `feature2_local_voice_workflow.py`, `feature2_pronunciation_dictionary.py`, `feature2_audio_evidence.py` and `feature2_feature4_voiceover.py` are **candidate** nondeployable or separate future speech-worker modules **only after the coordinator proves they are not transitively imported by active entrypoints**. Listing them here does not prove they are safe to omit.
- The protected mandatory ZIP members include the Functions wrapper, host/requirements, `ai_agents/schemas.py`, `render_worker.py`, `video-engine/render.py`, `poster-engine/render.py`, `poster_worker.py`, `bin/ffmpeg`, `bin/ffprobe`, and `bin/THIRD_PARTY_NOTICES.txt`. Any allowlist must retain these and every transitive runtime dependency for **all existing triggers**, including disabled-by-default but registered routes.

## Coordinator-owned patch criteria

1. Instead of broad `*.py` glob inclusion, ratify a **versioned deployable runtime manifest**. Compute the import closure from the actual Azure `function_app.py` (including dynamic imports, queue/timer triggers, branch-enabled modes, and regional wrappers); maintain an auditable list of nondeployable/offline modules. Do not trim based on filenames alone.
2. Prove that the default, existing retailer trend, paid Feature2 flag OFF/ON (mock services only), Feature3 v2, poster/render queue, poison and timer triggers can import and index correctly from an **extract-only verified ZIP**, without pulling any host files outside the ZIP. A missing required worker import must fail preflight.
3. Keep exact 120-member, 300 MiB compressed, 400 MiB unpacked, static ELF/FFmpeg license, 20m timeout, 25m lease, 780s encoder timeout, permission, traversal and duplicate-name guards unchanged.
4. Re-run four exact merged-head PR checks and the existing negative release/rollback/poison security tests; a separate independently reviewed future CPU speech-worker deployment may be necessary to keep ONNX weights out of a small Functions ZIP.
5. The coordinator, not the Feature2 owner branch, changes `scripts/deploy/package.py`, `.github/workflows/**` and canonical `docs/INTERFACES_V1.md`. Feature2 PR #551 remains draft until the ratified fix succeeds.

See [coordinator issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650); no Azure, paid GPU, PROD, original media or WineShopPOS action was taken.
