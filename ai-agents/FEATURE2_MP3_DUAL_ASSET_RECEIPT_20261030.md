# Feature #2 F2-29 — private MP3 dual-asset registration receipt (2026-10-30)

**IN PROGRESS, source-only.** This is a stacked proposal on draft #551, not a merged feature or a live authenticated upload.

## Change and fixture verification
The trusted storage callback for unreviewed retailer MP3 must confirm two distinct UUID private asset IDs, both exact byte SHA-256 digests, a same-shop/campaign receipt, pending-rights state, and `atomic_pair_committed=true`. Previously a writer could omit the derived WAV asset ID and still obtain a successful receipt; that made the derivative's private registration unverifiable. New negative fixture tests reject missing/foreign/aliased derivative IDs, false atomic-commit flag, wrong SHA and nonprivate receipts. The positive fixture explicitly supplies both IDs. A browser rights checkbox is never accepted as commercial permission.

Source: `ai-agents/src/ai_agents/feature2_voiceover_upload.py`, `ai-agents/tests/test_feature2_voiceover_upload.py`.

## Remaining evidence and gates
- Fresh exact-head CI: **pending verification**, and parent #551 has shared packaging issue #650; no passing CI is asserted here.
- Coordinator must implement a durable transactional private storage writer with atomic pair receipt, same-tenant RLS, signed user JWT, rollback and uncertain-write reconciliation, then review and merge with postmerge main 4/4.
- Original MP3 and derived WAV remain **unreviewed**, not original recorded F7 ASR proof, not approved F4 narration, not publishable and not model output.
- No paid models, GPU, PROD, deployment or WineShopPOS changes.

Proposed task-manager status: F2-29 remains `IN PROGRESS`; this PR is source evidence only, not an integrated DONE receipt.
