# Feature #2 / original task #29 — private MP3 + derived WAV registration receipt

2026-10-29 · source-only, **IN PROGRESS**. Scoped continuation of Feature2 unified draft PR #551, with a separate nonconflicting branch. Does **not** claim hosted tenant reads, real approved model audio or commercial rights.

## Change
`feature2_voiceover_upload.accept_unreviewed_mp3` now refuses a trusted storage callback that only returns an MP3 asset ID. It requires a **different** valid private derived WAV asset ID, original and derived byte SHA-256, same shop/campaign, `derived_wav_private: true`, explicit `atomic_pair_registered: true` and pending review. A callback claiming publishing, motion, commercial-use rights or human speech verification is denied. The return remains pending review with no signed URL, F7 source registration or paid work.

Regression tests contain synthetic/monkeypatched local FFmpeg-decoder bytes only; they deny missing, aliased, malformed, public, non-atomic, cross-shop, changed SHA and elevated callback receipts. Existing real FFmpeg synthetic MP3 decode test is preserved and its trusted storage test double now returns the explicitly required second object.

## Integration/acceptance
The coordinator must connect a **server-trusted atomic two-object private store** that independently commits both bytes and their immutable metadata, validates tenant membership and revocation, and supplies this receipt only after the transaction is durable. Do not trust browser JSON as a backend receipt. Need actual signed DEV tests for simultaneous private object visibility, rollback on one failed write, rights denial, and F7 original-WAV registration; no live implementation is present in this source change.

Source tests, exact-head four-job CI, coordinator review, parent #551 integration, fresh main 4/4, #650 ZIP release and #249 live route remain gates. No new paid models, GPU, PROD or WineShopPOS changes.
