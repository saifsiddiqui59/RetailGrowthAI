# Feature2 F2-05 quality + source-only music recommendations — 2026-11-15

## Exact source integration

Retain existing **unchanged** Feature2 parent #551 (`d80d6b50705323290c4b214bf2f006eacef1ef33`) implementation and tests, not a rewrite:

| Source or test | Original Git blob SHA |
| --- | --- |
| `src/ai_agents/feature2_creative_quality.py` | `d96c88bec7e6e37270138157158166d51051711c` |
| `tests/test_feature2_creative_quality.py` | `415bd5aa50ac2d7536f2b71eb20b2e49b70dc2d1` |
| `src/ai_agents/feature2_music_recommender.py` | `a2cfdb7e7e671d928319e707eeb0b83ebf20e312` |
| `tests/test_feature2_music_recommender.py` | `c265e387d4c1a0a9e507a40d8a44a33d149b8208` |

Scope: original **F2-05** 15/30/60s structural creative validation and related draft-only audio discovery/ranking for creative review. Source checks do not certify writing quality, brand accuracy, actual sound trends, music rights or generated visuals. Tests stay under `ai-agents/tests/` and run through unchanged full Part 1 Python CI, in addition to isolated Supabase, FFmpeg and frontend checks. No role grant, provider call, direct retailer route or generation is newly registered.

**Non-authorization boundary:** a structurally high score is NOT a human approval; recommendations never claim that a trending sound grants sync, performance or commercial reuse. The platform-audio reference mode and separately licensed embedded music must remain distinct. Unverified images, audio, customer discounts and releases are not inputs to any live publish/billing dispatcher in this PR.

Original #551 and stacked #848 remain open: distinct verified-editor/tenant review, VoiceStudio private storage, real audio licensing, Feature4 renderer/QA and Feature5 GPU remain independently gated. Pinned Creative Director source itself already merged through #949; do not re-merge it here. This source component must pass final-head four-job CI and fresh postmerge main 4/4 before accepted source integration. Original task status F2-05 is **source-complete** only; no original hosted task or feature release DONE by this merge.

GPU and all paid model/provider calls OFF. No SQL or hosted Azure deployment, PROD or WineShopPOS modification.
