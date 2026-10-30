# Feature #2 F2-02 — Unicode discount-scope hardening (2026-10-30)

Status: **IN PROGRESS / SOURCE ONLY**. Owner: Feature #2. Parent source PR: #551. This stacked change proposes review, not coordinator acceptance or an integrated DONE event.

## Change
- Extend the existing deterministic, review-only retailer copy claim guard to detect long numeric percentages, fullwidth/small/Arabic percent signs, and compatibility-width spelled percentages.
- Reject invisible formatting and control characters that could hide an unapproved discount from a reviewer.
- Compare all detected discount occurrences with exact source-approved claim spans; normalization is detection-only and **never** transforms a retailer's legal approved wording into an authorization.
- Add isolated negative fixtures for extra 50/1000 percent offers, Arabic-Indic/fullwidth symbols, hidden zero-width/bidi characters, and a permitted exact 20% scoped claim.

## Evidence / acceptance
- Source files: `ai-agents/src/ai_agents/feature2_creative_quality.py`, `ai-agents/tests/test_feature2_unicode_discount_scope.py`.
- Branch: `feat/feature2-copy-unicode-claims-20261030` stacked on `feat/feature2-unified-offline-source-20261028`.
- CI: **pending fresh exact-head four-job evidence**; do not infer success from an earlier #551 run.
- Coordinator must review stacked PR, reconcile against #551, integrate into main, and verify fresh main 4/4 before marking F2-02 DONE in `coordination/task_progress.json`.
- No real retailer facts, current JWT/RLS, independent offer approval, hosted acceptance, commercial content, or model output is verified by these fixtures. No paid model, GPU, PROD, Azure deployment or WineShopPOS change.

## Remaining blockers
- F2-02 live acceptance: coordinator-owned authoritative current shop offer and rights read-model, signed reviewer approval, actual hosted route and tenant/role revocation tests.
- ISSUE-650: coordinator-owned Azure package <=120 members and protected release checks.
- ISSUE-249: Azure reliability lead must verify signed DEV 503 fix.
