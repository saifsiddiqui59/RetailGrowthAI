# Original F4-04/F4-20 #715 — immutable Feature7 edit decision provenance (2026-11-17)

Original obsolete draft #715 head `dbae534f002940545aa130668f718215c8dc8528`. Original source `video-engine/feature4_edit_execution.py` Git blob `efd57f5685b105308c220d9ffc084164583b805c` is EXACTLY preserved in surviving OPEN draft #906, and every original test method and nonblank test line is preserved (with additional regressions in #906). Original #715 had separately revised task tracker and Azure handoff; unique historical text is retained verbatim below. Never restore stale #715 entire tracker/Azure handoff over current parent, nor claim original task DONE.

## Original task tracker excerpt

## 2026-10-30 — F4-04 / F4-20 approved-edit decision integrity (stacked PR #715)

- **Security gap found:** source-only Feature7 editor execution previously matched only the approval ID / four review metadata fields and original draft hash; an attacker able to substitute a scene decision could replay a valid approval ID with altered trim/reorder/transition instructions.
- **Owned source fix:** require `snapshot.edit_decision_sha256` (server-persisted canonical SHA-256 of the **entire approved Feature7 decision**, including every scene command). Reject missing, invalid, changed or unbound decisions before any compiler output; remove this internal trust-envelope field before calling the existing immutable renderer contract. Negative tests cover tampered order/trim, forged or missing digest, and independent malformed trusted decisions. No customer media, external inference, or cloud calls.
- **Coordinator dependency / acceptance:** coordinator-owned authenticated approval transaction must persist the digest when human review occurs and load it independently from the submitted render request, in the same authorized snapshot. Do **not** derive the trusted hash from a browser request; do not auto-approve a Feature7 recommendation. F7 owns actual reviewed decision input; coordinator owns JWT/RLS and persistence. Until a reviewed coordinator adapter and exact-head CI pass, this is **source IN PROGRESS**, not accepted or hosted DONE.
- **PR:** [#714](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/715) targets the existing Feature4 branch under [draft #322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322). This is not a change to shared contracts, migrations, production, or the canonical task_progress ledger.


## Original Azure handoff excerpt

## 2026-10-30 — Feature7 reviewed scene-decision binding (PR #715)

The source-only `feature4_edit_execution.execute_approved_edit` now requires a **trusted, persisted** `snapshot.edit_decision_sha256` matching the canonical JSON SHA-256 of the full `approved_edits` object. This closes a review-ID replay gap: the prior check verified review metadata and original draft hash, not the approved edit commands themselves. The function removes the internal digest field before invoking the unchanged `creative_reel_v1` compiler.

**Coordinator-owned blocker:** within an authenticated, same-shop, RLS-authorized approval transaction, persist the exact approved Feature7 decision hash; when rendering, independently reload the immutable reviewed decision and its digest alongside the original draft. Never compute the *trusted* digest from the browser/model-supplied decision, never accept unapproved edits, and never bypass the existing quota/outbox and media rights checks. Acceptance requires tests for modified scene order, trim, transition, cross-tenant review, revoked review and stale draft plus hosted negative paths. PR #715 is stacked source-only and does not attest real DEV sign-in or production release.


## Required continuation
- Keep #906 open until its conflict with newer Feature4 parent #322 is resolved safely, all mandatory exact-head CI passes, and affected Feature7 reviewer independently checks persisted snapshot digest authorization and cross-tenant replay risks.
- This is a code path with **no authenticated hosted DB persistence yet**. No main/hosted acceptance, no approved customer media, and no F4-04/F4-20 DONE by dedup closure.
- No GPU, paid AI, cloud deployment, PROD or WineShopPOS changes.
