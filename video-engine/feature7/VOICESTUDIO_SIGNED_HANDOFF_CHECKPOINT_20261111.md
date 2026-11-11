# F7 VoiceStudio signed handoff checkpoint — 2026-11-11

Stacked child [#926](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/926) on existing Feature7 parent [#513](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513), following merged upstream adapter [#911](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/911). F4 dependency [#910](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/910) is merged into F4 parent, not main.

Implemented `voicestudio_signed_handoff.mjs`: the trusted worker receives reviewed word timestamps, distinct original WAV and original video SHA256 digests, active exact shop/asset/job/model lease, normalizes through existing Feature7 transcript digest and HMAC signing, verifies the resulting evidence, emits source-relative Indic caption cues and non-executable Feature4 edit advice. No automatic approval or render.

Added `tests/media/test_feature7_voicestudio_signed_handoff.py` with positive Hindi word timings and negative foreign tenant, wrong video/audio, expired/revoked/foreign lease, model mismatch, bad timing, Unicode bidi and tampered evidence checks. These are offline deterministic fixtures, **not** proof of real ASR or licensed model accuracy.

**Next code action:** connect this bridge to the existing trusted original-video extraction and current-authority review worker (never expose it as a browser endpoint); validate the actual video bytes and exact WAV extraction provenance and recheck active lease at consumption. Then run targeted offline CPU tests and exact-head four-job CI. Integrate child into #513 only after green checks; parent main merge must be serialized by Integration Sprint. No main 4/4 or hosted product acceptance is claimed. Model/paid/GPU/PROD remain OFF.


## 2026-11-11 — child #926 integrated, next WAV provenance hardening
- Child #926 squash-merged into parent #513 as `025a6db3ce8f3dc3ab29af3910abfd80db8b7e7e` after exact-head [CI #42957638080](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42957638080) passed all four jobs. This is **parent source**, not a main merge.
- New scoped follow-on child branch `feat/feature7-voicestudio-wav-chunk-integrity-20261111` rejects duplicated RIFF `data` chunks and a `data` chunk preceding the PCM `fmt ` declaration, even if attacker-provided WAV bytes and SHA256 are self-consistent. Deterministic negative cases added in `tests/media/test_feature7_voicestudio_verified_media.py`.
- Next: exact-head four-job PR CI, merge child to #513 if green and policy eligible; Integration Sprint owns serialized parent-to-main reconciliation. Confirm parent CI and independently reviewed current-main compatibility before accepted DONE.
- Original F7-06 remains IN PROGRESS. F4 dependency [#910](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/910) is merged only into F4 parent; licensed model, hosted STT, real JWT/RLS, GPU and paid inference remain OFF.
