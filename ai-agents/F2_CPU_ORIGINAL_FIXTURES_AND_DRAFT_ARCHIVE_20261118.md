# Feature2 original media fixtures and historical draft preservation (2026-11-18)

Current-main source recovery from original conflicted #551 head `d80d6b50705323290c4b214bf2f006eacef1ef33`.

Preserved original, byte-identical Git blobs:
- `ai-agents/test-fixtures/clothing-shop-pexels/generate-synthetic-matte.py`: `ff19964c51ceb8adaae31e97dcf376b8e91bae1f`
- `ai-agents/tests/test_feature2_synthetic_matte.py`: `fbeec0f33218f797cdff5b25a3418feb9e7b1f45`
- `ai-agents/test-fixtures/clothing-shop-pexels/generate-original-test-audio.py`: `dddf96a47d417155974b40dcc1736a6313b133bf`
- `ai-agents/tests/test_feature2_original_test_audio.py`: `426ad3df24025171db522623fe8d48f2ae691379`

These use Python standard-library CPU only: deterministic 1080x1920 synthetic PNG with SHA/provenance and an original 5-second PCM test music bed with SHA/frame/overwrite denial tests. **Not** real product photography, licensed music, voice, Kokoro/VoiceStudio/Wan/FLUX inference, private media, signed retailer rights, generated video, or publishing output.

Historical stacked PRs [#697](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/697) F2-27, [#700](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/700) F2-20 and [#917](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/917) F2-21 contain old Kokoro-specific, security-sensitive source patches. All **complete original changed-file patch hunks**, path names, original exact heads and ledger amendments are preserved under `ai-agents/source-archives/PR_697_...`, `PR_700_...` and `PR_917_...` without applying obsolete model paths or overwriting newer tenant code. These are archival evidence, **not integrated source functionality**. Original tasks F2-20/21/27 remain IN PROGRESS until modern VoiceStudio/real JWT+RLS private atomic store and F4/F7 owner review.

After exact-head four-job PR CI, merge to main with expected head, verify fresh main four-job CI; then retire those 3 original obsolete stacked PRs UNMERGED as source-lossless archives only, with individual evidence comments. No GPU/paid provider, cloud/SQL/PROD or WineShopPOS changes.
