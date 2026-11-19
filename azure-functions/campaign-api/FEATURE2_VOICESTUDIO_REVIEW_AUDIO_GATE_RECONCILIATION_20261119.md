# Feature2 VoiceStudio reviewer source-only current-main recovery — 2026-11-19

Original PR #937 head 603e6e488085ce78fa4a86e3ef2f4c9bb0c820e2; main baseline d22758e2c4c81ac1349f428bd1ddb747f3f12aa6.

Added exactly seven previously absent unregistered private-audio reviewer modules, negative tests, and handoff from #937, without overwriting any main files. Preserved newer main versions of the three already-existing dependencies:
- azure-functions/campaign-api/FEATURE2_VOICESTUDIO_PRIVATE_READ_HANDOFF_20261111.md
- azure-functions/campaign-api/feature2_voicestudio_storage.py
- tests/ai/test_feature2_voicestudio_storage.py

This is CPU-only source and tests. The root route is unregistered; no real SQL RPC, licensing/signature issuance, Azure deployment, model inference, commercial rights or public WAV exposure is approved. Latest new-head four-job CI and independent backend tenant/finance approval must be checked before live activation. The historical source #937 remains traceable through merge ancestry. Do not mark F2-19/20 or release DONE based on source alone.
