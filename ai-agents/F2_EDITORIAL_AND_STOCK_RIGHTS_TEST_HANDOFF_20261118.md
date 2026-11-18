# Feature #2 original editorial-claims and Pexels review-negative regression recovery (2026-11-18)

This is a **test-only source reconstruction** from old conflicted F2 parent #551 head `d80d6b50705323290c4b214bf2f006eacef1ef33`, on verified current main `343585467c8bc8f0d517c0fff8b90e0d07d7fbf7`.

Original unchanged Git blobs:
- `ai-agents/tests/test_feature2_editorial_basis.py`: `630353729b85e16dcd61e944ca1fdcb8c7a73f1e`, 438 lines of offline evergreen/trend/RSS, tenant rights, Unicode/Hindi/Marathi retailer claims and fake viral/discount negative tests.
- `ai-agents/test-fixtures/clothing-shop-pexels/rights-provider-general-review.json`: `5a9e4bb9d5a052edaa5bab0cecea8d60839c4ed9`, **historical Oct 28 2026 observation only**, not a current live Pexels audit or individual model/license permission.
- `ai-agents/tests/test_feature2_rights_review.py`: `a4eb98f70aa7c0cfad97b4c82e16e0668e625fcc`, original cross-fixture check rejecting asset SHA, human release, rights, source-media import, publication.
  
Verified current `ai-agents/src/ai_agents/feature2_creative_quality.py` Git blob `d96c88bec7e6e37270138157158166d51051711c` matches original #551 **byte-identically**. Verified present current Pexels `manifest.json` has the exact same four source reference IDs as archived review fixture; **no real media downloaded**. No production code, JWT, RLS, OSS licenses, model, API, routes or workflows changed.

The historical Pexels snapshot has `provider_commercial_ads_general_license_verified=true` but should be read **only as its dated author claim**, not a new independent license audit or permission for virtual try-on, private media or retailer endorsement; `can_publish=false`, signed tenant storage absent. As of this checkpoint, actual current licensing and human releases remain NOT VERIFIED.

Accept this isolated test-only milestone only after **exact PR final-head four-job CI**, safe scoped current-main merge with head verification and **fresh exact-main four-job CI**. This does not close original F2 task IDs or hosted rights/approval requirements. No GPU, paid model/provider, Azure/Supabase deployment/SQL/PROD or WineShopPOS actions.

## Additional cross-feature synthetic acceptance test (same batch)
- Added the original unchanged `ai-agents/tests/test_feature2_full_upstream_stock_audio_pipeline.py` Git blob `4438a0947e5716eea0353611ede91518359fa02c` from #551. It verifies two 30/60-second **synthetic** source-only director→caption→private-stock B-roll→PCM-audio handoff paths and denies tenant mismatch, modified rights receipt and GPU/publish flags. It does **not** synthesize a complete video file, verify an actual user JWT, authorize private tenant data, or confer commercial rights.
- Compared original #551 vs latest main: `feature2_stock_media.py` blob `5513813b0e87caea1f11e682bd30a2851faf61fe`, `feature2_stock_cutaway.py` blob `c67397517dabe3388c59618a82919f999ddf2a3a`, `feature2_audio_evidence.py` blob `ff1100207186b9e98a4e3267c2fd846a06aa4302` and `feature2_creative_quality.py` blob `d96c88bec7e6e37270138157158166d51051711c` are byte-identical. This additional test only uses fake locally synthesized bytes, local Node MIT sources and no provider/network.
