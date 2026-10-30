# Feature #2 F2-18 — OpenPronounce visible-evidence safety (2026-10-30)

**Task:** F2-18, offline OpenPronounce checkpoint and correction benchmark. **Status:** IN PROGRESS; this is an independent source-only reviewer hardening change, not a completed model benchmark.

The existing `feature2_voice_quality.project_offline_openpronounce_review` previously rejected ASCII control characters and HTML angle brackets but permitted Unicode bidirectional overrides and invisible formatting controls in reported words and IPA. Those characters could mislead a human pronunciation reviewer. The Feature2-owned projector now rejects Unicode category C controls/format characters in words and IPA while preserving visible Devanagari text and legitimate IPA combining marks. Seven synthetic-only regression cases cover both denial and legitimate script handling.

**Branch:** `feat/feature2-openpronounce-control-safety-20261030` stacked on [draft #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551). **Targeted test:** `uv run --project ai-agents pytest ai-agents/tests/test_feature2_voice_quality.py -q`; exact-head CI must be inspected. No local or hosted execution is claimed in this handoff.

**Dependency:** `F2-18-ORIGINAL-CHECKPOINT`, owner **Feature2 operator / coordinator**. Required: verified original OpenPronounce 0.3.0 and model checkpoint digests/licenses, preloaded offline CPU-only worker and real original rights-cleared WAV, bounded cold/warm CPU timing and independently listened comparison. Acceptance: actual model output SHA/provenance, safe pronunciation/correction evaluation with human signoff, no external gTTS or hidden network calls, and coordinator-accepted exact-head 4/4 plus postmerge main 4/4 CI. Model downloads, live TTS and billable operations remain OFF.

**Shared gate:** coordinator-owned [issue #650](https://github.com/saifsiddiqui59/RetailGrowthAI/issues/650) protected Functions ZIP member limit. No bypass. Feature2 ledger and canonical task status are coordinator-owned after review/merge; do not mark integrated DONE. No GPU, paid inference, hosted SQL, PROD, WineShopPOS, customer media or user-facing sample.
