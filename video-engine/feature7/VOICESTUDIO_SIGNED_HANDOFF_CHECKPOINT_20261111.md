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


## 2026-11-11 — follow-on strict WAV chunk boundary
- After merged child #933, scoped follow-on rejects all RIFF chunks following the verified PCM data chunk, including zero-length LIST and self-consistent SHA256 trailing JUNK. Deterministic negative cases added to `tests/media/test_feature7_voicestudio_verified_media.py`.
- Next: verify exact-head four-job CI; if green and reviewed, merge child into #513, then let Integration Sprint reconcile parent with current main. Revisit lease expiry clock races and original extraction provenance as next independent F7 tasks. F4 dependency #910 remains parent-only. No model, GPU, paid, cloud or PROD work.

## 2026-11-11 — executable WAV gate repair
- Reviewed child #940 patch and found escaped `\\n` text inside a `//` comment, which commented out the `seenData` rejection and following `fmt` branch. Replaced with real newlines in commit `a02f571b1bcf764c43a90c3ca31f4bc54117880b` so trailing chunks are rejected as intended.
- Exact-head four-job CI is not yet reported for this commit; no child merge. Container cannot resolve github.com for local clone, so local targeted tests remain unverified. Do not claim 4/4.
- NEXT CODE ACTION: verify the exact-head CI jobs; run the owned offline `test_feature7_voicestudio_verified_media.py` and signed-handoff tests in a reachable runner; if green, merge #940 into parent #513 using expected head SHA, then inspect parent CI and queue parent-to-main reconciliation for the Integration Sprint. Next independent task: lease expiry race against current clock rather than caller-provided `now_ms`.

## 2026-11-12 — exact-head CI and child integration
- Feature7 child [#942](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/942) at exact head `5bd5a8aa96b155713b32991c19205cb3723729ba` passed all four jobs in [Actions #43256348158](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43256348158): Supabase isolation, FFmpeg, frontend and Python/uv.
- Squash-merged eligible child into existing Feature7 parent [#513](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/513) at `c548f59bcbf3ad23a1899e736db7632866549b28`. No main merge; parent reports `mergeable_state=dirty` against current main and requires scoped conflict review. This verifies source CI only, not hosted acceptance or independently licensed STT.
- **NEXT CODE ACTION:** inspect #513 vs current main conflict files; reconcile only Feature7-owned paths, preserve other workers' changes, run offline CPU `tests/media/test_feature7_voicestudio*` plus exact-head four-job CI, and hand main merge to Integration Sprint. Then implement original-video/WAV extraction provenance verification in the trusted worker, with negative cross-tenant and stale-lease tests. F4 dependency [#910](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/910). GPU, paid inference, cloud/PROD and WineShopPOS remain OFF.

## 2026-11-13 — reject accessor-backed ASR word records
- Hardened `voicestudio_signed_handoff.mjs` to reject sparse word arrays and accessor-backed `word`, `start`, `end` fields before normalization/HMAC signing; deterministic negative cases added in `tests/media/test_feature7_voicestudio_signed_handoff.py`.
- Commits `fb1bf1a1` (source), `6dbdca9c` (tests). Local GitHub clone remains blocked by DNS; **no local test pass claimed**. Exact-head four-job CI still requires verification.
- **NEXT CODE ACTION:** verify final-head CI and targeted offline tests; inspect/reconcile #513 against latest main without touching other feature paths; link F4 dependency #910. Keep signed evidence review-only and no GPU/paid/PROD/cloud changes.
