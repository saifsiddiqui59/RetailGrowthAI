# Feature #7 — F7-06 current F2/F4 contract drift review (source only)


## 2026-10-30 — F7-06 latest F2/F4 source-contract drift review (not integrated)

- Read actual Feature2 draft #551 head `4294e9bc2f8f905fa0bbda237b8da9305db0042a`: `review_signed_audio_transcript` and `compare_signed_feature7_word_error_rate` require source-SHA/job/current-rights-bound `feature7_signed_faster_whisper_asr_v1` original `audio/wav` evidence. Feature7's current `original_wav_cpu.mjs` emits that schema; genuine model inference and human reference WER remain unverified.
- Read actual Feature4 draft #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f`: `execute_approved_edit` only accepts persisted server-approved `creative_reel_v1` edit decisions with one contiguous trim per scene. Feature7's nonlinear speech/caption/music bundle remains `approved:false`, `renderable:false` and cannot be passed as an executable Feature4 decision.
- Added source-only `CROSS_FEATURE_CONTRACT_AUDIT_20261030.json` and `test_feature7_cross_feature_contract_audit.py`. Local Feature7 checks always run; actual F2/F4 Python source checks **explicitly skip** until the coordinator combines their real branches in one checkout. This is a pinned drift snapshot and proposed integration tripwire, not a production cross-feature E2E test.
- **F7-06 remains IN PROGRESS** until real same-checkout F2/F4 tests and coordinator integration pass; external `DEP-F7-14`, `DEP-F7-19`, `DEP-F7-23` remain. No shared docs/contract edits, cloud, GPU, paid model, PROD or WineShopPOS operations.

