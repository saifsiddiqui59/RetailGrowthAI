# Feature #4 F4-13 — all-rendered-media release rights fence (source-only)

**Scope:** Feature4-owned `feature4_release_gate.py` and offline negative tests.
**Parent:** draft PR #322, `feat/feature4-professional-video-studio`.
**Task:** `F4-13` (private input/license/dependency integrity), with an additional release-readiness check for `F4-31`.

## Problem and fix

The prior release validator required current rights for the reviewed Feature3 product and Feature5 motion only. A rendered Reel's additional audio, logo, poster, stock video or other referenced media could be foreign-shop, unapproved, revoked or explicitly synthetic while the two primary records still passed. It also accepted a present but non-UUID output asset reference.

The proposed guard now validates the canonical private output asset ID and **every** ID in the authoritative `lineage.media_asset_ids` list: bounded unique canonical IDs, matching shop, known media kind, nonempty source provenance and rights evidence, current approved/commercial flags and explicit `synthetic_fixture=False`. It preserves the stricter original Feature3-product/Feature5-motion provenance checks. No new public API, schema, model, queue, billing, RLS or cloud resource is introduced.

## Verification and remaining gates

- Added isolated offline positive fixture for independently reviewed audio and negative tests for missing, foreign, unapproved, synthetic, unsupported-kind, unlicensed, duplicate and malformed auxiliary media and malformed output asset IDs.
- **CI evidence:** pending exact-head GitHub Actions; do not treat source implementation or synthetic tests as integrated DONE.
- **Not live proof:** The injected `job`, `lineage`, `reviewed`, `media` objects are only trustworthy if the coordinator fetches fresh same-tenant DB records with revocation and signed reviewer evidence. This change does not provide those readers, verify original MP4 visually, grant commercial rights, sign downloads or approve production.
- **Task status proposal to coordinator:** `F4-13` remains **IN PROGRESS / SOURCE PROPOSED** until PR review, merge into main, fresh four-job postmerge CI, and independent commercial license/notice approval. `F4-31` remains **BLOCKED** on real owner review and signed rights. Do not record DONE in `coordination/task_progress.json` from this branch.
- **Dependencies:** F3-LICENSED-MEDIA (Feature3: actual retailer model/garment approval); F5-REAL-WAN-MOTION (Feature5: approved garment-matched encoded motion; GPU OFF); F4-EDITOR-SOURCE (coordinator: merge #322); commercial human review (retailer owner/coordinator). Fixtures are not approved production assets.

No paid GPU/model calls, Azure deployment, PROD changes, or WineShopPOS modification.
