# Feature #2 #8/#12: private audit and blind human-review post-CAS revocation

Date: 2026-10-30. **Source-only, IN PROGRESS**.

## Reason and change

Feature2's existing HMAC-linked trace writer (`append_feature2_trace`) and blind reviewer scoring CAS (`stage_blind_human_review_revision`) validated current tenant/source before private writes, but a revoked membership or changed candidates *during* a trusted writer callback could return an apparently valid success receipt. The source now revalidates current signed scope or editor+immutable candidate identity after write, and rejects any returned storage receipt asserting paid motion, publication or a promoted review status. Do **not** recheck the previous CAS revision after a successful increment; that would reject valid writes.

Regression cases use injected fake callbacks: revoked immediately after writing a private trace, revoked after writing a signed human-score revision, and writer receipts with elevated publish/payment/review flags. Tests preserve existing successful private proof behavior and never equate fixture signatures with actual human reviewers or worker/model activity.

## Integration requirements

This Python source check cannot undo DB writes already committed before revocation. The coordinator owns real authenticated JWT/RLS, transactional lease/role/candidate fencing, immutable unique event/CAS store, partial-write cleanup, independently signed human reviews, authorization-by-read and live acceptance. Review [parent PR #684](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/684) and [unified F2 draft #551](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/551) as a stack; this change must be merged only after branch exact-head 4/4, protected packager issue #650, accepted integration and fresh main 4/4. Feature2 original tasks #8 and #12 remain IN PROGRESS; don't infer product DONE. GPU OFF; no paid inference/hosted SQL/PROD/WineShopPOS.


## Reconciliation checkpoint — 2026-10-31

The existing source/test post-CAS scope and elevated-receipt changes from #704 were selectively integrated into #848 while preserving newer batch Creative Director and Unicode logic. The original #704 remains open for provenance. No actual DB transaction, signed reviewer or production authorization was exercised. Combined exact-head CI must be checked after this integration; #650 packaging is a separate coordinator gate.
