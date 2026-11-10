# F4-04 / F4-20 — Original #715 approved-edit snapshot safety reconciliation

2026-11-11 — Source-only pending review on current Feature4 parent #322 (`5d858bc18d1974a11fcca0e628f66f09fd4a1001`).

The older open draft [#715](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/715) introduced a missing authorization boundary: matching only Feature7 approval ID / shop / campaign does not bind the exact approved scene edit decisions. An untrusted reordered or retimed source could replay a valid approval ID. The original existing Feature4 edit executor and its deterministic tests have been ported onto the latest parent, without resetting the v2 compiler, as a small feature-owned source reconciliation.

`edit_decision_fingerprint` computes a canonical SHA-256 of the **entire** Feature7 decision (including every scene operation) and `execute_approved_edit` requires the digest from a separately persisted, trusted server-side snapshot; it strips the envelope-only digest before calling the existing v2 compiler. Negative fixtures deny missing/forged decisions, altered trims/durations and reordering after approval. This does not create a real DB approval transaction or authorize a browser to supply the trusted digest.

Acceptance: exact final-head Part1 CI four jobs, legitimate affected-lead review for the shared Feature7 decision contract, compatible merge onto existing Feature4 parent, fresh parent four-job CI, and eventual reviewed main/hosted tenant authorization and original rights checks. Only after accepted source merge with complete tests may original #715 be retired as source-superseded. Do not mark F4-04/F4-20 DONE or approve actual customer release.

No GPU/paid inference, hosted SQL/Azure, PROD or WineShopPOS changes. Feature4 parent #322 and Issue #650/#249 remain separate.
