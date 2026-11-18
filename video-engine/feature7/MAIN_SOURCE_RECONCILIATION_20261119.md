# F7 source-only conflict-safe reconciliation — 2026-11-19

Original #513 head: eb9df22f34604f2ac592e9c1620430a7978794b5.
Base main snapshot: 49609efcec0f7106d4d10337fb57c39a7a090c17.

This merge commit preserves current main (including all global JWT/RLS/Functions/workflow and Feature 3/4/2 code), incorporates exactly 129 previously absent Feature7-owned source/test/license/handoff paths verbatim from the old branch, and retains 3 already-existing newer F7 paths on main:
- tests/media/test_feature7_voicestudio_asr.py
- video-engine/feature7/VOICESTUDIO_ASR_HANDOFF_20261111.md
- video-engine/feature7/voicestudio_transcription.py

No existing main file was overwritten. The original branch remains a merge parent to preserve its exact history. Offline checks must be rerun on this new head and reviewed. This is **source-only**; customer assets/rights, signed real DEV JWT/RLS/SQL, commercial ASR, Feature4 native acceptability, media quality and publishing have NOT been approved. Do not infer Feature7 task DONE or launch GPU/paid inference/cloud resources.
