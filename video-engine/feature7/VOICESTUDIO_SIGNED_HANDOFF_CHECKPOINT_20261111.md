# F7 VoiceStudio signed handoff checkpoint — 2026-11-11

Stacked child [#926](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/926) on existing Feature7 parent [#513](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513), following merged upstream adapter [#911](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/911). F4 dependency [#910](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/910) is merged into F4 parent, not main.

Implemented `voicestudio_signed_handoff.mjs`: the trusted worker receives reviewed word timestamps, distinct original WAV and original video SHA256 digests, active exact shop/asset/job/model lease, normalizes through existing Feature7 transcript digest and HMAC signing, verifies the resulting evidence, emits source-relative Indic caption cues and non-executable Feature4 edit advice. No automatic approval or render.

Added `tests/media/test_feature7_voicestudio_signed_handoff.py` with positive Hindi word timings and negative foreign tenant, wrong video/audio, expired/revoked/foreign lease, model mismatch, bad timing, Unicode bidi and tampered evidence checks. These are offline deterministic fixtures, **not** proof of real ASR or licensed model accuracy.

**Next code action:** connect this bridge to the existing trusted original-video extraction and current-authority review worker (never expose it as a browser endpoint); validate the actual video bytes and exact WAV extraction provenance and recheck active lease at consumption. Then run targeted offline CPU tests and exact-head four-job CI. Integrate child into #513 only after green checks; parent main merge must be serialized by Integration Sprint. No main 4/4 or hosted product acceptance is claimed. Model/paid/GPU/PROD remain OFF.
