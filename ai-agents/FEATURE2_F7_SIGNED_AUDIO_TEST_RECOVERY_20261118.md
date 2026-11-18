# Feature2/F7 signed-audio offline regression recovery — 2026-11-18

Source-only recovery from original Feature2 parent [#551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551), original head `d80d6b50705323290c4b214bf2f006eacef1ef33`.

- Restored the **unchanged** 239-line source Git blob `22442f7107ceebc587d4201519b7920f9d74c9ec` at `ai-agents/tests/test_feature2_feature7_signed_audio.py`.
- Existing imported production code `ai-agents/src/ai_agents/feature2_voice_quality.py` already matches original source Git blob `aaa66fe01591a3f6e89051d53530737ef9ebb673` on baseline main `f981fb2c2d7bf20b7e409097ce18a5001855ce17`. No production source change and no cross-feature API changes.
- Offline fixtures cover signed HMAC scope/source/job binding, tampered WAV digest/word/time evidence, revoked editor/human transcript confirmation, Indic text word-level error accounting and refusal to conflate word error rate with human pronunciation or commercial publication approval.
- Suggested targeted check: `python -m pytest -q ai-agents/tests/test_feature2_feature7_signed_audio.py`. Mandatory final exact-head PR CI and fresh main 4/4 must also pass before integration acceptance. This document records source only, **not** a tested, hosted, or accepted claim.

Still OPEN: F2-17/20/23 actual signed Feature7 ASR provenance, private original WAV/current tenant rights, independent human audio/commercial licensing review and Feature4 consumer acceptance. Synthetic HMAC/words cannot prove live inference, model rights, vocal quality or publishability. All paid inference, GPU, Azure/Supabase hosted changes, PROD and WineShopPOS remain OFF.
